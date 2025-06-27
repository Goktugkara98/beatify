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
        console.log(`%c[DOMManager] Event: widget:intro | Set: ${detail.set}`, 'color: #00BCD4; font-weight: bold;');
        console.log(`[DOMManager] Adım 1: İçerik güncelleniyor -> ${detail.set}`);
        this.contentUpdater.updateAllForSet(detail.set, detail.data);
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        console.log(`[DOMManager] Adım 2: Animasyon başlatılıyor...`);
        this.animationService.playIntro();
        console.log(`[DOMManager] Adım 3: Progress updater başlatılıyor...`);
        this.contentUpdater.startProgressUpdater(detail.data, detail.set);
    }
    
    _handleOutro() {
        console.log('%c[DOMManager] Event: widget:outro', 'color: #00BCD4; font-weight: bold;');
        this.animationService.playOutro();
        this.contentUpdater.stopProgressUpdater();
    }

    async _handleTransition(detail) {
        console.log(`%c[DOMManager] Event: widget:transition | Aktif: ${detail.activeSet}, Pasif: ${detail.passiveSet}`, 'color: #00BCD4; font-weight: bold;');

        console.log(`[DOMManager] Adım 1: İçerik güncelleniyor -> ${detail.passiveSet}`);
        this.contentUpdater.updateAllForSet(detail.passiveSet, detail.data);

        console.log(`[DOMManager] Adım 2: Animasyon başlatılıyor...`);
        await this.animationService.playTransition(detail);
        console.log(`[DOMManager] Adım 2: Animasyon tamamlandı.`);

        console.log(`[DOMManager] Adım 3: State sonlandırılıyor -> yeni aktif set: ${detail.passiveSet}`);
        this.stateService.finalizeTransition(detail.passiveSet);

        console.log(`%c[DOMManager] ŞARKI GEÇİŞİ TAMAMLANDI.`, 'color: #00BCD4; font-weight: bold;');
    }

    _handleSync({ data, set }) {
        // Bu log çok sık tekrarlanacağı için kapalı
        // console.log(`[DOMManager] Event: widget:sync | Set: ${set}`);
        this.contentUpdater.startProgressUpdater(data, set);
    }
    
    _handleError({ message }) {
        console.log('%c[DOMManager] Event: widget:error', 'color: #00BCD4; font-weight: bold;');
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