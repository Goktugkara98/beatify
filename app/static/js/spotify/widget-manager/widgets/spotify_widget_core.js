/**
 * @file spotify_widget_core.js
 * @description Bu dosya, Spotify widget'ının ana işlevselliğini yönetir.
 * ... (diğer yorumlar aynı)
 */
class SpotifyWidgetCore {
    // constructor, init, fetchData, processData gibi diğer fonksiyonlar öncekiyle aynı...
    constructor(widgetElement) {
        if (!widgetElement) {
            throw new Error("Widget elementi bulunamadı!");
        }

        this.widgetElement = widgetElement;
        this.token = widgetElement.dataset.token;
        this.endpoint = widgetElement.dataset.endpointTemplate.replace('{TOKEN}', this.token);

        // --- Durum Yönetimi (State Management) ---
        this.currentTrackId = null;   // Mevcut şarkının ID'si, değişiklikleri anlamak için.
        this.isPlaying = false;       // Müzik çalıyor mu?
        this.isInitialLoad = true;    // Sayfa ilk defa mı yükleniyor? (Intro animasyonu için)
        this.activeSet = 'a';         // Aktif veri seti ('a' veya 'b'). Geçiş animasyonları için kullanılır.
        this.currentData = null;      // API'den gelen en son veriyi tutar.
        this.config = null;           // Backend'den gelen config verisini tutar.

        // --- Zamanlayıcılar (Timers) ---
        this.progressInterval = null; // Şarkı ilerlemesini güncelleyen setInterval'ı tutar.
        this.pollInterval = null;     // Veri çekme döngüsünü tutar.
        
        // Backend'den gelen config verisini yükle
        this.loadConfig();
    }

    /**
     * Backend'den gelen config verisini yükler.
     */
    loadConfig() {
        try {
            // Global olarak tanımlanmış config verisini kontrol et
            if (window.configData) {
                this.config = window.configData;
                console.log('Config verisi yüklendi:', this.config);
            } else {
                console.warn('Config verisi bulunamadı. HTML içinde tanımlandığından emin olun.');
            }
        } catch (error) {
            console.error('Config verisi yüklenirken hata oluştu:', error);
        }
    }

    /**
     * Widget'ı başlatır. İlk veriyi çeker ve periyodik güncellemeleri ayarlar.
     */
    init() {
        console.log("SpotifyWidgetCore başlatılıyor...");
        this.fetchData(); // İlk veriyi hemen çek
        // Her 5 saniyede bir yeni veri için backend'i kontrol et.
        this.pollInterval = setInterval(() => this.fetchData(), 5000);
    }

    /**
     * Backend API'sinden güncel şarkı bilgilerini çeker.
     */
    async fetchData() {
        try {
            const response = await fetch(this.endpoint);
            if (!response.ok) {
                // API'den hata dönerse (örn. token geçersiz, servis kapalı)
                const errorData = await response.json();
                this.displayError(errorData.error || `Sunucu hatası: ${response.status}`);
                return;
            }
            const data = await response.json();
            this.processData(data);

        } catch (error) {
            // Network hatası veya JSON parse hatası
            console.error("Veri alınırken hata oluştu:", error);
            this.displayError("Widget verisi alınamıyor.");
        }
    }

    /**
     * API'den gelen veriyi işler ve state değişikliklerini belirler.
     * @param {object} data - API'den gelen şarkı bilgisi.
     */
    processData(data) {
        this.clearError(); // Başarılı veri geldiyse eski hataları temizle.
        this.currentData = data; // En son veriyi sakla

        // Durum 1: Müzik çalmıyor veya API'de aktif bir oturum yok.
        if (!data.is_playing) {
            if (this.isPlaying) {
                // Eğer bir önceki durumda çalıyorduysa, şimdi durdu demektir.
                // Outro animasyonu için sinyal ver.
                console.log("Durum: Müzik Durduruldu.");
                this.isPlaying = false;
                this.stopProgressUpdater();
                this.dispatchEvent('widget:outro', { activeSet: this.activeSet });
                this.currentTrackId = null; // Bir sonraki başlangıcı yeni şarkı gibi algıla.
            }
            return; // Müzik çalmıyorsa başka bir işlem yapma.
        }

        // --- Müzik Çalıyor Durumu ---

        // Durum 2: Sayfa ilk defa yükleniyor ve müzik çalıyor.
        if (this.isInitialLoad) {
            console.log("Durum: İlk Yükleme (Intro).");
            this.isPlaying = true;
            this.isInitialLoad = false;
            this.currentTrackId = data.item.id;

            this.updateElements(this.activeSet, data);
            this.startProgressUpdater();

            // Intro animasyonunu tetiklemesi için modern.js'e haber ver.
            this.dispatchEvent('widget:intro', {
                set: this.activeSet,
                data: data
            });
            return;
        }

        // Durum 3: Şarkı değişti.
        if (this.currentTrackId !== data.item.id) {
            console.log("Durum: Şarkı Değişti (Transition).");
            this.isPlaying = true;
            this.stopProgressUpdater(); // Eski şarkının sayacını durdur.

            // Aktif olmayan (pasif) seti belirle ve yeni veriyi ona yükle.
            const passiveSet = this.activeSet === 'a' ? 'b' : 'a';
            this.updateElements(passiveSet, data);

            // Geçiş (transition) animasyonunu tetiklemesi için modern.js'e haber ver.
            // Hangi setin aktif, hangisinin pasif olduğunu bildiriyoruz.
            this.dispatchEvent('widget:transition', {
                activeSet: this.activeSet,
                passiveSet: passiveSet,
                data: data
            });
            
            // Not: activeSet ve currentTrackId, animasyon bittikten sonra
            // modern.js tarafından çağrılacak `finalizeTransition` metodu ile güncellenecek.
            return;
        }
        
        // Durum 4: Aynı şarkı çalmaya devam ediyor.
        // Sadece ilerleme çubuğunu ve zamanı senkronize et.
        if (!this.isPlaying) {
             console.log("Durum: Aynı şarkı çalmaya devam ediyor.");
             this.isPlaying = true; // Durdurulmuş durumdan devam ediyor olabilir.
        }
        this.startProgressUpdater();
    }

    /**
     * Belirtilen veri setindeki ('a' veya 'b') HTML elementlerini günceller.
     * @param {string} set - Güncellenecek set ('a' veya 'b').
     * @param {object} data - API'den gelen veri.
     */
    updateElements(set, data) {
        const item = data.item;
        if (!item) return;
        
        // Kapsayıcıları seç
        const trackNameElem = this.widgetElement.querySelector(`.TrackNameElement[data-set="${set}"]`);
        const artistNameElem = this.widgetElement.querySelector(`.ArtistNameElement[data-set="${set}"]`);
        const coverElem = this.widgetElement.querySelector(`.CoverElement[data-set="${set}"]`);
        const coverBgElem = this.widgetElement.querySelector(`.AlbumArtBackgroundElement[data-set="${set}"]`);
        const totalTimeElem = this.widgetElement.querySelector(`.TotalTimeElement[data-set="${set}"]`);

        // Elementleri doldur
        if (trackNameElem) trackNameElem.innerText = item.name;
        if (artistNameElem) artistNameElem.innerText = item.artists.map(artist => artist.name).join(', ');
        if (coverElem) coverElem.src = item.album.images[0]?.url || '';
        if (coverBgElem) coverBgElem.src = item.album.images[0]?.url || '';
        if (totalTimeElem) totalTimeElem.innerText = this.formatTime(item.duration_ms);
    }
    
    /**
     * Şarkı ilerlemesini ve zaman göstergesini güncelleyen sayacı başlatır/senkronize eder.
     */
    startProgressUpdater() {
        // Zaten çalışan bir sayaç varsa tekrar başlatma.
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        const update = () => {
            const progressMs = this.currentData.progress_ms;
            const durationMs = this.currentData.item.duration_ms;
            
            // Zaman ve ilerleme çubuğu elementlerini seç
            const currentTimeElem = this.widgetElement.querySelector(`.CurrentTimeElement[data-set="${this.activeSet}"]`);
            const progressBarElem = this.widgetElement.querySelector(`.ProgressBarElement[data-set="${this.activeSet}"]`);

            if (currentTimeElem) {
                currentTimeElem.innerText = this.formatTime(progressMs);
            }
            if (progressBarElem) {
                const percentage = durationMs > 0 ? (progressMs / durationMs) * 100 : 0;
                progressBarElem.style.width = `${Math.min(percentage, 100)}%`;
            }
            
            // Bir sonraki saniye için ilerlemeyi artır
            this.currentData.progress_ms += 1000;
        };

        update(); // Hemen bir kez çalıştırarak gecikmeyi önle.
        this.progressInterval = setInterval(update, 1000);
    }

    /**
     * İlerleme sayacını durdurur.
     */
    stopProgressUpdater() {
        clearInterval(this.progressInterval);
        this.progressInterval = null;
    }

    /**
     * Geçiş animasyonu tamamlandığında modern.js tarafından çağrılır.
     * Aktif seti ve mevcut şarkı ID'sini günceller.
     * @param {string} newActiveSet - Yeni aktif setin adı ('a' veya 'b').
     */
    finalizeTransition(newActiveSet) {
        console.log(`Core: Geçiş tamamlandı. Yeni aktif set: ${newActiveSet}`);
        this.activeSet = newActiveSet;
        this.currentTrackId = this.currentData.item.id;
        this.startProgressUpdater(); // Yeni şarkı için sayacı başlat.

        // --- YENİ EKLENEN KISIM ---
        // Eski seti belirle ve verilerini temizle.
        const oldSet = newActiveSet === 'a' ? 'b' : 'a';
        console.log(`Core: Eski set (${oldSet}) verileri sıfırlanıyor.`);
        this.resetSetData(oldSet);
        // --- YENİ EKLENEN KISIM SONU ---
    }
    
    /**
     * YENİ FONKSİYON: Belirtilen setteki elementlerin içeriğini sıfırlar.
     * Bu, bir sonraki geçişte eski verilerin anlık görünmesini engeller.
     * @param {string} set - Sıfırlanacak set ('a' veya 'b').
     */
    resetSetData(set) {
        const trackNameElem = this.widgetElement.querySelector(`.TrackNameElement[data-set="${set}"]`);
        const artistNameElem = this.widgetElement.querySelector(`.ArtistNameElement[data-set="${set}"]`);
        const coverElem = this.widgetElement.querySelector(`.CoverElement[data-set="${set}"]`);
        const coverBgElem = this.widgetElement.querySelector(`.AlbumArtBackgroundElement[data-set="${set}"]`);
        const totalTimeElem = this.widgetElement.querySelector(`.TotalTimeElement[data-set="${set}"]`);
        const currentTimeElem = this.widgetElement.querySelector(`.CurrentTimeElement[data-set="${set}"]`);
        const progressBarElem = this.widgetElement.querySelector(`.ProgressBarElement[data-set="${set}"]`);

        if (trackNameElem) trackNameElem.innerText = '';
        if (artistNameElem) artistNameElem.innerText = '';
        if (coverElem) coverElem.src = '';
        if (coverBgElem) coverBgElem.src = '';
        if (totalTimeElem) totalTimeElem.innerText = '0:00';
        if (currentTimeElem) currentTimeElem.innerText = '0:00';
        if (progressBarElem) progressBarElem.style.width = '0%';
    }

    /**
     * Widget üzerinde özel bir olay (CustomEvent) yayınlar.
     * modern.js bu olayları dinleyerek animasyonları tetikler.
     * @param {string} eventName - Olayın adı (örn: 'widget:intro').
     * @param {object} detail - Olaya eklenecek veri.
     */
    dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, {
            bubbles: true, // Olayın DOM'da yukarı doğru köpürmesini sağlar.
            composed: true, // Shadow DOM sınırlarını aşmasını sağlar.
            detail: detail
        });
        this.widgetElement.dispatchEvent(event);
    }

    /**
     * Widget'ta bir hata mesajı gösterir.
     * @param {string} message - Gösterilecek hata mesajı.
     */
    displayError(message) {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement) {
            errorElement.innerText = message;
            this.widgetElement.classList.add('error-active');
        }
        this.stopProgressUpdater(); // Hata durumunda her şeyi durdur.
    }
    
    /**
     * Hata mesajını temizler.
     */
    clearError() {
         const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement && errorElement.innerText !== '') {
            errorElement.innerText = '';
            this.widgetElement.classList.remove('error-active');
        }
    }

    /**
     * Milisaniyeyi "dakika:saniye" formatına çevirir.
     * @param {number} ms - Milisaniye.
     * @returns {string} Formatlanmış zaman (örn: "3:45").
     */
    formatTime(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}

// DOM tamamen yüklendiğinde widget'ı başlat.
document.addEventListener('DOMContentLoaded', () => {
    const widgetElement = document.getElementById('spotifyWidgetModern');
    if (widgetElement) {
        window.spotifyWidget = new SpotifyWidgetCore(widgetElement);
        window.spotifyWidget.init();
    } else {
        console.error("Spotify widget ana elementi ('spotifyWidgetModern') bulunamadı.");
    }
});