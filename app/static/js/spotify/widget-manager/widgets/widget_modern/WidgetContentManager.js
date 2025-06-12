window.WidgetContentManager = class WidgetContentManager {
    constructor(widgetElement) {
        if (!widgetElement) {
            throw new Error("WidgetContentManager için widgetElement gereklidir.");
        }
        this.widgetElement = widgetElement;
        this.progressInterval = null;

        this.listenToEvents();
    }

    listenToEvents() {
        this.widgetElement.addEventListener('widget:intro', (e) => this._updateDOMContent(e.detail.set, e.detail.data));
        this.widgetElement.addEventListener('widget:transition', (e) => {
            this.stopProgressUpdater();
            this._updateDOMContent(e.detail.passiveSet, e.detail.data);
        });
        this.widgetElement.addEventListener('widget:outro', () => this.stopProgressUpdater());
        this.widgetElement.addEventListener('widget:sync', (e) => this.startProgressUpdater(e.detail.data, e.detail.set));
        this.widgetElement.addEventListener('widget:error', (e) => this.displayError(e.detail.message));
        this.widgetElement.addEventListener('widget:clear-error', () => this.clearError());
    }

    _updateDOMContent(set, data) {
        const item = data.item;
        if (!item) return;
        const query = (selector) => this.widgetElement.querySelector(`${selector}[data-set="${set}"]`);

        const trackNameElem = query('.TrackNameElement');
        const artistNameElem = query('.ArtistNameElement');
        const coverElem = query('.CoverElement');
        const coverBgElem = query('.AlbumArtBackgroundElement');
        const totalTimeElem = query('.TotalTimeElement');

        if (trackNameElem) trackNameElem.innerText = item.name;
        if (artistNameElem) artistNameElem.innerText = item.artists.map(a => a.name).join(', ');
        if (coverElem) coverElem.src = item.album.images[0]?.url || '';
        if (coverBgElem) coverBgElem.src = item.album.images[0]?.url || '';
        if (totalTimeElem) totalTimeElem.innerText = this._formatTime(item.duration_ms);
    }

    startProgressUpdater(data, set) {
        if (this.progressInterval) clearInterval(this.progressInterval);
        
        let progressMs = data.progress_ms;
        const durationMs = data.item.duration_ms;

        const update = () => {
            const currentTimeElem = this.widgetElement.querySelector(`.CurrentTimeElement[data-set="${set}"]`);
            const progressBarElem = this.widgetElement.querySelector(`.ProgressBarElement[data-set="${set}"]`);

            if (currentTimeElem) currentTimeElem.innerText = this._formatTime(progressMs);
            if (progressBarElem) {
                const percentage = durationMs > 0 ? (progressMs / durationMs) * 100 : 0;
                progressBarElem.style.width = `${Math.min(percentage, 100)}%`;
            }
            progressMs += 1000;
        };
        update();
        this.progressInterval = setInterval(update, 1000);
    }

    stopProgressUpdater() {
        clearInterval(this.progressInterval);
        this.progressInterval = null;
    }

    displayError(message) {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement) {
            errorElement.innerText = message;
            this.widgetElement.classList.add('error-active');
        }
        this.stopProgressUpdater();
    }

    clearError() {
        const errorElement = this.widgetElement.querySelector('#ErrorMessageElement');
        if (errorElement && errorElement.innerText !== '') {
            errorElement.innerText = '';
            this.widgetElement.classList.remove('error-active');
        }
    }

    _formatTime(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}