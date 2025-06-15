// DOSYA ADI: main.js
// =================================================================================================
// ||                                     İÇİNDEKİLER                                             ||
// =================================================================================================
//
// 1.0. WIDGET BAŞLATMA (Widget Initialization)
//    - DOMContentLoaded Event Listener: Sayfa tamamen yüklendiğinde widget'ı başlatan ana mantık.
//
// =================================================================================================

/**
 * 1.0. WIDGET BAŞLATMA
 * Sayfa içeriği tamamen yüklendiğinde (DOMContentLoaded), widget'ı başlatmak için bu olay dinleyici tetiklenir.
 * Gerekli tüm bileşenlerin ve yapılandırmanın mevcut olduğunu doğrular, ardından servisleri başlatır.
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1.1. Gerekli Element ve Konfigürasyonun Alınması
    const widgetElement = document.getElementById('spotifyWidgetModern');
    const config = window.configData; // Backend'den gelen yapılandırma verisi

    // 1.2. Doğrulama Kontrolleri
    // Gerekli HTML elementi veya JavaScript sınıfları bulunamazsa hata günlüğe kaydedilir ve işlem durdurulur.
    if (!widgetElement || typeof SpotifyStateService === 'undefined' || typeof WidgetDOMManager === 'undefined') {
        Logger.log("[Main] HATA: Gerekli HTML elementi (spotifyWidgetModern) veya sınıflar (SpotifyStateService, WidgetDOMManager) bulunamadı.", 'MAIN');
        return;
    }

    // Backend konfigürasyonu yüklenemezse hata günlüğe kaydedilir.
    if (!config) {
        Logger.log("[Main] HATA: Backend konfigürasyonu (window.configData) yüklenemedi.", 'MAIN');
        return;
    }
    
    // 1.3. Servislerin Başlatılması
    // StateService, widget'ın durumunu (hangi şarkı çalıyor, duraklatıldı mı vb.) yönetir.
    const stateService = new SpotifyStateService(widgetElement);
    
    // DOMManager, tüm görsel güncellemeleri, animasyonları ve DOM manipülasyonlarını yönetir.
    // StateService'den gelen olayları dinleyerek çalışır.
    new WidgetDOMManager(widgetElement, config, stateService);

    // 1.4. Sistemi Çalıştırma
    // StateService'in init() metodu, Spotify verilerini çekme sürecini başlatır ve widget'ı canlandırır.
    stateService.init();
    
    Logger.log("[Main] Spotify Widget başarıyla başlatıldı.", 'MAIN');
});