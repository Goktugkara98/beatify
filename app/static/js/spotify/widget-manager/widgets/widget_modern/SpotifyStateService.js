// ===================================================================================
// DOSYA ADI: SpotifyStateService.js
// AÇIKLAMA: Spotify API'sinden veri çeker, durumu yönetir ve olayları tetikler.
// YENİ YAPI NOTU: Her 'fetchData' çağrısı kendi ana grubunu oluşturur.
//                 'processData' ve 'dispatchEvent' gibi adımlar alt grup olarak
//                 loglanır. Bu sayede her bir veri çekme döngüsü izole
//                 bir şekilde incelenebilir.
// ===================================================================================
class SpotifyStateService {
    constructor(widgetElement, logger) {
        this.logger = logger;
        this.CALLER_FILE = 'SpotifyStateService.js';
        
        if (!widgetElement) {
            const error = new Error("SpotifyStateService için bir widget elementi sağlanmalıdır!");
            this.logger.error(this.CALLER_FILE, 'Constructor Hatası:', error);
            throw error;
        }

        this.widgetElement = widgetElement;
        this.token = widgetElement.dataset.token;
        this.endpoint = widgetElement.dataset.endpointTemplate.replace('{TOKEN}', this.token);
        this.logger.info(this.CALLER_FILE, `SpotifyStateService oluşturuldu. Endpoint: ${this.endpoint}`);

        this.currentTrackId = null;
        this.isPlaying = false;
        this.isInitialLoad = true;
        this.activeSet = 'a';
        this.currentData = null;
        this.pollInterval = null;
        this.pollCount = 0;
    }

    init() {
        this.logger.info(this.CALLER_FILE, "Servis başlatılıyor (init). Veri yoklama döngüsü başlayacak.");
        this.fetchData();
        this.pollInterval = setInterval(() => {
            this.pollCount++;
            this.fetchData();
        }, 5000);
    }

    async fetchData() {
        this.logger.group(`VERİ ÇEKME DÖNGÜSÜ #${this.pollCount}`);
        const startTime = performance.now();
        try {
            const response = await fetch(this.endpoint);
            const fetchTime = performance.now() - startTime;

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.error || `Sunucu hatası: ${response.status}`;
                this.logger.error(this.CALLER_FILE, `API Hatası (${response.status}): ${errorMessage}`, `Süre: ${fetchTime.toFixed(2)}ms`);
                this.dispatchEvent('widget:error', { message: errorMessage });
                return;
            }

            const data = await response.json();
            this.logger.info(this.CALLER_FILE, `Veri başarıyla çekildi.`, `Süre: ${(performance.now() - startTime).toFixed(2)}ms`);
            this.processData(data);
        } catch (error) {
            this.logger.error(this.CALLER_FILE, `Fetch sırasında kritik hata: ${error.message || 'Bilinmeyen hata'}`, error);
            this.dispatchEvent('widget:error', { message: `Widget verisi alınamıyor.` });
        } finally {
            this.logger.groupEnd(); // Her durumda veri çekme döngüsü grubunu kapat
        }
    }

    processData(data) {
        this.logger.subgroup('[StateService] Gelen Veri İşleniyor');
        try {
            this.logger.data(this.CALLER_FILE, "Gelen Ham Veri", data);

            this.dispatchEvent('widget:clear-error');
            this.currentData = data;

            if (!data.is_playing) {
                if (this.isPlaying) {
                    this.logger.action(this.CALLER_FILE, "Durum Değişikliği: Müzik durdu. 'Outro' tetikleniyor.");
                    this.isPlaying = false;
                    this.currentTrackId = null;
                    this.dispatchEvent('widget:outro', { activeSet: this.activeSet });
                } else {
                    this.logger.info(this.CALLER_FILE, "Müzik hala çalmıyor, durum değişikliği yok.");
                }
                return;
            }

            if (this.isInitialLoad) {
                this.logger.action(this.CALLER_FILE, "Durum Değişikliği: İlk yükleme. 'Intro' tetikleniyor.");
                this.isPlaying = true;
                this.isInitialLoad = false;
                this.currentTrackId = data.item.id;
                this.dispatchEvent('widget:intro', { set: this.activeSet, data: data });
                return;
            }

            if (this.currentTrackId !== data.item.id) {
                this.logger.action(this.CALLER_FILE, `Durum Değişikliği: Şarkı değişti. 'Transition' tetikleniyor.`);
                this.logger.info(this.CALLER_FILE, `Eski ID: ${this.currentTrackId} -> Yeni ID: ${data.item.id}`);
                this.isPlaying = true;
                const passiveSet = this.activeSet === 'a' ? 'b' : 'a';
                this.dispatchEvent('widget:transition', { activeSet: this.activeSet, passiveSet: passiveSet, data: data });
                return;
            }
            
            this.logger.info(this.CALLER_FILE, "Aynı şarkı çalıyor. 'Sync' tetikleniyor.");
            this.dispatchEvent('widget:sync', { data: data, set: this.activeSet });

        } finally {
            this.logger.groupEnd(); // Veri işleme alt grubunu kapat
        }
    }

    finalizeTransition(newActiveSet) {
        this.logger.subgroup('[StateService] Geçiş Sonlandırılıyor');
        try {
            this.activeSet = newActiveSet;
            this.currentTrackId = this.currentData.item.id;
            this.logger.info(this.CALLER_FILE, `Aktif set güncellendi: '${newActiveSet}'`);
            this.logger.info(this.CALLER_FILE, `Mevcut şarkı ID'si doğrulandı: ${this.currentTrackId}`);
            this.dispatchEvent('widget:sync', { data: this.currentData, set: this.activeSet });
        } finally {
            this.logger.groupEnd();
        }
    }

    dispatchEvent(eventName, detail = {}) {
        this.logger.subgroup(`[StateService] Olay Gönderiliyor: ${eventName}`);
        try {
            this.logger.data(this.CALLER_FILE, "Olay Detayları", detail);
            const event = new CustomEvent(eventName, { detail: detail });
            this.widgetElement.dispatchEvent(event);
        } finally {
            this.logger.groupEnd();
        }
    }
}
