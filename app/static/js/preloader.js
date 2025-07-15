document.addEventListener('DOMContentLoaded', () => {
    // Preloader sadece index sayfasında çalışsın
    if (!document.querySelector('.hero')) {
        return;
    }

    // Preloader elementi var mı kontrol et
    const preloaderElement = document.getElementById('preloader');
    if (!preloaderElement) {
        return;
    }
    
    // Canvas elementi al
    const canvasElement = document.getElementById('preloader-canvas');
    if (!canvasElement) {
        return;
    }

    // Font'u önceden yükle
    const font = new FontFace('Poppins', 'url(https://fonts.gstatic.com/s/poppins/v20/pxiByp8kv8JHgFVrLEj6Z1xlFd2JQEk.woff2)');
    
    document.body.classList.add('preloader-active');
    
    // Rastgele sayı üreten yardımcı fonksiyon
    const rand = (min, max) => {
        return Math.random() * (max - min) + min;
    };

    // Her bir pikseli temsil eden sınıf
    class Pixel {
        constructor(x, y, color, speed, delay, delayHide, step, boundSize) {
            this.x = x;
            this.y = y;
            this.color = color;
            this.speed = rand(0.1, 0.9) * speed;
            this.size = 0;
            this.sizeStep = rand(0.1, 0.4);
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
            this.centerX = width / 2;
            this.centerY = height / 2;
        }

        // Pikseli canvas'a çizme
        draw(ctx) {
            const centerOffset = this.maxSizeAvailable * 0.5 - this.size * 0.5;
            ctx.fillStyle = this.color;
            ctx.fillRect(this.x + centerOffset, this.y + centerOffset, this.size, this.size);
        }

        // Pikseli gösterme animasyonu
        show() {
            this.isHidden = false;
            this.counterHide = 0;
            if (this.counter <= this.delay) {
                this.counter += this.counterStep;
                // Giriş animasyonu sırasında da titreşme efekti uygula
                if (this.isFlicking && this.size > 0) {
                    this.flicking();
                }
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

        // Pikseli gizleme animasyonu - dıştan ortaya doğru kaybolma efekti
        hide() {
            this.counter = 0;
            
            // Merkezden uzaklığı hesapla
            const dx = this.x - this.centerX;
            const dy = this.y - this.centerY;
            const distanceToCenter = Math.sqrt(dx * dx + dy * dy);
            
            // Maksimum mesafeye göre normalize et (0-1 aralığında)
            const maxDistance = Math.sqrt(Math.pow(width/2, 2) + Math.pow(height/2, 2));
            const normalizedDistance = distanceToCenter / maxDistance;
            
            // Dıştan içe doğru kaybolma efekti için gecikme hesapla
            // Merkeze uzak olanlar daha önce kaybolmaya başlasın
            const hideDelay = (1 - normalizedDistance) * 0.8; // 0.8 saniye maksimum gecikme
            
            if (this.counterHide <= this.delayHide + hideDelay) {
                this.counterHide += this.counterStep;
                // Çıkış animasyonu sırasında da titreşme efekti devam etsin
                this.flicking();
                return;
            }
            
            // Pikselin konumuna göre kaybolma hızını ayarla
            // Dıştaki pikseller daha hızlı kaybolsun
            const speedMultiplier = normalizedDistance * 0.5 + 1.5; // 1.5 - 2.0 arası hız çarpanı (daha hızlı)
            this.size -= 0.3 * speedMultiplier; // Daha hızlı kaybolma
            
            // Boyut küçüldükçe titreşme hızını azalt
            if (this.size > 0.5) {
                this.flicking();
            }
            
            // Boyut çok küçükse tamamen gizle
            if (this.size <= 0.1) {
                this.size = 0;
                this.isHidden = true;
            }
        }

        // Ekranda kaldığı sürece titreşme efekti
        flicking() {
            // Boyut 0'dan büyükse titreşme efekti uygula
            if (this.size > 0) {
                if (this.size >= this.maxSize) this.sizeDirection = -1;
                else if (this.size <= this.minSize) this.sizeDirection = 1;
                this.size += this.sizeDirection * this.speed;
            }
        }
    }

    // Bu fonksiyon artık kullanılmıyor çünkü preloader HTML'de zaten var
    // const createPreloader = () => { ... };

    const ctx = canvasElement.getContext("2d", { willReadFrequently: true });
    const interval = 1000 / 60; // 60 FPS

    let width;
    let height;
    let pixels = [];
    let request;
    let lastTime;
    let startTime;

    // Piksel gecikmesini pozisyona göre hesaplama (dalga efekti için)
    const getDelay = (x, y, isClosing = false) => {
        const dx = x - width * 0.5;
        const dy = y - height * 0.5;
        const distance = Math.sqrt(dx ** 2 + dy ** 2);
        
        // Açılışta merkeze yakın olanlar önce, uzak olanlar sonra görünür
        // Kapanışta tam tersi: uzak olanlar önce, merkeze yakın olanlar sonra kaybolur
        if (isClosing) {
            // Maksimum mesafeye göre normalize et
            const maxDistance = Math.sqrt(Math.pow(width/2, 2) + Math.pow(height/2, 2));
            // Uzaklığı tersine çevir - uzak olanlar küçük değer, yakın olanlar büyük değer alır
            return maxDistance - distance;
        }
        
        // Normal açılış için mesafeyi doğrudan döndür
        return distance;
    };

    // "beatify" yazısından pikselleri oluşturma
    const initTextPixels = () => {
        const text = "Beatify";  // Baş harfi büyük yap, daha şık görünüm
        const fontName = "'Poppins', sans-serif";
        const fontSize = Math.min(width, height) * 0.15; // Yazı boyutunu daha küçük ayarla
        
        ctx.font = `${fontSize}px ${fontName}`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Yazıyı canvas'ın ortasına çiz
        ctx.fillText(text, width / 2, height / 2);

        // Canvas'taki piksellerin verisini al
        const imageData = ctx.getImageData(0, 0, width, height).data;
        ctx.clearRect(0, 0, width, height); // Yazıyı temizle

        // Farklı renk paletleri oluştur
        const colorPalettes = [
            // Mor-Mavi Paleti (Gece)
            [
                '#7c4dff', // Mor
                '#536dfe', // İndigo
                '#448aff', // Mavi
                '#03a9f4', // Açık mavi
                '#1db954'  // Spotify yeşili
            ],
            // Kırmızı-Turuncu Paleti (Gündüz)
            [
                '#ff1744', // Kırmızı
                '#ff5252', // Açık kırmızı
                '#ff9100', // Turuncu
                '#ffab40', // Açık turuncu
                '#ffd740'  // Amber
            ],
            // Yeşil-Turkuaz Paleti (Bahar)
            [
                '#00c853', // Yeşil
                '#69f0ae', // Açık yeşil
                '#00e5ff', // Açık turkuaz
                '#18ffff', // Açık cyan
                '#64ffda'  // Teal
            ],
            // Pembe-Mor Paleti (Günbatımı)
            [
                '#d500f9', // Mor
                '#e040fb', // Açık mor
                '#ff4081', // Pembe
                '#ff80ab', // Açık pembe
                '#b388ff'  // Açık mor
            ],
            // Sarı-Altın Paleti (Güneş)
            [
                '#ffd600', // Sarı
                '#ffea00', // Açık sarı
                '#ffab00', // Amber
                '#ff6d00', // Turuncu
                '#ffcc80'  // Açık turuncu
            ]
        ];
        
        // Zamanı kullanarak renk paletini seç
        const now = new Date();
        const timeValue = now.getHours() + now.getMinutes() + now.getSeconds() + now.getMilliseconds();
        const paletteIndex = timeValue % colorPalettes.length;
        
        // Seçilen renk paleti
        const colors = colorPalettes[paletteIndex];
        
        // Arka plan her zaman siyah kalsın, sadece piksellerin renkleri değişsin

        const gap = 3; // Pikseller arasındaki boşluğu azalt (daha yoğun görünüm)
        const step = (width + height) * 0.006; // Biraz daha hızlı animasyon
        const speed = rand(0.01, 0.2); // Daha dengeli hız aralığı
        const maxSize = gap * 0.85; // Biraz daha küçük pikseller

        pixels = [];
        // Görüntü verisini tara ve yazıya ait pikselleri bul
        for (let y = 0; y < height; y += gap) {
            for (let x = 0; x < width; x += gap) {
                const index = (y * width + x) * 4;
                const alpha = imageData[index + 3]; // Pikselin alpha (görünürlük) değeri

                // Eğer piksel görünürse (yazının bir parçasıysa)
                if (alpha > 128) {
                    const color = colors[Math.floor(Math.random() * colors.length)];
                    const delay = getDelay(x, y);
                    const delayHide = 0; // Çıkışta gecikme olmasın
                    pixels.push(new Pixel(x, y, color, speed, delay, delayHide, step, maxSize));
                }
            }
        }
    };

    // Ana animasyon döngüsü
    const animate = () => {
        request = requestAnimationFrame(animate);

        const now = performance.now();
        const diff = now - (lastTime || 0);
        if (diff < interval) return;
        lastTime = now - diff % interval;

        const elapsedTime = (now - startTime) / 1000; // Geçen süre (saniye)

        ctx.clearRect(0, 0, width, height);

        // Animasyonun yaşam döngüsü
        const isClosing = elapsedTime >= 3; // 3 saniyeden sonra kapanış başlar
        
        // Kapanış aşamasında pikselleri merkeze olan uzaklığa göre sırala
        // Böylece dıştaki pikseller önce, içteki pikseller sonra kaybolur
        if (isClosing && !pixels.sorted) {
            // Her piksel için merkeze olan uzaklığı hesapla
            pixels.forEach(pixel => {
                const dx = pixel.x - width / 2;
                const dy = pixel.y - height / 2;
                pixel.distanceToCenter = Math.sqrt(dx * dx + dy * dy);
            });
            
            // Pikselleri merkeze olan uzaklığa göre sırala (uzaktan yakına)
            pixels.sort((a, b) => b.distanceToCenter - a.distanceToCenter);
            pixels.sorted = true; // Sadece bir kez sıralama yap
        }
        
        // Her pikseli güncelle ve çiz
        let allHidden = true;
        pixels.forEach((pixel, index) => {
            if (!isClosing) {
                // Açılış animasyonu
                pixel.show();
                if (!pixel.isHidden) allHidden = false;
            } else {
                // Kapanış animasyonu - dıştan içe doğru
                // Pikselin sırasına göre ek gecikme ekle (0-0.5 saniye arası - daha hızlı kaybolma)
                const extraDelay = (index / pixels.length) * 0.5;
                
                // Geçen süre kapanış başlangıcı + ek gecikmeyi geçtiyse pikseli gizle
                if (elapsedTime > 3 + extraDelay) {
                    // Çıkış animasyonu sırasında da titreşme efekti devam etsin
                    pixel.hide();
                } else {
                    // Kapanış başlamış ama henüz bu piksel için hide çağrılmamışsa
                    // titreşme efektini devam ettir
                    pixel.flicking();
                }
                
                // Eğer piksel hala görünürse, tüm pikseller kaybolmadı demektir
                if (!pixel.isHidden) allHidden = false;
            }
            pixel.draw(ctx);
        });

        // Tüm pikseller kaybolduğunda veya maksimum süre dolduğunda preloader'ı kaldır
        const allPixelsHidden = allHidden;
        const maxTimeReached = elapsedTime > 4.0; // Maksimum süreyi 4.0 saniyeye ayarla
        
        if (allPixelsHidden || maxTimeReached) {
            cancelAnimationFrame(request); // Animasyon döngüsünü durdur
            
            // Animasyon bittiğinde preloader'ı yavaşça yok et
            preloaderElement.style.opacity = '0';
            
            // CSS geçişi bittikten sonra preloader'ı tamamen kaldır ve ana içeriği göster
            preloaderElement.addEventListener('transitionend', () => {
                preloaderElement.remove();
                document.body.classList.remove('preloader-active');
            }, { once: true }); // Olay dinleyicisini bir kez çalıştır
        }
    };

    // Canvas boyutunu ayarlama ve animasyonu başlatma
    const setup = () => {
        const rect = preloaderElement.getBoundingClientRect();
        width = canvasElement.width = Math.floor(rect.width);
        height = canvasElement.height = Math.floor(rect.height);
        
        initTextPixels();
        startTime = performance.now();
        animate();
    };

    // Font yüklendikten sonra preloader'ı başlat
    font.load().then(() => {
        document.fonts.add(font);
        setup();
    }).catch(err => {
        console.error('Font yüklenemedi:', err);
        // Font yüklenemese bile preloader'ı başlat
        setup();
    });

    // Pencere yeniden boyutlandırıldığında animasyonu yeniden başlat
    window.addEventListener('resize', setup);
});
