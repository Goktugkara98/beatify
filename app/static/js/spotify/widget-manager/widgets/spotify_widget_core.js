/**
 * spotify_widget_core.js
 *
 * Tüm Spotify widget'ları için ortak temel işlevleri içeren modüler yapı.
 *
 * İÇİNDEKİLER:
 * 1. GENEL AYARLAR VE YARDIMCILAR
 *      1.1. Global Değişkenler (Gerekirse)
 *      1.2. Temel Yardımcı Fonksiyonlar
 *          1.2.1. msToTimeFormat
 *          1.2.2. updateTextContent
 *          1.2.3. updateImageSource
 *          1.2.4. showError
 *          1.2.5. hideError
 * 2. BACKEND İLETİŞİMİ
 *      2.1. fetchWidgetData
 * 3. ANİMASYON YÖNETİMİ
 *      3.1. Genel Animasyon Tetikleyicileri
 *          3.1.1. triggerAnimation (Yeni genel fonksiyon)
 *      3.2. Özel Durum Animasyonları
 *          3.2.1. playIntroAnimation (triggerAnimation kullanacak şekilde güncellenebilir)
 *          3.2.2. playSongTransitionAnimation (triggerAnimation kullanacak şekilde güncellenebilir)
 *          3.2.3. playOutroAnimation
 * 4. PROGRESS BAR YÖNETİMİ
 *      4.1. updateProgressBar
 * 5. OLAY DİNLEYİCİLERİ (Genel)
 *      5.1. Sayfa Kapanış Olayı (playOutroAnimation için)
 * 6. MODÜL DIŞA AKTARIMI
 */

const WidgetCommon = (() => {
    'use strict';

    // 1. GENEL AYARLAR VE YARDIMCILAR
    // 1.1. Global Değişkenler (Gerekirse)
    // Örnek: const DEFAULT_ANIMATION_DURATION = 500;

    // 1.2. Temel Yardımcı Fonksiyonlar

    /**
     * 1.2.1. Milisaniyeyi "dakika:saniye" formatına çevirir
     * @param {number} ms - Milisaniye cinsinden süre
     * @returns {string} "dakika:saniye" formatında string
     */
    function msToTimeFormat(ms) {
        if (isNaN(ms) || ms === null || ms < 0) return '0:00';
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }

    /**
     * 1.2.2. Bir DOM elementinin metin içeriğini ve başlığını günceller
     * @param {HTMLElement} element - Güncellenecek DOM elementi
     * @param {string} text - Yeni metin içeriği
     * @param {string} [title] - Opsiyonel title attribute değeri
     */
    function updateTextContent(element, text, title) {
        if (element) {
            element.textContent = text;
            if (title) {
                element.title = title;
            }
        }
    }

    /**
     * 1.2.3. Bir resim elementinin src'sini günceller ve yüklenme/hata durumlarını yönetir
     * @param {HTMLImageElement} imgElement - Güncellenecek resim elementi
     * @param {string} newSrc - Yeni resim URL'si
     * @param {string} placeholderSrc - Hata durumunda gösterilecek placeholder URL'si
     * @param {function} [onLoadCallback] - Resim başarıyla yüklendiğinde çağrılacak fonksiyon
     */
    function updateImageSource(imgElement, newSrc, placeholderSrc, onLoadCallback) {
        if (imgElement) {
            if (imgElement.src !== newSrc || !imgElement.dataset.loadedOnce) {
                imgElement.style.opacity = '0';
                const tempImage = new Image();
                tempImage.onload = () => {
                    imgElement.src = newSrc;
                    imgElement.style.opacity = '1';
                    imgElement.dataset.loadedOnce = 'true';
                    if (typeof onLoadCallback === 'function') onLoadCallback(true, newSrc);
                };
                tempImage.onerror = () => {
                    console.warn(`Core: Resim yüklenemedi: ${newSrc}. Placeholder kullanılıyor.`);
                    imgElement.src = placeholderSrc;
                    imgElement.style.opacity = '1';
                    imgElement.dataset.loadedOnce = 'true';
                    if (typeof onLoadCallback === 'function') onLoadCallback(false, placeholderSrc);
                };
                tempImage.src = newSrc;
            } else if (imgElement.style.opacity === '0') {
                 imgElement.style.opacity = '1';
            }
        }
    }

    /**
     * 1.2.4. Kullanıcıya bir hata mesajı gösterir
     * @param {HTMLElement} errorElement - Hata mesajının gösterileceği DOM elementi
     * @param {string} message - Gösterilecek hata mesajı
     */
    function showError(errorElement, message) {
        if (errorElement) {
            updateTextContent(errorElement, message);
            errorElement.classList.add('visible');
            errorElement.classList.remove('hidden'); // TailwindCSS uyumluluğu için
        }
    }

    /**
     * 1.2.5. Hata mesajını gizler
     * @param {HTMLElement} errorElement - Hata mesajının gizleneceği DOM elementi
     */
    function hideError(errorElement) {
        if (errorElement) {
            errorElement.classList.remove('visible');
            errorElement.classList.add('hidden'); // TailwindCSS uyumluluğu için
        }
    }

    /**
     * 1.2.6. Determines the appropriate polling interval based on the current playback state.
     * @param {Object|null} data - The current track data from the API.
     * @param {boolean} [isError=false] - Whether the last fetch resulted in an error.
     * @returns {number} The polling interval in milliseconds.
     */
    function determinePollInterval(data, isError = false) {
        const MIN_POLL_INTERVAL = 1500; // Minimum 1.5 seconds
        const DEFAULT_POLL_INTERVAL = 7000; // Default 7 seconds (e.g., for live streams or when duration is unknown)
        const NOT_PLAYING_POLL_INTERVAL = 15000; // When not playing, 15 seconds
        const ERROR_POLL_INTERVAL = 30000; // On error, 30 seconds

        if (isError) {
            return ERROR_POLL_INTERVAL;
        }

        if (!data || (!data.item && !data.track_name)) { // No data or no track item
            return NOT_PLAYING_POLL_INTERVAL;
        }

        // Check if is_playing exists and is explicitly false. If undefined, assume not playing for safety.
        if (typeof data.is_playing === 'boolean' && data.is_playing === false) {
            return NOT_PLAYING_POLL_INTERVAL;
        }
        // If data.is_playing is not a boolean (e.g. undefined), also treat as not playing for polling interval.
        if (typeof data.is_playing !== 'boolean') {
             return NOT_PLAYING_POLL_INTERVAL;
        }

        // If playing:
        if (data.item && typeof data.item.duration_ms === 'number' && typeof data.progress_ms === 'number') {
            const remainingTimeMs = data.item.duration_ms - data.progress_ms;
            // Poll a bit after the song is expected to end.
            // Add a small buffer (e.g., 1.5s) to account for API lag or slight timing discrepancies.
            // Ensure it's not less than the minimum.
            return Math.max(MIN_POLL_INTERVAL, remainingTimeMs + 1500);
        }

        return DEFAULT_POLL_INTERVAL; // Default for playing tracks with unknown duration (e.g., podcasts, live)
    }

    // 2. BACKEND İLETİŞİMİ
    /**
     * 2.1. Widget verilerini backend'den çeker
     * @param {string} token - Widget token
     * @param {string} endpointTemplate - API endpoint şablonu (örn: '/api/data/{TOKEN}')
     * @returns {Promise<object|null>} API'den gelen veri veya hata durumunda { error: "mesaj" }
     */
    async function fetchWidgetData(token, endpointTemplate) {
        if (!token) {
            console.error('Core: Veri çekmek için token sağlanmadı.');
            return { error: 'Token eksik.' };
        }
        if (!endpointTemplate) {
            console.error('Core: Veri çekmek için endpoint şablonu sağlanmadı.');
            return { error: 'Endpoint şablonu eksik.'};
        }

        const apiUrl = endpointTemplate.replace('{TOKEN}', token);
        console.log(`Core: Veri çekiliyor: ${apiUrl}`);

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    errorData = { error: `HTTP ${response.status} - ${response.statusText}` };
                }
                console.error('Core: Veri çekme hatası:', response.status, errorData);
                return { error: errorData.error || `Sunucudan ${response.status} koduyla yanıt alındı.` };
            }
            return await response.json();
        } catch (error) {
            console.error('Core: fetchWidgetData içinde kritik hata:', error);
            return { error: 'Ağ hatası veya sunucuya ulaşılamıyor.' };
        }
    }

    // 3. ANİMASYON YÖNETİMİ
    // 3.1. Genel Animasyon Tetikleyicileri
    /**
     * 3.1.1. Bir element üzerinde belirtilen CSS animasyonunu tetikler.
     * @param {HTMLElement} element - Animasyon uygulanacak HTML elementi.
     * @param {string} animationClass - Uygulanacak CSS animasyon sınıfı.
     * @param {Array<string>} [classesToRemove=[]] - Animasyon öncesi kaldırılacak sınıflar.
     */
    function triggerAnimation(element, animationClass, classesToRemove = []) {
        if (!element || !animationClass) {
            console.warn('Core: Animasyon için element veya animasyon sınıfı eksik.');
            return;
        }
        // Önce mevcut olası animasyon sınıflarını temizle
        classesToRemove.forEach(cls => element.classList.remove(cls));
        element.classList.remove(animationClass); // Eğer aynı animasyon tekrar tetikleniyorsa

        // Reflow tetikleyerek animasyonun baştan başlamasını sağla
        void element.offsetWidth;

        // Yeni animasyonu uygula
        element.classList.add(animationClass);
    }

    // 3.2. Özel Durum Animasyonları
    /**
     * 3.2.1. Sayfa açılışında animasyon tetikler.
     * Widget'a özel JS dosyasında tanımlanan animasyon sınıfını kullanır.
     * @param {HTMLElement} element - Animasyon uygulanacak element.
     * @param {string} specificIntroAnimationClass - Widget'a özel giriş animasyon sınıfı.
     */
    function playIntroAnimation(element, specificIntroAnimationClass) {
        // Örnek genel animasyon sınıfları (widget'a özel olanlarla çakışmaması için)
        const commonAnimationClasses = ['core-fade-in-up', 'core-fade-in', 'core-slide-in', 'core-fade-out'];
        triggerAnimation(element, specificIntroAnimationClass, commonAnimationClasses);
    }

    /**
     * 3.2.2. Şarkı değişiminde animasyon tetikler.
     * Widget'a özel JS dosyasında tanımlanan animasyon sınıfını kullanır.
     * @param {HTMLElement} element - Animasyon uygulanacak element.
     * @param {string} specificTransitionAnimationClass - Widget'a özel geçiş animasyon sınıfı.
     * @param {string} currentTrackId - Mevcut şarkı ID'si (animasyonun gerekliliğini kontrol etmek için).
     * @param {string} lastTrackId - Son çalınan şarkı ID'si (animasyonun gerekliliğini kontrol etmek için).
     */
    function playSongTransitionAnimation(element, specificTransitionAnimationClass, currentTrackId, lastTrackId) {
        if (currentTrackId && currentTrackId !== lastTrackId) {
            const commonAnimationClasses = ['core-fade-in-up', 'core-fade-in', 'core-slide-in', 'core-fade-out'];
            triggerAnimation(element, specificTransitionAnimationClass, commonAnimationClasses);
        }
    }

    /**
     * 3.2.3. Sayfa kapatılırken animasyon tetikler.
     * Widget'a özel JS dosyasında tanımlanan animasyon sınıfını kullanır veya ortak bir sınıf kullanır.
     * @param {HTMLElement} element - Animasyon uygulanacak element.
     * @param {string} specificOutroAnimationClass - Widget'a özel çıkış animasyon sınıfı (veya ortak 'core-fade-out').
     * @param {number} duration - Animasyon süresi (ms).
     * @returns {Promise<void>} Animasyon tamamlandığında çözülen Promise.
     */
    function playOutroAnimation(element, specificOutroAnimationClass = 'core-fade-out', duration = 500) {
        if (element) {
            triggerAnimation(element, specificOutroAnimationClass);
            return new Promise(resolve => {
                setTimeout(resolve, duration);
            });
        }
        return Promise.resolve();
    }

    // 4. PROGRESS BAR YÖNETİMİ
    /**
     * 4.1. Progress bar'ı günceller.
     * @param {HTMLElement} progressBarElement - Progress bar elementi.
     * @param {HTMLElement} currentTimeElement - Mevcut süre elementi.
     * @param {HTMLElement} totalTimeElement - Toplam süre elementi.
     * @param {number} progressMs - Mevcut ilerleme (ms).
     * @param {number} durationMs - Toplam süre (ms).
     * @param {boolean} isPlaying - Çalma durumu.
     * @param {function} [onComplete] - Şarkı bittiğinde çağrılacak fonksiyon.
     * @returns {number|null} Interval ID veya null.
     */
    function updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, progressMs, durationMs, isPlaying, onComplete) {
        let intervalId = null;

        if (!progressBarElement || !currentTimeElement || !totalTimeElement) {
            console.warn("Core: Progress bar elementleri eksik.");
            return null;
        }
        
        if (durationMs <= 0 || isNaN(durationMs)) {
            progressBarElement.style.width = '0%';
            updateTextContent(currentTimeElement, msToTimeFormat(0));
            updateTextContent(totalTimeElement, msToTimeFormat(0));
            return null;
        }

        let currentProgress = progressMs;

        const updateDOM = () => {
            const percentage = Math.min(100, (currentProgress / durationMs) * 100);
            progressBarElement.style.width = `${percentage}%`;
            updateTextContent(currentTimeElement, msToTimeFormat(currentProgress));
        };

        updateTextContent(totalTimeElement, msToTimeFormat(durationMs));
        updateDOM();

        if (isPlaying) {
            intervalId = setInterval(() => {
                currentProgress += 1000;
                if (currentProgress >= durationMs) {
                    currentProgress = durationMs;
                    updateDOM();
                    clearInterval(intervalId);
                    intervalId = null; // Interval temizlendiğini belirt
                    if (typeof onComplete === 'function') {
                        onComplete();
                    }
                } else {
                    updateDOM();
                }
            }, 1000);
        }
        return intervalId;
    }

    // 5. OLAY DİNLEYİCİLERİ (Genel)
    /**
     * 5.1. Sayfa kapatılırken animasyonlu kapanış için olay dinleyicisi.
     * Bu fonksiyon, widget'ın ana JS dosyasında `initPageCloseAnimation` gibi bir fonksiyonla çağrılmalıdır.
     * @param {HTMLElement} animatedElement - Kapanış animasyonu uygulanacak ana widget elementi.
     * @param {string} outroAnimationClass - Kullanılacak çıkış animasyon sınıfı.
     * @param {number} animationDuration - Animasyon süresi.
     */
    function setupPageUnloadAnimation(animatedElement, outroAnimationClass, animationDuration) {
        window.addEventListener('beforeunload', (event) => {
            // Bazı tarayıcılar senkronize olmayan işlemlere izin vermeyebilir,
            // bu yüzden animasyonun tamamlanmasını beklemek her zaman mümkün olmayabilir.
            // En iyi yaklaşım, kısa bir animasyon kullanmaktır.
            if (animatedElement && !animatedElement.classList.contains(outroAnimationClass)) {
                 playOutroAnimation(animatedElement, outroAnimationClass, animationDuration);
                // Tarayıcıya çıkışı biraz geciktirmesi için çok kısa bir bloklama (her zaman çalışmayabilir)
                // const start = Date.now();
                // while (Date.now() - start < animationDuration - 50) { /* bekle */ }
            }
            // event.preventDefault(); // Eğer kullanıcıya bir onay göstermek isterseniz (standart dışı olabilir)
            // event.returnValue = ''; // Chrome için gerekli
        });
    }


    // 6. MODÜL DIŞA AKTARIMI
    return {
        // 1. Genel Ayarlar ve Yardımcılar
        msToTimeFormat,
        updateTextContent,
        updateImageSource,
        showError,
        hideError,
        // 2. Backend İletişimi
        fetchWidgetData,
        // 3. Animasyon Yönetimi
        triggerAnimation, // Genel animasyon tetikleyici
        playIntroAnimation,
        playSongTransitionAnimation,
        playOutroAnimation,
        // 4. Progress Bar Yönetimi
        updateProgressBar,
        // 1.2.6. determinePollInterval (Yeni eklendi)
        determinePollInterval,

        // 5. Olay Dinleyicileri
        setupPageUnloadAnimation
    };
})();

// Global scope'a ekle (veya ES6 modül sistemini kullanıyorsanız export edin)
window.WidgetCommon = WidgetCommon;

// Sayfa yüklendiğinde genel bir giriş animasyonu için örnek bir tetikleyici
// Bu, widget'ın kendi JS dosyasında daha spesifik olarak yönetilmelidir.
/*
document.addEventListener('DOMContentLoaded', () => {
    const widgetContainer = document.querySelector('.widget-container'); // Ana widget container'ı seçin
    if (widgetContainer && WidgetCommon) {
        // Widget'a özel JS dosyasının bu animasyon sınıfını sağlaması beklenir.
        // Örneğin: widgetContainer.dataset.introAnimationClass = 'widget-specific-fade-in';
        const introAnimClass = widgetContainer.dataset.introAnimationClass || 'core-fade-in-up'; // Varsayılan
        WidgetCommon.playIntroAnimation(widgetContainer, introAnimClass);
    }
});
*/
