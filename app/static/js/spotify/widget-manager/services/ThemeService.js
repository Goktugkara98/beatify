/**
 * ThemeService
 * Tema seçimi, carousel navigasyonu ve backend güncellemelerinden sorumludur.
 */
class ThemeService {
    constructor(elements, config, callbacks) {
        this.elements = elements;
        this.config = config;
        this.callbacks = callbacks; // { onThemeChanged: (theme) => void }

        this._initCarousel();
        this._bindThemeSelection();
    }

    /**
     * Carousel ok butonlarını ve kaydırma mantığını başlatır.
     */
    _initCarousel() {
        const { carousel, prevBtn, nextBtn } = this.elements;
        
        if (carousel && prevBtn && nextBtn) {
            prevBtn.addEventListener('click', () => {
                carousel.scrollBy({ left: -320, behavior: 'smooth' });
            });
            nextBtn.addEventListener('click', () => {
                carousel.scrollBy({ left: 320, behavior: 'smooth' });
            });
        }
    }

    /**
     * Tema kartlarına tıklama olaylarını dinler.
     */
    _bindThemeSelection() {
        const cards = document.querySelectorAll('.theme-card:not(.coming-soon)');
        
        cards.forEach(card => {
            card.addEventListener('click', async () => {
                const selectedTheme = card.dataset.theme;
                
                // UI Güncellemesi (Aktif kartı işaretle)
                cards.forEach(c => c.classList.remove('active'));
                card.classList.add('active');

                // Önizlemeyi gizle (geçiş efekti için)
                if (this.callbacks.onBeforeUpdate) {
                    this.callbacks.onBeforeUpdate();
                }

                // Tema değişikliğini bildir (Backend güncellemesi yapmadan)
                // Çünkü her temanın kendi widget'ı ve token'ı var.
                if (this.callbacks.onThemeChanged) {
                    this.callbacks.onThemeChanged(selectedTheme);
                }
            });
        });
    }

    /**
     * Tam konfigürasyonu backend'e gönderir.
     * @param {object} fullConfig 
     * @returns {Promise<boolean>}
     */
    async saveFullConfig(fullConfig) {
        try {
            const response = await fetch('/spotify/widget/update-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    widget_token: this.config.token,
                    config: fullConfig
                })
            });
            return response.ok;
        } catch (error) {
            throw error;
        }
    }

    /**
     * Seçilen temayı backend'e gönderir.
     * @param {string} theme 
     * @returns {Promise<boolean>}
     */
    async _saveThemeConfig(theme) {
        try {
            const response = await fetch('/spotify/widget/update-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    widget_token: this.config.token,
                    theme: theme
                })
            });
            return response.ok;
        } catch (error) {
            throw error;
        }
    }
}

