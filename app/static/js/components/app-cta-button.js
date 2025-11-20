document.addEventListener('DOMContentLoaded', () => {
    // Güvenlik: PixelButton tanımlı mı kontrol et
    if (typeof PixelButton !== 'function') {
        console.warn('PixelButton sınıfı bulunamadı. app-cta-button efekti çalışmayacak.');
        return;
    }

    const ctaButtons = document.querySelectorAll('.app-cta-button');
    ctaButtons.forEach(button => {
        new PixelButton(button);
    });
});


