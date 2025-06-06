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

    // 2. ANA WIDGET ELEMENTİ VE DETAYLI DOM REFERANSLARI
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
    const widgetTrackInfoElement = spotifyWidgetElement.querySelector('.widget-track-info');
    const playerControlsElement = spotifyWidgetElement.querySelector('.widget-player-controls');
    const spotifyLogoElement = spotifyWidgetElement.querySelector('.widget-spotify-logo');
    // Not: albumArtElement, albumArtBackgroundElement vb. zaten yukarıda tanımlı.

    // Animasyon temel sınıfları (module scope)
    let introAnimationClassBase = '';
    let transitionAnimationClassBase = '';
    let outroAnimationClassBase = '';

    // 3.1. GİRİŞ ANİMASYONU (INTRO ANIMATION)
    async function playFullIntroAnimation() {
        if (!introAnimationClassBase) {
            WidgetCore.log("ModernWidget: Giriş animasyon seti tanımlanmamış, atlanıyor.", 'warn');
            return;
        }
        WidgetCore.log(`ModernWidget: "${introAnimationClassBase}" giriş animasyon seti kullanılıyor.`, 'info');

        // İlk veriyi al ve UI'ı güncelle (animasyondan önce)
        const initialData = WidgetCore.getLastFetchedData();
        if (initialData) {
            updateWidgetUI(initialData);
            WidgetCore.log('ModernWidget: İlk UI güncellemesi giriş animasyonundan önce yapıldı.', 'info');
        } else {
            WidgetCore.log('ModernWidget: Giriş animasyonu için ilk veri bulunamadı.', 'warn');
            // Opsiyonel: Hata durumu veya boş UI gösterilebilir.
            // updateWidgetUI(null, "Başlangıç verisi yüklenemedi.");
        }

        const animations = [];
        if (albumArtElement) animations.push(WidgetCore.triggerAnimation(albumArtElement, `${introAnimationClassBase}-art`));
        if (albumArtBackgroundElement) animations.push(WidgetCore.triggerAnimation(albumArtBackgroundElement, `${introAnimationClassBase}-art`)); // Genellikle aynı animasyon
        if (widgetTrackInfoElement) animations.push(WidgetCore.triggerAnimation(widgetTrackInfoElement, `${introAnimationClassBase}-text`));
        if (playerControlsElement) animations.push(WidgetCore.triggerAnimation(playerControlsElement, `${introAnimationClassBase}-controls`));
        if (spotifyLogoElement) animations.push(WidgetCore.triggerAnimation(spotifyLogoElement, `${introAnimationClassBase}-logo`));

        try {
            await Promise.all(animations);
            WidgetCore.log("ModernWidget: Giriş animasyonları tamamlandı.", 'info');
        } catch (error) {
            WidgetCore.log("ModernWidget: Giriş animasyonları sırasında hata.", 'error', error);
        }
    }

    // 3.2. ÇIKIŞ ANİMASYONU (OUTRO ANIMATION)
    async function playFullOutroAnimation() {
        if (!outroAnimationClassBase) {
            WidgetCore.log("ModernWidget: Çıkış animasyon seti tanımlanmamış, atlanıyor.", 'warn');
            return;
        }
        WidgetCore.log(`ModernWidget: "${outroAnimationClassBase}" çıkış animasyon seti kullanılıyor.`, 'info');

        const animations = [];
        // Outro animasyonları genellikle daha basittir ve tüm elemanları aynı anda etkileyebilir
        // veya belirli elemanlara özel olabilir. HTML'deki data-outro-animation-class="modern-fade-out"
        // gibi bir değere göre -art, -text ekleyerek özelleştirebiliriz.
        if (albumArtElement) animations.push(WidgetCore.triggerAnimation(albumArtElement, `${outroAnimationClassBase}-art`));
        if (albumArtBackgroundElement) animations.push(WidgetCore.triggerAnimation(albumArtBackgroundElement, `${outroAnimationClassBase}-art`)); 
        if (widgetTrackInfoElement) animations.push(WidgetCore.triggerAnimation(widgetTrackInfoElement, `${outroAnimationClassBase}-text`));
        if (playerControlsElement) animations.push(WidgetCore.triggerAnimation(playerControlsElement, `${outroAnimationClassBase}-controls`));
        if (spotifyLogoElement) animations.push(WidgetCore.triggerAnimation(spotifyLogoElement, `${outroAnimationClassBase}-logo`));
        // Alternatif olarak, ana widget elementine tek bir animasyon uygulanabilir:
        // animations.push(WidgetCore.triggerAnimation(spotifyWidgetElement, outroAnimationClassBase));

        try {
            await Promise.all(animations);
            WidgetCore.log("ModernWidget: Çıkış animasyonları tamamlandı.", 'info');
        } catch (error) {
            WidgetCore.log("ModernWidget: Çıkış animasyonları sırasında hata.", 'error', error);
        }
    }

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
    async function handleSongChange(newData, oldData) {
        WidgetCore.log('ModernWidget: Gerçek şarkı değişimi algılandı.', 'info', { 
            newTrack: newData?.item?.name || newData?.track_name,
            oldTrack: oldData?.item?.name || oldData?.track_name 
        });

        // Eğer oldData yoksa (bu ilk yüklemedir), geçiş animasyonunu atla, UI zaten playFullIntroAnimation'da güncellendi.
        // Veya playFullIntroAnimation'da UI güncellenmiyorsa burada güncellenir ama animasyonsuz.
        // Mevcut akışta playFullIntroAnimation UI'ı güncelleyecek.
        if (!oldData) {
            WidgetCore.log('ModernWidget: İlk yükleme, onSongChange içinde geçiş animasyonu atlanıyor.', 'info');
            // updateWidgetUI(newData); // playFullIntroAnimation zaten bunu yapacak.
            return; // Erken çıkış, geçiş animasyonuna gerek yok.
        }

        const transitionSetBaseName = spotifyWidgetElement.dataset.transitionAnimationClass; // HTML'deki data-transition-animation-class

        if (transitionSetBaseName && albumArtElement && widgetTrackInfoElement) {
            WidgetCore.log(`ModernWidget: "${transitionSetBaseName}" geçiş animasyon seti kullanılıyor.`, 'info');
            
            // Çıkış (Out) Aşaması
            const outAnimations = [];
            if (albumArtElement) outAnimations.push(WidgetCore.triggerAnimation(albumArtElement, `${transitionSetBaseName}-art-out`));
            if (albumArtBackgroundElement) outAnimations.push(WidgetCore.triggerAnimation(albumArtBackgroundElement, `${transitionSetBaseName}-art-out`));
            if (widgetTrackInfoElement) outAnimations.push(WidgetCore.triggerAnimation(widgetTrackInfoElement, `${transitionSetBaseName}-text-out`));
            // Gerekirse playerControlsElement için de bir çıkış animasyonu eklenebilir.

            if (outAnimations.length > 0) {
                await Promise.all(outAnimations);
                WidgetCore.log('ModernWidget: Geçiş animasyonu - Çıkış aşaması tamamlandı.', 'info');
            }

            updateWidgetUI(newData); // İçeriği güncelle
            WidgetCore.log('ModernWidget: UI, yeni şarkı verisiyle güncellendi.', 'info');

            // Giriş (In) Aşaması
            const inAnimations = [];
            if (albumArtElement) inAnimations.push(WidgetCore.triggerAnimation(albumArtElement, `${transitionSetBaseName}-art-in`));
            if (albumArtBackgroundElement) inAnimations.push(WidgetCore.triggerAnimation(albumArtBackgroundElement, `${transitionSetBaseName}-art-in`));
            if (widgetTrackInfoElement) inAnimations.push(WidgetCore.triggerAnimation(widgetTrackInfoElement, `${transitionSetBaseName}-text-in`));
            // Gerekirse playerControlsElement için de bir giriş animasyonu eklenebilir.

            if (inAnimations.length > 0) {
                await Promise.all(inAnimations);
                WidgetCore.log('ModernWidget: Geçiş animasyonu - Giriş aşaması tamamlandı.', 'info');
            }

        } else {
            updateWidgetUI(newData); // Animasyon tanımlı değilse veya elementler yoksa doğrudan güncelle
            if (!transitionSetBaseName) {
                WidgetCore.log('ModernWidget: Geçiş animasyon seti tanımlanmamış, UI doğrudan güncellendi.', 'warn');
            } else {
                WidgetCore.log('ModernWidget: Geçiş animasyonu için gerekli elementler bulunamadı, UI doğrudan güncellendi.', 'warn');
            }
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

    // WidgetCore'dan gelen olaylara tepki vermek için event listener'lar
    spotifyWidgetElement.addEventListener('coreSongChange', (event) => {
        handleSongChange(event.detail.newData, event.detail.oldData);
    });

    spotifyWidgetElement.addEventListener('coreDataUpdate', (event) => {
        handleDataUpdate(event.detail.newData);
    });

    spotifyWidgetElement.addEventListener('coreError', (event) => {
        handleError(event.detail.errorData);
    });

    // 5. BAŞLATMA (INITIALIZATION)
    /**
     * Widget'ı başlatan ana fonksiyon.
     * HTML'den yapılandırmayı okur ve WidgetCore'u bu yapılandırmayla başlatır.
     */
    async function initWidget() { // async yaptık
        // Defensive check for spotifyWidgetElement and its dataset property
        if (!spotifyWidgetElement || typeof spotifyWidgetElement.dataset === 'undefined') {
            console.error(
                "Modern Widget initWidget: spotifyWidgetElement is invalid or does not have a 'dataset' property.",
                {
                    element: spotifyWidgetElement,
                    typeofElement: typeof spotifyWidgetElement,
                    hasDataset: spotifyWidgetElement ? typeof spotifyWidgetElement.dataset !== 'undefined' : false
                }
            );
            // Attempt to show error on UI if possible, though DOM might be compromised
            if (errorMessageElement) {
                 WidgetCore.showError(errorMessageElement, "Widget initialization error: Main element invalid.");
            } else {
                // Fallback if even errorMessageElement is not available
                document.body.insertAdjacentHTML('afterbegin', '<div style="color:red;padding:10px;text-align:center;background:#fff;border:1px solid red;">Critical widget init error.</div>');
            }
            return; // Stop further execution in initWidget
        }

        // Yapılandırmayı HTML elementinin data-* özelliklerinden al
        const token = spotifyWidgetElement.dataset.token;
        const endpointTemplate = spotifyWidgetElement.dataset.endpointTemplate;
        // Module scope'taki değişkenleri initialize et
        introAnimationClassBase = spotifyWidgetElement.dataset.introAnimationClass || null;
        transitionAnimationClassBase = spotifyWidgetElement.dataset.transitionAnimationClass || 'modern-content-pop'; // Varsayılan
        outroAnimationClassBase = spotifyWidgetElement.dataset.outroAnimationClass || null;

        if (!token || !endpointTemplate) {
            handleError({ error: "Yapılandırma eksik: 'data-token' veya 'data-endpoint-template' bulunamadı." });
            return;
        }

        // WidgetCore'u başlatmak için tüm yapılandırmayı bir nesne olarak hazırla
        const coreConfig = {
            widgetElement: spotifyWidgetElement,
            token: token,
            endpointTemplate: endpointTemplate,
            introAnimationClass: null, // Core artık intro/outro'yu doğrudan tetiklemiyor
            outroAnimationClass: null,
            onActivate: playFullIntroAnimation, // WidgetCore.activateWidget çağrıldığında bu çalışacak
            onDeactivate: playFullOutroAnimation, // WidgetCore.deactivateWidget çağrıldığında bu çalışacak
            onSongChange: (newData, oldData) => {
                spotifyWidgetElement.dispatchEvent(new CustomEvent('coreSongChange', { detail: { newData, oldData } }));
            },
            onDataUpdate: (newData) => {
                spotifyWidgetElement.dispatchEvent(new CustomEvent('coreDataUpdate', { detail: { newData } }));
            },
            onError: (errorData) => {
                spotifyWidgetElement.dispatchEvent(new CustomEvent('coreError', { detail: { errorData } }));
            }
        };
        
        // Orkestra şefine (WidgetCore) notalarını (coreConfig) ver ve başlat komutu gönder.
        WidgetCore.initWidgetBase(coreConfig);
    }

    // Widget'ı başlat!
    initWidget();
});