/**
 * Spotify Neon Widget - JavaScript
 * Modern, neon temalı Spotify widget için işlevsellik
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Element Referansları
    const albumArtElement = document.getElementById('albumArtNeon');
    const albumBackgroundElement = document.querySelector('.neon-glow');
    const trackNameElement = document.getElementById('trackNameNeon');
    const artistNameElement = document.getElementById('artistNameNeon');
    const currentTimeElement = document.getElementById('currentTimeNeon');
    const totalTimeElement = document.getElementById('totalTimeNeon');
    const progressBarFill = document.getElementById('progressBarFill');
    const errorMessageElement = document.getElementById('errorMessageNeon');
    const statusIndicator = document.getElementById('statusIndicator');
    const nowPlayingText = document.getElementById('nowPlayingText');
    const soundWave = document.getElementById('soundWave');
    const vinylDisc = document.getElementById('vinylDisc');

    // Global değişkenler
    let currentTrackData = null;
    let progressInterval = null;
    let fetchTimeoutId = null;
    let _isPlaying = false;
    let WIDGET_TOKEN = window.WIDGET_TOKEN || null;
    let lastTrackId = null;
    let lastAlbumArt = null;

    // Token alma işlemi
    console.log('Widget token aranıyor (Neon tasarım)...');
    
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
        return; 
    }
    console.log('Kullanılacak Widget Token (Neon):', WIDGET_TOKEN);

    // Yardımcı fonksiyonlar
    function msToTimeFormat(ms) {
        if (isNaN(ms) || ms < 0) return '0:00';
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }

    // Veri çekme fonksiyonu
    async function fetchCurrentlyPlayingData() {
        if (!WIDGET_TOKEN) return;
        if (fetchTimeoutId) clearTimeout(fetchTimeoutId);

        try {
            // API endpoint'i kullan - DATA_ENDPOINT değişkenini doğru şekilde kontrol et
            const apiUrl = window.DATA_ENDPOINT && window.DATA_ENDPOINT !== "{{ data_endpoint|safe }}" ? 
                window.DATA_ENDPOINT : 
                `/spotify/api/widget-data/${WIDGET_TOKEN}`;
            console.log('Neon widget veri çekme URL:', apiUrl);
            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                console.error('Veri çekme hatası:', response.status, errorData);
                
                let errorMessage = 'Veri alınamadı.';
                if (response.status === 404) {
                    errorMessage = 'Kullanıcı bulunamadı veya token geçersiz.';
                } else if (response.status === 401 || response.status === 403) {
                    errorMessage = 'Spotify oturumunuz sona ermiş olabilir.';
                }
                
                showError(errorMessage);
                setWidgetState(false, false);
                
                // Hata durumunda bile belirli bir süre sonra tekrar deneyelim
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 30000); // 30 saniye
                return;
            }

            const data = await response.json();
            
            // Test modu için kontrol - track_name ve artist_name doğrudan veri içinde olabilir
            const isTestMode = data.source === 'Test Data';
            
            if (isTestMode) {
                // Test verisi doğrudan kullanılabilir
                console.log('Test modu: Sahte veri kullanılıyor');
                hideError();
                currentTrackData = data;
                updateUIForTestMode(data);
                
                // Test modunda da periyodik güncelleme yapalım
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 5000);
                return;
            }
            
            // Normal mod - API formatını kontrol et
            // İki format olabilir: Spotify API formatı (item içeren) veya basitleştirilmiş format (track_name içeren)
            const isSimplifiedFormat = data && data.track_name !== undefined;
            
            if (isSimplifiedFormat) {
                // Basitleştirilmiş format - doğrudan track_name, artist_name gibi alanlar var
                console.log('Basitleştirilmiş veri formatı algılandı:', data);
                hideError();
                currentTrackData = data;
                updateUIForTestMode(data); // Aynı fonksiyonu kullanabiliriz çünkü format benzer
                
                // Periyodik güncelleme
                const refreshInterval = data.is_playing ? 5000 : 10000;
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, refreshInterval);
                return;
            }
            
            // Spotify API formatı - item içeren
            if (!data || !data.item) {
                // Çalınan bir şey yok veya veri boş
                console.log('Şu anda çalınan bir şey yok veya veri boş.');
                setWidgetState(true, false); // Bağlı ama çalmıyor
                
                if (data && data.error && data.error.message) {
                    showError(data.error.message);
                } else if (data && data.device === null) {
                    showError('Aktif Spotify cihazı bulunamadı.');
                } else {
                    showError('Şu anda çalınan bir şey yok.');
                }
                
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 10000); // 10 saniye
                return;
            }

            // Hata mesajını gizle, veri başarıyla alındı
            hideError();
            
            // Veriyi işle ve UI'ı güncelle
            currentTrackData = data;
            updateUI(data);
            
            // Bir sonraki veri çekme zamanını ayarla
            const nextFetchDelay = data.is_playing ? 5000 : 10000; // Çalıyorsa 5 saniye, değilse 10 saniye
            fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, nextFetchDelay);
            
        } catch (error) {
            console.error('Veri çekme sırasında kritik hata:', error);
            showError('Bağlantı hatası. Tekrar deneniyor...');
            setWidgetState(false, false);
            fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000); // 15 saniye
        }
    }

    // UI güncelleme fonksiyonu - Normal Spotify API formatı için
    function updateUI(data) {
        if (!data || !data.item) return;
        
        const isPlaying = data.is_playing;
        const track = data.item;
        const trackId = track.id;
        const albumArt = track.album.images[0]?.url;
        
        // Widget durumunu güncelle
        setWidgetState(true, isPlaying);
        
        // Şarkı değiştiyse veya ilk yüklemeyse albüm kapağını güncelle
        if (trackId !== lastTrackId || !lastAlbumArt) {
            updateAlbumArt(albumArt);
            lastTrackId = trackId;
            lastAlbumArt = albumArt;
        }
        
        // Şarkı ve sanatçı bilgilerini güncelle
        trackNameElement.textContent = track.name;
        trackNameElement.title = track.name;
        
        const artistNames = track.artists.map(artist => artist.name).join(', ');
        artistNameElement.textContent = artistNames;
        artistNameElement.title = artistNames;
        
        // Zaman ve ilerleme bilgilerini güncelle
        updateProgress(data.progress_ms, track.duration_ms, isPlaying);
    }
    
    // Test modu için UI güncelleme fonksiyonu
    function updateUIForTestMode(data) {
        if (!data) return;
        
        const isPlaying = data.is_playing;
        const trackId = 'test-' + Date.now(); // Benzersiz bir ID oluştur
        const albumArt = data.album_image_url;
        
        // Widget durumunu güncelle
        setWidgetState(true, isPlaying);
        
        // Şarkı değiştiyse veya ilk yüklemeyse albüm kapağını güncelle
        if (trackId !== lastTrackId || !lastAlbumArt) {
            updateAlbumArt(albumArt);
            lastTrackId = trackId;
            lastAlbumArt = albumArt;
        }
        
        // Şarkı ve sanatçı bilgilerini güncelle
        trackNameElement.textContent = data.track_name;
        trackNameElement.title = data.track_name;
        
        artistNameElement.textContent = data.artist_name;
        artistNameElement.title = data.artist_name;
        
        // Zaman ve ilerleme bilgilerini güncelle
        updateProgress(data.progress_ms, data.duration_ms, isPlaying);
    }

    // Albüm kapağı güncelleme
    function updateAlbumArt(imageUrl) {
        if (!imageUrl) return;
        
        // Yeni albüm kapağını yükle
        const newImage = new Image();
        newImage.onload = function() {
            // Görsel yüklendikten sonra DOM'u güncelle
            albumArtElement.src = imageUrl;
            
            // Arkaplan efektini güncelle (opsiyonel)
            const dominantColor = getDominantColorSimple(newImage);
            updateBackgroundGlow(dominantColor);
        };
        newImage.src = imageUrl;
    }
    
    // Basit dominant renk çıkarma fonksiyonu
    function getDominantColorSimple(image) {
        // Bu basit bir yaklaşım, gerçek dominant renk analizi için canvas kullanılabilir
        // Şimdilik varsayılan neon renklerini kullanıyoruz
        return {
            r: 0,
            g: 255,
            b: 255
        };
    }
    
    // Arkaplan parlaklığını güncelleme
    function updateBackgroundGlow(color) {
        // Neon efekti için renk geçişlerini güncelle
        // Burada CSS değişkenlerini güncelleyebiliriz, ancak şimdilik basit tutuyoruz
    }

    // İlerleme çubuğu ve zaman güncelleme
    function updateProgress(progressMs, durationMs, isPlaying) {
        // İlerleme yüzdesini hesapla
        const progressPercent = durationMs > 0 ? (progressMs / durationMs) * 100 : 0;
        
        // İlerleme çubuğunu güncelle
        progressBarFill.style.width = `${progressPercent}%`;
        
        // Zaman bilgilerini güncelle
        currentTimeElement.textContent = msToTimeFormat(progressMs);
        totalTimeElement.textContent = msToTimeFormat(durationMs);
        
        // Eğer çalıyorsa ve interval yoksa, interval başlat
        if (isPlaying) {
            if (!progressInterval) {
                let localProgress = progressMs;
                progressInterval = setInterval(() => {
                    localProgress += 1000; // Her saniye 1000ms artır
                    if (localProgress <= durationMs) {
                        const newPercent = (localProgress / durationMs) * 100;
                        progressBarFill.style.width = `${newPercent}%`;
                        currentTimeElement.textContent = msToTimeFormat(localProgress);
                    } else {
                        // Şarkı bitmiş olabilir, interval'i temizle
                        clearInterval(progressInterval);
                        progressInterval = null;
                        // Yeni veriyi hemen çek
                        fetchCurrentlyPlayingData();
                    }
                }, 1000);
            }
        } else if (progressInterval) {
            // Çalmıyorsa ve interval varsa, interval'i temizle
            clearInterval(progressInterval);
            progressInterval = null;
        }
    }

    // Widget durumunu ayarlama
    function setWidgetState(isConnected, isPlaying) {
        _isPlaying = isPlaying;
        
        // Durum göstergesini güncelle
        if (statusIndicator) {
            statusIndicator.style.backgroundColor = isConnected ? 'var(--neon-accent)' : 'red';
            statusIndicator.style.animation = isConnected ? 'pulse 2s infinite' : 'none';
        }
        
        // Now Playing yazısını güncelle
        if (nowPlayingText) {
            nowPlayingText.textContent = isPlaying ? 'NOW PLAYING' : 'PAUSED';
            nowPlayingText.style.color = isPlaying ? 'var(--neon-primary)' : 'var(--neon-secondary)';
        }
        
        // Ses dalgası animasyonunu güncelle
        if (soundWave) {
            if (isPlaying) {
                soundWave.classList.remove('paused');
            } else {
                soundWave.classList.add('paused');
            }
        }
        
        // Vinyl animasyonunu güncelle
        if (vinylDisc) {
            if (isPlaying) {
                vinylDisc.classList.add('playing');
            } else {
                vinylDisc.classList.remove('playing');
            }
        }
    }

    // Hata mesajı gösterme
    function showError(message) {
        if (!errorMessageElement) return;
        errorMessageElement.textContent = message;
        errorMessageElement.classList.add('visible');
    }
    
    // Hata mesajı gizleme
    function hideError() {
        if (!errorMessageElement) return;
        errorMessageElement.classList.remove('visible');
    }

    // İlk veri çekme işlemini başlat
    fetchCurrentlyPlayingData();
});
