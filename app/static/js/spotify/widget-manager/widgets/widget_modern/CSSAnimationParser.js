class CSSAnimationParser {
    constructor() {
        this.styleCache = new Map();
    }

    getInitialStyle(animationName) {
        if (this.styleCache.has(animationName)) {
            return this.styleCache.get(animationName);
        }

        for (const sheet of document.styleSheets) {
            try {
                const rules = sheet.cssRules || sheet.rules;
                for (const rule of rules) {
                    if (rule.type === CSSRule.KEYFRAMES_RULE && rule.name === animationName) {
                        for (const keyframe of rule.cssRules) {
                            if (keyframe.keyText === 'from' || keyframe.keyText === '0%') {
                                const styles = {};
                                for (const prop of keyframe.style) {
                                    styles[prop] = keyframe.style.getPropertyValue(prop);
                                }
                                this.styleCache.set(animationName, styles);
                                return styles;
                            }
                        }
                    }
                }
            } catch (e) {
                // Stil sayfası okunamadı (CORS hatası olabilir)
            }
        }

        this.styleCache.set(animationName, null);
        return null;
    }
}