/**
 * @class AnimationService
 * @description CSS animasyonlarını yönetir, elementleri animasyon için hazırlar, yürütür ve sonrasında temizler.
 */
class AnimationService {
    /**
     * Z-index katmanlarını tanımlayan statik konfigürasyon.
     * @static
     */
    static Z_INDEX_CONFIG = {
        AlbumArtBackgroundAnimationContainer: { a: 3, b: 1 },
        CoverAnimationContainer: { a: 4, b: 2 },
        default: { a: 6, b: 5 }
    };

    /**
     * Sık kullanılan CSS sınıflarını ve seçicileri tanımlar.
     * @static
     */
    static CSS_CLASSES = {
        PASSIVE: 'passive',
        ANIMATION_CONTAINER_SELECTOR: '[class*="AnimationContainer"]'
    };

    /**
     * AnimationService'in bir örneğini oluşturur.
     * @param {HTMLElement} widgetElement - Widget'ın ana element'i.
     * @param {object} config - Animasyon yapılandırmalarını içeren nesne.
     */
    constructor(widgetElement, config) {
        this.widgetElement = widgetElement;
        this.config = config;
        this.animationCache = {};
        this.zIndexConfig = JSON.parse(JSON.stringify(AnimationService.Z_INDEX_CONFIG));
    }

    /**
     * Bir elementi animasyonun belirli bir fazı için hazırlar.
     * Stilleri temizler ve animasyonun başlangıç karelerini uygular.
     * NOT: .passive sınıfını KALDIRMAZ - bu execute() sırasında yapılır.
     * @param {string} elementId - Hazırlanacak elementin ID'si.
     * @param {string} phase - Animasyon fazı ('intro', 'transitionIn', vb.).
     */
    prepareElement(elementId, phase) {
        const element = document.getElementById(elementId);
        if (!element) return;

        // Mevcut stilleri temizle
        element.removeAttribute('style');
        
        // Animasyon konfigürasyonunu al
        const animConfig = this.config[elementId]?.[phase];
        if (animConfig?.animation && animConfig.animation !== 'none') {
            // Başlangıç keyframe'lerini al ve uygula
            const initialStyles = this._getInitialKeyframeStyles(animConfig.animation);
            if (initialStyles) {
                // Başlangıç keyframe'indeki stilleri element'e uygula
                for (let i = 0; i < initialStyles.length; i++) {
                    const propName = initialStyles[i];
                    // !important ekleme, sadece değeri uygula
                    element.style.setProperty(propName, initialStyles.getPropertyValue(propName));
                }
            }
        }
        
        // Z-index'i ayarla
        this._applyZIndex(elementId);
    }

    /**
     * Belirtilen element için yapılandırılmış animasyonu yürütür.
     * CSS Contract'a göre çalışır: Önce .passive kaldırılır, sonra animasyon başlatılır.
     * @param {string} elementId - Animasyon uygulanacak elementin ID'si.
     * @param {string} phase - Animasyon fazı.
     * @returns {Promise<void>} Animasyon tamamlandığında çözülen bir Promise.
     */
    execute(elementId, phase) {
        return new Promise(resolve => {
            const element = document.getElementById(elementId);
            const animConfig = this.config[elementId]?.[phase];

            if (!element || !animConfig?.animation || animConfig.animation === 'none') {
                resolve();
                return;
            }
            
            const { animation, duration = 0, delay = 0 } = animConfig;
            const easing = (phase === 'transitionOut' || phase === 'outro') ? 'ease-in' : 'ease-out';
            const container = element.closest(AnimationService.CSS_CLASSES.ANIMATION_CONTAINER_SELECTOR);

            const handleAnimationEnd = (event) => {
                // Sadece bu element ve bu animasyon için tetiklenen olayı işle
                if (event.target === element && event.animationName === animation) {
                    element.removeEventListener('animationend', handleAnimationEnd);
                    resolve();
                }
            };

            // Animasyon bitişini dinle
            element.addEventListener('animationend', handleAnimationEnd);

            // RAF kullanarak pasif sınıfını kaldır ve animasyonu başlat
            requestAnimationFrame(() => {
                // 1. Önce .passive sınıfını kaldır (görünür hale gelir)
                element.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);
                if (container) {
                    container.classList.remove(AnimationService.CSS_CLASSES.PASSIVE);
                }

                // 2. Hemen ardından animasyonu başlat
                element.style.animation = `${animation} ${duration / 1000}s ${easing} ${delay / 1000}s forwards`;
            });
        });
    }

    /**
     * Animasyon sonrası bir elementi temizler.
     * - Giden (outgoing) elementler için: .passive ekler
     * - Gelen (incoming) elementler için: inline stilleri temizler
     * @param {string} elementId - Temizlenecek elementin ID'si.
     * @param {string} type - Temizleme tipi ('incoming' veya 'outgoing').
     */
    cleanupElement(elementId, type) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const container = element.closest(AnimationService.CSS_CLASSES.ANIMATION_CONTAINER_SELECTOR);
        
        // Bu satırlar her iki durumda da çalıştığı için burada kalabilir.
        element.style.animation = '';
        element.style.animationName = '';
        
        if (type === 'outgoing') {
            // 1. ADIM: Elementi gizlemek için .passive sınıfını ekle.
            element.classList.add(AnimationService.CSS_CLASSES.PASSIVE);
            if (container) {
                container.classList.add(AnimationService.CSS_CLASSES.PASSIVE);
            }
            // 2. ADIM: Animasyondan kalan tüm inline stilleri temizle.
            element.removeAttribute('style');

        } else { // 'incoming'
            // Gelen element için de tüm inline stilleri temizle.
            element.removeAttribute('style');
        }

            // 2. ADIM: BU SATIRI SİLİYORUZ VEYA YORUM SATIRI YAPIYORUZ
            // this._applyZIndex(elementId); 
    }
    
    /**
     * Belirtilen element ID'lerine sahip görsellerin yüklenmesini bekler.
     * @param {string[]} elementIds - IMG elementlerinin ID'lerini içeren dizi.
     * @returns {Promise<void>} Tüm görseller yüklendiğinde veya hata verdiğinde çözülen bir Promise.
     */
    waitForImages(elementIds) {
        const imageElements = elementIds
            .map(id => document.getElementById(id))
            .filter(el => el?.tagName === 'IMG' && el.src && !el.complete);

        if (imageElements.length === 0) {
            return Promise.resolve();
        }

        const promises = imageElements.map(img => 
            new Promise(resolve => {
                img.onload = resolve;
                img.onerror = resolve; // Hata durumunda da devam et
            })
        );

        return Promise.all(promises);
    }
    
    /**
     * Geçiş animasyonları için z-index değerlerini tersine çevirir.
     * @private
     */
    _flipZIndexes() {
        for (const key in this.zIndexConfig) {
            const config = this.zIndexConfig[key];
            [config.a, config.b] = [config.b, config.a];
        }
    }

    /**
     * Bir elemente konfigürasyona göre doğru z-index değerini uygular.
     * @param {string} elementId - Z-index uygulanacak elementin ID'si.
     * @private
     */
    /**
     * Bir elemente konfigürasyona göre doğru z-index değerini uygular.
     * @param {string} elementId - Z-index uygulanacak elementin ID'si.
     * @private
     */
    _applyZIndex(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        // Değişiklik: baseName artık doğrudan gelen containerId'den türetiliyor.
        // 'AnimationContainer' -> 'Element' dönüşümü kaldırıldı.
        // Örnek: "CoverAnimationContainer_a" ise baseName "CoverAnimationContainer" olacak.
        const baseName = elementId.substring(0, elementId.lastIndexOf('_'));
        const setLetter = elementId.slice(-1); // Bu, orijinal container ID'sinin son harfini alır.
        const zIndexConfig = this.zIndexConfig[baseName] || this.zIndexConfig.default;
        const zIndexValue = zIndexConfig?.[setLetter];
        
        if (typeof zIndexValue !== 'undefined') {
            element.style.zIndex = zIndexValue;
        }
    }

    /**
     * Bir CSS animasyonunun başlangıç (`0%` veya `from`) keyframe stillerini bulur ve önbelleğe alır.
     * @param {string} animationName - Stil sayfalarında aranacak animasyonun adı.
     * @returns {CSSStyleDeclaration | null} Bulunan stil nesnesi veya bulunamazsa null.
     * @private
     */
    _getInitialKeyframeStyles(animationName) {
        if (animationName in this.animationCache) {
            return this.animationCache[animationName];
        }

        for (const sheet of document.styleSheets) {
            try {
                const rules = sheet.cssRules || sheet.rules;
                for (const rule of rules) {
                    if (rule.type === CSSRule.KEYFRAMES_RULE && rule.name === animationName) {
                        for (const keyframe of rule.cssRules) {
                            if (keyframe.keyText === '0%' || keyframe.keyText === 'from') {
                                this.animationCache[animationName] = keyframe.style;
                                return keyframe.style;
                            }
                        }
                    }
                }
            } catch (e) {
                // Çapraz köken (CORS) stil sayfalarına erişim hatalarını yoksay.
            }
        }

        this.animationCache[animationName] = null;
        return null;
    }
}
