/**
 * Navbar specific JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Navbar script loaded');
    
    // Initialize navbar functionality
    initNavbar();
});

/**
 * Initialize navbar-specific functionality
 */
function initNavbar() {
    // Mobile navigation toggle
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');
    
    if (navbarToggle && navbarMenu) {
        navbarToggle.addEventListener('click', function() {
            navbarMenu.classList.toggle('active');
            
            // Change toggle icon to X when menu is open
            const toggleIcon = this.querySelector('.toggle-icon');
            if (toggleIcon) {
                toggleIcon.classList.toggle('active');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInside = navbarToggle.contains(event.target) || 
                                 navbarMenu.contains(event.target);
            
            if (!isClickInside && navbarMenu.classList.contains('active')) {
                navbarMenu.classList.remove('active');
                const toggleIcon = navbarToggle.querySelector('.toggle-icon');
                if (toggleIcon) {
                    toggleIcon.classList.remove('active');
                }
            }
        });
    }
    
    // Search form functionality
    const searchForm = document.querySelector('.search-form');
    const searchInput = document.querySelector('.search-input');
    
    if (searchForm && searchInput) {
        // Expand search input on focus
        searchInput.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        searchInput.addEventListener('blur', function() {
            if (this.value === '') {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Handle search submission
        searchForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const searchTerm = searchInput.value.trim();
            if (searchTerm !== '') {
                console.log('Searching for:', searchTerm);
                // Here you would typically redirect to search results page
                // window.location.href = `/search?q=${encodeURIComponent(searchTerm)}`;
                
                // For now, just log the search term
                showSearchNotification(searchTerm);
            }
        });
    }
}

/**
 * Display a notification for search
 * @param {string} searchTerm - The search term
 */
function showSearchNotification(searchTerm) {
    // Check if the global notification function exists
    if (typeof showNotification === 'function') {
        showNotification(`Searching for: ${searchTerm}`, 'info');
    } else {
        // Fallback if global function is not available
        console.log(`Search initiated for: ${searchTerm}`);
    }
}
