document.addEventListener('DOMContentLoaded', () => {
    const htmlEl = document.documentElement;

    // GSAP animasyonlarını ve tema durumunu yöneten merkezi fonksiyon
    const setTheme = (theme) => {
        // Temayı ve localStorage'ı güncelle
        htmlEl.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Animasyonları ve buton durumlarını ayarla
        if (theme === 'dark') {
            // Gündüzden geceye geçiş animasyonu
            gsap.to("#sun", 1, { x: -157, opacity: 0, ease: Power1.easeInOut });
            gsap.to("#cloud", 0.5, { opacity: 0, ease: Power1.easeInOut });
            gsap.to("#moon", 1, { x: -157, rotate: -360, transformOrigin: "center", opacity: 1, ease: Power1.easeInOut });
            gsap.to(".star", 0.5, { opacity: 1, ease: Power1.easeInOut });
            gsap.to("#night", 1, { background: "#224f6d", borderColor: "#cad4d8", ease: Power1.easeInOut });
            gsap.to("#background", 1, { background: "#0d1f2b", ease: Power1.easeInOut });
            
            $("#day").css({ "pointer-events": "none" });
            setTimeout(() => $("#night").css({ "pointer-events": "all" }), 1000);
        } else {
            // Geceden gündüze geçiş animasyonu
            gsap.to("#sun", 1, { x: 15, opacity: 1, ease: Power1.easeInOut });
            gsap.to("#cloud", 1, { opacity: 1, ease: Power1.easeInOut });
            gsap.to("#moon", 1, { opacity: 0, x: 35, rotate: 360, transformOrigin: "center", ease: Power1.easeInOut });
            gsap.to(".star", 1, { opacity: 0, ease: Power1.easeInOut });
            gsap.to("#night", 1, { background: "#9cd6ef", borderColor: "#65c0e7", ease: Power1.easeInOut });
            gsap.to("#background", 1, { background: "#d3edf8", ease: Power1.easeInOut });

            $("#night").css({ "pointer-events": "none" });
            setTimeout(() => $("#day").css({ "pointer-events": "all" }), 1000);
        }
    };

    // Sayfa yüklendiğinde temayı ayarla
    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlEl.setAttribute('data-theme', savedTheme);

    // GSAP başlangıç durumlarını ayarla (animasyonsuz)
    if (savedTheme === 'dark') {
        gsap.set("#sun, #cloud", { opacity: 0 });
        gsap.set("#moon, .star", { opacity: 1 });
        gsap.set("#moon", { x: -157 });
        gsap.set("#sun", { x: -157 });
        gsap.set("#night", { background: "#224f6d", borderColor: "#cad4d8" });
        gsap.set("#background", { background: "#0d1f2b" });
        $("#day").css({ "pointer-events": "none" });
        $("#night").css({ "pointer-events": "all" });
    } else {
        gsap.set("#moon, .star", { opacity: 0 });
        gsap.set("#sun, #cloud", { opacity: 1 });
        gsap.set("#sun, #cloud, #moon", { x: 15 });
        gsap.set(".star", { x: 35, y: -5 });
        $("#night").css({ "pointer-events": "none" });
        $("#day").css({ "pointer-events": "all" });
    }

    // Tıklama olayları
    $("#day").on('click', () => setTheme('dark'));
    $("#night").on('click', () => setTheme('light'));
});
