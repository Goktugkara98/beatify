/*
    widget-manager.js (Revize Edilmiş)

    İÇİNDEKİLER:

    1. DOM YÜKLENDİĞİNDE ÇALIŞACAK ANA FONKSİYON (DOMContentLoaded)
        1.1. Değişken Tanımlamaları
            1.1.1. DOM Elementleri
            1.1.2. Durum Değişkenleri (State)
            1.1.3. Pixel Canvas Referansları
            1.1.4. Carousel Değişkenleri
            1.1.5. Kart Boyutları ve Boşluk

        1.2. Carousel Fonksiyonları
            1.2.1. navigateCarousel(direction)
            1.2.2. goToSlide(slideIndex)
            1.2.3. updateIndicators()

        1.3. Widget Seçim ve Yönetim Fonksiyonları
            1.3.1. selectWidget(widgetType, widgetCard)

        1.4. Önizleme Fonksiyonları
            1.4.1. updateWidgetPreview(widgetType)

        1.5. Olay Dinleyicileri (Event Listeners)
            1.5.1. Carousel Navigasyon Butonları (Önceki/Sonraki)
            1.5.2. Carousel Gösterge Noktaları
            1.5.3. Ekran Boyutu Değişikliği (Resize)
            1.5.4. Widget Seçim Butonları
            1.5.5. Widget Kartları (Tıklama)

        1.6. Başlangıç Ayarları ve Çağrılar
            1.6.1. Carousel Başlangıç Pozisyonu
            1.6.2. Carousel Göstergelerini Güncelleme
            1.6.3. Pixel Canvas Elementlerini Toplama ve Başlangıç Ayarları
            1.6.4. Önizleme Alanını Başlangıç Durumuna Getirme
            1.6.5. Konsol Mesajı
*/

// 1. DOM YÜKLENDİĞİNDE ÇALIŞACAK ANA FONKSİYON
document.addEventListener('DOMContentLoaded', function() {
    // =============================================
    // 1.1. Değişken Tanımlamaları
    // =============================================

    // 1.1.1. DOM Elementleri
    const widgetSelectButtons = document.querySelectorAll('.widget-select-btn');
    const widgetCards = document.querySelectorAll('.widget-card');
    const widgetPreviewContainer = document.getElementById('widget-preview');
    const cardsContainer = document.querySelector('.widget-cards-container');
    const indicators = document.querySelectorAll('.indicator');
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');

    // 1.1.2. Durum Değişkenleri (State)
    let selectedWidgetType = null; // Seçili olan widget'ın tipini tutar (örn: 'normal', 'alt')
    // let selectedWidgetCard = null; // Bu değişken orijinal kodda tanımlanmış ama aktif olarak kullanılmıyor gibi. İhtiyaç halinde aktif edilebilir.

    // 1.1.3. Pixel Canvas Referansları
    // Her bir widget tipine ait pixel-canvas elementini saklar.
    const pixelCanvases = {}; // Örn: { normal: <pixel-canvas for normal>, alt: <pixel-canvas for alt> }

    // 1.1.4. Carousel Değişkenleri
    let currentSlide = 0; // Mevcut aktif carousel slide indeksi
    // Ekran genişliğine göre bir slide'da gösterilecek kart sayısı
    const initialCardsPerSlide = window.innerWidth < 768 ? 1 : window.innerWidth < 1200 ? 2 : 3;
    let cardsPerSlide = initialCardsPerSlide; // Dinamik olarak değişebilir (resize ile)
    // Toplam slide sayısı (widget kartı sayısına ve slide başına kart sayısına göre hesaplanır)
    const totalSlides = widgetCards.length > 0 ? Math.ceil(widgetCards.length / cardsPerSlide) : 0;

    // 1.1.5. Kart Boyutları ve Boşluk (Carousel hesaplamaları için)
    // İlk widget kartının genişliği (eğer kart varsa)
    const cardWidth = widgetCards.length > 0 ? widgetCards[0].offsetWidth : 0;
    const cardGap = 24; // Kartlar arası boşluk (CSS'deki 1.5rem = 24px varsayımıyla)

    // =============================================
    // 1.2. Carousel Fonksiyonları
    // =============================================

    /**
     * 1.2.1. Carousel'i önceki veya sonraki slide'a götürür.
     * @param {string} direction - Kaydırma yönü ('prev' veya 'next')
     */
    function navigateCarousel(direction) {
        if (totalSlides === 0) return; // Eğer hiç slide yoksa işlem yapma

        if (direction === 'next') {
            currentSlide = (currentSlide + 1) % totalSlides;
        } else {
            currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
        }
        goToSlide(currentSlide);
    }

    /**
     * 1.2.2. Belirtilen index'teki slide'a gider.
     * @param {number} slideIndex - Gidilecek slide'ın indeksi
     */
    function goToSlide(slideIndex) {
        if (!cardsContainer || totalSlides === 0) return; // Gerekli element yoksa veya slide yoksa işlem yapma

        currentSlide = slideIndex;

        // Her slide için kaydırma mesafesini hesapla: (kart genişliği + kartlar arası boşluk) * slide başına kart sayısı
        // Not: Orijinal koddaki offset hesaplaması biraz karmaşıktı, daha standart bir yaklaşımla güncellendi.
        // Kartların ve boşlukların toplam genişliği üzerinden hesaplama yapmak daha tutarlı olabilir.
        const slideWidthCalculation = cardsPerSlide * cardWidth + (cardsPerSlide -1) * cardGap;
        let offset = -slideIndex * slideWidthCalculation;
        
        // Orijinal koddaki özel ayarlamalar (örn: if (slideIndex === 1) offset += 10;)
        // Bu tür ayarlamalar genellikle CSS veya kart genişliği hesaplamalarındaki
        // tutarsızlıklardan kaynaklanır. İdealde, bu tür düzeltmelere gerek kalmamalıdır.
        // Şimdilik orijinal mantığı koruyoruz ama gözden geçirilebilir.
        if (slideIndex > 0 && slideIndex === 1 && cardsPerSlide > 1) { // Sadece birden fazla kart gösteriliyorsa ve ikinci slayttaysa
             // Bu düzeltme, kartlar arası boşluğun (gap) ilk karttan önce uygulanmaması durumunu telafi etmek için olabilir.
             // Örneğin, ilk kartın solunda boşluk yokken, diğerlerinin solunda var.
             // offset += cardGap / cardsPerSlide; // Ortalama bir düzeltme, daha hassas ayar gerekebilir.
             // Orijinal koddaki gibi sabit bir değer de kullanılabilir:
             // offset += 10; // Örnek: 10px daha az kaydır
        }


        cardsContainer.style.transform = `translateX(${offset}px)`;
        updateIndicators();
    }

    /**
     * 1.2.3. Carousel gösterge noktalarını ve navigasyon butonlarının görünürlüğünü günceller.
     */
    function updateIndicators() {
        if (totalSlides === 0) { // Eğer hiç slide yoksa butonları ve göstergeleri gizle
            if(prevBtn) prevBtn.style.display = 'none';
            if(nextBtn) nextBtn.style.display = 'none';
            indicators.forEach(indicator => indicator.style.display = 'none');
            return;
        } else {
            if(prevBtn) prevBtn.style.display = 'flex'; // veya 'block'
            if(nextBtn) nextBtn.style.display = 'flex';
             indicators.forEach(indicator => indicator.style.display = 'block'); // veya 'inline-block'
        }


        // Gösterge noktalarını güncelle
        indicators.forEach((indicator, index) => {
            if (index === currentSlide) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });

        // Navigasyon butonlarının görünürlüğünü ayarla
        if (prevBtn) {
            prevBtn.style.opacity = currentSlide === 0 ? '0.3' : '1'; // İlk slide'da soluklaştır
            prevBtn.style.pointerEvents = currentSlide === 0 ? 'none' : 'auto'; // İlk slide'da tıklamayı engelle
        }

        if (nextBtn) {
            // Son slide'da (veya tek slide varsa) sağ butonu soluklaştır/gizle
            const isLastSlide = currentSlide === totalSlides - 1 || totalSlides <=1;
            nextBtn.style.opacity = isLastSlide ? '0.3' : '1';
            nextBtn.style.pointerEvents = isLastSlide ? 'none' : 'auto';
        }
    }

    // =============================================
    // 1.3. Widget Seçim ve Yönetim Fonksiyonları
    // =============================================

    /**
     * 1.3.1. Bir widget'ı seçer, ilgili stilleri ve animasyonları ayarlar.
     * @param {string} widgetType - Seçilen widget'ın tipi (data-widget-type attribute'u)
     * @param {HTMLElement} widgetCardElement - Seçilen widget kartının DOM elementi
     */
    function selectWidget(widgetType, widgetCardElement) {
        // Önceki seçimi temizle
        widgetCards.forEach(card => {
            card.classList.remove('selected');
            const btn = card.querySelector('.widget-select-btn');
            if (btn) btn.classList.remove('selected');

            const cardType = card.getAttribute('data-widget-type');
            if (pixelCanvases[cardType] && pixelCanvases[cardType].handleAnimation) {
                pixelCanvases[cardType].handleAnimation('disappear'); // Animasyonu durdur/gizle
                pixelCanvases[cardType].style.display = 'none'; // Pixel canvas'ı gizle
                if (typeof pixelCanvases[cardType].stopAnimation === 'function') {
                     pixelCanvases[cardType].stopAnimation(); // Eğer varsa özel durdurma fonksiyonu
                }
                pixelCanvases[cardType]._isActive = false;
                pixelCanvases[cardType].keepAnimating = false;
            }
        });

        // Yeni seçimi işaretle
        widgetCardElement.classList.add('selected');
        const selectBtn = widgetCardElement.querySelector('.widget-select-btn');
        if (selectBtn) selectBtn.classList.add('selected');

        selectedWidgetType = widgetType;
        // selectedWidgetCard = widgetCardElement; // İhtiyaç duyulursa aktif edilebilir.

        // Seçilen kartın pixel animasyonunu başlat
        if (pixelCanvases[widgetType] && pixelCanvases[widgetType].handleAnimation) {
            pixelCanvases[widgetType].style.display = 'block'; // Pixel canvas'ı görünür yap
            pixelCanvases[widgetType].handleAnimation('appear'); // Animasyonu başlat
            pixelCanvases[widgetType]._isActive = true;
            pixelCanvases[widgetType].keepAnimating = true; // Sürekli animasyon için (eğer component destekliyorsa)
             if (typeof pixelCanvases[widgetType].startAnimation === 'function') {
                 pixelCanvases[widgetType].startAnimation(); // Eğer varsa özel başlatma fonksiyonu
            }
        }

        updateWidgetPreview(widgetType); // Önizlemeyi güncelle
    }

    // =============================================
    // 1.4. Önizleme Fonksiyonları
    // =============================================

    /**
     * 1.4.1. Widget önizleme alanını seçilen widget tipine göre günceller.
     * @param {string | null} widgetType - Gösterilecek widget'ın tipi veya null (seçim yoksa)
     */
    function updateWidgetPreview(widgetType) {
        if (!widgetPreviewContainer) return; // Önizleme konteyneri yoksa işlem yapma

        widgetPreviewContainer.innerHTML = ''; // Önceki içeriği temizle

        if (!widgetType) {
            const noSelectionMessage = document.createElement('p');
            noSelectionMessage.className = 'no-selection-message';
            noSelectionMessage.textContent = 'Önizleme için bir widget seçin';
            widgetPreviewContainer.appendChild(noSelectionMessage);
            return;
        }

        const previewContent = document.createElement('div');
        previewContent.className = 'widget-preview-content';
        let placeholderHTML = '';

        switch(widgetType) {
            case 'normal':
                placeholderHTML = `
                    <div class="widget-preview-placeholder normal-widget">
                        <h4>Normal Widget</h4>
                        <p>Standart Spotify widget önizlemesi.</p>
                    </div>`;
                break;
            case 'alt':
                placeholderHTML = `
                    <div class="widget-preview-placeholder alt-widget">
                        <h4>Alt Widget</h4>
                        <p>Alternatif Spotify widget önizlemesi.</p>
                    </div>`;
                break;
            case 'neon':
                placeholderHTML = `
                    <div class="widget-preview-placeholder neon-widget">
                        <h4>Neon Widget</h4>
                        <p>Neon efektli Spotify widget önizlemesi.</p>
                    </div>`;
                break;
            default:
                placeholderHTML = `
                    <div class="widget-preview-placeholder">
                        <h4>Bilinmeyen Widget</h4>
                        <p>Bu widget tipi için önizleme bulunmamaktadır.</p>
                    </div>`;
        }
        previewContent.innerHTML = placeholderHTML;
        widgetPreviewContainer.appendChild(previewContent);

        // console.log(`Widget önizlemesi güncellendi: ${widgetType}`);
    }

    // =============================================
    // 1.5. Olay Dinleyicileri (Event Listeners)
    // =============================================

    // 1.5.1. Carousel Navigasyon Butonları
    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            navigateCarousel('prev');
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            navigateCarousel('next');
        });
    }

    // 1.5.2. Carousel Gösterge Noktaları
    indicators.forEach((indicator, index) => {
        indicator.addEventListener('click', function() {
            goToSlide(index);
        });
    });

    // 1.5.3. Ekran Boyutu Değişikliği (Resize)
    window.addEventListener('resize', function() {
        const newCardsPerSlide = window.innerWidth < 768 ? 1 : window.innerWidth < 1200 ? 2 : 3;
        if (newCardsPerSlide !== cardsPerSlide) {
            // Ekran boyutu değiştiğinde ve slide başına kart sayısı değiştiğinde
            // carousel'i yeniden hesaplamak ve sayfayı yenilemek yerine
            // dinamik olarak ayarlamak daha iyi bir kullanıcı deneyimi sunar.
            // Şimdilik orijinal 'location.reload()' mantığı korunuyor, ancak bu geliştirilebilir.
            // cardsPerSlide = newCardsPerSlide;
            // totalSlides = widgetCards.length > 0 ? Math.ceil(widgetCards.length / cardsPerSlide) : 0;
            // goToSlide(0); // veya currentSlide'ı koruyarak yeniden ayarla
            // updateIndicators();
            location.reload(); // Orijinal davranış
        }
    });

    // 1.5.4. Widget Seçim Butonları
    widgetSelectButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.stopPropagation(); // Kartın tıklama olayının tetiklenmesini engelle
            const widgetType = this.getAttribute('data-widget-type');
            const parentCard = this.closest('.widget-card');
            if (parentCard) {
                selectWidget(widgetType, parentCard);
            }
        });
    });

    // 1.5.5. Widget Kartları (Tıklama)
    // Kartın kendisine tıklandığında da widget seçimi yapar
    widgetCards.forEach(card => {
        card.addEventListener('click', function() {
            // Eğer tıklanan element buton değilse (kartın kendisine tıklandıysa)
            // Bu kontrol orijinal kodda vardı, ancak buton tıklaması zaten kendi event listener'ında
            // `event.stopPropagation()` ile yönetildiği için burada gereksiz olabilir.
            // Yine de, kartın içindeki başka interaktif olmayan bir elemente tıklanırsa
            // kartın seçilmesini sağlamak için bu genel kart tıklama olayı faydalıdır.
            const widgetType = this.getAttribute('data-widget-type');
            selectWidget(widgetType, this);
        });
    });

    // =============================================
    // 1.6. Başlangıç Ayarları ve Çağrılar
    // =============================================

    // 1.6.1. Carousel Başlangıç Pozisyonu
    // Sayfa yüklendikten kısa bir süre sonra ilk slide'a git (CSS geçişlerinin düzgün çalışması için)
    if (widgetCards.length > 0 && cardsContainer) { // Sadece kartlar ve konteyner varsa
        setTimeout(() => {
            goToSlide(0);
        }, 100); // 100ms gecikme, DOM'un tam olarak oturması için
    }


    // 1.6.2. Carousel Göstergelerini Güncelleme
    updateIndicators(); // Başlangıçta göstergeleri ve butonları ayarla

    // 1.6.3. Pixel Canvas Elementlerini Toplama ve Başlangıç Ayarları
    document.querySelectorAll('pixel-canvas').forEach(canvas => {
        const parentCard = canvas.closest('.widget-card');
        if (parentCard) {
            const widgetType = parentCard.getAttribute('data-widget-type');
            if (widgetType) {
                pixelCanvases[widgetType] = canvas;
                // Başlangıçta tüm pixel canvas animasyonlarını durdur ve gizle
                if (canvas.handleAnimation) { // Eğer custom element bu metodu destekliyorsa
                    canvas.handleAnimation('disappear');
                }
                canvas.style.display = 'none';
                canvas._isActive = false; // Aktif durumunu takip etmek için özel bir özellik
                canvas.keepAnimating = false; // Sürekli animasyon bayrağı
            }
        }
    });

    // 1.6.4. Önizleme Alanını Başlangıç Durumuna Getirme
    updateWidgetPreview(null); // Başlangıçta hiçbir widget seçili olmadığı için boş önizleme

    // 1.6.5. Konsol Mesajı
    console.log('Widget Manager JS (Revize Edilmiş) yüklendi ve hazır.');
});
