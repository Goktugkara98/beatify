// ===================================================================================
// DOSYA ADI: main.js
// ===================================================================================
document.addEventListener('DOMContentLoaded', () => {
    // YENİ: Logger servisini başlat
    const logger = new LoggerService();
    window.logger = logger; // Diğer dosyalardan kolay erişim için global yap

    logger.group('WIDGET BAŞLATMA SÜRECİ');

    const widgetElement = document.getElementById('spotifyWidgetModern');
    const config = window.configData;

    if (!widgetElement || typeof SpotifyStateService === 'undefined' || typeof WidgetDOMManager === 'undefined') {
        logger.error("Hata: Gerekli HTML elementi (spotifyWidgetModern) veya sınıflar (SpotifyStateService, WidgetDOMManager) bulunamadı.");
        logger.groupEnd();
        return;
    }

    if (!config) {
        logger.error("Backend konfigürasyonu (window.configData) bulunamadı.");
        logger.groupEnd();
        return;
    }

    logger.action('Tüm doğrulamalar başarılı.');
    logger.action('Servisler başlatılıyor...');

    // YENİ: Logger'ı servislere constructor üzerinden aktar
    const stateService = new SpotifyStateService(widgetElement, logger);
    new WidgetDOMManager(widgetElement, config, stateService, logger);

    stateService.init();

    logger.info("Spotify Widget başarıyla başlatıldı.");
    logger.groupEnd();
});
