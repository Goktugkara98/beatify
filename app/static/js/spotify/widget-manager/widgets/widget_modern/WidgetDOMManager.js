class WidgetDOMManager {
    constructor(widgetElement, services) {
        this.widgetElement = widgetElement;
        this.stateService = services.stateService;
        this.animationService = services.animationService;
        this.contentUpdater = services.contentUpdater;
        this.errorContainer = widgetElement.querySelector('.WidgetErrorContainer');

        this._bindEvents();
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
        // 1. İçeriğin tam olarak yüklenmesini BEKLE. (Mevcut hali doğru)
        await this.contentUpdater.updateAllForSet(detail.set, detail.data);

        // 2. Tarayıcının bu yeni içeriği çizmesi için bir fırsat ver. (Mevcut hali doğru)
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));

        // 3. Her şey hazır olduğunda GİRİŞ animasyonunu oynat ve BİTMESİNİ BEKLE.
        // DEĞİŞİKLİK: "await" eklendi.
        await this.animationService.playIntro();

        // 4. Animasyon BİTTİKTEN SONRA (veya başladıktan hemen sonra, mevcut hali daha iyi)
        // ilerleme çubuğunu başlat.
        this.contentUpdater.startProgressUpdater(detail.data, detail.set);
    }
    
    _handleOutro() {
        this.animationService.playOutro();
        this.contentUpdater.stopAllProgressUpdaters();
    }

    async _handleTransition(detail) {
        this.contentUpdater.updateAllForSet(detail.passiveSet, detail.data);
        this.contentUpdater.startProgressUpdater(detail.data, detail.passiveSet);

        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    
        await this.animationService.playTransition(detail);
        
        this.contentUpdater.stopProgressUpdater(detail.activeSet);
    
        this.stateService.finalizeTransition(detail.passiveSet);
        
        this.contentUpdater.clearAllForSet(detail.activeSet);
    }

    _handleSync({ data, set }) {
        this.contentUpdater.startProgressUpdater(data, set);
    }
    
    _handleError({ message }) {
        if(this.errorContainer) {
            this.errorContainer.innerText = message;
            this.errorContainer.style.display = 'block';
        }
        this.animationService.playOutro();
        this.contentUpdater.stopAllProgressUpdaters();
    }
    
    _handleClearError() {
        if(this.errorContainer && this.errorContainer.style.display !== 'none') {
            this.errorContainer.style.display = 'none';
        }
    }
}