// DOSYA ADI: AnimationService.js
class AnimationService {
    // Animasyonla ilgili statik yapılandırmalar buraya taşındı
    static Z_INDEX_CONFIG = {
        AlbumArtBackgroundElement: { a: 3, b: 1 },
        CoverElement: { a: 4, b: 2 },
        default: { a: 6, b: 5 }
    };
    static CSS_CLASSES = {
        PASSIVE: 'passive',
        ANIMATION_CONTAINER_SELECTOR: '[class*="AnimationContainer"]'
    };

    constructor(widgetElement, config) {
        this.widgetElement = widgetElement;
        this.config = config;
        this.animationCache = {};
        // Her servis örneği için z-index yapılandırmasının bir kopyasını oluştur
        this.zIndexConfig = JSON.parse(JSON.stringify(AnimationService.Z_INDEX_CONFIG));
    }

    /**
     * Bir şarkıdan diğerine geçiş için tam animasyon sekansını yönetir.
     * @param {string} activeSet - Dışarı çıkan set.
     * @param {string} passiveSet - İçeri giren set.
     */
    async runTransitionSequence(activeSet, passiveSet) {
        this._flipZIndexes();

        const outgoingElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
        const incomingElementIds = this.config.elements.filter(id => id.endsWith(`_${passiveSet}`));

        incomingElementIds.forEach(id => this._setElementState(id, 'prepared', 'transitionIn'));
        outgoingElementIds.forEach(id => this._setElementState(id, 'active'));
        
        const imageElementIds = incomingElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG');
        await this.waitForImages(imageElementIds);

        console.log(`[AnimationService] Geçiş başlıyor: ${activeSet} -> ${passiveSet}`);
        const outgoingAnimations = outgoingElementIds.map(id => this.execute(id, 'transitionOut'));
        const incomingAnimations = incomingElementIds.map(id => this.execute(id, 'transitionIn'));

        await Promise.all([...outgoingAnimations, ...incomingAnimations]);
        console.log("[AnimationService] Geçiş animasyonları tamamlandı.");

        // Temizlik
        outgoingElementIds.forEach(id => this._setElementState(id, 'passive'));
        incomingElementIds.forEach(id => this._setElementState(id, 'active')); // stilleri temizle
    }

    /**
     * Promise tabanlı, merkezi animasyon fonksiyonu.
     * @param {string} elementId - Animasyon uygulanacak elementin ID'si.
     * @param {string} phase - Animasyon fazı ('intro', 'transitionIn', 'transitionOut').
     * @returns {Promise<void>} Animasyon tamamlandığında resolve olan bir Promise.
     */
    execute(elementId, phase) {
        return new Promise(resolve => {
            const element = document.getElementById(elementId);
            const animConfig = this.config[elementId]?.[phase];

            if (!element || !animConfig || !animConfig.animation || animConfig.animation === 'none') {
                resolve();
                return;
            }
            
            const { animation, duration = 0, delay = 0 } = animConfig;
            const easing = (phase === 'transitionOut' || phase === 'outro') ? 'ease-in' : 'ease-out';

            const handleAnimationEnd = (event) => {
                if (event.animationName === animation) {
                    element.removeEventListener('animationend', handleAnimationEnd);
                    resolve();
                }
            };

            element.addEventListener('animationend', handleAnimationEnd);
            element.style.animation = `${animation} ${duration / 1000}s ${easing} ${delay / 1000}s both`;
        });
    }

    _setElementState(elementId, state, phaseForPreparation) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const container = element.closest(AnimationService.CSS_CLASSES.ANIMATION_CONTAINER_SELECTOR);
        element.removeAttribute('style');
        
        if (state === 'passive') {
            element.classList.add(AnimationService.CSS_CLASSES.PASSIVE);
            if (container) container.classList.add(AnimationService.CSS_CLASSES.PASSIVE);
        } else {
            element.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);
            if (container) container.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);

            if (state === 'prepared' && phaseForPreparation) {
                const animConfig = this.config[elementId]?.[phaseForPreparation];
                if (animConfig) {
                    const initialStyles = this.getInitialKeyframeStyles(animConfig.animation);
                    if (initialStyles) {
                        for (const prop of initialStyles) {
                            element.style[prop] = initialStyles[prop];
                        }
                    }
                }
            }
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
        if (imageElements.length === 0) return Promise.resolve();
        const promises = imageElements.map(img => new Promise(resolve => {
            if (img.complete) return resolve();
            img.onload = () => resolve();
            img.onerror = () => resolve();
        }));
        return Promise.all(promises);
    }
    
    _flipZIndexes() {
        for (const key in this.zIndexConfig) {
            [this.zIndexConfig[key].a, this.zIndexConfig[key].b] = [this.zIndexConfig[key].b, this.zIndexConfig[key].a];
        }
    }

    _applyZIndex(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        const baseName = elementId.substring(0, elementId.lastIndexOf('_'));
        const setLetter = elementId.slice(-1);
        const zIndexValue = (this.zIndexConfig[baseName] || this.zIndexConfig.default)[setLetter];
        if (typeof zIndexValue !== 'undefined') {
            element.style.zIndex = zIndexValue;
        }
    }
}