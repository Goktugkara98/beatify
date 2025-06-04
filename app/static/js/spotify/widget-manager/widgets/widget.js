/*
    widget.js (Revize Edilmiş)

    İÇİNDEKİLER:

    1. DOM YÜKLENDİĞİNDE ÇALIŞACAK ANA FONKSİYON (DOMContentLoaded)
        1.1. Değişken Tanımlamaları
            1.1.1. DOM Elementleri
            1.1.2. Global Durum Değişkenleri
        1.2. Token Alma İşlemleri
            1.2.1. window.WIDGET_TOKEN Kontrolü
            1.2.2. URL Path'ten Token Alma
            1.2.3. iFrame Src'den Token Alma
            1.2.4. URL Query Parametresinden Token Alma
            1.2.5. Token Bulunamama Durumu
        1.3. Yardımcı Fonksiyonlar
            1.3.1. msToTimeFormat(ms)
        1.4. Ana Veri Çekme ve İşleme Fonksiyonları
            1.4.1. fetchCurrentlyPlayingData()
            1.4.2. updateUI(data)
            1.4.3. updatePlayPauseButton(isPlaying) (Not: Butonlar kaldırıldığı için işlevsiz)
            1.4.4. updateProgressBar(progressMs, durationMs, isPlaying)
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
    const spotifyWidgetElement = document.getElementById('spotifyWidget');
    const albumArtElement = document.getElementById('albumArt');
    const albumArtBackgroundElement = document.getElementById('albumArtBackground');
    const trackNameElement = document.getElementById('trackName');
    const artistNameElement = document.getElementById('artistName');
    // const progressBarContainer = document.getElementById('progressBarContainer'); // Kullanılmıyorsa kaldırılabilir
    const progressBarElement = document.getElementById('progressBar');
    const currentTimeElement = document.getElementById('currentTime');
    const totalTimeElement = document.getElementById('totalTime');
    const errorMessageElement = document.getElementById('errorMessage');
    const overlayContentElement = document.getElementById('overlayContent');

    // 1.1.2. Global Durum Değişkenleri
    let WIDGET_TOKEN; // Spotify API token'ı
    // let currentTrackData = null; // Mevcut şarkı verisi, aktif kullanılmıyor gibi, ihtiyaç halinde açılabilir
    let _isPlaying = false; // Şarkının çalma durumu
    let progressInterval = null; // İlerleme çubuğu için zamanlayıcı
    let fetchTimeoutId = null; // Veri çekme için zamanlayıcı ID'si

    // =============================================
    // 1.2. Token Alma İşlemleri
    // =============================================
    console.log('Widget token aranıyor (widget.js)...');

    // 1.2.1. window.WIDGET_TOKEN Kontrolü
    if (typeof window.WIDGET_TOKEN !== 'undefined' && window.WIDGET_TOKEN && window.WIDGET_TOKEN !== "{{ config.widgetToken|safe }}") {
        WIDGET_TOKEN = window.WIDGET_TOKEN;
        console.log('Token HTML global değişkeninden (window.WIDGET_TOKEN) alındı:', WIDGET_TOKEN);
    }

    // 1.2.2. URL Path'ten Token Alma
    if (!WIDGET_TOKEN) {
        const pathParts = window.location.pathname.split('/');
        const widgetPathIndex = pathParts.findIndex(part => part === 'widget');
        if (widgetPathIndex !== -1 && pathParts.length > widgetPathIndex + 1) {
            const tokenFromPath = pathParts[widgetPathIndex + 1];
            if (tokenFromPath && tokenFromPath.length > 8) { // Basit bir token geçerlilik kontrolü
                WIDGET_TOKEN = tokenFromPath;
                console.log('Token URL path\'ten alındı:', WIDGET_TOKEN);
            }
        }
    }

    // 1.2.3. iFrame Src'den Token Alma
    if (!WIDGET_TOKEN) {
        try {
            if (window.self !== window.top) { // iframe içinde mi?
                const iframeSrc = window.location.href;
                if (iframeSrc.includes('/widget/')) {
                    const srcParts = iframeSrc.split('/widget/');
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

    // 1.2.4. URL Query Parametresinden Token Alma
    if (!WIDGET_TOKEN) {
        const urlParams = new URLSearchParams(window.location.search);
        const tokenParam = urlParams.get('token');
        if (tokenParam && tokenParam.length > 8) {
            WIDGET_TOKEN = tokenParam;
            console.log('Token URL query parametresinden alındı:', WIDGET_TOKEN);
        }
    }

    // 1.2.5. Token Bulunamama Durumu
    if (!WIDGET_TOKEN) {
        console.error('Widget token bulunamadı! Widget çalıştırılamıyor.');
        if (errorMessageElement) {
            errorMessageElement.textContent = 'Widget token konfigürasyonu eksik. Widget çalıştırılamıyor.';
            errorMessageElement.classList.remove('hidden'); // 'hidden' yerine 'visible' class'ı yönetilebilir
            errorMessageElement.classList.add('visible');
        }
        if (spotifyWidgetElement) spotifyWidgetElement.classList.add('pointer-events-none', 'opacity-50');
        return; // Token yoksa devam etme
    }
    console.log('Kullanılacak Widget Token (widget.js):', WIDGET_TOKEN);

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
            const response = await fetch(`/spotify/api/widget-data/${WIDGET_TOKEN}`);
            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                console.error('Veri çekme hatası:', response.status, errorData);
                let userMessage = 'Veri alınamadı veya çalınan bir şey yok.';
                if (response.status === 401 || response.status === 403) userMessage = "Yetkilendirme hatası. Token geçersiz olabilir.";
                else if (errorData && errorData.error) userMessage = errorData.error;
                showError(userMessage);
                updateUI(null);
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, 15000); // 15 saniye sonra tekrar dene
                return;
            }

            const data = await response.json();

            if (data && (data.is_playing !== undefined || (data.item && data.item.name))) {
                // currentTrackData = data; // İhtiyaç halinde saklanabilir
                _isPlaying = data.is_playing;
                updateUI(data);
                hideError();
                const refreshInterval = _isPlaying ? 7000 : 15000; // Çalıyorsa 7sn, çalmıyorsa 15sn
                fetchTimeoutId = setTimeout(fetchCurrentlyPlayingData, refreshInterval);
            } else if (data && data.error) {
                console.error('API Hatası:', data.error);
                showError(data.error === "Player command failed: No active device found" ? "Aktif bir cihaz bulunamadı." : (data.error.message || data.error || "Bilinmeyen bir API hatası oluştu."));
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

    /**
     * 1.4.2. Gelen verilere göre kullanıcı arayüzünü günceller.
     * @param {object|null} data - Spotify API'den gelen veri veya null.
     */
    function updateUI(data) {
        if (data && (data.item || data.track_name)) { // Veri varsa ve şarkı bilgisi içeriyorsa
            const trackName = data.item ? data.item.name : (data.track_name || "Bilinmiyor");
            const artistName = data.item && data.item.artists ? data.item.artists.map(artist => artist.name).join(', ') : (data.artist_name || "-");
            let albumImageUrl = 'https://placehold.co/300x250/1f2937/e5e7eb?text=Beatify'; // Varsayılan placeholder

            if (data.item && data.item.album && data.item.album.images && data.item.album.images.length > 0) {
                albumImageUrl = data.item.album.images.reduce((prev, curr) => {
                    return (Math.abs(curr.width - 300) < Math.abs(prev.width - 300) ? curr : prev);
                }).url || data.item.album.images[0].url;
            } else if (data.album_image_url) {
                albumImageUrl = data.album_image_url;
            }

            if (trackNameElement) {
                trackNameElement.textContent = trackName;
                trackNameElement.title = trackName; // Tooltip için
            }
            if (artistNameElement) {
                artistNameElement.textContent = artistName;
                artistNameElement.title = artistName; // Tooltip için
            }

            if (albumArtElement && albumArtElement.src !== albumImageUrl) {
                albumArtElement.classList.add('opacity-0');
                if (albumArtBackgroundElement) albumArtBackgroundElement.classList.add('opacity-0');

                setTimeout(() => {
                    albumArtElement.src = albumImageUrl;
                    if (albumArtBackgroundElement) albumArtBackgroundElement.src = albumImageUrl; // Arka plan için de aynı resim

                    albumArtElement.onload = () => {
                        albumArtElement.classList.remove('opacity-0');
                        if (albumArtBackgroundElement) albumArtBackgroundElement.classList.remove('opacity-0');
                    };
                    albumArtElement.onerror = () => { // Resim yüklenemezse
                        const errorPlaceholder = 'https://placehold.co/300x250/1f2937/e5e7eb?text=Hata';
                        albumArtElement.src = errorPlaceholder;
                        if (albumArtBackgroundElement) albumArtBackgroundElement.src = errorPlaceholder;
                        albumArtElement.classList.remove('opacity-0');
                        if (albumArtBackgroundElement) albumArtBackgroundElement.classList.remove('opacity-0');
                    };
                }, 100); // CSS geçiş süresiyle uyumlu
            } else if (albumArtElement && albumArtElement.classList.contains('opacity-0')) { // Eğer src aynı ama gizliyse görünür yap
                albumArtElement.classList.remove('opacity-0');
                if (albumArtBackgroundElement) albumArtBackgroundElement.classList.remove('opacity-0');
            }

            _isPlaying = data.is_playing !== undefined ? data.is_playing : false;
            // updatePlayPauseButton(_isPlaying); // Butonlar kaldırıldığı için çağrılmıyor

            const progressMs = data.progress_ms !== undefined ? data.progress_ms : 0;
            const durationMs = data.item ? data.item.duration_ms : (data.duration_ms || 0);

            if (totalTimeElement) totalTimeElement.textContent = msToTimeFormat(durationMs);
            updateProgressBar(progressMs, durationMs, _isPlaying);

            if (overlayContentElement) overlayContentElement.classList.remove('opacity-0'); // Şarkı bilgisi varsa overlay'i göster

        } else { // Çalınan bir şey yoksa veya veri eksikse
            if (trackNameElement) {
                trackNameElement.textContent = 'Bir şey çalmıyor';
                trackNameElement.title = 'Bir şey çalmıyor';
            }
            if (artistNameElement) artistNameElement.textContent = '-';

            const placeholderUrl = 'https://placehold.co/300x250/1f2937/e5e7eb?text=Beatify';
            if (albumArtElement && albumArtElement.src !== placeholderUrl) {
                albumArtElement.classList.add('opacity-0');
                if (albumArtBackgroundElement) albumArtBackgroundElement.classList.add('opacity-0');
                setTimeout(() => {
                    albumArtElement.src = placeholderUrl;
                    if (albumArtBackgroundElement) albumArtBackgroundElement.src = placeholderUrl;
                    albumArtElement.onload = () => {
                         albumArtElement.classList.remove('opacity-0');
                         if (albumArtBackgroundElement) albumArtBackgroundElement.classList.remove('opacity-0');
                    }
                }, 100);
            } else if (albumArtElement && albumArtElement.classList.contains('opacity-0') && albumArtElement.src.includes('placehold.co')) {
                albumArtElement.classList.remove('opacity-0'); // Placeholder ise zaten görünür olsun
                if (albumArtBackgroundElement) albumArtBackgroundElement.classList.remove('opacity-0');
            }


            updateProgressBar(0, 1, false); // İlerleme çubuğunu ve zamanı sıfırla
            if (currentTimeElement) currentTimeElement.textContent = "0:00";
            if (totalTimeElement) totalTimeElement.textContent = "0:00";
            // if (overlayContentElement) overlayContentElement.classList.add('opacity-0'); // Şarkı yoksa overlay gizlenebilir
        }
    }

    /**
     * 1.4.3. Oynat/Duraklat butonunun durumunu günceller.
     * (Not: Bu widget versiyonunda butonlar kaldırıldığı için bu fonksiyon UI'ı etkilemez.)
     * @param {boolean} isPlaying - Şarkının çalma durumu.
     */
    function updatePlayPauseButton(isPlaying) {
        // Bu fonksiyon, butonlar widget'tan kaldırıldığı için artık UI güncellemesi yapmamaktadır.
        // Mantığı burada tutulabilir, eğer butonlar geri eklenirse diye.
    }

    /**
     * 1.4.4. Şarkı ilerleme çubuğunu ve zamanını günceller.
     * @param {number} progressMs - Mevcut ilerleme (ms).
     * @param {number} durationMs - Toplam süre (ms).
     * @param {boolean} isPlaying - Şarkının çalma durumu.
     */
    function updateProgressBar(progressMs, durationMs, isPlaying) {
        if (progressInterval) clearInterval(progressInterval);
        progressInterval = null;

        if (!progressBarElement || !currentTimeElement || !durationMs || durationMs <= 0) {
            if (progressBarElement) progressBarElement.style.width = '0%';
            if (currentTimeElement) currentTimeElement.textContent = msToTimeFormat(0);
            return;
        }

        let currentProgress = progressMs;

        const updateDOM = () => {
            const percentage = Math.min(100, (currentProgress / durationMs) * 100);
            progressBarElement.style.width = `${percentage}%`;
            currentTimeElement.textContent = msToTimeFormat(currentProgress);
        };

        updateDOM(); // İlk güncellemeyi hemen yap

        if (isPlaying) {
            progressInterval = setInterval(() => {
                currentProgress += 1000; // Her saniye artır
                if (currentProgress >= durationMs) {
                    currentProgress = durationMs; // Süreyi aşmasın
                    updateDOM();
                    clearInterval(progressInterval);
                    progressInterval = null;
                    // Şarkı bittiğinde veriyi daha hızlı yenilemek için
                    setTimeout(fetchCurrentlyPlayingData, 1200); // Kısa bir gecikmeyle
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
        errorMessageElement.classList.add('visible');
        errorMessageElement.classList.remove('fade'); // Eğer fade animasyonu varsa, görünür yapmadan önce kaldır

        clearTimeout(errorTimeout); // Önceki zaman aşımını temizle
        errorTimeout = setTimeout(() => {
            errorMessageElement.classList.add('fade'); // Yavaşça kaybolması için class ekle
            // 'fade' animasyonu tamamlandıktan sonra 'visible' class'ını kaldır
            setTimeout(() => errorMessageElement.classList.remove('visible'), 300); // CSS transition süresiyle uyumlu
        }, 5000); // 5 saniye sonra mesajı kaldır
    }

    /**
     * 1.5.2. Hata mesajını gizler.
     */
    function hideError() {
        if (!errorMessageElement) return;
        clearTimeout(errorTimeout);
        errorMessageElement.classList.add('fade');
        setTimeout(() => errorMessageElement.classList.remove('visible'), 300);
    }

    // Kontrol butonları ve ilgili event listener'lar bu widget versiyonundan kaldırılmıştır.

    // =============================================
    // 1.6. Başlangıç Çağrısı
    // =============================================
    fetchCurrentlyPlayingData(); // Sayfa yüklendiğinde veriyi çek
    // Periyodik veri çekme artık fetchCurrentlyPlayingData fonksiyonu içinde yönetiliyor.
    console.log('widget.js (Revize Edilmiş) yüklendi ve çalışıyor.');
});
