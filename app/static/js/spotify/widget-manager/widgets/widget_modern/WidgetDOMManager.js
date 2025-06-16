// ===================================================================================
// DOSYA ADI: WidgetDOMManager.js
// AÇIKLAMA: DOM manipülasyonlarını, animasyonları ve içerik güncellemelerini yönetir.
// ===================================================================================
class WidgetDOMManager {
    static CSS_CLASSES = { WIDGET_INACTIVE: 'widget-inactive' };

    constructor(widgetElement, config, stateService, logger) {
        this.logger = logger;
        this.CALLER_FILE = 'WidgetDOMManager.js';

        this.logger.subgroup('WidgetDOMManager Kurulumu (constructor)');

        if (!widgetElement || !config || !stateService) {
            const error = new Error("Gerekli tüm modüller sağlanmalıdır.");
            this.logger.error(this.CALLER_FILE, "Başlatma Hatası:", error);
            throw error;
        }

        this.widgetElement = widgetElement;
        this.config = config;
        this.stateService = stateService;
        this.isBusy = false;
        this.pendingEvent = null;

        this.logger.action(this.CALLER_FILE, "Uzman servisler oluşturuluyor...");
        this.contentUpdater = new ContentUpdaterService(this.widgetElement, this.logger);
        this.animationService = new AnimationService(this.widgetElement, this.config, this.logger);

        this.listenToEvents();
        this.logger.info(this.CALLER_FILE, "Kurulum tamamlandı.");
        this.logger.groupEnd();
    }

    listenToEvents() {
        this.logger.action(this.CALLER_FILE, "Olay dinleyicileri (event listeners) ayarlanıyor.");
        
        const handleEvent = (eventName, handler) => {
            this.widgetElement.addEventListener(eventName, (e) => {
                this.logger.subgroup(`Olay Alındı: ${eventName}`);
                this.logger.data(this.CALLER_FILE, "Olay Detayı", e.detail);

                if (this.isBusy && (eventName === 'widget:intro' || eventName === 'widget:transition')) {
                    this.logger.warn(this.CALLER_FILE, "Widget meşgul, olay sıraya alınıyor.");
                    this.pendingEvent = { type: eventName.split(':')[1], detail: e.detail };
                } else {
                    handler(e.detail);
                }
                this.logger.groupEnd();
            });
        };

        handleEvent('widget:intro', (detail) => this.runIntro(detail));
        handleEvent('widget:transition', (detail) => this.runTransition(detail));
        handleEvent('widget:outro', (detail) => this.runOutro(detail));
        
        this.widgetElement.addEventListener('widget:sync', (e) => {
             this.logger.subgroup("Olay Alındı: widget:sync");
             this.logger.data(this.CALLER_FILE, "Olay Detayı", e.detail);
            if (!this.isBusy) {
                this.contentUpdater.startProgressUpdater(e.detail.data, e.detail.set);
            } else {
                this.logger.warn(this.CALLER_FILE, "Widget meşgul, 'sync' işlemi atlanıyor.");
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
            this.logger.action(this.CALLER_FILE, `1. Adım: İçerik dolduruluyor (Set: ${set}).`);
            this.contentUpdater.updateAll(set, data);

            const introElementIds = this.config.elements.filter(id => id.endsWith(`_${set}`));
            const imageElementIds = introElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG');
            
            this.logger.action(this.CALLER_FILE, '2. Adım: Animasyonlar için elementler hazırlanıyor.');
            introElementIds.forEach(id => this.animationService.prepareElement(id, 'intro'));

            this.logger.action(this.CALLER_FILE, `3. Adım: Resimlerin yüklenmesi bekleniyor (${imageElementIds.length} adet).`);
            await this.animationService.waitForImages(imageElementIds);
            
            this.logger.action(this.CALLER_FILE, '4. Adım: Widget aktive ediliyor ve animasyonlar başlatılıyor.');
            this.widgetElement.classList.remove(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            
            const introAnimations = introElementIds.map(id => this.animationService.execute(id, 'intro'));
            await Promise.all(introAnimations);
            this.logger.info(this.CALLER_FILE, 'Tüm intro animasyonları tamamlandı.');

            this.logger.action(this.CALLER_FILE, '5. Adım: İlerleme çubuğu başlatılıyor.');
            this.contentUpdater.startProgressUpdater(data, set);
            
        } catch (error) {
            this.logger.error(this.CALLER_FILE, 'runIntro sırasında hata:', error);
        } finally {
            this.isBusy = false;
            this.logger.info(this.CALLER_FILE, 'Intro eylemi tamamlandı. Meşgul durumu kaldırıldı.');
            this.processPendingEvent();
            this.logger.groupEnd();
        }
    }

    async runTransition({ activeSet, passiveSet, data }) {
        this.logger.group(`Eylem: ŞARKI GEÇİŞİ ('${activeSet}' -> '${passiveSet}')`);
        this.isBusy = true;
        try {
            this.logger.action(this.CALLER_FILE, '0. Adım: Mevcut ilerleme çubuğu durduruluyor.');
            this.contentUpdater.stopProgressUpdater();

            this.logger.action(this.CALLER_FILE, `1. Adım: Yeni içerik pasif sete yükleniyor (Set: ${passiveSet}).`);
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
            this.logger.info(this.CALLER_FILE, 'Tüm geçiş animasyonları tamamlandı.');
            this.logger.groupEnd();

            this.logger.group('FAZ 3: TEMİZLİK');
            outgoingElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            incomingElementIds.forEach(id => this.animationService.cleanupElement(id, 'incoming'));
            this.contentUpdater.reset(activeSet);
            this.logger.groupEnd();
            
            this.logger.action(this.CALLER_FILE, "SON ADIM: StateService'e geçişin tamamlandığı bildiriliyor.");
            this.stateService.finalizeTransition(passiveSet);
            
        } catch (error) {
            this.logger.error(this.CALLER_FILE, 'runTransition sırasında hata:', error);
        } finally {
            this.isBusy = false;
            this.logger.info(this.CALLER_FILE, 'Transition eylemi tamamlandı. Meşgul durumu kaldırıldı.');
            this.processPendingEvent();
            this.logger.groupEnd();
        }
    }

    async runOutro({ activeSet }) {
        this.logger.group('Eylem: WIDGET OUTRO');
        try {
            this.logger.action(this.CALLER_FILE, '1. Adım: İlerleme çubuğu durduruluyor.');
            this.contentUpdater.stopProgressUpdater();
            
            this.logger.action(this.CALLER_FILE, '2. Adım: Widget inaktif duruma getiriliyor.');
            this.widgetElement.classList.add(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            
            const outroElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
            this.logger.action(this.CALLER_FILE, `3. Adım: Çıkış yapılacak elementler temizleniyor (${outroElementIds.length} adet).`);
            outroElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            
            this.logger.action(this.CALLER_FILE, `4. Adım: Aktif set içeriği sıfırlanıyor (Set: ${activeSet}).`);
            this.contentUpdater.reset(activeSet);
            
            this.logger.info(this.CALLER_FILE, 'Outro tamamlandı.');
        } catch (error) {
            this.logger.error(this.CALLER_FILE, 'runOutro sırasında hata:', error);
        } finally {
             this.logger.groupEnd();
        }
    }

    processPendingEvent() {
        if (!this.pendingEvent) return;
        
        const { type, detail } = this.pendingEvent;
        this.logger.warn(this.CALLER_FILE, `Sıradaki olay işleniyor: ${type}`);
        this.pendingEvent = null;
        
        switch (type) {
            case 'intro': this.runIntro(detail); break;
            case 'transition': this.runTransition(detail); break;
            default: this.logger.error(this.CALLER_FILE, `Bilinmeyen bekleyen olay tipi: ${type}`);
        }
    }
}
