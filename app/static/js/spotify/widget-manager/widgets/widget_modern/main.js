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

        // Parent pencereden (Widget Manager) gelen mesajları dinle
        window.addEventListener('message', (event) => {
            if (event.data === 'startOutro') {
                // Outro animasyonunu tetikle
                widgetElement.dispatchEvent(new CustomEvent('widget:outro'));
            } else if (event.data && event.data.type === 'changeTrack') {
                // Demo modunda track değiştir, değilse sadece yeni veri çek
                if (window.demoController && window.demoController.mockAPI) {
                    // Demo açık değilse otomatik başlat
                    if (!window.demoController.isActive) {
                        window.demoController.start();
                    }
                    window.demoController.mockAPI.nextTrack();
                }
                // Veriyi hemen yenile ki transition tetiklensin
                stateService.fetchData();
            }
        });

    } catch (error) {
        // Hata durumunda konsola bir şey yazdırılmayacak.
    }
});