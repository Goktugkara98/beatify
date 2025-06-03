// widget.js
document.addEventListener('DOMContentLoaded', () => {
    // Element referansları
    const spotifyWidgetElement = document.getElementById('spotifyWidget');
    const albumArtElement = document.getElementById('albumArt');
    const albumArtBackgroundElement = document.getElementById('albumArtBackground');
    const trackNameElement = document.getElementById('trackName');
    const artistNameElement = document.getElementById('artistName');
    const progressBarContainer = document.getElementById('progressBarContainer'); // İlerleme çubuğu konteyneri
    const progressBarElement = document.getElementById('progressBar');
    const currentTimeElement = document.getElementById('currentTime'); // Yeni
    const totalTimeElement = document.getElementById('totalTime');     // Yeni
    const errorMessageElement = document.getElementById('errorMessage');
    const overlayContentElement = document.getElementById('overlayContent');

    let WIDGET_TOKEN;
    let currentTrackData = null;
    let _isPlaying = false; // Still needed for progress tracking
    let progressInterval = null;
    let fetchTimeoutId = null; // Periyodik fetch için timeout ID'si

    // --- TOKEN ALMA BÖLÜMÜ (Mevcut kodunuzdan alındı ve iyileştirildi) ---
    console.log('Widget token aranıyor...');
    if (typeof window.WIDGET_TOKEN !== 'undefined' && window.WIDGET_TOKEN && window.WIDGET_TOKEN !== "{{ config.widgetToken|safe }}") { // Template literal'ı değilse
        WIDGET_TOKEN = window.WIDGET_TOKEN;
        console.log('Token HTML global değişkeninden (window.WIDGET_TOKEN) alındı:', WIDGET_TOKEN);
    }

    if (!WIDGET_TOKEN) {
        const pathParts = window.location.pathname.split('/');
        // URL yapısı /spotify/widget/TOKEN veya /widget/TOKEN (nginx yönlendirmesine göre)
        const widgetPathIndex = pathParts.findIndex(part => part === 'widget');
        if (widgetPathIndex !== -1 && pathParts.length > widgetPathIndex + 1) {
            const tokenFromPath = pathParts[widgetPathIndex + 1];
            if (tokenFromPath && tokenFromPath.length > 8) { // Basit bir token geçerlilik kontrolü
                WIDGET_TOKEN = tokenFromPath;
                console.log('Token URL path\'ten alındı:', WIDGET_TOKEN);
            }
        }
    }

    if (!WIDGET_TOKEN) {
        try {
            if (window.self !== window.top) { // iframe içinde mi?
                const iframeSrc = window.location.href;
                if (iframeSrc.includes('/widget/')) { // Veya /spotify/widget/
                    const srcParts = iframeSrc.split('/widget/'); // Veya /spotify/widget/
                    if (srcParts.length > 1 && srcParts[1]) {
                        const cleanToken = srcParts[1].split('?')[0].split('#')[0];
                        if (cleanToken && cleanToken.length > 8) {
                            WIDGET_TOKEN = cleanToken;
                            console.log('Token iframe src\'den alındı:', WIDGET_TOKEN);
                        }
                    }
                }
            }
        } catch (e) {
            console.warn('iframe src kontrolü sırasında hata (güvenlik kısıtlaması olabilir):', e.message);
        }
    }

    if (!WIDGET_TOKEN) {
        const urlParams = new URLSearchParams(window.location.search);
        const tokenParam = urlParams.get('token');
        if (tokenParam && tokenParam.length > 8) {
            WIDGET_TOKEN = tokenParam;
            console.log('Token URL query parametresinden alındı:', WIDGET_TOKEN);
        }
    }
    
    if (!WIDGET_TOKEN) {
        console.error('Widget token bulunamadı! Widget çalıştırılamıyor.');
        if(errorMessageElement) {
            errorMessageElement.textContent = 'Widget token konfigürasyonu eksik. Widget çalıştırılamıyor.';
            errorMessageElement.classList.remove('hidden');
            if(spotifyWidgetElement) spotifyWidgetElement.classList.add('pointer-events-none', 'opacity-50');
        }
        // Gerekirse widget'ı devre dışı bırak
        return; // Token yoksa devam etme
    }
    console.log('Kullanılacak Widget Token:', WIDGET_TOKEN);
    // --- TOKEN ALMA BÖLÜMÜ SONU ---


    // Milisaniyeyi dakika:saniye formatına çevirme
    function msToTimeFormat(ms) {
        if (isNaN(ms) || ms < 0) return '0:00';
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }

    async function fetchCurrentlyPlayingData() {
        if (!WIDGET_TOKEN) return;
        // Bir önceki timeout'u temizle (eğer varsa)
        if (fetchTimeoutId) clearTimeout(fetchTimeoutId);

        try {
            const response = await fetch(`/spotify/api/widget-data/${WIDGET_TOKEN}`);
            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                console.error('Veri çekme hatası:', response.status, errorData);
                let userMessage = 'Veri alınamadı veya çalınan bir şey yok.';
                if (response.status === 401 || response.status === 403) userMessage = "Yetkilendirme hatası. Token geçersiz olabilir.";
                else if (errorData && errorData.error) userMessage = errorData.error;
                showError(userMessage);
                updateUI(null);
                // Hata durumunda daha kısa bir süre sonra tekrar dene
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000); // 15 saniye
                return;
            }

            const data = await response.json();
            
            if (data && (data.is_playing !== undefined || (data.item && data.item.name))) { // Daha esnek kontrol
                currentTrackData = data; // Gelen tüm veriyi sakla
                _isPlaying = data.is_playing;
                updateUI(data);
                hideError();
                 // Başarılı veri alımından sonra normal periyotta devam et
                const refreshInterval = _isPlaying ? 7000 : 15000; // Çalıyorsa 7, çalmıyorsa 15 sn
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, refreshInterval);
            } else if (data && data.error) {
                console.error('API Hatası:', data.error);
                showError(data.error === "Player command failed: No active device found" ? "Aktif bir cihaz bulunamadı." : (data.error || "Bilinmeyen bir API hatası oluştu."));
                updateUI(null);
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000);
            } else {
                console.log('Çalınan bir şey yok veya veri formatı beklenmiyor.', data);
                showError('Şu anda çalınan bir şey yok.');
                updateUI(null);
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000);
            }

        } catch (error) {
            console.error('fetchCurrentlyPlayingData içinde kritik hata:', error);
            showError('Widget verileri güncellenemedi (Ağ hatası?).');
            updateUI(null);
            fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 20000); // Daha uzun bir süre sonra tekrar dene
        }
    }

    function updateUI(data) {
        if (data && (data.item || data.track_name)) { // Veri varsa
            const trackName = data.item ? data.item.name : (data.track_name || "Bilinmiyor");
            const artistName = data.item && data.item.artists ? data.item.artists.map(artist => artist.name).join(', ') : (data.artist_name || "-");
            let albumImageUrl = 'https://placehold.co/300x250/1f2937/e5e7eb?text=Beatify'; // Varsayılan
            if (data.item && data.item.album && data.item.album.images && data.item.album.images.length > 0) {
                // En uygun boyuttaki resmi seç (örneğin 300px civarı)
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
            // Update both main and background album art
            if (albumArtElement && albumArtElement.src !== albumImageUrl) {
                albumArtElement.classList.add('opacity-0'); // Önce gizle
                if (albumArtBackgroundElement) {
                    albumArtBackgroundElement.classList.add('opacity-0'); // Arka planı da gizle
                }
                
                setTimeout(() => { // Resmin yüklenmesi için kısa bir bekleme sonrası fade-in
                    // Ana albüm kapağını güncelle
                    albumArtElement.src = albumImageUrl;
                    
                    // Arka plan albüm kapağını da güncelle
                    if (albumArtBackgroundElement) {
                        albumArtBackgroundElement.src = albumImageUrl;
                    }
                    
                    albumArtElement.onload = () => {
                        albumArtElement.classList.remove('opacity-0');
                        if (albumArtBackgroundElement) {
                            albumArtBackgroundElement.classList.remove('opacity-0');
                        }
                    }
                    
                    albumArtElement.onerror = () => { // Resim yüklenemezse placeholder'a geri dön ve görünür yap
                        const errorPlaceholder = 'https://placehold.co/300x250/1f2937/e5e7eb?text=Hata';
                        albumArtElement.src = errorPlaceholder;
                        if (albumArtBackgroundElement) {
                            albumArtBackgroundElement.src = errorPlaceholder;
                        }
                        albumArtElement.classList.remove('opacity-0');
                        if (albumArtBackgroundElement) {
                            albumArtBackgroundElement.classList.remove('opacity-0');
                        }
                    }
                }, 100); // CSS transition süresiyle uyumlu olabilir
            } else if (albumArtElement.classList.contains('opacity-0')) { // Eğer src aynı ama gizliyse
                albumArtElement.classList.remove('opacity-0');
                if (albumArtBackgroundElement) {
                    albumArtBackgroundElement.classList.remove('opacity-0');
                }
            }


            _isPlaying = data.is_playing !== undefined ? data.is_playing : false;
            // No need to update button states as they've been removed
            
            const progressMs = data.progress_ms !== undefined ? data.progress_ms : 0;
            const durationMs = data.item ? data.item.duration_ms : (data.duration_ms || 0);
            
            if (totalTimeElement) totalTimeElement.textContent = msToTimeFormat(durationMs);
            updateProgressBar(progressMs, durationMs, _isPlaying);

            if (overlayContentElement) overlayContentElement.classList.remove('opacity-0');

        } else { // Çalınan bir şey yoksa veya veri eksikse
            if (trackNameElement) {
                trackNameElement.textContent = 'Bir şey çalmıyor';
                trackNameElement.title = 'Bir şey çalmıyor';
            }
            if (artistNameElement) artistNameElement.textContent = '-';
            if (albumArtElement && !albumArtElement.src.includes('placehold.co')) { // Sadece placeholder değilse değiştir
                albumArtElement.classList.add('opacity-0');
                setTimeout(() => {
                    albumArtElement.src = 'https://placehold.co/300x250/1f2937/e5e7eb?text=Beatify';
                    albumArtElement.onload = () => albumArtElement.classList.remove('opacity-0');
                }, 100);
            } else if (albumArtElement.classList.contains('opacity-0') && albumArtElement.src.includes('placehold.co')){
                 albumArtElement.classList.remove('opacity-0'); // Placeholder ise zaten görünür olsun
            }


            updateProgressBar(0, 1, false); // İlerleme çubuğunu ve zamanı sıfırla
            if (currentTimeElement) currentTimeElement.textContent = "0:00";
            if (totalTimeElement) totalTimeElement.textContent = "0:00";
        }
    }
    
    function updatePlayPauseButton(isPlaying) {
        // Function kept for compatibility but no longer updates UI elements
        // since play/pause buttons have been removed
    }

    function updateProgressBar(progressMs, durationMs, isPlaying) {
        if (progressInterval) clearInterval(progressInterval);
        progressInterval = null;

        if (!progressBarElement || !currentTimeElement || !durationMs || durationMs <= 0) {
             if(progressBarElement) progressBarElement.style.width = '0%';
             if(currentTimeElement) currentTimeElement.textContent = msToTimeFormat(0);
            return;
        }

        let currentProgress = progressMs;
        
        const update = () => {
            const percentage = Math.min(100, (currentProgress / durationMs) * 100);
            progressBarElement.style.width = `${percentage}%`;
            currentTimeElement.textContent = msToTimeFormat(currentProgress);
        };
        
        update(); // İlk güncellemeyi hemen yap

        if (isPlaying) {
            progressInterval = setInterval(() => {
                currentProgress += 1000; // Her saniye artır
                if (currentProgress >= durationMs) {
                    currentProgress = durationMs;
                    update();
                    clearInterval(progressInterval);
                    progressInterval = null;
                    // Şarkı bittiğinde veriyi yenilemek iyi olabilir
                    setTimeout(fetchCurrentlyPlayingData, 1200); // Kısa bir gecikmeyle
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
        errorMessageElement.classList.remove('fade');

        clearTimeout(errorTimeout); // Önceki timeout'u temizle
        errorTimeout = setTimeout(() => {
            errorMessageElement.classList.add('fade'); // Yavaşça kaybolsun
            setTimeout(() => errorMessageElement.classList.remove('visible'), 300); // Sonra DOM'dan gizle
        }, 5000); // 5 saniye sonra mesajı kaldır
    }

    function hideError() {
        if (!errorMessageElement) return;
        clearTimeout(errorTimeout);
        errorMessageElement.classList.add('fade');
        setTimeout(() => errorMessageElement.classList.remove('visible'), 300);
    }

    // Control player function removed as buttons have been removed

    // Event listeners removed as buttons have been removed

    // Sayfa yüklendiğinde veriyi çek
    fetchCurrentlyPlayingData();
    // Periyodik veri çekme artık fetchCurrentlyPlayingData içinde yönetiliyor.
});