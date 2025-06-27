/**
 * @file CSSAnimationParser.js
 * @description Canlı stil sayfalarından @keyframes kurallarını okur ve
 * bir animasyonun başlangıç stillerini döndürür.
 */
class CSSAnimationParser {
    constructor() {
        this.styleCache = new Map(); // Ayrıştırılan stilleri tekrar tekrar aratmamak için önbellek
        console.log('[CSSAnimationParser] Servis başlatıldı.');
    }

    /**
     * Verilen animasyon adının başlangıç stillerini CSS'ten bulur ve döndürür.
     * @param {string} animationName - @keyframes'te tanımlanan animasyon adı.
     * @returns {object | null} Stil nesnesi (örn: { opacity: '0' }) veya null.
     */
    getInitialStyle(animationName) {
        // 1. Önbelleği kontrol et
        if (this.styleCache.has(animationName)) {
            return this.styleCache.get(animationName);
        }

        // 2. Tüm stil sayfalarını gez
        for (const sheet of document.styleSheets) {
            try {
                // Not: Farklı bir domain'den yüklenen CSS dosyaları burada hata verebilir (CORS).
                const rules = sheet.cssRules || sheet.rules;
                for (const rule of rules) {
                    // 3. @keyframes kuralını bul
                    if (rule.type === CSSRule.KEYFRAMES_RULE && rule.name === animationName) {
                        // 4. 'from' veya '0%' kuralını bul
                        for (const keyframe of rule.cssRules) {
                            if (keyframe.keyText === 'from' || keyframe.keyText === '0%') {
                                // 5. Stil nesnesini oluştur ve döndür
                                const styles = {};
                                for (const prop of keyframe.style) {
                                    styles[prop] = keyframe.style.getPropertyValue(prop);
                                }
                                // TEŞHİS KODU: Hangi stillerin bulunduğunu konsola yazdır.
                                console.log(`%c[CSSAnimationParser] Found initial styles for '${animationName}':`, 'color: #007bff;', JSON.stringify(styles));
                                this.styleCache.set(animationName, styles); // Önbelleğe ekle
                                return styles;
                            }
                        }
                    }
                }
            } catch (e) {
                // console.warn(`Stil sayfası okunamadı (CORS hatası olabilir): ${sheet.href}`, e);
            }
        }

        console.warn(`[CSSAnimationParser] '${animationName}' animasyonu için başlangıç karesi bulunamadı.`);
        this.styleCache.set(animationName, null); // Bulunamadığını da önbelleğe al
        return null;
    }
}