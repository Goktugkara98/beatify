/*
    widget_neon.js (Revize Edilmiş - Neon Tasarım)

    İÇİNDEKİLER:

    1. DOM YÜKLENDİĞİNDE ÇALIŞACAK ANA FONKSİYON (DOMContentLoaded)
        1.1. Değişken Tanımlamaları
            1.1.1. DOM Elementleri
            1.1.2. Global Durum Değişkenleri
        1.2. Token Alma İşlemleri
            1.2.1. window.WIDGET_TOKEN Kontrolü (Öncelikli)
            1.2.2. URL Path'ten Token Alma
            1.2.3. Token Bulunamama Durumu
        1.3. Yardımcı Fonksiyonlar
            1.3.1. msToTimeFormat(ms)
            1.3.2. getDominantColorSimple(image) (Not: Şu an varsayılan renk döndürüyor)
        1.4. Ana Veri Çekme ve İşleme Fonksiyonları
            1.4.1. fetchCurrentlyPlayingData()
            1.4.2. updateUI(data) (Normal Spotify API formatı için)
            1.4.3. updateUIForTestMode(data) (Test veya basitleştirilmiş format için)
            1.4.4. updateAlbumArt(imageUrl)
            1.4.5. updateBackgroundGlow(color) (Not: Şu an işlevsiz)
            1.4.6. updateProgress(progressMs, durationMs, isPlaying)
        1.5. Widget Durum ve Hata Gösterim Fonksiyonları
            1.5.1. setWidgetState(isConnected, isPlaying)
            1.5.2. showError(message)
            1.5.3. hideError()
        1.6. Başlangıç Çağrısı
*/

// 1. DOM YÜKLENDİĞİNDE ÇALIŞACAK ANA FONKSİYON
document.addEventListener('DOMContentLoaded', function() {
    // =============================================
    // 1.1. Değişken Tanımlamaları
    // =============================================

    // 1.1.1. DOM Elementleri
    const albumArtElement = document.getElementById('albumArtNeon');
    // const albumBackgroundElement = document.querySelector('.neon-glow'); // Aktif kullanılmıyor gibi
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

    // 1.1.2. Global Durum Değişkenleri
    // let currentTrackData = null; // Aktif kullanılmıyor gibi, ihtiyaç halinde açılabilir
    let progressInterval = null;
    let fetchTimeoutId = null;
    let _isPlaying = false;
    let WIDGET_TOKEN = window.WIDGET_TOKEN || null;
    let lastTrackId = null; // Son şarkı ID'si, albüm kapağı güncellemesi için
    let lastAlbumArt = null; // Son albüm kapağı URL'si

    // =============================================
    // 1.2. Token Alma İşlemleri
    // =============================================
    console.log('Widget token aranıyor (widget_neon.js)...');

    // 1.2.1. window.WIDGET_TOKEN Kontrolü (Öncelikli)
    // WIDGET_TOKEN zaten yukarıda `window.WIDGET_TOKEN || null` ile atandı.

    // 1.2.2. URL Path'ten Token Alma (Eğer globalde yoksa)
    if (!WIDGET_TOKEN) {
        const pathParts = window.location.pathname.split('/');
        const widgetPathIndex = pathParts.findIndex(part => part === 'widget');
        if (widgetPathIndex !== -1 && pathParts.length > widgetPathIndex + 1) {
            const tokenFromPath = pathParts[widgetPathIndex + 1];
            if (tokenFromPath && tokenFromPath.length > 8) {
                WIDGET_TOKEN = tokenFromPath;
                console.log('Token URL path\'ten alındı:', WIDGET_TOKEN);
            }
        }
    }

    // 1.2.3. Token Bulunamama Durumu
    if (!WIDGET_TOKEN) {
        console.error('Widget token bulunamadı! Widget çalıştırılamıyor.');
        if (errorMessageElement) {
            showError('Widget token bulunamadı.');
        }
        // Widget'ı görsel olarak devre dışı bırakmak için ek stil eklenebilir.
        return;
    }
    console.log('Kullanılacak Widget Token (Neon - widget_neon.js):', WIDGET_TOKEN);

    // =============================================
    // 1.3. Yardımcı Fonksiyonlar
    // =============================================

    /**
     * 1.3.1. Milisaniyeyi dakika:saniye formatına çevirir.
     * @param {number} ms - Milisaniye cinsinden süre.
     * @returns {string} "dakika:saniye" formatında string.
     */
    function msToTimeFormat(ms) {
        if (isNaN(ms) || ms < 0) return '0:00';
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`; // Saniyeyi her zaman iki haneli yap
    }

    /**
     * 1.3.2. Resimden basit bir dominant renk çıkarır (Şu an varsayılan bir renk döndürür).
     * @param {HTMLImageElement} image - Renk analizi yapılacak resim elementi.
     * @returns {object} {r, g, b} formatında renk nesnesi.
     */
    function getDominantColorSimple(image) {
        // Not: Bu fonksiyon gerçek bir dominant renk analizi yapmaz.
        // Daha gelişmiş bir analiz için canvas kullanılabilir.
        // Şimdilik varsayılan bir neon rengi döndürüyor.
        console.warn("getDominantColorSimple: Gerçek dominant renk analizi uygulanmadı, varsayılan renk kullanılıyor.");
        return { r: 0, g: 255, b: 255 }; // Örnek bir cyan rengi
    }


    // =============================================
    // 1.4. Ana Veri Çekme ve İşleme Fonksiyonları
    // =============================================

    /**
     * 1.4.1. Spotify'dan mevcut çalınan şarkı verisini çeker.
     */
    async function fetchCurrentlyPlayingData() {
        if (!WIDGET_TOKEN) return;
        if (fetchTimeoutId) clearTimeout(fetchTimeoutId);

        try {
            const apiUrl = (typeof window.DATA_ENDPOINT !== 'undefined' && window.DATA_ENDPOINT && window.DATA_ENDPOINT !== "{{ data_endpoint|safe }}")
                ? window.DATA_ENDPOINT
                : `/spotify/api/widget-data/${WIDGET_TOKEN}`;
            console.log('Neon widget veri çekme URL:', apiUrl);

            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                console.error('Veri çekme hatası:', response.status, errorData);
                let errorMessage = 'Veri alınamadı.';
                if (response.status === 404) errorMessage = 'Kullanıcı bulunamadı veya token geçersiz.';
                else if (response.status === 401 || response.status === 403) errorMessage = 'Spotify oturumunuz sona ermiş olabilir.';
                else if (errorData && errorData.error) errorMessage = errorData.error.message || errorData.error;

                showError(errorMessage);
                setWidgetState(false, false); // Bağlantı yok, çalmıyor
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 30000); // 30 saniye sonra tekrar dene
                return;
            }

            const data = await response.json();
            const isTestMode = data.source === 'Test Data'; // Backend'den test verisi gelip gelmediğini kontrol et
            const isSimplifiedFormat = data && data.track_name !== undefined && !data.item; // 'item' yoksa basitleştirilmiş format

            if (isTestMode || isSimplifiedFormat) {
                console.log(isTestMode ? 'Test modu: Veri kullanılıyor' : 'Basitleştirilmiş veri formatı algılandı');
                hideError();
                // currentTrackData = data; // İhtiyaç halinde saklanabilir
                updateUIForTestMode(data); // Test/Basit format için UI güncelle
                const refreshInterval = data.is_playing ? 5000 : 10000;
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, refreshInterval);
                return;
            }

            // Normal Spotify API formatı (item içeren)
            if (!data || !data.item) {
                console.log('Şu anda çalınan bir şey yok veya veri boş (normal format).');
                setWidgetState(true, false); // Bağlı ama çalmıyor
                if (data && data.error && data.error.message) showError(data.error.message);
                else if (data && data.device === null) showError('Aktif Spotify cihazı bulunamadı.');
                else showError('Şu anda çalınan bir şey yok.');
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 10000);
                return;
            }

            hideError(); // Veri başarıyla alındı, hata mesajını gizle
            // currentTrackData = data; // İhtiyaç halinde saklanabilir
            updateUI(data); // Normal format için UI güncelle
            const nextFetchDelay = data.is_playing ? 5000 : 10000;
            fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, nextFetchDelay);

        } catch (error) {
            console.error('Veri çekme sırasında kritik hata:', error);
            showError('Bağlantı hatası. Tekrar deneniyor...');
            setWidgetState(false, false);
            fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000);
        }
    }

    /**
     * 1.4.2. Gelen standart Spotify API verilerine göre kullanıcı arayüzünü günceller.
     * @param {object} data - Spotify API'den gelen veri (item içermeli).
     */
    function updateUI(data) {
        if (!data || !data.item) return;

        const isPlaying = data.is_playing;
        const track = data.item;
        const trackId = track.id;
        // Albüm kapağı için en uygun boyutu seçmeye çalış (örn: 300px civarı, yoksa ilkini al)
        const albumArt = track.album.images.reduce((prev, curr) => {
            return (Math.abs(curr.width - 300) < Math.abs(prev.width - 300) ? curr : prev);
        }, track.album.images[0])?.url || 'https://placehold.co/300x300/000000/1DB954?text=Neon';


        setWidgetState(true, isPlaying); // Bağlı ve çalma durumunu ayarla

        if (trackId !== lastTrackId || albumArt !== lastAlbumArt) { // Şarkı veya albüm kapağı değiştiyse
            updateAlbumArt(albumArt);
            lastTrackId = trackId;
            lastAlbumArt = albumArt;
        }

        if (trackNameElement) {
            trackNameElement.textContent = track.name;
            trackNameElement.title = track.name;
        }
        if (artistNameElement) {
            const artistNames = track.artists.map(artist => artist.name).join(', ');
            artistNameElement.textContent = artistNames;
            artistNameElement.title = artistNames;
        }

        updateProgress(data.progress_ms, track.duration_ms, isPlaying);
    }

    /**
     * 1.4.3. Test modu veya basitleştirilmiş veri formatı için UI'ı günceller.
     * @param {object} data - Test veya basitleştirilmiş formatta veri.
     */
    function updateUIForTestMode(data) {
        if (!data) return;

        const isPlaying = data.is_playing;
        // Test modu için benzersiz bir trackId oluşturmaya gerek yok, albüm kapağına göre kontrol yeterli
        const albumArt = data.album_image_url || 'https://placehold.co/300x300/000000/1DB954?text=NeonTest';

        setWidgetState(true, isPlaying);

        if (albumArt !== lastAlbumArt) { // Sadece albüm kapağı değiştiyse güncelle
            updateAlbumArt(albumArt);
            lastAlbumArt = albumArt;
        }
        // lastTrackId test modunda çok anlamlı olmayabilir, bu yüzden sadece albüm kapağına odaklanıyoruz.

        if (trackNameElement) {
            trackNameElement.textContent = data.track_name || "Bilinmeyen Şarkı";
            trackNameElement.title = data.track_name || "Bilinmeyen Şarkı";
        }
        if (artistNameElement) {
            artistNameElement.textContent = data.artist_name || "Bilinmeyen Sanatçı";
            artistNameElement.title = data.artist_name || "Bilinmeyen Sanatçı";
        }

        updateProgress(data.progress_ms || 0, data.duration_ms || 1, isPlaying); // duration 0 olmasın diye 1 varsay
    }

    /**
     * 1.4.4. Albüm kapağını günceller.
     * @param {string} imageUrl - Gösterilecek albüm kapağının URL'si.
     */
    function updateAlbumArt(imageUrl) {
        if (!imageUrl || !albumArtElement) return;

        // Fade out efekti için
        albumArtElement.style.opacity = '0';

        // Yeni resmi yükle ve fade in yap
        const newImage = new Image();
        newImage.onload = function() {
            albumArtElement.src = imageUrl;
            albumArtElement.style.opacity = '1'; // Fade in
            // Arka plan efektini güncelle (şu an basit bir renk döndürüyor)
            // const dominantColor = getDominantColorSimple(newImage);
            // updateBackgroundGlow(dominantColor); // Bu fonksiyon şu an işlevsiz
        };
        newImage.onerror = function() { // Resim yüklenemezse placeholder göster
            albumArtElement.src = 'https://placehold.co/300x300/000000/1DB954?text=Hata';
            albumArtElement.style.opacity = '1';
        }
        newImage.src = imageUrl;
    }

    /**
     * 1.4.5. Arka plan parlaklığını günceller (Şu an işlevsiz).
     * @param {object} color - {r, g, b} formatında renk.
     */
    function updateBackgroundGlow(color) {
        // Bu fonksiyon, neon efekt için CSS değişkenlerini güncelleyebilirdi.
        // Örneğin: document.documentElement.style.setProperty('--neon-glow-color', `rgba(${color.r}, ${color.g}, ${color.b}, 0.5)`);
        // Ancak şu an için aktif bir kullanımı yok.
        console.warn("updateBackgroundGlow fonksiyonu çağrıldı ancak şu an için bir işlem yapmıyor.");
    }

    /**
     * 1.4.6. İlerleme çubuğunu ve zamanı günceller.
     * @param {number} progressMs - Mevcut ilerleme (ms).
     * @param {number} durationMs - Toplam süre (ms).
     * @param {boolean} isPlaying - Şarkının çalma durumu.
     */
    function updateProgress(progressMs, durationMs, isPlaying) {
        if (progressInterval) clearInterval(progressInterval);
        progressInterval = null;

        if (!progressBarFill || !currentTimeElement || !totalTimeElement || !durationMs || durationMs <= 0) {
            if(progressBarFill) progressBarFill.style.width = '0%';
            if(currentTimeElement) currentTimeElement.textContent = msToTimeFormat(0);
            if(totalTimeElement) totalTimeElement.textContent = msToTimeFormat(0);
            return;
        }


        const updateDOM = (currentProg) => {
            const progressPercent = durationMs > 0 ? (currentProg / durationMs) * 100 : 0;
            progressBarFill.style.width = `${Math.min(100, progressPercent)}%`; // %100'ü geçmesin
            currentTimeElement.textContent = msToTimeFormat(currentProg);
        };

        totalTimeElement.textContent = msToTimeFormat(durationMs); // Toplam süreyi başta ayarla
        updateDOM(progressMs); // İlk güncellemeyi hemen yap

        if (isPlaying) {
            let localProgress = progressMs;
            progressInterval = setInterval(() => {
                localProgress += 1000;
                if (localProgress <= durationMs) {
                    updateDOM(localProgress);
                } else {
                    updateDOM(durationMs); // Tam sürede durdur
                    clearInterval(progressInterval);
                    progressInterval = null;
                    setTimeout(fetchCurrentlyPlayingData, 1200); // Şarkı bitince yenile
                }
            }, 1000);
        }
    }

    // =============================================
    // 1.5. Widget Durum ve Hata Gösterim Fonksiyonları
    // =============================================

    /**
     * 1.5.1. Widget'ın genel durumunu (bağlantı, çalma durumu, animasyonlar) ayarlar.
     * @param {boolean} isConnected - Spotify'a bağlı mı?
     * @param {boolean} isPlayingMusic - Şarkı çalıyor mu?
     */
    function setWidgetState(isConnected, isPlayingMusic) {
        _isPlaying = isPlayingMusic; // Global çalma durumunu güncelle

        if (statusIndicator) {
            statusIndicator.style.backgroundColor = isConnected ? 'var(--neon-accent)' : 'red'; // Bağlantı rengi
            statusIndicator.style.animation = isConnected && isPlayingMusic ? 'pulse 2s infinite' : 'none'; // Sadece çalıyorsa pulse
        }

        if (nowPlayingText) {
            nowPlayingText.textContent = isPlayingMusic ? 'NOW PLAYING' : (isConnected ? 'PAUSED' : 'OFFLINE');
            nowPlayingText.style.color = isPlayingMusic ? 'var(--neon-primary)' : 'var(--neon-secondary)';
        }

        if (soundWave) { // Ses dalgası animasyonu
            soundWave.classList.toggle('paused', !isPlayingMusic);
        }

        if (vinylDisc) { // Dönen disk animasyonu
            vinylDisc.classList.toggle('playing', isPlayingMusic);
        }
    }

    /**
     * 1.5.2. Kullanıcıya bir hata mesajı gösterir.
     * @param {string} message - Gösterilecek hata mesajı.
     */
    function showError(message) {
        if (!errorMessageElement) return;
        errorMessageElement.textContent = message;
        errorMessageElement.classList.add('visible');
    }

    /**
     * 1.5.3. Hata mesajını gizler.
     */
    function hideError() {
        if (!errorMessageElement) return;
        errorMessageElement.classList.remove('visible');
    }

    // =============================================
    // 1.6. Başlangıç Çağrısı
    // =============================================
    fetchCurrentlyPlayingData();
    console.log('widget_neon.js (Revize Edilmiş) yüklendi ve çalışıyor.');
});
