class GSAPAnimationService {
    constructor(widgetElement, themeService) {
        this.widgetElement = widgetElement;
        this.themeService = themeService;
        this.activeAnimations = {
            intro: null,
            outro: null,
            transition: null
        };
        this.currentState = {
            activeSet: null,
            isAnimating: false
        };
    }

    async playIntro({ set }) {
        if (!this.themeService?.themeData) {
            return null;
        }

        this._killAnimation('intro');
        this._killAnimation('outro');

        this.currentState.activeSet = set;
        this.currentState.isAnimating = true;

        try {
            this._applyZIndexes(set, 'active');

            const container = this.widgetElement.querySelector(`.WidgetContainer_${set}`);
            if (!container) return null;

            const tl = gsap.timeline({
                id: 'intro',
                onComplete: () => {
                    this.currentState.isAnimating = false;
                },
                onInterrupt: () => {
                    this.currentState.isAnimating = false;
                }
            });

            this.activeAnimations.intro = tl;

            const components = this.themeService.themeData.components;

            Object.entries(components).forEach(([componentName, componentData]) => {
                const setData = componentData[`set_${set}`];
                const introAnim = setData?.animations?.intro;

                if (introAnim && introAnim.animation !== 'none') {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (!element) return;
                    
                    // İlk yükleme durumu: Elementi görünür yap ama opacity 0'dan başlat (fade efekti için)
                    // Diğer efektler için de benzer şekilde başlangıç state'ini ayarla
                    // Bunu _addAnimationToTimeline içinde yapıyoruz ama burada container'ın görünür olduğunu garanti edelim.
                    container.style.opacity = '1';
                    container.style.visibility = 'visible';

                    this._addAnimationToTimeline(tl, element, introAnim, 0, componentName);
                }
            });

            // Eğer timeline boşsa bile çalıştır ki onComplete tetiklensin
            if (tl.duration() === 0) {
                // Küçük bir delay ekle ki render cycle yetişsin
                tl.to({}, { duration: 0.1 });
            }

            return tl;
        } catch (error) {
            if (window.WidgetDebug) window.WidgetDebug.error("Intro animasyon hatası:", error);
            this.currentState.isAnimating = false;
            return null;
        }
    }

    async playOutro() {
        if (!this.themeService?.themeData) {
            return null;
        }

        this._killAnimation('intro');
        this._killAnimation('outro');

        const activeSet = this.currentState.activeSet ||
            (this.widgetElement.querySelector('.WidgetContainer_a.passive') ? 'b' : 'a');

        this.currentState.isAnimating = true;

        try {
            const container = this.widgetElement.querySelector(`.WidgetContainer_${activeSet}`);
            if (!container) return null;

            const tl = gsap.timeline({
                id: 'outro',
                onComplete: () => {
                    this.currentState.isAnimating = false;
                },
                onInterrupt: () => {
                    this.currentState.isAnimating = false;
                }
            });

            this.activeAnimations.outro = tl;

            const components = this.themeService.themeData.components;

            Object.entries(components).forEach(([componentName, componentData]) => {
                const setData = componentData[`set_${activeSet}`];
                const outroAnim = setData?.animations?.outro;

                if (outroAnim && outroAnim.animation !== 'none') {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (!element) return;
                    this._addAnimationToTimeline(tl, element, outroAnim, 0, componentName);
                }
            });

            return tl;
        } catch (error) {
            if (window.WidgetDebug) window.WidgetDebug.error("Outro animasyon hatası:", error);
            this.currentState.isAnimating = false;
            return null;
        }
    }

    async playTransition({ activeSet, passiveSet }) {
        return new Promise((resolve) => {
            if (!this.themeService?.themeData) {
                resolve(null);
                return;
            }
    
            const activeContainer = this.widgetElement.querySelector(`.WidgetContainer_${activeSet}`);
            const passiveContainer = this.widgetElement.querySelector(`.WidgetContainer_${passiveSet}`);
    
            if (!activeContainer || !passiveContainer) {
                resolve(null);
                return;
            }
    
            this._killAnimation('transition');
            this.currentState.activeSet = passiveSet;
            this.currentState.isAnimating = true;
    
            // --- YENİ MANTIK BAŞLANGICI ---
            // Güvenlik: class state bozulduysa (ör. aktif set yanlışlıkla passive kaldıysa)
            // transitionOut başlamadan "flash" gibi kaybolmasın.
            activeContainer.classList.remove('passive');
            activeContainer.style.opacity = '1';
            activeContainer.style.visibility = 'visible';

            passiveContainer.style.zIndex = '2';
            activeContainer.style.zIndex = '1';
    
            passiveContainer.classList.add('active');
            passiveContainer.classList.remove('passive');
            // Container görünür olduğundan emin ol
            passiveContainer.style.opacity = '1';
            passiveContainer.style.visibility = 'visible';
    
            activeContainer.classList.remove('active');
            // --- YENİ MANTIK SONU ---
    
            const tl = gsap.timeline({
                id: 'transition',
                onComplete: () => {
                    this.currentState.isAnimating = false;
    
                    // --- YENİ MANTIK: TEMİZLİK ---
                    activeContainer.classList.add('passive');
    
                    activeContainer.style.zIndex = '';
                    passiveContainer.style.zIndex = '';
    
                    resolve(tl);
                },
                onInterrupt: () => {
                    this.currentState.isAnimating = false;
                    resolve(null);
                }
            });
    
            this.activeAnimations.transition = tl;
            const components = this.themeService.themeData.components;
    
            // Transition Out (Eski elemanlar)
            Object.entries(components).forEach(([componentName, componentData]) => {
                const setData = componentData[`set_${activeSet}`];
                const outroAnim = setData?.animations?.transitionOut;
    
                if (outroAnim && outroAnim.animation !== 'none') {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (element) {
                        this._addAnimationToTimeline(tl, element, outroAnim, 0, componentName);
                    }
                }
            });
    
            // Transition In (Yeni elemanlar)
            Object.entries(components).forEach(([componentName, componentData]) => {
                const setData = componentData[`set_${passiveSet}`];
                const introAnim = setData?.animations?.transitionIn;
    
                if (introAnim && introAnim.animation !== 'none') {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (element) {
                        this._addAnimationToTimeline(tl, element, introAnim, '<', componentName);
                    }
                }
            });
    
            if (tl.duration() === 0) {
                tl.progress(1).kill();
            }
        });
    }
    
    destroy() {
        Object.keys(this.activeAnimations).forEach(type => {
            this._killAnimation(type);
        });

        this.currentState = {
            activeSet: null,
            isAnimating: false
        };
    }

    isAnimating() {
        return this.currentState.isAnimating;
    }

    getActiveSet() {
        return this.currentState.activeSet;
    }

    _killAnimation(type) {
        if (this.activeAnimations[type]) {
            this.activeAnimations[type].kill();
            this.activeAnimations[type] = null;
        }
    }

    _applyZIndexes(set, state) {
        const container = this.widgetElement.querySelector(`.WidgetContainer_${set}`);
        if (!container) return;

        container.style.zIndex = state === 'active' ? '2' : '1';
        container.classList.toggle('active', state === 'active');
        container.classList.toggle('passive', state === 'passive');
        
        // Görünürlük kontrolü
        if (state === 'active') {
            container.style.opacity = '1';
            container.style.visibility = 'visible';
        }
    }

    _addAnimationToTimeline(timeline, element, animConfig, position = 0, componentName = 'Unknown') {
        if (!element || !animConfig) {
            return;
        }
    
        const {
            type: animation = 'fade',
            duration = 300,
            delay = 0,
            ease = 'power1.out'
        } = animConfig;
    
        const durationSec = duration / 1000;
        const delaySec = delay / 1000;
        const validEase = ease === 'none' ? 'linear' : ease;
    
        // Görünürlük ayarları - Elementin kendisi için
        gsap.set(element, { visibility: 'visible' });
    
        switch (animation) {
            case 'fade-in':
            case 'fade':
                // Sadece opacity: Presetler ease + from/to opacity ile farklılaştırılabilir.
                // Default: 0 -> 1
                const fadeInFrom = typeof animConfig.fromOpacity === 'number' ? animConfig.fromOpacity : 0;
                const fadeInTo = typeof animConfig.toOpacity === 'number' ? animConfig.toOpacity : 1;
                timeline.fromTo(
                    element,
                    { opacity: fadeInFrom },
                    { opacity: fadeInTo, duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            case 'slide-up':
                timeline.fromTo(element, { y: '100%', opacity: 0 }, { y: 0, opacity: 1, duration: durationSec, delay: delaySec, ease: validEase }, position);
                break;
            case 'slide-down':
                timeline.fromTo(element, { y: '-100%', opacity: 0 }, { y: 0, opacity: 1, duration: durationSec, delay: delaySec, ease: validEase }, position);
                break;
            case 'slide-left':
                timeline.fromTo(element, { x: '100%', opacity: 0 }, { x: 0, opacity: 1, duration: durationSec, delay: delaySec, ease: validEase }, position);
                break;
            case 'slide-right':
                timeline.fromTo(element, { x: '-100%', opacity: 0 }, { x: 0, opacity: 1, duration: durationSec, delay: delaySec, ease: validEase }, position);
                break;
            case 'zoom-in-soft':
                timeline.fromTo(
                    element,
                    { scale: 0.9, opacity: 0 },
                    { scale: 1, opacity: 1, duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            case 'zoom-out-soft':
                timeline.fromTo(
                    element,
                    { scale: 1.05, opacity: 0 },
                    { scale: 1, opacity: 1, duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            case 'float-up':
                timeline.fromTo(
                    element,
                    { y: 16, opacity: 0 },
                    { y: 0, opacity: 1, duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            case 'float-badge':
                timeline.fromTo(
                    element,
                    { y: 10, scale: 0.9, opacity: 0 },
                    { y: 0, scale: 1, opacity: 1, duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            case 'blur-in':
                timeline.fromTo(
                    element,
                    { filter: 'blur(18px)', opacity: 0 },
                    { filter: 'blur(0px)', opacity: 1, duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            case 'tilt-in':
                timeline.fromTo(
                    element,
                    { rotationY: -8, y: 12, opacity: 0, transformOrigin: 'center center' },
                    { rotationY: 0, y: 0, opacity: 1, duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            case 'card-pop':
                // Küçük bir pop efekti: önce hafif büyü, sonra normale dön
                timeline.fromTo(
                    element,
                    { scale: 0.94, opacity: 0 },
                    { scale: 1.02, opacity: 1, duration: durationSec * 0.7, delay: delaySec, ease: validEase },
                    position
                );
                timeline.to(
                    element,
                    { scale: 1, duration: Math.max(0.1, durationSec * 0.3), ease: 'power2.out' },
                    '>'
                );
                break;
            case 'underline-sweep':
                timeline.fromTo(
                    element,
                    { scaleX: 0, opacity: 0.2, transformOrigin: 'left center' },
                    { scaleX: 1, opacity: 1, duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            case 'clip-up':
                timeline.fromTo(
                    element,
                    { y: 16, opacity: 0, clipPath: 'inset(100% 0 0 0)' },
                    { y: 0, opacity: 1, clipPath: 'inset(0 0 0 0)', duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            case 'clip-left':
                timeline.fromTo(
                    element,
                    { x: 16, opacity: 0, clipPath: 'inset(0 0 0 100%)' },
                    { x: 0, opacity: 1, clipPath: 'inset(0 0 0 0)', duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            
            // Çıkış animasyonları
            case 'fade-out':
                // Default: -> 0
                if (typeof animConfig.fromOpacity === 'number') {
                    gsap.set(element, { opacity: animConfig.fromOpacity });
                }
                const fadeOutTo = typeof animConfig.toOpacity === 'number' ? animConfig.toOpacity : 0;
                timeline.to(element, { opacity: fadeOutTo, duration: durationSec, delay: delaySec, ease: validEase }, position);
                break;
            case 'blur-fade-out':
                timeline.to(
                    element,
                    { filter: 'blur(14px)', opacity: 0, duration: durationSec, delay: delaySec, ease: validEase },
                    position
                );
                break;
            case 'slide-up-out':
                timeline.to(element, { y: '-100%', opacity: 0, duration: durationSec, delay: delaySec, ease: validEase }, position);
                break;
            case 'slide-down-out':
                timeline.to(element, { y: '100%', opacity: 0, duration: durationSec, delay: delaySec, ease: validEase }, position);
                break;
            case 'slide-left-out':
                timeline.to(element, { x: '-100%', opacity: 0, duration: durationSec, delay: delaySec, ease: validEase }, position);
                break;
            case 'slide-right-out':
                timeline.to(element, { x: '100%', opacity: 0, duration: durationSec, delay: delaySec, ease: validEase }, position);
                break;

            case 'none':
            default:
                 // Animasyon yoksa bile görünür yap
                 gsap.set(element, { opacity: 1 });
                 if (window.WidgetDebug && animation !== 'none') {
                      window.WidgetDebug.warn(`Bilinmeyen animasyon: ${animation} (${componentName})`);
                 }
                break;
        }
    }
}

window.GSAPAnimationService = GSAPAnimationService;
