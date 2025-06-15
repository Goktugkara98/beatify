// DOSYA ADI: ContentUpdaterService.js
class ContentUpdaterService {
    constructor(widgetElement) {
        this.widgetElement = widgetElement;
        this.progressInterval = null;
        this.CSS_CLASSES = {
            ERROR_ACTIVE: 'error-active'
        };
    }

    /**
     * Belirtilen sete ait DOM elementlerinin içeriğini (şarkı adı, sanatçı vb.) günceller.
     * @param {string} set - Güncellenecek element seti ('a' veya 'b').
     * @param {object} data - Spotify'dan gelen veri nesnesi.
     */
    updateAll(set, data) {
        const item = data.item;
        if (!item) return;
        
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);
        const trackNameElem = query('.TrackNameElement');
        const artistNameElem = query('.ArtistNameElement');
        const coverElem = query('.CoverElement');
        const coverBgElem = query('.AlbumArtBackgroundElement');
        const totalTimeElem = query('.TotalTimeElement');

        if (trackNameElem) { 
            trackNameElem.innerText = item.name; 
            trackNameElem.title = item.name; 
        }
        if (artistNameElem) {
            artistNameElem.innerText = item.artists.map(a => a.name).join(', ');
        }
        if (coverElem) {
            coverElem.src = item.album.images[0]?.url || '';
        }
        if (coverBgElem) {
            coverBgElem.src = item.album.images[0]?.url || '';
        }
        if (totalTimeElem) {
            totalTimeElem.innerText = this._formatTime(item.duration_ms);
        }
    }

    /**
     * Bir setteki tüm dinamik verileri (şarkı adı, süreler, resimler) sıfırlar.
     * @param {string} set - Temizlenecek set ('a' veya 'b').
     */
    reset(set) {
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);
        
        const elemsToReset = [query('.TrackNameElement'), query('.ArtistNameElement'), query('.TotalTimeElement'), query('.CurrentTimeElement')];
        const elemsToClearSrc = [query('.CoverElement'), query('.AlbumArtBackgroundElement')];
        const progressBarElem = query('.ProgressBarElement');

        elemsToReset.forEach(el => { if (el) el.innerText = (el.classList.contains('CurrentTimeElement') || el.classList.contains('TotalTimeElement')) ? '0:00' : ''; });
        elemsToClearSrc.forEach(el => { if (el) el.src = ''; });
        if (progressBarElem) progressBarElem.style.width = '0%';
    }

    /**
     * Şarkının ilerleme çubuğunu ve geçerli süre metnini saniyede bir günceller.
     * @param {object} data - Güncel şarkı verisi.
     * @param {string} set - Güncellenecek set ('a' veya 'b').
     */
    startProgressUpdater(data, set) {
        this.stopProgressUpdater(); // Öncekini temizle
        
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
    
    /** Mevcut ilerleme çubuğu güncelleme döngüsünü durdurur. */
    stopProgressUpdater() {
        clearInterval(this.progressInterval);
        this.progressInterval = null;
    }

    /** Widget'ta bir hata mesajı gösterir. */
    displayError(message) {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement) {
            errorElement.innerText = message;
            this.widgetElement.classList.add(this.CSS_CLASSES.ERROR_ACTIVE);
        }
        this.stopProgressUpdater();
    }

    /** Gösterilen hata mesajını temizler. */
    clearError() {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement && this.widgetElement.classList.contains(this.CSS_CLASSES.ERROR_ACTIVE)) {
            errorElement.innerText = '';
            this.widgetElement.classList.remove(this.CSS_CLASSES.ERROR_ACTIVE);
        }
    }
    
    _formatTime(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}