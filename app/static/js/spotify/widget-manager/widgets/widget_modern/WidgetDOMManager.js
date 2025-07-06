class WidgetDOMManager {
    constructor(widgetElement, services) {
        this.widgetElement = widgetElement;
        this.stateService = services.stateService;
        this.animationService = services.animationService;
        this.contentUpdater = services.contentUpdater;
        this.errorContainer = widgetElement.querySelector('.WidgetErrorContainer');
        this.activeAnimations = [];
        this._bindEvents();
    }


    destroy() {
        this.activeAnimations.forEach(animation => {
            if (animation && typeof animation.kill === 'function') {
                animation.kill();
            }
        });
        this.activeAnimations = [];
    }

    _bindEvents() {
        this.widgetElement.addEventListener('widget:intro', (e) => this._handleIntro(e.detail));
        this.widgetElement.addEventListener('widget:outro', (e) => this._handleOutro(e.detail));
        this.widgetElement.addEventListener('widget:transition', (e) => this._handleTransition(e.detail));
        this.widgetElement.addEventListener('widget:sync', (e) => this._handleSync(e.detail));
        this.widgetElement.addEventListener('widget:error', (e) => this._handleError(e.detail));
        this.widgetElement.addEventListener('widget:clear-error', () => this._handleClearError());
    }

    async _handleIntro(detail) {
        try {
            // 1. ADIM: İçeriği doldur. Elementler zaten CSS yüzünden görünmez durumda.
            await this.contentUpdater.updateAllForSet(detail.set, detail.data);
    
            // 2. ADIM: Tarayıcının bir sonraki çizime hazırlanmasını bekle.
            await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    
            // 3. ADIM: Ana widget kapsayıcısını görünür yap.
            this.widgetElement.classList.remove('widget-inactive');
            this.widgetElement.classList.add('widget-active');
    
            // 4. ADIM: Animasyonu başlat. GSAP, CSS'teki 'opacity: 0' kuralını
            // geçersiz kılarak animasyonu başlatacaktır.
            const introAnimation = await this.animationService.playIntro({ set: detail.set });
            this.activeAnimations.push(introAnimation);
            this.contentUpdater.startProgressUpdater(detail.data, detail.set);
        } catch (error) {
            // Hata yönetimi
        }
    }

    async _handleOutro(detail) {
        try {
            const outroAnimation = await this.animationService.playOutro();
            this.activeAnimations.push(outroAnimation);
            this.contentUpdater.stopAllProgressUpdaters();
        } catch (error) {
            // Error handling
        }
    }

    async _handleTransition(detail) {
        try {
            await this.contentUpdater.updateAllForSet(detail.passiveSet, detail.data);
            this.contentUpdater.startProgressUpdater(detail.data, detail.passiveSet);

            await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));

            const transitionAnimation = await this.animationService.playTransition({
                activeSet: detail.activeSet,
                passiveSet: detail.passiveSet
            });
            this.activeAnimations.push(transitionAnimation);

            this.contentUpdater.stopProgressUpdater(detail.activeSet);
            this.stateService.finalizeTransition(detail.passiveSet);
            this.contentUpdater.clearAllForSet(detail.activeSet);
        } catch (error) {
            // Error handling
        }
    }

    _handleSync({ data, set }) {
        this.contentUpdater.startProgressUpdater(data, set);
    }

    _handleError({ message }) {
        if (this.errorContainer) {
            this.errorContainer.innerText = message;
            this.errorContainer.style.display = 'block';
        }
        this._handleOutro();
        this.contentUpdater.stopAllProgressUpdaters();
    }

    _handleClearError() {
        if (this.errorContainer && this.errorContainer.style.display !== 'none') {
            this.errorContainer.style.display = 'none';
        }
    }
}
