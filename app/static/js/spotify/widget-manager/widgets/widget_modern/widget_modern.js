/**
 * widget_modern.js - New Animation Logic by Cascade
 *
 * Manages dual-set (A/B) element animations for smooth transitions in the Spotify widget.
 * Integrates with WidgetCore for data updates and state management.
 */
document.addEventListener('DOMContentLoaded', () => {
    'use strict'; // Strict mode

    // Section 1: Module Dependency Check
    if (typeof WidgetCore === 'undefined') {
        console.error('Modern Widget: WidgetCore not found! Please ensure spotify_widget_core.js is loaded.');
        document.body.insertAdjacentHTML('afterbegin', '<div style="color:red;padding:10px;text-align:center;background:#fff;border:1px solid red;">Widget failed to initialize: Core components missing.</div>');
        return;
    }

    // Section 2: Main Widget Element
    const spotifyWidgetElement = document.getElementById('spotifyWidgetModern');
    if (!spotifyWidgetElement) {
        console.error("Modern Widget: Main widget element (#spotifyWidgetModern) not found in DOM.");
        return;
    }
    const generalErrorMessageElement = document.getElementById('errorMessage'); // For general, non-UI specific errors

    // 1. Durum (State) Yönetimi
    let currentState = 'a'; // Başlangıçta 'a' seti aktif
    let isAnimating = false;
    
    // Backend'den gelen konfigürasyonu kontrol et
    console.log('window.configData:', window.configData); // Tüm configData'yı logla
    
    // Eğer configData yoksa veya boşsa uyarı ver
    if (!window.configData) {
        console.warn('window.configData tanımlı değil! Backend\'den konfigürasyon gelmiyor olabilir.');
    } else if (!window.configData.animations) {
        console.warn('window.configData.animations tanımlı değil! Backend\'den animasyon konfigürasyonu gelmiyor.');
    } else {
        console.log('Backend\'den gelen animasyon konfigürasyonu:', window.configData.animations);
    }
    
    // Varsayılan animasyon konfigürasyonu
    const defaultAnimationConfig = {
        albumArt: {
            intro: { animation: 'fade-in', duration: 1000, delay: 200 },
            transitionIn: { animation: 'slide-in-right', duration: 1000, delay: 0 },
            transitionOut: { animation: 'slide-out-left', duration: 1000, delay: 0 },
            outro: { animation: 'slide-out-left', duration: 1000, delay: 0 }
        },
        trackInfo: {
            intro: { animation: 'fade-in', duration: 1000, delay: 400 },
            transitionIn: { animation: 'slide-in-right', duration: 1000, delay: 100 },
            transitionOut: { animation: 'slide-out-left', duration: 1000, delay: 0 },
            outro: { animation: 'slide-out-left', duration: 1000, delay: 0 }
        },
        playerControls: {
            intro: { animation: 'fade-in', duration: 1000, delay: 400 },
            transitionIn: { animation: 'slide-in-right', duration: 1000, delay: 0 },
            transitionOut: { animation: 'slide-out-left', duration: 1000, delay: 0 },
            outro: { animation: 'slide-out-left', duration: 1000, delay: 0 }
        },
        spotifyLogo: {
            intro: { animation: 'fade-in', duration: 1000, delay: 500 },
            transitionIn: { animation: 'slide-in-right', duration: 1000, delay: 0 },
            transitionOut: { animation: 'slide-out-left', duration: 1000, delay: 0 },
            outro: { animation: 'slide-out-left', duration: 1000, delay: 0 }
        }
    };
    
    // Backend'den gelen konfigürasyonu kullan, yoksa varsayılanı kullan
    const animationConfig = window.configData?.animations || defaultAnimationConfig;
    
    // Map element types to their animation configs
    const elementTypeToConfig = {
        'albumArt': 'albumArt',
        'albumArtBackground': 'albumArtBackground',
        'trackName': 'trackName',
        'artistName': 'artistName',
        'playerControls': 'playerControls',
        'spotifyLogo': 'spotifyLogo'
    };

    // Tüm animasyonlu elementleri setlerine göre grupla
    const elements = {
        a: document.querySelectorAll('[data-set="a"]'),
        b: document.querySelectorAll('[data-set="b"]')
    };

    // Helper function to apply animations based on backend config
    function _applyAnimations(elementsToAnimate, animationTypeKey, currentSetKeyForLogging = '', onCompletePerElement = null) {
        let longestOverallDuration = 0;

        const animAttrMap = {
            intro: { isIncoming: true },
            transitionIn: { isIncoming: true },
            transitionOut: { isIncoming: false },
            outro: { isIncoming: false }
        };

        const config = animAttrMap[animationTypeKey];
        if (!config) {
            WidgetCore.log(`ModernWidget: _applyAnimations - Invalid animationTypeKey: ${animationTypeKey}`, 'error');
            return 0;
        }

        elementsToAnimate.forEach(el => {
            const elementType = el.dataset.type;
            const setKey = el.dataset.set; // 'a' veya 'b'
            const configKey = `${elementTypeToConfig[elementType] || 'trackInfo'}_${setKey}`;
            
            // Önce doğrudan element_set formatında ara (örn: albumArt_a)
            let animConfig;
            if (animationConfig[configKey] && animationConfig[configKey][animationTypeKey]) {
                animConfig = animationConfig[configKey][animationTypeKey];
            } 
            // Yoksa varsayılan yapıya geri dön
            else if (defaultAnimationConfig[elementTypeToConfig[elementType]] && 
                     defaultAnimationConfig[elementTypeToConfig[elementType]][animationTypeKey]) {
                animConfig = defaultAnimationConfig[elementTypeToConfig[elementType]][animationTypeKey];
            } 
            // Hiçbiri yoksa boş animasyon kullan
            else {
                animConfig = { animation: 'none', duration: 0, delay: 0 };
            }
            
            const animName = animConfig.animation;
            const duration = animConfig.duration || 0;
            const delay = animConfig.delay || 0;
            const elementTotalDuration = delay + duration;

            if (config.isIncoming) {
                el.classList.remove('passive');
                el.style.opacity = 0; // Start all incoming elements (animating or 'none') as transparent
            }
            // For outgoing elements, they are already visible. Animation will handle fade-out.
            // Final opacity 0 will be set in the setTimeout callback.

            if (animName && animName !== 'none') {
                el.style.animation = `${animName} ${duration}ms ease-out ${delay}ms forwards`;
            }

            setTimeout(() => {
                el.style.animation = ''; // Clear animation style

                if (config.isIncoming) {
                    el.style.opacity = 1; // Ensure incoming elements are visible
                    WidgetCore.log(`ModernWidget: Element ${el.id || el.className} (${animationTypeKey} ${currentSetKeyForLogging}) animation complete. Now active and visible.`, 'debug');
                } else { // Outgoing
                    el.style.opacity = 0; // Ensure outgoing elements are hidden
                    el.classList.add('passive');
                    WidgetCore.log(`ModernWidget: Element ${el.id || el.className} (${animationTypeKey} ${currentSetKeyForLogging}) animation complete. Now passive and hidden.`, 'debug');
                }

                if (typeof onCompletePerElement === 'function') {
                    onCompletePerElement(el);
                }
            }, elementTotalDuration);

            if (elementTotalDuration > longestOverallDuration) {
                longestOverallDuration = elementTotalDuration;
            }
        });
        return longestOverallDuration;
    }

    // Helper function to update content of an element set
    function updateElementSet(setKey, data) {
        const suffix = (setKey === 'a') ? '_a' : '_b';

        const albumArtElement = document.getElementById('albumArt' + suffix);
        const albumArtBackgroundElement = document.getElementById('albumArtBackground' + suffix);
        const trackNameElement = document.getElementById('trackName' + suffix);
        const artistNameElement = document.getElementById('artistName' + suffix);
        
        const playerControlsContainer = document.querySelector(`.widget-player-controls[data-set="${setKey}"]`);
        let progressBarElement, currentTimeElement, totalTimeElement;
        if (playerControlsContainer) {
            progressBarElement = playerControlsContainer.querySelector('#progressBar' + suffix);
            currentTimeElement = playerControlsContainer.querySelector('#currentTime' + suffix);
            totalTimeElement = playerControlsContainer.querySelector('#totalTime' + suffix);
        }

        if (data && (data.item || data.track_name)) {
            if(generalErrorMessageElement) WidgetCore.hideError(generalErrorMessageElement); // Hide general error if we have good data

            const track = data.item || {};
            const trackName = track.name || data.track_name || "Bilinmeyen Şarkı";
            const artists = track.artists || (data.artist_name ? [{ name: data.artist_name }] : []);
            const artistNameText = artists.map(artist => artist.name).join(', ') || 'Sanatçı Bilgisi Yok';
            const albumImageUrl = track.album?.images?.[0]?.url || data.album_image_url || 'https://placehold.co/600x360/1f2937/e5e7eb?text=Beatify';
            const albumBgImageUrl = track.album?.images?.[0]?.url || data.album_image_url || 'https://placehold.co/600x600/121212/e5e7eb?text=Beatify+BG';

            if (trackNameElement) WidgetCore.updateTextContent(trackNameElement, trackName);
            if (artistNameElement) WidgetCore.updateTextContent(artistNameElement, artistNameText);
            if (albumArtElement) WidgetCore.updateImageSource(albumArtElement, albumImageUrl, trackName + ' - Albüm Kapağı');
            if (albumArtBackgroundElement) WidgetCore.updateImageSource(albumArtBackgroundElement, albumBgImageUrl, trackName + ' - Arka Plan Albüm Sanatı');

            const isPlaying = data.is_playing ?? false;
            const progressMs = data.progress_ms ?? 0;
            const durationMs = track.duration_ms || data.duration_ms || 0;
            if (progressBarElement && currentTimeElement && totalTimeElement) {
                WidgetCore.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, progressMs, durationMs, isPlaying);
            }
        } else { // No song playing or error in data structure
            if (trackNameElement) WidgetCore.updateTextContent(trackNameElement, 'Bir Şey Çalmıyor');
            if (artistNameElement) WidgetCore.updateTextContent(artistNameElement, 'Spotify');
            if (albumArtElement) WidgetCore.updateImageSource(albumArtElement, 'https://placehold.co/600x360/1f2937/e5e7eb?text=Beatify', 'Albüm Kapağı Yok');
            if (albumArtBackgroundElement) WidgetCore.updateImageSource(albumArtBackgroundElement, 'https://placehold.co/600x600/121212/e5e7eb?text=Beatify+BG', 'Arka Plan Albüm Sanatı Yok');
            if (progressBarElement && currentTimeElement && totalTimeElement) {
                WidgetCore.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, 0, 0, false);
            }
        }
    }

    // 2. Widget_Core'dan Gelen Çağrı (Ana Mantık)
    function handleSongChange(newData, oldData) {
        WidgetCore.log('ModernWidget: handleSongChange triggered.', 'debug', { newDataIsInitial: newData?.is_initial_data, isAnimating });
        
        if (isAnimating && !(newData && newData.is_initial_data === true)) {
            WidgetCore.log('ModernWidget: Animation in progress, new song change ignored.', 'warn');
            return; 
        }

        const activeSetKey = currentState;
        const passiveSetKey = (currentState === 'a') ? 'b' : 'a';
        
        if (newData && newData.is_initial_data === true) {
            WidgetCore.log('ModernWidget: Initial data load, playing intro.', 'info');
            playIntroAnimation(activeSetKey, newData);
        } else if (newData) { 
            WidgetCore.log('ModernWidget: New song data, playing transition.', 'info');
            playTransition(activeSetKey, passiveSetKey, newData);
        } else { 
            WidgetCore.log('ModernWidget: No new data (song stopped or error), playing outro.', 'info');
            playOutroAnimation(activeSetKey);
        }
    }

    function playIntroAnimation(setKey, data) {
        if (spotifyWidgetElement) {
            spotifyWidgetElement.classList.remove('widget-inactive');
            WidgetCore.log('ModernWidget: widget-inactive class removed.', 'debug');
        }
        isAnimating = true;
        updateElementSet(setKey, data);
        const introElements = elements[setKey];

        // _applyAnimations will handle removing 'passive' and other animation logic
        const longestIntro = _applyAnimations(introElements, 'intro', setKey);

        setTimeout(() => {
            isAnimating = false;
            WidgetCore.log('ModernWidget: Intro animation sequence complete.', 'debug');
        }, longestIntro);
    }

    function playOutroAnimation(setKey) {
        isAnimating = true;
        const outroElements = elements[setKey];

        // _applyAnimations will handle applying 'passive' class and other animation logic
        const longestOutro = _applyAnimations(outroElements, 'outro', setKey);

        setTimeout(() => {
            isAnimating = false;
            WidgetCore.log('ModernWidget: Outro animation sequence complete.', 'debug');
            if (spotifyWidgetElement) {
                spotifyWidgetElement.classList.add('widget-inactive');
                WidgetCore.log('ModernWidget: widget-inactive class added.', 'debug');
            }
        }, longestOutro);
    }

    // 3. Animasyon Orkestrasyonu (Transition)
    function playTransition(activeKey, passiveKey, data) {
        isAnimating = true;
        const activeElements = elements[activeKey]; // Outgoing elements
        const passiveElements = elements[passiveKey]; // Incoming elements

        updateElementSet(passiveKey, data); // Populate incoming elements with new data

        const zIndexConfig = {
            outgoing: { 'albumArtBackground': '0', 'albumArt': '2', 'trackName': '4', 'artistName': '4', 'playerControls': '6', 'spotifyLogo': '6' },
            incoming: { 'albumArtBackground': '1', 'albumArt': '3', 'trackName': '5', 'artistName': '5', 'playerControls': '7', 'spotifyLogo': '7' }
        };

        function getElementType(element) {
            return element.dataset.type || null;
        }

        // Apply z-indexes before starting animations
        passiveElements.forEach(el => {
            const elementType = getElementType(el);
            if (elementType && zIndexConfig.incoming[elementType]) {
                el.style.zIndex = zIndexConfig.incoming[elementType];
            }
        });
        activeElements.forEach(el => {
            const elementType = getElementType(el);
            if (elementType && zIndexConfig.outgoing[elementType]) {
                el.style.zIndex = zIndexConfig.outgoing[elementType];
            }
        });

        // Callback to reset z-index after individual animation completes
        const onElementTransitionComplete = (element) => {
            element.style.zIndex = ''; // Reset z-index to CSS default
            WidgetCore.log(`ModernWidget: Element ${element.id || element.className} z-index reset post-transition.`, 'debug');
        };

        // Apply animations using the helper
        const longestOutDuration = _applyAnimations(activeElements, 'transitionOut', activeKey, onElementTransitionComplete);
        const longestInDuration = _applyAnimations(passiveElements, 'transitionIn', passiveKey, onElementTransitionComplete);

        const longestOverallTransition = Math.max(longestOutDuration, longestInDuration);

        // Global cleanup after the entire transition animation sequence

        setTimeout(() => {
            // Individual elements handle their own state changes (passive, opacity, animation clear).
            // This main timeout is for global state updates.
            currentState = passiveKey;
            isAnimating = false;
            WidgetCore.log('ModernWidget: Transition sequence complete. Current set:', 'debug', currentState);
        }, longestOverallTransition);
    }

    // CORE EVENT HANDLERS (for events other than song change)
    function handleCoreDataUpdate(event) {
        WidgetCore.log('ModernWidget: CoreDataUpdate received.', 'debug', event.detail.newData);
        // This could be used for minor updates that don't require full A/B transition,
        // e.g., just updating progress bar on the currently active set if not animating.
        if (!isAnimating && elements[currentState]) {
            // Example: Update progress on current elements if it's just a progress update
            // This requires more specific data structure from WidgetCore or more complex logic here.
            // For now, we assume all significant changes come via onSongChange.
        }
    }

    function handleCoreError(event) { 
        const errorData = event.detail.errorData;
        WidgetCore.log('ModernWidget: CoreError received.', 'error', errorData);
        if (generalErrorMessageElement) {
            WidgetCore.showError(generalErrorMessageElement, errorData.message || errorData.error || 'Bilinmeyen bir hata oluştu.');
        }
        // Consider playing an outro for the current set if error is critical and UI should hide
        if (!isAnimating) { // Avoid interfering with ongoing animations
            playOutroAnimation(currentState);
        }
    }

    spotifyWidgetElement.addEventListener('coreDataUpdate', handleCoreDataUpdate);
    spotifyWidgetElement.addEventListener('coreError', handleCoreError);

    // 5. BAŞLATMA (INITIALIZATION)
    async function initWidget() {
        try {
            // Backend'den gelen konfigürasyonu kontrol et
            console.log('initWidget: window.configData kontrol ediliyor...');
            
            if (window.configData) {
                console.log('initWidget: window.configData mevcut:', window.configData);
                
                if (window.configData.animations) {
                    console.log('initWidget: Backend\'den animasyon konfigürasyonu alındı:', window.configData.animations);
                    // Backend'den gelen konfigürasyonu kullanıyoruz, zaten animationConfig değişkeninde mevcut
                } else {
                    console.warn('initWidget: Backend\'den animasyon konfigürasyonu gelmedi, varsayılanlar kullanılacak');
                }
            } else {
                console.warn('initWidget: Backend\'den hiç konfigürasyon gelmedi, tüm ayarlar varsayılan değerlerle çalışacak');
            }

            const token = spotifyWidgetElement.dataset.token;
            const endpointTemplate = spotifyWidgetElement.dataset.endpointTemplate;

            if (!token || !endpointTemplate) {
                const errorMsg = "Yapılandırma eksik: 'data-token' veya 'data-endpoint-template' bulunamadı.";
                console.error("Modern Widget: " + errorMsg);
                if (generalErrorMessageElement) WidgetCore.showError(generalErrorMessageElement, errorMsg);
                else document.body.insertAdjacentHTML('afterbegin', `<div style="color:red;padding:10px;text-align:center;background:#fff;border:1px solid red;">${errorMsg}</div>`);
                return;
            }

            // Ensure initial state of 'b' elements is passive
            elements.b.forEach(el => {
                el.classList.add('passive');
                el.style.opacity = 0;
            });

            const coreConfig = {
                widgetElement: spotifyWidgetElement,
                token: token,
                endpointTemplate: endpointTemplate,
                onSongChange: handleSongChange,
                onDataUpdate: (newData) => {
                    spotifyWidgetElement.dispatchEvent(new CustomEvent('coreDataUpdate', { detail: { newData } }));
                },
                onError: (errorData) => {
                    spotifyWidgetElement.dispatchEvent(new CustomEvent('coreError', { detail: { errorData } }));
                }
            };
            
            WidgetCore.initWidgetBase(coreConfig);
            
            // Initial display of set A with intro animation
            if (elements.a.length > 0) {
                playIntroAnimation('a', {});
            }
            
            WidgetCore.log('ModernWidget: Initialization complete.', 'info');
        } catch (error) {
            console.error('ModernWidget: Initialization failed:', error);
            if (generalErrorMessageElement) {
                generalErrorMessageElement.textContent = 'Widget başlatılırken bir hata oluştu.';
                generalErrorMessageElement.style.display = 'block';
            }
        }
    }

    initWidget();
});