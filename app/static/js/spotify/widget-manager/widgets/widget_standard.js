/**
 * widget_standard.js
 *
 * Standard Spotify widget'ı için özel JavaScript.
 * WidgetCommon modülünü kullanarak UI'ı yönetir ve widget'a özgü davranışları tanımlar.
 *
 * İÇİNDEKİLER:
 * 1. MODÜL BAĞIMLILIK KONTROLÜ
 * =====================================
 * 2. WIDGET'A ÖZEL AYARLAR VE SABİTLER
 *      2.1. Placeholder Resim URL'leri
 *      2.2. Ana Widget Elementi ve Animasyon Sınıfları (HTML data-* attributes ile senkronize)
 * =====================================
 * 3. DURUM DEĞİŞKENLERİ (State Variables)
 *      3.1. currentTrackProgressInterval
 *      3.2. lastTrackId
 *      3.3. currentFetchTimeoutId
 * =====================================
 * 4. DOM ELEMENT REFERANSLARI
 *      4.1. Albüm Kapağı Elementleri (Ana ve Arka Plan)
 *      4.2. Şarkı Bilgisi Elementleri
 *      4.3. Progress Bar Elementleri
 *      4.4. Hata Mesajı Elementi
 *      4.5. İçerik Alanı Elementi (Animasyonlar için)
 *      4.6. Spotify Logo Elementi (Animasyon için)
 * =====================================
 * 5. TEMEL YARDIMCI FONKSİYONLAR
 *      5.1. clearCurrentFetchTimeout
 * =====================================
 * 6. UI GÜNCELLEME FONKSİYONLARI
 *      6.1. updateWidgetUI (Ana UI güncelleme fonksiyonu)
 * =====================================
 * 7. VERİ YÖNETİMİ (Data Management)
 *      7.1. fetchAndDisplayData (Veri çekme ve UI güncelleme döngüsü)
 * =====================================
 * 8. WIDGET'A ÖZEL ANİMASYON FONKSİYONLARI
 *      8.1. playStandardSongChangeAnimation
 * =====================================
 * 9. BAŞLATMA (Initialization)
 *      9.1. initWidget (Widget'ı başlatan ana fonksiyon)
 *      9.2. DOMContentLoaded Olay Dinleyicisi
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    // 1. MODÜL BAĞIMLILIK KONTROLÜ
    if (typeof WidgetCommon === 'undefined') {
        console.error('Standard Widget: WidgetCommon bulunamadı! spotify_widget_core.js yüklendiğinden emin olun.');
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
    const PLACEHOLDER_IMAGE_URL = 'https://placehold.co/250x250/374151/e5e7eb?text=♪'; // Standard widget için ana kapak boyutu
    const PLACEHOLDER_BACKGROUND_URL = 'https://placehold.co/700x300/1f2937/e5e7eb?text=Beatify'; // Arka plan için
    const PLACEHOLDER_ERROR_URL = 'https://placehold.co/250x250/cc0000/ffffff?text=Hata';

    // 2.2. Ana Widget Elementi ve Animasyon Sınıfları
    const spotifyWidgetElement = document.getElementById('spotifyWidgetStandard');
    if (!spotifyWidgetElement) {
        console.error("Standard Widget: Ana widget elementi (#spotifyWidgetStandard) DOM'da bulunamadı.");
        return;
    }
    const INTRO_ANIMATION_CLASS = spotifyWidgetElement.dataset.introAnimationClass || 'standard-fade-in-up';
    // TRANSITION_ANIMATION_CLASS 'standard-content-pop' ana widget'a eklenir ve CSS'ten çocukları hedefler.
    // Biz şarkı değişimi için elementlere özel animasyon sınıflarını kullanacağız.
    const OUTRO_ANIMATION_CLASS = spotifyWidgetElement.dataset.outroAnimationClass || 'standard-fade-out';
    
    // CSS'te tanımlı özel animasyon sınıfları (JS ile elementlere direkt uygulanacak)
    const ALBUM_ART_POP_CLASS = 'album-art-pop';
    const CONTENT_POP_ANIMATION_CLASS = 'content-pop-animation';
    const LOGO_TRANSITION_CLASS = 'spotify-logo-transition'; // CSS'teki spotifyLogoTransitionAnimation keyframe'ine karşılık gelir


    // 3. DURUM DEĞİŞKENLERİ
    let currentTrackProgressInterval = null;
    let lastTrackId = null;
    let currentFetchTimeoutId = null;

    // 4. DOM ELEMENT REFERANSLARI
    const albumArtElement = document.getElementById('albumArt');
    const albumArtBackgroundElement = document.getElementById('albumArtBackground');
    const trackNameElement = document.getElementById('trackName');
    const artistNameElement = document.getElementById('artistName');
    const progressBarElement = document.getElementById('progressBar');
    const currentTimeElement = document.getElementById('currentTime');
    const totalTimeElement = document.getElementById('totalTime');
    const errorMessageElement = document.getElementById('errorMessage');
    // Animasyon için belirli elementler
    const trackInfoElement = document.querySelector('.widget-track-info'); 
    const playerControlsElement = document.querySelector('.widget-player-controls'); 
    const spotifyLogoElement = document.querySelector('.widget-spotify-logo'); 

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
     * 6.1. Gelen verilere göre standart widget UI'ını günceller.
     * @param {Object|null} data - API'den gelen şarkı verisi veya null.
     * @param {string|null} [errorMessageText=null] - Harici bir hata mesajı.
     */
    function updateWidgetUI(data, errorMessageText = null) {
        if (!spotifyWidgetElement) return;

        if (errorMessageText) {
            WidgetCommon.showError(errorMessageElement, errorMessageText);
            WidgetCommon.updateTextContent(trackNameElement, 'Hata Oluştu', 'Veri alınırken bir sorun oluştu.');
            WidgetCommon.updateTextContent(artistNameElement, '-', '-');
            WidgetCommon.updateImageSource(albumArtElement, PLACEHOLDER_ERROR_URL, PLACEHOLDER_ERROR_URL);
            WidgetCommon.updateImageSource(albumArtBackgroundElement, PLACEHOLDER_BACKGROUND_URL, PLACEHOLDER_BACKGROUND_URL); 
            if (trackNameElement) trackNameElement.classList.remove('playing');
            if (currentTrackProgressInterval) clearInterval(currentTrackProgressInterval);
            WidgetCommon.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, 0, 0, false);
            return;
        }

        if (data && (data.item || data.track_name)) {
            WidgetCommon.hideError(errorMessageElement);

            const track = data.item || {};
            const trackName = track.name || data.track_name || "Bilinmeyen Şarkı";
            const artists = track.artists || (data.artist_name ? [{ name: data.artist_name }] : []);
            const artistName = artists.map(artist => artist.name).join(', ') || "Bilinmeyen Sanatçı";
            
            let albumImageUrl = PLACEHOLDER_IMAGE_URL;
            let albumImageBackgroundUrl = PLACEHOLDER_BACKGROUND_URL;

            if (track.album?.images?.length > 0) {
                albumImageUrl = track.album.images.find(img => img.height >= 250)?.url || track.album.images[0].url;
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

        } else {
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

    // 7. VERİ YÖNETİMİ
    /**
     * 7.1. Veriyi backend'den çeker ve UI'ı günceller. Periyodik olarak kendini çağırır.
     */
    async function fetchAndDisplayData() {
        clearCurrentFetchTimeout();

        const token = window.WIDGET_TOKEN_FROM_HTML;
        const endpointTemplate = window.DATA_ENDPOINT_TEMPLATE;

        if (!token || !endpointTemplate) {
            const errorMsg = !token ? 'Widget token eksik.' : 'API endpoint şablonu eksik.';
            updateWidgetUI(null, `Başlatma hatası: ${errorMsg}`);
            if (spotifyWidgetElement) spotifyWidgetElement.classList.add('widget-disabled');
            return;
        }
        if (spotifyWidgetElement) spotifyWidgetElement.classList.remove('widget-disabled');

        try {
            const data = await WidgetCommon.fetchWidgetData(token, endpointTemplate);
            const currentTrackId = data?.item?.id || data?.track_name || null;

            if (lastTrackId !== null && currentTrackId && currentTrackId !== lastTrackId) {
                playStandardSongChangeAnimation();
            }
            lastTrackId = currentTrackId;

            updateWidgetUI(data);

            const refreshInterval = (data?.is_playing && data?.item?.duration_ms)
                ? Math.min(7000, (data.item.duration_ms - (data.progress_ms || 0)) + 1500)
                : (data?.is_playing ? 7000 : 15000);
            
            currentFetchTimeoutId = setTimeout(fetchAndDisplayData, Math.max(1500, refreshInterval));
        } catch (error) {
            console.error("Standard Widget: Veri çekme hatası:", error);
            // Hata mesajını UI'da gösterirken error.message'ı kullanmak daha bilgilendirici olabilir.
            updateWidgetUI(null, `Veri alınırken bir hata oluştu: ${error.message || 'Sunucu yanıt vermiyor veya ağ sorunu.'}`);
            currentFetchTimeoutId = setTimeout(fetchAndDisplayData, 30000); // Hata durumunda daha uzun bekle
        }
    }

    // 8. WIDGET'A ÖZEL ANİMASYON FONKSİYONLARI
    /**
     * 8.1. Standart widget için şarkı değişiminde özel animasyonları tetikler.
     * WidgetCommon.triggerAnimation doğru şekilde çağrılır ve animasyon sınıfları manuel olarak kaldırılır.
     */
    function playStandardSongChangeAnimation() {
        const animationDuration = 1200; // ms, CSS animasyon süreleriyle eşleşmeli

        if (albumArtElement) {
            WidgetCommon.triggerAnimation(albumArtElement, ALBUM_ART_POP_CLASS);
            setTimeout(() => {
                albumArtElement.classList.remove(ALBUM_ART_POP_CLASS);
            }, animationDuration);
        }

        if (trackInfoElement) {
            setTimeout(() => { // trackInfo için hafif gecikme
                WidgetCommon.triggerAnimation(trackInfoElement, CONTENT_POP_ANIMATION_CLASS);
                setTimeout(() => {
                    trackInfoElement.classList.remove(CONTENT_POP_ANIMATION_CLASS);
                }, animationDuration);
            }, 100);
        }

        if (playerControlsElement) {
            setTimeout(() => { // playerControls için biraz daha gecikme
                WidgetCommon.triggerAnimation(playerControlsElement, CONTENT_POP_ANIMATION_CLASS);
                setTimeout(() => {
                    playerControlsElement.classList.remove(CONTENT_POP_ANIMATION_CLASS);
                }, animationDuration);
            }, 200);
        }

        if (spotifyLogoElement) {
            setTimeout(() => { // logo için en son gecikme
                WidgetCommon.triggerAnimation(spotifyLogoElement, LOGO_TRANSITION_CLASS);
                setTimeout(() => {
                    spotifyLogoElement.classList.remove(LOGO_TRANSITION_CLASS);
                }, animationDuration);
            }, 300);
        }
    }


    // 9. BAŞLATMA
    /**
     * 9.1. Widget'ı başlatır: İlk veri çekme, animasyonlar.
     */
    function initWidget() {
        WidgetCommon.playIntroAnimation(spotifyWidgetElement, INTRO_ANIMATION_CLASS);
        // Giriş animasyon sınıfının da (eğer `forwards` değilse) kaldırılması gerekebilir.
        // Şimdilik CSS'in bunu yönettiğini varsayıyoruz.
        // Alternatif:
        // setTimeout(() => {
        //     if (spotifyWidgetElement) spotifyWidgetElement.classList.remove(INTRO_ANIMATION_CLASS);
        // }, CSS_INTRO_ANIM_DURATION);


        WidgetCommon.setupPageUnloadAnimation(spotifyWidgetElement, OUTRO_ANIMATION_CLASS, 400); 
        fetchAndDisplayData();
        console.log("Standard Spotify Widget Başlatıldı.");
    }

    // 9.2. DOMContentLoaded Olay Dinleyicisi içinde widget'ı başlat
    initWidget();
});
