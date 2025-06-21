/**
 * =================================================================================
 * SpotifyStateService - İçindekiler
 * =================================================================================
 *
 * Spotify API'sinden veri çeker, durumu yönetir ve widget olaylarını tetikler.
 *
 * ---
 *
 * BÖLÜM 1: KURULUM VE BAŞLATMA (SETUP & INITIALIZATION)
 * 1.1. constructor: Servisi başlatır ve temel değişkenleri ayarlar.
 * 1.2. init: Servisi başlatır ve periyodik veri çekme döngüsünü ayarlar.
 *
 * BÖLÜM 2: VERİ YÖNETİMİ (DATA MANAGEMENT)
 * 2.1. fetchData: Spotify API'sinden mevcut çalma durumunu çeker.
 * 2.2. _processData: API'den gelen veriyi işler ve duruma göre ilgili olayı tetikler.
 *
 * BÖLÜM 3: DURUM GÜNCELLEME (STATE UPDATE)
 * 3.1. finalizeTransition: Şarkı geçişi animasyonu sonrası durumu günceller.
 *
 * BÖLÜM 4: ÖZEL OLAY YAYINLAMA (PRIVATE EVENT DISPATCHING)
 * 4.1. _dispatchEvent: Widget elementinde özel bir olay tetikler.
 *
 * =================================================================================
 */
class SpotifyStateService {
    // =================================================================================
    // BÖLÜM 1: KURULUM VE BAŞLATMA (SETUP & INITIALIZATION)
    // =================================================================================

    /**
     * 1.1. SpotifyStateService'in bir örneğini oluşturur.
     * @param {HTMLElement} widgetElement - Widget'ın ana elementi.
     */
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
     * 1.2. Servisi başlatır ve periyodik veri çekme döngüsünü ayarlar.
     */
    init() {
        this.fetchData();
        this.pollInterval = setInterval(() => this.fetchData(), 5000);
    }

    // =================================================================================
    // BÖLÜM 2: VERİ YÖNETİMİ (DATA MANAGEMENT)
    // =================================================================================

    /**
     * 2.1. Spotify API'sinden mevcut çalma durumunu çeker.
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
     * 2.2. API'den gelen veriyi işler ve duruma göre ilgili olayı tetikler.
     * @param {object} data - API'den gelen veri.
     * @private
     */
    _processData(data) {
        this._dispatchEvent('widget:clear-error');
        this.currentData = data;

        if (!data.is_playing) {
            if (this.isPlaying) {
                this.isPlaying = false;
                this.currentTrackId = null;
                this._dispatchEvent('widget:outro', { activeSet: this.activeSet });
            }
            return;
        }

        if (this.isInitialLoad) {
            this.isPlaying = true;
            this.isInitialLoad = false;
            this.currentTrackId = data.item.id;
            this._dispatchEvent('widget:intro', { set: this.activeSet, data: data });
            return;
        }

        if (this.currentTrackId !== data.item.id) {
            this.isPlaying = true;
            const passiveSet = this.activeSet === 'a' ? 'b' : 'a';
            this._dispatchEvent('widget:transition', { activeSet: this.activeSet, passiveSet: passiveSet, data: data });
            return;
        }
        
        this._dispatchEvent('widget:sync', { data: data, set: this.activeSet });
    }

    // =================================================================================
    // BÖLÜM 3: DURUM GÜNCELLEME (STATE UPDATE)
    // =================================================================================

    /**
     * 3.1. Şarkı geçişi animasyonu tamamlandıktan sonra durumu günceller.
     * @param {string} newActiveSet - Yeni aktif set ('a' veya 'b').
     */
    finalizeTransition(newActiveSet) {
        this.activeSet = newActiveSet;
        this.currentTrackId = this.currentData.item.id;
        this._dispatchEvent('widget:sync', { data: this.currentData, set: this.activeSet });
    }

    // =================================================================================
    // BÖLÜM 4: ÖZEL OLAY YAYINLAMA (PRIVATE EVENT DISPATCHING)
    // =================================================================================

    /**
     * 4.1. Widget elementinde özel bir olay tetikler.
     * @param {string} eventName - Tetiklenecek olayın adı.
     * @param {object} detail - Olayla birlikte gönderilecek veri.
     * @private
     */
    _dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        this.widgetElement.dispatchEvent(event);
    }
}
