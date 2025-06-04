/**
 * widget_modern.js
 *
 * Modern Spotify widget'ı için özel JavaScript.
 * WidgetCommon modülünü kullanarak UI'ı yönetir ve widget'a özgü davranışları tanımlar.
 *
 * İÇİNDEKİLER:
 * 1. WIDGET'A ÖZEL AYARLAR VE SABİTLER
 *      1.1. Placeholder Resim URL'leri
 *      1.2. Animasyon Sınıfları
 * 2. DURUM DEĞİŞKENLERİ
 *      2.1. currentTrackProgressInterval
 *      2.2. lastTrackId
 *      2.3. currentFetchTimeoutId
 * 3. DOM ELEMENT REFERANSLARI
 * 4. UI GÜNCELLEME FONKSİYONLARI
 *      4.1. updateWidgetUI
 * 5. VERİ YÖNETİMİ
 *      5.1. fetchAndDisplayData
 *      5.2. clearCurrentFetchTimeout
 * 6. WIDGET'A ÖZEL ANİMASYONLAR
 *      6.1. playModernSongChangeAnimation
 * 7. BAŞLATMA VE OLAY YÖNETİMİ
 *      7.1. initWidget
 *      7.2. DOMContentLoaded Olayı
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    // WidgetCommon modülünün varlığını kontrol et
    if (typeof WidgetCommon === 'undefined') {
        console.error('Modern Widget: WidgetCommon bulunamadı! spotify_widget_core.js yüklendiğinden emin olun.');
        const body = document.body;
        const errorDiv = document.createElement('div');
        errorDiv.textContent = 'Widget başlatılamadı: Temel bileşenler eksik.';
        errorDiv.style.color = 'red';
        errorDiv.style.padding = '10px';
        errorDiv.style.textAlign = 'center';
        body.insertBefore(errorDiv, body.firstChild);
        return;
    }

    // 1. WIDGET'A ÖZEL AYARLAR VE SABİTLER
    // 1.1. Placeholder Resim URL'leri
    const PLACEHOLDER_IMAGE_URL = 'https://placehold.co/600x600/1f2937/e5e7eb?text=Beatify';
    const PLACEHOLDER_ERROR_URL = 'https://placehold.co/600x600/cc0000/ffffff?text=Hata';

    // 2. DURUM DEĞİŞKENLERİ
    // 2.1. currentTrackProgressInterval
    let currentTrackProgressInterval = null;
    // 2.2. lastTrackId
    let lastTrackId = null;
    // 2.3. currentFetchTimeoutId
    let currentFetchTimeoutId = null;

    // 3. DOM ELEMENT REFERANSLARI
    // 3.1. Ana Widget Elementi
    const spotifyWidgetElement = document.getElementById('spotifyWidgetModern');

    // 1.2. Animasyon Sınıfları
    const INTRO_ANIMATION_CLASS = spotifyWidgetElement?.dataset.introAnimationClass || 'modern-fade-in';
    const TRANSITION_ANIMATION_CLASS = spotifyWidgetElement?.dataset.transitionAnimationClass || 'modern-content-slide';
    const OUTRO_ANIMATION_CLASS = spotifyWidgetElement?.dataset.outroAnimationClass || 'modern-fade-out';

    // 3.2. Albüm Kapağı Elementleri
    const albumArtElement = document.getElementById('albumArt');
    
    // 3.3. Şarkı Bilgisi Elementleri
    const trackNameElement = document.getElementById('trackName');
    const artistNameElement = document.getElementById('artistName');
    
    // 3.4. Progress Bar Elementleri
    const progressBarContainerElement = document.getElementById('progressBarContainer');
    const progressBarElement = document.getElementById('progressBar');
    const currentTimeElement = document.getElementById('currentTime');
    const totalTimeElement = document.getElementById('totalTime');
    
    // 3.5. Hata Mesajı Elementi
    const errorMessageElement = document.getElementById('errorMessage');
    
    // 3.6. İçerik Alanı Elementi
    const widgetContentElement = document.getElementById('widgetContent');

    // 5.2. Timeout temizleme fonksiyonu
    function clearCurrentFetchTimeout() {
        if (currentFetchTimeoutId) {
            clearTimeout(currentFetchTimeoutId);
            currentFetchTimeoutId = null;
        }
    }

    // 4. UI GÜNCELLEME FONKSİYONLARI
    /**
     * 4.1. Gelen verilere göre modern widget UI'ını günceller.
     * @param {Object|null} data - API'den gelen şarkı verisi veya null.
     */
    function updateWidgetUI(data) {
        if (!spotifyWidgetElement) {
            console.error("Modern Widget: Ana widget elementi bulunamadı.");
            return;
        }

        if (data && (data.item || data.track_name)) { // Aktif bir şarkı verisi var
            WidgetCommon.hideError(errorMessageElement);

            const track = data.item || {}; // Spotify API'nin tam yapısı için
            const trackName = track.name || data.track_name || "Bilinmeyen Şarkı";
            const artists = track.artists || (data.artist_name ? [{name: data.artist_name}] : []);
            const artistName = artists.map(artist => artist.name).join(', ') || "Bilinmeyen Sanatçı";
            
            let albumImageUrl = PLACEHOLDER_IMAGE_URL;

            if (track.album && track.album.images && track.album.images.length > 0) {
                // En büyük boyuttaki kapak resmini seç
                albumImageUrl = track.album.images.find(img => img.height >= 600)?.url || track.album.images[0].url;
            } else if (data.album_image_url) {
                albumImageUrl = data.album_image_url;
            }

            WidgetCommon.updateTextContent(trackNameElement, trackName, trackName);
            WidgetCommon.updateTextContent(artistNameElement, artistName, artistName);
            WidgetCommon.updateImageSource(albumArtElement, albumImageUrl, PLACEHOLDER_ERROR_URL);

            const isPlaying = data.is_playing !== undefined ? data.is_playing : false;
            const progressMs = data.progress_ms !== undefined ? data.progress_ms : 0;
            const durationMs = track.duration_ms || data.duration_ms || 0;

            if (trackNameElement) {
                isPlaying ? trackNameElement.classList.add('playing') : trackNameElement.classList.remove('playing');
            }

            if (currentTrackProgressInterval) clearInterval(currentTrackProgressInterval);
            currentTrackProgressInterval = WidgetCommon.updateProgressBar(
                progressBarElement,
                currentTimeElement,
                totalTimeElement,
                progressMs,
                durationMs,
                isPlaying,
                () => { // Şarkı bittiğinde callback
                    clearCurrentFetchTimeout();
                    setTimeout(fetchAndDisplayData, 1500); // Kısa bir gecikmeyle veriyi yenile
                }
            );

        } else { // Çalınan bir şey yok veya veri eksik/hatalı
            WidgetCommon.updateTextContent(trackNameElement, 'Bir şey çalmıyor', 'Spotify\'da aktif bir içerik yok.');
            WidgetCommon.updateTextContent(artistNameElement, '-', '-');
            WidgetCommon.updateImageSource(albumArtElement, PLACEHOLDER_IMAGE_URL, PLACEHOLDER_IMAGE_URL);

            if (trackNameElement) trackNameElement.classList.remove('playing');
            if (currentTrackProgressInterval) clearInterval(currentTrackProgressInterval);
            WidgetCommon.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, 0, 0, false);
            
            if (data && data.error) { // Eğer backend'den bir hata mesajı geldiyse göster
                 WidgetCommon.showError(errorMessageElement, data.error);
            } else if (!data?.item && !data?.track_name && !data?.error) { // Ne veri ne de hata yoksa, genel mesaj
                 WidgetCommon.showError(errorMessageElement, 'Şu an aktif bir yayın yok veya veri alınamadı.');
            }
        }
    }

    // 5. VERİ YÖNETİMİ
    /**
     * 5.1. Veriyi backend'den çeker ve UI'ı günceller. Periyodik olarak kendini çağırır.
     */
    async function fetchAndDisplayData() {
        clearCurrentFetchTimeout();

        const token = window.WIDGET_TOKEN_FROM_HTML;
        const endpointTemplate = window.DATA_ENDPOINT_TEMPLATE;

        if (!token || !endpointTemplate) {
            const errorMessage = !token ? 'Widget token eksik.' : 'API endpoint şablonu eksik.';
            WidgetCommon.showError(errorMessageElement, `Başlatma hatası: ${errorMessage}`);
            updateWidgetUI(null); // UI'ı varsayılan duruma getir
            if (spotifyWidgetElement) spotifyWidgetElement.classList.add('widget-disabled');
            return;
        }

        const data = await WidgetCommon.fetchWidgetData(token, endpointTemplate);

        const currentTrackId = data?.item?.id || data?.track_name || null; // Benzersiz bir ID veya şarkı adı
        if (currentTrackId && currentTrackId !== lastTrackId && lastTrackId !== null) { // Sadece ilk yükleme değil, şarkı değiştiyse
            playModernSongChangeAnimation();
        }
        lastTrackId = currentTrackId;

        updateWidgetUI(data); // data null olsa bile UI'ı temizlemek için çağır

        // Bir sonraki veri çekme için zamanlayıcı
        const refreshInterval = data && data.is_playing ? 7000 : 15000; // Çalıyorsa 7sn, duruyorsa 15sn
        currentFetchTimeoutId = setTimeout(fetchAndDisplayData, refreshInterval);
    }

    // 6. WIDGET'A ÖZEL ANİMASYONLAR
    /**
     * 6.1. Modern widget için şarkı değişiminde özel animasyonları tetikler.
     */
    function playModernSongChangeAnimation() {
        if (!widgetContentElement || !albumArtElement) return;

        // Albüm kapağı için animasyon
        albumArtElement.style.transform = 'scale(1.05)';
        setTimeout(() => {
            albumArtElement.style.transform = 'scale(1)';
        }, 300);

        // İçerik alanı için animasyon
        WidgetCommon.triggerAnimation(widgetContentElement, TRANSITION_ANIMATION_CLASS);
    }

    // 7. BAŞLATMA VE OLAY YÖNETİMİ
    /**
     * 7.1. Widget'ı başlatır: İlk veri çekme, animasyonlar ve olay dinleyicileri.
     */
    function initWidget() {
        if (!spotifyWidgetElement) {
            console.error("Modern Widget: Ana widget elementi bulunamadı.");
            return;
        }

        // Giriş animasyonu
        WidgetCommon.playIntroAnimation(spotifyWidgetElement, INTRO_ANIMATION_CLASS);

        // Sayfa kapatma animasyonu
        WidgetCommon.setupPageUnloadAnimation(spotifyWidgetElement, OUTRO_ANIMATION_CLASS, 500);

        // İlk veri çekme
        fetchAndDisplayData();

        console.log("Modern Widget: Widget başlatıldı.");
    }

    // 7.2. DOMContentLoaded Olayı içinde widget'ı başlat
    initWidget();
});