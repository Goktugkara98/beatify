/*
    widget_alt.js (Revize Edilmiş - Alternatif Tasarım)

    İÇİNDEKİLER:

    1. DOM YÜKLENDİĞİNDE ÇALIŞACAK ANA FONKSİYON (DOMContentLoaded)
        1.1. Değişken Tanımlamaları
            1.1.1. DOM Elementleri
            1.1.2. Global Durum Değişkenleri
            1.1.3. Dairesel İlerleme Çubuğu Değişkenleri
        1.2. Token Alma İşlemleri
            1.2.1. window.WIDGET_TOKEN Kontrolü (Öncelikli)
            1.2.2. URL Path'ten Token Alma
            1.2.3. Token Bulunamama Durumu
        1.3. Yardımcı Fonksiyonlar
            1.3.1. msToTimeFormat(ms)
        1.4. Ana Veri Çekme ve İşleme Fonksiyonları
            1.4.1. fetchCurrentlyPlayingData()
            1.4.2. updateUI(data)
            1.4.3. updatePlayPauseVisuals(isPlaying)
            1.4.4. updateCircularProgressBar(progressMs, durationMs, isPlaying)
        1.5. Hata Gösterim Fonksiyonları
            1.5.1. showError(message)
            1.5.2. hideError()
        1.6. Başlangıç Çağrısı
*/

// 1. DOM YÜKLENDİĞİNDE ÇALIŞACAK ANA FONKSİYON
document.addEventListener('DOMContentLoaded', () => {
    // =============================================
    // 1.1. Değişken Tanımlamaları
    // =============================================

    // 1.1.1. DOM Elementleri
    const spotifyWidgetElement = document.getElementById('spotifyWidgetAlt');
    const albumArtElement = document.getElementById('albumArtAlt');
    const albumArtBackgroundElement = document.getElementById('albumArtBackgroundAlt'); // Arka plan için
    const trackNameElement = document.getElementById('trackNameAlt');
    const artistNameElement = document.getElementById('artistNameAlt');
    const progressCircleElement = document.getElementById('progressCircle'); // Dairesel ilerleme çubuğu SVG elementi
    const currentTimeElement = document.getElementById('currentTimeAlt');
    const totalTimeElement = document.getElementById('totalTimeAlt');
    const errorMessageElement = document.getElementById('errorMessageAlt');
    // const playPauseOverlay = document.getElementById('playPauseOverlay'); // Kullanılmıyorsa kaldırılabilir
    const playPauseIcon = document.getElementById('playPauseIcon'); // Oynat/Duraklat ikonu
    const albumDiscContainer = document.querySelector('.album-disc-container'); // Dönen disk efekti için

    // 1.1.2. Global Durum Değişkenleri
    // let currentTrackData = null; // Aktif kullanılmıyor gibi, ihtiyaç halinde açılabilir
    let progressInterval = null; // İlerleme çubuğu için zamanlayıcı
    let fetchTimeoutId = null; // Veri çekme için zamanlayıcı ID'si
    let _isPlaying = false; // Şarkının çalma durumu
    let WIDGET_TOKEN = window.WIDGET_TOKEN || null; // Spotify API token'ı (önce globalden almayı dene)
    // let lastTrackId = null; // Son çalınan şarkı ID'si, aktif kullanılmıyor
    // let lastAlbumArt = null; // Son albüm kapağı URL'si, aktif kullanılmıyor

    // 1.1.3. Dairesel İlerleme Çubuğu Değişkenleri
    const circleRadius = progressCircleElement ? parseFloat(progressCircleElement.r.baseVal.value) : 0;
    const circumference = 2 * Math.PI * circleRadius; // Çemberin çevresi
    if (progressCircleElement) {
        progressCircleElement.style.strokeDasharray = circumference; // Çizgi ve boşluk uzunluğu
        progressCircleElement.style.strokeDashoffset = circumference; // Başlangıçta tamamen gizli
    }

    // =============================================
    // 1.2. Token Alma İşlemleri
    // =============================================
    console.log('Widget token aranıyor (widget_alt.js)...');

    // 1.2.1. window.WIDGET_TOKEN Kontrolü (Öncelikli)
    // WIDGET_TOKEN zaten yukarıda `window.WIDGET_TOKEN || null` ile atandı.

    // 1.2.2. URL Path'ten Token Alma (Eğer globalde yoksa)
    if (!WIDGET_TOKEN) {
        const pathParts = window.location.pathname.split('/');
        const widgetPathIndex = pathParts.findIndex(part => part === 'widget');
        if (widgetPathIndex !== -1 && pathParts.length > widgetPathIndex + 1) {
            const tokenFromPath = pathParts[widgetPathIndex + 1];
            if (tokenFromPath && tokenFromPath.length > 8) { // Basit token geçerlilik kontrolü
                WIDGET_TOKEN = tokenFromPath;
                console.log('Token URL path\'ten alındı:', WIDGET_TOKEN);
            }
        }
    }
    // Diğer token alma yöntemleri (iframe, query param) bu dosyada yok, gerekirse eklenebilir.

    // 1.2.3. Token Bulunamama Durumu
    if (!WIDGET_TOKEN) {
        console.error('Widget token bulunamadı! Widget çalıştırılamıyor.');
        if (errorMessageElement) {
            showError('Widget token bulunamadı.'); // showError fonksiyonunu kullan
        }
        if (spotifyWidgetElement) spotifyWidgetElement.classList.add('opacity-50', 'pointer-events-none');
        return; // Token yoksa devam etme
    }
    console.log('Kullanılacak Widget Token (Alternatif - widget_alt.js):', WIDGET_TOKEN);

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
        return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
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
            // API endpoint'i: Önce window.DATA_ENDPOINT kontrol et, yoksa standart URL kullan
            const apiUrl = (typeof window.DATA_ENDPOINT !== 'undefined' && window.DATA_ENDPOINT && window.DATA_ENDPOINT !== "{{ data_endpoint|safe }}")
                ? window.DATA_ENDPOINT
                : `/spotify/api/widget-data/${WIDGET_TOKEN}`;
            console.log('Alt widget veri çekme URL:', apiUrl);

            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                console.error('Veri çekme hatası:', response.status, errorData);
                let userMessage = 'Veri alınamadı veya çalınan bir şey yok.';
                if (response.status === 401 || response.status === 403) userMessage = "Yetkilendirme hatası. Token geçersiz olabilir.";
                else if (response.status === 404 && errorData && errorData.error === "Widget not found or token invalid") userMessage = "Widget bulunamadı veya token geçersiz.";
                else if (errorData && errorData.error) userMessage = errorData.error.message || errorData.error; // error.message olabilir
                showError(userMessage);
                updateUI(null); // UI'ı boş duruma getir
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000);
                return;
            }

            const data = await response.json();

            if (data && (data.is_playing !== undefined || (data.item && data.item.name))) {
                // currentTrackData = data; // İhtiyaç halinde saklanabilir
                _isPlaying = data.is_playing;
                updateUI(data);
                hideError();
                const refreshInterval = _isPlaying ? 7000 : 15000;
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, refreshInterval);
            } else if (data && data.error) {
                console.error('API Hatası:', data.error);
                const displayError = data.error === "Player command failed: No active device found"
                    ? "Aktif bir cihaz bulunamadı."
                    : (data.error.message || data.error || "Bilinmeyen bir API hatası oluştu.");
                showError(displayError);
                updateUI(null);
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000);
            } else {
                // Eğer is_playing false ve item null ise, bu "çalınan bir şey yok" durumu.
                if (data && data.is_playing === false && data.item === null) {
                    updateUI(data); // UI'ı "çalınmıyor" olarak güncelle
                    hideError(); // Hata mesajı varsa gizle
                } else {
                    console.log('Çalınan bir şey yok veya veri formatı beklenmiyor.', data);
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

    /**
     * 1.4.2. Gelen verilere göre kullanıcı arayüzünü günceller.
     * @param {object|null} data - Spotify API'den gelen veri veya null.
     */
    function updateUI(data) {
        if (data && (data.item || data.track_name)) { // Veri varsa ve şarkı bilgisi içeriyorsa
            const trackName = data.item ? data.item.name : (data.track_name || "Bilinmiyor");
            const artistName = data.item && data.item.artists ? data.item.artists.map(artist => artist.name).join(', ') : (data.artist_name || "-");
            let albumImageUrl = 'https://placehold.co/200x200/121212/444444?text=Beatify'; // Varsayılan placeholder

            if (data.item && data.item.album && data.item.album.images && data.item.album.images.length > 0) {
                albumImageUrl = data.item.album.images.reduce((prev, curr) => { // Uygun boyutta resim seç
                    return (Math.abs(curr.width - 200) < Math.abs(prev.width - 200) ? curr : prev);
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
                        if (albumArtBackgroundElement) albumArtBackgroundElement.style.opacity = '0.3'; // Arka plan için daha düşük opaklık
                    };
                    albumArtElement.onerror = () => {
                        const errorPlaceholder = 'https://placehold.co/200x200/121212/444444?text=Hata';
                        albumArtElement.src = errorPlaceholder;
                        if (albumArtBackgroundElement) albumArtBackgroundElement.style.backgroundImage = `url(${errorPlaceholder})`;
                        albumArtElement.style.opacity = '1';
                        if (albumArtBackgroundElement) albumArtBackgroundElement.style.opacity = '0.3';
                    };
                }, 200); // CSS geçişi için zaman
            } else if (albumArtElement && albumArtElement.style.opacity === '0') { // Eğer src aynı ama gizliyse
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
                    };
                }, 200);
            } else if (albumArtElement && albumArtElement.style.opacity === '0' && albumArtElement.src.includes('placehold.co')) {
                albumArtElement.style.opacity = '1';
                if (albumArtBackgroundElement) albumArtBackgroundElement.style.opacity = '0.3';
            }

            _isPlaying = false;
            updatePlayPauseVisuals(false);
            updateCircularProgressBar(0, 1, false); // İlerlemeyi sıfırla
            if (currentTimeElement) currentTimeElement.textContent = "0:00";
            if (totalTimeElement) totalTimeElement.textContent = "0:00";
        }
    }

    /**
     * 1.4.3. Oynat/Duraklat ikonunu ve disk animasyonunu günceller.
     * @param {boolean} isPlaying - Şarkının çalma durumu.
     */
    function updatePlayPauseVisuals(isPlaying) {
        if (playPauseIcon) {
            playPauseIcon.classList.remove(isPlaying ? 'fa-play' : 'fa-pause');
            playPauseIcon.classList.add(isPlaying ? 'fa-pause' : 'fa-play');
        }
        if (albumDiscContainer) {
            albumDiscContainer.classList.toggle('playing', isPlaying); // 'playing' class'ını ekle/kaldır
        }
    }

    /**
     * 1.4.4. Dairesel ilerleme çubuğunu ve zamanını günceller.
     * @param {number} progressMs - Mevcut ilerleme (ms).
     * @param {number} durationMs - Toplam süre (ms).
     * @param {boolean} isPlaying - Şarkının çalma durumu.
     */
    function updateCircularProgressBar(progressMs, durationMs, isPlaying) {
        if (progressInterval) clearInterval(progressInterval);
        progressInterval = null;

        if (!progressCircleElement || !currentTimeElement || !durationMs || durationMs <= 0) {
            if (progressCircleElement) progressCircleElement.style.strokeDashoffset = circumference; // Sıfırla
            if (currentTimeElement) currentTimeElement.textContent = msToTimeFormat(0);
            return;
        }

        let currentProgress = progressMs;

        const updateDOM = () => {
            const percentage = Math.min(1, (currentProgress / durationMs)); // Yüzdeyi 0-1 arasında tut
            const offset = circumference * (1 - percentage); // strokeDashoffset hesapla
            progressCircleElement.style.strokeDashoffset = offset;
            currentTimeElement.textContent = msToTimeFormat(currentProgress);
        };

        updateDOM(); // İlk güncellemeyi hemen yap

        if (isPlaying) {
            progressInterval = setInterval(() => {
                currentProgress += 1000;
                if (currentProgress >= durationMs) {
                    currentProgress = durationMs;
                    updateDOM();
                    clearInterval(progressInterval);
                    progressInterval = null;
                    setTimeout(fetchCurrentlyPlayingData, 1200); // Şarkı bitince yenile
                } else {
                    updateDOM();
                }
            }, 1000);
        }
    }

    // =============================================
    // 1.5. Hata Gösterim Fonksiyonları
    // =============================================
    let errorTimeout; // Hata mesajının zaman aşımı ID'si

    /**
     * 1.5.1. Kullanıcıya bir hata mesajı gösterir.
     * @param {string} message - Gösterilecek hata mesajı.
     */
    function showError(message) {
        if (!errorMessageElement) return;
        errorMessageElement.textContent = message;
        errorMessageElement.classList.add('visible'); // CSS ile görünür yap

        clearTimeout(errorTimeout);
        errorTimeout = setTimeout(() => {
            errorMessageElement.classList.remove('visible');
        }, 5000); // 5 saniye sonra mesajı kaldır
    }

    /**
     * 1.5.2. Hata mesajını gizler.
     */
    function hideError() {
        if (!errorMessageElement) return;
        clearTimeout(errorTimeout);
        errorMessageElement.classList.remove('visible');
    }

    // Kontrol butonları ve ilgili event listener'lar bu widget versiyonundan kaldırılmıştır.

    // =============================================
    // 1.6. Başlangıç Çağrısı
    // =============================================
    fetchCurrentlyPlayingData();
    console.log('widget_alt.js (Revize Edilmiş) yüklendi ve çalışıyor.');
});
