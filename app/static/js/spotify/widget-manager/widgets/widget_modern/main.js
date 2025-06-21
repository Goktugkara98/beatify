/**
 * =================================================================================
 * Uygulama Başlatıcı (main.js)
 * =================================================================================
 *
 * Bu dosya, uygulamanın ana başlangıç noktasıdır. DOM yüklendiğinde çalışır
 * ve aşağıdaki adımları izler:
 *
 * 1. Gerekli HTML Elementini ve Konfigürasyonu Bulur:
 * - 'spotifyWidgetModern' ID'li ana widget elementini seçer.
 * - 'window.configData' üzerinden backend konfigürasyonunu alır.
 *
 * 2. Bağımlılıkları Kontrol Eder:
 * - Gerekli tüm servis sınıflarının (SpotifyStateService, WidgetDOMManager, vb.)
 * yüklendiğinden emin olur.
 *
 * 3. Servisleri Başlatır:
 * - SpotifyStateService'i oluşturur (API iletişimi için).
 * - WidgetDOMManager'ı oluşturur (DOM manipülasyonları için).
 *
 * 4. Veri Akışını Başlatır:
 * - SpotifyStateService'in `init()` metodunu çağırarak periyodik veri
 * çekme döngüsünü tetikler.
 *
 * 5. Hata Yönetimi:
 * - Başlatma sırasında herhangi bir kritik hata olursa yakalar, konsola
 * yazdırır ve kullanıcıya bir hata mesajı gösterir.
 *
 * =================================================================================
 */
document.addEventListener('DOMContentLoaded', () => {
    try {
        // --- 1. Gerekli Element ve Konfigürasyonu Bulma ---
        const widgetElement = document.getElementById('spotifyWidgetModern');
        const config = window.configData;

        // --- 2. Bağımlılık Kontrolü ---
        if (!widgetElement) {
            throw new Error("Gerekli HTML elementi (ID: spotifyWidgetModern) bulunamadı.");
        }
        if (!config) {
            throw new Error("Backend konfigürasyonu (window.configData) bulunamadı.");
        }
        if (typeof SpotifyStateService === 'undefined' || typeof WidgetDOMManager === 'undefined' || typeof AnimationService === 'undefined' || typeof ContentUpdaterService === 'undefined') {
            throw new Error("Gerekli JavaScript sınıflarından biri veya birkaçı yüklenemedi.");
        }

        // --- 3. Servisleri Başlatma ---
        const stateService = new SpotifyStateService(widgetElement);
        new WidgetDOMManager(widgetElement, config, stateService);

        // --- 4. Veri Akışını Başlatma ---
        stateService.init();

    } catch (error) {
        // --- 5. Hata Yönetimi ---
        console.error("Widget başlatılırken kritik bir hata oluştu:", error);
        const errorDisplay = document.getElementById('spotifyWidgetModern');
        if (errorDisplay) {
            errorDisplay.innerText = "Widget yüklenirken bir sorun oluştu. Lütfen daha sonra tekrar deneyin.";
            errorDisplay.style.color = 'white';
            errorDisplay.style.textAlign = 'center';
            errorDisplay.style.padding = '20px';
        }
    }
});
