document.addEventListener('DOMContentLoaded', () => {
    // Initialize both regular particle buttons and auth particle buttons
    const particleButtons = document.querySelectorAll('.particle-button, .auth-particle-button');
    particleButtons.forEach(button => {
        new PixelButton(button);
    });
});

class PixelButton {
    constructor(element) {
        this.element = element;
        // Handle text elements for different button variants
        this.textElement =
            this.element.querySelector('.particle-button-text') ||
            this.element.querySelector('.auth-button-text') ||
            this.element.querySelector('.app-cta-button-text');
        this.colors = this.element.dataset.colors ? this.element.dataset.colors.split(',') : ['#1DB954', '#1ED760', '#FFFFFF'];
        this.pixelGap = this.element.dataset.gap ? parseInt(this.element.dataset.gap, 10) : 3;
        this.animationFrame = null;
        this.isAnimatingIn = false;
        this.isAnimatingOut = false;

        this.init();
    }

    init() {
        this.createCanvas();
        this.createPixels();
        this.attachEventListeners();
    }

    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.context = this.canvas.getContext('2d');
        this.element.appendChild(this.canvas);
        this.resize();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        const rect = this.element.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        this.createPixels();
    }

    createPixels() {
        this.pixels = [];
        const width = this.canvas.width;
        const height = this.canvas.height;
        const center = { x: width / 2, y: height / 2 };
        const maxDist = Math.sqrt(Math.pow(center.x, 2) + Math.pow(center.y, 2));

        for (let x = 0; x < width; x += this.pixelGap) {
            for (let y = 0; y < height; y += this.pixelGap) {
                const color = this.colors[Math.floor(Math.random() * this.colors.length)];
                const speed = Math.random() * 0.4 + 0.1; // Hızı yavaşlattık
                const delay = Math.random() * (width + height) * 0.5;
                const distance = Math.sqrt(Math.pow(x - center.x, 2) + Math.pow(y - center.y, 2));
                this.pixels.push(new Pixel(this.canvas, this.context, x, y, color, speed, delay, distance, maxDist));
            }
        }
    }

    attachEventListeners() {
        this.element.addEventListener('mouseenter', () => this.animateIn());
        this.element.addEventListener('mouseleave', () => this.animateOut());
        this.element.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.animateIn();
        }, { passive: false });
        this.element.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.animateOut();
        });
    }

    animateIn() {
        if (this.animationFrame) cancelAnimationFrame(this.animationFrame);
        this.isAnimatingIn = true;
        this.isAnimatingOut = false;
        this.pixels.forEach(p => p.reset());
        this.animationLoop();
    }

    animateOut() {
        this.isAnimatingIn = false;
        this.isAnimatingOut = true;
    }

    animationLoop() {
        this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
        let allIdle = true;

        this.pixels.forEach(pixel => {
            if (this.isAnimatingIn) {
                pixel.appear();
            } else if (this.isAnimatingOut) {
                pixel.disappear();
            }

            if (!pixel.isIdle) {
                allIdle = false;
            }
        });

        if (!allIdle) {
            this.animationFrame = requestAnimationFrame(() => this.animationLoop());
        } else {
            if (this.isAnimatingOut) {
                this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
                this.isAnimatingOut = false;
            }
        }
    }
}

class Pixel {
    constructor(canvas, context, x, y, color, speed, delay, distance, maxDist) {
        this.ctx = context;
        this.x = x;
        this.y = y;
        this.color = color;
        this.speed = speed;
        this.delay = delay;
        this.distance = distance;
        this.maxDist = maxDist;
        this.maxSize = 2; // Pikselleri daha da küçülttük

        this.reset();
    }

    reset() {
        this.size = 0;
        this.sizeStep = Math.random() * 0.5 + 0.1;
        this.minSize = 0.2;
        this.maxSizeActual = this.getRandomValue(this.minSize, this.maxSize);
        this.counter = 0;
        this.counterStep = Math.random() * 4 + (this.ctx.canvas.width + this.ctx.canvas.height) * 0.01;
        this.isIdle = true;
        this.isReverse = false;
        this.isShimmer = false;
    }

    getRandomValue(min, max) {
        return Math.random() * (max - min) + min;
    }

    draw() {
        // Merkeze olan uzaklığa göre opaklığı ayarla
        const opacity = Math.min(1, Math.max(0.2, this.distance / this.maxDist));
        const rgbaColor = this.hexToRgba(this.color, opacity);

        const centerOffset = this.maxSize * 0.5 - this.size * 0.5;
        this.ctx.fillStyle = rgbaColor;
        this.ctx.fillRect(
            this.x + centerOffset,
            this.y + centerOffset,
            this.size,
            this.size
        );
    }

    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    appear() {
        this.isIdle = false;

        if (this.counter <= this.delay) {
            this.counter += this.counterStep;
            return;
        }

        if (this.size >= this.maxSizeActual) {
            this.isShimmer = true;
        }

        if (this.isShimmer) {
            this.shimmer();
        } else {
            this.size += this.sizeStep;
        }

        this.draw();
    }

    disappear() {
        this.isShimmer = false;

        if (this.size <= 0) {
            this.isIdle = true;
            return;
        } else {
            this.size -= 0.2;
        }

        this.draw();
    }

    shimmer() {
        if (this.size >= this.maxSizeActual) {
            this.isReverse = true;
        } else if (this.size <= this.minSize) {
            this.isReverse = false;
        }

        if (this.isReverse) {
            this.size -= this.speed * 0.5;
        } else {
            this.size += this.speed * 0.5;
        }
    }
}
