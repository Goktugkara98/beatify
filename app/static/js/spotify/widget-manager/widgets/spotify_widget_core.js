/**
 * spotify_widget_core.js (Backend Veri Yapısına Uyumlu Son Versiyon)
 *
 * Tüm Spotify widget'ları için ortak temel işlevleri içeren modüler yapı.
 * Sorumluluklar:
 * - Widget yaşam döngüsünü yönetme (Giriş animasyonu, veri çekme).
 * - Backend'den veri çekme ve periyodik sorgulama (polling).
 * - İlk yükleme ile gerçek şarkı değişikliklerini ayırt etme ve widget'a bildirme.
 * - Temel DOM manipülasyon yardımcıları.
 * - Detaylı loglama ile genel animasyon tetikleme mekanizması.
 * - İlerleme çubuğu yönetimi.
 */
const WidgetCore = (() => {
    'use strict';

    // -------------------------------------------------------------------------
    // 1. ÇEKİRDEK DURUM VE AYARLAR (CORE STATE & CONFIGURATION)
    // -------------------------------------------------------------------------
    let currentTrackId = null; // Artık track_url'i tutacak
    let lastFetchedData = null;
    let pollTimeoutId = null;
    let isPollingActive = false;
    let progressBarIntervalId = null;

    let widgetConfig = {
        token: null,
        endpointTemplate: null,
        widgetElement: null,
        introAnimationClass: null,
        transitionAnimationClass: null,
        onSongChange: (newData, oldData) => { _log('Varsayılan onSongChange tetiklendi.', { newData, oldData }); },
        onDataUpdate: (newData) => { /* Detaylı loglama için devre dışı bırakıldı. */ },
        onError: (error) => { _log('Varsayılan onError tetiklendi.', 'error', error); },
        minPollInterval: 1500,
        defaultPollInterval: 7000,
        notPlayingPollInterval: 15000,
        errorPollInterval: 30000
    };

    // -------------------------------------------------------------------------
    // 2. LOGLAMA VE YARDIMCI FONKSİYONLAR (LOGGER & UTILITY FUNCTIONS)
    // -------------------------------------------------------------------------
    function _log(message, level = 'log', data = null) {
        const prefix = 'Core:';
        const fullMessage = `${prefix} ${message}`;
        if (data !== null && data !== undefined) {
            console[level](fullMessage, data);
        } else {
            console[level](fullMessage);
        }
    }
    function msToTimeFormat(ms) {
        if (isNaN(ms) || ms === null || ms < 0) return '0:00';
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }
    function updateTextContent(element, text, title) {
        if (element) {
            element.textContent = text;
            if (title) {
                element.title = title;
            }
        }
    }
    function updateImageSource(imgElement, newSrc, placeholderSrc, onLoadCallback) {
        if (imgElement) {
            if (imgElement.src === newSrc && imgElement.dataset.loadedOnce === 'true' && imgElement.style.opacity !== '0') {
                if (typeof onLoadCallback === 'function') onLoadCallback(true, newSrc);
                return;
            }
            imgElement.style.opacity = '0';
            const tempImage = new Image();
            tempImage.onload = () => {
                imgElement.src = newSrc;
                imgElement.style.opacity = '1';
                imgElement.dataset.loadedOnce = 'true';
                if (typeof onLoadCallback === 'function') onLoadCallback(true, newSrc);
            };
            tempImage.onerror = () => {
                _log(`Resim yüklenemedi: ${newSrc}. Placeholder kullanılıyor.`, 'warn');
                imgElement.src = placeholderSrc;
                imgElement.style.opacity = '1';
                imgElement.dataset.loadedOnce = 'true';
                if (typeof onLoadCallback === 'function') onLoadCallback(false, placeholderSrc);
            };
            tempImage.src = newSrc;
        }
    }
    function showError(errorElement, message) {
        if (errorElement) {
            updateTextContent(errorElement, message);
            errorElement.classList.add('visible');
            errorElement.classList.remove('hidden');
        }
    }
    function hideError(errorElement) {
        if (errorElement) {
            errorElement.classList.remove('visible');
            errorElement.classList.add('hidden');
        }
    }

    // -------------------------------------------------------------------------
    // 3. VERİ YÖNETİMİ VE SORGULAMA (DATA MANAGEMENT & POLLING)
    // -------------------------------------------------------------------------
    async function _fetchData() {
        if (!widgetConfig.token || !widgetConfig.endpointTemplate) {
            const errorMsg = 'Token veya endpoint şablonu yapılandırılmamış.';
            return { error: errorMsg };
        }
        const apiUrl = widgetConfig.endpointTemplate.replace('{TOKEN}', widgetConfig.token);
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                let errorData;
                try { errorData = await response.json(); } catch (e) { errorData = { message: `HTTP ${response.status} - ${response.statusText}` }; }
                return { error: errorData.message || errorData.error || `Sunucudan ${response.status} koduyla yanıt alındı.` };
            }
            return await response.json();
        } catch (error) {
            _log('_fetchData içinde kritik hata.', 'error', error);
            return { error: 'Ağ hatası veya sunucuya ulaşılamıyor.' };
        }
    }

    // ########### GÜNCELLENEN FONKSİYON ###########
    function _determinePollInterval(data, isFetchError = false) {
        if (isFetchError) {
            return widgetConfig.errorPollInterval;
        }
        if (!data || !data.track_name || (typeof data.is_playing === 'boolean' && !data.is_playing)) {
            return widgetConfig.notPlayingPollInterval;
        }
        if (typeof data.is_playing !== 'boolean') {
            return widgetConfig.notPlayingPollInterval;
        }
    
        // --- DEĞİŞİKLİK BURADA ---
        // Akıllı sorgulama kısmını geçici olarak devre dışı bırakmak için:
        /*
        if (typeof data.duration_ms === 'number' && typeof data.progress_ms === 'number' && data.duration_ms > 0) {
            const remainingTimeMs = data.duration_ms - data.progress_ms;
            return Math.max(widgetConfig.minPollInterval, remainingTimeMs + 1500);
        }
        */
        
        // Her zaman varsayılan aralıkla (örn: 7 saniye) devam etmesini sağla.
        return widgetConfig.defaultPollInterval;
    }

    async function _pollForData() {
        if (!isPollingActive) return;
    
        const newData = await _fetchData();
        let fetchErrorOccurred = false;
    
        if (newData && !newData.error) {
            if (typeof widgetConfig.onDataUpdate === 'function') {
                widgetConfig.onDataUpdate(newData);
            }
            
            const newTrackIdentifier = newData.track_url || null;
    
            if (newTrackIdentifier && newTrackIdentifier !== currentTrackId) {
                const isInitialLoad = (currentTrackId === null);
                
                if (isInitialLoad) {
                    _log(`İlk şarkı verisi ayarlandı. Kimlik (URL): ${newTrackIdentifier}`, 'info');
                } else {
                    _log(`Gerçek şarkı değişikliği algılandı! Kimlik (URL) değişti.`, 'info', {
                        old: currentTrackId,
                        new: newTrackIdentifier
                    });
                    
                    const oldDataToPass = lastFetchedData || { id: currentTrackId };
                    if (typeof widgetConfig.onSongChange === 'function') {
                        widgetConfig.onSongChange(newData, oldDataToPass);
                    }
                }
                
                currentTrackId = newTrackIdentifier;
            }
    
            lastFetchedData = newData;
    
        } else if (newData && newData.error) {
            fetchErrorOccurred = true;
            _log('Sorgulama sırasında hata oluştu.', 'warn', newData.error);
            if (typeof widgetConfig.onError === 'function') {
                widgetConfig.onError(newData);
            }
        }
    
        const interval = _determinePollInterval(newData, fetchErrorOccurred);

        // YENİ DEBUG LOG'U:
        // Bu log, bir sonraki isteğin ne kadar süre sonra yapılacağını ve o anki verinin ne olduğunu gösterir.
        _log(`Bir sonraki sorgulama için aralık ayarlandı: ${interval}ms`, 'warn', { data: newData });

        pollTimeoutId = setTimeout(_pollForData, interval);
    }

    async function initWidgetBase(config) {
        _log('Widget başlatılıyor... (Core)');
        widgetConfig = { ...widgetConfig, ...config };

        if (!widgetConfig.token || !widgetConfig.endpointTemplate || !widgetConfig.widgetElement) {
            const errorMsg = "initWidgetBase için token, endpointTemplate ve widgetElement gereklidir.";
            _log(errorMsg, 'error');
            if(typeof widgetConfig.onError === 'function') widgetConfig.onError({error: errorMsg});
            return;
        }

        _log('Widget yapılandırması tamamlandı.', 'info', { token: '********' });

        if (widgetConfig.introAnimationClass) {
            _log('Giriş animasyonu Core tarafından tetikleniyor...', 'info');
            await playIntroAnimation(widgetConfig.widgetElement, widgetConfig.introAnimationClass);
            _log('Giriş animasyonu Core tarafından tamamlandı.', 'info');
        } else {
            _log('Giriş animasyonu tanımlanmamış, atlanıyor.', 'info');
        }
        
        if (isPollingActive) {
            _log("Polling zaten aktif. Durdurulup yeniden başlatılıyor.", 'warn');
            stopPolling();
        }
        isPollingActive = true;
        currentTrackId = null;
        lastFetchedData = null;
        
        _log('Polling başlatılıyor (Core)...', 'info');
        _pollForData();
        _log("Polling başlatıldı. (Core)");
    }

    function stopPolling() {
        if (pollTimeoutId) {
            clearTimeout(pollTimeoutId);
            pollTimeoutId = null;
        }
        if(progressBarIntervalId) {
            clearInterval(progressBarIntervalId);
            progressBarIntervalId = null;
        }
        isPollingActive = false;
        _log("Polling durduruldu. (Core)");
    }
    
    // -------------------------------------------------------------------------
    // 4. ANİMASYON YÖNETİMİ (ANIMATION MANAGEMENT)
    // -------------------------------------------------------------------------
    function triggerAnimation(element, animationClass) {
        return new Promise((resolve) => {
            if (!element || !animationClass) {
                resolve();
                return;
            }
            const elementId = element.id ? `#${element.id}` : 'IDsiz Element';
            _log(`Animasyon başlatıldı (Core): [${animationClass}] -> ${elementId}`, 'info', { element: element });
            const handleAnimationEnd = (event) => {
                if (event.target === element) {
                    element.classList.remove(animationClass);
                    element.removeEventListener('animationend', handleAnimationEnd);
                    resolve();
                }
            };
            element.addEventListener('animationend', handleAnimationEnd);
            element.classList.add(animationClass);
        });
    }
    function playIntroAnimation(element, specificIntroAnimationClass) {
        return triggerAnimation(element, specificIntroAnimationClass);
    }
    function playSongTransitionAnimation(element, specificTransitionAnimationClass) {
        return triggerAnimation(element, specificTransitionAnimationClass);
    }
    function playOutroAnimation(element, specificOutroAnimationClass) {
        return triggerAnimation(element, specificOutroAnimationClass);
    }
    
    // -------------------------------------------------------------------------
    // 5. İLERLEME ÇUBUĞU YÖNETİMİ (PROGRESS BAR MANAGEMENT)
    // -------------------------------------------------------------------------
    function updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, progressMs, durationMs, isPlaying, onComplete) {
        if (progressBarIntervalId) {
            clearInterval(progressBarIntervalId);
            progressBarIntervalId = null;
        }
        if (!progressBarElement || !currentTimeElement || !totalTimeElement || isNaN(progressMs) || isNaN(durationMs) || durationMs <= 0) {
            if(progressBarElement) progressBarElement.style.width = '0%';
            if(currentTimeElement) updateTextContent(currentTimeElement, msToTimeFormat(0));
            if(totalTimeElement) updateTextContent(totalTimeElement, msToTimeFormat(0));
            return;
        }
        let currentProgress = Math.max(0, Math.min(progressMs, durationMs));
        const updateDisplay = () => {
            const percentage = (currentProgress / durationMs) * 100;
            progressBarElement.style.width = `${percentage}%`;
            updateTextContent(currentTimeElement, msToTimeFormat(currentProgress));
        };
        updateTextContent(totalTimeElement, msToTimeFormat(durationMs));
        updateDisplay();
        if (isPlaying && currentProgress < durationMs) {
            const startTime = Date.now();
            let elapsedSinceLastSync = 0;
            progressBarIntervalId = setInterval(() => {
                elapsedSinceLastSync = Date.now() - startTime;
                currentProgress = progressMs + elapsedSinceLastSync;
                if (currentProgress >= durationMs) {
                    currentProgress = durationMs;
                    updateDisplay();
                    clearInterval(progressBarIntervalId);
                    progressBarIntervalId = null;
                    if (typeof onComplete === 'function') {
                        onComplete();
                    }
                } else {
                    updateDisplay();
                }
            }, 1000);
        }
    }

    // -------------------------------------------------------------------------
    // 6. SAYFA YAŞAM DÖNGÜSÜ (PAGE LIFECYCLE)
    // -------------------------------------------------------------------------
    function setupPageUnloadAnimation(animatedElement, outroAnimationClass) {
        if (!animatedElement || !outroAnimationClass) return;
        window.addEventListener('beforeunload', function (event) {
            playOutroAnimation(animatedElement, outroAnimationClass);
        });
    }

    // -------------------------------------------------------------------------
    // 7. MODÜL DIŞA AKTARIMI (MODULE EXPORTS)
    // -------------------------------------------------------------------------
    return {
        initWidgetBase,
        stopPolling,
        msToTimeFormat,
        updateTextContent,
        updateImageSource,
        showError,
        hideError,
        updateProgressBar,
        setupPageUnloadAnimation,
        playIntroAnimation,
        playSongTransitionAnimation,
        playOutroAnimation,
        log: _log,
    };

})();