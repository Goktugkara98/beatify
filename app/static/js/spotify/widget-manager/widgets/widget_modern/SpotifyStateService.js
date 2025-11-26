class SpotifyStateService {
    constructor(widgetElement) {
        this.widgetElement = widgetElement;
        const token = widgetElement.dataset.token;
        const endpointTemplate = widgetElement.dataset.endpointTemplate;
        this.endpoint = endpointTemplate.replace('{TOKEN}', token);
        console.log('[SpotifyStateService] Initialized with token:', token, 'endpoint:', this.endpoint);

        this.currentTrackId = null;
        this.isPlaying = false;
        this.isInitialLoad = true;
        this.activeSet = 'a';
        this.currentData = null;
    }

    init() {
        console.log('[SpotifyStateService] init() called. Starting polling loop...');
        this.fetchData();
        setInterval(() => this.fetchData(), 2000);
    }

    async fetchData() {
        try {
            console.log('[SpotifyStateService] fetchData() ->', this.endpoint);
            const response = await fetch(this.endpoint);
            console.log('[SpotifyStateService] fetchData() response status:', response.status);
            if (!response.ok) {
                if (this.isPlaying || this.isInitialLoad) {
                    this._dispatchEvent('widget:error', { message: `API Hatası: ${response.status}` });
                }
                this.isPlaying = false;
                return;
            }
            const data = await response.json();
            console.log('[SpotifyStateService] fetchData() JSON alındı:', {
                is_playing: data && data.is_playing,
                track_id: data && data.item && data.item.id
            });
            this._processData(data);
        } catch (error) {
            console.error('[SpotifyStateService] fetchData() sırasında hata:', error);
            this._dispatchEvent('widget:error', { message: 'Widget verisi alınamıyor.' });
            this.isPlaying = false;
        }
    }

    finalizeTransition(newActiveSet) {
        this.activeSet = newActiveSet;
        if (this.currentData && this.currentData.item) {
            this.currentTrackId = this.currentData.item.id;
        }
    }

    _processData(data) {
        this._dispatchEvent('widget:clear-error');
        this.currentData = data;

        const isNowPlaying = data && data.item && data.is_playing;
        const newTrackId = isNowPlaying ? data.item.id : null;
        console.log('[SpotifyStateService] _processData()', {
            isNowPlaying,
            newTrackId,
            currentTrackId: this.currentTrackId,
            isInitialLoad: this.isInitialLoad,
            activeSet: this.activeSet
        });

        if (!isNowPlaying) {
            if (this.isPlaying) {
                this.isPlaying = false;
                this.currentTrackId = null;
                this.isInitialLoad = true;
                console.log('[SpotifyStateService] Çalma durdu, widget pasifleştiriliyor.');
                this.widgetElement.classList.add('widget-inactive');
                this.widgetElement.classList.remove('widget-active');
                this._dispatchEvent('widget:outro', { activeSet: this.activeSet });
            }
            return;
        }

        if (this.isInitialLoad) {
            this.isPlaying = true;
            this.isInitialLoad = false;
            this.currentTrackId = newTrackId;
            console.log('[SpotifyStateService] İlk yükleme, intro animasyonu tetikleniyor. set=', this.activeSet);
            this._dispatchEvent('widget:intro', { set: this.activeSet, data: data });
            return;
        }

        if (this.currentTrackId !== newTrackId) {
            this.isPlaying = true;
            this.currentTrackId = newTrackId;
            console.log('[SpotifyStateService] Parça değişti, transition tetikleniyor. eskiSet=', this.activeSet);
            this.widgetElement.classList.remove('widget-inactive');
            this.widgetElement.classList.add('widget-active');
            const nextSet = this.activeSet === 'a' ? 'b' : 'a';
            this._dispatchEvent('widget:transition', {
                activeSet: this.activeSet,
                passiveSet: nextSet,
                data: data
            });
            this.activeSet = nextSet;
            return;
        }

        if (this.isPlaying) {
            console.log('[SpotifyStateService] Aynı parça çalıyor, sync olayı tetikleniyor. set=', this.activeSet);
            this._dispatchEvent('widget:sync', { data: data, set: this.activeSet });
        }
    }

    _dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        this.widgetElement.dispatchEvent(event);
    }
}
