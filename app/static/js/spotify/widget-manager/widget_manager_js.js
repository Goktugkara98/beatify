
/* ===== WIDGET MANAGER JAVASCRIPT ===== */
/*
 * Table of Contents:
 * 1. Initialization and Event Listeners
 * 2. Widget Type Selection
 *    2.1 Widget Card Click Event
 *    2.2 Widget Type Navigation
 *        2.2.1 Navigation Buttons (Prev/Next)
 *        2.2.2 Navigation Dots
 * 3. Widget Preview Functions
 *    3.1 Update Widget Preview
 *    3.2 Create Now Playing Preview
 *    3.3 Create Recently Played Preview
 *    3.4 Create Top Tracks Preview
 * 4. Customization Functions
 *    4.1 Tab Initialization
 *    4.2 Form Controls Initialization
 *        4.2.1 Size Selector
 *        4.2.2 Slider Controls
 *        4.2.3 Color Pickers
 *        4.2.4 Toggle Switches
 *        4.2.5 Font Selector
 *        4.2.6 Visibility Options
 *    4.3 Apply Customization Settings
 * 5. Device Switcher
 * 6. Embed Code Modal
 *    6.1 Action Buttons (Refresh, Theme, Embed)
 *    6.2 Theme Toggle
 *    6.3 Modal Initialization
 *    6.4 Modal Open/Close
 *    6.5 Copy Embed Code
 *    6.6 Update Embed Code
 * 7. Utility Functions
 *    7.1 Hex to RGBA Conversion
 *    7.2 RGB to Hex Conversion
 *    7.3 Color Lightening
 *    7.4 Debounce Function
 * 8. DOM Ready Widget Selection (Initial Code Snippet - moved to end for clarity)
 */

// ===== 1. INITIALIZATION AND EVENT LISTENERS =====
document.addEventListener('DOMContentLoaded', function() {
    initializeWidgetManager();
});

function initializeWidgetManager() {
    // Initialize widget type selection
    initWidgetTypeSelection();

    // Initialize tabs for customization options
    initTabs();

    // Initialize device switcher for preview
    initDeviceSwitcher();

    // Initialize action buttons in customization area
    initActionButtons();

    // Initialize embed code modal functionality
    initEmbedCodeModal();

    // Initialize form controls for widget customization
    initFormControls();

    // Load initial widget preview after setup
    updateWidgetPreview();
}


// ===== 2. WIDGET TYPE SELECTION =====

// 2.1 Widget Card Click Event
function initWidgetTypeSelection() {
    const widgetTypeCards = document.querySelectorAll('.widget-type-card:not(.coming-soon)');

    widgetTypeCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remove 'selected' class from all widget type cards
            widgetTypeCards.forEach(c => c.classList.remove('selected'));

            // Add 'selected' class to the clicked widget type card
            this.classList.add('selected');

            // Get the data-widget-type attribute from the selected card
            const widgetType = this.getAttribute('data-widget-type');

            // Update the widget preview based on the selected type and customizations
            updateWidgetPreview();
        });
    });

    // Initialize widget type navigation (prev/next buttons, dots)
    initWidgetTypeNavigation();
}


// 2.2 Widget Type Navigation
function initWidgetTypeNavigation() {
    const container = document.querySelector('.widget-types-container');
    const prevBtn = document.querySelector('.nav-btn.prev');
    const nextBtn = document.querySelector('.nav-btn.next');

    if (prevBtn && nextBtn) {
        // 2.2.1 Navigation Buttons (Prev/Next)
        prevBtn.addEventListener('click', () => {
            container.scrollBy({ left: -250, behavior: 'smooth' });
        });

        nextBtn.addEventListener('click', () => {
            container.scrollBy({ left: 250, behavior: 'smooth' });
        });

        // Update navigation button states based on scroll position
        container.addEventListener('scroll', updateNavButtons);

        // Initial button state update
        updateNavButtons();
    }

    // 2.2.2 Navigation Dots
    initNavDots();
}

function updateNavButtons() {
    const container = document.querySelector('.widget-types-container');
    const prevBtn = document.querySelector('.nav-btn.prev');
    const nextBtn = document.querySelector('.nav-btn.next');

    if (container && prevBtn && nextBtn) {
        // Disable 'prev' button if scrolled to the start
        prevBtn.disabled = container.scrollLeft <= 10;

        // Check if there is more content to scroll to the right
        const canScrollRight = container.scrollWidth > container.clientWidth + container.scrollLeft;
        // Disable 'next' button if scrolled to the end
        nextBtn.disabled = !canScrollRight;

        // Add pulse animation to 'next' button if scrollable and at the beginning
        if (canScrollRight && container.scrollLeft === 0) {
            nextBtn.classList.add('pulse-hint');
        } else {
            nextBtn.classList.remove('pulse-hint');
        }
    }
}

function initNavDots() {
    const dots = document.querySelectorAll('.nav-dot');
    const container = document.querySelector('.widget-types-container');

    if (dots.length > 0 && container) {
        dots.forEach((dot, index) => {
            dot.addEventListener('click', () => {
                // Calculate scroll position based on dot index
                const scrollWidth = container.scrollWidth;
                const clientWidth = container.clientWidth;
                const scrollableWidth = scrollWidth - clientWidth;
                const scrollPosition = (scrollableWidth / (dots.length - 1)) * index;

                container.scrollTo({ left: scrollPosition, behavior: 'smooth' });

                // Update active dot indicator
                dots.forEach(d => d.classList.remove('active'));
                dot.classList.add('active');
            });
        });

        // Update active dot based on scroll position
        container.addEventListener('scroll', () => {
            const scrollWidth = container.scrollWidth;
            const clientWidth = container.clientWidth;
            const scrollableWidth = scrollWidth - clientWidth;
            const scrollPosition = container.scrollLeft;

            // Determine the index of the active dot based on scroll position
            const activeDotIndex = Math.round((scrollPosition / scrollableWidth) * (dots.length - 1));

            dots.forEach((dot, index) => {
                dot.classList.toggle('active', index === activeDotIndex);
            });
        });
    }
}


// ===== 3. WIDGET PREVIEW FUNCTIONS =====

// 3.1 Update Widget Preview
function updateWidgetPreview() {
    const widgetPreview = document.getElementById('widget-preview');
    if (!widgetPreview) return;

    // Get the currently selected widget type card
    const selectedCard = document.querySelector('.widget-type-card.selected');
    if (!selectedCard) return;

    const widgetType = selectedCard.getAttribute('data-widget-type');

    // Clear the previous widget preview content
    widgetPreview.innerHTML = '';

    // Create preview content based on the selected widget type
    if (widgetType === 'now-playing') {
        // 3.2 Create Now Playing Preview
        createNowPlayingPreview(widgetPreview);
    } else if (widgetType === 'recently-played') {
        // 3.3 Create Recently Played Preview
        createRecentlyPlayedPreview(widgetPreview);
    } else if (widgetType === 'top-tracks') {
        // 3.4 Create Top Tracks Preview
        createTopTracksPreview(widgetPreview);
    }

    // Apply customization settings to the preview
    applyCustomizationSettings();
}

// 3.2 Create Now Playing Preview
function createNowPlayingPreview(container) {
    // HTML structure for Now Playing widget preview
    const widgetHTML = `
        <div class="widget-now-playing">
            <div class="widget-album-art">
                <img src="https://via.placeholder.com/60" alt="Album Art">
            </div>
            <div class="widget-track-info">
                <div class="widget-track-name">Bohemian Rhapsody</div>
                <div class="widget-artist-name">Queen</div>
            </div>
            <div class="widget-progress">
                <div class="widget-progress-bar"></div>
            </div>
        </div>
    `;

    container.innerHTML = widgetHTML;
}

// 3.3 Create Recently Played Preview
function createRecentlyPlayedPreview(container) {
    // HTML structure for Recently Played widget preview
    const widgetHTML = `
        <div class="widget-recently-played">
            <div class="widget-header">Recently Played</div>
            <div class="widget-track-list">
                <div class="widget-track-item">
                    <div class="widget-track-number">1</div>
                    <div class="widget-track-art">
                        <img src="https://via.placeholder.com/40" alt="Album Art">
                    </div>
                    <div class="widget-track-info">
                        <div class="widget-track-name">Shape of You</div>
                        <div class="widget-artist-name">Ed Sheeran</div>
                    </div>
                </div>
                <div class="widget-track-item">
                    <div class="widget-track-number">2</div>
                    <div class="widget-track-art">
                        <img src="https://via.placeholder.com/40" alt="Album Art">
                    </div>
                    <div class="widget-track-info">
                        <div class="widget-track-name">Blinding Lights</div>
                        <div class="widget-artist-name">The Weeknd</div>
                    </div>
                </div>
                <div class="widget-track-item">
                    <div class="widget-track-number">3</div>
                    <div class="widget-track-art">
                        <img src="https://via.placeholder.com/40" alt="Album Art">
                    </div>
                    <div class="widget-track-info">
                        <div class="widget-track-name">Dance Monkey</div>
                        <div class="widget-artist-name">Tones and I</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = widgetHTML;
}

// 3.4 Create Top Tracks Preview
function createTopTracksPreview(container) {
    // HTML structure for Top Tracks widget preview
    const widgetHTML = `
        <div class="widget-top-tracks">
            <div class="widget-header">Your Top Tracks</div>
            <div class="widget-track-list">
                <div class="widget-track-item">
                    <div class="widget-track-number">1</div>
                    <div class="widget-track-art">
                        <img src="https://via.placeholder.com/40" alt="Album Art">
                    </div>
                    <div class="widget-track-info">
                        <div class="widget-track-name">Bad Guy</div>
                        <div class="widget-artist-name">Billie Eilish</div>
                    </div>
                </div>
                <div class="widget-track-item">
                    <div class="widget-track-number">2</div>
                    <div class="widget-track-art">
                        <img src="https://via.placeholder.com/40" alt="Album Art">
                    </div>
                    <div class="widget-track-info">
                        <div class="widget-track-name">Uptown Funk</div>
                        <div class="widget-artist-name">Mark Ronson ft. Bruno Mars</div>
                    </div>
                </div>
                <div class="widget-track-item">
                    <div class="widget-track-number">3</div>
                    <div class="widget-track-art">
                        <img src="https://via.placeholder.com/40" alt="Album Art">
                    </div>
                    <div class="widget-track-info">
                        <div class="widget-track-name">Someone You Loved</div>
                        <div class="widget-artist-name">Lewis Capaldi</div>
                    </div>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = widgetHTML;
}


// ===== 4. CUSTOMIZATION FUNCTIONS =====

// 4.1 Tab Initialization
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Deactivate all tabs and content
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Activate the clicked tab and its corresponding content
            button.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });
}


// 4.2 Form Controls Initialization
function initFormControls() {
    // 4.2.1 Size Selector
    initSizeSelector();

    // 4.2.2 Slider Controls
    initSliders();

    // 4.2.3 Color Pickers
    initColorPickers();

    // 4.2.4 Toggle Switches
    initToggleSwitches();

    // 4.2.5 Font Selector
    initFontSelector();

    // 4.2.6 Visibility Options
    initVisibilityOptions();
}

// 4.2.1 Size Selector
function initSizeSelector() {
    const sizeOptions = document.querySelectorAll('.size-option');
    const customSizeRow = document.querySelector('.custom-size-row');
    const widthInput = document.getElementById('width-input');
    const heightInput = document.getElementById('height-input');

    if (sizeOptions.length > 0) {
        sizeOptions.forEach(option => {
            option.addEventListener('click', () => {
                // Deactivate all size options
                sizeOptions.forEach(opt => opt.classList.remove('active'));

                // Activate the clicked size option
                option.classList.add('active');

                // Show custom size inputs if 'custom' size is selected
                if (option.getAttribute('data-size') === 'custom') {
                    customSizeRow.style.display = 'block';
                } else {
                    customSizeRow.style.display = 'none';

                    // Set predefined widget sizes
                    let width, height;
                    const size = option.getAttribute('data-size');

                    if (size === 'small') {
                        width = 250;
                        height = 100;
                    } else if (size === 'medium') {
                        width = 300;
                        height = 150;
                    } else if (size === 'large') {
                        width = 400;
                        height = 200;
                    }

                    // Update widget preview size
                    updateWidgetSize(width, height);
                }

                // Refresh widget preview to apply size changes
                updateWidgetPreview();
            });
        });

        // Event listeners for custom width and height inputs
        if (widthInput && heightInput) {
            widthInput.addEventListener('input', debounce(() => {
                updateWidgetSize(widthInput.value, heightInput.value);
            }, 300));

            heightInput.addEventListener('input', debounce(() => {
                updateWidgetSize(widthInput.value, heightInput.value);
            }, 300));
        }
    }
}

function updateWidgetSize(width, height) {
    const widgetPreview = document.getElementById('widget-preview');
    if (widgetPreview) {
        widgetPreview.style.width = `${width}px`;
        widgetPreview.style.height = `${height}px`;
    }
}

// 4.2.2 Slider Controls
function initSliders() {
    const sliders = document.querySelectorAll('.slider');

    sliders.forEach(slider => {
        const valueDisplay = slider.parentElement.querySelector('.slider-value');

        // Initialize slider value display
        if (valueDisplay) {
            valueDisplay.textContent = `${slider.value}px`;
        }

        // Update slider value display and apply customization on input change
        slider.addEventListener('input', () => {
            if (valueDisplay) {
                valueDisplay.textContent = `${slider.value}px`;
            }

            // Apply customization settings to preview
            applyCustomizationSettings();
        });
    });
}

// 4.2.3 Color Pickers
function initColorPickers() {
    const colorInputs = document.querySelectorAll('.color-input');

    colorInputs.forEach(input => {
        const colorPreview = input.parentElement;

        // Set initial color preview based on input value
        colorPreview.style.backgroundColor = input.value;

        // Update color preview and apply customization on input change
        input.addEventListener('input', () => {
            colorPreview.style.backgroundColor = input.value;

            // If background color is changed, update opacity as well
            if (input.id === 'background-color') {
                updateBackgroundOpacity();
            } else {
                // Apply customization settings to preview
                applyCustomizationSettings();
            }
        });
    });

    // Initialize background opacity slider
    const opacitySlider = document.getElementById('background-opacity');
    if (opacitySlider) {
        opacitySlider.addEventListener('input', updateBackgroundOpacity);
    }
}

function updateBackgroundOpacity() {
    const opacitySlider = document.getElementById('background-opacity');
    const colorInput = document.getElementById('background-color');
    const colorPreview = colorInput.parentElement;

    if (opacitySlider && colorInput) {
        const opacity = opacitySlider.value / 100;
        const color = colorInput.value;

        // Update color preview with new opacity
        colorPreview.style.backgroundColor = hexToRgba(color, opacity);

        // Apply customization settings to preview
        applyCustomizationSettings();
    }
}

// 4.2.4 Toggle Switches
function initToggleSwitches() {
    const toggles = document.querySelectorAll('.toggle-switch input');

    toggles.forEach(toggle => {
        toggle.addEventListener('change', () => {
            // Apply customization settings to preview on toggle change
            applyCustomizationSettings();
        });
    });
}

// 4.2.5 Font Selector
function initFontSelector() {
    const fontSelector = document.getElementById('font-family');

    if (fontSelector) {
        fontSelector.addEventListener('change', () => {
            // Apply customization settings to preview on font change
            applyCustomizationSettings();
        });
    }
}

// 4.2.6 Visibility Options
function initVisibilityOptions() {
    const visibilityToggles = document.querySelectorAll('.visibility-option input');

    visibilityToggles.forEach(toggle => {
        toggle.addEventListener('change', () => {
            // Apply customization settings to preview on visibility option change
            applyCustomizationSettings();
        });
    });
}


// 4.3 Apply Customization Settings
function applyCustomizationSettings() {
    const widgetPreview = document.getElementById('widget-preview');
    if (!widgetPreview) return;

    // Retrieve customization values from form elements
    const bgColor = document.getElementById('background-color')?.value || '#121212';
    const bgOpacity = document.getElementById('background-opacity')?.value || 100;
    const textColor = document.getElementById('text-color')?.value || '#FFFFFF';
    const accentColor = document.getElementById('accent-color')?.value || '#1DB954';
    const borderRadius = document.getElementById('border-radius')?.value || 12;
    const fontFamily = document.getElementById('font-family')?.value || 'Montserrat';
    const enableShadow = document.getElementById('enable-shadow')?.checked || false;
    const enableBorder = document.getElementById('enable-border')?.checked || false;
    const borderColor = document.getElementById('border-color')?.value || '#FFFFFF';
    const borderWidth = document.getElementById('border-width')?.value || 1;

    // Apply background color with opacity
    widgetPreview.style.backgroundColor = hexToRgba(bgColor, bgOpacity / 100);

    // Apply border radius
    widgetPreview.style.borderRadius = `${borderRadius}px`;

    // Apply font family
    widgetPreview.style.fontFamily = fontFamily;

    // Apply text color to relevant elements
    const textElements = widgetPreview.querySelectorAll('.widget-track-name, .widget-artist-name, .widget-header');
    textElements.forEach(element => {
        element.style.color = textColor;
    });

    // Apply accent color to accent elements (e.g., progress bar)
    const accentElements = widgetPreview.querySelectorAll('.widget-progress-bar');
    accentElements.forEach(element => {
        element.style.backgroundColor = accentColor;
    });

    // Toggle shadow based on 'enableShadow'
    widgetPreview.style.boxShadow = enableShadow ? '0 8px 16px rgba(0, 0, 0, 0.3)' : 'none';

    // Toggle border based on 'enableBorder' and set border properties
    widgetPreview.style.border = enableBorder ? `${borderWidth}px solid ${borderColor}` : 'none';

    // Visibility options - retrieve visibility states
    const showAlbumArt = document.getElementById('show-album-art')?.checked ?? true;
    const showTrackName = document.getElementById('show-track-name')?.checked ?? true;
    const showArtistName = document.getElementById('show-artist-name')?.checked ?? true;
    const showProgress = document.getElementById('show-progress')?.checked ?? true;

    // Apply visibility settings to corresponding elements
    const albumArtElements = widgetPreview.querySelectorAll('.widget-album-art, .widget-track-art');
    albumArtElements.forEach(element => {
        element.style.display = showAlbumArt ? 'block' : 'none';
    });

    const trackNameElements = widgetPreview.querySelectorAll('.widget-track-name');
    trackNameElements.forEach(element => {
        element.style.display = showTrackName ? 'block' : 'none';
    });

    const artistNameElements = widgetPreview.querySelectorAll('.widget-artist-name');
    artistNameElements.forEach(element => {
        element.style.display = showArtistName ? 'block' : 'none';
    });

    const progressElements = widgetPreview.querySelectorAll('.widget-progress');
    progressElements.forEach(element => {
        element.style.display = showProgress ? 'block' : 'none';
    });
}


// ===== 5. DEVICE SWITCHER =====
function initDeviceSwitcher() {
    const deviceButtons = document.querySelectorAll('.device-button');
    const deviceFrame = document.querySelector('.device-frame');
    const widgetPreview = document.getElementById('widget-preview');

    if (deviceButtons.length > 0 && deviceFrame && widgetPreview) {
        deviceButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Deactivate all device buttons
                deviceButtons.forEach(btn => btn.classList.remove('active'));

                // Activate the clicked device button
                button.classList.add('active');

                // Get the device type from data attribute
                const deviceType = button.getAttribute('data-device');

                // Apply device-specific styles to the preview frame
                if (deviceType === 'desktop') {
                    deviceFrame.style.width = '100%';
                    deviceFrame.style.maxWidth = '500px';
                    deviceFrame.style.padding = '0';
                    deviceFrame.style.borderRadius = '0';
                    deviceFrame.style.border = 'none';
                } else if (deviceType === 'tablet') {
                    deviceFrame.style.width = '100%';
                    deviceFrame.style.maxWidth = '400px';
                    deviceFrame.style.padding = '20px 10px';
                    deviceFrame.style.borderRadius = '20px';
                    deviceFrame.style.border = '10px solid #333';
                } else if (deviceType === 'mobile') {
                    deviceFrame.style.width = '100%';
                    deviceFrame.style.maxWidth = '280px';
                    deviceFrame.style.padding = '20px 10px';
                    deviceFrame.style.borderRadius = '20px';
                    deviceFrame.style.border = '10px solid #333';
                }
            });
        });
    }
}


// ===== 6. EMBED CODE MODAL =====

// 6.1 Action Buttons (Refresh, Theme, Embed)
function initActionButtons() {
    const refreshPreviewBtn = document.getElementById('refresh-preview');
    const toggleThemeBtn = document.getElementById('toggle-theme');
    const getEmbedCodeBtn = document.getElementById('get-embed-code');

    if (refreshPreviewBtn) {
        refreshPreviewBtn.addEventListener('click', () => {
            updateWidgetPreview();
        });
    }

    if (toggleThemeBtn) {
        toggleThemeBtn.addEventListener('click', togglePreviewTheme);
    }

    if (getEmbedCodeBtn) {
        getEmbedCodeBtn.addEventListener('click', openEmbedCodeModal);
    }
}

// 6.2 Theme Toggle
function togglePreviewTheme() {
    const previewArea = document.querySelector('.preview-area');
    const themeIcon = document.querySelector('#toggle-theme i');

    if (previewArea && themeIcon) {
        const isDarkTheme = previewArea.classList.contains('dark-theme') || !previewArea.classList.contains('light-theme');

        if (isDarkTheme) {
            // Switch to light theme
            previewArea.classList.remove('dark-theme');
            previewArea.classList.add('light-theme');
            previewArea.style.backgroundColor = '#f5f5f5';
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        } else {
            // Switch to dark theme
            previewArea.classList.remove('light-theme');
            previewArea.classList.add('dark-theme');
            previewArea.style.backgroundColor = 'rgba(10, 10, 10, 0.3)';
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        }
    }
}

// 6.3 Modal Initialization
function initEmbedCodeModal() {
    const modal = document.getElementById('embed-modal');
    const closeBtn = modal?.querySelector('.modal-close');
    const copyBtn = modal?.querySelector('.copy-button');

    if (closeBtn) {
        closeBtn.addEventListener('click', closeEmbedCodeModal);
    }

    if (copyBtn) {
        copyBtn.addEventListener('click', copyEmbedCode);
    }

    // Close modal when clicking outside of it
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeEmbedCodeModal();
            }
        });
    }
}

// 6.4 Modal Open/Close
function openEmbedCodeModal() {
    const modal = document.getElementById('embed-modal');

    if (modal) {
        // Update embed code content before opening
        updateEmbedCode();

        // Show the embed code modal
        modal.classList.add('active');
    }
}

function closeEmbedCodeModal() {
    const modal = document.getElementById('embed-modal');

    if (modal) {
        // Hide the embed code modal
        modal.classList.remove('active');
    }
}

// 6.5 Copy Embed Code
function copyEmbedCode() {
    const codeContent = document.querySelector('.code-content');
    const copyButton = document.querySelector('.copy-button');

    if (codeContent && copyButton) {
        // Create a temporary textarea to copy the code to clipboard
        const textarea = document.createElement('textarea');
        textarea.value = codeContent.textContent;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);

        // Provide visual feedback that code has been copied
        const originalIcon = copyButton.innerHTML;
        copyButton.innerHTML = '<i class="fas fa-check"></i>';

        // Revert back to the original icon after 2 seconds
        setTimeout(() => {
            copyButton.innerHTML = originalIcon;
        }, 2000);
    }
}

// 6.6 Update Embed Code
function updateEmbedCode() {
    const codeContent = document.querySelector('.code-content');
    if (!codeContent) return;

    // Retrieve widget settings to generate embed code
    const widgetType = document.querySelector('.widget-type-card.selected').getAttribute('data-widget-type');
    const bgColor = document.getElementById('background-color').value;
    const bgOpacity = document.getElementById('background-opacity').value;
    const textColor = document.getElementById('text-color').value;
    const accentColor = document.getElementById('accent-color').value;
    const borderRadius = document.getElementById('border-radius').value;
    const font = document.getElementById('font-family').value;
    const shadowEnabled = document.getElementById('enable-shadow').checked;
    const borderEnabled = document.getElementById('enable-border').checked;

    // Determine widget size based on selected option
    let width, height;
    const activeSize = document.querySelector('.size-option.active').getAttribute('data-size');

    if (activeSize === 'custom') {
        width = document.getElementById('width-input').value;
        height = document.getElementById('height-input').value;
    } else if (activeSize === 'small') {
        width = 250;
        height = 100;
    } else if (activeSize === 'medium') {
        width = 300;
        height = 150;
    } else if (activeSize === 'large') {
        width = 400;
        height = 200;
    }

    // Construct the iframe embed code with current widget settings
    const embedCode = `<iframe
    src="https://beatify.example.com/widget/${widgetType}?bg=${bgColor.substring(1)}&opacity=${bgOpacity}&text=${textColor.substring(1)}&accent=${accentColor.substring(1)}&radius=${borderRadius}&font=${font}&shadow=${shadowEnabled}&border=${borderEnabled}"
    width="${width}"
    height="${height}"
    frameborder="0"
    allowtransparency="true">
</iframe>`;

    // Update the content of the embed code display area
    codeContent.textContent = embedCode;
}


// ===== 7. UTILITY FUNCTIONS =====

// 7.1 Hex to RGBA Conversion
function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// 7.2 RGB to Hex Conversion
function rgbToHex(rgb) {
    // Extract RGB values from rgb string
    const rgbValues = rgb.match(/\d+/g);
    if (!rgbValues || rgbValues.length < 3) return '#000000';

    const r = parseInt(rgbValues[0]);
    const g = parseInt(rgbValues[1]);
    const b = parseInt(rgbValues[2]);

    // Convert RGB to Hexadecimal format
    return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
}

// 7.3 Color Lightening
function lightenColor(hex, amount) {
    let r = parseInt(hex.slice(1, 3), 16);
    let g = parseInt(hex.slice(3, 5), 16);
    let b = parseInt(hex.slice(5, 7), 16);

    r = Math.min(255, Math.max(0, r + amount));
    g = Math.min(255, Math.max(0, g + amount));
    b = Math.min(255, Math.max(0, b + amount));

    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}

// 7.4 Debounce Function
function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            func.apply(context, args);
        }, wait);
    };
}


// ===== 8. DOM Ready Widget Selection (Initial Code Snippet - moved to end for clarity) =====
// This section contains the initial code snippet from the original js file,
// which seems to be related to a different approach of widget selection and customization.
// It is kept here for reference but is not directly part of the current Widget Manager functionality
// outlined in the Table of Contents above.

/*
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const widgetCards = document.querySelectorAll('.widget-card');
    const widgetSelectionArea = document.getElementById('widget-selection');
    const selectedWidgetContainer = document.getElementById('selected-widget-container');
    const selectedWidgetName = document.getElementById('selected-widget-name');
    const backToSelectionBtn = document.getElementById('back-to-selection');
    const widgetCustomizationArea = document.getElementById('widget-customization-area');

    // Widget type to display name mapping
    const widgetTypeNames = {
        'now-playing': 'Şu An Çalan',
        'recently-played': 'Son Çalınanlar',
        'top-tracks': 'En Çok Dinlenenler',
        'playlist': 'Çalma Listesi'
    };

    // Widget selection event
    widgetCards.forEach(card => {
        card.addEventListener('click', function() {
            const widgetType = this.getAttribute('data-widget-type');
            selectWidget(widgetType);
        });
    });

    // Back button event
    backToSelectionBtn.addEventListener('click', function(e) {
        e.preventDefault();
        showWidgetSelection();
    });

    // Select a widget
    function selectWidget(widgetType) {
        // Update selected widget name
        selectedWidgetName.textContent = widgetTypeNames[widgetType];

        // Hide widget selection and show customization
        widgetSelectionArea.style.display = 'none';
        selectedWidgetContainer.classList.remove('hidden');

        // Load widget customization options
        loadWidgetCustomizationOptions(widgetType);

        // Add animation class
        selectedWidgetContainer.classList.add('fade-in');

        // Scroll to the customization area
        selectedWidgetContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Show widget selection
    function showWidgetSelection() {
        // Hide customization and show widget selection
        selectedWidgetContainer.classList.add('hidden');
        widgetSelectionArea.style.display = 'block';

        // Add animation class
        widgetSelectionArea.classList.add('fade-in');

        // Clear customization area
        widgetCustomizationArea.innerHTML = '';

        // Scroll to the widget selection
        widgetSelectionArea.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Load widget customization options based on widget type
    function loadWidgetCustomizationOptions(widgetType) {
        // This function will be expanded in the next phase
        // For now, just show a placeholder message
        widgetCustomizationArea.innerHTML = `
            <div class="placeholder-message">
                <i class="fas fa-cog fa-spin"></i>
                <h3>${widgetTypeNames[widgetType]} widget'ı seçildi</h3>
                <p>Bu widget için özelleştirme seçenekleri yakında eklenecektir.</p>
            </div>
        `;
    }

    // Add hover effects for better interactivity
    widgetCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.querySelector('.widget-icon').classList.add('pulse');
        });

        card.addEventListener('mouseleave', function() {
            this.querySelector('.widget-icon').classList.remove('pulse');
        });
    });

    // Add some CSS animations
    document.head.insertAdjacentHTML('beforeend', `
        <style>
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }

            .pulse {
                animation: pulse 1s infinite;
            }

            .fade-in {
                animation: fadeIn 0.5s ease-in-out;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .placeholder-message {
                text-align: center;
                padding: 40px 20px;
            }

            .placeholder-message i {
                font-size: 3rem;
                color: var(--primary-color);
                margin-bottom: 20px;
            }

            .placeholder-message h3 {
                font-size: 1.5rem;
                margin-bottom: 10px;
            }

            .placeholder-message p {
                color: var(--text-secondary);
            }
        </style>
    `);
});
*/
