// widget.js
document.addEventListener('DOMContentLoaded', () => {
    // Element referansları
    const albumArtElement = document.getElementById('albumArt');
    const trackNameElement = document.getElementById('trackName');
    const artistNameElement = document.getElementById('artistName');
    const playPauseButton = document.getElementById('playPauseButton');
    const playPauseIcon = document.getElementById('playPauseIcon');
    const prevButton = document.getElementById('prevButton');
    const nextButton = document.getElementById('nextButton');
    const progressBarElement = document.getElementById('progressBar');
    const errorMessageElement = document.getElementById('errorMessage');
    
    let WIDGET_TOKEN;

    // 1. WIDGET_TOKEN'ı al - Çeşitli kaynaklardan token'i almayı dene
    // Öncelik sırası: 
    // 1. Global window.WIDGET_TOKEN değişkeni (HTML içine backend tarafından enjekte edilmiş olabilir)
    // 2. URL path'inden token (Backend URL yapısı: /spotify/widget/<token_value>)
    // 3. iframe'in src attribute'undaki token (widget manager içinde gömülü olduğunda)
    // 4. URL query parametresinden token (?token=XYZ)

    console.log('Widget token aranıyor...');
    console.log('Current URL:', window.location.href);
    console.log('Current pathname:', window.location.pathname);
    
    // Önce global değişkeni kontrol et (en güvenilir kaynak)
    if (typeof window.WIDGET_TOKEN !== 'undefined' && window.WIDGET_TOKEN) {
        WIDGET_TOKEN = window.WIDGET_TOKEN;
        console.log('Token HTML\'den alındı (global değişken):', WIDGET_TOKEN);
    }
    
    // Global değişken yoksa URL path'inden almayı dene
    if (!WIDGET_TOKEN) {
        const pathParts = window.location.pathname.split('/');
        console.log('URL path parçaları:', pathParts);
        
        // URL yapısı /spotify/widget/<token> şeklinde olduğu için son eleman token olacaktır
        const tokenFromPath = pathParts[pathParts.length - 1];
        
        if (tokenFromPath && tokenFromPath !== 'widget' && tokenFromPath !== 'widget.html' && tokenFromPath.length > 8) {
            WIDGET_TOKEN = tokenFromPath;
            console.log('Token URL path\'ten alındı:', WIDGET_TOKEN);
        }
    }
    
    // Hala bulunamadıysa ve iframe içindeysek src'den almayı dene
    if (!WIDGET_TOKEN) {
        try {
            // Eğer bu sayfa bir iframe içindeyse
            if (window.self !== window.top) {
                console.log('iframe içindeyiz');
                const iframeSrc = window.location.href;
                console.log('iframe src:', iframeSrc);
                
                if (iframeSrc.includes('/spotify/widget/')) {
                    const srcParts = iframeSrc.split('/spotify/widget/');
                    console.log('iframe src parçaları:', srcParts);
                    
                    if (srcParts.length > 1 && srcParts[1]) {
                        // URL'den token'i çıkar (query parametrelerini kaldır)
                        const cleanToken = srcParts[1].split('?')[0];
                        if (cleanToken && cleanToken.length > 0) {
                            WIDGET_TOKEN = cleanToken;
                            console.log('Token iframe src\'den alındı:', WIDGET_TOKEN);
                        }
                    }
                }
            }
        } catch (e) {
            console.error('iframe kontrolü sırasında hata:', e);
        }
    }
    
    // Son çare olarak URL query parametresinden dene
    if (!WIDGET_TOKEN) {
        const urlParams = new URLSearchParams(window.location.search);
        const tokenParam = urlParams.get('token');
        console.log('URL parametreleri:', urlParams.toString());
        
        if (tokenParam) {
            WIDGET_TOKEN = tokenParam;
            console.log('Token URL parametresinden alındı:', WIDGET_TOKEN);
        }
    }

    // Doğrudan URL'den token'ı almayı dene - en güvenilir yöntem
    // URL yapısı /spotify/widget/TOKEN şeklinde olmalı
    const pathParts = window.location.pathname.split('/');
    console.log('URL path parçaları:', pathParts);
    
    // Spotify widget URL yapısını kontrol et
    if (pathParts.length >= 3 && pathParts[1] === 'spotify' && pathParts[2] === 'widget') {
        const tokenFromPath = pathParts[3]; // /spotify/widget/TOKEN formatında 3. indeks token olacaktır
        if (tokenFromPath && tokenFromPath.length > 0) {
            WIDGET_TOKEN = tokenFromPath;
            console.log('Token URL path\'ten alındı:', WIDGET_TOKEN);
        }
    }
    
    // Hala token bulunamadıysa ve global değişken varsa onu kullan
    if (!WIDGET_TOKEN && typeof window.WIDGET_TOKEN !== 'undefined' && window.WIDGET_TOKEN) {
        WIDGET_TOKEN = window.WIDGET_TOKEN;
        console.log('Token global değişkenden alındı:', WIDGET_TOKEN);
    }
    
    // Son çare olarak URL query parametresinden dene
    if (!WIDGET_TOKEN) {
        const urlParams = new URLSearchParams(window.location.search);
        const tokenParam = urlParams.get('token');
        if (tokenParam) {
            WIDGET_TOKEN = tokenParam;
            console.log('Token URL parametresinden alındı:', WIDGET_TOKEN);
        }
    }

    if (!WIDGET_TOKEN) {
        console.error('Widget token bulunamadı!');
        if(errorMessageElement) {
            errorMessageElement.textContent = 'Widget token konfigürasyonu eksik.';
            errorMessageElement.classList.remove('hidden');
        }
        // Gerekirse widget'ı devre dışı bırak
        if(playPauseButton) playPauseButton.disabled = true;
        if(prevButton) prevButton.disabled = true;
        if(nextButton) nextButton.disabled = true;
        return; // Token yoksa devam etme
    }
    
    // Doğrudan token'ı konsola yazdır (debug için)
    console.log('Kullanılacak Widget Token:', WIDGET_TOKEN);

    let currentTrackData = null;
    let _isPlaying = false;
    let progressInterval = null;

    // Spotify API'sinden veri çekme fonksiyonu
    async function fetchCurrentlyPlayingData() {
        if (!WIDGET_TOKEN) return;

        try {
            // Backend URL yapısına uygun endpoint
            const response = await fetch(`/spotify/api/widget-data/${WIDGET_TOKEN}`);
            if (!response.ok) {
                // HTTP 4xx/5xx hataları
                const errorData = await response.json().catch(() => null);
                console.error('Veri çekme hatası:', response.status, errorData);
                showError(errorData ? errorData.error : 'Veri alınamadı veya çalınan bir şey yok.');
                updateUI(null); // UI'ı sıfırla
                return;
            }

            const data = await response.json();
            
            if (data && data.is_playing !== undefined) {
                currentTrackData = data;
                _isPlaying = data.is_playing;
                updateUI(data);
                hideError();
            } else if (data && data.error) {
                console.error('API Hatası:', data.error);
                showError(data.error === "Player command failed: No active device found" ? "Aktif bir cihaz bulunamadı." : (data.error || "Bilinmeyen bir hata oluştu."));
                updateUI(null);
            } else {
                 // Çalınan bir şey yoksa veya beklenmedik format
                console.log('Çalınan bir şey yok veya veri formatı beklenmiyor.', data);
                showError('Şu anda çalınan bir şey yok.');
                updateUI(null); // UI'ı sıfırla
            }

        } catch (error) {
            console.error('fetchCurrentlyPlayingData içinde hata:', error);
            showError('Widget verileri güncellenemedi.');
            updateUI(null); // Hata durumunda UI'ı sıfırla
        }
    }

    // Kullanıcı arayüzünü güncelleme
    function updateUI(data) {
        // Backend'in döndüğü veri formatına uygun şekilde işlem yap
        // Backend ya doğrudan Spotify API formatını döndürüyor ya da kendi formatını kullanıyor
        if (data && (data.item || data.track_name)) { // Backend'in döndüğü veri formatına göre kontrol et
            if (trackNameElement) {
                // Backend'in döndüğü formata göre şarkı adını al
                const trackName = data.item ? data.item.name : data.track_name;
                trackNameElement.textContent = trackName;
                trackNameElement.title = trackName;
            }
            if (artistNameElement) {
                // Backend'in döndüğü formata göre sanatçı adını al
                let artistName;
                if (data.item && data.item.artists) {
                    artistName = data.item.artists.map(artist => artist.name).join(', ');
                } else {
                    artistName = data.artist_name || '-';
                }
                artistNameElement.textContent = artistName;
                artistNameElement.title = artistName;
            }
            if (albumArtElement) {
                // Backend'in döndüğü formata göre albüm kapağı URL'sini al
                let albumImageUrl;
                if (data.item && data.item.album && data.item.album.images && data.item.album.images.length > 0) {
                    albumImageUrl = data.item.album.images[0].url;
                } else {
                    albumImageUrl = data.album_image_url || 'https://placehold.co/200x200/2d3748/e2e8f0?text=Beatify';
                }
                albumArtElement.src = albumImageUrl;
            }

            // Backend'in döndüğü formata göre çalma durumunu al
            _isPlaying = data.is_playing !== undefined ? data.is_playing : false;
            updatePlayPauseButton(_isPlaying);
            
            // Backend'in döndüğü formata göre ilerleme ve süre bilgilerini al
            const progressMs = data.progress_ms !== undefined ? data.progress_ms : 0;
            const durationMs = data.item ? data.item.duration_ms : (data.duration_ms || 0);
            updateProgressBar(progressMs, durationMs, _isPlaying);

        } else { // Çalınan bir şey yoksa veya veri eksikse
            if (trackNameElement) {
                trackNameElement.textContent = 'Bir şey çalmıyor';
                trackNameElement.title = 'Bir şey çalmıyor';
            }
            if (artistNameElement) artistNameElement.textContent = '-';
            if (albumArtElement) albumArtElement.src = 'https://placehold.co/200x200/2d3748/e2e8f0?text=Beatify';
            
            updatePlayPauseButton(false);
            updateProgressBar(0, 1, false); // İlerleme çubuğunu sıfırla
        }
    }
    
    function updatePlayPauseButton(isPlaying) {
        if (!playPauseIcon) return;
        if (isPlaying) {
            playPauseIcon.classList.remove('fa-play');
            playPauseIcon.classList.add('fa-pause');
            playPauseButton.title = "Duraklat";
        } else {
            playPauseIcon.classList.remove('fa-pause');
            playPauseIcon.classList.add('fa-play');
            playPauseButton.title = "Oynat";
        }
    }

    function updateProgressBar(progressMs, durationMs, isPlaying) {
        if (!progressBarElement || !progressMs || !durationMs) {
             if(progressBarElement) progressBarElement.style.width = '0%';
            if (progressInterval) clearInterval(progressInterval);
            progressInterval = null;
            return;
        }

        let currentProgress = progressMs;
        const percentage = (currentProgress / durationMs) * 100;
        progressBarElement.style.width = `${Math.min(100, percentage)}%`;

        if (progressInterval) clearInterval(progressInterval);

        if (isPlaying) {
            progressInterval = setInterval(() => {
                currentProgress += 1000; // Her saniye artır
                if (currentProgress >= durationMs) {
                    currentProgress = durationMs;
                    clearInterval(progressInterval);
                    progressInterval = null;
                    // Şarkı bittiğinde veriyi yenilemek iyi olabilir
                    setTimeout(fetchCurrentlyPlayingData, 1200); // Kısa bir gecikmeyle
                }
                const newPercentage = (currentProgress / durationMs) * 100;
                progressBarElement.style.width = `${Math.min(100, newPercentage)}%`;
            }, 1000);
        }
    }

    function showError(message) {
        if (!errorMessageElement) return;
        errorMessageElement.textContent = message;
        errorMessageElement.classList.remove('hidden');
    }

    function hideError() {
         if (!errorMessageElement) return;
        errorMessageElement.classList.add('hidden');
    }

    // Player kontrol fonksiyonu
    async function controlPlayer(action) {
        if (!WIDGET_TOKEN) return;
        try {
            // Şu anda backend'de bu endpoint yok, bu yüzden uygun bir endpoint oluşturulmalı
            // Örnek: /spotify/widget/action/{token}/{action} şeklinde bir endpoint olabilir
            const response = await fetch(`/spotify/widget/action/${WIDGET_TOKEN}/${action}`, {
                method: 'POST',
            });
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    console.log(`${action} komutu başarılı.`);
                    // Komut başarılı olduktan hemen sonra UI'ı güncelle
                    // Spotify API'sinin değişikliği yansıtması biraz zaman alabilir,
                    // bu yüzden kısa bir gecikme eklenebilir veya polling'e güvenilebilir.
                    setTimeout(fetchCurrentlyPlayingData, 500); // 0.5 saniye sonra veriyi yenile
                } else {
                    console.error(`${action} komutu hatası:`, result.error);
                    showError(result.error === "Player command failed: No active device found" ? "Aktif bir cihaz bulunamadı." : (result.error || `İşlem "${action}" başarısız oldu.`));
                }
            } else {
                const errorData = await response.json().catch(() => ({ error: "Sunucu hatası veya geçersiz yanıt." }));
                console.error(`${action} isteği HTTP hatası:`, response.status, errorData);
                showError(errorData.error || `İstek "${action}" başarısız oldu.`);
            }
        } catch (error) {
            console.error(`${action} fonksiyonunda hata:`, error);
            showError(`"${action}" işlemi sırasında bir hata oluştu.`);
        }
    }

    // Event listener'lar
    if (playPauseButton) {
        playPauseButton.addEventListener('click', () => {
            // _isPlaying durumuna göre ters eylemi gönder
            controlPlayer(_isPlaying ? 'pause' : 'play');
        });
    }

    if (prevButton) {
        prevButton.addEventListener('click', () => controlPlayer('previous'));
    }

    if (nextButton) {
        nextButton.addEventListener('click', () => controlPlayer('next'));
    }

    // Sayfa yüklendiğinde ve periyodik olarak veriyi çek
    fetchCurrentlyPlayingData();
    setInterval(fetchCurrentlyPlayingData, 7000); // Her 7 saniyede bir güncelle (Spotify API limitlerini göz önünde bulundurun)
});
