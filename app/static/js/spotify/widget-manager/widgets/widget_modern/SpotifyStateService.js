// YENİ DOSYA ADI: SpotifyStateService.js

class SpotifyStateService {
    constructor(widgetElement) {
        if (!widgetElement) throw new Error("Widget elementi bulunamadı!"); //

        this.widgetElement = widgetElement; //
        this.token = widgetElement.dataset.token; //
        this.endpoint = widgetElement.dataset.endpointTemplate.replace('{TOKEN}', this.token); //

        // --- Durum Yönetimi ---
        this.currentTrackId = null; //
        this.isPlaying = false; //
        this.isInitialLoad = true; //
        this.activeSet = 'a'; //
        this.currentData = null; //
        this.pollInterval = null; //
    }

    init() {
        this.fetchData(); //
        this.pollInterval = setInterval(() => this.fetchData(), 5000); //
    }

    async fetchData() {
        try {
            const response = await fetch(this.endpoint); //
            if (!response.ok) { //
                const errorData = await response.json(); //
                this.dispatchEvent('widget:error', { message: errorData.error || `Sunucu hatası: ${response.status}` }); //
                return;
            }
            const data = await response.json(); //
            this.processData(data); //
        } catch (error) {
            this.dispatchEvent('widget:error', { message: "Widget verisi alınamıyor." }); //
        }
    }

    processData(data) {
        this.dispatchEvent('widget:clear-error'); //
        this.currentData = data; //

        if (!data.is_playing) { //
            if (this.isPlaying) { //
                this.isPlaying = false; //
                this.dispatchEvent('widget:outro', { activeSet: this.activeSet }); //
                this.currentTrackId = null; //
            }
            return;
        }

        if (this.isInitialLoad) { //
            this.isPlaying = true; //
            this.isInitialLoad = false; //
            this.currentTrackId = data.item.id; //
            this.dispatchEvent('widget:intro', { set: this.activeSet, data: data }); //
            return;
        }

        if (this.currentTrackId !== data.item.id) { //
            this.isPlaying = true; //
            const passiveSet = this.activeSet === 'a' ? 'b' : 'a'; //
            this.dispatchEvent('widget:transition', { //
                activeSet: this.activeSet, //
                passiveSet: passiveSet, //
                data: data //
            });
            return;
        }
        
        // --- DEĞİŞTİ: Artık direkt sayaç başlatmıyor, sadece durumu bildiriyor ---
        if (!this.isPlaying) { //
             this.isPlaying = true; //
        }
        this.dispatchEvent('widget:sync', { data: data, set: this.activeSet });
    }

    // --- DEĞİŞTİ: Bu metot artık `WidgetDOMManager` tarafından çağrılacak ---
    finalizeTransition(newActiveSet) {
        this.activeSet = newActiveSet; //
        this.currentTrackId = this.currentData.item.id; //
        // Olay, yeni setin senkronize edilmesi gerektiğini bildirir.
        this.dispatchEvent('widget:sync', { data: this.currentData, set: this.activeSet }); //
    }
    
    // --- KALDIRILDI ---
    // updateElements, resetSetData, startProgressUpdater, stopProgressUpdater,
    // displayError, clearError, formatTime gibi tüm DOM ve formatlama
    // fonksiyonları bu dosyadan kaldırıldı.

    dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail: detail }); //
        this.widgetElement.dispatchEvent(event); //
    }
}