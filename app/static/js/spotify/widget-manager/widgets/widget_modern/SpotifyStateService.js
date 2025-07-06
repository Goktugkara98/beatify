class SpotifyStateService {
    constructor(widgetElement) {
        this.widgetElement = widgetElement;
        const token = widgetElement.dataset.token;
        const endpointTemplate = widgetElement.dataset.endpointTemplate;
        this.endpoint = endpointTemplate.replace('{TOKEN}', token);

        this.currentTrackId = null;
        this.isPlaying = false;
        this.isInitialLoad = true;
        this.activeSet = 'a';
        this.currentData = null;
    }

    init() {
        this.fetchData();
        setInterval(() => this.fetchData(), 2000);
    }

    async fetchData() {
        try {
            const response = await fetch(this.endpoint);
            if (!response.ok) {
                if (this.isPlaying || this.isInitialLoad) {
                    this._dispatchEvent('widget:error', { message: `API Hatası: ${response.status}` });
                }
                this.isPlaying = false;
                return;
            }
            const data = await response.json();
            this._processData(data);
        } catch (error) {
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

        if (!isNowPlaying) {
            if (this.isPlaying) {
                this.isPlaying = false;
                this.currentTrackId = null;
                this.isInitialLoad = true;
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
            this._dispatchEvent('widget:intro', { set: this.activeSet, data: data });
            return;
        }

        if (this.currentTrackId !== newTrackId) {
            this.isPlaying = true;
            this.currentTrackId = newTrackId;
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
            this._dispatchEvent('widget:sync', { data: data, set: this.activeSet });
        }
    }

    _dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        this.widgetElement.dispatchEvent(event);
    }
}
