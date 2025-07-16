document.addEventListener('DOMContentLoaded', () => {
    // --- 1. Gerekli Elementleri ve Koşulları Kontrol Et ---
    const preloaderElement = document.getElementById('preloader');
    const canvasElement = document.getElementById('preloader-canvas');

    if (!document.querySelector('.banner-container') || !preloaderElement || !canvasElement) {
        if (preloaderElement) preloaderElement.remove();
        document.body.classList.remove('preloader-active');
        return;
    }

    // --- 2. Değişkenler ve Ayarlar ---
    const ctx = canvasElement.getContext("2d");
    let width, height, pixels = [], animationFrameId;

    const transitionWidth = 120;
    const showTime = 1000;
    const holdTime = 1000;
    const hideTime = 1000;
    const totalDuration = showTime + holdTime + hideTime;

    let startTime;
    let activeColors = [];
    let isEnding = false;

    // --- 3. Pixel Sınıfı ve Yardımcı Fonksiyonlar ---
    const rand = (min, max) => Math.random() * (max - min) + min;
    const easeInOut = (t) => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    const hexToRgba = (hex, alpha = 1) => {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    };

    class Pixel {
        constructor(x, y, color, size) {
            this.x = x;
            this.y = y;
            this.hexColor = color;
            this.baseSize = rand(0.8, size);
            this.size = this.baseSize;
            this.speed = rand(0.05, 0.2);
            this.sizeDirection = 1;
        }
        flicker() {
            if (this.size >= this.baseSize) this.sizeDirection = -1;
            else if (this.size <= 0.8) this.sizeDirection = 1;
            this.size += this.sizeDirection * this.speed;
        }
        draw(opacity = 1) {
            this.flicker();
            if (opacity <= 0) return;
            ctx.fillStyle = hexToRgba(this.hexColor, opacity);
            const centerOffset = this.baseSize * 0.5 - this.size * 0.5;
            ctx.fillRect(this.x + centerOffset, this.y + centerOffset, this.size, this.size);
        }
    }

    // --- 4. Ana Preloader Mantığı ---
    const createTextPixels = () => {
        const colorPalettes = [
            // Mor-Mavi-Yeşil Palette (Genişletilmiş)
            ['#7c4dff', '#536dfe', '#448aff', '#03a9f4', '#1db954', '#651fff', '#304ffe', '#2979ff', '#00b0ff', '#00e676'],
            // Kırmızı-Turuncu-Sarı Palette (Genişletilmiş)
            ['#ff1744', '#ff5252', '#ff9100', '#ffab40', '#ffd740', '#d50000', '#ff3d00', '#ff6d00', '#ffab00', '#ffc400'],
            // Yeşil-Turkuaz Palette (Genişletilmiş)
            ['#00c853', '#69f0ae', '#00e5ff', '#18ffff', '#64ffda', '#00e676', '#1de9b6', '#00b8d4', '#00e5ff', '#1de9b6'],
            // Mor-Pembe Palette (Genişletilmiş)
            ['#d500f9', '#e040fb', '#ff4081', '#ff80ab', '#b388ff', '#aa00ff', '#c51162', '#f50057', '#ff4081', '#ea80fc'],
            // Yeni: Mavi-Yeşil Palette
            ['#0288d1', '#26c6da', '#00acc1', '#00bcd4', '#4dd0e1', '#00838f', '#006064', '#0097a7', '#80deea', '#26a69a'],
            // Yeni: Turuncu-Sarı-Yeşil Palette
            ['#ff6f00', '#ffab00', '#ffc400', '#ffea00', '#c0ca33', '#afb42b', '#827717', '#fdd835', '#ffee58', '#fff176'],
            // Yeni: Kırmızı-Mor Palette
            ['#c62828', '#d32f2f', '#f44336', '#e91e63', '#9c27b0', '#673ab7', '#5e35b1', '#512da8', '#d81b60', '#ad1457']
        ];
        activeColors = colorPalettes[Math.floor(Math.random() * colorPalettes.length)];
        const text = "Beatify";
        const fontName = "'Poppins', sans-serif";
        const fontSize = Math.min(width, height) * 0.18;
        ctx.font = `bold ${fontSize}px ${fontName}`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, width / 2, height / 2);
        const imageData = ctx.getImageData(0, 0, width, height).data;
        ctx.clearRect(0, 0, width, height);
        const gap = 3;
        const pixelSize = gap * 0.95;
        pixels = [];
        for (let y = 0; y < height; y += gap) {
            for (let x = 0; x < width; x += gap) {
                if (imageData[(y * width + x) * 4 + 3] > 128) {
                    const color = activeColors[Math.floor(Math.random() * activeColors.length)];
                    pixels.push(new Pixel(x, y, color, pixelSize));
                }
            }
        }
    };

    const endPreloader = () => {
        cancelAnimationFrame(animationFrameId);
        preloaderElement.style.transition = 'opacity 0.5s ease-out';
        preloaderElement.style.opacity = '0';
        preloaderElement.addEventListener('transitionend', () => {
            preloaderElement.remove();
            document.body.classList.remove('preloader-active');
        }, { once: true });
    };

    const animate = (timestamp) => {
        if (!startTime) startTime = timestamp;
        const elapsedTime = timestamp - startTime;
        ctx.clearRect(0, 0, width, height);
        
        const centerX = width / 2;

        // DÜZELTİLMİŞ ANİMASYON MANTIĞI
        let revealProgress = 0;

        if (elapsedTime < showTime) {
            // Açılış: İlerleme 0'dan 1'e gider
            revealProgress = easeInOut(elapsedTime / showTime);
        }
        else if (elapsedTime < showTime + holdTime) {
            // Bekleme: İlerleme tam olarak 1'de kalır
            revealProgress = 1;
        }
        else if (elapsedTime < totalDuration) {
            // Kapanış: İlerleme 1'den 0'a geri gider
            const hideProgress = easeInOut((elapsedTime - (showTime + holdTime)) / hideTime);
            revealProgress = 1 - hideProgress;
        }
        else {
            if (!isEnding) {
                isEnding = true;
                endPreloader();
            }
            return;
        }

        // Her piksel için opaklığı yeniden hesapla
        const revealWidth = (centerX + transitionWidth) * revealProgress;
        
        pixels.forEach(p => {
            const distFromCenter = Math.abs(p.x - centerX);
            
            // Opaklık, perdenin ilerlemesine göre hesaplanır
            // ve 0 ile 1 arasında sınırlandırılır.
            const opacity = Math.max(0, Math.min(1, (revealWidth - distFromCenter) / transitionWidth));
            
            p.draw(opacity);
        });
        
        animationFrameId = requestAnimationFrame(animate);
    };

    // --- 5. Başlatma ve Olay Dinleyicileri ---
    const setup = () => {
        if (animationFrameId) cancelAnimationFrame(animationFrameId);
        isEnding = false;
        
        const rect = preloaderElement.getBoundingClientRect();
        width = canvasElement.width = Math.floor(rect.width);
        height = canvasElement.height = Math.floor(rect.height);
        
        startTime = null;
        createTextPixels();
        animationFrameId = requestAnimationFrame(animate);
    };
    
    const font = new FontFace('Poppins', 'url(https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLEj6Z1xlFd2JQEk.woff2)');
    document.body.classList.add('preloader-active');
    
    font.load().then(() => {
        document.fonts.add(font);
        setup();
    }).catch(err => {
        console.error('Font could not be loaded, starting preloader anyway.', err);
        setup();
    });

    window.addEventListener('resize', setup);
});