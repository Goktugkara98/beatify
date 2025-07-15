document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme');

    // Sayfa yüklendiğinde kaydedilmiş temayı uygula
    if (currentTheme === 'dark-theme') {
        document.body.classList.add('dark-theme');
    }

    // Tema değiştirme düğmesine tıklandığında
    themeToggleBtn.addEventListener('click', () => {
        // Tema geçişi için animasyon
        document.body.classList.toggle('dark-theme');

        // Temayı yerel depolamaya kaydet
        const isDarkTheme = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDarkTheme ? 'dark-theme' : 'light-theme');
    });

    // Navbar scroll efekti
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });
});
