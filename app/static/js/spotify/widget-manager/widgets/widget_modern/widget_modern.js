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

    // Element referansları yukarıda zaten tanımlı.

    // YARDIMCI FONKSİYON: Element için animasyon yapılandırmasını data-* özniteliklerinden okur
    function getAnimationConfig(element, phasePrefix) {
        if (!element || !element.dataset) return null;

        const animType = element.dataset[`${phasePrefix}Type`];
        if (!animType) return null; // Animasyon tipi belirtilmemişse animasyon yok

        return {
            animType: animType,
            options: {
                duration: element.dataset[`${phasePrefix}Duration`] || null, // CSS varsayılanını kullanır
                delay: element.dataset[`${phasePrefix}Delay`] || null,
                timingFunction: element.dataset[`${phasePrefix}Timing`] || null
            }
        };
    }

    // 3.1. GİRİŞ ANİMASYONU (INTRO ANIMATION)
    async function playFullIntroAnimation() {
        console.log('!!! GÜNCEL playFullIntroAnimation ÇALIŞIYOR !!!');
        WidgetCore.log("ModernWidget: Giriş animasyonları başlatılıyor...", 'info');
        
        const initialData = WidgetCore.getLastFetchedData();
        if (initialData) {
            updateWidgetUI(initialData);
            WidgetCore.log('ModernWidget: İlk UI güncellemesi giriş animasyonundan önce yapıldı.', 'info');
        } else {
            WidgetCore.log('ModernWidget: Giriş animasyonu için ilk veri bulunamadı.', 'warn');
        }

        const animations = [];
        const elementsToAnimateIntro = [
            { el: albumArtElement, name: 'Album Art (Main)' },
            { el: albumArtBackgroundElement, name: 'Album Art (Background)' },
            { el: widgetTrackInfoElement, name: 'Track Info Container' },
            { el: playerControlsElement, name: 'Player Controls' },
            { el: spotifyLogoElement, name: 'Spotify Logo' }
        ];
        
        // ve for döngüsündeki if (item.name === ...) koşulunu kaldırın:
        for (const item of elementsToAnimateIntro) {
            if (item.el) {
                const animConfig = getAnimationConfig(item.el, 'intro');
                // ... (debug logları kalabilir) ...
                if (animConfig) {
                    // ... (loglar) ...
                    animations.push(WidgetCore.triggerAnimation(item.el, animConfig.animType, animConfig.options));
                }
            }
        }

        if (animations.length === 0) {
            WidgetCore.log("ModernWidget: Tetiklenecek giriş animasyonu bulunamadı.", 'info');
            // Eğer albumArtElement bulunamazsa veya animConfig null ise buraya düşebilir.
            // Bu durumda polling'in başlaması için onActivate'in çözülmesi gerekir.
            // Ancak biz animasyonun kendisini test ediyoruz, bu yüzden Promise.all'a gitmeli.
            // Eğer gerçekten hiç animasyon yoksa, polling'in başlaması için buradan resolve etmek gerekebilir.
            // Şimdilik, en az bir animasyonun (albumArt) eklendiğini varsayıyoruz.
            // Eğer albumArt için bile animasyon eklenmiyorsa, bu ayrı bir sorundur.
            // return; // Bu satırı dikkatli kullanın, eğer animasyon yoksa ve polling bekleniyorsa sorun olur.
        }

        try {
            WidgetCore.log("ModernWidget: Promise.all çağrılmadan hemen önce...", 'debug', { animationCount: animations.length });
            await Promise.all(animations);
            WidgetCore.log("ModernWidget: Giriş animasyonları tamamlandı.", 'info');
        } catch (error) {
            WidgetCore.log("ModernWidget: Giriş animasyonları sırasında hata.", 'error', error);
        }
        // Polling'in başlaması için bu fonksiyonun başarıyla tamamlanması (resolve olması) gerekir.
    }

    // 3.2. ÇIKIŞ ANİMASYONU (OUTRO ANIMATION)
    async function playFullOutroAnimation() {
        WidgetCore.log("ModernWidget: Çıkış animasyonları başlatılıyor...", 'info');

        const animations = [];
        const elementsToAnimateOutro = [
            { el: albumArtElement, name: 'Album Art (Main)' },
            { el: albumArtBackgroundElement, name: 'Album Art (Background)' },
            { el: widgetTrackInfoElement, name: 'Track Info Container' },
            { el: playerControlsElement, name: 'Player Controls' },
            { el: spotifyLogoElement, name: 'Spotify Logo' }
        ];

        for (const item of elementsToAnimateOutro) {
            if (item.el) {
                const animConfig = getAnimationConfig(item.el, 'outro');
                if (animConfig) {
                    WidgetCore.log(`ModernWidget: Çıkış animasyonu [${animConfig.animType}] -> ${item.name}`, 'info', animConfig.options);
                    animations.push(WidgetCore.triggerAnimation(item.el, animConfig.animType, animConfig.options));
                } else {
                    // WidgetCore.log(`ModernWidget: Çıkış animasyon konfigürasyonu bulunamadı: ${item.name}`, 'debug');
                }
            }
        }

        if (animations.length === 0) {
            WidgetCore.log("ModernWidget: Tetiklenecek çıkış animasyonu bulunamadı.", 'info');
            return;
        }

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

        if (!oldData) {
            WidgetCore.log('ModernWidget: İlk yükleme, onSongChange içinde geçiş animasyonu atlanıyor.', 'info');
            return; 
        }

        WidgetCore.log("ModernWidget: Şarkı geçiş animasyonları başlatılıyor...", 'info');

        const elementsForTransition = [
            { el: albumArtElement, name: 'Album Art (Main)' },
            { el: albumArtBackgroundElement, name: 'Album Art (Background)' },
            { el: widgetTrackInfoElement, name: 'Track Info Container' }
            // playerControlsElement de buraya eklenebilir
        ];

        // Çıkış (Exit) Aşaması
        const exitAnimations = [];
        for (const item of elementsForTransition) {
            if (item.el) {
                const animConfig = getAnimationConfig(item.el, 'exit'); // 'exit' şarkı geçişi çıkış fazı için
                if (animConfig) {
                    WidgetCore.log(`ModernWidget: Şarkı geçişi (çıkış) [${animConfig.animType}] -> ${item.name}`, 'info', animConfig.options);
                    exitAnimations.push(WidgetCore.triggerAnimation(item.el, animConfig.animType, animConfig.options));
                }
            }
        }

        if (exitAnimations.length > 0) {
            try {
                await Promise.all(exitAnimations);
                WidgetCore.log('ModernWidget: Geçiş animasyonu - Çıkış aşaması tamamlandı.', 'info');
            } catch (error) {
                WidgetCore.log('ModernWidget: Geçiş animasyonu (çıkış) sırasında hata.', 'error', error);
            }
        } else {
            WidgetCore.log('ModernWidget: Tetiklenecek çıkış (geçiş) animasyonu bulunamadı.', 'info');
        }

        updateWidgetUI(newData); 
        WidgetCore.log('ModernWidget: UI, yeni şarkı verisiyle güncellendi (geçiş ortası).', 'info');

        // Giriş (Entry) Aşaması
        const entryAnimations = [];
        for (const item of elementsForTransition) {
            if (item.el) {
                const animConfig = getAnimationConfig(item.el, 'entry'); // 'entry' şarkı geçişi giriş fazı için
                if (animConfig) {
                    WidgetCore.log(`ModernWidget: Şarkı geçişi (giriş) [${animConfig.animType}] -> ${item.name}`, 'info', animConfig.options);
                    entryAnimations.push(WidgetCore.triggerAnimation(item.el, animConfig.animType, animConfig.options));
                }
            }
        }

        if (entryAnimations.length > 0) {
            try {
                await Promise.all(entryAnimations);
                WidgetCore.log('ModernWidget: Geçiş animasyonu - Giriş aşaması tamamlandı.', 'info');
            } catch (error) {
                WidgetCore.log('ModernWidget: Geçiş animasyonu (giriş) sırasında hata.', 'error', error);
            }
        } else {
            WidgetCore.log('ModernWidget: Tetiklenecek giriş (geçiş) animasyonu bulunamadı.', 'info');
        }
    }

    /**
     * Core'dan her yeni veri geldiğinde (şarkı aynı olsa bile) tetiklenir.
     * İlerleme çubuğu gibi anlık durumları güncellemek için kullanılır.
     */
    function handleDataUpdate(newData) {
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
    async function initWidget() {
        if (!spotifyWidgetElement || typeof spotifyWidgetElement.dataset === 'undefined') {
            console.error("Modern Widget initWidget: spotifyWidgetElement is invalid or does not have a 'dataset' property.");
            if (errorMessageElement) {
                 WidgetCore.showError(errorMessageElement, "Widget initialization error: Main element invalid.");
            } else {
                document.body.insertAdjacentHTML('afterbegin', '<div style="color:red;padding:10px;text-align:center;background:#fff;border:1px solid red;">Critical widget init error.</div>');
            }
            return; 
        }

        const token = spotifyWidgetElement.dataset.token;
        const endpointTemplate = spotifyWidgetElement.dataset.endpointTemplate;
        // Eski global animasyon sınıfı okumaları kaldırıldı.

        if (!token || !endpointTemplate) {
            handleError({ error: "Yapılandırma eksik: 'data-token' veya 'data-endpoint-template' bulunamadı." });
            return;
        }

        const coreConfig = {
            widgetElement: spotifyWidgetElement,
            token: token,
            endpointTemplate: endpointTemplate,
            introAnimationClass: null, 
            outroAnimationClass: null,
            onActivate: playFullIntroAnimation, 
            onDeactivate: playFullOutroAnimation, 
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
        
        WidgetCore.initWidgetBase(coreConfig);
    }

    // Widget'ı başlat!
    initWidget();
});