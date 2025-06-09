/**
 * widget_standard.js
 *
 * Standart dikdörtgen widget için animasyon ve UI mantığını yönetir.
 * WidgetCore ile entegre çalışarak veri güncellemelerini alır ve A/B set animasyonlarını yönetir.
 */
document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    // Modül bağımlılığını kontrol et
    if (typeof WidgetCore === 'undefined') {
        console.error('Standard Widget: WidgetCore bulunamadı! spotify_widget_core.js yüklendiğinden emin olun.');
        return;
    }

    // Ana widget elementini seç
    const spotifyWidgetElement = document.getElementById('spotifyWidgetStandard');
    if (!spotifyWidgetElement) {
        console.error("Standard Widget: Ana widget elementi (#spotifyWidgetStandard) DOM'da bulunamadı.");
        return;
    }
    const generalErrorMessageElement = document.getElementById('errorMessage');

    // Durum Yönetimi
    let currentState = 'a'; // Başlangıçta 'a' seti aktif
    let isAnimating = false;

    // Standart widget için basitleştirilmiş animasyon konfigürasyonu
    const animationConfig = {
        albumArt: {
            intro: { animation: 'slide-cover-in', duration: 600, delay: 100 },
            transitionIn: { animation: 'slide-cover-in', duration: 500, delay: 0 },
            transitionOut: { animation: 'slide-cover-out', duration: 500, delay: 0 }
        },
        trackInfo: { // trackName ve artistName için ortak
            intro: { animation: 'slide-up-in', duration: 500, delay: 200 },
            transitionIn: { animation: 'slide-up-in', duration: 400, delay: 100 },
            transitionOut: { animation: 'slide-down-out', duration: 400, delay: 0 }
        },
        playerControls: { // progressBar, currentTime, totalTime için ortak
            intro: { animation: 'fade-in', duration: 500, delay: 300 },
            transitionIn: { animation: 'fade-in', duration: 400, delay: 200 },
            transitionOut: { animation: 'fade-out', duration: 300, delay: 0 }
        },
        spotifyLogo: {
            intro: { animation: 'fade-in', duration: 500, delay: 400 },
            transitionIn: { animation: 'fade-in', duration: 400, delay: 0 },
            transitionOut: { animation: 'fade-out', duration: 400, delay: 0 }
        }
    };
    
    // Element tiplerini animasyon konfigürasyonlarına eşle
    const elementTypeToConfigKey = {
        'albumArt': 'albumArt',
        'trackName': 'trackInfo',
        'artistName': 'trackInfo',
        'progressBar': 'playerControls',
        'currentTime': 'playerControls',
        'totalTime': 'playerControls',
        'spotifyLogo': 'spotifyLogo'
    };

    // Tüm animasyonlu elementleri setlerine göre grupla
    const elements = {
        a: document.querySelectorAll('[data-set="a"]'),
        b: document.querySelectorAll('[data-set="b"]')
    };

    // Animasyonları uygulama yardımcısı
    function _applyAnimations(elementsToAnimate, animationTypeKey) {
        let longestOverallDuration = 0;

        elementsToAnimate.forEach(el => {
            const elementType = el.dataset.type;
            const configKey = elementTypeToConfigKey[elementType];
            if (!configKey || !animationConfig[configKey] || !animationConfig[configKey][animationTypeKey]) return;

            const animConfig = animationConfig[configKey][animationTypeKey];
            const animName = animConfig.animation;
            const duration = animConfig.duration || 0;
            const delay = animConfig.delay || 0;
            const elementTotalDuration = delay + duration;

            if (animationTypeKey === 'intro' || animationTypeKey === 'transitionIn') {
                el.classList.remove('passive');
            }

            el.style.animation = `${animName} ${duration}ms ease-out ${delay}ms forwards`;

            setTimeout(() => {
                el.style.animation = '';
                if (animationTypeKey === 'transitionOut' || animationTypeKey === 'outro') {
                    el.classList.add('passive');
                }
            }, elementTotalDuration);

            if (elementTotalDuration > longestOverallDuration) {
                longestOverallDuration = elementTotalDuration;
            }
        });
        return longestOverallDuration;
    }

    // Bir element setinin içeriğini güncelle
    function updateElementSet(setKey, data) {
        const suffix = (setKey === 'a') ? '_a' : '_b';

        const albumArtElement = document.getElementById('albumArt' + suffix);
        const trackNameElement = document.getElementById('trackName' + suffix);
        const artistNameElement = document.getElementById('artistName' + suffix);
        const progressBarElement = document.getElementById('progressBar' + suffix);
        const currentTimeElement = document.getElementById('currentTime' + suffix);
        const totalTimeElement = document.getElementById('totalTime' + suffix);
        
        if (data && (data.item || data.track_name)) {
            if(generalErrorMessageElement) WidgetCore.hideError(generalErrorMessageElement);

            const track = data.item || {};
            const trackName = track.name || data.track_name || "Bilinmeyen Şarkı";
            const artists = track.artists || (data.artist_name ? [{ name: data.artist_name }] : []);
            const artistNameText = artists.map(artist => artist.name).join(', ') || 'Sanatçı Bilgisi Yok';
            const albumImageUrl = track.album?.images?.[0]?.url || data.album_image_url || 'https://placehold.co/120x120/1f2937/e5e7eb?text=Beatify';

            WidgetCore.updateTextContent(trackNameElement, trackName);
            WidgetCore.updateTextContent(artistNameElement, artistNameText);
            WidgetCore.updateImageSource(albumArtElement, albumImageUrl, trackName + ' - Albüm Kapağı');

            const isPlaying = data.is_playing ?? false;
            const progressMs = data.progress_ms ?? 0;
            const durationMs = track.duration_ms || data.duration_ms || 0;

            WidgetCore.updateProgressBar(
                progressBarElement, currentTimeElement, totalTimeElement, 
                progressMs, durationMs, isPlaying
            );
        } else {
            WidgetCore.updateTextContent(trackNameElement, 'Bir Şey Çalmıyor');
            WidgetCore.updateTextContent(artistNameElement, 'Spotify');
            WidgetCore.updateImageSource(albumArtElement, 'https://placehold.co/120x120/1f2937/e5e7eb?text=Beatify', 'Albüm Kapağı Yok');
            WidgetCore.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, 0, 0, false);
        }
    }

    // Widget_Core'dan gelen ana çağrı
    function handleSongChange(newData, oldData) {
        if (isAnimating && !(newData && newData.is_initial_data)) return;
        
        const activeSetKey = currentState;
        const passiveSetKey = (currentState === 'a') ? 'b' : 'a';

        if (newData && newData.is_initial_data) {
            playIntroAnimation(activeSetKey, newData);
        } else if (newData) {
            playTransition(activeSetKey, passiveSetKey, newData);
        }
    }

    function playIntroAnimation(setKey, data) {
        spotifyWidgetElement.classList.remove('widget-inactive');
        isAnimating = true;
        updateElementSet(setKey, data);
        const introElements = elements[setKey];
        const longestIntro = _applyAnimations(introElements, 'intro');
        setTimeout(() => { isAnimating = false; }, longestIntro);
    }

    function playTransition(activeKey, passiveKey, data) {
        isAnimating = true;
        updateElementSet(passiveKey, data);

        const longestOutDuration = _applyAnimations(elements[activeKey], 'transitionOut');
        const longestInDuration = _applyAnimations(elements[passiveKey], 'transitionIn');
        const longestOverallTransition = Math.max(longestOutDuration, longestInDuration);

        setTimeout(() => {
            currentState = passiveKey;
            isAnimating = false;
        }, longestOverallTransition);
    }
    
    function handleCoreError(errorData) { 
        WidgetCore.log('StandardWidget: CoreError alındı.', 'error', errorData);
        if (generalErrorMessageElement) {
            WidgetCore.showError(generalErrorMessageElement, errorData.message || errorData.error || 'Bilinmeyen bir hata oluştu.');
        }
    }

    // Başlatma
    function initWidget() {
        const token = spotifyWidgetElement.dataset.token;
        const endpointTemplate = spotifyWidgetElement.dataset.endpointTemplate;

        if (!token || !endpointTemplate) {
            const errorMsg = "Yapılandırma eksik: 'data-token' veya 'data-endpoint-template' bulunamadı.";
            console.error("Standard Widget: " + errorMsg);
            WidgetCore.showError(generalErrorMessageElement, errorMsg);
            return;
        }

        elements.b.forEach(el => el.classList.add('passive'));

        const coreConfig = {
            widgetElement: spotifyWidgetElement,
            token,
            endpointTemplate,
            onSongChange: handleSongChange,
            onDataUpdate: () => {}, // Standart widget anlık güncellemeleri farklı işlemiyor
            onError: handleCoreError,
        };
        
        WidgetCore.initWidgetBase(coreConfig);
    }

    initWidget();
});
