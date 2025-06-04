// Pixel Canvas Animation for Widget Cards
class Pixel {
  constructor(canvas, context, x, y, color, speed, delay) {
    this.width = canvas.width;
    this.height = canvas.height;
    this.ctx = context;
    this.x = x;
    this.y = y;
    this.color = color;
    
    // Daha yavaş animasyon için hızı azalt
    this.speed = this.getRandomValue(0.05, 0.4) * speed;
    
    this.size = 0;
    // Daha yavaş büyüme için adım boyutunu azalt
    this.sizeStep = Math.random() * 0.2;
    
    this.minSize = 0.5;
    this.maxSizeInteger = 2;
    this.maxSize = this.getRandomValue(this.minSize, this.maxSizeInteger);
    
    // Daha uzun gecikme süresi
    this.delay = delay * 2;
    this.counter = 0;
    this.counterStep = Math.random() * 2 + (this.width + this.height) * 0.005;
    
    // Merkeze yakınlık hesaplama
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const distanceToCenter = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
    const maxDistance = Math.sqrt(Math.pow(canvas.width, 2) + Math.pow(canvas.height, 2)) / 2;
    
    // Pixel'lerin opacity'sini merkeze olan uzaklığa göre ayarla
    // Kenarlar daha belirgin, orta daha saydam
    const normalizedDistance = distanceToCenter / maxDistance;
    
    // Basit bir doğrusal fonksiyon kullan
    this.opacity = normalizedDistance;
    
    this.isIdle = false;
    this.isReverse = false;
    this.isShimmer = false;
  }

  getRandomValue(min, max) {
    return Math.random() * (max - min) + min;
  }

  draw() {
    const centerOffset = this.maxSizeInteger * 0.5 - this.size * 0.5;

    // Rengi RGBA formatına çevir ve opacity'yi uygula
    const rgb = this.hexToRgb(this.color);
    if (rgb) {
      this.ctx.fillStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${this.opacity})`;
    } else {
      // Fallback olarak orijinal rengi kullan
      this.ctx.fillStyle = this.color;
    }
    
    this.ctx.fillRect(
      this.x + centerOffset,
      this.y + centerOffset,
      this.size,
      this.size
    );
  }
  
  // Hex renk kodunu RGB'ye çeviren yardımcı fonksiyon
  hexToRgb(hex) {
    // Kısa hex formatını (#fff) tam formata (#ffffff) çevir
    const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
    hex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);

    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16)
        }
      : null;
  }

  appear() {
    this.isIdle = false;

    if (this.counter <= this.delay) {
      this.counter += this.counterStep;
      return;
    }

    if (this.size >= this.maxSize) {
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
    this.counter = 0;

    if (this.size <= 0) {
      this.isIdle = true;
      return;
    } else {
      this.size -= 0.1;
    }

    this.draw();
  }

  shimmer() {
    if (this.size >= this.maxSize) {
      this.isReverse = true;
    } else if (this.size <= this.minSize) {
      this.isReverse = false;
    }

    if (this.isReverse) {
      this.size -= this.speed;
    } else {
      this.size += this.speed;
    }
  }
}

class PixelCanvas extends HTMLElement {
  static register(tag = "pixel-canvas") {
    if ("customElements" in window) {
      customElements.define(tag, this);
    }
  }

  static css = `
    :host {
      display: grid;
      inline-size: 100%;
      block-size: 100%;
      overflow: hidden;
      position: absolute;
      inset: 0;
      z-index: 0;
    }
  `;

  get colors() {
    return this.dataset.colors?.split(",") || ["#f8fafc", "#f1f5f9", "#cbd5e1"];
  }

  get gap() {
    const value = this.dataset.gap || 5;
    const min = 4;
    const max = 50;

    if (value <= min) {
      return min;
    } else if (value >= max) {
      return max;
    } else {
      return parseInt(value);
    }
  }

  get speed() {
    const value = this.dataset.speed || 35;
    const min = 0;
    const max = 100;
    const throttle = 0.001;

    if (value <= min || this.reducedMotion) {
      return min;
    } else if (value >= max) {
      return max * throttle;
    } else {
      return parseInt(value) * throttle;
    }
  }

  get noFocus() {
    return this.hasAttribute("data-no-focus");
  }

  connectedCallback() {
    const canvas = document.createElement("canvas");
    const sheet = new CSSStyleSheet();

    this._parent = this.parentNode;
    this.shadowroot = this.attachShadow({ mode: "open" });

    sheet.replaceSync(PixelCanvas.css);

    this.shadowroot.adoptedStyleSheets = [sheet];
    this.shadowroot.append(canvas);
    this.canvas = this.shadowroot.querySelector("canvas");
    this.ctx = this.canvas.getContext("2d");
    this.timeInterval = 1000 / 60;
    this.timePrevious = performance.now();
    this.reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    this.init();
    this.resizeObserver = new ResizeObserver(() => this.init());
    this.resizeObserver.observe(this);

    this._parent.addEventListener("mouseenter", this);
    this._parent.addEventListener("mouseleave", this);

    if (!this.noFocus) {
      this._parent.addEventListener("focusin", this);
      this._parent.addEventListener("focusout", this);
    }
  }

  disconnectedCallback() {
    this.resizeObserver.disconnect();
    this._parent.removeEventListener("mouseenter", this);
    this._parent.removeEventListener("mouseleave", this);

    if (!this.noFocus) {
      this._parent.removeEventListener("focusin", this);
      this._parent.removeEventListener("focusout", this);
    }

    delete this._parent;
  }

  handleEvent(event) {
    this[`on${event.type}`](event);
  }

  // Hover olaylarını devre dışı bıraktık, sadece seçilen kart için animasyon çalışacak
  onmouseenter() {
    // Hover'da animasyon yok
  }

  onmouseleave() {
    // Hover'da animasyon yok
  }

  onfocusin(e) {
    // Focus'ta animasyon yok
  }

  onfocusout(e) {
    // Focus'ta animasyon yok
  }

  handleAnimation(type) {
    if (this.reducedMotion) return;

    if (type === "appear") {
      this.isActive = true;
      this.keepAnimating = true;
      this.animate();
    } else {
      if (!this.keepAnimating) {
        this.isActive = false;
      }
    }
  }

  init() {
    this.isActive = false;
    this.pixels = [];

    this.canvas.width = this.offsetWidth;
    this.canvas.height = this.offsetHeight;

    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    const pixelSize = this.gap;
    const cols = Math.floor(this.canvas.width / pixelSize);
    const rows = Math.floor(this.canvas.height / pixelSize);

    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        const x = i * pixelSize;
        const y = j * pixelSize;
        const color = this.colors[Math.floor(Math.random() * this.colors.length)];
        const delay = Math.random() * 100;

        this.pixels.push(
          new Pixel(this.canvas, this.ctx, x, y, color, this.speed, delay)
        );
      }
    }
  }

  animate() {
    if (!this.isActive && !this.keepAnimating) return;

    const timeNow = performance.now();
    const elapsed = timeNow - this.timePrevious;

    if (elapsed > this.timeInterval) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

      for (let i = 0; i < this.pixels.length; i++) {
        const pixel = this.pixels[i];

        if (this.isActive || this.keepAnimating) {
          pixel.appear();
          
          // Seçili kartlar için sürekli animasyon efekti
          if (this.keepAnimating && pixel.isShimmer) {
            // Pixel'in shimmer efektini güçlendir
            pixel.speed = Math.max(pixel.speed, 0.05);
          }
        } else {
          pixel.disappear();
        }
      }

      this.timePrevious = timeNow - (elapsed % this.timeInterval);
    }

    requestAnimationFrame(() => this.animate());
  }
}

// Register the custom element
PixelCanvas.register();
