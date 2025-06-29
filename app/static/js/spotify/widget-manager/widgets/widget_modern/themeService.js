class ThemeService {
    constructor() {
        this.themeData = null;
    }

    async load() {
        if (window.themeConfig) {
            this.themeData = window.themeConfig;
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