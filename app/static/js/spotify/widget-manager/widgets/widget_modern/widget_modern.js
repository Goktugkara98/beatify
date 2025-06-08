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

    // Tüm animasyonlu elementleri setlerine göre grupla
    const elements = {
        a: document.querySelectorAll('[data-set="a"]'),
        b: document.querySelectorAll('[data-set="b"]')
    };

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
        let longestIntro = 0;

        introElements.forEach(el => {
            const animName = el.dataset.introAnimation;
            const duration = parseInt(el.dataset.introDuration, 10) || 0;
            const delay = parseInt(el.dataset.introDelay, 10) || 0;
            const elementTotalDuration = delay + duration;

            el.classList.remove('passive');

            if (animName && animName !== 'none') {
                el.style.animation = `${animName} ${duration}ms ease-out ${delay}ms forwards`;
                setTimeout(() => {
                    el.style.animation = ''; // Clear animation for this element
                }, elementTotalDuration);
            } else { // animName is 'none' or not specified
                if (delay > 0) {
                    el.style.opacity = 0; // Start invisible if there's a delay
                    setTimeout(() => {
                        el.style.opacity = 1;
                        // No animation to clear for 'none', but ensure final state after its 'duration'
                        setTimeout(() => { /* Potentially do nothing or ensure opacity is 1 */ }, duration); 
                    }, delay);
                } else {
                    el.style.opacity = 1; // Ensure visible if no animation and no delay
                     // No animation to clear for 'none', but ensure final state after its 'duration'
                    setTimeout(() => { /* Potentially do nothing or ensure opacity is 1 */ }, duration); 
                }
            }
            if (elementTotalDuration > longestIntro) {
                longestIntro = elementTotalDuration;
            }
        });

        setTimeout(() => {
            // Individual animations are cleared by their own timeouts.
            // This main timeout is now just for the global state.
            isAnimating = false;
            WidgetCore.log('ModernWidget: Intro animation sequence complete.', 'debug');
        }, longestIntro);
    }

    function playOutroAnimation(setKey) {
        isAnimating = true;
        const outroElements = elements[setKey];
        let longestOutro = 0;

        outroElements.forEach(el => {
            const animName = el.dataset.outroAnimation;
            const duration = parseInt(el.dataset.outroDuration, 10) || 0;
            const delay = parseInt(el.dataset.outroDelay, 10) || 0;
            const elementTotalDuration = delay + duration;

            if (animName && animName !== 'none') {
                el.style.animation = `${animName} ${duration}ms ease-out ${delay}ms forwards`;
            } else { // animName is 'none' or not specified
                el.style.opacity = 1; // Ensure it's visible during its "none" animation time
                // No actual animation, but we respect its duration for visibility
            }

            setTimeout(() => {
                el.style.animation = ''; // Clear animation style
                el.classList.add('passive');
                el.style.opacity = 0;
                el.style.zIndex = ''; // Reset z-index to default (from CSS)
                WidgetCore.log(`ModernWidget: Element ${el.id || el.tagName} (outgoing ${setKey}) animation/transition complete. Now passive, z-index reset.`, 'debug');
            }, elementTotalDuration);

            if (elementTotalDuration > longestOutro) {
                longestOutro = elementTotalDuration;
            }
        });

        setTimeout(() => {
            // Individual elements handle their own state changes (passive, opacity, animation clear).
            // This main timeout is for global state updates.
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
        const activeElements = elements[activeKey];
        const passiveElements = elements[passiveKey];

        updateElementSet(passiveKey, data);

        const zIndexConfig = {
            outgoing: {
                'albumArtBackground': '0',
                'albumArt': '2',
                'trackName': '4',
                'artistName': '4',
                'playerControls': '6',
                'spotifyLogo': '6'
            },
            incoming: {
                'albumArtBackground': '1',
                'albumArt': '3',
                'trackName': '5',
                'artistName': '5',
                'playerControls': '7',
                'spotifyLogo': '7'
            }
        };

        function getElementType(element) {
            if (element.id.startsWith('albumArtBackground_')) return 'albumArtBackground';
            if (element.id.startsWith('albumArt_')) return 'albumArt';
            if (element.id.startsWith('trackName_')) return 'trackName';
            if (element.id.startsWith('artistName_')) return 'artistName';
            if (element.classList.contains('widget-player-controls')) return 'playerControls';
            if (element.classList.contains('widget-spotify-logo')) return 'spotifyLogo';
            return null;
        }

        passiveElements.forEach(el => {
            el.classList.remove('passive'); // Make them part of the layout for animation
            const elementType = getElementType(el);
            if (elementType && zIndexConfig.incoming[elementType]) {
                el.style.zIndex = zIndexConfig.incoming[elementType];
                WidgetCore.log(`ModernWidget: Element ${el.id || el.className} (incoming ${passiveKey}) z-index set to ${zIndexConfig.incoming[elementType]}.`, 'debug');
            } else if (elementType) {
                WidgetCore.log(`ModernWidget: Element ${el.id || el.className} (incoming ${passiveKey}) type ${elementType} not in zIndexConfig.incoming.`, 'warn');
            } else {
                WidgetCore.log(`ModernWidget: Element ${el.id || el.className} (incoming ${passiveKey}) type unknown for z-index.`, 'warn');
            }
        });

        activeElements.forEach(el => {
            const elementType = getElementType(el);
            if (elementType && zIndexConfig.outgoing[elementType]) {
                el.style.zIndex = zIndexConfig.outgoing[elementType];
                WidgetCore.log(`ModernWidget: Element ${el.id || el.className} (outgoing ${activeKey}) z-index set to ${zIndexConfig.outgoing[elementType]}.`, 'debug');
            } else if (elementType) {
                WidgetCore.log(`ModernWidget: Element ${el.id || el.className} (outgoing ${activeKey}) type ${elementType} not in zIndexConfig.outgoing.`, 'warn');
            } else {
                WidgetCore.log(`ModernWidget: Element ${el.id || el.className} (outgoing ${activeKey}) type unknown for z-index.`, 'warn');
            }
        });

        let longestAnimation = 0;

        activeElements.forEach(el => {
            const animName = el.dataset.transitionOutAnimation;
            const duration = parseInt(el.dataset.transitionOutDuration, 10) || 0;
            const delay = parseInt(el.dataset.transitionOutDelay, 10) || 0;
            const elementOutDuration = delay + duration;

            if (animName && animName !== 'none') {
                el.style.animation = `${animName} ${duration}ms ease-out ${delay}ms forwards`;
            } else { // animName is 'none' or not specified for transition-out
                el.style.opacity = 1; // Ensure visible during its "none" out phase
                el.style.animation = ''; // Clear any previous animation
            }

            setTimeout(() => {
                el.style.animation = ''; // Clear animation style
                el.classList.add('passive');
                el.style.opacity = 0;
                el.style.zIndex = ''; // Reset z-index to default (from CSS)
                WidgetCore.log(`ModernWidget: Element ${el.id || el.tagName} (outgoing ${activeKey}) animation/transition complete. Now passive, z-index reset.`, 'debug');
            }, elementOutDuration);

            if (elementOutDuration > longestAnimation) {
                longestAnimation = elementOutDuration;
            }
        });

        passiveElements.forEach(el => {
            const animName = el.dataset.transitionInAnimation;
            const duration = parseInt(el.dataset.transitionInDuration, 10) || 0;
            const delay = parseInt(el.dataset.transitionInDelay, 10) || 0;
            const elementInDuration = delay + duration;

            if (animName && animName !== 'none') {
                el.style.opacity = 0; // Start transparent for actual animations
                el.style.animation = `${animName} ${duration}ms ease-in ${delay}ms forwards`;
                setTimeout(() => {
                    el.style.animation = '';
                    el.style.opacity = 1; // Ensure fully visible after animation
                }, elementInDuration);
            } else { // animName is 'none' or not specified for transition-in
                 el.style.animation = '';
                 if (delay > 0) {
                    el.style.opacity = 0; // Start transparent if there's a delay
                    setTimeout(() => {
                        el.style.opacity = 1;
                        // After its 'duration' for 'none', ensure opacity is 1
                        setTimeout(() => { el.style.opacity = 1; }, duration);
                    }, delay);
                 } else {
                    el.style.opacity = 1; // Become visible immediately
                    // After its 'duration' for 'none', ensure opacity is 1
                    setTimeout(() => { el.style.opacity = 1; }, duration);
                 }
            }
            if (elementInDuration > longestAnimation) {
                longestAnimation = elementInDuration;
            }
        });

        setTimeout(() => {
            // Individual elements handle their own state changes (passive, opacity, animation clear).
            // This main timeout is for global state updates.
            currentState = passiveKey;
            isAnimating = false;
            WidgetCore.log('ModernWidget: Transition sequence complete. Current set:', 'debug', currentState);
        }, longestAnimation);
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
        elements.b.forEach(el => el.classList.add('passive'));

        const coreConfig = {
            widgetElement: spotifyWidgetElement,
            token: token,
            endpointTemplate: endpointTemplate,
            onSongChange: (newData, oldData) => {
                let markedNewData = newData ? {...newData} : null;
                if (oldData === undefined && markedNewData !== null) { 
                    markedNewData.is_initial_data = true;
                }
                handleSongChange(markedNewData, oldData);
            },
            onDataUpdate: (newData) => {
                spotifyWidgetElement.dispatchEvent(new CustomEvent('coreDataUpdate', { detail: { newData } }));
            },
            onError: (errorData) => {
                spotifyWidgetElement.dispatchEvent(new CustomEvent('coreError', { detail: { errorData } }));
            }
        };
        
        WidgetCore.initWidgetBase(coreConfig);
        // Initial data fetch is triggered by initWidgetBase, which then calls onSongChange.
    }

    initWidget();
});