// ===================================================================================
// DOSYA ADI: main.js
// AÇIKLAMA: Uygulamanın başlangıç noktası. Servisleri başlatır ve
//           bağımlılıkları enjekte eder.
// YENİ YAPI NOTU: Bu dosya, en üst seviye 'WIDGET BAŞLATMA SÜRECİ' grubunu
//                 yönetir ve tüm başlatma işlemlerinin bu grup altında
//                 loglanmasını sağlar.
// ===================================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Logger servisini başlat
    const logger = new LoggerService();
    window.logger = logger; // Diğer dosyalardan kolay erişim için global yap

    const CALLER_FILE = 'main.js';
    
    // En üst seviye başlangıç grubunu oluştur
    logger.group('WIDGET BAŞLATMA SÜRECİ');

    try {
        const widgetElement = document.getElementById('spotifyWidgetModern');
        const config = window.configData;

        if (!widgetElement || typeof SpotifyStateService === 'undefined' || typeof WidgetDOMManager === 'undefined') {
            logger.error(CALLER_FILE, "Hata: Gerekli HTML elementi (spotifyWidgetModern) veya sınıflar (SpotifyStateService, WidgetDOMManager) bulunamadı.");
            return; // groupEnd() finally bloğunda çalışacak
        }

        if (!config) {
            logger.error(CALLER_FILE, "Backend konfigürasyonu (window.configData) bulunamadı.");
            return; // groupEnd() finally bloğunda çalışacak
        }

        logger.action(CALLER_FILE, 'Tüm doğrulamalar başarılı. Servisler başlatılıyor...');

        // Logger'ı servislere constructor üzerinden aktar
        const stateService = new SpotifyStateService(widgetElement, logger);
        new WidgetDOMManager(widgetElement, config, stateService, logger);

        // StateService'i başlat. Bu, veri çekme döngüsünü tetikleyecek.
        stateService.init();

        logger.info(CALLER_FILE, "Spotify Widget başarıyla başlatıldı.");

    } catch (error) {
        logger.error(CALLER_FILE, "Widget başlatılırken kritik bir hata oluştu:", error);
    } finally {
        // Başlatma süreci grubunu her durumda kapat
        logger.groupEnd();
    }
});
