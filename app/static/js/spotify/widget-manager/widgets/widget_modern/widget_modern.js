/**
 * widget_modern.js (Core Compatible Revised Version) - Refreshed by Cascade
 *
 * Configures the WidgetCore module and updates the UI in response to events from Core.
 * All data fetching and state management logic is delegated to WidgetCore.
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict'; // Strict mode

    // Section 1: Module Dependency Check
    if (typeof WidgetCore === 'undefined') {
        console.error('Modern Widget: WidgetCore not found! Please ensure spotify_widget_core.js is loaded.'); // Minor text change
        // Display a simple user alert
        document.body.insertAdjacentHTML('afterbegin', '<div style="color:red;padding:10px;text-align:center;background:#fff;border:1px solid red;">Widget failed to initialize: Core components missing.</div>'); // Minor text change
        return;
    }

    // Section 2: Main Widget Element and Detailed DOM References
    const spotifyWidgetElement = document.getElementById('spotifyWidgetModern');
    if (!spotifyWidgetElement) {
        console.error("Modern Widget: Main widget element (#spotifyWidgetModern) not found in DOM."); // Minor text change
        return;
    }

    // Get all necessary UI elements
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
    // Note: albumArtElement, albumArtBackgroundElement etc., are already defined above. // Minor text change

    // Element references are already defined above. // Minor text change

    // HELPER FUNCTION: Reads animation configuration for an element from data-* attributes
    function getAnimationConfig(element, phasePrefix) { // Refreshed by Cascade
        if (!element || !element.dataset) return null;

        const animType = element.dataset[`${phasePrefix}Type`];
        // If animType is not specified OR is 'anim-none' or 'none', ignore animation.
        if (!animType || animType === 'anim-none' || animType === 'none') {
            return null;
        }

        return {
            animType: animType,
            options: {
                duration: element.dataset[`${phasePrefix}Duration`] || null, // Uses CSS default
                delay: element.dataset[`${phasePrefix}Delay`] || null,
                timingFunction: element.dataset[`${phasePrefix}Timing`] || null
            }
        };
    } // End of getAnimationConfig

    // Section: Intro Animation (3.1)
    async function playFullIntroAnimation() {
        console.log('!!! CURRENT playFullIntroAnimation IS RUNNING !!!'); // Changed log
        WidgetCore.log("ModernWidget: Intro animations starting...", 'info'); // Changed log
        
        const initialData = WidgetCore.getLastFetchedData();
        if (initialData) {
            updateWidgetUI(initialData);
            WidgetCore.log('ModernWidget: Initial UI update done before intro animation.', 'info'); // Changed log
        } else {
            WidgetCore.log('ModernWidget: Initial data not found for intro animation.', 'warn'); // Changed log
        }

        const animations = [];
        const elementsToAnimateIntro = [
            { el: albumArtElement, name: 'Album Art (Main)' },
            { el: albumArtBackgroundElement, name: 'Album Art (Background)' },
            { el: widgetTrackInfoElement, name: 'Track Info Container' },
            { el: playerControlsElement, name: 'Player Controls' },
            { el: spotifyLogoElement, name: 'Spotify Logo' }
        ];
        
        // Remove if (item.name === ...) condition in the for loop:
        for (const item of elementsToAnimateIntro) {
            if (item.el) {
                const animConfig = getAnimationConfig(item.el, 'intro');
                // ... (debug logs can remain) ...
                if (animConfig) {
                    // ... (logs) ...
                    animations.push(WidgetCore.triggerAnimation(item.el, animConfig.animType, animConfig.options));
                }
            }
        }

        if (animations.length === 0) {
            WidgetCore.log("ModernWidget: No intro animations to trigger.", 'info'); // Changed log
            // This can happen if albumArtElement is not found or animConfig is null.
            // Polling needs onActivate to resolve for it to start.
            // We are testing the animation itself, so it should go to Promise.all.
            // If there are truly no animations, resolving here might be needed for polling.
            // For now, assume at least one animation (albumArt) is added.
            // If no animation is added even for albumArt, that's a separate issue.
            // return; // Use this line carefully; it can cause issues if polling is expected and no animation runs.
        }

        try {
            WidgetCore.log("ModernWidget: Just before calling Promise.all for intro...", 'debug', { animationCount: animations.length }); // Changed log
            await Promise.all(animations);
            WidgetCore.log("ModernWidget: Intro animations completed.", 'info'); // Changed log
        } catch (error) {
            WidgetCore.log("ModernWidget: Error during intro animations.", 'error', error); // Changed log
        }
        // This function must complete successfully (resolve) for polling to start.
    } // Cascade_Clean_Refresh_Intro_v1

    // ELEMENT LIST FOR SONG TRANSITIONS (EXIT/ENTRY)
const ELEMENTS_FOR_SONG_TRANSITION = [
    { el: albumArtElement, name: 'Album Art (Main)' },
    { el: albumArtBackgroundElement, name: 'Album Art (Background)' },
    { el: widgetTrackInfoElement, name: 'Track Info Container' },
    { el: playerControlsElement, name: 'Player Controls' },
    { el: spotifyLogoElement, name: 'Spotify Logo' }
]; // Refreshed by Cascade

// Note: Exit/Entry animation logic is now part of handleSongChange.


// Section: Outro Animation (3.2)
    async function playFullOutroAnimation() {
        WidgetCore.log("ModernWidget: Outro animations starting.", 'info'); // Log message slightly changed
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
                    WidgetCore.log(`ModernWidget: Outro anim [${animConfig.animType}] for ${item.name}`, 'info', animConfig.options); // Log message slightly changed
                    animations.push(WidgetCore.triggerAnimation(item.el, animConfig.animType, animConfig.options));
                } else {
                    // WidgetCore.log(`ModernWidget: Çıkış animasyon konfigürasyonu bulunamadı: ${item.name}`, 'debug'); // This commented-out log remains as is
                }
            }
        }

        if (animations.length === 0) {
            WidgetCore.log("ModernWidget: No outro animations to trigger.", 'info'); // Log message slightly changed
            return;
        }

        try {
            await Promise.all(animations);
            WidgetCore.log("ModernWidget: Outro animations completed.", 'info'); // Log message slightly changed
        } catch (error) {
            WidgetCore.log("ModernWidget: Error during outro animations.", 'error', error); // Log message slightly changed
        }
    } // End of playFullOutroAnimation function (Cascade Clean Attempt)

    // This function updates the main UI of the widget.
    /**
     * Updates the widget UI.
     * @param {object|null} data The song data.
     * @param {string|null} [errorMessageText] An optional error message.
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
        }
    }

    // 4. CORE'DAN GELEN OLAYLARI YÖNETEN CALLBACK FONKSİYONLARI
    async function handleSongChange(newData, oldData) {
        WidgetCore.log('ModernWidget: handleSongChange triggered. Inspecting data:', 'debug', {
            newDataRaw: newData ? JSON.parse(JSON.stringify(newData)) : null,
            oldDataRaw: oldData ? JSON.parse(JSON.stringify(oldData)) : null
        });
        // Erken çıkış: Eğer eski veri yoksa (ilk yükleme) veya yeni veri yoksa veya şarkı değişmemişse.
        if (!oldData && newData) {
            WidgetCore.log('ModernWidget: İlk şarkı yüklemesi (handleSongChange), geçiş animasyonu atlanıyor. UI güncelleniyor.', 'info', { newData });
            updateWidgetUI(newData); // Sadece UI'ı ilk veriyle güncelle
            return;
        }

        const newTrackIdentifier = newData?.item?.id || newData?.item?.name || newData?.track_name; // Prioritize item.id, then item.name, then track_name (snake_case)
        const oldTrackIdentifier = oldData?.item?.id || oldData?.item?.name || oldData?.track_name; // Same for oldData

        if (!newData || !oldData || newTrackIdentifier === oldTrackIdentifier) {
            WidgetCore.log('ModernWidget: Şarkı aynı veya veri yetersiz, geçiş animasyonu atlanıyor (handleSongChange).', 'info', {
                conditionMet_NoNewData: !newData,
                conditionMet_NoOldData: !oldData,
                conditionMet_IdentifiersSame: newTrackIdentifier === oldTrackIdentifier,
                attemptedNewItemId: newData?.item?.id,
                attemptedNewItemName: newData?.item?.name,
                attemptedNewTrack_name: newData?.track_name, // snake_case
                attemptedOldItemId: oldData?.item?.id,
                attemptedOldItemName: oldData?.item?.name,
                attemptedOldTrack_name: oldData?.track_name, // snake_case
                finalNewIdentifier: newTrackIdentifier,
                finalOldIdentifier: oldTrackIdentifier
            });
            if (newData) { 
                updateWidgetUI(newData);
            }
            return;
        }

        WidgetCore.log(`ModernWidget: Gerçek şarkı değişimi algılandı. Yeni: ${newTrackIdentifier}, Eski: ${oldTrackIdentifier}`, 'info');
        WidgetCore.log("ModernWidget: Şarkı geçiş animasyonları (klonlama ile) başlatılıyor...", 'info');

        const outgoingElementsClones = [];
        const entryAnimationPromises = [];
        const exitAnimationPromises = [];

        for (const item of ELEMENTS_FOR_SONG_TRANSITION) {
            if (item.el && item.el.parentNode) {
                const clone = item.el.cloneNode(true);
                item.el.parentNode.insertBefore(clone, item.el); 
                
                clone.style.position = 'absolute'; 
                clone.style.top = item.el.offsetTop + 'px'; 
                clone.style.left = item.el.offsetLeft + 'px';
                clone.style.width = item.el.offsetWidth + 'px';
                clone.style.height = item.el.offsetHeight + 'px';
                clone.style.zIndex = '1'; 
                
                outgoingElementsClones.push({ original: item.el, clone: clone, name: item.name });
                
                item.el.style.opacity = '0'; 
            } else if (item.el) {
                WidgetCore.log(`ModernWidget: Klonlama atlandı, element (${item.name}) veya ebeveyni bulunamadı.`, 'warn', {element: item.el});
            }
        }

        // Exit animations for clones (OLD data)
        for (const entry of outgoingElementsClones) {
            const animConfig = getAnimationConfig(entry.clone, 'exit');
            if (animConfig) {
                WidgetCore.log(`ModernWidget: Klon (çıkış) [${animConfig.animType}] -> ${entry.name}`, 'info', animConfig.options);
                exitAnimationPromises.push(
                    WidgetCore.triggerAnimation(entry.clone, animConfig.animType, animConfig.options)
                        .then(() => {
                            if (entry.clone.parentNode) entry.clone.remove();
                            WidgetCore.log(`ModernWidget: Klon (çıkış) ${entry.name} kaldırıldı.`, 'debug');
                        })
                        .catch(err => {
                            WidgetCore.log(`ModernWidget: Klon (çıkış) ${entry.name} animasyon/kaldırma hatası.`, 'error', err);
                            if (entry.clone.parentNode) entry.clone.remove(); 
                        })
                );
            } else { 
                if (entry.clone.parentNode) entry.clone.remove();
                WidgetCore.log(`ModernWidget: Klon (çıkış) ${entry.name} animasyonsuz kaldırıldı.`, 'debug');
            }
        }

        // updateWidgetUI(newData); // MOVED: Called after clone exit animations complete.

        // Entry animations for original elements (NEW data)
        for (const entry of outgoingElementsClones) {
            if (!entry.original) continue;
            const animConfig = getAnimationConfig(entry.original, 'entry');
            if (animConfig) {
                WidgetCore.log(`ModernWidget: Orijinal (giriş) [${animConfig.animType}] -> ${entry.name}`, 'info', animConfig.options);
                entry.original.style.removeProperty('opacity'); 
                entryAnimationPromises.push(WidgetCore.triggerAnimation(entry.original, animConfig.animType, animConfig.options));
            } else { 
                 entry.original.style.opacity = '1'; 
            }
        }

        Promise.allSettled(exitAnimationPromises)
            .then(() => {
                WidgetCore.log("ModernWidget: Clone exit animations complete. Updating UI for new song.", 'info');
                updateWidgetUI(newData); // Update original UI elements with NEW data NOW.

                // Now, prepare and start entry animations for the original elements.
                const entryAnimationPromises = []; // Initialize a new array for entry promises.
                for (const entry of outgoingElementsClones) {
                    if (!entry.original) continue;
                    const animConfig = getAnimationConfig(entry.original, 'entry');
                    if (animConfig) {
                        WidgetCore.log(`ModernWidget: Orijinal (giriş) [${animConfig.animType}] -> ${entry.name}`, 'info', animConfig.options);
                        entry.original.style.removeProperty('opacity'); 
                        entryAnimationPromises.push(WidgetCore.triggerAnimation(entry.original, animConfig.animType, animConfig.options));
                    } else { 
                        entry.original.style.opacity = '1'; // No animation, just make it visible.
                    }
                }

                if (entryAnimationPromises.length > 0) {
                    return Promise.allSettled(entryAnimationPromises); // Chain this promise for entry animations.
                }
                return Promise.resolve([]); // Resolve with an empty array if no entry animations.
            })
            .then((entryResults) => { 
                if (entryResults && entryResults.length > 0) { 
                    WidgetCore.log("ModernWidget: Original element entry animations complete.", 'info');
                }
                // Optional: Cleanup for original elements after entry, if needed.
                // for (const item of outgoingElementsClones) {
                //     if(item.original) {
                //         // item.original.style.removeProperty('position'); 
                //         // item.original.style.removeProperty('z-index');
                //     }
                // }
                WidgetCore.log("ModernWidget: Full song transition sequence finished.", 'info');
            })
            .catch(error => { 
                WidgetCore.log("ModernWidget: Error during song transition animation sequence.", 'error', error);
                // Fallback: Ensure UI is updated even if animations fail.
                updateWidgetUI(newData); 
                for (const entry of outgoingElementsClones) {
                    if (entry.original) entry.original.style.opacity = '1'; // Make sure new content is visible.
                }
            });
    }

    async function handleDataUpdate(newData) {
        // WidgetCore.log('ModernWidget: Veri güncellemesi alındı (handleDataUpdate).', 'debug', newData);
        updateWidgetUI(newData); 
    }

    async function handleError(errorData) { 
        WidgetCore.log('ModernWidget: Hata alındı (handleError).', 'error', errorData);
        updateWidgetUI(null, errorData.message || errorData.error || 'Bilinmeyen bir hata oluştu.');
    }

    // WidgetCore'dan gelen olaylara tepki vermek için event listener'lar (şimdi fonksiyon tanımlarından sonra)
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