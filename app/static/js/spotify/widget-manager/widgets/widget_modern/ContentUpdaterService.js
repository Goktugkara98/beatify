// ===================================================================================
// DOSYA ADI: ContentUpdaterService.js
// AÇIKLAMA: DOM elementlerinin içeriğini (metin, resim vb.) günceller.
// YENİ YAPI NOTU: Bu sınıf artık log gruplarını yönetmez. Sadece kendi
//                 spesifik görevleriyle ilgili (içerik güncelleme, sıfırlama vb.)
//                 'info', 'warn' gibi detay logları basar. Grup yönetimi,
//                 bu servisi çağıran 'WidgetDOMManager' tarafından yapılır.
// ===================================================================================
class ContentUpdaterService {
    constructor(widgetElement, logger) {
        this.logger = logger;
        this.CALLER_FILE = 'ContentUpdaterService.js';
        this.widgetElement = widgetElement;
        this.progressInterval = null;
        this.CSS_CLASSES = { ERROR_ACTIVE: 'error-active' };
        this.logger.info(this.CALLER_FILE, 'ContentUpdaterService oluşturuldu.');
    }

    updateAll(set, data) {
        this.logger.info(this.CALLER_FILE, `Tüm içerik güncelleniyor (Set: ${set}).`);
        this.logger.data(this.CALLER_FILE, "Güncellenecek Şarkı Verisi", data.item);

        const item = data.item;
        if (!item) {
            this.logger.warn(this.CALLER_FILE, 'updateAll çağrıldı ancak güncellenecek "item" verisi boş.');
            return;
        }
        
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);
        
        const trackNameElem = query('.TrackNameElement');
        if (trackNameElem) { trackNameElem.innerText = item.name; trackNameElem.title = item.name; }

        const artistNameElem = query('.ArtistNameElement');
        if (artistNameElem) { artistNameElem.innerText = item.artists.map(a => a.name).join(', '); }

        const coverElem = query('.CoverElement');
        if (coverElem) { coverElem.src = item.album.images[0]?.url || ''; }

        const coverBgElem = query('.AlbumArtBackgroundElement');
        if (coverBgElem) { coverBgElem.src = item.album.images[0]?.url || ''; }

        const totalTimeElem = query('.TotalTimeElement');
        if (totalTimeElem) { totalTimeElem.innerText = this._formatTime(item.duration_ms); }
        
        this.logger.info(this.CALLER_FILE, "Tüm elementlerin içeriği başarıyla güncellendi.");
    }

    reset(set) {
        this.logger.info(this.CALLER_FILE, `Set içeriği sıfırlanıyor: ${set}`);
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);
        
        [query('.TrackNameElement'), query('.ArtistNameElement'), query('.TotalTimeElement'), query('.CurrentTimeElement')]
            .forEach(el => { if (el) el.innerText = (el.classList.contains('CurrentTimeElement') || el.classList.contains('TotalTimeElement')) ? '0:00' : ''; });
        
        [query('.CoverElement'), query('.AlbumArtBackgroundElement')]
            .forEach(el => { if (el) el.src = ''; });

        const progressBarElem = query('.ProgressBarElement');
        if (progressBarElem) progressBarElem.style.width = '0%';
    }

    startProgressUpdater(data, set) {
        this.stopProgressUpdater(); 
        this.logger.info(this.CALLER_FILE, `İlerleme çubuğu güncelleyici başlatılıyor (Set: ${set}).`);
        
        let progressMs = data.progress_ms;
        const durationMs = data.item.duration_ms;
        const currentTimeElem = this.widgetElement.querySelector(`.CurrentTimeElement[data-set="${set}"]`);
        const progressBarElem = this.widgetElement.querySelector(`.ProgressBarElement[data-set="${set}"]`);

        if (!currentTimeElem || !progressBarElem) {
             this.logger.warn(this.CALLER_FILE, "İlerleme çubuğu için gerekli elementler bulunamadı.");
             return;
        }

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
    
    stopProgressUpdater() {
        if (this.progressInterval) {
            this.logger.info(this.CALLER_FILE, 'İlerleme çubuğu güncelleyici durduruluyor.');
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    displayError(message) {
        this.logger.error(this.CALLER_FILE, `Hata Mesajı Gösteriliyor: ${message}`);
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement) {
            errorElement.innerText = message;
            this.widgetElement.classList.add(this.CSS_CLASSES.ERROR_ACTIVE);
        }
        this.stopProgressUpdater();
    }

    clearError() {
        this.logger.info(this.CALLER_FILE, 'Hata durumu temizleniyor.');
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
