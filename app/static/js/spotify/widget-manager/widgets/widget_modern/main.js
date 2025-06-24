/**
 * @file main.js
 * @description Uygulamanın ana başlangıç noktasıdır.
 * Gerekli servisleri ve yöneticileri başlatır.
 */
document.addEventListener('DOMContentLoaded', () => {
    try {
        const widgetElement = document.getElementById('spotifyWidgetModern');
        if (!widgetElement) {
            throw new Error("Ana widget elementi (ID: spotifyWidgetModern) bulunamadı.");
        }

        // 1. Durum ve veri akışını yönetecek servisi başlat
        const stateService = new SpotifyStateService(widgetElement);

        // 2. Arayüzü (DOM) yönetecek olan yöneticiyi başlat
        new WidgetDOMManager(widgetElement, stateService);

        // 3. Veri çekme döngüsünü başlat
        stateService.init();

    } catch (error) {
        console.error("Widget başlatılırken kritik bir hata oluştu:", error);
        const errorDisplay = document.getElementById('spotifyWidgetModern');
        if (errorDisplay) {
            errorDisplay.innerText = "Widget yüklenemedi.";
            errorDisplay.classList.remove('widget-inactive');
        }
    }
});
