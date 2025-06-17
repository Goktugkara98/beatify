/**
 * @file main.js
 * @description Uygulamanın başlangıç noktası. Gerekli servisleri başlatır ve bağımlılıkları enjekte eder.
 */

document.addEventListener('DOMContentLoaded', () => {
    try {
        const widgetElement = document.getElementById('spotifyWidgetModern');
        const config = window.configData;

        // Gerekli element ve konfigürasyonun varlığını kontrol et
        if (!widgetElement) {
            throw new Error("Gerekli HTML elementi (ID: spotifyWidgetModern) bulunamadı.");
        }
        if (!config) {
            throw new Error("Backend konfigürasyonu (window.configData) bulunamadı.");
        }
        if (typeof SpotifyStateService === 'undefined' || typeof WidgetDOMManager === 'undefined' || typeof AnimationService === 'undefined' || typeof ContentUpdaterService === 'undefined') {
            throw new Error("Gerekli JavaScript sınıflarından biri veya birkaçı yüklenemedi.");
        }

        // Servisleri başlat
        const stateService = new SpotifyStateService(widgetElement);
        new WidgetDOMManager(widgetElement, config, stateService);

        // Veri çekme döngüsünü başlat
        stateService.init();

    } catch (error) {
        console.error("Widget başlatılırken kritik bir hata oluştu:", error);
        // İsteğe bağlı olarak kullanıcıya bir hata mesajı gösterebilirsiniz.
        const errorDisplay = document.getElementById('spotifyWidgetModern');
        if(errorDisplay) {
            errorDisplay.innerText = "Widget yüklenirken bir sorun oluştu. Lütfen daha sonra tekrar deneyin.";
            errorDisplay.style.color = 'white';
            errorDisplay.style.textAlign = 'center';
            errorDisplay.style.padding = '20px';
        }
    }
});
