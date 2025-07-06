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
                    // DÜZELTİLDİ: componentName parametresi eklendi
                    this._addAnimationToTimeline(tl, element, introAnim, 0, componentName);
                }
            });

            return tl;
        } catch (error) {
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
                    // DÜZELTİLDİ: componentName parametresi eklendi
                    this._addAnimationToTimeline(tl, element, outroAnim, 0, componentName);
                }
            });

            return tl;
        } catch (error) {
            this.currentState.isAnimating = false;
            return null;
        }
    }

    async playTransition({ activeSet, passiveSet }) {
        if (!this.themeService?.themeData) {
            return null;
        }

        const activeContainer = this.widgetElement.querySelector(`.WidgetContainer_${activeSet}`);
        const passiveContainer = this.widgetElement.querySelector(`.WidgetContainer_${passiveSet}`);

        if (!activeContainer || !passiveContainer) return null;

        this._killAnimation('transition');

        this.currentState.activeSet = passiveSet;
        this.currentState.isAnimating = true;

        try {
            this._applyZIndexes(passiveSet, 'active');
            this._applyZIndexes(activeSet, 'passive');

            const tl = gsap.timeline({
                id: 'transition',
                onComplete: () => {
                    this.currentState.isAnimating = false;
                },
                onInterrupt: () => {
                    this.currentState.isAnimating = false;
                }
            });

            this.activeAnimations.transition = tl;

            const components = this.themeService.themeData.components;

            // Transition Out (Eski elemanlar)
            Object.entries(components).forEach(([componentName, componentData]) => {
                const setData = componentData[`set_${activeSet}`];
                const outroAnim = setData?.animations?.transitionOut; // transitionOut kullanıldı

                if (outroAnim && outroAnim.animation !== 'none') {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (!element) return;
                     // DÜZELTİLDİ: componentName parametresi eklendi
                    this._addAnimationToTimeline(tl, element, outroAnim, 0, componentName);
                }
            });

            // Transition In (Yeni elemanlar)
            Object.entries(components).forEach(([componentName, componentData]) => {
                const setData = componentData[`set_${passiveSet}`];
                const introAnim = setData?.animations?.transitionIn; // transitionIn kullanıldı

                if (introAnim && introAnim.animation !== 'none') {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (!element) return;
                    // DÜZELTİLDİ: componentName parametresi eklendi ve pozisyon korunuyor
                    this._addAnimationToTimeline(tl, element, introAnim, '<', componentName);
                }
            });

            return tl;
        } catch (error) {
            this.currentState.isAnimating = false;
            return null;
        }
    }
    
    // ... Diğer fonksiyonlar (destroy, isAnimating vs.) olduğu gibi kalabilir ...
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
    }

    // DÜZELTİLDİ: Fonksiyon imzası ve loglama
    _addAnimationToTimeline(timeline, element, animConfig, position = 0, componentName = 'Unknown') {
        if (!element || !animConfig) {
            return;
        }

        const {
            type: animation = 'fade',
            duration = 300,
            delay = 0,
            ease = 'power1.out' // Varsayılan 'power1.out'
        } = animConfig;

        // --- LOGLAMA KODU ---
        console.log(`[Animation Log] Component: ${componentName} | Ease: ${ease}`);
        // --------------------

        const durationSec = duration / 1000;
        const delaySec = delay / 1000;

        switch (animation) {
            case 'fade-in':
            case 'fade':
                timeline.fromTo(element, { opacity: 0 }, {
                    opacity: 1,
                    duration: durationSec,
                    delay: delaySec,
                    ease: ease
                }, position);
                break;
            case 'slide-up':
                timeline.fromTo(element, { y: '100%', opacity: 0 }, {
                    y: 0,
                    opacity: 1,
                    duration: durationSec,
                    delay: delaySec,
                    ease: ease
                }, position);
                break;
            case 'slide-down':
                timeline.fromTo(element, { y: '-100%', opacity: 0 }, {
                    y: 0,
                    opacity: 1,
                    duration: durationSec,
                    delay: delaySec,
                    ease: ease
                }, position);
                break;
            case 'slide-left':
                timeline.fromTo(element, { x: '100%', opacity: 0 }, {
                    x: 0,
                    opacity: 1,
                    duration: durationSec,
                    delay: delaySec,
                    ease: ease
                }, position);
                break;
            case 'slide-right':
                timeline.fromTo(element, { x: '-100%', opacity: 0 }, {
                    x: 0,
                    opacity: 1,
                    duration: durationSec,
                    delay: delaySec,
                    ease: ease
                }, position);
                break;
            default:
                break;
        }
    }
}

window.GSAPAnimationService = GSAPAnimationService;