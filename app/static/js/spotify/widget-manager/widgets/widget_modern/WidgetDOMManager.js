/**
 * =================================================================================
 * WidgetDOMManager - İçindekiler
 * =================================================================================
 *
 * DOM manipülasyonlarını, animasyonları ve içerik güncellemelerini yönetir.
 * Olayları dinler ve ilgili servisleri koordine eder.
 *
 * ---
 *
 * BÖLÜM 1: KURULUM VE OLAY YÖNETİMİ (SETUP & EVENT MANAGEMENT)
 * 1.1. constructor: Servisleri başlatır ve olay dinleyicilerini ayarlar.
 * 1.2. _listenToEvents: StateService tarafından tetiklenen widget olaylarını dinler.
 *
 * BÖLÜM 2: ANA ANİMASYON AKIŞLARI (MAIN ANIMATION FLOWS)
 * 2.1. runIntro: Widget'ın ilk açılış animasyonunu (intro) çalıştırır.
 * 2.2. runTransition: Şarkı değiştirme animasyonunu (transition) çalıştırır.
 * 2.3. runOutro: Müzik durduğunda widget'ı kapatma (outro) işlemini yürütür.
 *
 * BÖLÜM 3: DOĞRUDAN OLAY İŞLEYİCİLER (DIRECT EVENT HANDLERS)
 * (Bu bölümde, _listenToEvents içinde doğrudan çağrılan basit olaylar yer alır)
 *
 * =================================================================================
 */
class WidgetDOMManager {
    static CSS_CLASSES = { WIDGET_INACTIVE: 'widget-inactive' };

    // =================================================================================
    // BÖLÜM 1: KURULUM VE OLAY YÖNETİMİ (SETUP & EVENT MANAGEMENT)
    // =================================================================================

    /**
     * 1.1. WidgetDOMManager'in bir örneğini oluşturur.
     * @param {HTMLElement} widgetElement - Widget'ın ana elementi.
     * @param {object} config - Animasyon yapılandırmaları.
     * @param {SpotifyStateService} stateService - Durum yönetimi servisi.
     */
    constructor(widgetElement, config, stateService) {
        if (!widgetElement || !config || !stateService) {
            throw new Error("WidgetDOMManager için gerekli tüm modüller sağlanmalıdır.");
        }

        this.widgetElement = widgetElement;
        this.config = config;
        this.stateService = stateService;
        this.contentUpdater = new ContentUpdaterService(this.widgetElement);
        this.animationService = new AnimationService(this.widgetElement, this.config);

        this._listenToEvents();
    }

    /**
     * 1.2. StateService tarafından tetiklenen widget olaylarını dinler.
     * @private
     */
    _listenToEvents() {
        this.widgetElement.addEventListener('widget:intro', (e) => this.runIntro(e.detail));
        this.widgetElement.addEventListener('widget:transition', (e) => this.runTransition(e.detail));
        this.widgetElement.addEventListener('widget:outro', (e) => this.runOutro(e.detail));
        
        // BÖLÜM 3: DOĞRUDAN OLAY İŞLEYİCİLER
        this.widgetElement.addEventListener('widget:sync', (e) => {
            this.contentUpdater.startProgressUpdater(e.detail.data, e.detail.set);
        });
        this.widgetElement.addEventListener('widget:error', (e) => this.contentUpdater.displayError(e.detail.message));
        this.widgetElement.addEventListener('widget:clear-error', () => this.contentUpdater.clearError());
    }

    // =================================================================================
    // BÖLÜM 2: ANA ANİMASYON AKIŞLARI (MAIN ANIMATION FLOWS)
    // =================================================================================

    /**
     * 2.1. Widget'ın ilk açılış animasyonunu (intro) çalıştırır.
     * @param {object} detail - Olay detayı.
     * @param {string} detail.set - Aktif set ('a' veya 'b').
     * @param {object} detail.data - Şarkı verisi.
     */
    async runIntro({ set, data }) {
        try {
            this.contentUpdater.updateAll(set, data);
            const introContainerIds = this.config.AnimationContainers.filter(id => id.endsWith(`_${set}`));
            introContainerIds.forEach(id => this.animationService.prepareElement(id, 'intro'));
            
            const imageElementIds = introContainerIds
                .filter(id => id.startsWith('AlbumArt') || id.startsWith('Cover'))
                .map(id => id.replace('AnimationContainer', 'Element'));
            await this.animationService.waitForImages(imageElementIds);
            
            this.widgetElement.classList.remove(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            await Promise.all(introContainerIds.map(id => this.animationService.execute(id, 'intro')));
            
            introContainerIds.forEach(id => this.animationService.cleanupElement(id, 'incoming'));
            this.contentUpdater.startProgressUpdater(data, set);
        } catch (error) {
            console.error('runIntro sırasında hata:', error);
        }
    }

    /**
     * 2.2. Şarkı değiştirme animasyonunu (transition) çalıştırır.
     * @param {object} detail - Olay detayı.
     * @param {string} detail.activeSet - Giden set.
     * @param {string} detail.passiveSet - Gelen set.
     * @param {object} detail.data - Yeni şarkı verisi.
     */
    async runTransition({ activeSet, passiveSet, data }) {
        try {
            this.contentUpdater.stopProgressUpdater();
            this.contentUpdater.updateAll(passiveSet, data);
    
            const outgoingContainerIds = this.config.AnimationContainers.filter(id => id.endsWith(`_${activeSet}`));
            const incomingContainerIds = this.config.AnimationContainers.filter(id => id.endsWith(`_${passiveSet}`));
            
            this.animationService._flipZIndexes();
    
            incomingContainerIds.forEach(id => this.animationService.prepareElement(id, 'transitionIn'));
            outgoingContainerIds.forEach(id => this.animationService.prepareElement(id, 'transitionOut'));
    
            const incomingImageElementIds = incomingContainerIds
                .filter(id => id.startsWith('AlbumArt') || id.startsWith('Cover'))
                .map(id => id.replace('AnimationContainer', 'Element'));
            await this.animationService.waitForImages(incomingImageElementIds);
    
            const outgoingAnimationsPromise = Promise.all(
                outgoingContainerIds.map(id => this.animationService.execute(id, 'transitionOut'))
            ).then(() => {
                outgoingContainerIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
                this.contentUpdater.reset(activeSet);
            });

            const incomingAnimationsPromise = Promise.all(
                incomingContainerIds.map(id => this.animationService.execute(id, 'transitionIn'))
            ).then(() => {
                incomingContainerIds.forEach(id => this.animationService.cleanupElement(id, 'incoming'));
            });
            
            await Promise.all([outgoingAnimationsPromise, incomingAnimationsPromise]);
    
            this.stateService.finalizeTransition(passiveSet);
        } catch (error) {
            console.error('runTransition sırasında hata:', error);
        }
    }

    /**
     * 2.3. Müzik durduğunda widget'ı kapatma (outro) işlemini yürütür.
     * @param {object} detail - Olay detayı.
     * @param {string} detail.activeSet - Kapatılacak set.
     */
    async runOutro({ activeSet }) {
        try {
            this.contentUpdater.stopProgressUpdater();
            this.widgetElement.classList.add(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            
            const outroContainerIds = this.config.AnimationContainers.filter(id => id.endsWith(`_${activeSet}`));
            outroContainerIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            this.contentUpdater.reset(activeSet);
        } catch (error) {
            console.error('runOutro sırasında hata:', error);
        }
    }
}
