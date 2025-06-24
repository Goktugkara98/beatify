/**
 * @file AnimationService.js
 * @description Widget için CSS animasyonlarını yönetir.
 */
class AnimationService {
    constructor(widgetElement) {
        this.widgetElement = widgetElement;
    }

    playIntro() {
        this.widgetElement.classList.remove('widget-inactive');
        // Gelecekte daha karmaşık intro animasyonları için CSS sınıfları eklenebilir.
    }

    playOutro() {
        this.widgetElement.classList.add('widget-inactive');
        // Gelecekte daha karmaşık outro animasyonları için CSS sınıfları eklenebilir.
    }

    /**
     * Şarkı geçişi animasyonunu oynatır.
     * @param {object} detail - Hangi setin aktif, hangisinin pasif olduğunu içerir.
     * @returns {Promise<void>} Animasyon bittiğinde çözümlenen bir Promise döner.
     */
    playTransition({ activeSet, passiveSet }) {
        return new Promise(resolve => {
            const activeContainer = this.widgetElement.querySelector(`.WidgetContainer_${activeSet}`);
            const passiveContainer = this.widgetElement.querySelector(`.WidgetContainer_${passiveSet}`);

            if (!activeContainer || !passiveContainer) return resolve();

            // Pasif seti görünür yap ve animasyona hazırla
            passiveContainer.classList.remove('passive');
            
            // Animasyon sınıflarını ekle
            activeContainer.classList.add('transition-out');
            passiveContainer.classList.add('transition-in');

            // Animasyon bittiğinde olay dinleyicisi
            const onAnimationEnd = (event) => {
                // Sadece passiveContainer'daki animasyon bittiğinde işlem yap
                if (event.target === passiveContainer) {
                    // Temizlik yap
                    activeContainer.classList.remove('transition-out');
                    activeContainer.classList.add('passive');
                    passiveContainer.classList.remove('transition-in');
                    
                    passiveContainer.removeEventListener('animationend', onAnimationEnd);
                    resolve(); // Promise'i çöz
                }
            };
            
            passiveContainer.addEventListener('animationend', onAnimationEnd);
        });
    }
}
