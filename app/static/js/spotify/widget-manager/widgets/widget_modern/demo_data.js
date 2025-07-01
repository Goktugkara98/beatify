/**
 * demo_data.js - Mock Spotify API data for testing
 * This file provides sample data to test the widget without a real Spotify API
 */

// Sample track data
const DEMO_TRACKS = [
    {
        item: {
            id: "4iV5W9uYEdYUVa79Axb7Rh",
            name: "Bohemian Rhapsody",
            artists: [
                { name: "Queen" }
            ],
            album: {
                images: [
                    {
                        url: "https://i.scdn.co/image/ab67616d0000b273ce4f1737bc8a646c8c4bd25a"
                    }
                ]
            },
            duration_ms: 355000
        },
        is_playing: true,
        progress_ms: 45000
    },
    {
        item: {
            id: "7qiZfU4dY1lWllzX7mPBI3",
            name: "Shape of You",
            artists: [
                { name: "Ed Sheeran" }
            ],
            album: {
                images: [
                    {
                        url: "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96"
                    }
                ]
            },
            duration_ms: 233000
        },
        is_playing: true,
        progress_ms: 67000
    },
    {
        item: {
            id: "1mea3bSkSGXuIRvnydlB5b",
            name: "Blinding Lights",
            artists: [
                { name: "The Weeknd" }
            ],
            album: {
                images: [
                    {
                        url: "https://i.scdn.co/image/ab67616d0000b2738863bc11d2aa12b54f5aeb36"
                    }
                ]
            },
            duration_ms: 200000
        },
        is_playing: true,
        progress_ms: 120000
    },
    {
        item: {
            id: "0VjIjW4GlULA4LGvWeEY5u",
            name: "Someone Like You",
            artists: [
                { name: "Adele" }
            ],
            album: {
                images: [
                    {
                        url: "https://i.scdn.co/image/ab67616d0000b273372eb54bde0e3b60a8b0e8e0"
                    }
                ]
            },
            duration_ms: 285000
        },
        is_playing: true,
        progress_ms: 30000
    }
];

/**
 * Mock Spotify API service for testing
 */
class MockSpotifyAPI {
    constructor() {
        this.currentTrackIndex = 0;
        this.isPlaying = false;
        this.startTime = null;
        this.pausedAt = 0;
    }

    /**
     * Start playing the current track
     */
    play() {
        this.isPlaying = true;
        this.startTime = Date.now() - this.pausedAt;
        console.log('[MockSpotifyAPI] Started playing');
    }

    /**
     * Pause the current track
     */
    pause() {
        if (this.isPlaying) {
            this.pausedAt = Date.now() - this.startTime;
            this.isPlaying = false;
            console.log('[MockSpotifyAPI] Paused');
        }
    }

    /**
     * Stop playback
     */
    stop() {
        this.isPlaying = false;
        this.startTime = null;
        this.pausedAt = 0;
        console.log('[MockSpotifyAPI] Stopped');
    }

    /**
     * Skip to next track
     */
    nextTrack() {
        this.currentTrackIndex = (this.currentTrackIndex + 1) % DEMO_TRACKS.length;
        this.pausedAt = 0;
        if (this.isPlaying) {
            this.startTime = Date.now();
        }
        console.log(`[MockSpotifyAPI] Switched to track ${this.currentTrackIndex + 1}`);
    }

    /**
     * Skip to previous track
     */
    previousTrack() {
        this.currentTrackIndex = this.currentTrackIndex === 0 ? DEMO_TRACKS.length - 1 : this.currentTrackIndex - 1;
        this.pausedAt = 0;
        if (this.isPlaying) {
            this.startTime = Date.now();
        }
        console.log(`[MockSpotifyAPI] Switched to track ${this.currentTrackIndex + 1}`);
    }

    /**
     * Get current playback state
     * @returns {Object} Current playback state
     */
    getCurrentState() {
        if (!this.isPlaying) {
            return {
                is_playing: false,
                item: null,
                progress_ms: 0
            };
        }

        const currentTrack = DEMO_TRACKS[this.currentTrackIndex];
        const elapsed = this.startTime ? Date.now() - this.startTime : this.pausedAt;
        const progress = Math.min(elapsed, currentTrack.item.duration_ms);

        // Auto-advance to next track if current one is finished
        if (progress >= currentTrack.item.duration_ms) {
            this.nextTrack();
            return this.getCurrentState();
        }

        return {
            ...currentTrack,
            progress_ms: progress
        };
    }
}

/**
 * Demo controller for testing the widget
 */
class WidgetDemoController {
    constructor() {
        this.mockAPI = new MockSpotifyAPI();
        this.originalFetch = null;
        this.isActive = false;
        
        this.createControls();
    }

    /**
     * Start demo mode
     */
    start() {
        if (this.isActive) {
            console.warn('[WidgetDemoController] Demo mode already active');
            return;
        }

        console.log('[WidgetDemoController] Starting demo mode');
        
        // Override fetch for the widget endpoint
        this.originalFetch = window.fetch;
        window.fetch = (url, options) => {
            if (url.includes('/spotify/api/widget-data/')) {
                return this.mockFetch(url, options);
            }
            return this.originalFetch(url, options);
        };

        this.isActive = true;
        this.mockAPI.play();
        this.updateControlsVisibility();
    }

    /**
     * Stop demo mode
     */
    stop() {
        if (!this.isActive) {
            console.warn('[WidgetDemoController] Demo mode not active');
            return;
        }

        console.log('[WidgetDemoController] Stopping demo mode');
        
        // Restore original fetch
        if (this.originalFetch) {
            window.fetch = this.originalFetch;
            this.originalFetch = null;
        }

        this.isActive = false;
        this.mockAPI.stop();
        this.updateControlsVisibility();
    }

    /**
     * Mock fetch implementation
     * @param {string} url - Request URL
     * @param {Object} options - Request options
     * @returns {Promise} Mock response
     */
    async mockFetch(url, options) {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200));

        const state = this.mockAPI.getCurrentState();
        
        return {
            ok: true,
            status: 200,
            json: async () => state
        };
    }

    /**
     * Create demo control panel
     */
    createControls() {
        const controlsContainer = document.createElement('div');
        controlsContainer.id = 'demo-controls';
        controlsContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            z-index: 10000;
            min-width: 200px;
            display: none;
        `;

        controlsContainer.innerHTML = `
            <h3 style="margin: 0 0 10px 0;">Widget Demo Controls</h3>
            <div style="margin-bottom: 10px;">
                <button id="demo-start" style="margin-right: 5px;">Start Demo</button>
                <button id="demo-stop">Stop Demo</button>
            </div>
            <div style="margin-bottom: 10px;">
                <button id="demo-play" style="margin-right: 5px;">Play</button>
                <button id="demo-pause">Pause</button>
            </div>
            <div style="margin-bottom: 10px;">
                <button id="demo-prev" style="margin-right: 5px;">Previous</button>
                <button id="demo-next">Next</button>
            </div>
            <div>
                <small>Press Ctrl+D to toggle controls</small>
            </div>
        `;

        document.body.appendChild(controlsContainer);

        // Bind control events
        document.getElementById('demo-start').addEventListener('click', () => this.start());
        document.getElementById('demo-stop').addEventListener('click', () => this.stop());
        document.getElementById('demo-play').addEventListener('click', () => this.mockAPI.play());
        document.getElementById('demo-pause').addEventListener('click', () => this.mockAPI.pause());
        document.getElementById('demo-prev').addEventListener('click', () => this.mockAPI.previousTrack());
        document.getElementById('demo-next').addEventListener('click', () => this.mockAPI.nextTrack());

        // Toggle controls with Ctrl+D
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                this.toggleControls();
            }
        });

        this.controlsContainer = controlsContainer;
    }

    /**
     * Toggle control panel visibility
     */
    toggleControls() {
        const isVisible = this.controlsContainer.style.display !== 'none';
        this.controlsContainer.style.display = isVisible ? 'none' : 'block';
    }

    /**
     * Update controls based on demo state
     */
    updateControlsVisibility() {
        const startBtn = document.getElementById('demo-start');
        const stopBtn = document.getElementById('demo-stop');
        const playBtn = document.getElementById('demo-play');
        const pauseBtn = document.getElementById('demo-pause');

        if (startBtn && stopBtn) {
            startBtn.disabled = this.isActive;
            stopBtn.disabled = !this.isActive;
        }

        if (playBtn && pauseBtn) {
            playBtn.disabled = !this.isActive;
            pauseBtn.disabled = !this.isActive;
        }
    }
}

// Initialize demo controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.demoController = new WidgetDemoController();
    console.log('[Demo] Demo controller initialized. Press Ctrl+D to show controls.');
});

