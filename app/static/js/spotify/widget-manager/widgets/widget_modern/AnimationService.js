/**
 * @file AnimationService.js
 * @description Widget için CSS animasyonlarını ve z-index'i yönetir.
 */
class AnimationService {
    constructor(widgetElement, themeService, cssParser) {
        this.widgetElement = widgetElement;
        this.themeService = themeService;
        this.cssParser = cssParser;
    }

    // YARDIMCI METOT: z-index'leri uygular
    _applyZIndexes(set, state) {
        const zIndexConfig = this.themeService.themeData.definitions?.zIndex;
        if (!zIndexConfig) {
            console.warn('Z-Index konfigürasyonu bulunamadı.');
            return;
        }

        const zIndexStateData = zIndexConfig[state];
        if (!zIndexStateData) {
            console.warn(`Z-Index state verisi bulunamadı: ${state}`);
            return;
        }

        // Tüm elementleri dolaş
        Object.keys(zIndexStateData).forEach(elementBaseName => {
            // Element adını set bilgisine göre güncelle (örn: 'CoverElement' -> 'CoverElement_a')
            const elementClassName = `${elementBaseName}_${set}`;
            const zIndexValue = zIndexStateData[elementBaseName];
            
            if (zIndexValue !== undefined) {
                const element = this.widgetElement.querySelector(`.${elementClassName}`);
                if (element) {
                    element.style.zIndex = zIndexValue;
                    console.log(`[Z-Index] ${elementClassName} (${state}): ${zIndexValue}`);
                } else {
                    console.warn(`[Z-Index] Element bulunamadı: ${elementClassName}`);
                }
            }
        });
    }

    // YARDIMCI METOT: Sadece animasyonla ilgili stilleri temizler
    _cleanupAnimationStyles(element) {
        element.style.animation = '';
        element.style.opacity = '';
        element.style.transform = '';
    }
    
    // YARDIMCI METOT: Element'ten bileşen adını bulur
    _findComponentNameByElement(element) {
        const components = this.themeService.themeData.components;
        for (const componentName in components) {
            const setData = components[componentName].set_a || components[componentName].set_b;
            if (setData && element.classList.contains(setData.animationContainer)) {
                return componentName;
            }
        }
        return null;
    }

    playIntro() {
        if (!this.themeService || !this.themeService.themeData) {
            console.error("HATA: AnimationService içinde themeService veya themeData bulunamadı!");
            return;
        }

        console.log('%c[AnimationService] playIntro tetiklendi.', 'color: green; font-weight: bold;');
        
        this._applyZIndexes('a', 'active');

        const animatedElements = [];
        Object.keys(this.themeService.themeData.components).forEach(componentName => {
            const setData = this.themeService.getComponentSetData(componentName, 'a');
            const introAnim = setData?.animations?.intro;
            if (introAnim) {
                const initialStyle = this.cssParser.getInitialStyle(introAnim.animation);
                if (initialStyle) {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (element) {
                        Object.assign(element.style, initialStyle);
                        animatedElements.push(element);
                    }
                }
            }
        });
        
        this.widgetElement.classList.remove('widget-inactive');
        let maxDuration = 0;

        requestAnimationFrame(() => {
            animatedElements.forEach(element => {
                const componentName = this._findComponentNameByElement(element);
                if (!componentName) return;

                const setData = this.themeService.getComponentSetData(componentName, 'a');
                const animProps = setData.animations.intro;
                element.style.animation = `${animProps.animation} ${animProps.duration}ms ease-out ${animProps.delay}ms forwards`;
                
                const totalTime = (animProps.delay || 0) + (animProps.duration || 0);
                if (totalTime > maxDuration) {
                    maxDuration = totalTime;
                }
            });

            setTimeout(() => {
                animatedElements.forEach(element => {
                    this._cleanupAnimationStyles(element);
                });
            }, maxDuration);
        });
    }

    async playTransition({ activeSet, passiveSet }) {
        if (!this.themeService?.themeData) {
            console.error('Theme servisi veya verisi bulunamadı');
            return;
        }

        console.log(`%c[AnimationService] Geçiş başlıyor. Aktif: ${activeSet}, Pasif: ${passiveSet}`, 'color: #FFA500; font-weight: bold;');

        // HATA DÜZELTME: Aktif sete 'active' state'i, pasif sete 'passive' state'i uygulanmalı.
        // Pasif setin (yeni gelen) z-index'i daha yüksek olmalı ki üstte görünsün.
        this._applyZIndexes(passiveSet, 'passive');
        this._applyZIndexes(activeSet, 'active');

        const activeContainer = this.widgetElement.querySelector(`.WidgetContainer_${activeSet}`);
        const passiveContainer = this.widgetElement.querySelector(`.WidgetContainer_${passiveSet}`);

        if (!activeContainer || !passiveContainer) {
            console.error('Geçiş için gerekli containerlar bulunamadı');
            return;
        }

        console.log(`%c[Z-INDEX] ${passiveContainer.className} -> zIndex=2`, 'color: #8A2BE2;');
        passiveContainer.style.zIndex = 2;
        console.log(`%c[Z-INDEX] ${activeContainer.className} -> zIndex=1`, 'color: #8A2BE2;');
        activeContainer.style.zIndex = 1;

        activeContainer.classList.add('passive');
        passiveContainer.classList.remove('passive');

        const animatedElements = [];

        Object.keys(this.themeService.themeData.components).forEach(componentName => {
            const setData = this.themeService.getComponentSetData(componentName, activeSet);
            const transitionOutAnim = setData?.animations?.transitionOut;
            if (transitionOutAnim?.animation !== 'none') {
                const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                if (element) {
                    console.log(`%c  -> [Out Animation] ${componentName} (${activeSet}) | Anim: ${transitionOutAnim.animation}`, 'color: #FF6347');
                    const initialStyle = this.cssParser.getInitialStyle(transitionOutAnim.animation);
                    if (initialStyle) Object.assign(element.style, initialStyle);
                    animatedElements.push({ element, animation: transitionOutAnim, cleanup: true });
                }
            }
        });

        Object.keys(this.themeService.themeData.components).forEach(componentName => {
            const setData = this.themeService.getComponentSetData(componentName, passiveSet);
            const transitionInAnim = setData?.animations?.transitionIn;
            if (transitionInAnim?.animation !== 'none') {
                const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                if (element) {
                    console.log(`%c  -> [In Animation] ${componentName} (${passiveSet}) | Anim: ${transitionInAnim.animation}`, 'color: #32CD32');
                    const initialStyle = this.cssParser.getInitialStyle(transitionInAnim.animation);
                    if (initialStyle) Object.assign(element.style, initialStyle);
                    animatedElements.push({ element, animation: transitionInAnim, cleanup: true });
                }
            }
        });

        await new Promise(resolve => requestAnimationFrame(resolve));

        let maxDuration = 0;
        animatedElements.forEach(({ element, animation }) => {
            element.style.animation = `${animation.animation} ${animation.duration}ms ease-out ${animation.delay}ms forwards`;
            const totalTime = (animation.delay || 0) + (animation.duration || 0);
            if (totalTime > maxDuration) maxDuration = totalTime;
        });

        if (maxDuration > 0) {
            await new Promise(resolve => setTimeout(resolve, maxDuration));
        }

        animatedElements.forEach(({ element, cleanup }) => {
            if (cleanup) this._cleanupAnimationStyles(element);
        });

        console.log(`%c[Z-INDEX] Temizleniyor: ${activeContainer.className} ve ${passiveContainer.className}`, 'color: #8A2BE2;');
        activeContainer.style.zIndex = '';
        passiveContainer.style.zIndex = '';

        console.log('%c[AnimationService] Geçiş tamamlandı.', 'color: #FFA500; font-weight: bold;');
    }

    async playOutro() {
        if (!this.themeService?.themeData) {
            console.error('Theme servisi veya verisi bulunamadı');
            return;
        }
        
        console.log('[AnimationService] Çıkış animasyonu başlatılıyor...');
        
        // Tüm setler için çıkış animasyonlarını topla
        const animatedElements = [];
        const activeSet = this.widgetElement.querySelector('.WidgetContainer_a.passive') ? 'b' : 'a';
        
        // Aktif set için çıkış animasyonlarını uygula
        Object.keys(this.themeService.themeData.components).forEach(componentName => {
            const setData = this.themeService.getComponentSetData(componentName, activeSet);
            const outroAnim = setData?.animations?.outro;
            
            if (outroAnim?.animation !== 'none') {
                const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                if (element) {
                    const initialStyle = this.cssParser?.getInitialStyle?.(outroAnim.animation) || {};
                    Object.assign(element.style, initialStyle);
                    animatedElements.push({
                        element,
                        animation: outroAnim,
                        cleanup: true
                    });
                }
            }
        });
        
        // Widget'ı görünmez yap
        this.widgetElement.classList.add('widget-inactive');
        
        // Animasyonları başlat
        await new Promise(resolve => requestAnimationFrame(resolve));
        
        let maxDuration = 0;
        animatedElements.forEach(({element, animation}) => {
            element.style.animation = `${animation.animation} ${animation.duration}ms ease-out ${animation.delay}ms forwards`;
            
            const totalTime = (animation.delay || 0) + (animation.duration || 0);
            if (totalTime > maxDuration) {
                maxDuration = totalTime;
            }
        });
        
        // Animasyonların bitmesini bekle
        if (maxDuration > 0) {
            await new Promise(resolve => setTimeout(resolve, maxDuration));
        }
        
        // Temizlik
        animatedElements.forEach(({element, cleanup}) => {
            if (cleanup) {
                this._cleanupAnimationStyles(element);
            }
        });
        
        console.log('[AnimationService] Çıkış animasyonu tamamlandı');
    }
}