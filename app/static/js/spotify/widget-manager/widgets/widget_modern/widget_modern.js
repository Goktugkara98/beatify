/**
 * widget_modern.js - New Animation Logic by Cascade
 *
 * Manages dual-set (A/B) element animations for smooth transitions in the Spotify widget.
 * Integrates with WidgetCore for data updates and state management.
 */

// =========================
// LOGGER SINIFI (DETAYLI) - WidgetJS
// =========================
class Logger {
    constructor(options = {}) {
        this.levels = ['debug', 'info', 'warn', 'error'];
        this.colors = {
            debug: 'color: #9e9e9e;',
            info: 'color: #1976d2;',
            warn: 'color: #fbc02d;',
            error: 'color: #d32f2f; font-weight:bold;'
        };
        this.activeLevels = options.activeLevels || this.levels;
        this.memory = options.memory || false;
        this.logs = [];
        this.prefix = options.prefix || 'WidgetJS';
        this.enabled = options.enabled !== undefined ? options.enabled : true;
    }

    setEnabled(val) { this.enabled = !!val; }
    setActiveLevels(levels) { this.activeLevels = levels; }
    clearMemory() { this.logs = []; }
    getLogs() { return this.logs.slice(); }

    _shouldLog(level) {
        return this.enabled && this.activeLevels.includes(level);
    }

    _getTimestamp() {
        return new Date().toISOString();
    }

    log(message, level = 'info', data = null) {
        if (!this._shouldLog(level)) return;
        const timestamp = this._getTimestamp();
        const formatted = `[${timestamp}] [${this.prefix}] [${level.toUpperCase()}] ${message}`;
        if (this.memory) {
            this.logs.push({ timestamp, level, message, data });
        }
        if (data !== null && data !== undefined) {
            console.log(`%c${formatted}`, this.colors[level] || '', data);
        } else {
            console.log(`%c${formatted}`, this.colors[level] || '');
        }
    }
    debug(msg, data) { this.log(msg, 'debug', data); }
    info(msg, data) { this.log(msg, 'info', data); }
    warn(msg, data) { this.log(msg, 'warn', data); }
    error(msg, data) { this.log(msg, 'error', data); }
}

// WidgetJS için logger örneği
const logger = new Logger({
    activeLevels: ['debug', 'info', 'warn', 'error'],
    memory: true,
    prefix: 'WidgetJS',
    enabled: true
});

// Logger'ı fonksiyonel olarak da kullanmak için kısa bir fonksiyon
function logJS(msg, level = 'info', data = null) { logger.log(msg, level, data); }

// =========================
document.addEventListener('DOMContentLoaded', () => {
    'use strict'; // Strict mode

    // Section 1: Module Dependency Check
    if (typeof WidgetCore === 'undefined') {
        logger.error('Modern Widget: WidgetCore not found! Please ensure spotify_widget_core.js is loaded.');
        document.body.insertAdjacentHTML('afterbegin', '<div style="color:red;padding:10px;text-align:center;background:#fff;border:1px solid red;">Widget failed to initialize: Core components missing.</div>');
        return;
    }

    // Section 2: Main Widget Element
    const spotifyWidgetElement = document.getElementById('spotifyWidgetModern');
    if (!spotifyWidgetElement) {
        logger.error("Modern Widget: Main widget element (#spotifyWidgetModern) not found in DOM.");
        return;
    }
    const generalErrorMessageElement = document.getElementById('errorMessage'); // For general, non-UI specific errors

    // 1. Durum (State) Yönetimi
    let currentState = 'a'; // Başlangıçta 'a' seti aktif
    let isAnimating = false;
    
    // Backend'den gelen konfigürasyonu kontrol et
    logger.debug('window.configData:', window.configData); // Tüm configData'yı logla
    
    // Eğer configData yoksa veya boşsa uyarı ver
    if (!window.configData) {
        logger.warn('window.configData tanımlı değil! Backend\'den konfigürasyon gelmiyor olabilir.');
    } else if (!window.configData.animations) {
        logger.warn('window.configData.animations tanımlı değil! Backend\'den animasyon konfigürasyonu gelmiyor.');
    } else {
        logger.debug('Backend\'den gelen animasyon konfigürasyonu:', window.configData.animations);
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
        progressBar: {
            intro: { animation: 'fade-in', duration: 1000, delay: 400 },
            transitionIn: { animation: 'slide-in-right', duration: 1000, delay: 0 },
            transitionOut: { animation: 'slide-out-left', duration: 1000, delay: 0 },
            outro: { animation: 'slide-out-left', duration: 1000, delay: 0 }
        },
        currentTime: {
            intro: { animation: 'fade-in', duration: 1000, delay: 400 },
            transitionIn: { animation: 'slide-in-right', duration: 1000, delay: 0 },
            transitionOut: { animation: 'slide-out-left', duration: 1000, delay: 0 },
            outro: { animation: 'slide-out-left', duration: 1000, delay: 0 }
        },
        totalTime: {
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
        'progressBar': 'progressBar',
        'currentTime': 'currentTime',
        'totalTime': 'totalTime',
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
            logger.error(`ModernWidget: _applyAnimations - Invalid animationTypeKey: ${animationTypeKey}`);
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
                    logger.debug(`ModernWidget: Element ${el.id || el.className} (${animationTypeKey} ${currentSetKeyForLogging}) animation complete. Now active and visible.`);
                } else { // Outgoing
                    el.style.opacity = 0; // Ensure outgoing elements are hidden
                    el.classList.add('passive');
                    logger.debug(`ModernWidget: Element ${el.id || el.className} (${animationTypeKey} ${currentSetKeyForLogging}) animation complete. Now passive and hidden.`);
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

    // Helper function to reset the content of an element set to a blank state
    function resetElementSet(setKey) {
        const suffix = (setKey === 'a') ? '_a' : '_b';
        logger.debug(`ModernWidget: Resetting content for element set '${setKey}'.`);

        const albumArtElement = document.getElementById('albumArt' + suffix);
        const albumArtBackgroundElement = document.getElementById('albumArtBackground' + suffix);
        const trackNameElement = document.getElementById('trackName' + suffix);
        const artistNameElement = document.getElementById('artistName' + suffix);
        const progressBarElement = document.getElementById('progressBar' + suffix);
        const currentTimeElement = document.getElementById('currentTime' + suffix);
        const totalTimeElement = document.getElementById('totalTime' + suffix);

        if (albumArtElement) albumArtElement.src = '';
        if (albumArtBackgroundElement) albumArtBackgroundElement.src = '';
        if (trackNameElement) WidgetCore.updateTextContent(trackNameElement, '');
        if (artistNameElement) WidgetCore.updateTextContent(artistNameElement, '');
        
        // Reset progress bar and timers using the core function with zero values
        if (progressBarElement && currentTimeElement && totalTimeElement) {
            WidgetCore.updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, 0, 0, false);
        }
    }

    // Helper function to update content of an element set
    function updateElementSet(setKey, data) {
        const suffix = (setKey === 'a') ? '_a' : '_b';

        const albumArtElement = document.getElementById('albumArt' + suffix);
        const albumArtBackgroundElement = document.getElementById('albumArtBackground' + suffix);
        const trackNameElement = document.getElementById('trackName' + suffix);
        const artistNameElement = document.getElementById('artistName' + suffix);
        
        // Progress bar ve zaman göstergelerini seç
        const progressBarElement = document.getElementById('progressBar' + suffix);
        const currentTimeElement = document.getElementById('currentTime' + suffix);
        const totalTimeElement = document.getElementById('totalTime' + suffix);
        
        // Aktif setin elementlerini aktif yap
        if (progressBarElement) progressBarElement.classList.remove('passive');
        if (currentTimeElement) currentTimeElement.classList.remove('passive');
        if (totalTimeElement) totalTimeElement.classList.remove('passive');

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

            // Çekirdek fonksiyona tüm işi devret
            if (progressBarElement && currentTimeElement && totalTimeElement) {
                WidgetCore.updateProgressBar(
                    progressBarElement, 
                    currentTimeElement, 
                    totalTimeElement, 
                    progressMs, 
                    durationMs, 
                    isPlaying
                );
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
        logger.debug('ModernWidget: handleSongChange triggered.', { newDataIsInitial: newData?.is_initial_data, isAnimating });
        
        if (isAnimating && !(newData && newData.is_initial_data === true)) {
            logger.warn('ModernWidget: Animation in progress, new song change ignored.');
            return; 
        }

        const activeSetKey = currentState;
        const passiveSetKey = (currentState === 'a') ? 'b' : 'a';
        
        if (newData && newData.is_initial_data === true) {
            logger.info('ModernWidget: Initial data load, playing intro.');
            playIntroAnimation(activeSetKey, newData);
        } else if (newData) { 
            logger.info('ModernWidget: New song data, playing transition.');
            playTransition(activeSetKey, passiveSetKey, newData);
        } else { 
            logger.info('ModernWidget: No new data (song stopped or error), playing outro.');
            playOutroAnimation(activeSetKey);
        }
    }

    function playIntroAnimation(setKey, data) {
        if (spotifyWidgetElement) {
            spotifyWidgetElement.classList.remove('widget-inactive');
            logger.debug('ModernWidget: widget-inactive class removed.');
        }
        isAnimating = true;
        updateElementSet(setKey, data);
        const introElements = elements[setKey];

        // _applyAnimations will handle removing 'passive' and other animation logic
        const longestIntro = _applyAnimations(introElements, 'intro', setKey);

        setTimeout(() => {
            isAnimating = false;
            logger.debug('ModernWidget: Intro animation sequence complete.');
        }, longestIntro);
    }

    function playOutroAnimation(setKey) {
        isAnimating = true;
        const outroElements = elements[setKey];

        // _applyAnimations will handle applying 'passive' class and other animation logic
        const longestOutro = _applyAnimations(outroElements, 'outro', setKey);

        setTimeout(() => {
            isAnimating = false;
            logger.debug('ModernWidget: Outro animation sequence complete.');
            if (spotifyWidgetElement) {
                spotifyWidgetElement.classList.add('widget-inactive');
                logger.debug('ModernWidget: widget-inactive class added.');
            }
        }, longestOutro);
    }

    // 3. Animasyon Orkestrasyonu (Transition)
    // playTransition fonksiyonunu bulun ve aşağıdaki kodla değiştirin.

    function playTransition(activeKey, passiveKey, data) {
        isAnimating = true;
        logger.debug('ModernWidget: playTransition started.', { activeKey, passiveKey });
    
        // 1. Z-index'leri statik 'a' ve 'b' yerine "rol" bazlı tanımla.
        // Bu, hangi setin girdiği veya çıktığından bağımsız olarak mantığın doğru çalışmasını sağlar.
        const zIndexRoles = {
            // EKRANDAN ÇIKAN (eski şarkı) set için z-index değerleri.
            // Bu set her zaman altta kalmalıdır.
            outgoing: {
                'albumArtBackground': '1',
                'albumArt': '2',
                'trackName': '5',
                'artistName': '5',
                'progressBar': '7',
                'currentTime': '7',
                'totalTime': '7',
                'spotifyLogo': '9'
            },
            // EKRANA GİREN (yeni şarkı) set için z-index değerleri.
            // Bu set her zaman üstte olmalıdır.
            incoming: {
                'albumArtBackground': '3',
                'albumArt': '4',
                'trackName': '6',
                'artistName': '6',
                'progressBar': '8',
                'currentTime': '8',
                'totalTime': '8',
                'spotifyLogo': '10'
            }
        };
    
        const activeElements = elements[activeKey];   // Mevcut, ekrandan ÇIKAN elemanlar
        const passiveElements = elements[passiveKey]; // Yeni, ekrana GİREN elemanlar
        resetElementSet(passiveKey);
        // Yeni veriyi pasif (görünmeyen, ekrana GİRECEK olan) elemanlara yükle
        updateElementSet(passiveKey, data);
    
        // 2. Animasyon başlamadan önce z-index'leri rollerine göre uygula.
        // a. Ekranda çıkan (active) elemanlara "outgoing" z-index'lerini ata.
        activeElements.forEach(el => {
            const elementType = el.dataset.type;
            if (elementType && zIndexRoles.outgoing[elementType]) {
                el.style.zIndex = zIndexRoles.outgoing[elementType];
            }
        });
    
        // b. Ekrana giren (passive) elemanlara "incoming" z-index'lerini ata.
        passiveElements.forEach(el => {
            const elementType = el.dataset.type;
            if (elementType && zIndexRoles.incoming[elementType]) {
                el.style.zIndex = zIndexRoles.incoming[elementType];
            }
        });
    
        // 3. Animasyon sonrası z-index'leri temizlemek için callback fonksiyonunu tanımla
        const onElementTransitionComplete = (element) => {
            element.style.zIndex = ''; // z-index'i CSS'teki varsayılan değerine döndür
        };
    
        // 4. Animasyonları, tamamlandığında temizlik yapacak olan callback fonksiyonu ile birlikte başlat
        const longestOutDuration = _applyAnimations(activeElements, 'transitionOut', activeKey, onElementTransitionComplete);
        const longestInDuration = _applyAnimations(passiveElements, 'transitionIn', passiveKey, onElementTransitionComplete);
    
        const longestOverallTransition = Math.max(longestOutDuration, longestInDuration);
    
        // Global durumları ve animasyon kilidini en uzun animasyon bittikten sonra güncelle
        setTimeout(() => {
            currentState = passiveKey; // Aktif seti değiştir
            isAnimating = false;
            logger.debug('ModernWidget: Transition sequence complete. New active set:', currentState);
        }, longestOverallTransition);
    }

    // CORE EVENT HANDLERS (for events other than song change)
    function handleCoreDataUpdate(event) {
        logger.debug('ModernWidget: CoreDataUpdate received.', event.detail.newData);
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
        logger.error('ModernWidget: CoreError received.', errorData);
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
            logger.debug('initWidget: window.configData kontrol ediliyor...');
            
            if (window.configData) {
                logger.debug('initWidget: window.configData mevcut:', window.configData);
                
                if (window.configData.animations) {
                    logger.debug('initWidget: Backend\'den animasyon konfigürasyonu alındı:', window.configData.animations);
                    // Backend'den gelen konfigürasyonu kullanıyoruz, zaten animationConfig değişkeninde mevcut
                } else {
                    logger.warn('initWidget: Backend\'den animasyon konfigürasyonu gelmedi, varsayılanlar kullanılacak');
                }
            } else {
                logger.warn('initWidget: Backend\'den hiç konfigürasyon gelmedi, tüm ayarlar varsayılan değerlerle çalışacak');
            }

            const token = spotifyWidgetElement.dataset.token;
            const endpointTemplate = spotifyWidgetElement.dataset.endpointTemplate;

            if (!token || !endpointTemplate) {
                const errorMsg = "Yapılandırma eksik: 'data-token' veya 'data-endpoint-template' bulunamadı.";
                logger.error("Modern Widget: " + errorMsg);
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
            //if (elements.a.length > 0) {
            //    playIntroAnimation('a', {});
            //}
            
            logger.info('ModernWidget: Initialization complete.');
        } catch (error) {
            logger.error('ModernWidget: Initialization failed:', error);
            if (generalErrorMessageElement) {
                generalErrorMessageElement.textContent = 'Widget başlatılırken bir hata oluştu.';
                generalErrorMessageElement.style.display = 'block';
            }
        }
    }

    initWidget();
});