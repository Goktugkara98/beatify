/**
 * @class ContentUpdaterService
 * @description DOM elementlerinin içeriğini (metin, resim, ilerleme çubuğu vb.) günceller.
 */
class ContentUpdaterService {
    constructor(widgetElement) {
        this.widgetElement = widgetElement;
        this.progressInterval = null;
        this.CSS_CLASSES = { ERROR_ACTIVE: 'error-active' };
    }

    /**
     * Belirtilen veri setine ait tüm UI elementlerini (şarkı adı, sanatçı, kapak resmi) günceller.
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
        }

        const artistNameElem = query('.ArtistNameElement');
        if (artistNameElem) {
            artistNameElem.innerText = item.artists.map(a => a.name).join(', ');
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
     * Belirtilen sete ait tüm içerik elementlerini varsayılan durumuna sıfırlar.
     * @param {string} set - Sıfırlanacak element setinin adı.
     */
    reset(set) {
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);
        
        const textElements = [query('.TrackNameElement'), query('.ArtistNameElement'), query('.TotalTimeElement'), query('.CurrentTimeElement')];
        textElements.forEach(el => {
            if (el) el.innerText = (el.classList.contains('CurrentTimeElement') || el.classList.contains('TotalTimeElement')) ? '0:00' : '';
        });
        
        const imageElements = [query('.CoverElement'), query('.AlbumArtBackgroundElement')];
        imageElements.forEach(el => {
            if (el) el.src = '';
        });

        const progressBarElem = query('.ProgressBarElement');
        if (progressBarElem) {
            progressBarElem.style.width = '0%';
        }
    }

    /**
     * Şarkı ilerlemesini gösteren zamanlayıcıyı ve ilerleme çubuğunu başlatır.
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
     * Aktif ilerleme zamanlayıcısını durdurur.
     */
    stopProgressUpdater() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    /**
     * Widget'ta bir hata mesajı görüntüler.
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
     * Görüntülenen hata mesajını temizler.
     */
    clearError() {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement && this.widgetElement.classList.contains(this.CSS_CLASSES.ERROR_ACTIVE)) {
            errorElement.innerText = '';
            this.widgetElement.classList.remove(this.CSS_CLASSES.ERROR_ACTIVE);
        }
    }
    
    /**
     * Milisaniyeyi "dakika:saniye" formatına çevirir.
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
