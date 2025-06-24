document.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('[main.js] DOM yüklendi, widget başlatılıyor...');
        const widgetElement = document.getElementById('spotifyWidgetModern');
        if (!widgetElement) {
            throw new Error("Ana widget elementi bulunamadı.");
        }

        // 1. Tüm servisleri burada oluşturuyoruz.
        const themeService = new ThemeService();
        await themeService.load();

        const stateService = new SpotifyStateService(widgetElement);
        const cssParser = new CSSAnimationParser();
        const contentUpdater = new ContentUpdaterService(widgetElement);
        // AnimationService, ihtiyaç duyduğu themeService ve cssParser ile oluşturuluyor.
            const animationService = new AnimationService(widgetElement, themeService, cssParser);
            // YENİ LOG SATIRI:
            console.log('%c[main.js] OLUŞTURULAN animationService:', 'color: green; font-weight: bold;', animationService);


    // DOM Yöneticisine, oluşturduğumuz tüm servisleri bir "paket" halinde veriyoruz.
    new WidgetDOMManager(widgetElement, {
        stateService,
        animationService,
        contentUpdater
    });

        // 3. Başlatma komutunu veriyoruz.
        stateService.init();
        
        console.log('[main.js] Widget başarıyla başlatıldı.');

    } catch (error) {
        console.error("!!! [main.js] Widget başlatılırken kritik bir hata oluştu: !!!", error.message);
    }
});