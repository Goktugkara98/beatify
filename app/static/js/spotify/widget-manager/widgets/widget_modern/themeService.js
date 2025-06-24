/**
 * @file ThemeService.js
 * @description Tema konfigürasyonunu, doğrudan HTML'e gömülmüş olan
 * global `window.themeConfig` değişkeninden yükler ve yönetir.
 */
class ThemeService {
    constructor() {
        this.themeData = null;
        console.log('[ThemeService] Servis oluşturuldu.');
    }

    /**
     * Tema verisini global `window.themeConfig` değişkeninden senkronize eder.
     * Artık fetch olmadığı için bu işlem çok hızlıdır ama yapısal tutarlılık
     * için `async` olarak bırakılmıştır.
     * @returns {Promise<boolean>} Yükleme başarılı olursa true döner.
     */
    async load() {
        // Artık fetch yok! Doğrudan global değişkenden okuyoruz.
        if (window.themeConfig) {
            this.themeData = window.themeConfig;
            console.log('[ThemeService] Tema, HTML içerisinden başarıyla yüklendi:', this.themeData);
            return true;
        } else {
            console.error('[ThemeService] Kritik Hata: `window.themeConfig` değişkeni bulunamadı. Veri HTML\'e doğru şekilde gömülmüş mü?');
            this.themeData = null;
            return false;
        }
    }

    /**
     * Belirli bir bileşenin animasyon verisini döner.
     * (Bu metodun içi aynı kaldı, çünkü sadece yüklenen veriyi okuyor)
     * @param {string} componentName - Bileşen adı (örn: 'TrackName', 'Cover').
     * @param {'a' | 'b'} set - Hangi set için veri istendiği.
     * @returns {object | null} İlgili bileşenin set verisini döner.
     */
    getComponentSetData(componentName, set) {
        if (!this.themeData) return null;
        const component = this.themeData.components[componentName];
        if (!component) return null;
        
        return component[`set_${set}`];
    }
}