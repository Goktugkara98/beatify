document.addEventListener('DOMContentLoaded', async () => {
    try {
        const widgetElement = document.getElementById('spotifyWidgetModern');
        if (!widgetElement) {
            throw new Error("Ana widget elementi bulunamadı.");
        }

        const themeService = new ThemeService();
        await themeService.load();

        const stateService = new SpotifyStateService(widgetElement);
        const contentUpdater = new ContentUpdaterService(widgetElement);
        const animationService = new GSAPAnimationService(widgetElement, themeService);

        new WidgetDOMManager(widgetElement, {
            stateService,
            animationService,
            contentUpdater
        });

        stateService.init();

    } catch (error) {
        // Hata durumunda konsola bir şey yazdırılmayacak.
    }
});