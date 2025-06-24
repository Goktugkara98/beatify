/**
 * =================================================================================
 * ContentUpdaterService - İçindekiler
 * =================================================================================
 *
 * Bu servis, DOM elementlerinin içeriğini (metin, resim, ilerleme çubuğu vb.)
 * güncellemeyi yönetir.
 *
 * ---
 *
 * BÖLÜM 1: KURULUM (SETUP)
 * 1.1. constructor: Servisi başlatır ve temel ayarları yapar.
 *
 * BÖLÜM 2: GENEL İÇERİK YÖNETİMİ (PUBLIC CONTENT MANAGEMENT)
 * 2.1. updateAll: Belirtilen veri setine ait tüm UI elementlerini günceller.
 * 2.2. reset: Belirtilen sete ait tüm içerik elementlerini sıfırlar.
 *
 * BÖLÜM 3: İLERLEME ÇUBUĞU KONTROLÜ (PROGRESS UPDATER CONTROL)
 * 3.1. startProgressUpdater: Şarkı ilerlemesini gösteren zamanlayıcıyı başlatır.
 * 3.2. stopProgressUpdater: Aktif ilerleme zamanlayıcısını durdurur.
 *
 * BÖLÜM 4: HATA YÖNETİMİ (ERROR HANDLING)
 * 4.1. displayError: Widget'ta bir hata mesajı görüntüler.
 * 4.2. clearError: Görüntülenen hata mesajını temizler.
 *
 * BÖLÜM 5: ÖZEL YARDIMCI FONKSİYONLAR (PRIVATE HELPERS)
 * 5.1. _handleTextOverflow: Metin taşmalarını kontrol eder ve kayan yazı animasyonunu uygular.
 * 5.2. _formatTime: Milisaniyeyi "dakika:saniye" formatına çevirir.
 *
 * =================================================================================
 */
class ContentUpdaterService {
    // =================================================================================
    // BÖLÜM 1: KURULUM (SETUP)
    // =================================================================================

    /**
     * 1.1. ContentUpdaterService'in bir örneğini oluşturur.
     * @param {HTMLElement} widgetElement - Widget'ın ana elementi.
     */
    constructor(widgetElement) {
        this.widgetElement = widgetElement;
        this.progressInterval = null;
        this.CSS_CLASSES = { ERROR_ACTIVE: 'error-active' };
    }

    // =================================================================================
    // BÖLÜM 2: GENEL İÇERİK YÖNETİMİ (PUBLIC CONTENT MANAGEMENT)
    // =================================================================================

    /**
     * 2.1. Belirtilen veri setine ait tüm UI elementlerini (şarkı adı, sanatçı, kapak resmi) günceller.
     * @param {string} set - Güncellenecek element setinin adı ('a' veya 'b').
     * @param {object} data - Spotify'dan gelen ve şarkı bilgilerini içeren veri nesnesi.
     */
    updateAll(set, data) {
        const item = data.item;
        if (!item) return;
        
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);
        
        const trackNameElem = query('.TrackNameElement');
        if (trackNameElem) {
            trackNameElem.innerText = item.name;
            trackNameElem.title = item.name;
            // YENİ: Metin taşmasını kontrol et
            this._handleTextOverflow(trackNameElem);
        }

        const artistNameElem = query('.ArtistNameElement');
        if (artistNameElem) {
            artistNameElem.innerText = item.artists.map(a => a.name).join(', ');
            // YENİ: Metin taşmasını kontrol et
            this._handleTextOverflow(artistNameElem);
        }

        const coverElem = query('.CoverElement');
        if (coverElem) {
            coverElem.src = item.album.images[0]?.url || '';
        }

        const coverBgElem = query('.AlbumArtBackgroundElement');
        if (coverBgElem) {
            coverBgElem.src = item.album.images[0]?.url || '';
        }

        const totalTimeElem = query('.TotalTimeElement');
        if (totalTimeElem) {
            totalTimeElem.innerText = this._formatTime(item.duration_ms);
        }
    }

    /**
     * 2.2. Belirtilen sete ait tüm içerik elementlerini varsayılan durumuna sıfırlar.
     * @param {string} set - Sıfırlanacak element setinin adı.
     */
    reset(set) {
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);
        
        const trackNameElem = query('.TrackNameElement');
        const artistNameElem = query('.ArtistNameElement');

        const textElements = [trackNameElem, artistNameElem, query('.TotalTimeElement'), query('.CurrentTimeElement')];
        textElements.forEach(el => {
            if (el) el.innerText = (el.classList.contains('CurrentTimeElement') || el.classList.contains('TotalTimeElement')) ? '0:00' : '';
        });

        // YENİ: Marquee animasyonunu temizle
        if (trackNameElem) this._handleTextOverflow(trackNameElem);
        if (artistNameElem) this._handleTextOverflow(artistNameElem);
        
        const imageElements = [query('.CoverElement'), query('.AlbumArtBackgroundElement')];
        imageElements.forEach(el => {
            if (el) el.src = '';
        });

        const progressBarElem = query('.ProgressBarElement');
        if (progressBarElem) {
            progressBarElem.style.width = '0%';
        }
    }

    // =================================================================================
    // BÖLÜM 3: İLERLEME ÇUBUĞU KONTROLÜ (PROGRESS UPDATER CONTROL)
    // =================================================================================

    /**
     * 3.1. Şarkı ilerlemesini gösteren zamanlayıcıyı ve ilerleme çubuğunu başlatır.
     * @param {object} data - Mevcut çalma durumunu içeren veri nesnesi.
     * @param {string} set - Güncellenecek aktif set.
     */
    startProgressUpdater(data, set) {
        this.stopProgressUpdater(); 
        
        let progressMs = data.progress_ms;
        const durationMs = data.item.duration_ms;
        const currentTimeElem = this.widgetElement.querySelector(`.CurrentTimeElement[data-set="${set}"]`);
        const progressBarElem = this.widgetElement.querySelector(`.ProgressBarElement[data-set="${set}"]`);

        if (!currentTimeElem || !progressBarElem) return;

        const update = () => {
            currentTimeElem.innerText = this._formatTime(progressMs);
            const percentage = durationMs > 0 ? (progressMs / durationMs) * 100 : 0;
            progressBarElem.style.width = `${Math.min(percentage, 100)}%`;
            if (progressMs < durationMs) {
                progressMs += 1000;
            }
        };

        update();
        this.progressInterval = setInterval(update, 1000);
    }
    
    /**
     * 3.2. Aktif ilerleme zamanlayıcısını durdurur.
     */
    stopProgressUpdater() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    // =================================================================================
    // BÖLÜM 4: HATA YÖNETİMİ (ERROR HANDLING)
    // =================================================================================

    /**
     * 4.1. Widget'ta bir hata mesajı görüntüler.
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
     * 4.2. Görüntülenen hata mesajını temizler.
     */
    clearError() {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement && this.widgetElement.classList.contains(this.CSS_CLASSES.ERROR_ACTIVE)) {
            errorElement.innerText = '';
            this.widgetElement.classList.remove(this.CSS_CLASSES.ERROR_ACTIVE);
        }
    }
    
    // =================================================================================
    // BÖLÜM 5: ÖZEL YARDIMCI FONKSİYONLAR (PRIVATE HELPERS)
    // =================================================================================
    
    /**
     * 5.1. Bir elementin metin içeriğinin kapsayıcısını aşıp aşmadığını kontrol eder.
     * Eğer aşıyorsa, kayan yazı (marquee) animasyonunu tetiklemek için bir CSS sınıfı uygular.
     * @param {HTMLElement} element - Kontrol edilecek metin elementi.
     * @private
     */
    _handleTextOverflow(element) {
        if (!element) return;

        // Tarayıcının yeni metni render etmesine ve boyutları hesaplamasına izin vermek için kısa bir gecikme kullanın.
        requestAnimationFrame(() => {
            const isOverflowing = element.scrollWidth > element.clientWidth;

            if (isOverflowing) {
                // Kaydırılacak mesafeyi hesapla.
                const scrollDistance = element.scrollWidth - element.clientWidth;
                // Tutarlı bir hız sağlamak için taşma miktarına göre dinamik bir süre hesapla.
                // Saniyede 40 piksel hız varsayalım.
                const scrollSpeed = 40; // pixels per second
                // Animasyon süresi = (mesafe / hız) * (duraklamalar ve geri dönüş için çarpan)
                const animationDuration = (scrollDistance / scrollSpeed) * 2.5; 

                // Animasyon için CSS özel değişkenlerini ayarla.
                element.style.setProperty('--marquee-scroll-distance', `-${scrollDistance}px`);
                // Çok kısa animasyonları önlemek için minimum süre 10 saniye olsun.
                element.style.setProperty('--marquee-animation-duration', `${Math.max(10, animationDuration)}s`);
                
                element.classList.add('marquee-scroll');
            } else {
                // Taşma yoksa, sınıfı ve özel değişkenleri kaldır.
                element.classList.remove('marquee-scroll');
                element.style.removeProperty('--marquee-scroll-distance');
                element.style.removeProperty('--marquee-animation-duration');
            }
        });
    }

    /**
     * 5.2. Milisaniyeyi "dakika:saniye" formatına çevirir.
     * @param {number} ms - Dönüştürülecek milisaniye.
     * @returns {string} Formatlanmış zaman metni.
     * @private
     */
    _formatTime(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}
