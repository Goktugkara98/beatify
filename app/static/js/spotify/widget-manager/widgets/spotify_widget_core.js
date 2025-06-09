/**
 * WidgetCore.js - Spotify Widget Çekirdek Mantığı
 * * Bu modül, Spotify'dan veri çekme, durumu yönetme, şarkı değişikliklerini
 * algılama ve temel widget yaşam döngüsü (aktivasyon, deaktivasyon)
 * olaylarını yönetmekten sorumludur. Arayüzden (UI) bağımsızdır ve
 * herhangi bir widget görünümü (theme) tarafından kullanılabilir.
 */
const WidgetCore = (() => {
    'use strict';

    // =========================
    // LOGGER SINIFI (DETAYLI)
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
            this.prefix = options.prefix || 'WidgetCore';
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
                // Renkli konsol çıktısı
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

    // WidgetCore için logger örneği
    const logger = new Logger({
        activeLevels: ['debug', 'info', 'warn', 'error'],
        memory: true,
        prefix: 'WidgetCore',
        enabled: true
    });

    // ===================================================================================
    // BÖLÜM 1: ÇEKİRDEK DURUM (STATE) VE AYARLAR
    // Bu bölümde, widget'ın çalışması boyunca kullanılacak tüm durum değişkenleri
    // ve yapılandırma ayarları bulunmaktadır.
    // ===================================================================================

    let currentTrackId = null;          // Şu an çalan şarkının kimliği
    let lastFetchedData = null;         // API'den alınan son başarılı veri
    let pollTimeoutId = null;           // API sorgulama zamanlayıcısının kimliği
    let isPollingActive = false;        // API'ye düzenli istek atılıp atılmadığını belirten bayrak
    let isWidgetCurrentlyActive = false; // Widget'ın genel olarak aktif olup olmadığını belirten bayrak
    let progressBarIntervalId = null;   // İlerleme çubuğu animasyonunun zamanlayıcı kimliği
    let currentMockSongIndex = 0;       // Test için kullanılan sahte şarkı listesindeki indeks

    // Widget'ın varsayılan ve kullanıcı tarafından üzerine yazılabilecek ayarları
    let widgetConfig = {
        token: null,
        endpointTemplate: null,
        widgetElement: null,
        minPollInterval: 1000,          // En kısa sorgulama aralığı (ms)
        defaultPollInterval: 1000,      // Şarkı çalarken varsayılan sorgulama aralığı (ms)
        notPlayingPollInterval: 1000,  // Şarkı çalmazken sorgulama aralığı (ms)
        errorPollInterval: 30000,       // Hata durumunda sorgulama aralığı (ms)
        onSongChange: (newData, oldData) => { logger.info('Varsayılan onSongChange tetiklendi.', { newData, oldData }); },
        onDataUpdate: (newData) => { logger.debug('Varsayılan onDataUpdate tetiklendi.', newData); },
        onError: (error) => { logger.error('Varsayılan onError tetiklendi.', error); },
        onActivate: async () => { logger.info('Varsayılan onActivate tetiklendi.'); return Promise.resolve(); },
        onDeactivate: async () => { logger.info('Varsayılan onDeactivate tetiklendi.'); return Promise.resolve(); },
    };

    // ===================================================================================
    // BÖLÜM 2: YARDIMCI FONKSİYONLAR (UTILITIES)
    // Genel amaçlı, tekrar kullanılabilir fonksiyonlar.
    // ===================================================================================

    /**
     * Logger'ı kullanarak detaylı loglama yapar.
     * @param {string} message - Log mesajı
     * @param {string} [level='info'] - Log seviyesi (debug, info, warn, error)
     * @param {*} [data=null] - Ek veri
     */
    function _log(message, level = 'info', data = null) {
        logger.log(message, level, data);
    }

    /**
     * Milisaniyeyi "dakika:saniye" formatına çevirir.
     * @param {number} ms - Milisaniye cinsinden süre
     * @returns {string} Biçimlendirilmiş zaman (örn: "3:45")
     */
    function msToTimeFormat(ms) {
        if (isNaN(ms) || ms === null || ms < 0) return '0:00';
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }

    /**
     * Bir DOM elementinin metin içeriğini ve başlığını günceller.
     * @param {HTMLElement} element - Güncellenecek element
     * @param {string} text - Yeni metin içeriği
     * @param {string} [title] - Elementin yeni başlığı (tooltip)
     */
    function updateTextContent(element, text, title) {
        if (element) {
            element.textContent = text;
            if (title) {
                element.title = title;
            }
        }
    }

    /**
     * Bir <img> elementinin kaynağını güvenli bir şekilde günceller.
     * Hata durumunda isteğe bağlı olarak bir yedek resim gösterir.
     * @param {HTMLImageElement} imgElement - Güncellenecek resim elementi
     * @param {string} newSrc - Yeni resim URL'si
     * @param {string} [placeholderSrc] - Hata durumunda gösterilecek yedek URL
     * @param {Function} [onLoadCallback] - Yükleme tamamlandığında veya hata alındığında çalışacak callback
     */
    function updateImageSource(imgElement, newSrc, placeholderSrc, onLoadCallback) {
        if (!imgElement) return;
        if (imgElement.src === newSrc) {
            if (typeof onLoadCallback === 'function') onLoadCallback(true, newSrc);
            return;
        }
        imgElement.src = newSrc;
        imgElement.onload = () => {
            if (typeof onLoadCallback === 'function') onLoadCallback(true, newSrc);
        };
        imgElement.onerror = () => {
            _log('Resim yüklenirken hata oluştu: ' + newSrc, 'error');
            if (placeholderSrc) {
                imgElement.src = placeholderSrc;
            }
            if (typeof onLoadCallback === 'function') onLoadCallback(false, newSrc);
        };
    }

    /**
     * Hata mesajı elementini gösterir.
     * @param {HTMLElement} errorElement - Hata mesajı elementi
     * @param {string} message - Gösterilecek mesaj
     */
    function showError(errorElement, message) {
        if (errorElement) {
            updateTextContent(errorElement, message);
            errorElement.classList.add('visible');
            errorElement.classList.remove('hidden');
        }
    }

    /**
     * Hata mesajı elementini gizler.
     * @param {HTMLElement} errorElement - Hata mesajı elementi
     */
    function hideError(errorElement) {
        if (errorElement) {
            errorElement.classList.remove('visible');
            errorElement.classList.add('hidden');
        }
    }

    // ===================================================================================
    // BÖLÜM 3: API İLETİŞİMİ VE VERİ YÖNETİMİ
    // Backend ile iletişim kurma, veriyi çekme, işleme ve sorgulama döngüsünü yönetme.
    // ===================================================================================

    /**
     * Belirtilen endpoint'e API isteği göndererek güncel şarkı verisini çeker.
     * @returns {Promise<object>} API'den gelen veri veya bir hata nesnesi.
     */
    async function _fetchData() {
        logger.debug('API veri çekme fonksiyonu çağrıldı.');
        if (!widgetConfig.token || !widgetConfig.endpointTemplate) {
            const errorMsg = `Token veya endpoint template eksik. Token: ${widgetConfig.token ? 'VAR' : 'YOK'}, Endpoint: ${widgetConfig.endpointTemplate || 'YOK'}`;
            _log(errorMsg, 'error');
            return { error: errorMsg };
        }

        let endpoint = widgetConfig.endpointTemplate.replace('{TOKEN}', widgetConfig.token);
        if (endpoint.includes('use_mock=true')) {
            endpoint += `&mock_song_index=${currentMockSongIndex}`;
        }
        
        _log('API isteği gönderiliyor...', 'debug', { endpoint: endpoint.replace(widgetConfig.token, '***TOKEN***') });

        try {
            const startTime = performance.now();
            const response = await fetch(endpoint, {
                method: 'GET',
                headers: { 'Accept': 'application/json', 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' },
                credentials: 'same-origin'
            });
            const responseTime = Math.round(performance.now() - startTime);
            _log(`API yanıtı alındı (${response.status}) - ${responseTime}ms`, 'debug');

            const responseText = await response.text();
            if (!response.ok) {
                const errorData = { message: `API Hatası: ${response.status} ${response.statusText}`, responseText };
                _log('API hatası alındı', 'error', errorData);
                return { error: errorData.message, status: response.status, details: errorData };
            }

            const data = JSON.parse(responseText);
            _log('API yanıtı başarıyla işlendi', 'debug', data);
            return data;
        } catch (error) {
            _log('_fetchData içinde kritik hata.', 'error', error);
            return { error: 'Ağ hatası veya sunucuya ulaşılamıyor.' };
        }
    }

    /**
     * Gelen veriye göre bir sonraki API isteği için bekleme süresini belirler.
     * @param {object} data - API'den gelen veri
     * @param {boolean} [isFetchError=false] - Veri çekilirken hata oluşup oluşmadığı
     * @returns {number} Milisaniye cinsinden bekleme süresi
     */
    function _determinePollInterval(data, isFetchError = false) {
        if (isFetchError) {
            return widgetConfig.errorPollInterval;
        }
        if (!data || !data.is_playing) {
            return widgetConfig.notPlayingPollInterval;
        }
        return widgetConfig.defaultPollInterval;
    }

    /**
     * API'den gelen yeni veriyi işler, şarkı değişikliği olup olmadığını kontrol eder
     * ve ilgili callback'leri tetikler.
     * @param {object} newData - API'den gelen yeni veri
     */
    async function _processNewData(newData) {
        if (!newData || newData.error) {
            _log('Veri işlenirken hata tespit edildi veya veri boş.', 'warn', newData?.error);
            widgetConfig.onError(newData || { error: 'Boş veya tanımsız veri alındı.' });
            return;
        }

        const newTrackIdentifier = newData.item?.id || null;

        if (newTrackIdentifier && newTrackIdentifier !== currentTrackId) {
            const isInitialSong = (currentTrackId === null);
            _log(`Yeni şarkı tespit edildi: ${newData.item.name}`, 'info');
            
            const oldData = { ...lastFetchedData };
            const dataForCallback = isInitialSong ? { ...newData, is_initial_data: true } : newData;

            currentTrackId = newTrackIdentifier;
            lastFetchedData = newData;
            
            await widgetConfig.onSongChange(dataForCallback, oldData);
        } else if (newTrackIdentifier) {
            _log('Aynı şarkı devam ediyor, veri güncelleniyor.', 'debug');
            lastFetchedData = newData;
            await widgetConfig.onDataUpdate(newData);
        } else {
            _log('Alınan veride geçerli bir şarkı kimliği bulunamadı.', 'warn', newData);
        }
    }

    /**
     * Veri çekme döngüsünü (polling) başlatır ve yönetir.
     */
    async function _pollForData() {
        if (!isWidgetCurrentlyActive || !isPollingActive) {
            _log('Polling koşulları sağlanmıyor, atlanıyor.', 'warn', { isWidgetCurrentlyActive, isPollingActive });
            return;
        }
    
        const newData = await _fetchData();
        await _processNewData(newData);
    
        const interval = _determinePollInterval(newData, !!newData?.error);
        _log(`Bir sonraki sorgulama ${interval}ms sonra yapılacak.`, 'debug');
        pollTimeoutId = setTimeout(_pollForData, interval);
    }
    
    // ===================================================================================
    // BÖLÜM 4: İLERLEME ÇUBUĞU YÖNETİMİ
    // ===================================================================================

    /**
     * Şarkının ilerleme çubuğunu ve zaman göstergelerini günceller.
     * @param {HTMLElement} progressBarElement - İlerleme çubuğu elementi
     * @param {HTMLElement} currentTimeElement - Geçen süreyi gösteren element
     * @param {HTMLElement} totalTimeElement - Toplam süreyi gösteren element
     * @param {number} progressMs - Şarkının o anki ilerlemesi (ms)
     * @param {number} durationMs - Şarkının toplam süresi (ms)
     * @param {boolean} isPlaying - Şarkının çalıp çalmadığı
     * @param {Function} [onComplete] - Şarkı bittiğinde çalışacak callback
     */
    function updateProgressBar(progressBarElement, currentTimeElement, totalTimeElement, progressMs, durationMs, isPlaying, onComplete) {
        if (progressBarIntervalId) clearInterval(progressBarIntervalId);

        if (!progressBarElement || !currentTimeElement || !totalTimeElement || isNaN(progressMs) || isNaN(durationMs) || durationMs <= 0) {
            if (progressBarElement) progressBarElement.style.width = '0%';
            if (currentTimeElement) updateTextContent(currentTimeElement, '0:00');
            if (totalTimeElement) updateTextContent(totalTimeElement, '0:00');
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
            progressBarIntervalId = setInterval(() => {
                currentProgress = progressMs + (Date.now() - startTime);
                if (currentProgress >= durationMs) {
                    currentProgress = durationMs;
                    updateDisplay();
                    clearInterval(progressBarIntervalId);
                    if (typeof onComplete === 'function') onComplete();
                } else {
                    updateDisplay();
                }
            }, 1000);
        }
    }
    
    // ===================================================================================
    // BÖLÜM 5: WIDGET YAŞAM DÖNGÜSÜ YÖNETİMİ
    // Widget'ın başlatılması, etkinleştirilmesi, devre dışı bırakılması ve
    // sorgulama döngüsünün kontrolü.
    // ===================================================================================

    /**
     * Sorgulama döngüsünü durdurur.
     */
    function stopPolling() {
        if (pollTimeoutId) clearTimeout(pollTimeoutId);
        isPollingActive = false;
        _log('Polling durduruldu.', 'info');
    }
    
    /**
     * Widget'ı etkinleştirir, onActivate callback'ini çalıştırır ve veri sorgulama döngüsünü başlatır.
     */
    async function activateWidget() {
        logger.info('Widget etkinleştiriliyor...');
        if (isWidgetCurrentlyActive) {
            _log('Widget zaten aktif, activateWidget çağrısı yoksayılıyor.', 'warn');
            return;
        }
        _log('Widget aktive ediliyor...', 'info');
        isWidgetCurrentlyActive = true;

        logger.debug('onActivate callback çağrılıyor.');
        await widgetConfig.onActivate();
        
        isPollingActive = true;
        currentTrackId = null; 
        lastFetchedData = null;
        if (pollTimeoutId) clearTimeout(pollTimeoutId);
        _pollForData(); 
        logger.info('Widget başarıyla etkinleştirildi.');
    }

    /**
     * Widget'ı devre dışı bırakır, onDeactivate callback'ini çalıştırır ve sorgulama döngüsünü durdurur.
     */
    async function deactivateWidget() {
        logger.info('Widget devre dışı bırakılıyor...');
        if (!isWidgetCurrentlyActive) {
            _log('Widget zaten deaktif, deactivateWidget çağrısı yoksayılıyor.', 'warn');
            return;
        }
        _log('Widget deaktive ediliyor...', 'info');

        logger.debug('onDeactivate callback çağrılıyor.');
        await widgetConfig.onDeactivate();
        
        isWidgetCurrentlyActive = false;
        stopPolling();
        _log('Widget başarıyla devre dışı bırakıldı.', 'info');
    }

    /**
     * Widget'ı ilk yapılandırma ayarlarıyla başlatır ve ilk veriyi çeker.
     * @param {object} config - Widget yapılandırma nesnesi
     */
    async function initWidgetBase(config) {
        logger.info('WidgetCore.initWidgetBase çağrıldı.');
        widgetConfig = { ...widgetConfig, ...config };

        if (!widgetConfig.token || !widgetConfig.endpointTemplate || !widgetConfig.widgetElement) {
            const errorMsg = "initWidgetBase için token, endpointTemplate ve widgetElement gereklidir.";
            _log(errorMsg, 'error');
            widgetConfig.onError({error: errorMsg});
            return;
        }

        // Sahte şarkı değiştirme butonu için olay dinleyici (test amaçlı)
        const changeMockSongBtn = document.getElementById('changeMockSongBtn');
        if (changeMockSongBtn && widgetConfig.endpointTemplate.includes('use_mock=true')) {
            changeMockSongBtn.addEventListener('click', async () => {
                currentMockSongIndex++;
                _log(`Mock song index değişti: ${currentMockSongIndex}.`, 'info');
                if (!isWidgetCurrentlyActive) {
                    await activateWidget();
                } else {
                    stopPolling();
                    _pollForData(); // Veriyi anında yenile
                }
            });
        }
        
        _log('İlk veri çekiliyor ve widget aktive ediliyor...', 'info');
        await activateWidget();
    }

    // ===================================================================================
    // BÖLÜM 6: GENEL (PUBLIC) ARAYÜZ
    // Dış dünyaya açılan, widget'ı kontrol etmek için kullanılacak fonksiyonlar.
    // ===================================================================================

    function getLastFetchedData() {
        return lastFetchedData;
    }

    return {
        // Yaşam Döngüsü ve Başlatma
        initWidgetBase,
        activateWidget,
        deactivateWidget,
        stopPolling,
        
        // DOM ve Veri Yardımcıları
        updateProgressBar,
        updateTextContent,
        updateImageSource,
        showError,
        hideError,
        msToTimeFormat,
        getLastFetchedData,
        
        // Loglama
        log: _log
    };
})();
