// DOSYA ADI: AnimationService.js

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

    constructor(widgetElement, config) {
        this.widgetElement = widgetElement;
        this.config = config;
        this.animationCache = {};
        this.zIndexConfig = JSON.parse(JSON.stringify(AnimationService.Z_INDEX_CONFIG));
    }

    /**
     * YENİ: Bir elementi animasyona hazırlar.
     */
    prepareElement(elementId, phase) {
        const element = document.getElementById(elementId);
        if (!element) return;

        Logger.log(`[AnimationService] HAZIRLIK BAŞLADI: ${elementId}`, 'ANIM');
        const container = element.closest(AnimationService.CSS_CLASSES.ANIMATION_CONTAINER_SELECTOR);

        element.removeAttribute('style');
        element.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);
        if (container) container.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);

        const animConfig = this.config[elementId]?.[phase];
        if (animConfig && animConfig.animation !== 'none') {
            const initialStyles = this.getInitialKeyframeStyles(animConfig.animation);
            if (initialStyles) {
                // ==========================================================
                // DEĞİŞEN KISIM BURASI
                // ==========================================================
                // Eski 'for...in' döngüsü yerine, stil nesneleri için daha güvenli olan
                // 'for...of' döngüsü ve 'setProperty' metodu kullanılıyor.
                for (const propName of initialStyles) {
                    // propName -> 'opacity', 'transform' gibi stil adlarını verir.
                    element.style.setProperty(propName, initialStyles.getPropertyValue(propName));
                }
                // ==========================================================
            }
        }
        
        this._applyZIndex(elementId);
        Logger.log(`[AnimationService] HAZIRLIK TAMAMLANDI: ${elementId}`, 'ANIM');
    }

    /**
     * "Animasyon" aşaması.
     */
    execute(elementId, phase) {
        return new Promise(resolve => {
            const element = document.getElementById(elementId);
            const animConfig = this.config[elementId]?.[phase];

            if (!element || !animConfig || !animConfig.animation || animConfig.animation === 'none') {
                resolve();
                return;
            }
            
            Logger.log(`[AnimationService] ANİMASYON BAŞLADI: ${elementId} (${animConfig.animation})`, 'ANIM');
            const { animation, duration = 0, delay = 0 } = animConfig;
            const easing = (phase === 'transitionOut' || phase === 'outro') ? 'ease-in' : 'ease-out';

            const handleAnimationEnd = (event) => {
                if (event.target === element && event.animationName === animation) {
                    element.removeEventListener('animationend', handleAnimationEnd);
                    Logger.log(`[AnimationService] ANİMASYON TAMAMLANDI: ${elementId}`, 'ANIM');
                    resolve();
                }
            };

            element.addEventListener('animationend', handleAnimationEnd);
            element.style.animation = `${animation} ${duration / 1000}s ${easing} ${delay / 1000}s forwards`;
        });
    }

    /**
     * Bir element için animasyon sonrası temizlik yapar.
     */
    cleanupElement(elementId, type) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        Logger.log(`[AnimationService] TEMİZLİK BAŞLADI: ${elementId}`, 'ANIM');
        const container = element.closest(AnimationService.CSS_CLASSES.ANIMATION_CONTAINER_SELECTOR);
        element.removeAttribute('style'); 

        if (type === 'outgoing') {
            element.classList.add(AnimationService.CSS_CLASSES.PASSIVE);
            if (container) container.classList.add(AnimationService.CSS_CLASSES.PASSIVE);
        } else { // incoming
            element.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);
            if (container) container.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);
            this._applyZIndex(elementId); 
        }
        Logger.log(`[AnimationService] TEMİZLİK TAMAMLANDI: ${elementId}`, 'ANIM');
    }
    
    // Diğer yardımcı metotlar (Bunlar aynı kalmalı)
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