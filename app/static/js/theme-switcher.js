document.addEventListener('DOMContentLoaded', () => {
    const htmlEl = document.documentElement;
    const dayButton = document.getElementById('day');
    const nightButton = document.getElementById('night');

    // Tema değiştirme fonksiyonu (artık çok daha basit)
    const setTheme = (theme) => {
        // 1. HTML elementine data-theme attribute'unu ata. CSS gerisini halleder.
        htmlEl.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // 2. Buton animasyonlarını ve tıklanabilirlik durumunu yönet.
        if (theme === 'dark') {
            // Gündüzden geceye geçiş animasyonu
            gsap.to("#sun", { duration: 1, x: -157, opacity: 0, ease: "power1.inOut" });
            gsap.to("#cloud", { duration: 0.5, opacity: 0, ease: "power1.inOut" });
            gsap.to("#moon", { duration: 1, x: -157, rotate: -360, transformOrigin: "center", opacity: 1, ease: "power1.inOut" });
            gsap.to(".star", { duration: 0.5, opacity: 1, ease: "power1.inOut" });
            
            // Butonların tıklanabilirlik durumunu ayarla
            dayButton.style.pointerEvents = 'none';
            nightButton.style.pointerEvents = 'auto';

        } else {
            // Geceden gündüze geçiş animasyonu
            gsap.to("#sun", { duration: 1, x: 15, opacity: 1, ease: "power1.inOut" });
            gsap.to("#cloud", { duration: 1, opacity: 1, ease: "power1.inOut" });
            gsap.to("#moon", { duration: 1, opacity: 0, x: 35, rotate: 360, transformOrigin: "center", ease: "power1.inOut" });
            gsap.to(".star", { duration: 1, opacity: 0, ease: "power1.inOut" });

            // Butonların tıklanabilirlik durumunu ayarla
            nightButton.style.pointerEvents = 'none';
            dayButton.style.pointerEvents = 'auto';
        }
    };

    // Sayfa yüklendiğinde başlangıç temasını ve buton durumunu ayarla (animasyonsuz)
    const initializeTheme = () => {
        const savedTheme = localStorage.getItem('theme') || 'light';
        htmlEl.setAttribute('data-theme', savedTheme);

        if (savedTheme === 'dark') {
            gsap.set("#sun, #cloud", { opacity: 0 });
            gsap.set("#moon, .star", { opacity: 1 });
            gsap.set("#moon", { x: -157 });
            gsap.set("#sun", { x: -157 });
            dayButton.style.pointerEvents = 'none';
            nightButton.style.pointerEvents = 'auto';
        } else {
            gsap.set("#moon, .star", { opacity: 0 });
            gsap.set("#sun, #cloud", { opacity: 1 });
            gsap.set("#sun, #cloud, #moon", { x: 15 });
            gsap.set(".star", { x: 35, y: -5 });
            nightButton.style.pointerEvents = 'none';
            dayButton.style.pointerEvents = 'auto';
        }
    };

    // Başlangıç temasını kur
    initializeTheme();

    // Tıklama olaylarını bağla
    if(dayButton) dayButton.addEventListener('click', () => setTheme('dark'));
    if(nightButton) nightButton.addEventListener('click', () => setTheme('light'));
});