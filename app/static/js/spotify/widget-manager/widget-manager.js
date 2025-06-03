// widget-manager.js
document.addEventListener('DOMContentLoaded', function() {
    const generateTokenForm = document.getElementById('generateTokenForm');
    const widgetListContainer = document.getElementById('widgetList');
    const flashMessagesContainer = document.getElementById('flash-messages');
    
    // Sayfa yüklendiğinde mevcut widget token'ını kontrol et
    // Backend'den gelen widget_token değişkenini kontrol et (window._widgetToken)
    const existingWidgetToken = window._widgetToken || null;
    
    // Form gönderimi için event listener
    if (generateTokenForm) {
        generateTokenForm.addEventListener('submit', async function(event) {
            // AJAX ile dinamik token oluşturma ve sayfa yenilemeden güncelleme
            event.preventDefault();
            try {
                // Form verilerini FormData olarak gönder
                const formData = new FormData(generateTokenForm);
                
                const response = await fetch(generateTokenForm.action, {
                    method: 'POST',
                    body: formData
                    // FormData kullanırken Content-Type header'ı otomatik olarak ayarlanır
                });

                if (response.ok) {
                    const result = await response.json();
                    if (result.status === 'success') {
                        // Başarılı mesajı göster
                        showFlashMessage('success', result.message || 'Widget tokenı başarıyla oluşturuldu!');
                        // Widget listesini güncelle
                        fetchAndUpdateWidgetList();
                    } else {
                        showFlashMessage('error', result.message || 'Widget tokenı oluşturulamadı.');
                    }
                } else {
                    showFlashMessage('error', 'Token oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.');
                }
            } catch (error) {
                console.error('Token oluşturma hatası:', error);
                showFlashMessage('error', 'Beklenmedik bir hata oluştu.');
            }
        });
    }

    // Flash mesajları gösterme fonksiyonu (AJAX kullanılırsa)
    function showFlashMessage(category, message) {
        if (!flashMessagesContainer) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `p-4 rounded-md mb-3 ${category === 'success' ? 'bg-green-600' : 'bg-red-600'} text-white`;
        messageElement.textContent = message;
        
        flashMessagesContainer.appendChild(messageElement);
        
        // 5 saniye sonra mesajı kaldır
        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }

    // Widget listesini backend'den çekip güncelleme fonksiyonu (AJAX kullanılırsa)
    async function fetchAndUpdateWidgetList() {
        if (!widgetListContainer) return;
        
        try {
            // Mevcut token varsa ve sayfa ilk yüklendiğinde, doğrudan göster
            if (existingWidgetToken && widgetListContainer.querySelector('p.text-gray-400')) {
                // Mevcut token'ı kullanarak bir widget element'i oluştur
                const tokenData = {
                    value: existingWidgetToken,
                    username: 'current_user' // Backend'den alınabilir
                };
                updateWidgetListUI([tokenData]);
                return;
            }
            
            const response = await fetch('/spotify/widget-list');
            if (response.ok) {
                const widgets = await response.json();
                updateWidgetListUI(widgets);
            } else {
                console.error('Widget listesi alınamadı');
            }
        } catch (error) {
            console.error('Widget listesi çekilirken hata:', error);
        }
    }

    // Widget listesini UI'da güncelleme fonksiyonu (AJAX kullanılırsa)
    function updateWidgetListUI(widgets) {
        if (!widgetListContainer) return;
        
        // Mevcut içeriği temizle
        widgetListContainer.innerHTML = '';
        
        // Backend'den dönen yanıt bir dizi veya bir hata mesajı olabilir
        if (widgets && Array.isArray(widgets) && widgets.length > 0) {
            widgets.forEach(token => {
                const widgetElement = createWidgetElement(token);
                widgetListContainer.appendChild(widgetElement);
            });
        } else if (widgets && widgets.status === 'error') {
            // Hata durumunu göster
            const errorMessage = document.createElement('p');
            errorMessage.className = 'text-red-400';
            errorMessage.textContent = widgets.message || 'Widget listesi alınırken bir hata oluştu.';
            widgetListContainer.appendChild(errorMessage);
        } else {
            // Boş liste durumu
            const emptyMessage = document.createElement('p');
            emptyMessage.className = 'text-gray-400';
            emptyMessage.textContent = 'Henüz widget token\'ı oluşturmadınız.';
            widgetListContainer.appendChild(emptyMessage);
        }
    }

    // Widget elementi oluşturma fonksiyonu (AJAX kullanılırsa)
    function createWidgetElement(token) {
        const widgetDiv = document.createElement('div');
        widgetDiv.className = 'border border-gray-700 p-4 rounded-lg bg-gray-700/30';
        
        // Token bilgisi
        const tokenLabel = document.createElement('p');
        tokenLabel.className = 'text-gray-300 mb-1';
        tokenLabel.innerHTML = '<strong>Token:</strong>';
        
        const tokenCode = document.createElement('code');
        tokenCode.className = 'block bg-gray-900 p-2 rounded text-sm text-yellow-400 break-all mb-3';
        tokenCode.textContent = token.value;
        
        // Embed kodu
        const embedLabel = document.createElement('p');
        embedLabel.className = 'text-gray-300 mt-3 mb-1';
        embedLabel.innerHTML = '<strong>Embed Kodu (iframe):</strong>';
        
        const embedTextarea = document.createElement('textarea');
        embedTextarea.className = 'w-full h-28 bg-gray-900 text-gray-200 p-2 mt-1 border border-gray-600 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500';
        embedTextarea.readOnly = true;
        embedTextarea.value = `<iframe src="/spotify/widget/${token.value}" width="300" height="380" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>`;
        
        // Widget URL
        const urlLabel = document.createElement('p');
        urlLabel.className = 'text-gray-300 mt-3 mb-1';
        urlLabel.innerHTML = '<strong>Doğrudan Widget URL:</strong>';
        
        const urlInput = document.createElement('input');
        urlInput.type = 'text';
        urlInput.className = 'w-full bg-gray-900 text-gray-200 p-2 mt-1 border border-gray-600 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500';
        urlInput.readOnly = true;
        urlInput.value = `/spotify/widget/${token.value}`;
        
        // Önizleme başlığı
        const previewTitle = document.createElement('h4');
        previewTitle.className = 'text-lg font-semibold mt-4 mb-2 text-white';
        previewTitle.textContent = 'Önizleme:';
        
        // Önizleme container
        const previewContainer = document.createElement('div');
        previewContainer.className = 'border border-gray-600 rounded-md overflow-hidden w-[300px] h-[380px] mx-auto md:mx-0';
        
        // iframe
        const iframe = document.createElement('iframe');
        iframe.src = `/spotify/widget/${token.value}`;
        iframe.width = '300';
        iframe.height = '380';
        iframe.frameBorder = '0';
        iframe.scrolling = 'no';
        iframe.className = 'rounded-md';
        
        // Elementleri birleştir
        previewContainer.appendChild(iframe);
        widgetDiv.append(
            tokenLabel, tokenCode,
            embedLabel, embedTextarea,
            urlLabel, urlInput,
            previewTitle, previewContainer
        );
        
        return widgetDiv;
    }

    // Sayfa yüklenirken widget listesini otomatik olarak yükle
    fetchAndUpdateWidgetList();
    
    console.log('Widget Manager JS yüklendi.');
});
