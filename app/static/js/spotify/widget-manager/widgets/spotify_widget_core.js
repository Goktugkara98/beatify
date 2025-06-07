const WidgetCore = (() => {
    'use strict';

    // 1. ÇEKİRDEK DURUM VE AYARLAR
    let currentTrackId = null;
    let lastFetchedData = null;
    let pollTimeoutId = null;
    let isPollingActive = false;
    let isWidgetCurrentlyActive = false;
    let progressBarIntervalId = null;

    let widgetConfig = {
        token: null,
        endpointTemplate: null,
        widgetElement: null,
        onSongChange: (newData, oldData) => { _log('Varsayılan onSongChange tetiklendi.', { newData, oldData }); },
        onDataUpdate: (newData) => { /* Varsayılan boş, loglama ile izleniyor */ },
        onError: (error) => { _log('Varsayılan onError tetiklendi.', 'error', error); },
        onActivate: async () => { _log('Varsayılan onActivate tetiklendi.'); return Promise.resolve(); },
        onDeactivate: async () => { _log('Varsayılan onDeactivate tetiklendi.'); return Promise.resolve(); },
        minPollInterval: 1500,
        defaultPollInterval: 7000,
        notPlayingPollInterval: 15000,
        errorPollInterval: 30000
    };

    // 2. LOGLAMA VE YARDIMCI FONKSİYONLAR
    function _log(message, level = 'log', data = null) {
        const prefix = 'WidgetCore:';
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

    // 3. VERİ YÖNETİMİ VE SORGULAMA
    async function _fetchData() {
        if (!widgetConfig.token || !widgetConfig.endpointTemplate) {
            const errorMsg = `Token veya endpoint template eksik. Token: ${widgetConfig.token ? 'VAR' : 'YOK'}, Endpoint: ${widgetConfig.endpointTemplate || 'YOK'}`;
            _log(errorMsg, 'error');
            return { error: errorMsg };
        }

        let endpoint = widgetConfig.endpointTemplate.replace('{TOKEN}', widgetConfig.token);

        // Mock modu için endpoint'i kontrol et ve gerekirse 'use_mock=true' ekle
        // Bu, endpointTemplate'in kendisinde bir işaretçi (örneğin '?mock' veya '&mock') içermesine dayanır.
        // VEYA global bir mock flag'i de kullanılabilir.
        // Şimdilik, endpointTemplate'de '?use_mock=true' veya '&use_mock=true' olup olmadığını kontrol edelim.
        // Eğer widget_modern.html'deki DATA_ENDPOINT_TEMPLATE'e ?use_mock=true eklersek, bu kısım otomatik çalışır.
        // Daha sağlam bir çözüm için, widgetConfig'e bir `useMock` boolean eklenebilir ve burada kontrol edilebilir.

        // Eğer endpointTemplate zaten use_mock içeriyorsa, bu blok atlanacak.
        // Eğer widgetConfig.useMock gibi bir bayrak olsaydı, o zaman şöyle yapardık:
        // if (widgetConfig.useMock) {
        //     endpoint += (endpoint.includes('?') ? '&' : '?') + 'use_mock=true';
        // }
        // Şimdilik, HTML'den gelen template'in doğru ayarlandığını varsayıyoruz.
        const requestDetails = {
            endpoint: endpoint.replace(widgetConfig.token, '***TOKEN***'),
            method: 'GET',
            headers: { 'Accept': 'application/json', 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' },
            credentials: 'same-origin'
        };

        _log('API isteği gönderiliyor...', 'debug', requestDetails);
        
        try {
            const startTime = performance.now();
            const response = await fetch(endpoint, {
                method: 'GET',
                headers: { 'Accept': 'application/json', 'Cache-Control': 'no-cache', 'Pragma': 'no-cache' },
                credentials: 'same-origin'
            });
            const responseTime = Math.round(performance.now() - startTime);

            _log(`API yanıtı alındı (${response.status} ${response.statusText}) - ${responseTime}ms`, 'debug');

            const responseText = await response.text();
            
            if (!response.ok) {
                let errorData;
                try {
                    errorData = responseText ? JSON.parse(responseText) : { message: 'Empty response' };
                } catch (e) {
                    errorData = { message: `HTTP ${response.status} - ${response.statusText}`, responseText: responseText };
                }
                _log('API hatası alındı', 'error', { status: response.status, errorData });
                return { error: `API hatası: ${response.status} ${response.statusText}`, status: response.status, details: errorData };
            }

            let data;
            try {
                data = responseText ? JSON.parse(responseText) : {};
                _log('API yanıtı başarıyla ayrıştırıldı', 'debug', data);
            } catch (parseError) {
                _log('API yanıtı JSON olarak ayrıştırılamadı', 'error', { error: parseError.toString(), responseText });
                return { error: 'Geçersiz JSON yanıtı', parseError: parseError.toString(), responseText: responseText };
            }

            return data;
        } catch (error) {
            _log('_fetchData içinde kritik hata.', 'error', error);
            return { error: 'Ağ hatası veya sunucuya ulaşılamıyor.' };
        }
    }

    function _determinePollInterval(data, isFetchError = false) {
        if (isFetchError) {
            _log(`Hata nedeniyle sorgulama aralığı ${widgetConfig.errorPollInterval}ms olarak ayarlandı.`, 'warn');
            return widgetConfig.errorPollInterval;
        }
        if (!data || !data.track_name || (typeof data.is_playing === 'boolean' && !data.is_playing)) {
             _log(`Çalan şarkı yok, sorgulama aralığı ${widgetConfig.notPlayingPollInterval}ms olarak ayarlandı.`, 'info');
            return widgetConfig.notPlayingPollInterval;
        }
        if (typeof data.is_playing !== 'boolean') {
             _log(`is_playing durumu belirsiz, sorgulama aralığı ${widgetConfig.notPlayingPollInterval}ms olarak ayarlandı.`, 'warn');
            return widgetConfig.notPlayingPollInterval;
        }
        _log(`Varsayılan sorgulama aralığı ${widgetConfig.defaultPollInterval}ms kullanılıyor.`, 'info');
        return widgetConfig.defaultPollInterval;
    }

    async function _processNewData(newData) {
        _log('Yeni veri işleme süreci başladı.', 'debug', { hasData: !!newData, hasError: !!(newData && newData.error) });

        if (newData && !newData.error) {
            // Backend'den gelen 'track_url' veya 'item.id' alanını birincil kimlik olarak kullan
            const newTrackIdentifier = newData.track_url || newData.item?.id || null;

            _log('Yeni veri analizi:', 'debug', {
                newTrackIdentifier,
                currentTrackId,
                isSameTrack: newTrackIdentifier === currentTrackId
            });

            if (newTrackIdentifier && newTrackIdentifier !== currentTrackId) {
                _log('Yeni şarkı tespit edildi. Callback tetikleniyor.', 'info', { 
                    previousTrackId: currentTrackId, 
                    newTrackId: newTrackIdentifier,
                    trackName: newData.item?.name || newData.track_name
                });
                
                const oldData = { ...lastFetchedData };
                lastFetchedData = newData;
                currentTrackId = newTrackIdentifier;
                
                if (typeof widgetConfig.onSongChange === 'function') {
                    _log('onSongChange callback çağrılıyor...', 'debug');
                    try {
                        await widgetConfig.onSongChange(newData, oldData);
                        _log('onSongChange callback başarıyla tamamlandı.', 'debug');
                    } catch (error) {
                        _log('onSongChange callback hatası:', 'error', { error: error.toString(), stack: error.stack });
                    }
                }
            } else if (newTrackIdentifier) {
                _log('Aynı şarkı devam ediyor, veri güncelleniyor.', 'debug', { trackId: newTrackIdentifier });
                
                lastFetchedData = newData;
                if (typeof widgetConfig.onDataUpdate === 'function') {
                    _log('onDataUpdate callback çağrılıyor...', 'debug');
                    try {
                        await widgetConfig.onDataUpdate(newData);
                        _log('onDataUpdate callback başarıyla tamamlandı.', 'debug');
                    } catch (error) {
                        _log('onDataUpdate callback hatası:', 'error', { error: error.toString(), stack: error.stack });
                    }
                }
            } else {
                 _log('Alınan veride geçerli bir şarkı kimliği bulunamadı.', 'warn', newData);
            }
        } else if (newData && newData.error) {
            _log('Veri işlenirken hata tespit edildi.', 'warn', newData.error);
            if (typeof widgetConfig.onError === 'function') {
                widgetConfig.onError(newData);
            }
        } else {
             _log('İşlenecek geçerli bir veri yok veya veri boş.', 'warn');
             if (typeof widgetConfig.onError === 'function') {
                widgetConfig.onError({error: 'Boş veya tanımsız veri alındı.'});
            }
        }
    }

    async function _pollForData() {
        if (!isWidgetCurrentlyActive || !isPollingActive) {
            _log('Polling koşulları sağlanmıyor, atlanıyor.', 'warn', { isWidgetCurrentlyActive, isPollingActive });
            return;
        }
    
        _log('Yeni veri için sorgulama yapılıyor...', 'debug');
        const newData = await _fetchData();
        
        _log('Veri çekme tamamlandı, _processNewData çağrılıyor.', 'debug');
        await _processNewData(newData);
    
        const fetchErrorOccurred = !!(newData && newData.error);
        const interval = _determinePollInterval(newData, fetchErrorOccurred);
        
        _log(`Bir sonraki sorgulama ${interval}ms sonra yapılacak.`, 'debug');
        pollTimeoutId = setTimeout(_pollForData, interval);
    }
    
    async function _initiateFirstFetchAndActivate() {
        _log('İlk veri çekme ve aktivasyon süreci başladı.', 'info');
        const initialData = await _fetchData();

        if (initialData && !initialData.error) {
            _log('İlk veri başarıyla çekildi.', 'info');
            
            // İlk veriyi doğrudan işle, bu işlem currentTrackId ve lastFetchedData'yı ayarlayacak.
            await _processNewData(initialData);

            // Widget'ı 'aktif' olarak işaretle ve onActivate callback'ini çalıştır.
            await activateWidget(true); 
        } else {
            const errorMsg = initialData?.error || 'Bilinmeyen bir hata nedeniyle ilk veri çekilemedi.';
            _log(`İlk veri çekme sırasında hata: ${errorMsg}`, 'error', initialData);
            if (typeof widgetConfig.onError === 'function') {
                widgetConfig.onError({ error: errorMsg, details: initialData });
            }
            _log('İlk veri çekilemediği için widget deaktif kalacak.', 'warn');
        }
    }

    // 4. DIŞA AÇIK KONTROL FONKSİYONLARI
    async function initWidgetBase(config) {
        _log('WidgetCore.initWidgetBase çağrıldı.', 'info');
        widgetConfig = { ...widgetConfig, ...config };

        _log('Widget yapılandırma detayları:', 'debug', {
            config: { ...widgetConfig, token: widgetConfig.token ? '***SET***' : 'MISSING' }
        });

        if (!widgetConfig.token || !widgetConfig.endpointTemplate || !widgetConfig.widgetElement) {
            const errorMsg = "initWidgetBase için token, endpointTemplate ve widgetElement gereklidir.";
            _log(errorMsg, 'error');
            if(typeof widgetConfig.onError === 'function') widgetConfig.onError({error: errorMsg});
            return;
        }
        
        if (isPollingActive) {
            _log("Polling zaten aktif. Durdurulup yeniden başlatılıyor.", 'warn');
            stopPolling();
        }

        _initiateFirstFetchAndActivate().catch(error => {
            _log('İlk veri çekme işleminde beklenmeyen kritik hata:', 'error', error);
        });
    }

    function stopPolling(calledInternally = false) {
        if (pollTimeoutId) clearTimeout(pollTimeoutId);
        isPollingActive = false;
        _log(`Polling ${calledInternally ? 'dahili olarak' : 'manuel'} durduruldu.`, 'info');
    }

    // 5. İLERLEME ÇUBUĞU YÖNETİMİ
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
            progressBarIntervalId = setInterval(() => {
                const elapsedSinceLastSync = Date.now() - startTime;
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
    
    // 6. MODÜL DIŞA AKTARIMI
    async function activateWidget(isInitialActivation = false) {
        if (isWidgetCurrentlyActive) {
            _log('Widget zaten aktif, activateWidget çağrısı yoksayılıyor.', 'warn');
            return;
        }
        _log(`Widget aktive ediliyor... (${isInitialActivation ? 'otomatik ilk' : 'manuel'})`, 'info');
        isWidgetCurrentlyActive = true;

        if (typeof widgetConfig.onActivate === 'function') {
            _log('onActivate callback çağrılıyor...', 'debug');
            try {
                await widgetConfig.onActivate();
                _log('onActivate callback tamamlandı.', 'debug');
            } catch (error) {
                _log('onActivate callback sırasında hata.', 'error', error);
            }
        }
        
        isPollingActive = true;

        if (isInitialActivation) {
            _log('İlk aktivasyon: Polling zamanlanıyor...', 'debug');
            const interval = _determinePollInterval(lastFetchedData, (lastFetchedData && lastFetchedData.error));
            pollTimeoutId = setTimeout(_pollForData, interval);
        } else {
            _log('Manuel aktivasyon: Polling hemen başlatılıyor...', 'debug');
            currentTrackId = null; 
            lastFetchedData = null;
            if (pollTimeoutId) clearTimeout(pollTimeoutId);
            _pollForData(); 
        }
    }

    async function deactivateWidget() {
        if (!isWidgetCurrentlyActive) {
            _log('Widget zaten deaktif, deactivateWidget çağrısı yoksayılıyor.', 'warn');
            return;
        }
        _log('Widget deaktive ediliyor...', 'info');

        if (typeof widgetConfig.onDeactivate === 'function') {
             _log('onDeactivate callback çağrılıyor...', 'debug');
            try {
                await widgetConfig.onDeactivate();
                _log('onDeactivate callback tamamlandı.', 'debug');
            } catch (error) {
                _log('onDeactivate callback sırasında hata.', 'error', error);
            }
        }
        
        isWidgetCurrentlyActive = false;
        if (isPollingActive) {
            stopPolling(true);
        }
        _log('Widget başarıyla deaktive edildi.', 'info');
    }

    function getLastFetchedData() {
        return lastFetchedData;
    }

    return {
        initWidgetBase,
        activateWidget,
        deactivateWidget,
        updateProgressBar,
        showError,
        hideError,
        stopPolling,
        updateTextContent,
        updateImageSource,
        msToTimeFormat,
        getLastFetchedData,
        log: _log
    };
})();
