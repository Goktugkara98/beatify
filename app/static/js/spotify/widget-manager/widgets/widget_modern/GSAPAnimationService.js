/**
 * GSAPAnimationService.js
 * Handles all widget animations using GSAP
 */

class GSAPAnimationService {
    constructor(widgetElement, themeService) {
        this.widgetElement = widgetElement;
        this.themeService = themeService;
        
        // Track active animations by type for better cleanup
        this.activeAnimations = {
            intro: null,
            outro: null,
            transition: null
        };
        
        // Track animation states
        this.currentState = {
            activeSet: null,
            isAnimating: false
        };
    }

    /**
     * Play intro animation for the specified set
     * @param {Object} options - Animation options
     * @param {string} options.set - The set to animate ('a' or 'b')
     */
    async playIntro({ set }) {
        if (!this.themeService?.themeData) {
            return null;
        }

        // Kill any running intro/outro animations
        this._killAnimation('intro');
        this._killAnimation('outro');
        
        // Update state
        this.currentState.activeSet = set;
        this.currentState.isAnimating = true;

        try {
            // Apply initial z-indexes
            this._applyZIndexes(set, 'active');

            const container = this.widgetElement.querySelector(`.WidgetContainer_${set}`);
            if (!container) return null;

            // Create a timeline for the intro animation
            const tl = gsap.timeline({
                id: 'intro',
                onComplete: () => {
                    this.currentState.isAnimating = false;
                },
                onInterrupt: () => {
                    this.currentState.isAnimating = false;
                }
            });
            
            this.activeAnimations.intro = tl;

            // Get all components that need intro animations
            const components = this.themeService.themeData.components;
        
            Object.entries(components).forEach(([componentName, componentData]) => {
                const setData = componentData[`set_${set}`];
                const introAnim = setData?.animations?.intro;
                
                if (introAnim && introAnim.animation !== 'none') {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (!element) return;

                    // Map CSS animation to GSAP equivalent
                    this._addAnimationToTimeline(tl, element, introAnim);
                }
            });

            return tl;
        } catch (error) {
            console.error('Error playing intro animation:', error);
            this.currentState.isAnimating = false;
            return null;
        }
    }

    /**
     * Play outro animation for the active set
     */
    async playOutro() {
        if (!this.themeService?.themeData) {
            return null;
        }
        
        // Kill any running intro/outro animations
        this._killAnimation('intro');
        this._killAnimation('outro');
        
        const activeSet = this.currentState.activeSet || 
                         (this.widgetElement.querySelector('.WidgetContainer_a.passive') ? 'b' : 'a');
        
        this.currentState.isAnimating = true;
        
        try {
            const container = this.widgetElement.querySelector(`.WidgetContainer_${activeSet}`);
            if (!container) return null;

            // Create a new timeline for the outro
            const tl = gsap.timeline({
                id: 'outro',
                onComplete: () => {
                    this.currentState.isAnimating = false;
                },
                onInterrupt: () => {
                    this.currentState.isAnimating = false;
                }
            });
            
            this.activeAnimations.outro = tl;

            // Get all components that need outro animations
            const components = this.themeService.themeData.components;
        
            Object.entries(components).forEach(([componentName, componentData]) => {
                const setData = componentData[`set_${activeSet}`];
                const outroAnim = setData?.animations?.outro;
                
                if (outroAnim && outroAnim.animation !== 'none') {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (!element) return;

                    this._addAnimationToTimeline(tl, element, outroAnim);
                }
            });

            return tl;
        } catch (error) {
            console.error('Error playing outro animation:', error);
            this.currentState.isAnimating = false;
            return null;
        }
    }

    /**
     * Play transition between active and passive sets
     * @param {Object} options - Transition options
     * @param {string} options.activeSet - The currently active set
     * @param {string} options.passiveSet - The set to transition to
     */
    async playTransition({ activeSet, passiveSet }) {
        if (!this.themeService?.themeData) {
            return null;
        }

        const activeContainer = this.widgetElement.querySelector(`.WidgetContainer_${activeSet}`);
        const passiveContainer = this.widgetElement.querySelector(`.WidgetContainer_${passiveSet}`);
        
        if (!activeContainer || !passiveContainer) return null;
        
        // Kill any running transitions
        this._killAnimation('transition');
        
        this.currentState.activeSet = passiveSet;
        this.currentState.isAnimating = true;

        try {
            // Apply z-indexes for transition
            this._applyZIndexes(passiveSet, 'active');
            this._applyZIndexes(activeSet, 'passive');

            // Create a timeline for the transition
            const tl = gsap.timeline({
                id: 'transition',
                onComplete: () => {
                    this.currentState.isAnimating = false;
                },
                onInterrupt: () => {
                    this.currentState.isAnimating = false;
                }
            });
            
            this.activeAnimations.transition = tl;

            // Get all components that need transition animations
            const components = this.themeService.themeData.components;
            
            // First, handle the active set (outro)
            Object.entries(components).forEach(([componentName, componentData]) => {
                const setData = componentData[`set_${activeSet}`];
                const outroAnim = setData?.animations?.outro;
                
                if (outroAnim && outroAnim.animation !== 'none') {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (!element) return;

                    this._addAnimationToTimeline(tl, element, outroAnim);
                }
            });

            // Then handle the passive set (intro)
            Object.entries(components).forEach(([componentName, componentData]) => {
                const setData = componentData[`set_${passiveSet}`];
                const introAnim = setData?.animations?.intro;
                
                if (introAnim && introAnim.animation !== 'none') {
                    const element = this.widgetElement.querySelector(`.${setData.animationContainer}`);
                    if (!element) return;

                    this._addAnimationToTimeline(tl, element, introAnim, '>');
                }
            });

            return tl;
        } catch (error) {
            console.error('Error playing transition animation:', error);
            this.currentState.isAnimating = false;
            return null;
        }
    }

    /**
     * Kill a specific animation by type
     * @param {string} type - The animation type to kill ('intro', 'outro', 'transition')
     */
    _killAnimation(type) {
        if (this.activeAnimations[type]) {
            this.activeAnimations[type].kill();
            this.activeAnimations[type] = null;
        }
    }

    /**
     * Clean up all animations
     */
    destroy() {
        // Kill all active animations
        Object.keys(this.activeAnimations).forEach(type => {
            this._killAnimation(type);
        });
        
        // Reset state
        this.currentState = {
            activeSet: null,
            isAnimating: false
        };
    }
    
    /**
     * Check if any animation is currently playing
     * @returns {boolean} True if an animation is in progress
     */
    isAnimating() {
        return this.currentState.isAnimating;
    }
    
    /**
     * Get the currently active set
     * @returns {string|null} The active set ('a' or 'b') or null if unknown
     */
    getActiveSet() {
        return this.currentState.activeSet;
    }

    /**
     * Apply z-indexes based on the current state
     * @param {string} set - The set to apply z-indexes to
     * @param {string} state - The state ('active' or 'passive')
     */
    _applyZIndexes(set, state) {
        const container = this.widgetElement.querySelector(`.WidgetContainer_${set}`);
        if (!container) return;

        // Apply z-index based on state
        container.style.zIndex = state === 'active' ? '2' : '1';
        container.classList.toggle('active', state === 'active');
        container.classList.toggle('passive', state === 'passive');
    }

    /**
     * Add animation to timeline based on animation config
     * @param {GSAPTimeline} timeline - The GSAP timeline to add to
     * @param {HTMLElement} element - The element to animate
     * @param {Object} animConfig - The animation configuration
     * @param {string} position - Position in the timeline (default: 0)
     */
    _addAnimationToTimeline(timeline, element, animConfig, position = 0) {
        if (!element) {
            console.warn('No element provided for animation');
            return;
        }
        
        if (!animConfig) {
            console.warn('No animation configuration provided for element:', element);
            return;
        }
        
        // Debug log the animation config
        console.log('Animation config:', {
            element: element,
            config: animConfig,
            position: position
        });
        
        const { 
            type: animation = 'fade', // Default to 'fade' if type is not specified
            duration = 300, 
            delay = 0, 
            ease = 'power2.out' 
        } = animConfig;
        
        // Convert milliseconds to seconds for GSAP
        const durationSec = duration / 1000;
        const delaySec = delay / 1000;
        
        switch (animation) {
            case 'fade-in':
                timeline.fromTo(element,
                    { opacity: 0 },
                    { 
                        opacity: 1, 
                        duration: durationSec, 
                        delay: delaySec, 
                        ease: ease 
                    },
                    position
                );
                break;
            case 'fade':
                timeline.fromTo(element, 
                    { opacity: 0 },
                    { 
                        opacity: 1, 
                        duration: durationSec, 
                        delay: delaySec, 
                        ease: ease 
                    },
                    position
                );
                break;
                
            case 'slide-up':
                timeline.fromTo(element,
                    { y: '100%', opacity: 0 },
                    { 
                        y: 0, 
                        opacity: 1, 
                        duration: durationSec, 
                        delay: delaySec, 
                        ease: ease 
                    },
                    position
                );
                break;
                
            case 'slide-down':
                timeline.fromTo(element,
                    { y: '-100%', opacity: 0 },
                    { 
                        y: 0, 
                        opacity: 1, 
                        duration: durationSec, 
                        delay: delaySec, 
                        ease: ease 
                    },
                    position
                );
                break;
                
            case 'slide-left':
                timeline.fromTo(element,
                    { x: '100%', opacity: 0 },
                    { 
                        x: 0, 
                        opacity: 1, 
                        duration: durationSec, 
                        delay: delaySec, 
                        ease: ease 
                    },
                    position
                );
                break;
                
            case 'slide-right':
                timeline.fromTo(element,
                    { x: '-100%', opacity: 0 },
                    { 
                        x: 0, 
                        opacity: 1, 
                        duration: durationSec, 
                        delay: delaySec, 
                        ease: ease 
                    },
                    position
                );
                break;
                
            // Add more animation types as needed
            default:
                console.warn(`Unsupported animation type: ${animation}`);
                break;
        }
    }
}

// Export to global scope for non-module scripts
window.GSAPAnimationService = GSAPAnimationService;
