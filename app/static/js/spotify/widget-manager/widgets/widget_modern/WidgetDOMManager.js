// DOSYA ADI: WidgetDOMManager.js (Yeniden Düzenlenmiş Orkestratör)
class WidgetDOMManager {
    static CSS_CLASSES = {
        WIDGET_INACTIVE: 'widget-inactive'
    };

    constructor(widgetElement, config, stateService) {
        console.log('[WidgetDOMManager] Initializing with config:', config);
        if (!widgetElement || !config || !stateService) {
            const error = new Error("Gerekli tüm modüller sağlanmalıdır.");
            console.error('[WidgetDOMManager] Initialization error:', error);
            throw error;
        }
        
        this.widgetElement = widgetElement;
        this.config = config;
        this.stateService = stateService;
        this.isBusy = false;
        this.pendingEvent = null;

        console.log('[WidgetDOMManager] Creating service instances');
        // Uzman servislerin örneklerini oluştur
        this.contentUpdater = new ContentUpdaterService(this.widgetElement);
        this.animationService = new AnimationService(this.widgetElement, this.config);

        console.log('[WidgetDOMManager] Setting up event listeners');
        this.listenToEvents();
        console.log('[WidgetDOMManager] Initialization complete');
    }

    /**
     * StateService tarafından gönderilen olayları dinler ve ilgili yönetici metotları çağırır.
     */
    listenToEvents() {
        console.log('[WidgetDOMManager] Setting up event listeners');
        
        // Intro event handler
        this.widgetElement.addEventListener('widget:intro', (e) => {
            console.log('[WidgetDOMManager] Received widget:intro event', e.detail);
            if (this.isBusy) {
                console.log('[WidgetDOMManager] Busy, queuing intro event');
                this.pendingEvent = { type: 'intro', detail: e.detail };
                return;
            }
            this.runIntro(e.detail);
        });
        
        // Transition event handler
        this.widgetElement.addEventListener('widget:transition', (e) => {
            console.log('[WidgetDOMManager] Received widget:transition event', e.detail);
            if (this.isBusy) {
                console.log('[WidgetDOMManager] Busy, queuing transition event');
                this.pendingEvent = { type: 'transition', detail: e.detail };
                return;
            }
            this.runTransition(e.detail);
        });
        
        // Outro event handler (handled immediately if not busy)
        this.widgetElement.addEventListener('widget:outro', (e) => {
            console.log('[WidgetDOMManager] Received widget:outro event', e.detail);
            if (this.isBusy) {
                console.log('[WidgetDOMManager] Busy, but processing outro immediately');
            }
            this.runOutro(e.detail);
        });
        
        // Sync event handler (only if not busy)
        this.widgetElement.addEventListener('widget:sync', (e) => {
            console.log('[WidgetDOMManager] Received widget:sync event', e.detail);
            if (!this.isBusy) {
                this.contentUpdater.startProgressUpdater(e.detail.data, e.detail.set);
            } else {
                console.log('[WidgetDOMManager] Busy, skipping sync update');
            }
        });
        
        // Error handling
        this.widgetElement.addEventListener('widget:error', (e) => {
            console.error('[WidgetDOMManager] Received error:', e.detail.message);
            this.contentUpdater.displayError(e.detail.message);
        });
        
        this.widgetElement.addEventListener('widget:clear-error', () => {
            console.log('[WidgetDOMManager] Clearing error state');
            this.contentUpdater.clearError();
        });
    }

    /**
     * Widget ilk kez başlatıldığında çalışır. Görevleri delege eder.
     */
    async runIntro({ set, data }) {
        console.log(`[WidgetDOMManager] Running intro for set: ${set}`, data);
        this.isBusy = true;
        
        try {
            // 1. İçeriği doldur
            console.log(`[WidgetDOMManager] Updating content for set: ${set}`);
            this.contentUpdater.updateAll(set, data);

            // 2. Animasyonları çalıştır
            const introElementIds = this.config.elements.filter(id => id.endsWith(`_${set}`));
            const imageElementIds = introElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG');
            
            console.log(`[WidgetDOMManager] Preparing ${introElementIds.length} elements for intro animation`);
            introElementIds.forEach(id => this.animationService.prepareElement(id, 'intro'));
            
            console.log(`[WidgetDOMManager] Waiting for ${imageElementIds.length} images to load`);
            await this.animationService.waitForImages(imageElementIds);
            
            console.log('[WidgetDOMManager] Activating widget and starting animations');
            this.widgetElement.classList.remove(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            
            const introAnimations = introElementIds.map(id => this.animationService.execute(id, 'intro'));
            console.log(`[WidgetDOMManager] Started ${introAnimations.length} intro animations`);
            
            await Promise.all(introAnimations);
            console.log('[WidgetDOMManager] All intro animations completed');
            
            // 3. İlerleme çubuğunu başlat
            console.log(`[WidgetDOMManager] Starting progress updater for set: ${set}`);
            this.contentUpdater.startProgressUpdater(data, set);
            
        } catch (error) {
            console.error('[WidgetDOMManager] Error in runIntro:', error);
            throw error;
        } finally {
            this.isBusy = false;
            this.processPendingEvent();
        }
    }

    /**
     * runTransition metodu bir önceki adımdaki gibi kalacak.
     */
    async runTransition({ activeSet, passiveSet, data }) {
        console.log(`[WidgetDOMManager] Starting transition from ${activeSet} to ${passiveSet}`);
        this.isBusy = true;
        
        try {
            // 0. Mevcut ilerleme çubuğunu durdur
            console.log('[WidgetDOMManager] Stopping current progress updater');
            this.contentUpdater.stopProgressUpdater();

            // 1. Yeni içeriği pasif sete yükle
            console.log(`[WidgetDOMManager] Updating content for passive set: ${passiveSet}`);
            this.contentUpdater.updateAll(passiveSet, data);

            const outgoingElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
            const incomingElementIds = this.config.elements.filter(id => id.endsWith(`_${passiveSet}`));
            const incomingImageIds = incomingElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG');
            
            // FAZ 1: HAZIRLIK
            console.log('[WidgetDOMManager] PHASE 1: PREPARATION');
            console.log(`- Flipping z-indexes for ${outgoingElementIds.length} outgoing and ${incomingElementIds.length} incoming elements`);
            this.animationService._flipZIndexes();
            
            console.log(`- Preparing ${incomingElementIds.length} incoming elements`);
            incomingElementIds.forEach(id => this.animationService.prepareElement(id, 'transitionIn'));
            
            console.log(`- Preparing ${outgoingElementIds.length} outgoing elements`);
            outgoingElementIds.forEach(id => this.animationService.prepareElement(id, 'transitionOut'));
            
            console.log(`- Waiting for ${incomingImageIds.length} images to load`);
            await this.animationService.waitForImages(incomingImageIds);

            // FAZ 2: ANİMASYON
            console.log('[WidgetDOMManager] PHASE 2: ANIMATION');
            console.log(`- Starting ${outgoingElementIds.length} outgoing animations`);
            const outgoingAnimations = outgoingElementIds.map(id => this.animationService.execute(id, 'transitionOut'));
            
            console.log(`- Starting ${incomingElementIds.length} incoming animations`);
            const incomingAnimations = incomingElementIds.map(id => this.animationService.execute(id, 'transitionIn'));
            
            console.log(`- Waiting for all animations to complete (${outgoingAnimations.length + incomingAnimations.length} total)`);
            await Promise.all([...outgoingAnimations, ...incomingAnimations]);
            console.log('- All animations completed');

            // FAZ 3: TEMİZLİK
            console.log('[WidgetDOMManager] PHASE 3: CLEANUP');
            console.log(`- Cleaning up ${outgoingElementIds.length} outgoing elements`);
            outgoingElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            
            console.log(`- Cleaning up ${incomingElementIds.length} incoming elements`);
            incomingElementIds.forEach(id => this.animationService.cleanupElement(id, 'incoming'));
            
            console.log(`- Resetting active set: ${activeSet}`);
            this.contentUpdater.reset(activeSet);

            // SON ADIM: Durumu Sonlandır
            console.log(`[WidgetDOMManager] Finalizing transition to set: ${passiveSet}`);
            this.stateService.finalizeTransition(passiveSet);
            
        } catch (error) {
            console.error('[WidgetDOMManager] Error in runTransition:', error);
            throw error;
        } finally {
            this.isBusy = false;
            this.processPendingEvent();
        }
    }

    /**
     * DEĞİŞTİ: Müzik durduğunda çalışır. 
     * @param {Object} param - activeSet parametresi
     */
    async runOutro({ activeSet }) {
        console.log(`[WidgetDOMManager] Running outro for set: ${activeSet}`);
        
        try {
            // Ä°lerleme çubuğunu durdur
            console.log('[WidgetDOMManager] Stopping progress updater');
            this.contentUpdater.stopProgressUpdater();
            
            // Widget'ı inaktif duruma getir
            console.log('[WidgetDOMManager] Deactivating widget');
            this.widgetElement.classList.add(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            
            // Çıkış animasyonu için elemanları temizle
            const outroElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
            console.log(`[WidgetDOMManager] Cleaning up ${outroElementIds.length} elements`);
            
            // Elemanları pasif duruma getir ve stillerini temizle
            outroElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            
            // İçeriği sıfırla
            console.log(`[WidgetDOMManager] Resetting content for set: ${activeSet}`);
            this.contentUpdater.reset(activeSet);
            
            console.log('[WidgetDOMManager] Outro completed');
        } catch (error) {
            console.error('[WidgetDOMManager] Error in runOutro:', error);
            throw error;
        }
    }

    /**
     * Bekleyen olayı işler (eğer varsa).
     * Bir animasyon tamamlandığında çağrılır.
     */
    processPendingEvent() {
        if (!this.pendingEvent) {
            console.log('[WidgetDOMManager] No pending events to process');
            return;
        }
        
        const { type, detail } = this.pendingEvent;
        console.log(`[WidgetDOMManager] Processing pending ${type} event`);
        this.pendingEvent = null;
        
        switch (type) {
            case 'intro':
                this.runIntro(detail);
                break;
            case 'transition':
                this.runTransition(detail);
                break;
            default:
                console.warn(`[WidgetDOMManager] Unknown pending event type: ${type}`);
        }
    }
}