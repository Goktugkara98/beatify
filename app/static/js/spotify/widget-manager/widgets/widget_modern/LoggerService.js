// DOSYA ADI: LoggerService.js (TAMAMEN YENİ VERSİYON)

class LoggerService {
    constructor() {
        // DOM Elementleri
        this.container = null;
        this.logList = null;
        this.pauseBtn = null;
        this.clearBtn = null;
        this.toggleBtn = null;
        this.filterControls = null;

        // Durum (State) Değişkenleri
        this.isPaused = false;
        this.isHidden = false;
        this.activeFilters = new Set(); // Aktif olan filtreleri tutar

        // Log Kaynakları ve Renkleri
        this.logSources = {
            DOM: { color: '#87CEFA', label: 'DOM' },
            ANIM: { color: '#98FB98', label: 'Animasyon' },
            STATE: { color: '#FFD700', label: 'Durum' },
            CONTENT: { color: '#FFB6C1', label: 'İçerik'},
            MAIN: { color: '#FFA07A', label: 'Ana Sistem' },
            DEFAULT: { color: '#FFFFFF', label: 'Bilgi' }
        };
    }

    // Servisi başlatan ana metot
    init() {
        // DOM elementlerini bul
        this.container = document.getElementById('LiveLogContainer');
        this.logList = document.getElementById('LiveLogList');
        this.pauseBtn = document.getElementById('log-pause-btn');
        this.clearBtn = document.getElementById('log-clear-btn');
        this.toggleBtn = document.getElementById('log-toggle-btn');
        this.filterControls = document.getElementById('LogFilterControls');
        
        // Eğer gerekli elementler yoksa servisi başlatma
        if (!this.container || !this.logList) {
            console.error("LoggerService: Gerekli HTML elementleri bulunamadı. Logger başlatılamadı.");
            return;
        }

        // İnteraktif kontrolleri ve filtreleri oluştur
        this._createFilters();
        this._bindEvents();
        this._enableDrag();
        
        this.log('Logger başarıyla başlatıldı ve interaktif modda çalışıyor.', 'MAIN');
    }

    // Kontrol butonlarının olay dinleyicilerini bağla
    _bindEvents() {
        this.toggleBtn.addEventListener('click', () => this.toggleVisibility());
        this.clearBtn.addEventListener('click', () => this.clearLogs());
        this.pauseBtn.addEventListener('click', () => this.togglePause());
    }

    // Filtre checkbox'larını oluştur ve olay dinleyicilerini bağla
    _createFilters() {
        // Başlangıçta tüm filtreler aktif
        Object.keys(this.logSources).forEach(key => this.activeFilters.add(key));

        for (const sourceKey in this.logSources) {
            const source = this.logSources[sourceKey];
            const label = document.createElement('label');
            label.style.color = source.color;
            label.innerHTML = `<input type="checkbox" data-filter="${sourceKey}" checked> ${source.label}`;
            this.filterControls.appendChild(label);
        }

        this.filterControls.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox') {
                this._updateFilters();
            }
        });
    }

    // Filtre durumunu güncelle
    _updateFilters() {
        this.activeFilters.clear();
        const checkboxes = this.filterControls.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            if (cb.checked) {
                this.activeFilters.add(cb.dataset.filter);
            }
        });
        this._applyFilters();
    }

    // Filtreleri DOM'a uygula
    _applyFilters() {
        const logItems = this.logList.querySelectorAll('li');
        logItems.forEach(item => {
            const source = item.dataset.source;
            if (this.activeFilters.has(source)) {
                item.classList.remove('log-hidden');
            } else {
                item.classList.add('log-hidden');
            }
        });
    }

    // Ana loglama metodu
    log(message, sourceKey = 'DEFAULT') {
        if (!this.logList) return; // Güvenlik kontrolü

        const sourceInfo = this.logSources[sourceKey] || this.logSources.DEFAULT;
        const consoleStyle = `background: ${sourceInfo.color}; color: #000; padding: 2px 6px; border-radius: 3px; font-weight: bold;`;
        
        // 1. Konsola log bas
        console.log(`%c${sourceInfo.label}`, consoleStyle, message);
        
        // 2. Canlı log alanına ekle
        const li = document.createElement('li');
        li.dataset.source = sourceKey; // Filtreleme için veri ekle
        li.innerHTML = `<span style="color: ${sourceInfo.color}; flex-shrink: 0; width: 80px;">[${sourceInfo.label}]</span> <span>${message}</span>`;
        
        // Eğer filtre dışındaysa gizli olarak ekle
        if (!this.activeFilters.has(sourceKey)) {
            li.classList.add('log-hidden');
        }

        this.logList.appendChild(li);

        // Duraklatılmadıysa en alta kaydır
        if (!this.isPaused) {
            this.logList.scrollTop = this.logList.scrollHeight;
        }
    }

    // Grup loglama metotları
    group(label) {
        console.group(label);
        if (this.logList) {
             const li = document.createElement('li');
             li.dataset.source = 'DEFAULT';
             li.innerHTML = `<strong style="color: #FFD700; width: 100%; text-align: center;">▼ ${label}</strong>`;
             this.logList.appendChild(li);
        }
    }

    groupEnd() {
        console.groupEnd();
    }
    
    // İnteraktif kontrol metotları
    _enableDrag() {
        const header = this.container.querySelector('.LiveLogHeader');
        if (!header) return;
        let offsetX = 0, offsetY = 0, dragging = false;
        const move = (e) => {
            if (!dragging) return;
            this.container.style.left = `${e.clientX - offsetX}px`;
            this.container.style.top = `${e.clientY - offsetY}px`;
        };
        const up = () => {
            dragging = false;
            document.removeEventListener('mousemove', move);
            document.removeEventListener('mouseup', up);
        };
        header.addEventListener('mousedown', (e) => {
            dragging = true;
            offsetX = e.clientX - this.container.offsetLeft;
            offsetY = e.clientY - this.container.offsetTop;
            // switch to left/top positioning
            this.container.style.right = 'auto';
            this.container.style.bottom = 'auto';
            document.addEventListener('mousemove', move);
            document.addEventListener('mouseup', up);
        });
    }

    toggleVisibility() {
        this.isHidden = !this.isHidden;
        this.container.classList.toggle('logger-hidden', this.isHidden);
        this.toggleBtn.textContent = this.isHidden ? '▲' : '▼';
    }

    clearLogs() {
        this.logList.innerHTML = '';
        this.log('Loglar temizlendi.', 'MAIN');
    }

    togglePause() {
        this.isPaused = !this.isPaused;
        this.pauseBtn.textContent = this.isPaused ? '▶' : '❚❚';
        this.pauseBtn.classList.toggle('paused', this.isPaused);
        this.log(`Log akışı ${this.isPaused ? 'DURAKLATILDI' : 'DEVAM EDİYOR'}.`, 'MAIN');
    }
}

// Servisin tek bir örneğini oluştur
const Logger = new LoggerService();

// DOM tamamen yüklendiğinde servisi KENDİ KENDİNE başlat.
// Bu, zamanlama hatalarını önler.
document.addEventListener('DOMContentLoaded', () => {
    Logger.init();
});