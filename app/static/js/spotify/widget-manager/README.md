# Modüler Widget Yapısı

Bu belge, Spotify widget'ları için oluşturulan modüler yapıyı açıklamaktadır. Bu yapı, farklı widget tiplerinin ortak ve özel bileşenlerini sistemli bir şekilde ayırarak sürdürülebilir ve ölçeklenebilir hale getirmeyi amaçlamaktadır.

## İçindekiler

1. [Genel Yapı](#genel-yapı)
2. [Ortak Dosyalar](#ortak-dosyalar)
3. [Widget Özgü Dosyalar](#widget-özgü-dosyalar)
4. [Yeni Widget Oluşturma](#yeni-widget-oluşturma)
5. [Örnek Kullanım](#örnek-kullanım)

## Genel Yapı

Widget sistemi aşağıdaki bileşenlerden oluşmaktadır:

- **Ortak JavaScript (common.js)**: Tüm widget'lar tarafından kullanılan ortak fonksiyonlar
- **Ortak CSS (common.css)**: Tüm widget'lar için geçerli temel stil kuralları
- **Widget Özgü HTML**: Her widget için özel HTML yapısı
- **Widget Özgü JavaScript**: Her widget için özel JavaScript kodu
- **Widget Özgü CSS**: Her widget için özel stil tanımlamaları

## Ortak Dosyalar

### common.js

Bu dosya, tüm widget'lar tarafından kullanılan ortak fonksiyonları içerir:

1. **Backend İletişim Fonksiyonları**
   - `fetchWidgetData`: Backend'den widget verilerini çeker

2. **Animasyon Tetikleyicileri**
   - `playIntroAnimation`: Sayfa açılışında animasyon tetikler
   - `playSongTransitionAnimation`: Şarkı değişiminde animasyon tetikler
   - `playOutroAnimation`: Sayfa kapatılırken animasyon tetikler

3. **Progress Bar Hesaplama ve Kontrol**
   - `updateProgressBar`: Progress bar'ı günceller

4. **Yardımcı Fonksiyonlar**
   - `msToTimeFormat`: Milisaniyeyi "dakika:saniye" formatına çevirir
   - `updateTextContent`: DOM elementinin metin içeriğini günceller
   - `updateImageSource`: Resim elementinin src'sini günceller
   - `showError`: Hata mesajı gösterir
   - `hideError`: Hata mesajını gizler

### common.css

Bu dosya, tüm widget'lar için geçerli temel stil kurallarını içerir:

1. **Temel Sayfa Düzeni**
   - Sayfa arka planının şeffaf olması
   - Temel font ve boyut tanımlamaları

2. **Widget Konumlandırma**
   - Widget'ın sayfanın tam ortasında konumlandırılması

3. **Animasyon Tanımlamaları**
   - Fade In, Fade Out, Slide In gibi temel animasyonlar

4. **Yardımcı Sınıflar**
   - Progress bar temel stili
   - Zaman gösterimi
   - Hata mesajı

## Widget Özgü Dosyalar

Her widget için aşağıdaki dosyalar oluşturulmalıdır:

### HTML Dosyası

- Ortak CSS ve JS dosyalarını import eder
- Widget'a özel CSS ve JS dosyalarını import eder
- Widget'ın HTML yapısını tanımlar

### JavaScript Dosyası

- DOM elementlerini seçer
- UI güncelleme fonksiyonlarını içerir
- Veri çekme ve işleme fonksiyonlarını içerir
- Özel animasyonları tanımlar
- Widget'ı başlatır

### CSS Dosyası

- Widget özgü düzen tanımlar
- Özel animasyonları tanımlar
- Renk şeması ve görsel efektleri tanımlar

## Yeni Widget Oluşturma

Yeni bir widget oluşturmak için aşağıdaki adımları izleyin:

1. HTML dosyası oluşturun:
   - `app/templates/spotify/widgets/widget_[TEMA_ADI].html`
   - Ortak CSS ve JS dosyalarını import edin
   - Widget'a özel CSS ve JS dosyalarını import edin

2. JavaScript dosyası oluşturun:
   - `app/static/js/spotify/widget-manager/widgets/widget_[TEMA_ADI].js`
   - WidgetCommon modülünü kullanarak UI'ı yönetin

3. CSS dosyası oluşturun:
   - `app/static/css/spotify/widget-manager/widgets/widget_[TEMA_ADI].css`
   - Widget'a özel stilleri tanımlayın

## Örnek Kullanım

### HTML Dosyası

```html
<!DOCTYPE html>
<html lang="tr">
<head>
    <!-- Meta ve başlık -->
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotify Widget - [TEMA_ADI]</title>
    
    <!-- Ortak CSS -->
    <link rel="stylesheet" href="/static/css/spotify/widget-manager/common.css">
    
    <!-- Widget'a özel CSS -->
    <link rel="stylesheet" href="/static/css/spotify/widget-manager/widgets/widget_[TEMA_ADI].css">
</head>
<body>
    <div id="spotifyWidget" class="widget-container">
        <!-- Widget içeriği -->
    </div>

    <script>
        // WIDGET_TOKEN'ı modüllerin alabilmesi için global scope'a tanımla
        window.WIDGET_TOKEN_FROM_HTML = "{{ config.widgetToken|safe }}";
        window.DATA_ENDPOINT_TEMPLATE = '/spotify/api/widget-data/{TOKEN}';
    </script>
    
    <!-- Ortak JS dosyası -->
    <script src="/static/js/spotify/widget-manager/common.js"></script>
    
    <!-- Widget'a özel JS -->
    <script src="/static/js/spotify/widget-manager/widgets/widget_[TEMA_ADI].js"></script>
</body>
</html>
```

### JavaScript Dosyası

```javascript
document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    // WidgetCommon'ın yüklenmiş olduğundan emin ol
    if (typeof WidgetCommon === 'undefined') {
        console.error('[TEMA_ADI] Widget: WidgetCommon bulunamadı!');
        return;
    }

    // DOM Elementleri
    const spotifyWidgetElement = document.getElementById('spotifyWidget');
    const albumArtElement = document.getElementById('albumArt');
    // Diğer elementler...

    // Veriyi çek ve göster
    async function fetchAndDisplayData() {
        const token = window.WIDGET_TOKEN_FROM_HTML;
        const endpoint = window.DATA_ENDPOINT_TEMPLATE;
        
        const data = await WidgetCommon.fetchWidgetData(token, endpoint);
        
        // Veriyi işle ve UI'ı güncelle
        updateWidgetUI(data);
    }

    // Widget'ı başlat
    function initWidget() {
        // Sayfa açılış animasyonu
        WidgetCommon.playIntroAnimation(overlayContentElement);
        
        // Veriyi çek ve göster
        fetchAndDisplayData();
    }

    // Widget'ı başlat
    initWidget();
});
```

Bu modüler yapı, widget'ların daha kolay yönetilmesini ve yeni widget'ların hızlı bir şekilde oluşturulmasını sağlar.
