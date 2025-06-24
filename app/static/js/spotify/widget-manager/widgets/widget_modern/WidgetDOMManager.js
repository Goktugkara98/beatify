/**
 * @file WidgetDOMManager.js
 * @description StateService'den gelen olayları dinler ve DOM/Animasyon servislerini yönetir.
 */
class WidgetDOMManager {
    constructor(widgetElement, stateService) {
        this.widgetElement = widgetElement;
        this.stateService = stateService; // State'i güncellemek için referans

        // Servisleri başlat
        this.contentUpdater = new ContentUpdaterService(widgetElement);
        this.animationService = new AnimationService(widgetElement);
        this.errorContainer = widgetElement.querySelector('.WidgetErrorContainer');
        
        this._bindEvents();
    }

    /**
     * StateService'den gelecek olayları dinlemek için event listener'ları bağlar.
     */
    _bindEvents() {
        this.widgetElement.addEventListener('widget:intro', (e) => this._handleIntro(e.detail));
        this.widgetElement.addEventListener('widget:outro', (e) => this._handleOutro(e.detail));
        this.widgetElement.addEventListener('widget:transition', (e) => this._handleTransition(e.detail));
        this.widgetElement.addEventListener('widget:sync', (e) => this._handleSync(e.detail));
        this.widgetElement.addEventListener('widget:error', (e) => this._handleError(e.detail));
        this.widgetElement.addEventListener('widget:clear-error', () => this._handleClearError());
    }

    _handleIntro({ set, data }) {
        this.contentUpdater.updateAllForSet(set, data);
        this.contentUpdater.startProgressUpdater(data, set);
        this.animationService.playIntro();
    }
    
    _handleOutro() {
        this.animationService.playOutro();
        this.contentUpdater.stopProgressUpdater();
    }

    async _handleTransition(detail) {
        const { passiveSet, data } = detail;
        // 1. Pasif olan setin içeriğini yeni şarkı bilgileriyle doldur
        this.contentUpdater.updateAllForSet(passiveSet, data);
        
        // 2. Geçiş animasyonunu oynat ve bitmesini bekle
        await this.animationService.playTransition(detail);

        // 3. Animasyon bittikten sonra StateService'e durumu sonlandırmasını söyle
        this.stateService.finalizeTransition(passiveSet);
        
        // 4. Yeni aktif set için ilerleme çubuğunu başlat
        this._handleSync({data, set: passiveSet});
    }

    _handleSync({ data, set }) {
        // Sadece ilerleme ve zamanı güncelle
        this.contentUpdater.startProgressUpdater(data, set);
    }
    
    _handleError({ message }) {
        if(this.errorContainer) {
            this.errorContainer.innerText = message;
            this.errorContainer.style.display = 'block';
        }
        this.animationService.playOutro();
    }
    
    _handleClearError() {
        if(this.errorContainer && this.errorContainer.style.display !== 'none') {
            this.errorContainer.style.display = 'none';
        }
    }
}
