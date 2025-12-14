/**
 * PreviewService
 * Widget önizleme alanının boyutlandırılması, ölçeklenmesi ve yenilenmesinden sorumludur.
 */
class PreviewService {
    constructor(elements, config) {
        this.elements = elements;
        this.config = config;
        this.widgetDimensions = {
            'modern': { width: 600, height: 600 },
            'classic': { width: 600, height: 250 }
        };

        this._initResizeListener();
    }

    /**
     * Seçilen temaya göre önizleme boyutlarını günceller.
     * @param {string} theme - Seçilen tema adı
     */
    updateDimensions(theme) {
        const dims = this.widgetDimensions[theme] || this.widgetDimensions['modern'];
        
        // Iframe ve Wrapper boyutlarını gerçek widget boyutlarına ayarla
        this.elements.previewFrame.style.width = `${dims.width}px`;
        this.elements.previewFrame.style.height = `${dims.height}px`;
        this.elements.iframeWrapper.style.width = `${dims.width}px`;
        this.elements.iframeWrapper.style.height = `${dims.height}px`;

        // Ölçekleme işlemini tetikle
        this.fitToContainer(dims.width, dims.height);
    }

    /**
     * Widget'ı container içine sığacak şekilde ölçekler.
     * @param {number} widgetWidth 
     * @param {number} widgetHeight 
     */
    fitToContainer(widgetWidth, widgetHeight) {
        const container = this.elements.previewContainer;
        const wrapper = this.elements.iframeWrapper;

        if (!container || !wrapper) return;

        const containerStyles = window.getComputedStyle(container);
        // Paddingleri çıkar
        const containerW = container.clientWidth - parseFloat(containerStyles.paddingLeft) - parseFloat(containerStyles.paddingRight);
        const containerH = container.clientHeight - parseFloat(containerStyles.paddingTop) - parseFloat(containerStyles.paddingBottom);

        // Ölçek faktörünü hesapla
        const scaleW = containerW / widgetWidth;
        const scaleH = containerH / widgetHeight;
        
        // Önizleme alanına "tam oturması" için ekstra boşluk bırakma.
        // (Eski davranış: * 0.9 ile %10 boşluk bırakıyordu.)
        let scale = Math.min(scaleW, scaleH);

        // Büyütme yapma (sadece küçültme)
        if (scale > 1) scale = 1; 

        // Ölçekleme ve Ortalama (Absolute Center + Scale)
        wrapper.style.transform = `translate(-50%, -50%) scale(${scale})`;
        wrapper.style.transformOrigin = 'center center';
        wrapper.style.margin = '0';
    }

    /**
     * Önizlemeyi (iframe) yeniler veya yeni URL yükler.
     * @param {string|null} newUrl - Eğer belirtilirse iframe'in src'sini değiştirir.
     * @param {boolean} autoShow - Yükleme bitince otomatik olarak opacity'yi 1 yapar.
     */
    async refresh(newUrl = null, autoShow = true) {
        const { iframeWrapper, previewFrame } = this.elements;
        
        // Eğer yeni URL varsa (tema değişimi), önce outro animasyonunu tetikle
        if (newUrl) {
            // 1. Outro sinyali gönder
            if (previewFrame.contentWindow) {
                previewFrame.contentWindow.postMessage('startOutro', '*');
            }

            // 2. Outro animasyonunun tamamlanmasını bekle (örn: 800ms)
            // Not: Widget'tan 'outroComplete' mesajı beklemek daha sağlam olurdu ama
            // şimdilik sabit süre ile glitch'i önleyelim.
            await new Promise(resolve => setTimeout(resolve, 800));
        }

        // 3. Yükleniyor efekti için opaklığı düşür (Fade Out)
        iframeWrapper.style.opacity = '0';
        
        // Spinner göster (yükleniyor)
        if (this.elements.previewContainer) {
            this.elements.previewContainer.classList.add('is-loading');
        }
        
        // Fade out animasyonu için kısa bir bekleme (CSS transition: opacity 0.3s varsayarsak)
        if (newUrl) {
             await new Promise(resolve => setTimeout(resolve, 300));
        }
        
        // 4. URL belirle
        let urlToLoad;
        if (newUrl) {
            urlToLoad = newUrl;
        } else {
            const currentSrc = previewFrame.src;
            if (!currentSrc || currentSrc === 'about:blank' || currentSrc === '') return;
            
            const urlObj = new URL(currentSrc);
            urlObj.searchParams.set('t', new Date().getTime());
            urlToLoad = urlObj.toString();
        }
        
        // 5. Iframe yüklemesini dinle
        const onLoadHandler = () => {
            // Yüklendiğinde biraz bekle (render için) sonra göster
            setTimeout(() => {
                if (this.elements.previewContainer) {
                    this.elements.previewContainer.classList.remove('is-loading');
                }
                
                // Sadece element görünür durumdaysa (örneğin modal açıksa) opacity'yi 1 yap
                // Modal kapalıyken offsetParent null döner
                if (autoShow && iframeWrapper.offsetParent !== null) {
                    iframeWrapper.style.opacity = '1';
                }
            }, 300);
            previewFrame.removeEventListener('load', onLoadHandler);
        };

        previewFrame.addEventListener('load', onLoadHandler);

        // 6. Yeni URL'i yükle
        previewFrame.src = urlToLoad;
    }

    /**
     * Pencere boyutu değiştiğinde ölçeklemeyi yeniden hesaplar.
     */
    _initResizeListener() {
        window.addEventListener('resize', () => {
            // Aktif temayı bulmak yerine mevcut boyutları DOM'dan okuyabiliriz
            // veya son set edilen temayı saklayabiliriz.
            // Basitlik için wrapper'ın inline style'ındaki genişliği/yüksekliği alalım.
            const width = parseInt(this.elements.iframeWrapper.style.width) || 600;
            const height = parseInt(this.elements.iframeWrapper.style.height) || 600;
            this.fitToContainer(width, height);
        });
    }
}

