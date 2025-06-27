/**
 * @file SpotifyStateService.js
 * @description Spotify API'sinden veri çeker, durumu yönetir ve widget olaylarını tetikler.
 * Bu servis, uygulamanın durum makinesi (state machine) olarak görev yapar.
 */
class SpotifyStateService {
    /**
     * @param {HTMLElement} widgetElement - Ana widget elementi.
     */
    constructor(widgetElement) {
        this.widgetElement = widgetElement;
        const token = widgetElement.dataset.token;
        const endpointTemplate = widgetElement.dataset.endpointTemplate;
        this.endpoint = endpointTemplate.replace('{TOKEN}', token);

        // Durum (State) Değişkenleri
        this.currentTrackId = null; // Mevcut çalan şarkının ID'si
        this.isPlaying = false;     // Müzik çalıyor mu?
        this.isInitialLoad = true;  // Widget ilk defa mı yükleniyor?
        this.activeSet = 'a';       // Geçiş animasyonları için aktif set (a/b)
        this.currentData = null;    // API'den gelen en son geçerli veri
        
        console.log('[StateService] Servis başlatıldı. Endpoint:', this.endpoint);
    }

    /**
     * Servisi başlatır ve periyodik veri çekme döngüsünü ayarlar.
     */
    init() {
        this.fetchData(); // İlk veriyi hemen çek
        setInterval(() => this.fetchData(), 2000); // Veri çekme sıklığını 2 saniyeye ayarladım
    }

    /**
     * Spotify API'sinden veriyi çeker ve işlemeye gönderir.
     */
    async fetchData() {
        try {
            const response = await fetch(this.endpoint);
            if (!response.ok) {
                // API hatalarını bir kere göster, sürekli loglamayı önle
                if (this.isPlaying || this.isInitialLoad) {
                    console.error(`[StateService] API Hatası: ${response.status}`);
                    this._dispatchEvent('widget:error', { message: `API Hatası: ${response.status}` });
                }
                this.isPlaying = false;
                return;
            }
            const data = await response.json();
            this._processData(data);
        } catch (error) {
            console.error("[StateService] Veri çekme hatası:", error);
            this._dispatchEvent('widget:error', { message: 'Widget verisi alınamıyor.' });
            this.isPlaying = false;
        }
    }

    /**
     * Gelen veriyi işler ve duruma göre uygun olayı tetikler.
     * @param {object} data - API'den gelen veri.
     */
    _processData(data) {
        this._dispatchEvent('widget:clear-error');
        this.currentData = data;

        const isNowPlaying = data && data.item && data.is_playing;
        const newTrackId = isNowPlaying ? data.item.id : null;
        // console.log(`%c[StateService] Veri işleniyor. isNowPlaying: ${isNowPlaying}, newTrackId: ${newTrackId}, currentTrackId: ${this.currentTrackId}, isInitialLoad: ${this.isInitialLoad}`, 'color: #9E9E9E');

        if (!isNowPlaying) {
            if (this.isPlaying) {
                console.log('%c[StateService] DURUM 1: Şarkı Durduruldu -> widget:outro tetikleniyor.', 'color: orange; font-weight: bold;');
                this.isPlaying = false;
                this.currentTrackId = null;
                this.isInitialLoad = true;
                this._dispatchEvent('widget:outro', { activeSet: this.activeSet });
            }
            return;
        }

        if (this.isInitialLoad) {
            console.log('%c[StateService] DURUM 2: İlk Şarkı -> widget:intro tetikleniyor.', 'color: green; font-weight: bold;');
            this.isPlaying = true;
            this.isInitialLoad = false;
            this.currentTrackId = newTrackId;
            this._dispatchEvent('widget:intro', { set: this.activeSet, data: data });
            return;
        }

        if (this.currentTrackId !== newTrackId) {
            console.log(`%c[StateService] DURUM 3: Şarkı Değişti -> widget:transition tetikleniyor.`, 'color: cyan; font-weight: bold;', `\n  Eski ID: ${this.currentTrackId}\n  Yeni ID: ${newTrackId}`);
            this.isPlaying = true;
            const passiveSet = this.activeSet === 'a' ? 'b' : 'a';
            this._dispatchEvent('widget:transition', { activeSet: this.activeSet, passiveSet: passiveSet, data: data });
            return;
        }

        if (this.isPlaying) {
            // console.log('[StateService] DURUM 4: Senkronizasyon');
            this._dispatchEvent('widget:sync', { data: data, set: this.activeSet });
        }
    }

    /**
     * Şarkı geçişi animasyonu tamamlandıktan sonra durumu sonlandırır.
     * Bu metod WidgetDOMManager tarafından çağrılır.
     * @param {string} newActiveSet - Yeni aktif set ('a' veya 'b').
     */
    finalizeTransition(newActiveSet) {
        console.log(`%c[StateService] Geçiş Sonlandırıldı. Yeni Aktif Set: ${newActiveSet}`, 'color: purple;');
        this.activeSet = newActiveSet;
        // State'i en güncel veri ile güncelle
        if (this.currentData && this.currentData.item) {
            this.currentTrackId = this.currentData.item.id;
        }
    }

    /**
     * Widget genelinde özel bir olay yayınlar.
     * @param {string} eventName - Olayın adı (örn: 'widget:intro').
     * @param {object} detail - Olayla birlikte gönderilecek veri.
     */
    _dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        this.widgetElement.dispatchEvent(event);
    }
}