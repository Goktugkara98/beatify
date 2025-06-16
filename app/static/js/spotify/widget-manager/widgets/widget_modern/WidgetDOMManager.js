// ===================================================================================
// DOSYA ADI: WidgetDOMManager.js
// ===================================================================================
class WidgetDOMManager {
    static CSS_CLASSES = { WIDGET_INACTIVE: 'widget-inactive' };

    // DEĞİŞTİ: constructor'a logger eklendi
    constructor(widgetElement, config, stateService, logger) {
        this.logger = logger; // YENİ
        this.logger.subgroup('WidgetDOMManager Kurulumu (constructor)');

        if (!widgetElement || !config || !stateService) {
            const error = new Error("Gerekli tüm modüller sağlanmalıdır.");
            this.logger.error("Başlatma Hatası:", error);
            throw error;
        }

        this.widgetElement = widgetElement;
        this.config = config;
        this.stateService = stateService;
        this.isBusy = false;
        this.pendingEvent = null;

        this.logger.action("Uzman servisler oluşturuluyor...");
        // YENİ: Logger'ı alt servislere aktar
        this.contentUpdater = new ContentUpdaterService(this.widgetElement, this.logger);
        this.animationService = new AnimationService(this.widgetElement, this.config, this.logger);

        this.listenToEvents();
        this.logger.info("Kurulum tamamlandı.");
        this.logger.groupEnd();
    }

    listenToEvents() {
        this.logger.action("Olay dinleyicileri (event listeners) ayarlanıyor.");
        
        this.widgetElement.addEventListener('widget:intro', (e) => {
            this.logger.subgroup("Olay Alındı: widget:intro");
            this.logger.data("Olay Detayı", e.detail);
            if (this.isBusy) {
                this.logger.warn("Widget meşgul, olay sıraya alınıyor.");
                this.pendingEvent = { type: 'intro', detail: e.detail };
            } else {
                this.runIntro(e.detail);
            }
            this.logger.groupEnd();
        });

        this.widgetElement.addEventListener('widget:transition', (e) => {
            this.logger.subgroup("Olay Alındı: widget:transition");
            this.logger.data("Olay Detayı", e.detail);
            if (this.isBusy) {
                this.logger.warn("Widget meşgul, olay sıraya alınıyor.");
                this.pendingEvent = { type: 'transition', detail: e.detail };
            } else {
                this.runTransition(e.detail);
            }
            this.logger.groupEnd();
        });

        this.widgetElement.addEventListener('widget:outro', (e) => {
            this.logger.subgroup("Olay Alındı: widget:outro");
            this.logger.data("Olay Detayı", e.detail);
            this.runOutro(e.detail);
            this.logger.groupEnd();
        });

        this.widgetElement.addEventListener('widget:sync', (e) => {
             this.logger.subgroup("Olay Alındı: widget:sync");
             this.logger.data("Olay Detayı", e.detail);
            if (!this.isBusy) {
                this.contentUpdater.startProgressUpdater(e.detail.data, e.detail.set);
            } else {
                this.logger.warn("Widget meşgul, 'sync' işlemi atlanıyor.");
            }
             this.logger.groupEnd();
        });

        this.widgetElement.addEventListener('widget:error', (e) => this.contentUpdater.displayError(e.detail.message));
        this.widgetElement.addEventListener('widget:clear-error', () => this.contentUpdater.clearError());
    }

    async runIntro({ set, data }) {
        this.logger.group('Eylem: WIDGET INTRO');
        this.isBusy = true;
        try {
            this.logger.action(`1. Adım: İçerik dolduruluyor (Set: ${set}).`);
            this.contentUpdater.updateAll(set, data);

            const introElementIds = this.config.elements.filter(id => id.endsWith(`_${set}`));
            const imageElementIds = introElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG');
            
            this.logger.action('2. Adım: Animasyonlar için elementler hazırlanıyor.');
            introElementIds.forEach(id => this.animationService.prepareElement(id, 'intro'));

            this.logger.action(`3. Adım: Resimlerin yüklenmesi bekleniyor (${imageElementIds.length} adet).`);
            await this.animationService.waitForImages(imageElementIds);
            
            this.logger.action('4. Adım: Widget aktive ediliyor ve animasyonlar başlatılıyor.');
            this.widgetElement.classList.remove(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            
            const introAnimations = introElementIds.map(id => this.animationService.execute(id, 'intro'));
            await Promise.all(introAnimations);
            this.logger.info('Tüm intro animasyonları tamamlandı.');

            this.logger.action('5. Adım: İlerleme çubuğu başlatılıyor.');
            this.contentUpdater.startProgressUpdater(data, set);
            
        } catch (error) {
            this.logger.error('runIntro sırasında hata:', error);
        } finally {
            this.isBusy = false;
            this.logger.info('Intro eylemi tamamlandı. Meşgul durumu kaldırıldı.');
            this.processPendingEvent();
            this.logger.groupEnd();
        }
    }

    async runTransition({ activeSet, passiveSet, data }) {
        this.logger.group(`Eylem: ŞARKI GEÇİŞİ ('${activeSet}' -> '${passiveSet}')`);
        this.isBusy = true;
        try {
            this.logger.action('0. Adım: Mevcut ilerleme çubuğu durduruluyor.');
            this.contentUpdater.stopProgressUpdater();

            this.logger.action(`1. Adım: Yeni içerik pasif sete yükleniyor (Set: ${passiveSet}).`);
            this.contentUpdater.updateAll(passiveSet, data);

            const outgoingElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
            const incomingElementIds = this.config.elements.filter(id => id.endsWith(`_${passiveSet}`));
            const incomingImageIds = incomingElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG');
            
            this.logger.group('FAZ 1: HAZIRLIK');
            this.animationService._flipZIndexes();
            incomingElementIds.forEach(id => this.animationService.prepareElement(id, 'transitionIn'));
            outgoingElementIds.forEach(id => this.animationService.prepareElement(id, 'transitionOut'));
            await this.animationService.waitForImages(incomingImageIds);
            this.logger.groupEnd();

            this.logger.group('FAZ 2: ANİMASYON');
            const outgoingAnimations = outgoingElementIds.map(id => this.animationService.execute(id, 'transitionOut'));
            const incomingAnimations = incomingElementIds.map(id => this.animationService.execute(id, 'transitionIn'));
            await Promise.all([...outgoingAnimations, ...incomingAnimations]);
            this.logger.info('Tüm geçiş animasyonları tamamlandı.');
            this.logger.groupEnd();

            this.logger.group('FAZ 3: TEMİZLİK');
            outgoingElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            incomingElementIds.forEach(id => this.animationService.cleanupElement(id, 'incoming'));
            this.contentUpdater.reset(activeSet);
            this.logger.groupEnd();
            
            this.logger.action("SON ADIM: StateService'e geçişin tamamlandığı bildiriliyor.");
            this.stateService.finalizeTransition(passiveSet);
            
        } catch (error) {
            this.logger.error('runTransition sırasında hata:', error);
        } finally {
            this.isBusy = false;
            this.logger.info('Transition eylemi tamamlandı. Meşgul durumu kaldırıldı.');
            this.processPendingEvent();
            this.logger.groupEnd();
        }
    }

    async runOutro({ activeSet }) {
        this.logger.group('Eylem: WIDGET OUTRO');
        try {
            this.logger.action('1. Adım: İlerleme çubuğu durduruluyor.');
            this.contentUpdater.stopProgressUpdater();
            
            this.logger.action('2. Adım: Widget inaktif duruma getiriliyor.');
            this.widgetElement.classList.add(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            
            const outroElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
            this.logger.action(`3. Adım: Çıkış yapılacak elementler temizleniyor (${outroElementIds.length} adet).`);
            outroElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            
            this.logger.action(`4. Adım: Aktif set içeriği sıfırlanıyor (Set: ${activeSet}).`);
            this.contentUpdater.reset(activeSet);
            
            this.logger.info('Outro tamamlandı.');
        } catch (error) {
            this.logger.error('runOutro sırasında hata:', error);
        } finally {
             this.logger.groupEnd();
        }
    }

    processPendingEvent() {
        if (!this.pendingEvent) return;
        
        const { type, detail } = this.pendingEvent;
        this.logger.warn(`Sıradaki olay işleniyor: ${type}`);
        this.pendingEvent = null;
        
        switch (type) {
            case 'intro': this.runIntro(detail); break;
            case 'transition': this.runTransition(detail); break;
            default: this.logger.error(`Bilinmeyen bekleyen olay tipi: ${type}`);
        }
    }
}
