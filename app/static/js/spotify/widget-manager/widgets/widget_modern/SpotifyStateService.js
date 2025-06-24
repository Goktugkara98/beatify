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
        // Her başarılı veri alımında hata mesajını temizle
        this._dispatchEvent('widget:clear-error');
        this.currentData = data;

        const isNowPlaying = data && data.item && data.is_playing;
        const newTrackId = isNowPlaying ? data.item.id : null;

        // --- DURUM 1: MÜZİK ÇALMIYOR veya DURDURULDU ---
        if (!isNowPlaying) {
            if (this.isPlaying) { // Eğer önceden çalıyorsa, şimdi durduruldu demektir.
                console.log('%c[StateService] Olay: Şarkı Durduruldu', 'color: orange;');
                this.isPlaying = false;
                this.currentTrackId = null;
                this.isInitialLoad = true; // Bir sonraki şarkı başlangıcı 'intro' olmalı.
                this._dispatchEvent('widget:outro', { activeSet: this.activeSet });
            }
            // Zaten çalmıyorsa hiçbir şey yapma.
            return;
        }

        // --- DURUM 2: İLK ŞARKI AÇILIYOR (INTRO) ---
        // Widget'ın ilk yüklenmesi veya duraklatıldıktan sonra tekrar oynatılması durumu.
        if (this.isInitialLoad) {
            console.log('%c[StateService] Olay: İlk Şarkı Açılıyor (Intro)', 'color: green;');
            this.isPlaying = true;
            this.isInitialLoad = false;
            this.currentTrackId = newTrackId;
            this._dispatchEvent('widget:intro', { set: this.activeSet, data: data });
            return;
        }
        
        // --- DURUM 3: ŞARKI DEĞİŞTİ (TRANSITION) ---
        // Farklı bir şarkı ID'si tespit edildi.
        if (this.currentTrackId !== newTrackId) {
            console.log(`%c[StateService] Olay: Şarkı Değişti`, 'color: cyan;', `\n  Eski ID: ${this.currentTrackId}\n  Yeni ID: ${newTrackId}`);
            this.isPlaying = true;
            const passiveSet = this.activeSet === 'a' ? 'b' : 'a';
            // Geçiş olayını tetikle. DOM Yöneticisi animasyonu yönetecek.
            this._dispatchEvent('widget:transition', { activeSet: this.activeSet, passiveSet: passiveSet, data: data });
            // Not: currentTrackId burada DEĞİŞMEZ. Değişim, animasyon bittikten sonra `finalizeTransition` ile yapılır.
            return;
        }

        // --- DURUM 4: AYNI ŞARKI ÇALIYOR (SYNC) ---
        // Hiçbir durum değişmedi, sadece ilerleme çubuğu güncellenmeli.
        if (this.isPlaying) {
            // console.log('[StateService] Olay: Senkronizasyon (Aynı şarkı devam ediyor)'); // Bu log çok sık tekrarlanacağı için kapatıldı.
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