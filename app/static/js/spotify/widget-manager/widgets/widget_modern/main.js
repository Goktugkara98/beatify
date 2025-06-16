// ===================================================================================
// DOSYA ADI: main.js
// AÇIKLAMA: Uygulamanın başlangıç noktası. Servisleri başlatır ve
//           bağımlılıkları enjekte eder.
// ===================================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Logger servisini başlat
    // Not: Bu dosyadan önce LoggerService.js'nin yüklendiğinden emin olun.
    const logger = new LoggerService();
    window.logger = logger; // Diğer dosyalardan kolay erişim için global yap

    const CALLER_FILE = 'main.js';

    logger.group('WIDGET BAŞLATMA SÜRECİ');

    const widgetElement = document.getElementById('spotifyWidgetModern');
    const config = window.configData;

    if (!widgetElement || typeof SpotifyStateService === 'undefined' || typeof WidgetDOMManager === 'undefined') {
        logger.error(CALLER_FILE, "Hata: Gerekli HTML elementi (spotifyWidgetModern) veya sınıflar (SpotifyStateService, WidgetDOMManager) bulunamadı.");
        logger.groupEnd();
        return;
    }

    if (!config) {
        logger.error(CALLER_FILE, "Backend konfigürasyonu (window.configData) bulunamadı.");
        logger.groupEnd();
        return;
    }

    logger.action(CALLER_FILE, 'Tüm doğrulamalar başarılı. Servisler başlatılıyor...');

    // Logger'ı servislere constructor üzerinden aktar
    const stateService = new SpotifyStateService(widgetElement, logger);
    new WidgetDOMManager(widgetElement, config, stateService, logger);

    stateService.init();

    logger.info(CALLER_FILE, "Spotify Widget başarıyla başlatıldı.");
    logger.groupEnd();
});
