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

        this.currentTrackId = null;
        this.isPlaying = false;
        this.isInitialLoad = true;
        this.activeSet = 'a';
        this.currentData = null; // En son gelen veriyi saklar
    }

    /**
     * Servisi başlatır ve periyodik veri çekme döngüsünü ayarlar.
     */
    init() {
        this.fetchData(); // İlk veriyi hemen çek
        setInterval(() => this.fetchData(), 1000); // Her saniye tekrarla
    }

    /**
     * Spotify API'sinden veriyi çeker ve işlemeye gönderir.
     */
    async fetchData() {
        try {
            const response = await fetch(this.endpoint);
            if (!response.ok) {
                this._dispatchEvent('widget:error', { message: `API Hatası: ${response.status}` });
                return;
            }
            const data = await response.json();
            this._processData(data);
        } catch (error) {
            console.error("Veri çekme hatası:", error);
            this._dispatchEvent('widget:error', { message: 'Widget verisi alınamıyor.' });
        }
    }

    /**
     * Gelen veriyi işler ve duruma göre uygun olayı tetikler.
     * @param {object} data - API'den gelen veri.
     */
    _processData(data) {
        this._dispatchEvent('widget:clear-error'); // Her başarılı istekte hatayı temizle
        this.currentData = data;

        // Durum 1: Müzik çalmıyor
        if (!data || !data.item || !data.is_playing) {
            if (this.isPlaying) { // Eğer daha önce çalıyorsa, durduruldu demektir
                this.isPlaying = false;
                this.currentTrackId = null;
                this.isInitialLoad = true; // Tekrar çalmaya başladığında intro animasyonu için
                this._dispatchEvent('widget:outro', { activeSet: this.activeSet });
            }
            return;
        }

        // Durum 2: İlk yükleme veya durduktan sonra yeniden başlama
        if (this.isInitialLoad) {
            this.isPlaying = true;
            this.isInitialLoad = false;
            this.currentTrackId = data.item.id;
            this._dispatchEvent('widget:intro', { set: this.activeSet, data: data });
            return;
        }
        
        // Durum 3: Şarkı değişti
        if (this.currentTrackId !== data.item.id) {
            this.isPlaying = true;
            const passiveSet = this.activeSet === 'a' ? 'b' : 'a';
            // Geçiş olayını tetikle, animasyon yöneticisi bunu yakalayacak
            this._dispatchEvent('widget:transition', { activeSet: this.activeSet, passiveSet: passiveSet, data: data });
            return;
        }

        // Durum 4: Aynı şarkı çalıyor (sadece ilerleme güncellenecek)
        this._dispatchEvent('widget:sync', { data: data, set: this.activeSet });
    }

    /**
     * Şarkı geçişi animasyonu tamamlandıktan sonra durumu sonlandırır.
     * Bu metod WidgetDOMManager tarafından çağrılır.
     * @param {string} newActiveSet - Yeni aktif set ('a' veya 'b').
     */
    finalizeTransition(newActiveSet) {
        this.activeSet = newActiveSet;
        this.currentTrackId = this.currentData.item.id;
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
