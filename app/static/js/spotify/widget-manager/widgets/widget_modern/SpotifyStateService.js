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
        if (!widgetElement) throw new Error("SpotifyStateService için bir widget elementi sağlanmalıdır!");

        // --- Temel Yapılandırma ---
        this.widgetElement = widgetElement;
        this.token = widgetElement.dataset.token;
        this.endpoint = widgetElement.dataset.endpointTemplate.replace('{TOKEN}', this.token);

        // --- Durum Yönetimi Değişkenleri ---
        this.currentTrackId = null;     // Mevcut çalınan parçanın Spotify ID'si.
        this.isPlaying = false;         // Müziğin çalıp çalmadığını belirten boolean.
        this.isInitialLoad = true;      // Widget'ın ilk yüklemesi olup olmadığını kontrol eder.
        this.activeSet = 'a';           // Animasyonlar için aktif olan element setini ('a' veya 'b') belirtir.
        this.currentData = null;        // API'den gelen son başarılı veri.
        this.pollInterval = null;       // setInterval referansını tutar.
    }

    /**
     * 1.2. init
     * Servisi başlatır. İlk veri çekme işlemini yapar ve ardından periyodik olarak verileri günceller.
     */
    init() {
        this.fetchData(); // Başlangıçta veriyi hemen çek
        this.pollInterval = setInterval(() => this.fetchData(), 5000); // Her 5 saniyede bir tekrarla
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
        try {
            const response = await fetch(this.endpoint);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({})); // Hata mesajını alamazsa boş obje döner
                this.dispatchEvent('widget:error', { message: errorData.error || `Sunucu hatası: ${response.status}` });
                return;
            }
            const data = await response.json();
            this.processData(data);
        } catch (error) {
            Logger.log(`[SpotifyStateService] Veri çekme hatası: ${error}`, 'STATE');
            this.dispatchEvent('widget:error', { message: "Widget verisi alınamıyor." });
        }
    }

    /**
     * 2.2. processData
     * API'den gelen veriyi analiz eder ve widget'ın hangi durumda olduğuna karar verir.
     * (Örn: Müzik durdu, yeni şarkı başladı, ilk açılış vb.)
     * @param {object} data - API'den gelen JSON verisi.
     */
    processData(data) {
        this.dispatchEvent('widget:clear-error'); // Başarılı veri alındı, eski hatayı temizle.
        this.currentData = data;

        // Durum 1: Müzik çalmıyor.
        if (!data.is_playing) {
            if (this.isPlaying) { // Eğer daha önce çalıyorduysa 'outro' animasyonu için olay tetikle.
                this.isPlaying = false;
                this.currentTrackId = null;
                this.dispatchEvent('widget:outro', { activeSet: this.activeSet });
            }
            return;
        }

        // Durum 2: İlk yükleme ve müzik çalıyor. ('intro' animasyonu)
        if (this.isInitialLoad) {
            this.isPlaying = true;
            this.isInitialLoad = false;
            this.currentTrackId = data.item.id;
            this.dispatchEvent('widget:intro', { set: this.activeSet, data: data });
            return;
        }

        // Durum 3: Şarkı değişti. ('transition' animasyonu)
        if (this.currentTrackId !== data.item.id) {
            this.isPlaying = true;
            const passiveSet = this.activeSet === 'a' ? 'b' : 'a';
            this.dispatchEvent('widget:transition', {
                activeSet: this.activeSet,
                passiveSet: passiveSet,
                data: data
            });
            return;
        }
        
        // Durum 4: Aynı şarkı çalmaya devam ediyor veya duraklatmadan geri döndü. ('sync')
        if (!this.isPlaying) {
             this.isPlaying = true; // Duraklatılmış durumdan oynatılıyor durumuna geçiş.
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
        this.activeSet = newActiveSet;
        this.currentTrackId = this.currentData.item.id;
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
        this.widgetElement.dispatchEvent(event);
    }
}