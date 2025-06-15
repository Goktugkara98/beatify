// DOSYA ADI: SpotifyStateService.js
// =================================================================================================
// ||                                     İÇİNDEKİLER                                             ||
// =================================================================================================
//
// 1.0. KURULUM (SETUP)
//    1.1. constructor: Sınıfın başlangıç değerlerini ve temel yapılandırmasını ayarlar.
//    1.2. init: Veri çekme döngüsünü başlatarak servisi aktif hale getirir.
//
// 2.0. VERİ YÖNETİMİ VE API İLETİŞİMİ (DATA MANAGEMENT & API COMMUNICATION)
//    2.1. fetchData: Belirtilen endpoint'ten Spotify dinleme verisini asenkron olarak çeker.
//    2.2. processData: Gelen veriyi işler, durum değişikliklerini tespit eder ve ilgili olayları tetikler.
//
// 3.0. DURUM GÜNCELLEME VE OLAY TETİKLEME (STATE UPDATE & EVENT FIRING)
//    3.1. finalizeTransition: Geçiş animasyonu tamamlandığında DOM Yöneticisi tarafından çağrılır.
//    3.2. dispatchEvent: Widget elementine özel olaylar (custom events) gönderen yardımcı metot.
//
// =================================================================================================

class SpotifyStateService {
    // =========================================================================
    // ||                          1.0. KURULUM (SETUP)                       ||
    // =========================================================================

    /**
     * 1.1. constructor
     * Sınıf örneği oluşturulduğunda çağrılır. Temel değişkenleri ve durumları ayarlar.
     * @param {HTMLElement} widgetElement - Ana widget HTML elementi.
     */
    constructor(widgetElement) {
        console.log('[SpotifyStateService] Initializing with widget element');
        if (!widgetElement) throw new Error("SpotifyStateService için bir widget elementi sağlanmalıdır!");

        // --- Temel Yapılandırma ---
        this.widgetElement = widgetElement;
        this.token = widgetElement.dataset.token;
        this.endpoint = widgetElement.dataset.endpointTemplate.replace('{TOKEN}', this.token);
        console.log(`[SpotifyStateService] Endpoint configured: ${this.endpoint}`);

        // --- Durum Yönetimi Değişkenleri ---
        this.currentTrackId = null;     // Mevcut çalınan parçanın Spotify ID'si.
        this.isPlaying = false;         // Müziğin çalıp çalmadığını belirten boolean.
        this.isInitialLoad = true;      // Widget'ın ilk yüklemesi olup olmadığını kontrol eder.
        this.activeSet = 'a';           // Animasyonlar için aktif olan element setini ('a' veya 'b') belirtir.
        this.currentData = null;        // API'den gelen son başarılı veri.
        this.pollInterval = null;       // setInterval referansını tutar.
        this.pollCount = 0;             // Polling sayacı
    }

    /**
     * 1.2. init
     * Servisi başlatır. İlk veri çekme işlemini yapar ve ardından periyodik olarak verileri günceller.
     */
    init() {
        console.log('[SpotifyStateService] Initializing service, starting data polling');
        this.fetchData(); // Başlangıçta veriyi hemen çek
        this.pollInterval = setInterval(() => {
            this.pollCount++;
            console.log(`[SpotifyStateService] Polling data (${this.pollCount})`);
            this.fetchData();
        }, 5000); // Her 5 saniyede bir tekrarla
    }

    // =========================================================================
    // ||      2.0. VERİ YÖNETİMİ VE API İLETİŞİMİ (DATA & API)               ||
    // =========================================================================

    /**
     * 2.1. fetchData
     * Yapılandırılmış endpoint'e bir GET isteği göndererek mevcut dinleme verisini çeker.
     * Hata durumlarını yönetir ve 'widget:error' olayını tetikler.
     */
    async fetchData() {
        const startTime = performance.now();
        try {
            console.log(`[SpotifyStateService] Fetching data from: ${this.endpoint}`);
            const response = await fetch(this.endpoint);
            const fetchTime = performance.now() - startTime;
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.error || `Sunucu hatası: ${response.status}`;
                console.error(`[SpotifyStateService] API Error (${response.status}): ${errorMessage} (${fetchTime.toFixed(2)}ms)`);
                this.dispatchEvent('widget:error', { message: errorMessage });
                return;
            }
            
            const data = await response.json();
            const totalTime = performance.now() - startTime;
            console.log(`[SpotifyStateService] Data fetched in ${totalTime.toFixed(2)}ms (${fetchTime.toFixed(2)}ms network)`);
            this.processData(data);
        } catch (error) {
            const totalTime = performance.now() - startTime;
            console.error(`[SpotifyStateService] Fetch error after ${totalTime.toFixed(2)}ms:`, error);
            this.dispatchEvent('widget:error', { 
                message: `Widget verisi alınamıyor: ${error.message || 'Bilinmeyen hata'}` 
            });
        }
    }

    /**
     * 2.2. processData
     * API'den gelen veriyi analiz eder ve widget'ın hangi durumda olduğuna karar verir.
     * (Örn: Müzik durdu, yeni şarkı başladı, ilk açılış vb.)
     * @param {object} data - API'den gelen JSON verisi.
     */
    processData(data) {
        console.log('[SpotifyStateService] Processing new data:', {
            isPlaying: data.is_playing,
            track: data.item ? `${data.item.name} by ${data.item.artists.map(a => a.name).join(', ')}` : 'No track',
            progress: data.progress_ms ? `${Math.floor(data.progress_ms/1000)}s` : 'N/A'
        });
        
        this.dispatchEvent('widget:clear-error'); // Başarılı veri alındı, eski hatayı temizle.
        this.currentData = data;

        // Durum 1: Müzik çalmıyor.
        if (!data.is_playing) {
            if (this.isPlaying) { // Eğer daha önce çalıyorduysa 'outro' animasyonu için olay tetikle.
                console.log('[SpotifyStateService] Music stopped, triggering outro animation');
                this.isPlaying = false;
                this.currentTrackId = null;
                this.dispatchEvent('widget:outro', { activeSet: this.activeSet });
            } else {
                console.log('[SpotifyStateService] Music is still not playing, no state change');
            }
            return;
        }

        // Durum 2: İlk yükleme ve müzik çalıyor. ('intro' animasyonu)
        if (this.isInitialLoad) {
            console.log('[SpotifyStateService] Initial load with music playing, triggering intro');
            this.isPlaying = true;
            this.isInitialLoad = false;
            this.currentTrackId = data.item.id;
            console.log(`[SpotifyStateService] Current track set to: ${data.item.id}`);
            this.dispatchEvent('widget:intro', { set: this.activeSet, data: data });
            return;
        }

        // Durum 3: Şarkı değişti. ('transition' animasyonu)
        if (this.currentTrackId !== data.item.id) {
            console.log(`[SpotifyStateService] Track changed from ${this.currentTrackId} to ${data.item.id}, triggering transition`);
            this.isPlaying = true;
            const passiveSet = this.activeSet === 'a' ? 'b' : 'a';
            console.log(`[SpotifyStateService] Active set: ${this.activeSet}, Passive set: ${passiveSet}`);
            this.dispatchEvent('widget:transition', {
                activeSet: this.activeSet,
                passiveSet: passiveSet,
                data: data
            });
            return;
        }
        
        // Durum 4: Aynı şarkı çalmaya devam ediyor veya duraklatmadan geri döndü. ('sync')
        if (!this.isPlaying) {
            console.log('[SpotifyStateService] Music resumed after pause');
            this.isPlaying = true; // Duraklatılmış durumdan oynatılıyor durumuna geçiş.
        } else {
            console.log('[SpotifyStateService] Same track still playing, syncing progress');
        }
        this.dispatchEvent('widget:sync', { data: data, set: this.activeSet });
    }

    // =========================================================================
    // ||        3.0. DURUM GÜNCELLEME VE OLAY TETİKLEME (STATE & EVENTS)     ||
    // =========================================================================
    
    /**
     * 3.1. finalizeTransition
     * Bu metot, `WidgetDOMManager` tarafından bir geçiş animasyonu tamamlandığında çağrılır.
     * Aktif seti günceller ve yeni şarkının verilerini senkronize eder.
     * @param {string} newActiveSet - Yeni aktif set ('a' veya 'b').
     */
    finalizeTransition(newActiveSet) {
        console.log(`[SpotifyStateService] Finalizing transition to new active set: ${newActiveSet}`);
        this.activeSet = newActiveSet;
        this.currentTrackId = this.currentData.item.id;
        console.log(`[SpotifyStateService] Active set updated to: ${this.activeSet}, current track ID: ${this.currentTrackId}`);
        // Olay, yeni setin ilerleme çubuğunun senkronize edilmesi gerektiğini bildirir.
        this.dispatchEvent('widget:sync', { data: this.currentData, set: this.activeSet });
    }

    /**
     * 3.2. dispatchEvent
     * Widget DOM elementine özel olaylar gönderir. Bu olaylar `WidgetDOMManager` tarafından dinlenir.
     * @param {string} eventName - Gönderilecek olayın adı (örn: 'widget:intro').
     * @param {object} detail - Olayla birlikte gönderilecek veri.
     */
    dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail: detail });
        console.log(`[SpotifyStateService] Dispatching event: ${eventName}`, detail);
        this.widgetElement.dispatchEvent(event);
    }
}