const rand = (min, max) => {
    return Math.random() * (max - min) + min;
  };
  
  // Metin ve piksel ayarlarını kolayca değiştirmek için bir konfigürasyon nesnesi
  const config = {
    text: "PIXEL", // Görüntülenecek metin
    fontFamily: "monospace", // Font ailesi
    fontSize: 150, // Font boyutu (piksel), canvas boyutuna göre ayarlanır
    pixelGap: 4, // Pikseller arası boşluk. Detay seviyesini belirler. Daha küçük değer daha detaylıdır.
    pixelThreshold: 128 // Bir pikselin metne ait sayılması için gereken minimum opaklık (0-255)
  };
  
  
  // based on https://codepen.io/hexagoncircle/pen/KwPpdBZ
  class Pixel {
    constructor(x, y, color, speed, delay, delayHide, step, boundSize) {
      this.x = x;
      this.y = y;
  
      this.color = color;
      this.speed = rand(0.1, 0.9) * speed;
  
      this.size = 0;
      this.sizeStep = rand(0, 0.5);
      this.minSize = 0.5;
      this.maxSizeAvailable = boundSize || 2;
      this.maxSize = rand(this.minSize, this.maxSizeAvailable);
      this.sizeDirection = 1;
  
      this.delay = delay;
      this.delayHide = delayHide;
      this.counter = 0;
      this.counterHide = 0;
      this.counterStep = step;
  
      this.isHidden = false;
      this.isFlicking = false;
    }
  
    draw(ctx) {
      const centerOffset = this.maxSizeAvailable * 0.5 - this.size * 0.5;
  
      ctx.fillStyle = this.color;
      ctx.fillRect(
      this.x + centerOffset,
      this.y + centerOffset,
      this.size,
      this.size);
  
    }
  
    show() {
      this.isHidden = false;
      this.counterHide = 0;
  
      if (this.counter <= this.delay) {
        this.counter += this.counterStep;
        return;
      }
  
      if (this.size >= this.maxSize) {
        this.isFlicking = true;
      }
  
      if (this.isFlicking) {
        this.flicking();
      } else {
        this.size += this.sizeStep;
      }
    }
  
    hide() {
      this.counter = 0;
  
      if (this.counterHide <= this.delayHide) {
        this.counterHide += this.counterStep;
        if (this.isFlicking) {
          this.flicking();
        }
        return;
      }
  
      this.isFlicking = false;
  
      if (this.size <= 0) {
        this.size = 0;
        this.isHidden = true;
        return;
      } else {
        this.size -= 0.05;
      }
    }
  
    flicking() {
      if (this.size >= this.maxSize) {
        this.sizeDirection = -1;
      } else if (this.size <= this.minSize) {
        this.sizeDirection = 1;
      }
  
      this.size += this.sizeDirection * this.speed;
    }}
  
  
  const canvas = document.createElement("canvas");
  const container = document.querySelector("#container");
  const interval = 1000 / 60;
  
  container.append(canvas);
  
  const ctx = canvas.getContext("2d");
  
  let width;
  let height;
  let pixels;
  let request;
  let lastTime;
  let ticker;
  let maxTicker = 360;
  let animationDirection = 1;
  
  const getDelay = (x, y, direction) => {
    let dx = x - width * 0.5;
    let dy = y - height;
  
    if (direction) {
      dy = y;
    }
  
    return Math.sqrt(dx ** 2 + dy ** 2);
  };
  
  // YENİ FONKSİYON: Piksel verisini almak için metni canvas'a çizer
  const drawTextForSampling = () => {
      // Canvas'ı temizle
      ctx.clearRect(0, 0, width, height);
      
      // Font boyutunu canvas genişliğine göre dinamik yapalım
      const dynamicFontSize = Math.min(config.fontSize, width / config.text.length * 1.5);
  
      ctx.fillStyle = "white"; // Renk önemli değil, sadece alfa kanalı kullanılacak
      ctx.font = `${dynamicFontSize}px ${config.fontFamily}`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(config.text, width / 2, height / 2);
  }
  
  
  const initPixels = () => {
    // 1. Adım: Metni çiz ve piksel verisini al
    drawTextForSampling();
    const imageData = ctx.getImageData(0, 0, width, height);
    // Metni çizdikten sonra canvas'ı hemen temizle, çünkü sadece pikselleri göreceğiz
    ctx.clearRect(0, 0, width, height);
  
    const h = Math.floor(rand(0, 360));
    const colorsLen = 5;
    const colors = Array.from({ length: colorsLen }, (_, index) => `hsl(${Math.floor(rand(h, h + (index + 1) * 10))} 100% ${rand(50, 100)}%)`);
  
    const gap = config.pixelGap;
    const step = (width + height) * 0.005;
    const speed = rand(0.008, 0.25);
    const maxSize = Math.floor(gap * 0.9); // Piksellerin maksimum boyutu boşluktan biraz küçük olsun
  
    pixels = [];
  
    // 2. Adım: Canvas'ı tara ve sadece metnin olduğu yerlere piksel ekle
    for (let y = 0; y < height; y += gap) {
      for (let x = 0; x < width; x += gap) {
        // imageData dizisindeki ilgili pikselin alfa değerini bul
        // Her piksel 4 değerden oluşur (R,G,B,A). Bu yüzden 4 ile çarpılır.
        const alphaIndex = (y * width + x) * 4 + 3;
        const alpha = imageData.data[alphaIndex];
  
        // Eğer alfa değeri belirli bir eşikten yüksekse (yani bu piksel metnin bir parçasıysa)
        if (alpha > config.pixelThreshold) {
            const color = colors[Math.floor(Math.random() * colorsLen)];
            const delay = getDelay(x, y);
            const delayHide = getDelay(x, y);
  
            pixels.push(new Pixel(x, y, color, speed, delay, delayHide, step, maxSize));
        }
      }
    }
  };
  
  const animate = () => {
    request = requestAnimationFrame(animate);
  
    const now = performance.now();
    const diff = now - (lastTime || 0);
  
    if (diff < interval) {
      return;
    }
  
    lastTime = now - diff % interval;
  
    ctx.clearRect(0, 0, width, height);
  
    if (ticker >= maxTicker) {
      animationDirection = -1;
    } else if (ticker <= 0) {
      animationDirection = 1;
    }
  
    let allHidden = true;
  
    pixels.forEach(pixel => {
      if (animationDirection > 0) {
        pixel.show();
      } else {
        pixel.hide();
        allHidden = allHidden && pixel.isHidden;
      }
  
      pixel.draw(ctx);
    });
  
    ticker += animationDirection;
  
    if (animationDirection < 0 && allHidden) {
      // Animasyon bittiğinde yeniden başlaması için ayarları sıfırla
      ticker = 0;
      animationDirection = 1;
      // İsteğe bağlı: Her döngüde farklı renkler için yeniden başlatılabilir
      // initPixels(); 
    }
  };
  
  const resize = () => {
    cancelAnimationFrame(request);
  
    const rect = container.getBoundingClientRect();
  
    width = Math.floor(rect.width);
    height = Math.floor(rect.height);
  
    canvas.width = width;
    canvas.height = height;
  
    initPixels();
  
    ticker = 0;
  
    animate();
  };
  
  new ResizeObserver(resize).observe(container);
  
  document.addEventListener('click', resize);