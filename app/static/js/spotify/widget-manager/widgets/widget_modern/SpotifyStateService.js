// ===================================================================================
// DOSYA ADI: SpotifyStateService.js
// ===================================================================================
class SpotifyStateService {
    // DEĞİŞTİ: constructor'a logger parametresi eklendi
    constructor(widgetElement, logger) {
        // YENİ: Logger'ı sınıf içinde sakla
        this.logger = logger;
        this.logger.subgroup('SpotifyStateService Kurulumu (constructor)');

        if (!widgetElement) throw new Error("SpotifyStateService için bir widget elementi sağlanmalıdır!");

        this.widgetElement = widgetElement;
        this.token = widgetElement.dataset.token;
        this.endpoint = widgetElement.dataset.endpointTemplate.replace('{TOKEN}', this.token);
        this.logger.info(`Endpoint ayarlandı: ${this.endpoint}`);

        this.currentTrackId = null;
        this.isPlaying = false;
        this.isInitialLoad = true;
        this.activeSet = 'a';
        this.currentData = null;
        this.pollInterval = null;
        this.pollCount = 0;

        this.logger.groupEnd();
    }

    init() {
        this.logger.subgroup('Servis Başlatılıyor (init)');
        this.logger.info("Veri yoklama (polling) döngüsü başlıyor.");
        this.fetchData();
        this.pollInterval = setInterval(() => {
            this.pollCount++;
            this.fetchData();
        }, 5000);
        this.logger.groupEnd();
    }

    async fetchData() {
        this.logger.subgroup(`Veri Çekiliyor (fetchData) - İstek #${this.pollCount}`);
        const startTime = performance.now();
        try {
            const response = await fetch(this.endpoint);
            const fetchTime = performance.now() - startTime;

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.error || `Sunucu hatası: ${response.status}`;
                this.logger.error(`API Hatası (${response.status}): ${errorMessage}`, `Süre: ${fetchTime.toFixed(2)}ms`);
                this.dispatchEvent('widget:error', { message: errorMessage });
                return;
            }

            const data = await response.json();
            const totalTime = performance.now() - startTime;
            this.logger.info(`Veri başarıyla çekildi.`, `Süre: ${totalTime.toFixed(2)}ms`);
            this.processData(data);
        } catch (error) {
            const totalTime = performance.now() - startTime;
            this.logger.error(`Fetch sırasında kritik hata oluştu:`, error, `Süre: ${totalTime.toFixed(2)}ms`);
            this.dispatchEvent('widget:error', {
                message: `Widget verisi alınamıyor: ${error.message || 'Bilinmeyen hata'}`
            });
        } finally {
            this.logger.groupEnd();
        }
    }

    processData(data) {
        this.logger.group('VERİ İŞLENİYOR (processData)');
        this.logger.data("Gelen Ham Veri", data);

        this.dispatchEvent('widget:clear-error');
        this.currentData = data;

        if (!data.is_playing) {
            if (this.isPlaying) {
                this.logger.action("Durum Değişikliği: Müzik durdu. 'Outro' animasyonu tetikleniyor.");
                this.isPlaying = false;
                this.currentTrackId = null;
                this.dispatchEvent('widget:outro', { activeSet: this.activeSet });
            } else {
                this.logger.info("Müzik hala çalmıyor, durum değişikliği yok.");
            }
            this.logger.groupEnd();
            return;
        }

        if (this.isInitialLoad) {
            this.logger.action("Durum Değişikliği: İlk yükleme ve müzik çalıyor. 'Intro' animasyonu tetikleniyor.");
            this.isPlaying = true;
            this.isInitialLoad = false;
            this.currentTrackId = data.item.id;
            this.dispatchEvent('widget:intro', { set: this.activeSet, data: data });
            this.logger.groupEnd();
            return;
        }

        if (this.currentTrackId !== data.item.id) {
            this.logger.action(`Durum Değişikliği: Şarkı değişti. 'Transition' animasyonu tetikleniyor.`);
            this.logger.info(`Eski Şarkı ID: ${this.currentTrackId}`);
            this.logger.info(`Yeni Şarkı ID: ${data.item.id}`);
            this.isPlaying = true;
            const passiveSet = this.activeSet === 'a' ? 'b' : 'a';
            this.dispatchEvent('widget:transition', {
                activeSet: this.activeSet,
                passiveSet: passiveSet,
                data: data
            });
            this.logger.groupEnd();
            return;
        }

        if (!this.isPlaying) {
            this.logger.action("Durum Değişikliği: Müzik duraklatıldıktan sonra devam etti.");
            this.isPlaying = true;
        } else {
            this.logger.info("Aynı şarkı çalmaya devam ediyor, durum senkronize edilecek.");
        }
        this.dispatchEvent('widget:sync', { data: data, set: this.activeSet });
        this.logger.groupEnd();
    }

    finalizeTransition(newActiveSet) {
        this.logger.subgroup('Geçiş Sonlandırılıyor (finalizeTransition)');
        this.activeSet = newActiveSet;
        this.currentTrackId = this.currentData.item.id;
        this.logger.info(`Aktif set güncellendi: '${newActiveSet}'`);
        this.logger.info(`Mevcut şarkı ID'si doğrulandı: ${this.currentTrackId}`);
        this.dispatchEvent('widget:sync', { data: this.currentData, set: this.activeSet });
        this.logger.groupEnd();
    }

    dispatchEvent(eventName, detail = {}) {
        this.logger.subgroup(`Olay Gönderiliyor: ${eventName}`);
        this.logger.data("Olay Detayları", detail);
        const event = new CustomEvent(eventName, { detail: detail });
        this.widgetElement.dispatchEvent(event);
        this.logger.groupEnd();
    }
}
