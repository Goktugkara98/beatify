// ===================================================================================
// DOSYA ADI: WidgetDOMManager.js
// AÇIKLAMA: DOM manipülasyonlarını, animasyonları ve içerik güncellemelerini yönetir.
// YENİ YAPI NOTU: Bu sınıf, loglama hiyerarşisinin ana orkestratörüdür.
//                 Her bir 'run' metodu (intro, transition, outro) kendi ana eylem
//                 grubunu oluşturur ve içindeki adımları 'Faz' alt gruplarına ayırır.
// ===================================================================================
class WidgetDOMManager {
    static CSS_CLASSES = { WIDGET_INACTIVE: 'widget-inactive' };

    constructor(widgetElement, config, stateService, logger) {
        this.logger = logger;
        this.CALLER_FILE = 'WidgetDOMManager.js';

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

        this.logger.info(this.CALLER_FILE, "WidgetDOMManager oluşturuluyor. Uzman servisler başlatılacak.");
        this.contentUpdater = new ContentUpdaterService(this.widgetElement, this.logger);
        this.animationService = new AnimationService(this.widgetElement, this.config, this.logger);

        this.listenToEvents();
        this.logger.info(this.CALLER_FILE, "Kurulum tamamlandı ve olaylar dinleniyor.");
    }

    listenToEvents() {
        const createEventHandler = (eventName, handler) => {
            this.widgetElement.addEventListener(eventName, (e) => {
                if (this.isBusy && ['widget:intro', 'widget:transition'].includes(eventName)) {
                    this.logger.warn(this.CALLER_FILE, `Widget meşgul. Olay sıraya alınıyor: ${eventName.split(':')[1]}`);
                    this.pendingEvent = { type: eventName.split(':')[1], detail: e.detail };
                } else {
                    handler(e.detail);
                }
            });
        };

        createEventHandler('widget:intro', (detail) => this.runIntro(detail));
        createEventHandler('widget:transition', (detail) => this.runTransition(detail));
        createEventHandler('widget:outro', (detail) => this.runOutro(detail));
        
        this.widgetElement.addEventListener('widget:sync', (e) => {
            if (!this.isBusy) {
                this.contentUpdater.startProgressUpdater(e.detail.data, e.detail.set);
            } else {
                this.logger.warn(this.CALLER_FILE, "Widget meşgul olduğu için 'sync' işlemi atlandı.");
            }
        });
        this.widgetElement.addEventListener('widget:error', (e) => this.contentUpdater.displayError(e.detail.message));
        this.widgetElement.addEventListener('widget:clear-error', () => this.contentUpdater.clearError());
    }

    async runIntro({ set, data }) {
        this.logger.group('Eylem: WIDGET INTRO');
        this.isBusy = true;
        try {
            this.logger.subgroup('[DOMManager] Faz 1: İçerik ve Hazırlık');
            this.contentUpdater.updateAll(set, data);
            const introElementIds = this.config.elements.filter(id => id.endsWith(`_${set}`));
            introElementIds.forEach(id => this.animationService.prepareElement(id, 'intro'));
            const imageElementIds = introElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG');
            await this.animationService.waitForImages(imageElementIds);
            this.logger.groupEnd();
            
            this.logger.subgroup('[DOMManager] Faz 2: Animasyon');
            this.widgetElement.classList.remove(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            const introAnimations = introElementIds.map(id => this.animationService.execute(id, 'intro'));
            await Promise.all(introAnimations);
            this.logger.info(this.CALLER_FILE, 'Tüm intro animasyonları tamamlandı.');
            this.logger.groupEnd();

            this.logger.subgroup('[DOMManager] Faz 3: Sonlandırma');
            this.contentUpdater.startProgressUpdater(data, set);
            this.logger.groupEnd();
            
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
            this.logger.subgroup('[DOMManager] Faz 0: Başlangıç');
            this.contentUpdater.stopProgressUpdater();
            this.contentUpdater.updateAll(passiveSet, data);
            this.logger.groupEnd();

            const outgoingElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
            const incomingElementIds = this.config.elements.filter(id => id.endsWith(`_${passiveSet}`));
            
            this.logger.subgroup('[DOMManager] Faz 1: Animasyon Hazırlığı');
            this.animationService._flipZIndexes();
            incomingElementIds.forEach(id => this.animationService.prepareElement(id, 'transitionIn'));
            outgoingElementIds.forEach(id => this.animationService.prepareElement(id, 'transitionOut'));
            const incomingImageIds = incomingElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG');
            await this.animationService.waitForImages(incomingImageIds);
            this.logger.groupEnd();

            this.logger.subgroup('[DOMManager] Faz 2: Animasyon Yürütme');
            const outgoingAnimations = outgoingElementIds.map(id => this.animationService.execute(id, 'transitionOut'));
            const incomingAnimations = incomingElementIds.map(id => this.animationService.execute(id, 'transitionIn'));
            await Promise.all([...outgoingAnimations, ...incomingAnimations]);
            this.logger.info(this.CALLER_FILE, 'Tüm geçiş animasyonları tamamlandı.');
            this.logger.groupEnd();

            this.logger.subgroup('[DOMManager] Faz 3: Temizlik ve Sonlandırma');
            outgoingElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            incomingElementIds.forEach(id => this.animationService.cleanupElement(id, 'incoming'));
            this.contentUpdater.reset(activeSet);
            this.logger.action(this.CALLER_FILE, "StateService'e geçişin tamamlandığı bildiriliyor.");
            this.stateService.finalizeTransition(passiveSet);
            this.logger.groupEnd();
            
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
            this.logger.info(this.CALLER_FILE, "Outro işlemi başlıyor...");
            this.contentUpdater.stopProgressUpdater();
            this.widgetElement.classList.add(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            
            const outroElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
            outroElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
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
