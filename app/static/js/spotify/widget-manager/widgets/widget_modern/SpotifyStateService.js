/**
 * @class SpotifyStateService
 * @description Spotify API'sinden veri çeker, durumu yönetir ve widget olaylarını tetikler.
 */
class SpotifyStateService {
    constructor(widgetElement) {
        if (!widgetElement) {
            throw new Error("SpotifyStateService için bir widget elementi sağlanmalıdır!");
        }

        this.widgetElement = widgetElement;
        this.token = widgetElement.dataset.token;
        this.endpoint = widgetElement.dataset.endpointTemplate.replace('{TOKEN}', this.token);

        this.currentTrackId = null;
        this.isPlaying = false;
        this.isInitialLoad = true;
        this.activeSet = 'a';
        this.currentData = null;
        this.pollInterval = null;
    }

    /**
     * Servisi başlatır ve periyodik veri çekme döngüsünü ayarlar.
     */
    init() {
        this.fetchData();
        this.pollInterval = setInterval(() => this.fetchData(), 5000);
    }

    /**
     * Spotify API'sinden mevcut çalma durumunu çeker.
     * @async
     */
    async fetchData() {
        try {
            const response = await fetch(this.endpoint);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.error || `Sunucu hatası: ${response.status}`;
                this._dispatchEvent('widget:error', { message: errorMessage });
                return;
            }

            const data = await response.json();
            this._processData(data);
        } catch (error) {
            console.error("Fetch sırasında kritik hata:", error);
            this._dispatchEvent('widget:error', { message: `Widget verisi alınamıyor.` });
        }
    }

    /**
     * API'den gelen veriyi işler ve duruma göre ilgili olayı tetikler.
     * @param {object} data - API'den gelen veri.
     * @private
     */
    _processData(data) {
        this._dispatchEvent('widget:clear-error');
        this.currentData = data;

        // Müzik çalmıyorsa
        if (!data.is_playing) {
            if (this.isPlaying) {
                this.isPlaying = false;
                this.currentTrackId = null;
                this._dispatchEvent('widget:outro', { activeSet: this.activeSet });
            }
            return;
        }

        // İlk yükleme ise
        if (this.isInitialLoad) {
            this.isPlaying = true;
            this.isInitialLoad = false;
            this.currentTrackId = data.item.id;
            this._dispatchEvent('widget:intro', { set: this.activeSet, data: data });
            return;
        }

        // Şarkı değiştiyse
        if (this.currentTrackId !== data.item.id) {
            this.isPlaying = true;
            const passiveSet = this.activeSet === 'a' ? 'b' : 'a';
            this._dispatchEvent('widget:transition', { activeSet: this.activeSet, passiveSet: passiveSet, data: data });
            return;
        }
        
        // Aynı şarkı çalmaya devam ediyorsa (sadece senkronizasyon)
        this._dispatchEvent('widget:sync', { data: data, set: this.activeSet });
    }

    /**
     * Şarkı geçişi animasyonu tamamlandıktan sonra durumu günceller.
     * @param {string} newActiveSet - Yeni aktif set ('a' veya 'b').
     */
    finalizeTransition(newActiveSet) {
        this.activeSet = newActiveSet;
        this.currentTrackId = this.currentData.item.id;
        this._dispatchEvent('widget:sync', { data: this.currentData, set: this.activeSet });
    }

    /**
     * Widget elementinde özel bir olay tetikler.
     * @param {string} eventName - Tetiklenecek olayın adı.
     * @param {object} detail - Olayla birlikte gönderilecek veri.
     * @private
     */
    _dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        this.widgetElement.dispatchEvent(event);
    }
}
