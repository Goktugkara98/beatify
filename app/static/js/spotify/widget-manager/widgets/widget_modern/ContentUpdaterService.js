class ContentUpdaterService {
    constructor(widgetElement) {
        this.widgetElement = widgetElement;
        this.progressIntervals = {
            a: null,
            b: null
        };
    }

    async updateAllForSet(set, data) {
        const item = data.item;
        if (!item) return;

        this._updateText(`.TrackNameElement_${set}`, item.name);
        this._updateText(`.ArtistNameElement_${set}`, item.artists.map(a => a.name).join(', '));
        this._updateText(`.TotalTimeElement_${set}`, this._formatTime(item.duration_ms));

        await Promise.all([
            this._updateImage(`.CoverElement_${set}`, item.album.images[0]?.url),
            this._updateImage(`.AlbumArtBackgroundElement_${set}`, item.album.images[0]?.url)
        ]);
    }

    clearAllForSet(set) {
        this._updateText(`.TrackNameElement_${set}`, '');
        this._updateText(`.ArtistNameElement_${set}`, '');
        this._updateText(`.TotalTimeElement_${set}`, '0:00');
        this._updateImage(`.CoverElement_${set}`, '');
        this._updateImage(`.AlbumArtBackgroundElement_${set}`, '');
    }

    startProgressUpdater(data, set) {
        this.stopProgressUpdater(set);
        if (!data || !data.item || !data.is_playing) return;

        let progressMs = data.progress_ms;
        const durationMs = data.item.duration_ms;
        const currentTimeElem = this.widgetElement.querySelector(`.CurrentTimeElement_${set}`);
        const progressBarElem = this.widgetElement.querySelector(`.ProgressBarElement_${set}`);

        if (!currentTimeElem || !progressBarElem) return;

        const update = () => {
            currentTimeElem.innerText = this._formatTime(progressMs);
            const percentage = durationMs > 0 ? (progressMs / durationMs) * 100 : 0;
            progressBarElem.style.width = `${Math.min(percentage, 100)}%`;

            if (progressMs < durationMs) {
                progressMs += 1000;
            } else {
                progressMs = durationMs;
                this.stopProgressUpdater(set);
            }
        };

        update();
        this.progressIntervals[set] = setInterval(update, 1000);
    }

    stopProgressUpdater(set) {
        if (this.progressIntervals[set]) {
            clearInterval(this.progressIntervals[set]);
            this.progressIntervals[set] = null;
        }
    }

    stopAllProgressUpdaters() {
        this.stopProgressUpdater('a');
        this.stopProgressUpdater('b');
    }

    _updateText(selector, text) {
        const elem = this.widgetElement.querySelector(selector);
        if (!elem) {
            return;
        }

        elem.classList.remove('marquee', 'marquee_a', 'marquee_b');
        elem.style.animation = 'none';

        elem.textContent = text;
        elem.title = text;

        requestAnimationFrame(() => {
            const clientWidth = elem.clientWidth;
            const scrollWidth = elem.scrollWidth;
            const isOverflowing = scrollWidth > clientWidth;

            if (isOverflowing) {
                const buffer = 20;
                const overflowAmount = scrollWidth - clientWidth + buffer;

                elem.style.setProperty('--scroll-end', `-${overflowAmount}px`);

                if (elem.classList.contains('TrackNameElement_a') || elem.classList.contains('ArtistNameElement_a')) {
                    elem.classList.add('marquee_a');
                } else if (elem.classList.contains('TrackNameElement_b') || elem.classList.contains('ArtistNameElement_b')) {
                    elem.classList.add('marquee_b');
                } else {
                    elem.classList.add('marquee');
                }

                elem.style.animation = '';
            }
        });
    }

    _updateImage(selector, src) {
        return new Promise((resolve) => {
            const elem = this.widgetElement.querySelector(selector);
            if (!elem || !src || elem.src === src) {
                return resolve();
            }

            const img = new Image();
            img.src = src;

            const onImageLoad = () => {
                elem.src = src;
                resolve();
            };

            img.onload = onImageLoad;
            img.onerror = onImageLoad;
        });
    }

    _formatTime(ms) {
        if (typeof ms !== 'number') return '0:00';
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}
