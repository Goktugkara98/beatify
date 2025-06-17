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
        this.isBusy = false;
        this.pendingEvent = null;

        this.contentUpdater = new ContentUpdaterService(this.widgetElement);
        this.animationService = new AnimationService(this.widgetElement, this.config);

        this._listenToEvents();
    }

    /**
     * StateService tarafından tetiklenen widget olaylarını dinler.
     * @private
     */
    _listenToEvents() {
        const createEventHandler = (eventName, handler) => {
            this.widgetElement.addEventListener(eventName, (e) => {
                const isHighPriorityEvent = ['widget:intro', 'widget:transition'].includes(eventName);
                if (this.isBusy && isHighPriorityEvent) {
                    this.pendingEvent = { type: eventName.split(':')[1], detail: e.detail };
                } else {
                    handler.call(this, e.detail);
                }
            });
        };

        createEventHandler('widget:intro', this.runIntro);
        createEventHandler('widget:transition', this.runTransition);
        createEventHandler('widget:outro', this.runOutro);
        
        this.widgetElement.addEventListener('widget:sync', (e) => {
            if (!this.isBusy) {
                this.contentUpdater.startProgressUpdater(e.detail.data, e.detail.set);
            }
        });
        this.widgetElement.addEventListener('widget:error', (e) => this.contentUpdater.displayError(e.detail.message));
        this.widgetElement.addEventListener('widget:clear-error', () => this.contentUpdater.clearError());
    }

    /**
     * Widget'ın ilk açılış animasyonunu (intro) çalıştırır.
     */
    async runIntro({ set, data }) {
        if (this.isBusy) return;
        this.isBusy = true;
        
        try {
            this.contentUpdater.updateAll(set, data);
            const introElementIds = this.config.elements.filter(id => id.endsWith(`_${set}`));
            introElementIds.forEach(id => this.animationService.prepareElement(id, 'intro'));
            await this.animationService.waitForImages(introElementIds.filter(id => document.getElementById(id)?.tagName === 'IMG'));
            
            this.widgetElement.classList.remove(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            await Promise.all(introElementIds.map(id => this.animationService.execute(id, 'intro')));
            
            this.contentUpdater.startProgressUpdater(data, set);
        } catch (error) {
            console.error('runIntro sırasında hata:', error);
        } finally {
            this.isBusy = false;
            this._processPendingEvent();
        }
    }

    /**
     * Şarkı değiştirme animasyonunu (transition) çalıştırır.
     */
    async runTransition({ activeSet, passiveSet, data }) {
        if (this.isBusy) return;
        this.isBusy = true;
        
        try {
            this.contentUpdater.stopProgressUpdater();
            this.contentUpdater.updateAll(passiveSet, data);

            const outgoingIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
            const incomingIds = this.config.elements.filter(id => id.endsWith(`_${passiveSet}`));
            
            this.animationService._flipZIndexes();
            incomingIds.forEach(id => this.animationService.prepareElement(id, 'transitionIn'));
            outgoingIds.forEach(id => this.animationService.prepareElement(id, 'transitionOut'));
            await this.animationService.waitForImages(incomingIds.filter(id => document.getElementById(id)?.tagName === 'IMG'));

            const animations = [
                ...outgoingIds.map(id => this.animationService.execute(id, 'transitionOut')),
                ...incomingIds.map(id => this.animationService.execute(id, 'transitionIn'))
            ];
            await Promise.all(animations);

            outgoingIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            incomingIds.forEach(id => this.animationService.cleanupElement(id, 'incoming'));
            this.contentUpdater.reset(activeSet);
            
            this.stateService.finalizeTransition(passiveSet);
        } catch (error) {
            console.error('runTransition sırasında hata:', error);
        } finally {
            this.isBusy = false;
            this._processPendingEvent();
        }
    }

    /**
     * Müzik durduğunda widget'ı kapatma (outro) işlemini yürütür.
     */
    async runOutro({ activeSet }) {
        try {
            this.contentUpdater.stopProgressUpdater();
            this.widgetElement.classList.add(WidgetDOMManager.CSS_CLASSES.WIDGET_INACTIVE);
            
            const outroElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
            outroElementIds.forEach(id => this.animationService.cleanupElement(id, 'outgoing'));
            this.contentUpdater.reset(activeSet);
        } catch (error) {
            console.error('runOutro sırasında hata:', error);
        }
    }

    /**
     * Meşgul durumu bittiğinde sırada bekleyen bir olay varsa onu işler.
     * @private
     */
    _processPendingEvent() {
        if (!this.pendingEvent) return;
        
        const { type, detail } = this.pendingEvent;
        this.pendingEvent = null;
        
        switch (type) {
            case 'intro': this.runIntro(detail); break;
            case 'transition': this.runTransition(detail); break;
            default: console.error(`Bilinmeyen bekleyen olay tipi: ${type}`);
        }
    }
}
