// YENİ DOSYA ADI: main.js

document.addEventListener('DOMContentLoaded', () => {
    const widgetElement = document.getElementById('spotifyWidgetModern'); //
    
    // Gerekli sınıfların varlığını kontrol et
    if (!widgetElement || typeof SpotifyStateService === 'undefined' || typeof WidgetDOMManager === 'undefined') { //
        console.error("[Main] HATA: Gerekli sınıflar (StateService, DOMManager) bulunamadı.");
        return;
    }

    // Backend konfigürasyonunu al
    const config = window.configData; //
    if (!config) { //
        console.error("[Main] HATA: Backend konfigürasyonu yüklenemedi."); //
        return;
    }
    
    // Sınıfları başlat
    const stateService = new SpotifyStateService(widgetElement); //
    new WidgetDOMManager(widgetElement, config, stateService); // DOM Yöneticisi state'i bilmeli

    // Sistemi çalıştır
    stateService.init();
});