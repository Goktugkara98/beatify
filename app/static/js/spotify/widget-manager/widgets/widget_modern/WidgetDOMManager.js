// DOSYA ADI: WidgetDOMManager.js
// =================================================================================================
// ||                                     İÇİNDEKİLER                                             ||
// =================================================================================================
//
// 1.0. KURULUM VE OLAY DİNLEYİCİLERİ (SETUP & EVENT LISTENERS)
//    1.1. constructor: Sınıfı başlatır, referansları ve sabitleri ayarlar.
//    1.2. listenToEvents: StateService'den gelen özel olayları dinlemek için olay dinleyicileri ekler.
//
// 2.0. ANA OLAY YÖNETİCİLERİ (MAIN EVENT HANDLERS)
//    2.1. runIntro: 'widget:intro' olayı tetiklendiğinde çalışır, widget'ı görünür kılar.
//    2.2. runTransition: 'widget:transition' olayı tetiklendiğinde çalışır, şarkı geçiş animasyonunu yönetir.
//    2.3. runOutro: 'widget:outro' olayı tetiklendiğinde çalışır, widget'ı gizleme veya durdurma animasyonunu yönetir.
//
// 3.0. İÇERİK VE İLERLEME GÜNCELLEYİCİLER (CONTENT & PROGRESS UPDATERS)
//    3.1. _updateDOMContent: Elementlerin içeriğini (şarkı adı, sanatçı, kapak) günceller.
//    3.2. _resetSetData: Bir element setinin içeriğini temizler.
//    3.3. startProgressUpdater: Şarkı ilerleme çubuğunu ve zamanlayıcıyı başlatır/günceller.
//    3.4. stopProgressUpdater: İlerleme çubuğu güncelleyicisini durdurur.
//    3.5. _formatTime: Milisaniyeyi "dakika:saniye" formatına çevirir.
//
// 4.0. ANİMASYON YÖNETİMİ (ANIMATION MANAGEMENT)
//    4.1. _prepareElements: Animasyon için elementleri hazırlar (CSS sınıflarını ve z-index'i ayarlar).
//    4.2. _applyAnimation: Bir elemente yapılandırmadan gelen animasyonları uygular.
//    4.3. _waitForImages: Animasyonu başlatmadan önce resimlerin yüklenmesini bekler.
//    4.4. _flipZIndex: Geçiş animasyonu için 'a' ve 'b' setlerinin z-index değerlerini değiştirir.
//    4.5. _applyZIndex: Belirli bir elemente doğru z-index değerini atar.
//
// 5.0. HATA GÖSTERİMİ (ERROR DISPLAY)
//    5.1. displayError: Ekranda bir hata mesajı gösterir.
//    5.2. clearError: Hata mesajını temizler.
//
// =================================================================================================

class WidgetDOMManager {
    // --- Statik Yapılandırmalar ---
    static Z_INDEX_CONFIG = { AlbumArtBackgroundElement: { a: 3, b: 1 }, 
                                           CoverElement: { a: 4, b: 2 }, 
                                                default: { a: 6, b: 5 } 
                            };
    static CSS_CLASSES = { PASSIVE: 'passive', 
                           WIDGET_INACTIVE: 'widget-inactive', 
                           ANIMATION_CONTAINER_SELECTOR: '[class*="AnimationContainer"]', 
                           ERROR_ACTIVE: 'error-active' };

    // =========================================================================
    // ||           1.0. KURULUM VE OLAY DİNLEYİCİLERİ (SETUP)                ||
    // =========================================================================

    /**
     * 1.1. constructor
     * Gerekli referansları (element, config, stateService) alır ve olay dinleyicilerini başlatır.
     * @param {HTMLElement} widgetElement - Ana widget HTML elementi.
     * @param {object} config - Animasyon ve element yapılandırmasını içeren nesne.
     * @param {SpotifyStateService} stateService - Durum yönetimi servisi.
     */
    constructor(widgetElement, config, stateService) {
        if (!widgetElement || !config || !stateService) throw new Error("WidgetDOMManager için widgetElement, config ve stateService gereklidir.");
        
        this.widgetElement = widgetElement;
        this.config = config;
        this.stateService = stateService;
        this.progressInterval = null;
        

        // Yapılandırmaların kopyalarını oluşturarak orijinal statik nesnelerin değişmesini engelle
        this.zIndexConfig = JSON.parse(JSON.stringify(WidgetDOMManager.Z_INDEX_CONFIG));
        this.CSS_CLASSES = WidgetDOMManager.CSS_CLASSES;
        this.animationCache = {}; // Animasyon önbelleği için boş bir nesne oluştur.
        this.listenToEvents();
    }

    /**
     * YENİ FONKSİYON: getInitialKeyframeStyles
     * Verilen animasyon adının keyframes tanımını bulur ve ilk karesinin ('0%' veya 'from')
     * CSS stillerini bir nesne olarak döndürür. Sonuçlar performansı artırmak için önbelleğe alınır.
     * param {string} animationName - Aranacak keyframes animasyonunun adı.
     * returns {CSSStyleDeclaration | null} - Stil nesnesi veya bulunamazsa null.
     */
    getInitialKeyframeStyles(animationName) {
        // 1.2: Önbelleği kontrol et, animasyon daha önce bulunduysa direkt oradan döndür.
        if (this.animationCache[animationName]) {
            return this.animationCache[animationName];
        }

        // 1.3: Sayfadaki tüm stil dosyalarını döngüye al.
        for (const sheet of document.styleSheets) {
            try {
                // Not: Farklı bir domain'den yüklenen (CORS) stil dosyaları hataya neden olabilir.
                const rules = sheet.cssRules || sheet.rules;
                for (const rule of rules) {
                    // 1.4: Kuralın bir @keyframes kuralı olup olmadığını ve adının eşleşip eşleşmediğini kontrol et.
                    if (rule.type === CSSRule.KEYFRAMES_RULE && rule.name === animationName) {
                        // 1.5: @keyframes içindeki ilk kuralı bul ('0%' veya 'from').
                        for (const keyframe of rule.cssRules) {
                            if (keyframe.keyText === '0%' || keyframe.keyText === 'from') {
                                // 1.6: Stili bulduk! Önbelleğe kaydet ve döndür.
                                this.animationCache[animationName] = keyframe.style;
                                return keyframe.style;
                            }
                        }
                    }
                }
            } catch (e) {
                // CORS hatası veya başka bir erişim sorunu olursa konsola yazdır ve devam et.
                // console.warn(`'${sheet.href}' stil dosyası okunamadı.`, e);
            }
        }

        // 1.7: Animasyon bulunamadıysa, sonucu null olarak önbelleğe al ve null döndür.
        this.animationCache[animationName] = null;
        return null;
    }
    
    /**
     * 1.2. listenToEvents
     * StateService tarafından gönderilen olayları dinler ve ilgili yönetici metotları çağırır.
     */
    listenToEvents() {
        this.widgetElement.addEventListener('widget:intro', (e) => this.runIntro(e.detail));
        this.widgetElement.addEventListener('widget:transition', (e) => this.runTransition(e.detail));
        this.widgetElement.addEventListener('widget:outro', (e) => this.runOutro(e.detail));
        this.widgetElement.addEventListener('widget:sync', (e) => this.startProgressUpdater(e.detail.data, e.detail.set));
        this.widgetElement.addEventListener('widget:error', (e) => this.displayError(e.detail.message));
        this.widgetElement.addEventListener('widget:clear-error', () => this.clearError());
    }

    // =========================================================================
    // ||              2.0. ANA OLAY YÖNETİCİLERİ (EVENT HANDLERS)            ||
    // =========================================================================

    /**
     * 2.1. runIntro
     * Widget ilk kez başlatıldığında çalışır. Elementleri doldurur, hazırlar ve giriş animasyonunu oynatır.
     * @param {object} detail - Olay detayı. { set: string, data: object } içerir.
     */
    async runIntro({ set, data }) {
        const introElementIds = this.config.elements.filter(id => id.endsWith(`_${set}`));
        
        this._updateDOMContent(set, data);
        this._prepareElements(introElementIds);
        await this._waitForImages(introElementIds);
        
        this.widgetElement.classList.remove(this.CSS_CLASSES.WIDGET_INACTIVE);
        introElementIds.forEach(id => this._applyAnimation(id, 'intro'));
        this.startProgressUpdater(data, set);
    }

    /**
     * 2.2. runTransition
     * Bir şarkıdan diğerine geçişte çalışır. Mevcut şarkıyı dışarı, yeni şarkıyı içeri anime eder.
     * @param {object} detail - Olay detayı. { activeSet, passiveSet, data } içerir.
     */
    async runTransition({ activeSet, passiveSet, data }) {
        this._flipZIndex();
        this._updateDOMContent(passiveSet, data);
    
        const outgoingElementIds = this.config.elements.filter(id => id.endsWith(`_${activeSet}`));
        const incomingElementIds = this.config.elements.filter(id => id.endsWith(`_${passiveSet}`));
    
        this.stopProgressUpdater();
    
        // 1. Önce her iki seti de sayfa düzenine dahil et (passive sınıflarını kaldır).
        this._prepareElements(outgoingElementIds);
        this._prepareElements(incomingElementIds);
    
        // 2. "await" DEMEDEN HEMEN ÖNCE, gelen elementleri animasyonun başlangıç durumuna getir.
        // Bu, onları tarayıcı ekrana çizemeden görünmez yapar ve "flash" etkisini önler.
        incomingElementIds.forEach(id => {
            const element = document.getElementById(id);
            if (!element) return;
            
            const animConfig = this.config[id]?.['transitionIn'];
            if (!animConfig || !animConfig.animation) return;
    
            const initialStyles = this.getInitialKeyframeStyles(animConfig.animation);
            if (initialStyles) {
                for (let i = 0; i < initialStyles.length; i++) {
                    const propertyName = initialStyles[i];
                    element.style[propertyName] = initialStyles.getPropertyValue(propertyName);
                }
            }
        });
    
        // 3. Artık elementler görünmez olduğuna göre, resimlerin yüklenmesini güvenle bekleyebiliriz.
        await this._waitForImages(incomingElementIds);
    
        let maxTransitionTime = 0;
    
        // 4. Giden elementlerin animasyonunu başlat.
        const onTransitionOutEnd = (element) => {
            element.classList.add(this.CSS_CLASSES.PASSIVE);
            const container = element.closest(this.CSS_CLASSES.ANIMATION_CONTAINER_SELECTOR);
            if (container) {
                container.classList.add(this.CSS_CLASSES.PASSIVE);
            }
        };
        outgoingElementIds.forEach(id => {
            const time = this._applyAnimation(id, 'transitionOut', onTransitionOutEnd);
            if (time > maxTransitionTime) maxTransitionTime = time;
        });
    
        // 5. Gelen elementlerin animasyonunu başlat.
        const onTransitionInEnd = (element) => {
            element.removeAttribute('style');
            this._applyZIndex(element.id);
        };
        incomingElementIds.forEach(id => {
            const totalTime = this._applyAnimation(id, 'transitionIn', onTransitionInEnd);
            if (totalTime > maxTransitionTime) maxTransitionTime = totalTime;
        });
    
        // 6. Animasyon süresi sonunda durumu sonlandır ve eski seti temizle.
        setTimeout(() => {
            this.stateService.finalizeTransition(passiveSet);
            this._resetSetData(activeSet);
        }, maxTransitionTime);
    }

    /**
     * 2.3. runOutro
     * Müzik durduğunda çalışır. İsteğe bağlı olarak bir çıkış animasyonu yönetir.
     * @param {object} detail - Olay detayı. { activeSet } içerir.
     */
    runOutro({ activeSet }) {
        this.stopProgressUpdater();
        this.widgetElement.classList.add(this.CSS_CLASSES.WIDGET_INACTIVE);
        console.log(`Outro animasyonu ${activeSet} seti için çalıştırılıyor...`);
        // Gerekirse outro animasyon mantığı ve _applyAnimation çağrıları buraya eklenebilir.
    }

    // =========================================================================
    // ||      3.0. İÇERİK VE İLERLEME GÜNCELLEYİCİLER (CONTENT & PROGRESS)     ||
    // =========================================================================

    /**
     * 3.1. _updateDOMContent
     * Belirtilen sete ait DOM elementlerinin içeriğini (şarkı adı, sanatçı vb.) günceller.
     * @param {string} set - Güncellenecek element seti ('a' veya 'b').
     * @param {object} data - Spotify'dan gelen veri nesnesi.
     */
    _updateDOMContent(set, data) {
        const item = data.item;
        if (!item) return;
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);

        const trackNameElem = query('.TrackNameElement'), artistNameElem = query('.ArtistNameElement'),
              coverElem = query('.CoverElement'), coverBgElem = query('.AlbumArtBackgroundElement'),
              totalTimeElem = query('.TotalTimeElement');

        if (trackNameElem) trackNameElem.innerText = item.name;
        if (artistNameElem) artistNameElem.innerText = item.artists.map(a => a.name).join(', ');
        if (coverElem) coverElem.src = item.album.images[0]?.url || '';
        if (coverBgElem) coverBgElem.src = item.album.images[0]?.url || '';
        if (totalTimeElem) totalTimeElem.innerText = this._formatTime(item.duration_ms);
    }

    /**
     * 3.2. _resetSetData
     * Bir setteki tüm dinamik verileri (şarkı adı, süreler, resimler) sıfırlar.
     * @param {string} set - Temizlenecek set ('a' veya 'b').
     */
    _resetSetData(set) {
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);
        
        const elemsToReset = [query('.TrackNameElement'), query('.ArtistNameElement'), query('.TotalTimeElement'), query('.CurrentTimeElement')];
        const elemsToClearSrc = [query('.CoverElement'), query('.AlbumArtBackgroundElement')];
        const progressBarElem = query('.ProgressBarElement');

        elemsToReset.forEach(el => { if (el) el.innerText = (el.classList.contains('TimeElement')) ? '0:00' : ''; });
        elemsToClearSrc.forEach(el => { if (el) el.src = ''; });
        if (progressBarElem) progressBarElem.style.width = '0%';
    }

    /**
     * 3.3. startProgressUpdater
     * Şarkının ilerleme çubuğunu ve geçerli süre metnini saniyede bir günceller.
     * @param {object} data - Güncel şarkı verisi.
     * @param {string} set - Güncellenecek set ('a' veya 'b').
     */
    startProgressUpdater(data, set) {
        if (this.progressInterval) clearInterval(this.progressInterval);
        
        let progressMs = data.progress_ms;
        const durationMs = data.item.duration_ms;
        const currentTimeElem = this.widgetElement.querySelector(`.CurrentTimeElement[data-set="${set}"]`);
        const progressBarElem = this.widgetElement.querySelector(`.ProgressBarElement[data-set="${set}"]`);

        const update = () => {
            if (currentTimeElem) currentTimeElem.innerText = this._formatTime(progressMs);
            if (progressBarElem) {
                const percentage = durationMs > 0 ? (progressMs / durationMs) * 100 : 0;
                progressBarElem.style.width = `${Math.min(percentage, 100)}%`;
            }
            progressMs += 1000;
        };
        update(); // Anında bir güncelleme yap
        this.progressInterval = setInterval(update, 1000);
    }
    
    /**
     * 3.4. stopProgressUpdater
     * Mevcut ilerleme çubuğu güncelleme döngüsünü durdurur.
     */
    stopProgressUpdater() {
        clearInterval(this.progressInterval);
        this.progressInterval = null;
    }
    
    /**
     * 3.5. _formatTime
     * Milisaniye cinsinden süreyi "dakika:saniye" formatına dönüştüren yardımcı metot.
     * @param {number} ms - Milisaniye.
     * @returns {string} Formatlanmış zaman metni.
     */
    _formatTime(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    // =========================================================================
    // ||                  4.0. ANİMASYON YÖNETİMİ (ANIMATION)                ||
    // =========================================================================

    /**
     * 4.1. _prepareElements
     * Verilen element ID'lerini animasyona hazırlar.
     * @param {string[]} elementIds - Hazırlanacak elementlerin ID listesi.
     * @param {object} options - Ek seçenekler. { isIncoming: boolean }
     */
    _prepareElements(elementIds) {
        elementIds.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            el.classList.remove(this.CSS_CLASSES.PASSIVE);
            el.closest(this.CSS_CLASSES.ANIMATION_CONTAINER_SELECTOR)?.classList.remove(this.CSS_CLASSES.PASSIVE);
            this._applyZIndex(id);
        });
    }

    /**
     * 4.2. _applyAnimation
     * Bir elemente yapılandırma dosyasında belirtilen animasyonu uygular.
     * @param {string} elementId - Animasyon uygulanacak elementin ID'si.
     * @param {string} phase - Animasyon fazı ('intro', 'transitionIn', 'transitionOut').
     * @param {Function|null} onEndCallback - Animasyon bittiğinde çalışacak fonksiyon.
     * @returns {number} Animasyonun toplam süresi (gecikme dahil).
     */
    _applyAnimation(elementId, phase, onEndCallback = null) {
        const element = document.getElementById(elementId);
        if (!element || !this.config[elementId] || !this.config[elementId][phase]) return 0;
        const { animation, duration = 0, delay = 0 } = this.config[elementId][phase];
        if (!animation || animation === 'none') {
            if (onEndCallback) setTimeout(() => onEndCallback(element), duration + delay);
            return duration + delay;
        }
        
        const easing = (phase === 'transitionOut' || phase === 'outro') ? 'ease-in' : 'ease-out';
        element.style.animation = `${animation} ${duration / 1000}s ${easing} ${delay / 1000}s both`;

        element.addEventListener('animationend', function handleAnimationEnd(event) {
            if (event.animationName !== animation) return; // Sadece ilgili animasyon bittiğinde çalış
            element.style.animation = ''; // Temizlik
            if (onEndCallback) onEndCallback(element);
        }, { once: true });

        return duration + delay;
    }
    
    /**
     * 4.3. _waitForImages
     * Belirtilen elementler arasındaki IMG etiketlerinin yüklenmesini bekler.
     * @param {string[]} elementIds - Kontrol edilecek elementlerin ID listesi.
     * @returns {Promise} Tüm resimler yüklendiğinde çözülen bir Promise.
     */
    _waitForImages(elementIds) {
        const imageElements = elementIds
            .map(id => document.getElementById(id))
            .filter(el => el?.tagName === 'IMG' && el.src);

        if (imageElements.length === 0) return Promise.resolve();
        
        const promises = imageElements.map(img => new Promise(resolve => {
            if (img.complete) return resolve();
            img.onload = () => resolve();
            img.onerror = () => resolve(); // Hata durumunda da devam et
        }));
        
        return Promise.all(promises);
    }

    /**
     * 4.4. _flipZIndex
     * Geçiş animasyonları için 'a' ve 'b' setlerinin z-index yapılandırmasını tersine çevirir.
     */
    _flipZIndex() {
        for (const key in this.zIndexConfig) {
            [this.zIndexConfig[key].a, this.zIndexConfig[key].b] = [this.zIndexConfig[key].b, this.zIndexConfig[key].a];
        }
    }

    /**
     * 4.5. _applyZIndex
     * Bir elementin z-index'ini mevcut yapılandırmaya göre ayarlar.
     * @param {string} elementId - Z-index'i ayarlanacak elementin ID'si.
     */
    _applyZIndex(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        const baseName = elementId.substring(0, elementId.lastIndexOf('_'));
        const setLetter = elementId.slice(-1);
        
        const zIndexValue = (this.zIndexConfig[baseName] || this.zIndexConfig.default)[setLetter];
        if (typeof zIndexValue !== 'undefined') {
            element.style.zIndex = zIndexValue;
        }
    }

    // =========================================================================
    // ||                     5.0. HATA GÖSTERİMİ (ERROR)                     ||
    // =========================================================================

    /**
     * 5.1. displayError
     * Widget'ta bir hata mesajı gösterir ve ilerleme çubuğunu durdurur.
     * @param {string} message - Gösterilecek hata mesajı.
     */
    displayError(message) {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement) {
            errorElement.innerText = message;
            this.widgetElement.classList.add(this.CSS_CLASSES.ERROR_ACTIVE);
        }
        this.stopProgressUpdater();
    }

    /**
     * 5.2. clearError
     * Gösterilen hata mesajını temizler.
     */
    clearError() {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement && this.widgetElement.classList.contains(this.CSS_CLASSES.ERROR_ACTIVE)) {
            errorElement.innerText = '';
            this.widgetElement.classList.remove(this.CSS_CLASSES.ERROR_ACTIVE);
        }
    }
}