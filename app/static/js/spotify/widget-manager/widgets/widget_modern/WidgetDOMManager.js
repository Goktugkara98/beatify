/**
 * @file WidgetDOMManager.js
 * @description StateService'den gelen olayları dinler ve DOM/Animasyon servislerini yönetir.
 */
class WidgetDOMManager {

    /**
     * @param {HTMLElement} widgetElement
     * @param {object} services - Gerekli tüm servisleri içeren ve main.js tarafından sağlanan obje.
     */
    constructor(widgetElement, services) {
        this.widgetElement = widgetElement;

        // Bu kısım, main.js'in verdiği "dolu" servisleri alır.
        // Kendi içinde "new" ile bir şey oluşturmaz.
        this.stateService = services.stateService;
        this.animationService = services.animationService;
        this.contentUpdater = services.contentUpdater;
        
        this.errorContainer = widgetElement.querySelector('.WidgetErrorContainer');
        
        // Bu logu kontrol amaçlı bırakıyorum.
        console.log('%c[DOMManager constructor] BANA VERİLEN animationService:', 'color: orange; font-weight: bold;', this.animationService);

        this._bindEvents();
        console.log('[DOMManager] Yönetici başlatıldı ve olaylar dinleniyor.');
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
        console.log(`[DOMManager] İLK AÇILIŞ BAŞLADI (Set: ${detail.set})`);
        
        this.contentUpdater.updateAllForSet(detail.set, detail.data);
        
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        
        console.log('%c[DOMManager _handleIntro] KULLANILAN animationService:', 'color: red; font-weight: bold;', this.animationService);
        this.animationService.playIntro();
        
        this.contentUpdater.startProgressUpdater(detail.data, detail.set);
    }
    
    _handleOutro() {
        this.animationService.playOutro();
        this.contentUpdater.stopProgressUpdater();
    }

    async _handleTransition(detail) {
        console.log(`[DOMManager] ŞARKI GEÇİŞİ BAŞLADI (Aktif: ${detail.activeSet}, Pasif: ${detail.passiveSet})`);
    
        // 1. ADIM: Yeni (pasif) setin içeriğini animasyon başlamadan önce güncelle.
        // Bu olmadan, 'b' seti boş bir şekilde ekrana gelirdi.
        this.contentUpdater.updateAllForSet(detail.passiveSet, detail.data);
    
        // 2. ADIM: Geçiş animasyonunu başlat ve tamamlanmasını bekle.
        // 'await' olmadan, aşağıdaki kod animasyon bitmeden anında çalışırdı.
        await this.animationService.playTransition(detail);
    
        // 3. ADIM: Animasyon bittikten sonra StateService'e haber ver.
        // Bu, mevcut şarkı ID'sini güncelleyerek sonsuz döngüyü engeller.
        this.stateService.finalizeTransition(detail.passiveSet);
        
        console.log(`[DOMManager] ŞARKI GEÇİŞİ TAMAMLANDI. Yeni aktif set: ${detail.passiveSet}`);
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
    }
    
    _handleClearError() {
        if(this.errorContainer && this.errorContainer.style.display !== 'none') {
            this.errorContainer.style.display = 'none';
        }
    }
}