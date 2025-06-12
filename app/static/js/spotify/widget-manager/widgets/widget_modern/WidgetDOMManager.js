// DOSYA ADI: WidgetDOMManager.js

class WidgetDOMManager {
    // --- SABİT YAPILANDIRMALAR ---
    static Z_INDEX_CONFIG = {
        AlbumArtBackgroundElement: { a: 3, b: 1 },
        CoverElement:              { a: 4, b: 2 },
        default:                   { a: 6, b: 5 }
    };

    static CSS_CLASSES = {
        PASSIVE: 'passive',
        PREPARING: 'is-preparing',
        WIDGET_INACTIVE: 'widget-inactive',
        ANIMATION_CONTAINER_SELECTOR: '[class*="AnimationContainer"]',
        ERROR_ACTIVE: 'error-active'
    };

    constructor(widgetElement, config, stateService) {
        if (!widgetElement || !config || !stateService) {
            throw new Error("WidgetDOMManager için widgetElement, config ve stateService gereklidir.");
        }
        this.widgetElement = widgetElement;
        this.config = config;
        this.stateService = stateService;
        this.progressInterval = null;

        this.zIndexConfig = JSON.parse(JSON.stringify(WidgetDOMManager.Z_INDEX_CONFIG));
        this.CSS_CLASSES = WidgetDOMManager.CSS_CLASSES;

        this.listenToEvents();
        console.log("[WidgetDOMManager] Başlatıldı ve olayları dinliyor.");
    }

    listenToEvents() {
        this.widgetElement.addEventListener('widget:intro', (e) => this.runIntro(e.detail));
        this.widgetElement.addEventListener('widget:transition', (e) => this.runTransition(e.detail));
        this.widgetElement.addEventListener('widget:outro', (e) => this.runOutro(e.detail));
        this.widgetElement.addEventListener('widget:sync', (e) => this.startProgressUpdater(e.detail.data, e.detail.set));
        this.widgetElement.addEventListener('widget:error', (e) => this.displayError(e.detail.message));
        this.widgetElement.addEventListener('widget:clear-error', () => this.clearError());
    }

    // =========================================================================
    // ||                    OLAY YÖNETİM METOTLARI (EVENT HANDLERS)          ||
    // =========================================================================
    
    async runIntro({ set, data }) {
        const introElementIds = this.config.elements.filter(id => id.endsWith(`_${set}`));
        this._updateDOMContent(set, data);
        this._prepareElements(introElementIds);
        await this._waitForImages(introElementIds);
        this.widgetElement.classList.remove(this.CSS_CLASSES.WIDGET_INACTIVE);
        introElementIds.forEach(id => this._applyAnimation(id, 'intro'));
        this.startProgressUpdater(data, set);
    }

    async runTransition({ activeSet, passiveSet, data }) {
        this._flipZIndex();
        this._updateDOMContent(passiveSet, data);

        const outgoingElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
        const incomingElementIds = this.config.elements.filter(id => id.endsWith(`_${passiveSet}`));

        this.stopProgressUpdater();
        this._prepareElements(outgoingElementIds);
        this._prepareElements(incomingElementIds, { isIncoming: true });
        await this._waitForImages(incomingElementIds);

        let maxTransitionTime = 0;

        outgoingElementIds.forEach(id => {
            const time = this._applyAnimation(id, 'transitionOut', (el) => el.classList.add(this.CSS_CLASSES.PASSIVE));
            if (time > maxTransitionTime) maxTransitionTime = time;
        });

        incomingElementIds.forEach(id => {
            document.getElementById(id)?.classList.remove(this.CSS_CLASSES.PREPARING);
            const totalTime = this._applyAnimation(id, 'transitionIn');
            if (totalTime > maxTransitionTime) maxTransitionTime = totalTime;
        });

        setTimeout(() => {
            this.stateService.finalizeTransition(passiveSet);
            this._resetSetData(activeSet);
        }, maxTransitionTime);
    }

    runOutro({ activeSet }) {
        this.stopProgressUpdater();
        console.log(`Outro animasyonu ${activeSet} seti için çalıştırılıyor...`);
        // Gerekirse outro animasyon mantığı buraya eklenebilir.
    }

    // =========================================================================
    // ||               YARDIMCI METOTLAR: DOM İÇERİK YÖNETİMİ                ||
    // =========================================================================

    _updateDOMContent(set, data) {
        const item = data.item;
        if (!item) return;
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);

        const trackNameElem = query('.TrackNameElement');
        const artistNameElem = query('.ArtistNameElement');
        const coverElem = query('.CoverElement');
        const coverBgElem = query('.AlbumArtBackgroundElement');
        const totalTimeElem = query('.TotalTimeElement');

        if (trackNameElem) trackNameElem.innerText = item.name;
        if (artistNameElem) artistNameElem.innerText = item.artists.map(a => a.name).join(', ');
        if (coverElem) coverElem.src = item.album.images[0]?.url || '';
        if (coverBgElem) coverBgElem.src = item.album.images[0]?.url || '';
        if (totalTimeElem) totalTimeElem.innerText = this._formatTime(item.duration_ms);
    }

    _resetSetData(set) {
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);
        
        const trackNameElem = query('.TrackNameElement');
        const artistNameElem = query('.ArtistNameElement');
        const coverElem = query('.CoverElement');
        const coverBgElem = query('.AlbumArtBackgroundElement');
        const totalTimeElem = query('.TotalTimeElement');
        const currentTimeElem = query('.CurrentTimeElement');
        const progressBarElem = query('.ProgressBarElement');

        if (trackNameElem) trackNameElem.innerText = '';
        if (artistNameElem) artistNameElem.innerText = '';
        if (coverElem) coverElem.src = '';
        if (coverBgElem) coverBgElem.src = '';
        if (totalTimeElem) totalTimeElem.innerText = '0:00';
        if (currentTimeElem) currentTimeElem.innerText = '0:00';
        if (progressBarElem) progressBarElem.style.width = '0%';
    }

    startProgressUpdater(data, set) {
        if (this.progressInterval) clearInterval(this.progressInterval);
        
        let progressMs = data.progress_ms;
        const durationMs = data.item.duration_ms;

        const update = () => {
            const currentTimeElem = this.widgetElement.querySelector(`.CurrentTimeElement[data-set="${set}"]`);
            const progressBarElem = this.widgetElement.querySelector(`.ProgressBarElement[data-set="${set}"]`);

            if (currentTimeElem) currentTimeElem.innerText = this._formatTime(progressMs);
            if (progressBarElem) {
                const percentage = durationMs > 0 ? (progressMs / durationMs) * 100 : 0;
                progressBarElem.style.width = `${Math.min(percentage, 100)}%`;
            }
            progressMs += 1000;
        };
        update();
        this.progressInterval = setInterval(update, 1000);
    }

    stopProgressUpdater() {
        clearInterval(this.progressInterval);
        this.progressInterval = null;
    }

    displayError(message) {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement) {
            errorElement.innerText = message;
            this.widgetElement.classList.add(this.CSS_CLASSES.ERROR_ACTIVE);
        }
        this.stopProgressUpdater();
    }

    clearError() {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement && errorElement.innerText !== '') {
            errorElement.innerText = '';
            this.widgetElement.classList.remove(this.CSS_CLASSES.ERROR_ACTIVE);
        }
    }

    _formatTime(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    // =========================================================================
    // ||               YARDIMCI METOTLAR: ANİMASYON YÖNETİMİ                 ||
    // =========================================================================
    
    // Bu metotlar önceki yanıtta olduğu gibi tam ve doğrudur.
    _prepareElements(elementIds, options = { isIncoming: false }) {
        elementIds.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            el.classList.remove(this.CSS_CLASSES.PASSIVE);
            el.closest(this.CSS_CLASSES.ANIMATION_CONTAINER_SELECTOR)?.classList.remove(this.CSS_CLASSES.PASSIVE);
            if (options.isIncoming) {
                el.classList.add(this.CSS_CLASSES.PREPARING);
            }
            this._applyZIndex(id);
        });
    }

    _waitForImages(elementIds) {
        const imageElements = elementIds.map(id => document.getElementById(id)).filter(el => el && el.tagName === 'IMG' && el.src);
        if (imageElements.length === 0) return Promise.resolve();
        const promises = imageElements.map(img => new Promise(resolve => {
            if (img.complete) return resolve();
            const loadHandler = () => { cleanup(); resolve(); };
            const errorHandler = () => { cleanup(); resolve(); };
            const cleanup = () => {
                img.removeEventListener('load', loadHandler);
                img.removeEventListener('error', errorHandler);
            };
            img.addEventListener('load', loadHandler);
            img.addEventListener('error', errorHandler);
        }));
        return Promise.all(promises);
    }

    _flipZIndex() {
        for (const key in this.zIndexConfig) {
            const temp = this.zIndexConfig[key].a;
            this.zIndexConfig[key].a = this.zIndexConfig[key].b;
            this.zIndexConfig[key].b = temp;
        }
    }

    _applyZIndex(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        const baseName = elementId.substring(0, elementId.lastIndexOf('_'));
        const setLetter = elementId.slice(-1);
        const mapping = this.zIndexConfig[baseName] || this.zIndexConfig.default;
        const zIndex = mapping[setLetter];
        if (typeof zIndex !== 'undefined') {
            element.style.zIndex = zIndex;
        }
    }
    
    _applyAnimation(elementId, phase, onEndCallback = null) {
        const element = document.getElementById(elementId);
        if (!element || !this.config[elementId] || !this.config[elementId][phase]) return 0;
        const animConfig = this.config[elementId][phase];
        const { animation, duration, delay } = animConfig;
        if (typeof animation === 'undefined') return 0;
        if (animation === 'none') {
            const isOutPhase = phase === 'transitionOut' || phase === 'outro';
            if (isOutPhase) return (duration || 0) + (delay || 0);
            element.style.opacity = '0';
            setTimeout(() => { element.style.opacity = '1'; }, delay || 0);
            return delay || 0;
        }
        if (typeof duration === 'undefined' || typeof delay === 'undefined') return 0;
        const easing = (phase === 'transitionOut' || phase === 'outro') ? 'ease-in' : 'ease-out';
        const animationCssString = `${animation} ${duration / 1000}s ${easing} ${delay / 1000}s both`;
        element.style.animation = animationCssString;
        element.addEventListener('animationend', function handleAnimationEnd(event) {
            if (event.target !== element) return;
            element.style.animation = '';
            if (onEndCallback) onEndCallback(element);
        }, { once: true });
        return duration + delay;
    }
}