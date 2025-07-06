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
        // Bu fonksiyonu Promise tabanlı hale getirerek bir önceki adımdaki
        // zamanlama sorununu da kalıcı olarak çözelim.
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
            // 1. Z-index'leri en başta ayarla, katmanlama doğru olsun.
            passiveContainer.style.zIndex = '2';
            activeContainer.style.zIndex = '1';
    
            // 2. Gelen seti 'active' yap, 'passive' sınıfını kaldır.
            passiveContainer.classList.add('active');
            passiveContainer.classList.remove('passive');
    
            // 3. Giden setten 'active' sınıfını kaldır ama henüz 'passive' yapma!
            activeContainer.classList.remove('active');
            // --- YENİ MANTIK SONU ---
    
            const tl = gsap.timeline({
                id: 'transition',
                onComplete: () => {
                    this.currentState.isAnimating = false;
    
                    // --- YENİ MANTIK: TEMİZLİK ---
                    // 4. Animasyon BİTTİĞİNDE giden sete 'passive' sınıfını ekle.
                    activeContainer.classList.add('passive');
    
                    // 5. Stil temizliği yap, tarayıcıya bırak.
                    activeContainer.style.zIndex = '';
                    passiveContainer.style.zIndex = '';
    
                    // 6. Promise'i çözerek WidgetDOMManager'a işlemin bittiğini bildir.
                    resolve(tl);
                },
                onInterrupt: () => {
                    this.currentState.isAnimating = false;
                    resolve(null);
                }
            });
    
            this.activeAnimations.transition = tl;
            const components = this.themeService.themeData.components;
    
            // Transition Out (Eski elemanlar) - Bu kısım doğru çalışıyor
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
    
            // Transition In (Yeni elemanlar) - Bu kısım da doğru çalışıyor
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
    
            // Eğer timeline'a hiçbir animasyon eklenmediyse, hemen bitir.
            if (tl.duration() === 0) {
                tl.progress(1).kill(); // Timeline'ı manuel tamamla ve onComplete'i tetikle.
            }
        });
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
            ease = 'power1.out'
        } = animConfig;
    
        const durationSec = duration / 1000;
        const delaySec = delay / 1000;
    
        // GSAP'nin 'none' ease'ini doğru işlemesi için 'linear' kullanalım
        const validEase = ease === 'none' ? 'linear' : ease;
    
        // Mevcut pozisyondan animasyon yapmak için .to() kullanacağız.
        // .fromTo() başlangıç pozisyonunu zorla belirler, bu da 'out' animasyonları için genellikle istenmez.
        gsap.set(element, { opacity: 1 }); // Başlamadan önce elementin görünür olduğundan emin olalım.
    
        switch (animation) {
            // --- GİRİŞ ANİMASYONLARI ---
            case 'fade-in':
            case 'fade': // 'fade' 'fade-in' ile aynı işi görsün
                timeline.fromTo(element, { opacity: 0 }, { opacity: 1, duration: durationSec, delay: delaySec, ease: validEase }, position);
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
    
            // --- YENİ EKLENEN ÇIKIŞ ANİMASYONLARI ---
            case 'fade-out':
                timeline.to(element, { opacity: 0, duration: durationSec, delay: delaySec, ease: validEase }, position);
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
                // Hiçbir şey yapma
                break;
                
            default:
                // Bilinmeyen animasyon tipi için bir uyarı logu ekleyebiliriz.
                console.warn(`[GSAP Service] Bilinmeyen animasyon tipi: '${animation}' (Bileşen: ${componentName})`);
                break;
        }
    }
}

window.GSAPAnimationService = GSAPAnimationService;