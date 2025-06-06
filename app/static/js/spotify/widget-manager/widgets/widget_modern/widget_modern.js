/**
 * widget_modern.js (Core ile Uyumlu Revize Edilmiş Versiyon)
 *
 * WidgetCore modülünü yapılandırır ve Core'dan gelen olaylara tepki olarak UI'ı günceller.
 * Tüm veri çekme ve durum yönetimi mantığı WidgetCore'a devredilmiştir.
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    // 1. MODÜL BAĞIMLILIK KONTROLÜ
    if (typeof WidgetCore === 'undefined') {
        console.error('Modern Widget: WidgetCore bulunamadı! Lütfen spotify_widget_core.js dosyasının yüklendiğinden emin olun.');
        // Basit bir kullanıcı uyarısı göster
        document.body.insertAdjacentHTML('afterbegin', '<div style="color:red;padding:10px;text-align:center;background:#fff;border:1px solid red;">Widget başlatılamadı: Temel bileşenler eksik.</div>');
        return;
    }

    // 2. ANA WIDGET ELEMENTİ VE DOM REFERANSLARI
    const spotifyWidgetElement = document.getElementById('spotifyWidgetModern');
    if (!spotifyWidgetElement) {
        console.error("Modern Widget: Ana widget elementi (#spotifyWidgetModern) DOM'da bulunamadı.");
        return;
    }

    // Gerekli tüm UI elementlerini al
    const albumArtElement = document.getElementById('albumArt');
    const albumArtBackgroundElement = document.getElementById('albumArtBackground');
    const trackNameElement = document.getElementById('trackName');
    const artistNameElement = document.getElementById('artistName');
    const progressBarElement = document.getElementById('progressBar');
    const currentTimeElement = document.getElementById('currentTime');
    const totalTimeElement = document.getElementById('totalTime');
    const errorMessageElement = document.getElementById('errorMessage');
    const widgetContentElement = document.getElementById('widgetContent');

    // 3. UI GÜNCELLEME FONKSİYONU (Bu fonksiyon widget'ın "kas gücüdür")
    /**
     * Gelen verilere göre modern widget UI'ını A'dan Z'ye günceller.
     * Artık sadece Core'dan gelen veriyi görselleştirmekle sorumludur.
     * @param {Object|null} data - API'den gelen şarkı verisi.
     * @param {string|null} [errorMessageText=null] - Harici bir hata mesajı.
     */
    function updateWidgetUI(data, errorMessageText = null) {
        if (errorMessageText) {
            WidgetCore.showError(errorMessageElement, errorMessageText);
            WidgetCore.updateTextContent(trackNameElement, 'Hata Oluştu');
            WidgetCore.updateTextContent(artistNameElement, '-');
            // Hata durumunda görselleri ve ilerleme çubuğunu sıfırla
            WidgetCore.updateImageSource(albumArtElement, 'https://placehold.co/600x360/cc0000/ffffff?text=Hata', '');
            WidgetCore.updateImageSource(albumArtBackgroundElement, 'https://placehold.co/600x600/cc0000/ffffff?text=Hata', '');
            WidgetCore.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, 0, 0, false);
            return;
        }

        if (data && (data.item || data.track_name)) { // Aktif bir şarkı verisi var
            WidgetCore.hideError(errorMessageElement);

            const track = data.item || {};
            const trackName = track.name || data.track_name || "Bilinmeyen Şarkı";
            const artists = track.artists || (data.artist_name ? [{ name: data.artist_name }] : []);
            const artistName = artists.map(artist => artist.name).join(', ');
            const albumImageUrl = track.album?.images?.[0]?.url || data.album_image_url || 'https://placehold.co/600x360/1f2937/e5e7eb?text=Beatify';

            WidgetCore.updateTextContent(trackNameElement, trackName);
            WidgetCore.updateTextContent(artistNameElement, artistName);
            WidgetCore.updateImageSource(albumArtElement, albumImageUrl, '');
            WidgetCore.updateImageSource(albumArtBackgroundElement, albumImageUrl, '');

            const isPlaying = data.is_playing ?? false;
            const progressMs = data.progress_ms ?? 0;
            const durationMs = track.duration_ms || data.duration_ms || 0;
            WidgetCore.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, progressMs, durationMs, isPlaying);

        } else { // Çalınan bir şey yok
            WidgetCore.hideError(errorMessageElement);
            WidgetCore.updateTextContent(trackNameElement, 'Bir Şey Çalmıyor');
            WidgetCore.updateTextContent(artistNameElement, 'Spotify');
            WidgetCore.updateImageSource(albumArtElement, 'https://placehold.co/600x360/1f2937/e5e7eb?text=Beatify', '');
            WidgetCore.updateImageSource(albumArtBackgroundElement, 'https://placehold.co/600x600/121212/333333?text=BG', '');
            WidgetCore.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, 0, 0, false);
        }
    }

    // 4. CORE'DAN GELEN OLAYLARI YÖNETEN CALLBACK FONKSİYONLARI
    /**
     * Core "şarkı değişti" dediğinde tetiklenir.
     * Geçiş animasyonunu yönetmek için en doğru yerdir.
     */
    function handleSongChange(newData, oldData) {
        WidgetCore.log('ModernWidget: Gerçek şarkı değişimi algılandı, animasyon tetikleniyor.', 'info', { new: newData.item?.name, old: oldData.item?.name });
        
        const transitionAnimation = spotifyWidgetElement.dataset.transitionAnimation;
        if (widgetContentElement && transitionAnimation) {
            WidgetCore.playSongTransitionAnimation(widgetContentElement, transitionAnimation).then(() => {
                updateWidgetUI(newData); // Animasyon tamamlandığında içeriği güncelle
                WidgetCore.log('ModernWidget: Animasyon tamamlandı, içeriği güncellendi.', 'info', { newData });
            });
        } else {
            updateWidgetUI(newData); // Animasyon tanımlı değilse doğrudan güncelle
            WidgetCore.log('ModernWidget: Animasyon tanımlı değilse doğrudan güncelle', 'info', { newData });
        }
    }

    /**
     * Core'dan her yeni veri geldiğinde (şarkı aynı olsa bile) tetiklenir.
     * İlerleme çubuğu gibi anlık durumları güncellemek için kullanılır.
     */
    function handleDataUpdate(newData) {
        // Genellikle sadece UI'ı veriye göre güncelleriz.
        updateWidgetUI(newData);
    }

    /**
     * Core bir hata bildirdiğinde tetiklenir.
     */
    function handleError(error) {
        WidgetCore.log('ModernWidget: Core\'dan hata raporu alındı.', 'error', error);
        updateWidgetUI(null, error.error || 'Bilinmeyen bir hata oluştu.');
    }


    // 5. BAŞLATMA (INITIALIZATION)
    /**
     * Widget'ı başlatan ana fonksiyon.
     * HTML'den yapılandırmayı okur ve WidgetCore'u bu yapılandırmayla başlatır.
     */
    function initWidget() {
        // Yapılandırmayı HTML elementinin data-* özelliklerinden al
        const token = spotifyWidgetElement.dataset.token;
        const endpointTemplate = spotifyWidgetElement.dataset.endpointTemplate;
        const introAnimation = spotifyWidgetElement.dataset.introAnimation;
        // Geçiş animasyonu handleSongChange içinde okunuyor.

        if (!token || !endpointTemplate) {
            handleError({ error: "Yapılandırma eksik: 'data-token' veya 'data-endpoint-template' bulunamadı." });
            return;
        }

        // WidgetCore'u başlatmak için tüm yapılandırmayı bir nesne olarak hazırla
        const coreConfig = {
            token: token,
            endpointTemplate: endpointTemplate,
            widgetElement: spotifyWidgetElement,
            introAnimationClass: introAnimation,
            
            // Core'dan gelen olaylara hangi fonksiyonların tepki vereceğini bildir
            onSongChange: handleSongChange,
            onDataUpdate: handleDataUpdate,
            onError: handleError
        };
        
        // Orkestra şefine (WidgetCore) notalarını (coreConfig) ver ve başlat komutu gönder.
        WidgetCore.initWidgetBase(coreConfig);
    }

    // Widget'ı başlat!
    initWidget();
});