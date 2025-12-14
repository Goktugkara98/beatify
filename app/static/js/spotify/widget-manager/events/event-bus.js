class EventBus {
    constructor() {
        this.listeners = {};
    }

    on(event, handler) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(handler);
        return () => this.off(event, handler);
    }

    off(event, handler) {
        if (!this.listeners[event]) return;
        this.listeners[event] = this.listeners[event].filter(h => h !== handler);
    }

    emit(event, payload) {
        if (!this.listeners[event]) return;
        this.listeners[event].forEach(handler => {
            try {
                handler(payload);
            } catch (e) {
                console.error('[EventBus] listener error for', event, e);
            }
        });
    }
}

// Global erişim için
window.EventBus = EventBus;

