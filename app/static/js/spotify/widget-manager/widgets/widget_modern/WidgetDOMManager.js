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
        
        introElementIds.forEach(id => this.animationService._setElementState(id, 'active'));
        await this.animationService.waitForImages(imageElementIds);
        
        this.widgetElement.classList.remove(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
        const introAnimations = introElementIds.map(id => this.animationService.execute(id, 'intro'));
        
        await Promise.all(introAnimations);
        
        // 3. İlerleme çubuğunu başlat
        this.contentUpdater.startProgressUpdater(data, set);
        console.log("[DOMManager] Intro süreci tamamlandı.");
    }

    /**
     * Bir şarkıdan diğerine geçişi yönetir.
     */
    async runTransition({ activeSet, passiveSet, data }) {
        this.contentUpdater.stopProgressUpdater();
        
        // 1. Yeni içeriği pasif sete yükle
        this.contentUpdater.updateAll(passiveSet, data);

        // 2. Animasyon servisine tam geçiş sekansını çalıştırmasını söyle
        await this.animationService.runTransitionSequence(activeSet, passiveSet);
        
        // 3. Animasyon bittiğinde, eski setin verilerini temizle
        this.contentUpdater.reset(activeSet);
        
        // 4. StateService'e geçişin tamamlandığını bildir
        this.stateService.finalizeTransition(passiveSet);
    }

    /**
     * Müzik durduğunda çalışır.
     */
    runOutro({ activeSet }) {
        this.contentUpdater.stopProgressUpdater();
        this.widgetElement.classList.add(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
        
        const outroElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
        outroElementIds.forEach(id => this.animationService._setElementState(id, 'passive'));
        
        this.contentUpdater.reset(activeSet);
        console.log(`[DOMManager] Outro süreci tamamlandı.`);
    }
}