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
    const progressBarElement = document.getElementById('progressBar');
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
                playModernSongChangeAnimation();
            }
            lastTrackId = currentTrackId;

            updateWidgetUI(data);

            const refreshInterval = (data?.is_playing && data?.item?.duration_ms)
                ? Math.min(7000, (data.item.duration_ms - (data.progress_ms || 0)) + 1500) 
                : (data?.is_playing ? 7000 : 15000); 
            
            currentFetchTimeoutId = setTimeout(fetchAndDisplayData, Math.max(1500, refreshInterval)); 
        } catch (error) {
            console.error("Modern Widget: Veri çekme hatası:", error);
            updateWidgetUI(null, `Veri alınırken bir hata oluştu: ${error.message || 'Sunucu hatası'}`);
            currentFetchTimeoutId = setTimeout(fetchAndDisplayData, 30000); 
        }
    }

    // 8. WIDGET'A ÖZEL ANİMASYON FONKSİYONLARI
    /**
     * 8.1. Modern widget için şarkı değişiminde özel animasyonları tetikler.
     */
    function playModernSongChangeAnimation() {
        if (!widgetContentElement || !albumArtElement) { 
            console.warn("Modern Widget: Animasyon için content veya album art elementi bulunamadı.");
            return;
        }

        if (albumArtElement) {
            albumArtElement.style.opacity = '0.7';
             setTimeout(() => { albumArtElement.style.opacity = '1'; }, 500); 
        }
        if (albumArtBackgroundElement) {
            albumArtBackgroundElement.style.opacity = '0.7'; 
            setTimeout(() => { albumArtBackgroundElement.style.opacity = '1'; }, 500); 
        }
        
        WidgetCommon.triggerAnimation(widgetContentElement, TRANSITION_ANIMATION_CLASS);

        // Logo için de bir animasyon eklenebilir (opsiyonel)
        if (spotifyLogoElement) {
            spotifyLogoElement.style.transform = 'scale(1.1)';
            setTimeout(() => {
                spotifyLogoElement.style.transform = 'scale(1)';
            }, 300); // CSS transition süresiyle eşleşmeli veya ayrı bir animasyon sınıfı
        }
    }

    // 9. BAŞLATMA
    /**
     * 9.1. Widget'ı başlatır: İlk veri çekme, animasyonlar.
     */
    function initWidget() {
        WidgetCommon.playIntroAnimation(spotifyWidgetElement, INTRO_ANIMATION_CLASS);
        WidgetCommon.setupPageUnloadAnimation(spotifyWidgetElement, OUTRO_ANIMATION_CLASS, 500);
        fetchAndDisplayData();
        console.log("Modern Spotify Widget Başlatıldı.");
    }

    initWidget();
});
