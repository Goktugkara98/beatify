/**
 * EmbedService
 * Widget embed kodunun güncellenmesi ve kopyalama işlemlerinden sorumludur.
 */
class EmbedService {
    constructor(elements, config) {
        this.elements = elements;
        this.config = config;
        this.widgetDimensions = {
            'modern': { width: 600, height: 600 },
            'classic': { width: 600, height: 250 }
        };

        this._bindCopyEvents();
    }

    /**
     * Seçilen temaya göre embed kodunu günceller.
     * @param {string} theme - Seçilen tema adı
     */
    updateCode(theme, widgetUrl = null) {
        const url = widgetUrl || this.config.widgetUrl;
        const dims = this.widgetDimensions[theme] || this.widgetDimensions['modern'];
        const code = `<iframe src="${url}" width="${dims.width}" height="${dims.height}" frameborder="0" scrolling="no" allowtransparency="true"></iframe>`;
        
        if (this.elements.embedCodeArea) {
            this.elements.embedCodeArea.value = code;
        }
    }

    /**
     * Kopyalama butonlarının eventlerini dinler.
     */
    _bindCopyEvents() {
        const copyButtons = document.querySelectorAll('.btn-copy, .btn-copy-code');

        copyButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetSelector = btn.dataset.clipboardTarget;

                // Yeni layout'ta explicit bir data-clipboard-target yok, bu yüzden
                // güvenli bir şekilde fallback uygulayalım.
                if (!targetSelector) {
                    // Eğer global config'te embedCode alanı varsa onu kullan
                    const textarea = this.elements && this.elements.embedCodeArea
                        ? this.elements.embedCodeArea
                        : document.getElementById('embedCode');

                    if (!textarea) return;

                    textarea.select();
                    textarea.setSelectionRange(0, 99999);

                    try {
                        const text = textarea.value;
                        if (navigator.clipboard && navigator.clipboard.writeText) {
                            navigator.clipboard.writeText(text);
                        } else {
                            document.execCommand('copy');
                        }
                    } catch (e) {
                        console.warn('Clipboard copy failed', e);
                    }

                    const originalIcon = btn.innerHTML;
                    btn.innerHTML = '<i class="fas fa-check"></i>';
                    setTimeout(() => {
                        btn.innerHTML = originalIcon;
                    }, 2000);

                    return;
                }

                const target = document.querySelector(targetSelector);
                if (!target) return;

                target.select();
                target.setSelectionRange(0, 99999); // Mobil uyumluluk
                
                navigator.clipboard.writeText(target.value).then(() => {
                    const originalIcon = btn.innerHTML;
                    btn.innerHTML = '<i class="fas fa-check"></i>';
                    setTimeout(() => {
                        btn.innerHTML = originalIcon;
                    }, 2000);
                }).catch((e) => {
                    console.warn('Clipboard write failed', e);
                });
            });
        });
    }
}

