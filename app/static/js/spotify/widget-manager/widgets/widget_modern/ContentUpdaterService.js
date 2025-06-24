/**
 * @file ContentUpdaterService.js
 * @description Gelen veriye göre arayüzdeki içerikleri (metin, resim vb.) günceller.
 */
class ContentUpdaterService {
    constructor(widgetElement) {
        this.widgetElement = widgetElement;
        this.progressInterval = null;
    }

    /**
     * Belirtilen set ('a' veya 'b') için tüm bilgileri günceller.
     * @param {string} set - Güncellenecek UI seti.
     * @param {object} data - Spotify'dan gelen veri.
     */
    updateAllForSet(set, data) {
        const item = data.item;
        if (!item) return;

        this._updateText(`.TrackNameElement_${set}`, item.name);
        this._updateText(`.ArtistNameElement_${set}`, item.artists.map(a => a.name).join(', '));
        this._updateText(`.TotalTimeElement_${set}`, this._formatTime(item.duration_ms));
        this._updateImage(`.CoverElement_${set}`, item.album.images[0]?.url);
        this._updateImage(`.AlbumArtBackgroundElement_${set}`, item.album.images[0]?.url);
    }
    
    /**
     * Zaman ve ilerleme çubuğunu günceller.
     * @param {object} data - Spotify verisi.
     * @param {string} set - Aktif UI seti.
     */
    startProgressUpdater(data, set) {
        this.stopProgressUpdater(); // Önceki interval'i durdur
        if (!data || !data.item || !data.is_playing) return;

        let progressMs = data.progress_ms;
        const durationMs = data.item.duration_ms;
        const currentTimeElem = this.widgetElement.querySelector(`.CurrentTimeElement_${set}`);
        const progressBarElem = this.widgetElement.querySelector(`.ProgressBarElement_${set}`);

        const update = () => {
            if (currentTimeElem) currentTimeElem.innerText = this._formatTime(progressMs);
            if (progressBarElem) {
                const percentage = durationMs > 0 ? (progressMs / durationMs) * 100 : 0;
                progressBarElem.style.width = `${Math.min(percentage, 100)}%`;
            }
            if (progressMs < durationMs) progressMs += 1000;
        };
        
        update(); // Hemen bir kez çalıştır
        this.progressInterval = setInterval(update, 1000);
    }

    stopProgressUpdater() {
        if (this.progressInterval) clearInterval(this.progressInterval);
    }

    _updateText(selector, text) {
        const elem = this.widgetElement.querySelector(selector);
        if (elem) {
            elem.innerText = text;
            elem.title = text; // Tooltip için
        }
    }

    _updateImage(selector, src) {
        const elem = this.widgetElement.querySelector(selector);
        if (elem && elem.src !== src) elem.src = src || '';
    }

    _formatTime(ms) {
        if (typeof ms !== 'number') return '0:00';
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}
