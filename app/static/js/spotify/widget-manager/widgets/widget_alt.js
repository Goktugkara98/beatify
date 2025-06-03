// widget_alt.js
document.addEventListener('DOMContentLoaded', () => {
    // Yeni HTML element referansları
    const spotifyWidgetElement = document.getElementById('spotifyWidgetAlt');
    const albumArtElement = document.getElementById('albumArtAlt');
    const albumArtBackgroundElement = document.getElementById('albumArtBackgroundAlt');
    const trackNameElement = document.getElementById('trackNameAlt');
    const artistNameElement = document.getElementById('artistNameAlt');
    
    const progressCircleElement = document.getElementById('progressCircle');
    const currentTimeElement = document.getElementById('currentTimeAlt');
    const totalTimeElement = document.getElementById('totalTimeAlt');
    const errorMessageElement = document.getElementById('errorMessageAlt');

    const playPauseOverlay = document.getElementById('playPauseOverlay');
    const playPauseIcon = document.getElementById('playPauseIcon');
    
    const albumDiscContainer = document.querySelector('.album-disc-container');


    let currentTrackData = null;
    let progressInterval = null;
    let fetchTimeoutId = null;
    let _isPlaying = false;
    let WIDGET_TOKEN = window.WIDGET_TOKEN || null;
    let lastTrackId = null;
    let lastAlbumArt = null;

    const circleRadius = progressCircleElement ? parseFloat(progressCircleElement.r.baseVal.value) : 0;
    const circumference = 2 * Math.PI * circleRadius;
    if(progressCircleElement) {
        progressCircleElement.style.strokeDasharray = circumference;
        progressCircleElement.style.strokeDashoffset = circumference;
    }


    // Token alma işlemi
    console.log('Widget token aranıyor (alternatif tasarım)...');
    
    if (!WIDGET_TOKEN) {
        // URL'den token almayı dene
        const pathParts = window.location.pathname.split('/');
        const widgetPathIndex = pathParts.findIndex(part => part === 'widget');
        if (widgetPathIndex !== -1 && pathParts.length > widgetPathIndex + 1) {
            WIDGET_TOKEN = pathParts[widgetPathIndex + 1];
            console.log('Token URL path\'ten alındı:', WIDGET_TOKEN);
        }
    }
    
    if (!WIDGET_TOKEN) {
        console.error('Widget token bulunamadı! Widget çalıştırılamıyor.');
        if(errorMessageElement) {
            errorMessageElement.textContent = 'Widget token bulunamadı.';
            showError('Widget token bulunamadı.');
        }
        if(spotifyWidgetElement) spotifyWidgetElement.classList.add('opacity-50', 'pointer-events-none');
        return; 
    }
    console.log('Kullanılacak Widget Token (Alternatif):', WIDGET_TOKEN);

    function msToTimeFormat(ms) {
        if (isNaN(ms) || ms < 0) return '0:00';
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }

    async function fetchCurrentlyPlayingData() {
        if (!WIDGET_TOKEN) return;
        if (fetchTimeoutId) clearTimeout(fetchTimeoutId);

        try {
            // API endpoint'i kullan
            const apiUrl = window.DATA_ENDPOINT || `/spotify/api/widget-data/${WIDGET_TOKEN}`;
            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                console.error('Veri çekme hatası:', response.status, errorData);
                let userMessage = 'Veri alınamadı veya çalınan bir şey yok.';
                if (response.status === 401 || response.status === 403) userMessage = "Yetkilendirme hatası. Token geçersiz olabilir.";
                else if (response.status === 404 && errorData && errorData.error === "Widget not found or token invalid") userMessage = "Widget bulunamadı veya token geçersiz.";
                else if (errorData && errorData.error) userMessage = errorData.error;
                
                showError(userMessage);
                updateUI(null);
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000); // 15 saniye
                return;
            }

            const data = await response.json();
            
            if (data && (data.is_playing !== undefined || (data.item && data.item.name))) {
                currentTrackData = data;
                _isPlaying = data.is_playing;
                updateUI(data);
                hideError();
                const refreshInterval = _isPlaying ? 7000 : 15000;
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, refreshInterval);
            } else if (data && data.error) {
                console.error('API Hatası:', data.error);
                const displayError = data.error === "Player command failed: No active device found" ? 
                                     "Aktif bir cihaz bulunamadı." : 
                                     (data.error.message || data.error || "Bilinmeyen bir API hatası oluştu.");
                showError(displayError);
                updateUI(null);
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000);
            }
             else {
                console.log('Çalınan bir şey yok veya veri formatı beklenmiyor.', data);
                // Eğer `is_playing` false ise ve `item` null ise, bu bir "çalınan bir şey yok" durumu.
                // Bu durumda hata göstermek yerine UI'ı "çalınmıyor" durumuna getirmek daha iyi.
                if (data && data.is_playing === false && data.item === null) {
                     updateUI(data); // UI'ı "çalınmıyor" olarak güncelle
                     hideError(); // Hata mesajı varsa gizle
                } else {
                    showError('Şu anda çalınan bir şey yok.');
                    updateUI(null); // UI'ı boş duruma getir
                }
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000);
            }

        } catch (error) {
            console.error('fetchCurrentlyPlayingData içinde kritik hata:', error);
            showError('Widget verileri güncellenemedi (Ağ hatası?).');
            updateUI(null);
            fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 20000);
        }
    }

    function updateUI(data) {
        if (data && (data.item || data.track_name)) {
            const trackName = data.item ? data.item.name : (data.track_name || "Bilinmiyor");
            const artistName = data.item && data.item.artists ? data.item.artists.map(artist => artist.name).join(', ') : (data.artist_name || "-");
            let albumImageUrl = 'https://placehold.co/200x200/121212/444444?text=Beatify';
            if (data.item && data.item.album && data.item.album.images && data.item.album.images.length > 0) {
                albumImageUrl = data.item.album.images.reduce((prev, curr) => {
                    return (Math.abs(curr.width - 300) < Math.abs(prev.width - 300) ? curr : prev);
                }).url || data.item.album.images[0].url;
            } else if (data.album_image_url) {
                albumImageUrl = data.album_image_url;
            }

            if (trackNameElement) {
                trackNameElement.textContent = trackName;
                trackNameElement.title = trackName;
            }
            if (artistNameElement) {
                artistNameElement.textContent = artistName;
                artistNameElement.title = artistName;
            }

            if (albumArtElement && albumArtElement.src !== albumImageUrl) {
                albumArtElement.style.opacity = '0';
                if (albumArtBackgroundElement) albumArtBackgroundElement.style.opacity = '0';
                
                setTimeout(() => {
                    albumArtElement.src = albumImageUrl;
                    if (albumArtBackgroundElement) albumArtBackgroundElement.style.backgroundImage = `url(${albumImageUrl})`;
                    
                    albumArtElement.onload = () => {
                        albumArtElement.style.opacity = '1';
                         if (albumArtBackgroundElement) {
                            albumArtBackgroundElement.style.opacity = '0.3'; // Arka plan için daha düşük opaklık
                        }
                    }
                    albumArtElement.onerror = () => {
                        const errorPlaceholder = 'https://placehold.co/200x200/121212/444444?text=Hata';
                        albumArtElement.src = errorPlaceholder;
                        if (albumArtBackgroundElement) albumArtBackgroundElement.style.backgroundImage = `url(${errorPlaceholder})`;
                        albumArtElement.style.opacity = '1';
                        if (albumArtBackgroundElement) albumArtBackgroundElement.style.opacity = '0.3';
                    }
                }, 200);
            } else if (albumArtElement && albumArtElement.style.opacity === '0') {
                 albumArtElement.style.opacity = '1';
                 if (albumArtBackgroundElement) albumArtBackgroundElement.style.opacity = '0.3';
            }


            _isPlaying = data.is_playing !== undefined ? data.is_playing : false;
            updatePlayPauseVisuals(_isPlaying);
            
            const progressMs = data.progress_ms !== undefined ? data.progress_ms : 0;
            const durationMs = data.item ? data.item.duration_ms : (data.duration_ms || 0);
            
            if (totalTimeElement) totalTimeElement.textContent = msToTimeFormat(durationMs);
            updateCircularProgressBar(progressMs, durationMs, _isPlaying);

        } else { // Çalınan bir şey yoksa veya veri eksikse
            if (trackNameElement) {
                trackNameElement.textContent = 'Bir şey çalmıyor';
                trackNameElement.title = 'Bir şey çalmıyor';
            }
            if (artistNameElement) artistNameElement.textContent = '-';
            
            const placeholderUrl = 'https://placehold.co/200x200/121212/444444?text=Beatify';
            if (albumArtElement && albumArtElement.src !== placeholderUrl) {
                 albumArtElement.style.opacity = '0';
                 if (albumArtBackgroundElement) albumArtBackgroundElement.style.opacity = '0';
                setTimeout(() => {
                    albumArtElement.src = placeholderUrl;
                    if (albumArtBackgroundElement) albumArtBackgroundElement.style.backgroundImage = `url(${placeholderUrl})`;
                    albumArtElement.onload = () => {
                        albumArtElement.style.opacity = '1';
                        if (albumArtBackgroundElement) albumArtBackgroundElement.style.opacity = '0.3';
                    }
                }, 200);
            } else if (albumArtElement && albumArtElement.style.opacity === '0'){
                 albumArtElement.style.opacity = '1';
                 if (albumArtBackgroundElement) albumArtBackgroundElement.style.opacity = '0.3';
            }

            _isPlaying = false;
            updatePlayPauseVisuals(false);
            updateCircularProgressBar(0, 1, false);
            if (currentTimeElement) currentTimeElement.textContent = "0:00";
            if (totalTimeElement) totalTimeElement.textContent = "0:00";
        }
    }
    
    function updatePlayPauseVisuals(isPlaying) {
        if (playPauseIcon) {
            playPauseIcon.classList.remove(isPlaying ? 'fa-play' : 'fa-pause');
            playPauseIcon.classList.add(isPlaying ? 'fa-pause' : 'fa-play');
        }
        if (albumDiscContainer) {
             albumDiscContainer.classList.toggle('playing', isPlaying);
        }
    }

    function updateCircularProgressBar(progressMs, durationMs, isPlaying) {
        if (progressInterval) clearInterval(progressInterval);
        progressInterval = null;

        if (!progressCircleElement || !currentTimeElement || !durationMs || durationMs <= 0) {
            if(progressCircleElement) progressCircleElement.style.strokeDashoffset = circumference;
            if(currentTimeElement) currentTimeElement.textContent = msToTimeFormat(0);
            return;
        }

        let currentProgress = progressMs;
        
        const update = () => {
            const percentage = Math.min(1, (currentProgress / durationMs));
            const offset = circumference * (1 - percentage);
            progressCircleElement.style.strokeDashoffset = offset;
            currentTimeElement.textContent = msToTimeFormat(currentProgress);
        };
        
        update();

        if (isPlaying) {
            progressInterval = setInterval(() => {
                currentProgress += 1000;
                if (currentProgress >= durationMs) {
                    currentProgress = durationMs;
                    update();
                    clearInterval(progressInterval);
                    progressInterval = null;
                    setTimeout(fetchCurrentlyPlayingData, 1200);
                } else {
                    update();
                }
            }, 1000);
        }
    }

    let errorTimeout;
    function showError(message) {
        if (!errorMessageElement) return;
        errorMessageElement.textContent = message;
        errorMessageElement.classList.add('visible');
        
        clearTimeout(errorTimeout);
        errorTimeout = setTimeout(() => {
            errorMessageElement.classList.remove('visible');
        }, 5000);
    }

    function hideError() {
        if (!errorMessageElement) return;
        clearTimeout(errorTimeout);
        errorMessageElement.classList.remove('visible');
    }

    // Kontrol butonları kaldırıldığı için ilgili kodlar da kaldırıldı

    fetchCurrentlyPlayingData();
});
