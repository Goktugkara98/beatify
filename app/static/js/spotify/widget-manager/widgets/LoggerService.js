// DOSYA ADI: LoggerService.js
// AÇIKLAMA: Gelişmiş, kategorize edilmiş ve renklendirilmiş konsol logları üretmek için merkezi servis.

class LoggerService {
    /**
     * Log mesajları için stil tanımlamaları.
     * Bu stiller, logların konsolda daha okunaklı ve ayırt edilebilir olmasını sağlar.
     */
    static STYLES = {
        group: 'color: #FFFFFF; background-color: #007bff; font-weight: bold; padding: 3px 8px; border-radius: 4px;',
        subgroup: 'color: #007bff; font-weight: bold;',
        info: 'color: #28a745; font-style: italic;',
        warn: 'color: #ffc107;',
        error: 'color: #dc3545; font-weight: bold;',
        data: 'color: #6c757d; font-style: italic; padding-left: 10px;',
        action: 'color: #17a2b8; font-weight:bold;'
    };

    /**
     * Bir ana eylemi veya mantıksal birimi temsil eden yeni bir log grubu başlatır.
     * Örn: "ŞARKI GEÇİŞİ (Transition)"
     * @param {string} title - Grubun başlığı.
     */
    group(title) {
        console.group(`%c${title}`, LoggerService.STYLES.group);
    }

    /**
     * Bir fonksiyon veya alt işlemi temsil eden, varsayılan olarak kapalı bir alt grup başlatır.
     * @param {string} title - Alt grubun başlığı.
     */
    subgroup(title) {
        console.groupCollapsed(`%c▶ ${title}`, LoggerService.STYLES.subgroup);
    }

    /**
     * Bilgilendirici bir mesaj loglar.
     * @param {string} message - Log mesajı.
     * @param {...any} args - Mesaja eklenecek diğer değişkenler.
     */
    info(message, ...args) {
        console.info(`%cⓘ ${message}`, LoggerService.STYLES.info, ...args);
    }
    
    /**
     * Bir eylemi veya adımı loglar.
     * @param {string} message - Log mesajı.
     * @param {...any} args - Mesaja eklenecek diğer değişkenler.
     */
    action(message, ...args) {
        console.log(`%c↳ ${message}`, LoggerService.STYLES.action, ...args);
    }

    /**
     * Bir uyarı mesajı loglar.
     * @param {string} message - Uyarı mesajı.
     * @param {...any} args - Mesaja eklenecek diğer değişkenler.
     */
    warn(message, ...args) {
        console.warn(`%c⚠️ ${message}`, LoggerService.STYLES.warn, ...args);
    }

    /**
     * Bir hata mesajı loglar.
     * @param {string} message - Hata mesajı.
     * @param {...any} args - Mesaja eklenecek diğer değişkenler.
     */
    error(message, ...args) {
        console.error(`%c❌ ${message}`, LoggerService.STYLES.error, ...args);
    }

    /**
     * Bir veri nesnesini (object, array vb.) kapalı bir grup içinde loglar.
     * Bu, konsolun şişmesini engeller ve veriye sadece tıklandığında bakma imkanı sunar.
     * @param {string} title - Verinin başlığı (örn: "Gelen Spotify Verisi").
     * @param {object} dataObject - Loglanacak veri.
     */
    data(title, dataObject) {
        console.groupCollapsed(`%c${title}`, LoggerService.STYLES.data);
        console.log(dataObject);
        console.groupEnd();
    }

    /**
     * Mevcut en son başlatılan grubu kapatır.
     * `group` veya `subgroup` ile açılan her grup için çağrılmalıdır.
     */
    groupEnd() {
        console.groupEnd();
    }
}
