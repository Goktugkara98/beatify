// ===================================================================================
// DOSYA ADI: AnimationService.js
// ===================================================================================
class AnimationService {
    static Z_INDEX_CONFIG = {
        AlbumArtBackgroundElement: { a: 3, b: 1 },
        CoverElement: { a: 4, b: 2 },
        default: { a: 6, b: 5 }
    };
    static CSS_CLASSES = {
        PASSIVE: 'passive',
        ANIMATION_CONTAINER_SELECTOR: '[class*="AnimationContainer"]'
    };

    // DEĞİŞTİ: constructor'a logger eklendi
    constructor(widgetElement, config, logger) {
        this.logger = logger; // YENİ
        this.widgetElement = widgetElement;
        this.config = config;
        this.animationCache = {};
        this.zIndexConfig = JSON.parse(JSON.stringify(AnimationService.Z_INDEX_CONFIG));
    }

    prepareElement(elementId, phase) {
        this.logger.info(`Element hazırlanıyor: ${elementId}, Faz: ${phase}`);
        const element = document.getElementById(elementId);
        if (!element) {
            this.logger.warn(`Element bulunamadı: ${elementId}`);
            return;
        }

        const container = element.closest(AnimationService.CSS_CLASSES.ANIMATION_CONTAINER_SELECTOR);

        element.removeAttribute('style');
        element.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);
        if (container) container.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);

        const animConfig = this.config[elementId]?.[phase];
        if (animConfig && animConfig.animation !== 'none') {
            const initialStyles = this.getInitialKeyframeStyles(animConfig.animation);
            if (initialStyles) {
                for (const propName of initialStyles) {
                    element.style.setProperty(propName, initialStyles.getPropertyValue(propName));
                }
            }
        }
        
        this._applyZIndex(elementId);
    }

    async execute(elementId, phase) {
        return new Promise(resolve => {
            const element = document.getElementById(elementId);
            const animConfig = this.config[elementId]?.[phase];

            if (!element || !animConfig || !animConfig.animation || animConfig.animation === 'none') {
                resolve();
                return;
            }
            
            this.logger.subgroup(`Animasyon Yürütülüyor: ${elementId} (${phase})`);
            const startTime = performance.now();
            const { animation, duration = 0, delay = 0 } = animConfig;
            const easing = (phase === 'transitionOut' || phase === 'outro') ? 'ease-in' : 'ease-out';

            const handleAnimationEnd = (event) => {
                if (event.target === element && event.animationName === animation) {
                    const animDuration = performance.now() - startTime;
                    this.logger.info(`Animasyon tamamlandı. Süre: ${animDuration.toFixed(2)}ms`);
                    element.removeEventListener('animationend', handleAnimationEnd);
                    this.logger.groupEnd(); // Yürütme alt grubunu kapat
                    resolve();
                }
            };

            element.addEventListener('animationend', handleAnimationEnd);
            element.style.animation = `${animation} ${duration / 1000}s ${easing} ${delay / 1000}s forwards`;
        });
    }

    cleanupElement(elementId, type) {
        this.logger.info(`Element temizleniyor: ${elementId}, Tip: ${type}`);
        const element = document.getElementById(elementId);
        if (!element) {
            this.logger.warn(`Temizlenecek element bulunamadı: ${elementId}`);
            return;
        }
        
        const container = element.closest(AnimationService.CSS_CLASSES.ANIMATION_CONTAINER_SELECTOR);
        element.removeAttribute('style'); 

        if (type === 'outgoing') {
            element.classList.add(AnimationService.CSS_CLASSES.PASSIVE);
            if (container) container.classList.add(AnimationService.CSS_CLASSES.PASSIVE);
        } else {
            element.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);
            if (container) container.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);
            this._applyZIndex(elementId); 
        }
    }
    
    getInitialKeyframeStyles(animationName) {
        if (this.animationCache[animationName]) return this.animationCache[animationName];

        for (const sheet of document.styleSheets) {
            try {
                const rules = sheet.cssRules || sheet.rules;
                for (const rule of rules) {
                    if (rule.type === CSSRule.KEYFRAMES_RULE && rule.name === animationName) {
                        for (const keyframe of rule.cssRules) {
                            if (keyframe.keyText === '0%' || keyframe.keyText === 'from') {
                                this.animationCache[animationName] = keyframe.style;
                                return keyframe.style;
                            }
                        }
                    }
                }
            } catch (e) { /* CORS hatalarını yoksay */ }
        }
        this.animationCache[animationName] = null;
        return null;
    }

    waitForImages(elementIds) {
        const imageElements = elementIds.map(id => document.getElementById(id)).filter(el => el?.tagName === 'IMG' && el.src);
        if (imageElements.length === 0) {
            return Promise.resolve();
        }
        this.logger.info(`${imageElements.length} adet resmin yüklenmesi bekleniyor...`);
        const promises = imageElements.map(img => new Promise(resolve => {
            if (img.complete) return resolve();
            img.onload = () => resolve();
            img.onerror = () => resolve();
        }));
        return Promise.all(promises);
    }
    
    _flipZIndexes() {
        this.logger.info('z-index değerleri ters çevriliyor (flip).');
        for (const key in this.zIndexConfig) {
            [this.zIndexConfig[key].a, this.zIndexConfig[key].b] = [this.zIndexConfig[key].b, this.zIndexConfig[key].a];
        }
    }

    _applyZIndex(elementId) {
        const element = document.getElementById(elementId);
        if (!element) {
            this.logger.warn(`z-index uygulanamadı: Element bulunamadı - ${elementId}`);
            return;
        }
        const baseName = elementId.substring(0, elementId.lastIndexOf('_'));
        const setLetter = elementId.slice(-1);
        const zIndexValue = (this.zIndexConfig[baseName] || this.zIndexConfig.default)[setLetter];
        if (typeof zIndexValue !== 'undefined') {
            element.style.zIndex = zIndexValue;
        }
    }
}
