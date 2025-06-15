// DOSYA ADI: WidgetDOMManager.js (Yeniden Düzenlenmiş Orkestratör)
class WidgetDOMManager {
    static CSS_CLASSES = {
        WIDGET_INACTIVE: 'widget-inactive'
    };

    constructor(widgetElement, config, stateService) {
        if (!widgetElement || !config || !stateService) throw new Error("Gerekli tüm modüller sağlanmalıdır.");
        
        this.widgetElement = widgetElement;
        this.config = config;
        this.stateService = stateService;

        // Uzman servislerin örneklerini oluştur
        this.contentUpdater = new ContentUpdaterService(this.widgetElement);
        this.animationService = new AnimationService(this.widgetElement, this.config);

        this.listenToEvents();
    }

    /**
     * StateService tarafından gönderilen olayları dinler ve ilgili yönetici metotları çağırır.
     */
    listenToEvents() {
        this.widgetElement.addEventListener('widget:intro', (e) => this.runIntro(e.detail));
        this.widgetElement.addEventListener('widget:transition', (e) => this.runTransition(e.detail));
        this.widgetElement.addEventListener('widget:outro', (e) => this.runOutro(e.detail));
        this.widgetElement.addEventListener('widget:sync', (e) => this.contentUpdater.startProgressUpdater(e.detail.data, e.detail.set));
        this.widgetElement.addEventListener('widget:error', (e) => this.contentUpdater.displayError(e.detail.message));
        this.widgetElement.addEventListener('widget:clear-error', () => this.contentUpdater.clearError());
    }

    /**
     * Widget ilk kez başlatıldığında çalışır. Görevleri delege eder.
     */
    async runIntro({ set, data }) {
        // 1. İçeriği doldur
        this.contentUpdater.updateAll(set, data);

        // 2. Animasyonları çalıştır
        const introElementIds = this.config.elements.filter(id => id.endsWith(`_${set}`));
        const imageElementIds = introElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG');
        
        // DEĞİŞEN SATIR: Eski `_setElementState` yerine yeni `prepareElement` kullanılıyor.
        // Bu, elemanları animasyon için doğru başlangıç durumuna (z-index, opacity, transform vb.) getirir.
        introElementIds.forEach(id => this.animationService.prepareElement(id, 'intro'));
        
        await this.animationService.waitForImages(imageElementIds);
        
        this.widgetElement.classList.remove(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
        const introAnimations = introElementIds.map(id => this.animationService.execute(id, 'intro'));
        
        await Promise.all(introAnimations);
        
        // 3. İlerleme çubuğunu başlat
        this.contentUpdater.startProgressUpdater(data, set);
    }

    /**
     * runTransition metodu bir önceki adımdaki gibi kalacak.
     */
    async runTransition({ activeSet, passiveSet, data }) {
        // ... (Bu metot zaten doğru şekilde çalışıyor, değişiklik yok) ...
        this.contentUpdater.stopProgressUpdater();

        // 1. Yeni içeriği pasif sete yükle
        this.contentUpdater.updateAll(passiveSet, data);

        const outgoingElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
        const incomingElementIds = this.config.elements.filter(id => id.endsWith(`_${passiveSet}`));
        const incomingImageIds = incomingElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG');
        
        // FAZ 1: HAZIRLIK
        this.animationService._flipZIndexes();
        incomingElementIds.forEach(id => this.animationService.prepareElement(id, 'transitionIn'));
        outgoingElementIds.forEach(id => this.animationService.prepareElement(id, 'transitionOut'));
        await this.animationService.waitForImages(incomingImageIds);

        // FAZ 2: ANİMASYON
        const outgoingAnimations = outgoingElementIds.map(id => this.animationService.execute(id, 'transitionOut'));
        const incomingAnimations = incomingElementIds.map(id => this.animationService.execute(id, 'transitionIn'));
        await Promise.all([...outgoingAnimations, ...incomingAnimations]);

        // FAZ 3: TEMİZLİK
        outgoingElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
        incomingElementIds.forEach(id => this.animationService.cleanupElement(id, 'incoming'));
        this.contentUpdater.reset(activeSet);

        // SON ADIM: Durumu Sonlandır
        this.stateService.finalizeTransition(passiveSet);
    }

    /**
     * DEĞİŞTİ: Müzik durduğunda çalışır. Artık yeni animasyon temizlik metodunu kullanıyor.
     */
    runOutro({ activeSet }) {
        this.contentUpdater.stopProgressUpdater();
        this.widgetElement.classList.add(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
        
        const outroElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
        
        // DEĞİŞEN SATIR: Eski `_setElementState` yerine yeni `cleanupElement` kullanılıyor.
        // Bu, elemanları pasif duruma getirir ve stillerini temizler.
        outroElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
        
        this.contentUpdater.reset(activeSet);
    }
}