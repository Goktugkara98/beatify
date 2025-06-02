/**
 * Widget Manager JavaScript
 * 
 * Bu dosya, Spotify Widget Manager sayfasının tüm etkileşimli işlevlerini yönetir:
 * - Widget yapılandırma seçeneklerini işler
 * - Widget URL'sini oluşturur
 * - Önizleme iframe'ini günceller
 * - Kopyalama işlevlerini sağlar
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elementleri
    const widgetTypeSelect = document.getElementById('widget-type');
    const widgetThemeSelect = document.getElementById('widget-theme');
    const widgetAlbumArtSelect = document.getElementById('widget-album-art');
    const widgetFontSizeSelect = document.getElementById('widget-font-size');
    const generateWidgetBtn = document.getElementById('generate-widget-btn');
    const widgetPreviewIframe = document.getElementById('widget-preview-iframe');
    const widgetUrlInput = document.getElementById('widget-url');
    const widgetEmbedCodeTextarea = document.getElementById('widget-embed-code');
    const copyUrlBtn = document.getElementById('copy-url-btn');
    const copyEmbedBtn = document.getElementById('copy-embed-btn');

    // Sabit değerler
    const WIDGET_TOKEN = 'abcd'; // Gerçek uygulamada bu değer backend'den dinamik olarak alınmalı
    const BASE_URL = window.location.origin;

    // Widget URL'sini oluştur
    function generateWidgetUrl() {
        const widgetType = widgetTypeSelect.value;
        const widgetTheme = widgetThemeSelect.value;
        const widgetAlbumArt = widgetAlbumArtSelect.value;
        const widgetFontSize = widgetFontSizeSelect.value;

        // Widget URL'sini oluştur
        const widgetUrl = `${BASE_URL}/spotify/widget/${WIDGET_TOKEN}?type=${widgetType}&theme=${widgetTheme}&albumart=${widgetAlbumArt}&fontsize=${widgetFontSize}`;
        
        return widgetUrl;
    }

    // Gömme kodunu oluştur
    function generateEmbedCode(widgetUrl) {
        return `<iframe src="${widgetUrl}" frameborder="0" width="100%" height="300" style="max-width: 600px;"></iframe>`;
    }

    // Widget önizlemesini güncelle
    function updateWidgetPreview(widgetUrl) {
        widgetPreviewIframe.src = widgetUrl;
        widgetUrlInput.value = widgetUrl;
        widgetEmbedCodeTextarea.value = generateEmbedCode(widgetUrl);
    }

    // Kopyalama başarı bildirimi göster
    function showCopySuccess(message) {
        // Eğer zaten bir bildirim varsa, onu kaldır
        const existingNotification = document.querySelector('.copy-success');
        if (existingNotification) {
            document.body.removeChild(existingNotification);
        }

        // Yeni bildirim oluştur
        const notification = document.createElement('div');
        notification.className = 'copy-success';
        notification.textContent = message;
        document.body.appendChild(notification);

        // Bildirimi göster
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Bildirimi gizle ve kaldır
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Panoya kopyalama işlevi
    async function copyToClipboard(text, successMessage) {
        try {
            await navigator.clipboard.writeText(text);
            showCopySuccess(successMessage);
        } catch (err) {
            console.error('Kopyalama başarısız oldu:', err);
            alert('Kopyalama işlemi başarısız oldu. Lütfen manuel olarak kopyalayın.');
        }
    }

    // Widget oluştur butonuna tıklama olayı
    generateWidgetBtn.addEventListener('click', function() {
        const widgetUrl = generateWidgetUrl();
        updateWidgetPreview(widgetUrl);
    });

    // URL kopyalama butonu
    copyUrlBtn.addEventListener('click', function() {
        copyToClipboard(widgetUrlInput.value, 'URL panoya kopyalandı!');
    });

    // Gömme kodu kopyalama butonu
    copyEmbedBtn.addEventListener('click', function() {
        copyToClipboard(widgetEmbedCodeTextarea.value, 'Gömme kodu panoya kopyalandı!');
    });

    // Form alanları değiştiğinde otomatik önizleme güncelleme (isteğe bağlı)
    const formElements = [widgetTypeSelect, widgetThemeSelect, widgetAlbumArtSelect, widgetFontSizeSelect];
    formElements.forEach(element => {
        element.addEventListener('change', function() {
            const widgetUrl = generateWidgetUrl();
            updateWidgetPreview(widgetUrl);
        });
    });

    // Sayfa yüklendiğinde varsayılan widget'ı oluştur
    generateWidgetBtn.click();
});
