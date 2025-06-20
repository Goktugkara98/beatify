/**
 * @class WidgetDOMManager
 * @description DOM manipülasyonlarını, animasyonları ve içerik güncellemelerini yönetir.
 * Olayları dinler ve ilgili servisleri (AnimationService, ContentUpdaterService) koordine eder.
 */
class WidgetDOMManager {
    static CSS_CLASSES = { WIDGET_INACTIVE: 'widget-inactive' };

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
     * StateService tarafından tetiklenen widget olaylarını dinler.
     * @private
     */
    _listenToEvents() {
        this.widgetElement.addEventListener('widget:intro', (e) => this.runIntro(e.detail));
        this.widgetElement.addEventListener('widget:transition', (e) => this.runTransition(e.detail));
        this.widgetElement.addEventListener('widget:outro', (e) => this.runOutro(e.detail));
        
        this.widgetElement.addEventListener('widget:sync', (e) => {
            this.contentUpdater.startProgressUpdater(e.detail.data, e.detail.set);
        });
        this.widgetElement.addEventListener('widget:error', (e) => this.contentUpdater.displayError(e.detail.message));
        this.widgetElement.addEventListener('widget:clear-error', () => this.contentUpdater.clearError());
    }

    /**
     * Widget'ın ilk açılış animasyonunu (intro) çalıştırır.
     */
    async runIntro({ set, data }) {
        try {
            // Bu kısım aynı kalır, içeriği elementlere basar.
            this.contentUpdater.updateAll(set, data);

            // Animasyon uygulanacak container'ları yeni config'den al.
            const introContainerIds = this.config.AnimationContainers.filter(id => id.endsWith(`_${set}`));

            // prepareElement'ı container'lar için çağır.
            introContainerIds.forEach(id => this.animationService.prepareElement(id, 'intro'));

            // waitForImages için <img> elementlerinin ID'lerini al.
            const imageElementIds = introContainerIds
                .filter(id => id.startsWith('AlbumArt') || id.startsWith('Cover'))
                .map(id => id.replace('AnimationContainer', 'Element'));
            await this.animationService.waitForImages(imageElementIds);
            
            this.widgetElement.classList.remove(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);

            // execute'u container'lar için çağır.
            await Promise.all(introContainerIds.map(id => this.animationService.execute(id, 'intro')));
            
            // --- YENİ EKLENECEK KISIM ---
            // Animasyonlar bittikten sonra, 'incoming' (içeri giren) elementlerin
            // inline stil'lerini temizleyerek bir sonraki animasyona hazır hale getir.
            introContainerIds.forEach(id => this.animationService.cleanupElement(id, 'incoming'));
            // --- YENİ EKLENECEK KISIM SONU ---

            this.contentUpdater.startProgressUpdater(data, set);
        } catch (error) {
            console.error('runIntro sırasında hata:', error);
        }
    }

    /**
     * Şarkı değiştirme animasyonunu (transition) çalıştırır.
     * Bu versiyon, giden ve gelen animasyonları bağımsız olarak yönetir ve z-index durumunu doğru şekilde sıfırlar.
     */
    async runTransition({ activeSet, passiveSet, data }) {
        try {
            // 1. Mevcut durumu hazırla (ilerleme çubuğunu durdur, yeni veriyi yükle)
            this.contentUpdater.stopProgressUpdater();
            this.contentUpdater.updateAll(passiveSet, data);
    
            const outgoingContainerIds = this.config.AnimationContainers.filter(id => id.endsWith(`_${activeSet}`));
            const incomingContainerIds = this.config.AnimationContainers.filter(id => id.endsWith(`_${passiveSet}`));
            
            // 2. Z-index'leri GEÇİCİ olarak ters çevir (gelenler üste çıksın)
            this.animationService._flipZIndexes();
    
            // 3. Giden ve gelen tüm elementleri animasyonun ilk karesine hazırla
            // Bu aşamada stiller uygulanır ama elementler hala .passive sınıfına sahip olabilir
            incomingContainerIds.forEach(id => this.animationService.prepareElement(id, 'transitionIn'));
            outgoingContainerIds.forEach(id => this.animationService.prepareElement(id, 'transitionOut'));
    
            // 4. Yeni yüklenecek görsellerin hazır olmasını bekle (kritik adım)
            const incomingImageElementIds = incomingContainerIds
                .filter(id => id.startsWith('AlbumArt') || id.startsWith('Cover'))
                .map(id => id.replace('AnimationContainer', 'Element'));
            await this.animationService.waitForImages(incomingImageElementIds);
    
            // 5. Animasyonları BAĞIMSIZ olarak başlat ve tamamlanmalarını bekle
            // Her grup kendi içinde tamamlandığında temizlenir.
            const outgoingAnimationsPromise = Promise.all(
                outgoingContainerIds.map(id => this.animationService.execute(id, 'transitionOut'))
            ).then(() => {
                // Giden animasyonlar biter bitmez kendi temizliklerini yap
                outgoingContainerIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
                this.contentUpdater.reset(activeSet); // Giden setin içeriğini temizle
            });

            const incomingAnimationsPromise = Promise.all(
                incomingContainerIds.map(id => this.animationService.execute(id, 'transitionIn'))
            ).then(() => {
                // Gelen animasyonlar biter bitmez kendi temizliklerini yap
                incomingContainerIds.forEach(id => this.animationService.cleanupElement(id, 'incoming'));
            });
            
            // 6. Her iki animasyon grubunun da (ve temizliklerinin) bitmesini bekle
            await Promise.all([outgoingAnimationsPromise, incomingAnimationsPromise]);
    
            
            // 8. Ana durumu güncelle ve yeni şarkının ilerleme çubuğunu başlat
            this.stateService.finalizeTransition(passiveSet);

        } catch (error) {
            console.error('runTransition sırasında hata:', error);
        }
    }

    /**
     * Müzik durduğunda widget'ı kapatma (outro) işlemini yürütür.
     */
    async runOutro({ activeSet }) {
        try {
            this.contentUpdater.stopProgressUpdater();
            this.widgetElement.classList.add(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            
            // ESKİ: const outroElementIds = this.config.elements.filter(...)
            // YENİ: Container ID'lerini al.
            const outroContainerIds = this.config.AnimationContainers.filter(id => id.endsWith(`_${activeSet}`));

            // cleanupElement'ı container'lar için çağır.
            outroContainerIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            this.contentUpdater.reset(activeSet);
        } catch (error) {
            console.error('runOutro sırasında hata:', error);
        }
    }

}
