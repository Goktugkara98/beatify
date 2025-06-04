// widget-manager.js
document.addEventListener('DOMContentLoaded', function() {
    // Widget seçim butonları
    const widgetSelectButtons = document.querySelectorAll('.widget-select-btn');
    // Widget kartları
    const widgetCards = document.querySelectorAll('.widget-card');
    // Widget önizleme alanı
    const widgetPreviewContainer = document.getElementById('widget-preview');
    
    // Seçilen widget tipini saklamak için değişken
    let selectedWidgetType = null;
    let selectedWidgetCard = null;
    
    // Pixel canvas elementlerini saklamak için
    const pixelCanvases = {};
    
    // Carousel değişkenleri
    let currentSlide = 0;
    const cardsPerSlide = window.innerWidth < 768 ? 1 : window.innerWidth < 1200 ? 2 : 3;
    const cardsContainer = document.querySelector('.widget-cards-container');
    const totalSlides = Math.ceil(widgetCards.length / cardsPerSlide);
    const indicators = document.querySelectorAll('.indicator');
    const prevBtn = document.querySelector('.prev-btn');
    const nextBtn = document.querySelector('.next-btn');
    
    // Carousel göstergelerini ayarla
    updateIndicators();
    
    // Carousel navigasyon butonları için event listener'lar
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
    
    // Gösterge noktaları için event listener'lar
    indicators.forEach((indicator, index) => {
        indicator.addEventListener('click', function() {
            goToSlide(index);
        });
    });
    
    // Carousel'i kaydırma fonksiyonu
    function navigateCarousel(direction) {
        if (direction === 'next') {
            currentSlide = (currentSlide + 1) % totalSlides;
        } else {
            currentSlide = (currentSlide - 1 + totalSlides) % totalSlides;
        }
        
        goToSlide(currentSlide);
    }
    
    // Belirli bir slide'a gitme fonksiyonu
    function goToSlide(slideIndex) {
        currentSlide = slideIndex;
        const offset = -slideIndex * (cardsPerSlide * (widgetCards[0].offsetWidth + 24)); // 24px = gap
        cardsContainer.style.transform = `translateX(${offset}px)`;
        updateIndicators();
    }
    
    // Göstergeleri ve navigasyon butonlarını güncelleme fonksiyonu
    function updateIndicators() {
        // Gösterge noktalarını güncelle
        indicators.forEach((indicator, index) => {
            if (index === currentSlide) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
        
        // İlk slide'daysa geri butonunu gizle, değilse göster
        if (prevBtn) {
            if (currentSlide === 0) {
                prevBtn.style.opacity = '0';
                prevBtn.style.pointerEvents = 'none';
            } else {
                prevBtn.style.opacity = '1';
                prevBtn.style.pointerEvents = 'auto';
            }
        }
        
        // Son slide'daysa ileri butonunu gizle, değilse göster
        if (nextBtn) {
            if (currentSlide === totalSlides - 1) {
                nextBtn.style.opacity = '0';
                nextBtn.style.pointerEvents = 'none';
            } else {
                nextBtn.style.opacity = '1';
                nextBtn.style.pointerEvents = 'auto';
            }
        }
    }
    
    // Ekran boyutu değiştiğinde carousel'i güncelle
    window.addEventListener('resize', function() {
        const newCardsPerSlide = window.innerWidth < 768 ? 1 : window.innerWidth < 1200 ? 2 : 3;
        if (newCardsPerSlide !== cardsPerSlide) {
            // Ekran boyutu değiştiğinde sayfayı yenile
            location.reload();
        }
    });
    
    // Tüm pixel canvas elementlerini topla
    document.querySelectorAll('pixel-canvas').forEach(canvas => {
        // Parent widget kartını bul
        const parentCard = canvas.closest('.widget-card');
        if (parentCard) {
            const widgetType = parentCard.getAttribute('data-widget-type');
            pixelCanvases[widgetType] = canvas;
            
            // Başlangıçta tüm animasyonları durdur ve gizle
            canvas._isActive = false;
            canvas.style.display = 'none';
        }
    });
    
    // Widget seçim butonları için event listener
    widgetSelectButtons.forEach(button => {
        button.addEventListener('click', function() {
            const widgetType = this.getAttribute('data-widget-type');
            selectWidget(widgetType, this.closest('.widget-card'));
        });
    });
    
    // Widget kartı için event listener
    widgetCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Eğer tıklanan element buton değilse (kartın kendisine tıklandıysa)
            if (!e.target.classList.contains('widget-select-btn')) {
                const widgetType = this.getAttribute('data-widget-type');
                const selectBtn = this.querySelector('.widget-select-btn');
                selectWidget(widgetType, this);
            }
        });
    });
    
    // Widget seçme fonksiyonu
    function selectWidget(widgetType, widgetCard) {
        // Önceki seçimi temizle
        widgetCards.forEach(card => {
            card.classList.remove('selected');
            
            // Önceki seçilen kartın butonundan selected sınıfını kaldır
            const btn = card.querySelector('.widget-select-btn');
            if (btn) btn.classList.remove('selected');
            
            // Önceki seçilen kartın pixel animasyonunu durdur ve gizle
            const cardType = card.getAttribute('data-widget-type');
            if (pixelCanvases[cardType]) {
                // Animasyonu durdur
                pixelCanvases[cardType].handleAnimation('disappear');
                
                // Pixel canvas'i tamamen gizle
                pixelCanvases[cardType].style.display = 'none';
            }
        });
        
        // Yeni seçimi işaretle
        widgetCard.classList.add('selected');
        
        // Seçilen kartın butonunu işaretle
        const selectBtn = widgetCard.querySelector('.widget-select-btn');
        if (selectBtn) selectBtn.classList.add('selected');
        
        // Seçilen widget tipini al
        selectedWidgetType = widgetType;
        selectedWidgetCard = widgetCard;
        
        // Seçilen kartın pixel animasyonunu başlat ve sürekli çalışmasını sağla
        if (pixelCanvases[widgetType]) {
            // Pixel canvas'i görünür yap
            pixelCanvases[widgetType].style.display = 'block';
            
            // Animasyonu başlat
            pixelCanvases[widgetType].handleAnimation('appear');
            pixelCanvases[widgetType]._isActive = true;
            
            // Animasyonun sürekli çalışmasını sağla
            pixelCanvases[widgetType].keepAnimating = true;
        }
        
        // Widget önizlemesini güncelle
        updateWidgetPreview(widgetType);
    }
    
    // Widget önizlemesini güncelleme fonksiyonu
    function updateWidgetPreview(widgetType) {
        if (!widgetPreviewContainer) return;
        
        // Önizleme içeriğini temizle
        widgetPreviewContainer.innerHTML = '';
        
        if (!widgetType) {
            // Widget seçilmemişse mesaj göster
            const noSelectionMessage = document.createElement('p');
            noSelectionMessage.className = 'no-selection-message';
            noSelectionMessage.textContent = 'Önizleme için bir widget seçin';
            widgetPreviewContainer.appendChild(noSelectionMessage);
            return;
        }
        
        // Seçilen widget tipine göre önizleme oluştur
        const previewContent = document.createElement('div');
        previewContent.className = 'widget-preview-content';
        
        // Widget tipine göre farklı stil ve içerik
        switch(widgetType) {
            case 'normal':
                previewContent.innerHTML = `
                    <div class="widget-preview-placeholder normal-widget">
                        <h4>Normal Widget</h4>
                        <p>Standart Spotify widget önizlemesi</p>
                    </div>
                `;
                break;
            case 'alt':
                previewContent.innerHTML = `
                    <div class="widget-preview-placeholder alt-widget">
                        <h4>Alt Widget</h4>
                        <p>Alternatif Spotify widget önizlemesi</p>
                    </div>
                `;
                break;
            case 'neon':
                previewContent.innerHTML = `
                    <div class="widget-preview-placeholder neon-widget">
                        <h4>Neon Widget</h4>
                        <p>Neon efektli Spotify widget önizlemesi</p>
                    </div>
                `;
                break;
            default:
                previewContent.innerHTML = `
                    <div class="widget-preview-placeholder">
                        <p>Bilinmeyen widget tipi</p>
                    </div>
                `;
        }
        
        widgetPreviewContainer.appendChild(previewContent);
        
        // Widget seçildiğinde konsola bilgi yazdır (geliştirme amaçlı)
        console.log(`Widget seçildi: ${widgetType}`);
    }
    
    // Sayfa yüklendiğinde önizleme alanını başlangıç durumuna getir
    if (widgetPreviewContainer) {
        updateWidgetPreview(null);
    }
    
    console.log('Widget Manager JS yüklendi.');
});
