/**
 * =============================================================================
 * Navbar Script Modülü (navbar.js)
 * =============================================================================
 * Bu dosya, navbar için basit scroll efektini uygular.
 *
 * İÇİNDEKİLER:
 * -----------------------------------------------------------------------------
 * 1.0  DOM HAZIRLIK (DOM READY)
 *      1.1. DOMContentLoaded handler
 *
 * 2.0  FONKSİYONLAR (FUNCTIONS)
 *      2.1. initNavbarScrollEffect()
 * =============================================================================
 */

/**
 * Navbar scroll effect'i başlatır.
 */
function initNavbarScrollEffect() {
  const navbar = document.querySelector(".navbar");
  if (!navbar) return;

  window.addEventListener("scroll", () => {
    if (window.scrollY > 50) {
      navbar.classList.add("navbar-scrolled");
    } else {
      navbar.classList.remove("navbar-scrolled");
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initNavbarScrollEffect();
});
