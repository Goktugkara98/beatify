class AnimationService {
    constructor(widgetElement, themeService, cssParser) {
        this.widgetElement = widgetElement;
        this.themeService = themeService;
        this.cssParser = cssParser;
    }

    _applyZIndexes(set, state) {
        const zIndexConfig = this.themeService.themeData.definitions?.zIndex;
        if (!zIndexConfig) {
            return;
        }

        const zIndexStateData = zIndexConfig[state];
        if (!zIndexStateData) {
            return;
        }

        Object.keys(zIndexStateData).forEach(elementBaseName => {
            const elementClassName = `${elementBaseName}_${set}`;
            const zIndexValue = zIndexStateData[elementBaseName];
            
            if (zIndexValue !== undefined) {
                const element = this.widgetElement.querySelector(`.${elementClassName}`);
                if (element) {
                    element.style.zIndex = zIndexValue;
                }
            }
        });
    }

    _cleanupAnimationStyles(element) {
        element.style.animation = '';
        element.style.opacity = '';
        element.style.transform = '';
    }
    
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

    async playIntro() {
        if (!this.themeService || !this.themeService.themeData) {
            return;
        }
    
        this._applyZIndexes('a', 'active');
    
        const animatedElements = [];
        Object.keys(this.themeService.themeData.components).forEach(componentName => {
            const setData = this.themeService.getComponentSetData(componentName, 'a');
            const introAnim = setData?.animations?.intro;
            if (introAnim) {
                const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                if (element) {
                    animatedElements.push(element);
                }
            }
        });
    
        // --- YENİ EKLENEN ADIMLAR ---
        // 1. Animasyonlu tüm elementleri animasyon başlamadan önce manuel olarak gizle.
        animatedElements.forEach(element => {
            element.style.opacity = '0';
        });
    
        // 2. Tarayıcının bu stilleri uygulaması için bir kare bekle.
        await new Promise(resolve => requestAnimationFrame(resolve));
        // --- YENİ EKLENEN ADIMLARIN SONU ---
    
        // 3. Artık içi boşaltılmış/gizlenmiş elementlerle ana widget'ı görünür yap.
        this.widgetElement.classList.remove('widget-inactive');
    
        // Mevcut kodun geri kalanı büyük ölçüde aynı kalabilir.
        // CSS Parser ile başlangıç stili alma adımı artık daha az kritik.
        let maxDuration = 0;
    
        animatedElements.forEach(element => {
            const componentName = this._findComponentNameByElement(element);
            if (!componentName) return;
    
            const setData = this.themeService.getComponentSetData(componentName, 'a');
            const animProps = setData.animations.intro;
    
            element.style.animation = `${animProps.animation} ${animProps.duration}ms ease-out ${animProps.delay}ms both`;
    
            const totalTime = (animProps.delay || 0) + (animProps.duration || 0);
            if (totalTime > maxDuration) {
                maxDuration = totalTime;
            }
        });
    
        if (maxDuration > 0) {
            await new Promise(resolve => setTimeout(resolve, maxDuration));
        }
    
        // Animasyon sonrası temizlik stilini koru.
        animatedElements.forEach(element => {
            this._cleanupAnimationStyles(element);
            // ÖNEMLİ: Opacity'yi temizlediğimiz için eski haline getirmemiz gerekebilir.
            // Ancak 'both' fill mode ve sonrasında yapılan cleanup bunu zaten yönetiyor olmalı.
            // Eğer animasyon sonrası elementler kayboluyorsa, cleanup'tan opacity'yi çıkarın.
        });
    }

    async playTransition({ activeSet, passiveSet }) {
        if (!this.themeService?.themeData) {
            return;
        }
    
        const activeContainer = this.widgetElement.querySelector(`.WidgetContainer_${activeSet}`);
        const passiveContainer = this.widgetElement.querySelector(`.WidgetContainer_${passiveSet}`);
    
        if (!activeContainer || !passiveContainer) {
            return;
        }
    
        this._applyZIndexes(passiveSet, 'passive');
        this._applyZIndexes(activeSet, 'active');
    
        passiveContainer.classList.remove('passive');
        passiveContainer.style.zIndex = 2;
        activeContainer.style.zIndex = 1;
    
        const animatedElements = [];
        const animationPromises = [];
    
        Object.keys(this.themeService.themeData.components).forEach(componentName => {
            const setData = this.themeService.getComponentSetData(componentName, activeSet);
            const transitionOutAnim = setData?.animations?.transitionOut;
            if (transitionOutAnim?.animation !== 'none') {
                const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                if (element) {
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
                    const initialStyle = this.cssParser.getInitialStyle(transitionInAnim.animation);
                    if (initialStyle) Object.assign(element.style, initialStyle);
                    animatedElements.push({ element, animation: transitionInAnim, cleanup: true });
                }
            }
        });
    
        await new Promise(resolve => requestAnimationFrame(resolve));
    
        let maxDuration = 0;
        animatedElements.forEach(({ element, animation }) => {
            // DEĞİŞİKLİK: 'forwards' yerine 'both' kullanıyoruz.
            element.style.animation = `${animation.animation} ${animation.duration}ms ease-out ${animation.delay}ms both`;
            const totalTime = (animation.delay || 0) + (animation.duration || 0);
            if (totalTime > maxDuration) maxDuration = totalTime;
        });
    
        if (maxDuration > 0) {
            await new Promise(resolve => setTimeout(resolve, maxDuration));
        }
    
        activeContainer.classList.add('passive');
    
        animatedElements.forEach(({ element, cleanup }) => {
            if (cleanup) this._cleanupAnimationStyles(element);
        });
    
        activeContainer.style.zIndex = '';
        passiveContainer.style.zIndex = '';
    }

    async playOutro() {
        if (!this.themeService?.themeData) {
            return;
        }
        
        const animatedElements = [];
        const activeSet = this.widgetElement.querySelector('.WidgetContainer_a.passive') ? 'b' : 'a';
        
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
        
        this.widgetElement.classList.add('widget-inactive');
        
        await new Promise(resolve => requestAnimationFrame(resolve));
        
        let maxDuration = 0;
        animatedElements.forEach(({element, animation}) => {
            // DEĞİŞİKLİK: 'forwards' yerine 'both' kullanıyoruz.
            element.style.animation = `${animation.animation} ${animation.duration}ms ease-out ${animation.delay}ms both`;
            
            const totalTime = (animation.delay || 0) + (animation.duration || 0);
            if (totalTime > maxDuration) {
                maxDuration = totalTime;
            }
        });
        
        if (maxDuration > 0) {
            await new Promise(resolve => setTimeout(resolve, maxDuration));
        }
        
        animatedElements.forEach(({element, cleanup}) => {
            if (cleanup) {
                this._cleanupAnimationStyles(element);
            }
        });
    }
}