/**
 * Homepage specific JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Homepage script loaded');
    
    // Add any homepage-specific initialization here
    initHomepage();
});

/**
 * Initialize homepage-specific functionality
 */
function initHomepage() {
    // Example: Add a welcome animation or interaction
    const welcomeMessage = document.querySelector('.container h1');
    
    if (welcomeMessage) {
        // Add a subtle animation when hovering over the title
        welcomeMessage.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        welcomeMessage.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    }
}

/**
 * Example function for homepage-specific functionality
 * This could be expanded based on specific requirements
 */
function exampleHomepageFunction() {
    // Placeholder for future homepage-specific functionality
    console.log('Homepage function called');
}
