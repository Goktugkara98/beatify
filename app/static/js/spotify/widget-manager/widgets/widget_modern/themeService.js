class ThemeService {
    constructor() {
        this.themeData = null;
    }

    _normalizeThemeConfig(cfg) {
        const theme = cfg && typeof cfg === 'object' ? cfg : {};
        if (!theme.components || typeof theme.components !== 'object') {
            theme.components = {};
        }

        const animTypes = ['intro', 'transitionIn', 'transitionOut', 'outro'];
        Object.keys(theme.components).forEach((componentName) => {
            const comp = theme.components[componentName];
            if (!comp || typeof comp !== 'object') return;

            ['set_a', 'set_b'].forEach((setKey) => {
                const setData = comp[setKey];
                if (!setData || typeof setData !== 'object') return;
                if (!setData.animations || typeof setData.animations !== 'object') {
                    setData.animations = {};
                }

                animTypes.forEach((animType) => {
                    if (!setData.animations[animType] || typeof setData.animations[animType] !== 'object') {
                        setData.animations[animType] = { animation: 'none', type: 'none', duration: 0, delay: 0 };
                    }
                    const a = setData.animations[animType];

                    const name = (a.type || a.animation || 'none');
                    a.type = a.type || name;
                    a.animation = a.animation || name;

                    a.duration = typeof a.duration === 'number' ? a.duration : parseInt(a.duration || 0);
                    if (Number.isNaN(a.duration)) a.duration = 0;
                    a.delay = typeof a.delay === 'number' ? a.delay : parseInt(a.delay || 0);
                    if (Number.isNaN(a.delay)) a.delay = 0;

                    setData.animations[animType] = a;
                });
            });
        });

        return theme;
    }

    async load() {
        if (window.themeConfig) {
            // Widget tarafında da normalize et: özellikle `type` eksikse transition'da flash görülebilir.
            this.themeData = this._normalizeThemeConfig(window.themeConfig);
            return true;
        } else {
            this.themeData = null;
            return false;
        }
    }

    getComponentSetData(componentName, set) {
        if (!this.themeData) return null;
        const component = this.themeData.components[componentName];
        if (!component) return null;
        
        return component[`set_${set}`];
    }
}