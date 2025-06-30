class WidgetDOMManager {
    constructor(widgetElement, services) {
        this.widgetElement = widgetElement;
        this.stateService = services.stateService;
        this.animationService = services.animationService;
        this.contentUpdater = services.contentUpdater;
        this.errorContainer = widgetElement.querySelector('.WidgetErrorContainer');

        // Track active animations for cleanup
        this.activeAnimations = [];
        
        this._bindEvents();
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
        try {
            // 1. Wait for all content to be updated
            await this.contentUpdater.updateAllForSet(detail.set, detail.data);

            // 2. Let the browser render the new content
            await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));

            // 3. Play the intro animation and wait for it to complete
            const introAnimation = await this.animationService.playIntro({ set: detail.set });
            this.activeAnimations.push(introAnimation);
            
            // 4. Start the progress bar after the intro animation
            this.contentUpdater.startProgressUpdater(detail.data, detail.set);
        } catch (error) {
            console.error('Error in _handleIntro:', error);
        }
    }
    
    async _handleOutro(detail) {
        try {
            const outroAnimation = await this.animationService.playOutro();
            this.activeAnimations.push(outroAnimation);
            this.contentUpdater.stopAllProgressUpdaters();
        } catch (error) {
            console.error('Error in _handleOutro:', error);
        }
    }

    async _handleTransition(detail) {
        try {
            // Update content for the passive set
            await this.contentUpdater.updateAllForSet(detail.passiveSet, detail.data);
            this.contentUpdater.startProgressUpdater(detail.data, detail.passiveSet);

            // Let the browser render the new content
            await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        
            // Play the transition animation and wait for it to complete
            const transitionAnimation = await this.animationService.playTransition({
                activeSet: detail.activeSet,
                passiveSet: detail.passiveSet
            });
            this.activeAnimations.push(transitionAnimation);
            
            // Clean up the old active set
            this.contentUpdater.stopProgressUpdater(detail.activeSet);
            this.stateService.finalizeTransition(detail.passiveSet);
            this.contentUpdater.clearAllForSet(detail.activeSet);
        } catch (error) {
            console.error('Error in _handleTransition:', error);
        }
    }

    _handleSync({ data, set }) {
        this.contentUpdater.startProgressUpdater(data, set);
    }
    
    _handleError({ message }) {
        if (this.errorContainer) {
            this.errorContainer.innerText = message;
            this.errorContainer.style.display = 'block';
        }
        
        // Play outro animation on error
        this._handleOutro();
        this.contentUpdater.stopAllProgressUpdaters();
    }
    
    _handleClearError() {
        if (this.errorContainer && this.errorContainer.style.display !== 'none') {
            this.errorContainer.style.display = 'none';
        }
    }
    
    // Clean up any active animations when the widget is destroyed
    destroy() {
        this.activeAnimations.forEach(animation => {
            if (animation && typeof animation.kill === 'function') {
                animation.kill();
            }
        });
        this.activeAnimations = [];
    }
}