/**
 * widget_modern.js
 *
 * Modern Spotify widget'ı için özel JavaScript.
 * WidgetCommon modülünü kullanarak UI'ı yönetir ve widget'a özgü davranışları tanımlar.
 *
 * İÇİNDEKİLER:
 * 1. MODÜL BAĞIMLILIK KONTROLÜ
 * =====================================
 * 2. WIDGET'A ÖZEL AYARLAR VE SABİTLER
 * 2.1. Placeholder Resim URL'leri (Ana Kapak ve Arka Plan için)
 * 2.2. Ana Widget Elementi ve Animasyon Sınıfları
 * =====================================
 * 3. DURUM DEĞİŞKENLERİ
 * 3.1. currentTrackProgressInterval
 * 3.2. lastTrackId
 * 3.3. currentFetchTimeoutId
 * =====================================
 * 4. DOM ELEMENT REFERANSLARI
 * 4.1. Albüm Kapağı Elementleri (Ana ve Arka Plan)
 * 4.2. Şarkı Bilgisi Elementleri
 * 4.3. Progress Bar Elementleri
 * 4.4. Hata Mesajı Elementi
 * 4.5. İçerik Alanı Elementi
 * 4.6. Spotify Logo Elementi
 * =====================================
 * 5. TEMEL YARDIMCI FONKSİYONLAR
 * 5.1. clearCurrentFetchTimeout
 * =====================================
 * 6. UI GÜNCELLEME FONKSİYONLARI
 * 6.1. updateWidgetUI (Ana UI güncelleme fonksiyonu)
 * =====================================
 * 7. VERİ YÖNETİMİ
 * 7.1. fetchAndDisplayData (Veri çekme ve UI güncelleme döngüsü)
 * =====================================
 * 8. WIDGET'A ÖZEL ANİMASYON FONKSİYONLARI
 * 8.1. playModernSongChangeAnimation
 * =====================================
 * 9. BAŞLATMA
 * 9.1. initWidget (Widget'ı başlatan ana fonksiyon)
 * 9.2. DOMContentLoaded Olay Dinleyicisi (Implicit via direct call)
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    // 1. MODÜL BAĞIMLILIK KONTROLÜ
    if (typeof WidgetCommon === 'undefined') {
        console.error('Modern Widget: WidgetCommon bulunamadı! spotify_widget_core.js yüklendiğinden emin olun.');
        const body = document.body;
        if (body) {
            const errorDiv = document.createElement('div');
            errorDiv.textContent = 'Widget başlatılamadı: Temel bileşenler eksik.';
            errorDiv.style.cssText = 'color: red; padding: 10px; text-align: center; background: #fff; border: 1px solid red; position: fixed; top: 0; left: 0; width: 100%; z-index: 9999;';
            body.insertBefore(errorDiv, body.firstChild);
        }
        return;
    }

    // 2. WIDGET'A ÖZEL AYARLAR VE SABİTLER
    // 2.1. Placeholder Resim URL'leri
    const PLACEHOLDER_IMAGE_URL = 'https://placehold.co/600x360/1f2937/e5e7eb?text=Beatify'; // Ana kapak için (widget'ın %60 yüksekliği)
    const PLACEHOLDER_BACKGROUND_URL = 'https://placehold.co/600x600/121212/333333?text=BG'; // Tam widget boyutu arka plan için
    const PLACEHOLDER_ERROR_URL = 'https://placehold.co/600x360/cc0000/ffffff?text=Hata';
    const PLACEHOLDER_ERROR_BACKGROUND_URL = 'https://placehold.co/600x600/cc0000/ffffff?text=Hata+BG';

    // 2.2. Ana Widget Elementi ve Animasyon Sınıfları
    const spotifyWidgetElement = document.getElementById('spotifyWidgetModern');
    if (!spotifyWidgetElement) {
        console.error("Modern Widget: Ana widget elementi (#spotifyWidgetModern) DOM'da bulunamadı.");
        return;
    }
    const INTRO_ANIMATION_CLASS = spotifyWidgetElement.dataset.introAnimationClass || 'modern-fade-in';
    const TRANSITION_ANIMATION_CLASS = spotifyWidgetElement.dataset.transitionAnimationClass || 'modern-content-slide';
    const OUTRO_ANIMATION_CLASS = spotifyWidgetElement.dataset.outroAnimationClass || 'modern-fade-out';

    // 3. DURUM DEĞİŞKENLERİ
    let currentTrackProgressInterval = null;
    let lastTrackId = null;
    let currentFetchTimeoutId = null;

    // 4. DOM ELEMENT REFERANSLARI
    // 4.1. Albüm Kapağı Elementleri
    const albumArtElement = document.getElementById('albumArt'); // Ana, üstteki kapak
    const albumArtBackgroundElement = document.getElementById('albumArtBackground'); // Tam ekran, bulanık arka plan

    // 4.2. Şarkı Bilgisi Elementleri
    const trackNameElement = document.getElementById('trackName');
    const artistNameElement = document.getElementById('artistName');

    // 4.3. Progress Bar Elementleri
    const progressBarContainerElement = document.getElementById('progressBarContainer'); // Animating the container
    const progressBarElement = document.getElementById('progressBar'); // Actual bar, not directly animated here but part of container
    const currentTimeElement = document.getElementById('currentTime');
    const totalTimeElement = document.getElementById('totalTime');

    // 4.4. Hata Mesajı Elementi
    const errorMessageElement = document.getElementById('errorMessage');

    // 4.5. İçerik Alanı Elementi
    const widgetContentElement = document.getElementById('widgetContent'); // Şarkı bilgisi ve kontrolleri içeren ana bölüm

    // 4.6. Spotify Logo Elementi // YENİ EKLENDİ
    const spotifyLogoElement = spotifyWidgetElement.querySelector('.widget-spotify-logo');


    // 5. TEMEL YARDIMCI FONKSİYONLAR
    /**
     * 5.1. Mevcut veri çekme zamanlayıcısını temizler.
     */
    function clearCurrentFetchTimeout() {
        if (currentFetchTimeoutId) {
            clearTimeout(currentFetchTimeoutId);
            currentFetchTimeoutId = null;
        }
    }

    // 6. UI GÜNCELLEME FONKSİYONLARI
    /**
     * 6.1. Gelen verilere göre modern widget UI'ını günceller.
     * @param {Object|null} data - API'den gelen şarkı verisi veya null.
     * @param {string|null} [errorMessageText=null] - Harici bir hata mesajı.
     */
    function updateWidgetUI(data, errorMessageText = null) {
        if (!spotifyWidgetElement) return; // Ana element yoksa işlem yapma

        if (errorMessageText) {
            WidgetCommon.showError(errorMessageElement, errorMessageText);
            // Hata durumunda UI'ı sıfırla
            WidgetCommon.updateTextContent(trackNameElement, 'Hata Oluştu', 'Veri alınırken bir sorun oluştu.');
            WidgetCommon.updateTextContent(artistNameElement, '-', '-');
            WidgetCommon.updateImageSource(albumArtElement, PLACEHOLDER_ERROR_URL, PLACEHOLDER_ERROR_URL);
            WidgetCommon.updateImageSource(albumArtBackgroundElement, PLACEHOLDER_ERROR_BACKGROUND_URL, PLACEHOLDER_ERROR_BACKGROUND_URL); // Hata arka planı
            if (trackNameElement) trackNameElement.classList.remove('playing');
            if (currentTrackProgressInterval) clearInterval(currentTrackProgressInterval);
            WidgetCommon.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, 0, 0, false);
            // Logo görünürlüğünü de sıfırlayabiliriz veya olduğu gibi bırakabiliriz.
            if(spotifyLogoElement) spotifyLogoElement.style.opacity = '0.5'; // Örneğin hata durumunda yarı saydam yap
            return;
        }

        if (data && (data.item || data.track_name)) { // Aktif bir şarkı verisi var
            WidgetCommon.hideError(errorMessageElement);
            if(spotifyLogoElement) spotifyLogoElement.style.opacity = '1'; // Veri varsa logoyu tam görünür yap

            const track = data.item || {};
            const trackName = track.name || data.track_name || "Bilinmeyen Şarkı";
            const artists = track.artists || (data.artist_name ? [{ name: data.artist_name }] : []);
            const artistName = artists.map(artist => artist.name).join(', ') || "Bilinmeyen Sanatçı";
            
            let albumImageUrl = PLACEHOLDER_IMAGE_URL;
            let albumImageBackgroundUrl = PLACEHOLDER_BACKGROUND_URL; // Arka plan için

            if (track.album?.images?.length > 0) {
                albumImageUrl = track.album.images.find(img => img.height >= 300 && img.height <= 700)?.url || track.album.images[0].url;
                albumImageBackgroundUrl = track.album.images[0].url; 
            } else if (data.album_image_url) {
                albumImageUrl = data.album_image_url;
                albumImageBackgroundUrl = data.album_image_url;
            }

            WidgetCommon.updateTextContent(trackNameElement, trackName);
            WidgetCommon.updateTextContent(artistNameElement, artistName);
            WidgetCommon.updateImageSource(albumArtElement, albumImageUrl, PLACEHOLDER_ERROR_URL);
            WidgetCommon.updateImageSource(albumArtBackgroundElement, albumImageBackgroundUrl, PLACEHOLDER_BACKGROUND_URL); 

            const isPlaying = data.is_playing ?? false;
            const progressMs = data.progress_ms ?? 0;
            const durationMs = track.duration_ms || data.duration_ms || 0;

            if (trackNameElement) {
                trackNameElement.classList.toggle('playing', isPlaying);
            }

            if (currentTrackProgressInterval) clearInterval(currentTrackProgressInterval);
            if (durationMs > 0) { 
                currentTrackProgressInterval = WidgetCommon.updateProgressBar(
                    progressBarElement, currentTimeElement, totalTimeElement,
                    progressMs, durationMs, isPlaying,
                    () => { 
                        clearCurrentFetchTimeout(); 
                        currentFetchTimeoutId = setTimeout(fetchAndDisplayData, 1500); 
                    }
                );
            } else { 
                 WidgetCommon.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, 0, 0, false);
            }

        } else { // Çalınan bir şey yok veya veri eksik/hatalı
            if(spotifyLogoElement) spotifyLogoElement.style.opacity = '1'; // Logo genellikle görünür kalmalı
            WidgetCommon.updateTextContent(trackNameElement, 'Bir şey çalmıyor', 'Spotify\'da aktif bir içerik yok.');
            WidgetCommon.updateTextContent(artistNameElement, '-', '-');
            WidgetCommon.updateImageSource(albumArtElement, PLACEHOLDER_IMAGE_URL, PLACEHOLDER_IMAGE_URL);
            WidgetCommon.updateImageSource(albumArtBackgroundElement, PLACEHOLDER_BACKGROUND_URL, PLACEHOLDER_BACKGROUND_URL); 

            if (trackNameElement) trackNameElement.classList.remove('playing');
            if (currentTrackProgressInterval) clearInterval(currentTrackProgressInterval);
            WidgetCommon.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, 0, 0, false);
            
            if (data && data.error) {
                 WidgetCommon.showError(errorMessageElement, data.error);
            } else if (!data?.item && !data?.track_name && !data?.error && !errorMessageText) {
                 WidgetCommon.showError(errorMessageElement, 'Şu an aktif bir yayın yok veya veri alınamadı.');
            }
        }
    }

    // 8. WIDGET'A ÖZEL ANİMASYON FONKSİYONLARI
    const ANIMATION_DEFS = {
        albumArt:    { out: 'album-art-slide-out',   in: 'album-art-slide-in',     duration: 600, delay: 0,   element: null, classesToRemove: ['album-art-slide-out', 'album-art-slide-in', 'element-fade-out', 'element-fade-in'] },
        albumArtBg:  { out: 'album-art-bg-fade-out', in: 'album-art-bg-fade-in',   duration: 600, delay: 0,   element: null, classesToRemove: ['album-art-bg-fade-out', 'album-art-bg-fade-in', 'element-fade-out', 'element-fade-in'] },
        trackName:   { out: 'text-slide-out-left',   in: 'text-slide-in-from-right', duration: 500, delay: 50,  element: null, classesToRemove: ['text-slide-out-left', 'text-slide-in-from-right', 'element-fade-out', 'element-fade-in'] },
        artistName:  { out: 'text-slide-out-left',   in: 'text-slide-in-from-right', duration: 500, delay: 150, element: null, classesToRemove: ['text-slide-out-left', 'text-slide-in-from-right', 'element-fade-out', 'element-fade-in'] },
        spotifyLogo: { out: 'logo-slide-out-left',   in: 'logo-slide-in-from-right', duration: 500, delay: 200, element: null, classesToRemove: ['logo-slide-out-left', 'logo-slide-in-from-right', 'element-fade-out', 'element-fade-in'] },
        progressBar: { out: 'element-fade-out',      in: 'element-fade-in',        duration: 300, delay: 250, element: null, classesToRemove: ['element-fade-out', 'element-fade-in'] },
        currentTime: { out: 'element-fade-out',      in: 'element-fade-in',        duration: 300, delay: 300, element: null, classesToRemove: ['element-fade-out', 'element-fade-in'] },
        totalTime:   { out: 'element-fade-out',      in: 'element-fade-in',        duration: 300, delay: 300, element: null, classesToRemove: ['element-fade-out', 'element-fade-in'] }
    };

    /**
     * Helper function to apply an animation and return a Promise that resolves when the animation is presumed complete.
     * @param {Object} config - The animation configuration object from ANIMATION_DEFS.
     * @param {'in' | 'out'} type - The type of animation ('in' or 'out').
     * @returns {Promise<void>}
     */
    async function animateElement(config, type) {
        if (!config.element) {
            return Promise.resolve();
        }

        const animationClass = config[type];
        const duration = config.duration || 500;
        const delay = config.delay || 0;

        return new Promise(resolve => {
            setTimeout(() => {
                if (config.classesToRemove && Array.isArray(config.classesToRemove)) {
                    WidgetCommon.triggerAnimation(config.element, animationClass, config.classesToRemove);
                } else {
                    const otherType = type === 'in' ? 'out' : 'in';
                    WidgetCommon.triggerAnimation(config.element, animationClass, [config[otherType], config.in, config.out, 'element-fade-in', 'element-fade-out']);
                }
                setTimeout(resolve, duration);
            }, delay);
        });
    }

    /**
     * 8.1. Orchestrates the 'Masked Slide & Reveal' animation for song changes.
     * Elements slide/fade out, UI updates, then new elements slide/fade in.
     * @param {Object} newData - The new song data from the API.
     * @returns {Promise<void>}
     */
    async function playModernSongChangeAnimation(newData) {
        if (!widgetContentElement) {
            updateWidgetUI(newData);
            return Promise.resolve();
        }

        const elementsToAnimate = [
            ANIMATION_DEFS.albumArt,
            ANIMATION_DEFS.albumArtBg,
            ANIMATION_DEFS.trackName,
            ANIMATION_DEFS.artistName,
            ANIMATION_DEFS.spotifyLogo,
            ANIMATION_DEFS.progressBar,
            ANIMATION_DEFS.currentTime,
            ANIMATION_DEFS.totalTime
        ].filter(def => def.element);

        const outAnimations = elementsToAnimate.map(config => animateElement(config, 'out'));
        await Promise.all(outAnimations);

        updateWidgetUI(newData);

        const inAnimations = elementsToAnimate.map(config => animateElement(config, 'in'));
        await Promise.all(inAnimations);
    }

    // 7. VERİ YÖNETİMİ
    /**
     * 7.1. Veriyi backend'den çeker ve UI'ı günceller. Periyodik olarak kendini çağırır.
     */
    async function fetchAndDisplayData() {
        clearCurrentFetchTimeout();

        if (!WIDGET_TOKEN_FROM_HTML || !DATA_ENDPOINT_TEMPLATE) {
            updateWidgetUI(null, 'Widget yapılandırma hatası: Token veya endpoint eksik.');
            return;
        }
        const endpoint = DATA_ENDPOINT_TEMPLATE.replace('{widget_token}', WIDGET_TOKEN_FROM_HTML);

        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({})); // Try to parse error, default to empty if fail
                const errorMessage = errorData.error || `Sunucu hatası: ${response.status}`;
                updateWidgetUI(null, errorMessage);
                currentFetchTimeoutId = setTimeout(fetchAndDisplayData, WidgetCommon.determinePollInterval(null, true));
                return;
            }

            const data = await response.json();

            if (data && (data.item || data.track_name)) {
                const currentTrackId = data.item?.id || data.track_id || (data.track_name + (data.item?.artists?.[0]?.name || data.artist_name));

                if (lastTrackId === null) { // Initial load
                    updateWidgetUI(data);
                    lastTrackId = currentTrackId;
                    if (spotifyWidgetElement && INTRO_ANIMATION_CLASS) {
                        WidgetCommon.triggerAnimation(spotifyWidgetElement, INTRO_ANIMATION_CLASS);
                    }
                } else if (lastTrackId !== currentTrackId) { // Song has changed
                    await playModernSongChangeAnimation(data);
                    lastTrackId = currentTrackId;
                } else { // Song is the same
                    updateWidgetUI(data);
                }
            } else { // No song playing or error in data structure
                updateWidgetUI(data); // updateWidgetUI handles null/error data
                if (!data?.item && !data?.track_name && !data?.error) { // If truly empty and not an API error response
                    lastTrackId = null; // Reset lastTrackId if nothing is playing
                }
            }
            currentFetchTimeoutId = setTimeout(fetchAndDisplayData, WidgetCommon.determinePollInterval(data));

        } catch (error) {
            updateWidgetUI(null, `İstemci tarafı hata: ${error.message}`);
            currentFetchTimeoutId = setTimeout(fetchAndDisplayData, WidgetCommon.determinePollInterval(null, true));
        }
    }

    // 9. BAŞLATMA
    /**
     * 9.1. Widget'ı başlatan ana fonksiyon.
     */
    function initWidget() {
        ANIMATION_DEFS.albumArt.element = albumArtElement;
        ANIMATION_DEFS.albumArtBg.element = albumArtBackgroundElement;
        ANIMATION_DEFS.trackName.element = trackNameElement;
        ANIMATION_DEFS.artistName.element = artistNameElement;
        ANIMATION_DEFS.spotifyLogo.element = spotifyLogoElement;
        ANIMATION_DEFS.progressBar.element = progressBarContainerElement; // Animating the container
        ANIMATION_DEFS.currentTime.element = currentTimeElement;
        ANIMATION_DEFS.totalTime.element = totalTimeElement;

        if (!albumArtElement || !albumArtBackgroundElement || !trackNameElement || !artistNameElement || !widgetContentElement || !spotifyLogoElement || !progressBarContainerElement || !currentTimeElement || !totalTimeElement) {
            // console.warn("Modern Widget: Animasyonlar için gerekli DOM elementlerinden bazıları eksik. Animasyonlar beklendiği gibi çalışmayabilir.");
        }
        
        fetchAndDisplayData();
    }

    // 9.2. DOMContentLoaded Olay Dinleyicisi -> Call initWidget
    initWidget();
});
