/**
 * Widget Manager Main Entry Point (Unified Studio Layout)
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get config from global window object (injected by template)
    const config = window.beatifyWidgetConfig || {};
    
    if (!config.widgetsData) {
        console.error("Widget configuration not found or invalid.");
        return;
    }

    // EventBus (global)
    const eventBus = new EventBus();
    window.widgetEventBus = eventBus;

    // Track currently active theme (for settings saves, etc.)
    let currentTheme = config.initialTheme || 'modern';
    // Eğer tema değişimi sırasında önizleme yüklemesini modal tamamen açılana
    // kadar ertelemek istersek kullanılacak geçici URL
    let pendingPreviewUrl = null;
    // Modal'ı en son hangi kaynaktan açtığımızı takip et (hazır tema / kayıtlı widget)
    // 'ready'  -> üstteki hazır tema kartlarından açıldı
    // 'saved'  -> alt taraftaki kayıtlı widget kartlarından açıldı
    // null     -> henüz belirlenmedi
    let lastOpenSource = null;

    // Active widget state (selected token may be a saved widget, not only theme defaults)
    let activeWidgetToken = null;
    let activeWidgetName = null;
    // True when active token equals theme default token (config.widgetsData[theme].token)
    let activeWidgetIsThemeDefault = false;
    // Saved widgets cache (populated from /spotify/widget-list)
    let savedWidgetsIndex = {};

    // DOM Elements
    const elements = {
        // Preview Elements
        previewFrame: document.getElementById('widgetPreviewFrame'),
        iframeWrapper: document.querySelector('.iframe-wrapper'),
        previewContainer: document.querySelector('.preview-container'),
        refreshBtn: document.getElementById('refreshPreview'),
        changeTrackBtn: document.getElementById('changeTrackBtn'),
        
        // Embed Elements
        embedCodeArea: document.getElementById('embedCode'),
        copyBtn: document.getElementById('copyEmbedCode'),
        getEmbedCodeBtn: document.getElementById('getEmbedCodeBtn'),
        saveWidgetBtn: document.getElementById('saveWidgetBtn'),
        
        // Theme Selection Elements (gallery cards)
        themeCards: document.querySelectorAll('.theme-card[data-theme]:not(.coming-soon)'),

        // Theme gallery carousel controls
        carousel: document.getElementById('themeCarousel'),
        prevBtn: document.getElementById('themeCarouselPrev'),
        nextBtn: document.getElementById('themeCarouselNext'),

        // Saved widgets gallery
        savedWidgetsContainer: document.getElementById('savedWidgetsContainer'),

        // Modal elements
        themeStudioModal: document.getElementById('themeStudioModal'),
        themeStudioModalTitle: document.getElementById('themeStudioModalTitle'),
        
        // Settings Container
        settingsContainer: document.getElementById('themeSettingsContainer')
    };

    // Modalları, pozisyonlama bağımsız olsun diye body altına taşı
    ['themeStudioModal', 'embedModal'].forEach(id => {
        const el = document.getElementById(id);
        if (el && el.parentElement !== document.body) {
            document.body.appendChild(el);
        }
    });

    /**
     * Basit HTML kaçış yardımcı fonksiyonu.
     */
    const escapeHtml = (value) => {
        if (value === null || value === undefined) return '';
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    };

    /**
     * Token için sansürlü gösterim üretir.
     * Örn: abcd****wxyz
     */
    const maskToken = (value) => {
        if (!value) return '';
        const str = String(value);
        if (str.length <= 8) {
            return '••••' + str.slice(-4);
        }
        return str.slice(0, 4) + '••••' + str.slice(-4);
    };

    // Initialize Core Services
    // Note: Services are expected to be loaded before this script
    const previewService = new PreviewService(elements, config);
    const embedService = new EmbedService(elements, config);
    
    let themeSettingsService = null;
    let themeService = null;

    /**
     * Basit preset kimliğini (static / soft / dynamic) verilen config üzerinden tahmin eder.
     * ThemeSettingsService._getCurrentPresetId ile aynı mantığı kullanır.
     */
    const classifyPresetFromAnimations = (anims = {}) => {
        const normalize = (obj) => {
            if (!obj) return { name: '', duration: 0, delay: 0 };
            const name = (obj.animation || obj.type || '').toLowerCase();
            const duration = typeof obj.duration === 'number' ? obj.duration : 0;
            const delay = typeof obj.delay === 'number' ? obj.delay : 0;
            return { name, duration, delay };
        };

        const intro = normalize(anims.intro);
        const transitionIn = normalize(anims.transitionIn);
        const transitionOut = normalize(anims.transitionOut);
        const outro = normalize(anims.outro);

        if (!intro.name) return null;
        if (intro.name === 'none') return 'static';

        if (intro.name.startsWith('fade')) {
            if (intro.duration >= 1200) return 'fade-long';
            if (intro.duration >= 850) return 'mellow-fade';
            if (intro.duration >= 700) return 'fade-stagger';
            return 'fade-pulse';
        }

        const usesSlide = intro.name.startsWith('slide');
        if (usesSlide) {
            const spotlightLike = intro.name === 'slide-down'
                && outro.name === 'slide-up-out'
                && transitionIn.name.startsWith('fade');
            if (spotlightLike) {
                if (intro.duration < 760) return 'pop-spot';
                return 'spotlight';
            }

            const driftLike = intro.name === 'slide-left' && transitionIn.name.startsWith('fade');
            if (driftLike) return 'drift';

            const fastSlide = intro.duration && intro.duration <= 540;
            if (fastSlide) return 'slide-burst';

            if (intro.name === 'slide-left') return 'slide-left';
            if (intro.name === 'slide-right') return 'slide-right';
            if (intro.name === 'slide-up') return 'slide-up';
            if (intro.name === 'slide-down') return 'parallax';
        }

        if (intro.name && transitionIn.name.startsWith('fade') && outro.name.startsWith('slide')) {
            return 'burst-mix';
        }

        // Geri kalan her şey için gentle-slide kabul edilir
        return 'gentle-slide';
    };

    const getPresetIdFromConfig = (fullConfig) => {
        const components = fullConfig && fullConfig.components ? fullConfig.components : {};
        const names = Object.keys(components);

        for (const name of names) {
            const comp = components[name];
            if (!comp || !comp.set_a || !comp.set_a.animations) continue;
            const detected = classifyPresetFromAnimations(comp.set_a.animations);
            if (detected) return detected;
        }

        // Varsayılan: gentle-slide
        return 'gentle-slide';
    };

    // Preset preview class mapping (shared)
    const PREVIEW_CLASS_MAP = {
        'static': 'preset-static-preview',
        'mellow-fade': 'preset-fade-preview',
        'fade-long': 'preset-fade-preview',
        'fade-pulse': 'preset-fade-preview',
        'fade-stagger': 'preset-fade-preview',
        'gentle-slide': 'preset-slide-preview',
        'pop-spot': 'preset-spotlight-preview',
        'slide-left': 'preset-slide-preview',
        'slide-right': 'preset-slide-preview',
        'slide-up': 'preset-slide-preview',
        'slide-burst': 'preset-burst-preview',
        'spotlight': 'preset-spotlight-preview',
        'drift': 'preset-spotlight-preview',
        'parallax': 'preset-spotlight-preview',
        'burst-mix': 'preset-burst-preview'
    };
    const ALL_PREVIEW_CLASSES = Object.values(PREVIEW_CLASS_MAP);

    const getPreviewClassForConfig = (fullConfig) => {
        const presetId = getPresetIdFromConfig(fullConfig || {});
        return PREVIEW_CLASS_MAP[presetId] || PREVIEW_CLASS_MAP['gentle-slide'] || PREVIEW_CLASS_MAP['static'];
    };

    /**
     * Belirli bir tema için widget manager ekranındaki tüm kartlara
     * (hazır tema + kayıtlı widget kartları) preset önizleme sınıfı uygular.
     */
    const applyPresetPreviewForTheme = (themeKey) => {
        if (!themeKey || !config.widgetsData || !config.widgetsData[themeKey]) return;

        const cfg = config.widgetsData[themeKey].config || {};
        const previewClass = getPreviewClassForConfig(cfg);

        // IMPORTANT: only apply to READY theme cards, not saved widget cards.
        document.querySelectorAll(`.theme-card[data-theme="${themeKey}"]:not(.saved-widget-card)`).forEach(card => {
            card.classList.remove(...ALL_PREVIEW_CLASSES);
            card.classList.add(previewClass);
        });
    };

    const resolveThemeKeyFromConfig = (fullConfig, fallback = 'modern') => {
        const name = fullConfig && fullConfig.theme && fullConfig.theme.name;
        if (name === 'classic' || name === 'modern') return name;
        return fallback || 'modern';
    };

    const setActiveThemeCard = (themeKey) => {
        if (!elements.themeCards || !elements.themeCards.length) return;
        elements.themeCards.forEach(card => {
            if (card.dataset.theme === themeKey) card.classList.add('active');
            else card.classList.remove('active');
        });
    };

    // Callback for when settings are changed in the Settings Panel
    const onSettingsChange = async (newConfig) => {
        // Save to backend
        try {
            const success = await themeService.saveFullConfig(newConfig);
            if (success) {
                console.log("Configuration saved.");
                
                // Update local config state
                config.fullConfig = newConfig;

                // If editing theme-default widget, keep theme map in sync (for ready cards preview)
                if (config.widgetsData[currentTheme] && config.widgetsData[currentTheme].token === activeWidgetToken) {
                    config.widgetsData[currentTheme].config = newConfig;
                    applyPresetPreviewForTheme(currentTheme);
                }

                // If this is a saved widget card, update its own preview class in-place
                const savedCard = document.querySelector(`.saved-widget-card[data-widget-token="${activeWidgetToken}"]`);
                if (savedCard) {
                    savedCard.classList.remove(...ALL_PREVIEW_CLASSES);
                    savedCard.classList.add(getPreviewClassForConfig(newConfig));
                }

                // Update cache
                if (activeWidgetToken && savedWidgetsIndex[activeWidgetToken]) {
                    savedWidgetsIndex[activeWidgetToken].config_data = newConfig;
                }

                // Refresh the preview to show changes
                previewService.refresh();
            } else {
                console.error("Failed to save config.");
            }
        } catch (error) {
            console.error("Error saving config:", error);
        }
    };

    // Initialize Theme Settings Service (will be updated once theme is resolved)
    if (elements.settingsContainer) {
        themeSettingsService = new ThemeSettingsService(
            elements.settingsContainer, 
            config.fullConfig, 
            onSettingsChange
        );
    }

    // Helper: apply theme change end-to-end (UI + config + services)
    // options:
    //  - boolean => autoShow (eski kullanım ile geriye dönük uyumlu)
    //  - object  => { autoShow?: boolean, deferPreview?: boolean }
    const applyThemeChange = (newTheme, options = {}) => {
        // Eski imzayı destekle: ikinci argüman boolean ise autoShow gibi davran
        const normalized = typeof options === 'boolean'
            ? { autoShow: options, deferPreview: false }
            : {
                autoShow: options.autoShow !== undefined ? options.autoShow : true,
                deferPreview: options.deferPreview === true,
            };
        const { autoShow, deferPreview } = normalized;

        console.log("Theme changed to:", newTheme);
        currentTheme = newTheme;

        // 1. Update Active State in Theme Gallery
        if (elements.themeCards && elements.themeCards.length) {
            elements.themeCards.forEach(card => {
                if (card.dataset.theme === newTheme) {
                    card.classList.add('active');
                } else {
                    card.classList.remove('active');
                }
            });
        }

        // 2. Retrieve Data for New Theme
        const widgetData = config.widgetsData[newTheme];
        if (!widgetData) {
            console.error("Widget data not found for theme:", newTheme);
            return;
        }

        // 3. Update Global Config
        config.token = widgetData.token;
        config.fullConfig = widgetData.config || {};

        // Active widget bookkeeping
        activeWidgetToken = config.token;
        activeWidgetName = null;
        activeWidgetIsThemeDefault = true;
        
        // Base URL (canlı embed için)
        const baseUrl = config.widgetBaseUrl.replace('TOKEN_PLACEHOLDER', config.token);
        config.widgetUrl = baseUrl;

        // 4. Update Sub-services
        // Embed kodu her zaman gerçek (demo olmayan) URL ile üretilir
        embedService.updateCode(newTheme, baseUrl);

        // Önizleme boyutlarını temaya göre güncelle
        previewService.updateDimensions(newTheme);
        
        // Ayar paneline yeni config'i bas
        if (themeSettingsService) {
            themeSettingsService.updateConfig(config.fullConfig);
        }
        
        // 5. Kartlar üzerinde preset önizleme sınıflarını güncelle
        applyPresetPreviewForTheme(newTheme);

        // 6. Refresh Preview (her zaman demo=1 ile mock veri kullan)
        const previewUrl = `${baseUrl}?demo=1`;

        if (deferPreview) {
            // Önizlemeyi hemen yenileme; modal tamamen açıldığında
            // shown.bs.modal içinde yüklensin.
            pendingPreviewUrl = previewUrl;
        } else {
            // Normal akış: hemen yenile
            pendingPreviewUrl = null;
            previewService.refresh(previewUrl, autoShow);
        }

        // Modal başlığında tema adını göster (varsa)
        if (elements.themeStudioModalTitle) {
            const activeCard = document.querySelector(`.theme-card[data-theme="${newTheme}"]`);
            const label = activeCard ? (activeCard.dataset.themeLabel || activeCard.querySelector('h3')?.textContent || newTheme) : newTheme;
            elements.themeStudioModalTitle.textContent = `Widget Stüdyosu · ${label}`;
        }
    };

    // Apply a specific widget (token + config) - used for saved widgets
    const applyWidgetChange = (widgetToken, fullConfig, options = {}) => {
        const normalized = typeof options === 'boolean'
            ? { autoShow: options, deferPreview: false, widgetName: null }
            : {
                autoShow: options.autoShow !== undefined ? options.autoShow : true,
                deferPreview: options.deferPreview === true,
                widgetName: options.widgetName || null,
            };
        const { autoShow, deferPreview } = normalized;

        if (!widgetToken) return;

        const themeKey = resolveThemeKeyFromConfig(fullConfig, currentTheme || 'modern');

        // Keep currentTheme consistent with widget's theme
        currentTheme = themeKey;
        setActiveThemeCard(themeKey);

        // Update global config
        config.token = widgetToken;
        config.fullConfig = fullConfig || {};

        // Active widget bookkeeping
        activeWidgetToken = widgetToken;
        activeWidgetName = normalized.widgetName;
        activeWidgetIsThemeDefault = !!(config.widgetsData
            && config.widgetsData[themeKey]
            && config.widgetsData[themeKey].token === widgetToken);

        // Base URL (canlı embed için)
        const baseUrl = config.widgetBaseUrl.replace('TOKEN_PLACEHOLDER', config.token);
        config.widgetUrl = baseUrl;

        // Update embed + preview sizing + settings UI
        embedService.updateCode(themeKey, baseUrl);
        previewService.updateDimensions(themeKey);
        if (themeSettingsService) {
            themeSettingsService.updateConfig(config.fullConfig);
        }

        // Update modal title (prefer widget name if present)
        if (elements.themeStudioModalTitle) {
            const activeCard = document.querySelector(`.theme-card[data-theme="${themeKey}"]`);
            const label = activeCard ? (activeCard.dataset.themeLabel || activeCard.querySelector('h3')?.textContent || themeKey) : themeKey;
            const suffix = activeWidgetName ? ` — ${activeWidgetName}` : '';
            elements.themeStudioModalTitle.textContent = `Widget Stüdyosu · ${label}${suffix}`;
        }

        // Refresh preview (always demo in studio)
        const previewUrl = `${baseUrl}?demo=1`;
        if (deferPreview) {
            pendingPreviewUrl = previewUrl;
        } else {
            pendingPreviewUrl = null;
            previewService.refresh(previewUrl, autoShow);
        }
    };
    
    // Initialize Theme Service (for saving config & gallery bindings)
    themeService = new ThemeService(elements, config, {
        onBeforeUpdate: () => {
            // Fade out preview while loading new theme
            if (elements.iframeWrapper) {
                elements.iframeWrapper.style.opacity = '0';
            }
        },
        onThemeChanged: (newTheme) => {
            // Üstteki hazır tema kartları üzerinden seçim yapıldığında
            // kaynağı 'ready' olarak işaretle.
            lastOpenSource = 'ready';
            applyThemeChange(newTheme);
        },
        onError: () => {
            if (elements.iframeWrapper) {
                elements.iframeWrapper.style.opacity = '1';
            }
        }
    });

    // Saved widgets gallery – helper to map token -> theme
    const tokenToThemeMap = {};
    Object.keys(config.widgetsData || {}).forEach(themeKey => {
        const data = config.widgetsData[themeKey];
        if (data && data.token) {
            tokenToThemeMap[data.token] = themeKey;
        }
    });

    const buildSavedWidgetsGallery = async () => {
        if (!elements.savedWidgetsContainer) return;

        try {
            const response = await fetch('/spotify/widget-list');
            if (!response.ok) {
                throw new Error('Widget listesi alınamadı');
            }
            const widgets = await response.json();

            // Reset cache
            savedWidgetsIndex = {};
            (widgets || []).forEach(w => {
                const token = w.widget_token || w.widgetToken || w.token;
                if (token) savedWidgetsIndex[token] = w;
            });

            if (!widgets || !widgets.length) {
                elements.savedWidgetsContainer.innerHTML = `
                    <div class="text-center text-muted py-4 small">
                        Henüz kayıtlı widget bulunmuyor. İlk temanızı seçip kaydettiğinizde burada görünecek.
                    </div>
                `;
                return;
            }

            const fragment = document.createDocumentFragment();

            widgets.forEach(widget => {
                const token = widget.widget_token || widget.widgetToken || widget.token;
                if (!token) return;

                // Önce map'ten dene, yoksa config_data'dan temayı çöz
                let themeKey = tokenToThemeMap[token] || null;
                let parsedConfig = null;
                if (!themeKey) {
                    const rawConfig = widget.config_data || widget.configData || null;
                    if (rawConfig) {
                        try {
                            parsedConfig = typeof rawConfig === 'string' ? JSON.parse(rawConfig) : rawConfig;
                            const cfgThemeName = parsedConfig && parsedConfig.theme && parsedConfig.theme.name;
                            if (cfgThemeName === 'modern' || cfgThemeName === 'classic') {
                                themeKey = cfgThemeName;
                            }
                        } catch (e) {
                            console.warn('Widget config_data parse edilemedi, tema belirlenemedi:', e);
                        }
                    }
                }
                if (!parsedConfig) {
                    const rawConfig = widget.config_data || widget.configData || null;
                    if (rawConfig) {
                        try {
                            parsedConfig = typeof rawConfig === 'string' ? JSON.parse(rawConfig) : rawConfig;
                        } catch (e) {
                            parsedConfig = null;
                        }
                    }
                }

                const themeLabel = themeKey === 'classic' ? 'Klasik Tema' :
                                   themeKey === 'modern' ? 'Modern Tema' : 'Tema Bilinmiyor';

                const createdAt = widget.created_at || widget.createdAt || '';
                const name = widget.widget_name || widget.widgetName || 'Spotify Widget';

                const card = document.createElement('article');
                card.className = 'theme-card saved-widget-card';
                card.setAttribute('data-widget-token', token);
                if (themeKey) {
                    card.setAttribute('data-theme', themeKey);
                }
                card.setAttribute('data-widget-name', name);
                card.setAttribute('data-bs-toggle', 'modal');
                card.setAttribute('data-bs-target', '#themeStudioModal');

                // Apply per-widget preview class (based on its own config)
                if (parsedConfig) {
                    card.classList.add(getPreviewClassForConfig(parsedConfig));
                }

                const previewClass = themeKey === 'classic' ? 'classic-preview' : 'modern-preview';
                const silhouetteHtml = themeKey === 'classic'
                    ? `
                        <div class="silhouette-classic">
                            <div class="s-cover"></div>
                            <div class="s-right-col">
                                <div class="s-info">
                                    <div class="s-title"></div>
                                    <div class="s-artist"></div>
                                </div>
                                <div class="s-controls">
                                    <div class="s-progress">
                                        <div class="s-bar"></div>
                                    </div>
                                    <div class="s-timestamps">
                                        <div class="s-time"></div>
                                        <div class="s-time"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `
                    : `
                        <div class="silhouette-modern">
                            <div class="s-bg-image"></div>
                            <div class="s-overlay"></div>
                            <div class="s-content">
                                <div class="s-info">
                                    <div class="s-title"></div>
                                    <div class="s-artist"></div>
                                </div>
                                <div class="s-controls">
                                    <div class="s-progress">
                                        <div class="s-bar"></div>
                                    </div>
                                    <div class="s-timestamps">
                                        <div class="s-time"></div>
                                        <div class="s-time"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

                const createdAtText = createdAt ? new Date(createdAt).toLocaleString() : '';
                const maskedToken = maskToken(token);
                const safeName = escapeHtml(name);
                const safeToken = escapeHtml(token);

                card.innerHTML = `
                    <div class="card-preview ${previewClass}">
                        ${silhouetteHtml}
                    </div>
                    <div class="card-info saved-widget-card-body">
                        <div class="saved-widget-card-header">
                            <span class="badge bg-success-subtle text-success saved-widget-theme-badge">
                                <i class="fas fa-palette me-1"></i>${themeLabel}
                            </span>
                            <span class="saved-widget-created-at text-muted">
                                ${createdAtText}
                            </span>
                        </div>
                        <div class="saved-widget-name-wrapper">
                            <div class="saved-widget-name-row">
                                <h3 class="saved-widget-title" title="${safeName}">${safeName}</h3>
                                <button type="button" class="saved-widget-rename-btn" aria-label="Widget adını düzenle">
                                    <i class="fas fa-pen"></i>
                                </button>
                                <button type="button" class="saved-widget-delete-btn" aria-label="Widget'ı sil">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                            <div class="saved-widget-name-edit">
                                <input type="text" class="form-control form-control-sm saved-widget-name-input" value="${safeName}" maxlength="80">
                                <button type="button" class="btn btn-sm btn-success saved-widget-name-save">Kaydet</button>
                                <button type="button" class="btn btn-sm btn-outline-secondary saved-widget-name-cancel">Vazgeç</button>
                            </div>
                        </div>
                        <div class="saved-widget-token-row">
                            <span class="saved-widget-token-label text-muted">Token:</span>
                            <code class="saved-widget-token-code" data-full-token="${safeToken}" data-masked="true">${maskedToken}</code>
                            <button type="button" class="saved-widget-token-toggle" aria-label="Tokeni göster veya gizle">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                    </div>
                `;

                // İsim düzenleme etkileşimleri
                const nameTitleEl = card.querySelector('.saved-widget-title');
                const renameBtn = card.querySelector('.saved-widget-rename-btn');
                const nameEditRow = card.querySelector('.saved-widget-name-edit');
                const nameInput = card.querySelector('.saved-widget-name-input');
                const nameSaveBtn = card.querySelector('.saved-widget-name-save');
                const nameCancelBtn = card.querySelector('.saved-widget-name-cancel');

                if (renameBtn && nameEditRow && nameInput && nameTitleEl && nameSaveBtn && nameCancelBtn) {
                    const closeEditor = () => {
                        nameEditRow.classList.remove('is-active');
                    };

                    renameBtn.addEventListener('click', (event) => {
                        event.stopPropagation();
                        event.preventDefault();
                        nameInput.value = nameTitleEl.textContent.trim();
                        nameEditRow.classList.add('is-active');
                        nameInput.focus();
                        nameInput.select();
                    });

                    nameCancelBtn.addEventListener('click', (event) => {
                        event.stopPropagation();
                        event.preventDefault();
                        closeEditor();
                    });

                    const saveName = async (event) => {
                        event.stopPropagation();
                        event.preventDefault();
                        const newNameRaw = nameInput.value || '';
                        const newName = newNameRaw.trim();

                        if (!newName || newName === nameTitleEl.textContent.trim()) {
                            closeEditor();
                            return;
                        }

                        nameSaveBtn.disabled = true;
                        try {
                            const resp = await fetch('/spotify/widget/update-config', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    widget_token: token,
                                    widget_name: newName
                                })
                            });
                            const data = await resp.json();
                            if (!resp.ok || data.error) {
                                console.error('Widget adı güncellenemedi:', data.error || data);
                                alert('Widget adı güncellenemedi. Lütfen tekrar deneyin.');
                            } else {
                                const finalName = (data && data.widget_name) ? data.widget_name : newName;
                                nameTitleEl.textContent = finalName;
                                card.setAttribute('data-widget-name', finalName);
                                if (savedWidgetsIndex[token]) {
                                    savedWidgetsIndex[token].widget_name = finalName;
                                }
                                // If currently open widget is this one, reflect in modal title
                                if (activeWidgetToken === token) {
                                    activeWidgetName = finalName;
                                    if (elements.themeStudioModalTitle) {
                                        const activeCard = document.querySelector(`.theme-card[data-theme="${themeKey}"]`);
                                        const label = activeCard ? (activeCard.dataset.themeLabel || activeCard.querySelector('h3')?.textContent || themeKey) : themeKey;
                                        elements.themeStudioModalTitle.textContent = `Widget Stüdyosu · ${label} — ${finalName}`;
                                    }
                                }
                            }
                        } catch (err) {
                            console.error('Widget adı güncellenemedi:', err);
                            alert('Widget adı güncellenemedi. Lütfen tekrar deneyin.');
                        } finally {
                            nameSaveBtn.disabled = false;
                            closeEditor();
                        }
                    };

                    nameSaveBtn.addEventListener('click', saveName);
                    nameInput.addEventListener('keydown', (event) => {
                        if (event.key === 'Enter') {
                            saveName(event);
                        } else if (event.key === 'Escape') {
                            event.stopPropagation();
                            event.preventDefault();
                            closeEditor();
                        }
                    });

                    nameEditRow.addEventListener('click', (event) => {
                        event.stopPropagation();
                    });
                }

                // Silme butonu
                const deleteBtn = card.querySelector('.saved-widget-delete-btn');
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', async (event) => {
                        event.stopPropagation();
                        event.preventDefault();
                        const ok = confirm('Bu widget silinsin mi? Bu işlem geri alınamaz.');
                        if (!ok) return;
                        deleteBtn.disabled = true;
                        try {
                            const resp = await fetch('/spotify/widget/delete', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ widget_token: token })
                            });
                            const data = await resp.json();
                            if (!resp.ok || data.error) {
                                console.error('Widget silinemedi:', data.error || data);
                                alert('Widget silinemedi. Lütfen tekrar deneyin.');
                                return;
                            }

                            // UI: remove card
                            if (card && card.parentNode) {
                                card.parentNode.removeChild(card);
                            }
                            delete savedWidgetsIndex[token];

                            // If the currently open widget was deleted, fall back to theme default
                            if (activeWidgetToken === token) {
                                const fallbackTheme = themeKey || currentTheme || 'modern';
                                // Keep studio modal open, but switch to default token for that theme
                                applyThemeChange(fallbackTheme, { deferPreview: true });
                            }
                        } catch (err) {
                            console.error('Widget silinemedi:', err);
                            alert('Widget silinemedi. Lütfen tekrar deneyin.');
                        } finally {
                            deleteBtn.disabled = false;
                        }
                    });
                }

                // Token göster/gizle etkileşimi
                const tokenCodeEl = card.querySelector('.saved-widget-token-code');
                const tokenToggleBtn = card.querySelector('.saved-widget-token-toggle');
                if (tokenCodeEl && tokenToggleBtn) {
                    tokenToggleBtn.addEventListener('click', (event) => {
                        event.stopPropagation();
                        event.preventDefault();
                        const currentlyMasked = tokenCodeEl.dataset.masked === 'true';
                        if (currentlyMasked) {
                            tokenCodeEl.textContent = token;
                            tokenCodeEl.dataset.masked = 'false';
                            tokenToggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i>';
                        } else {
                            tokenCodeEl.textContent = maskedToken;
                            tokenCodeEl.dataset.masked = 'true';
                            tokenToggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
                        }
                    });
                }

                // Kartın genel tıklaması: ilgili temayı stüdyoda aç
                card.addEventListener('click', () => {
                    const record = savedWidgetsIndex[token] || widget;
                    const rawConfig = record ? (record.config_data || record.configData || null) : null;
                    let cfg = parsedConfig;
                    if (!cfg && rawConfig) {
                        try {
                            cfg = typeof rawConfig === 'string' ? JSON.parse(rawConfig) : rawConfig;
                        } catch (e) {
                            cfg = null;
                        }
                    }
                    const resolvedTheme = resolveThemeKeyFromConfig(cfg, themeKey || currentTheme || 'modern');

                    // Bu açılışın kayıtlı widget kartından geldiğini not et
                    lastOpenSource = 'saved';

                    // Önce demo önizleme için fade-out
                    if (themeService && themeService.callbacks && typeof themeService.callbacks.onBeforeUpdate === 'function') {
                        themeService.callbacks.onBeforeUpdate();
                    }

                    // Sonra seçili widget token/config'i uygula fakat gerçek iframe yüklemesini
                    // modal tamamen açılana kadar ertele (flash/glitch engelleme).
                    applyWidgetChange(token, cfg || {}, { deferPreview: true, widgetName: name });
                });

                fragment.appendChild(card);
            });

            elements.savedWidgetsContainer.innerHTML = '';
            elements.savedWidgetsContainer.appendChild(fragment);

            // Hazır temalar için preset önizleme sınıflarını uygula (saved kartlara dokunma)
            Object.keys(config.widgetsData || {}).forEach(themeKey => applyPresetPreviewForTheme(themeKey));
        } catch (error) {
            console.error('Kayıtlı widget listesi yüklenirken hata:', error);
            elements.savedWidgetsContainer.innerHTML = `
                <div class="text-center text-danger py-4 small">
                    Kayıtlı widgetlar yüklenirken bir hata oluştu.
                </div>
            `;
        }
    };

    // Event Listener: Copy Embed Code (works even without data-clipboard-target)
    if (elements.copyBtn && elements.embedCodeArea) {
        elements.copyBtn.addEventListener('click', () => {
            elements.embedCodeArea.select();
            document.execCommand('copy');
            
            const originalHTML = elements.copyBtn.innerHTML;
            elements.copyBtn.innerHTML = '<i class="fas fa-check me-2"></i>Kopyalandı!';
            elements.copyBtn.classList.add('btn-success');
            elements.copyBtn.classList.remove('btn-copy-code');
            
            setTimeout(() => {
                elements.copyBtn.innerHTML = originalHTML;
                elements.copyBtn.classList.remove('btn-success');
                elements.copyBtn.classList.add('btn-copy-code');
            }, 2000);
        });
    }

    // Event Listener: Manual Refresh
    if (elements.refreshBtn) {
        elements.refreshBtn.addEventListener('click', () => {
            // Mevcut src'yi sadece cache-bypass ile yenile
            previewService.refresh();
        });
    }

    // Event Listener: Save widget copy
    if (elements.saveWidgetBtn) {
        elements.saveWidgetBtn.addEventListener('click', async () => {
            if (!activeWidgetToken) {
                alert('Kaydedilecek aktif bir widget bulunamadı.');
                return;
            }

            const defaultName = activeWidgetName
                ? `${activeWidgetName} (Kopya)`
                : (currentTheme === 'classic' ? 'Klasik Widget (Kopya)' : 'Modern Widget (Kopya)');

            const nameInput = prompt('Yeni widget adı:', defaultName);
            if (nameInput === null) return; // cancelled
            const newName = (nameInput || '').trim();
            if (!newName) {
                alert('Widget adı boş olamaz.');
                return;
            }

            elements.saveWidgetBtn.disabled = true;
            try {
                const resp = await fetch('/spotify/widget/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        base_widget_token: activeWidgetToken,
                        widget_name: newName
                    })
                });
                const data = await resp.json();
                if (!resp.ok || data.error) {
                    console.error('Widget kaydedilemedi:', data.error || data);
                    alert('Widget kaydedilemedi. Lütfen tekrar deneyin.');
                    return;
                }

                // Refresh gallery and open the newly created widget in studio
                await buildSavedWidgetsGallery();
                const createdToken = data.widget_token;
                const createdConfig = data.config_data || {};

                // Fade-out before switching
                if (themeService && themeService.callbacks && typeof themeService.callbacks.onBeforeUpdate === 'function') {
                    themeService.callbacks.onBeforeUpdate();
                }
                lastOpenSource = 'saved';
                applyWidgetChange(createdToken, createdConfig, { deferPreview: true, widgetName: data.widget_name || newName });
            } catch (err) {
                console.error('Widget kaydedilemedi:', err);
                alert('Widget kaydedilemedi. Lütfen tekrar deneyin.');
            } finally {
                elements.saveWidgetBtn.disabled = false;
            }
        });
    }

    // Event Listener: Change Track (simüle edilmiş shuffle)
    if (elements.changeTrackBtn) {
        elements.changeTrackBtn.addEventListener('click', () => {
            eventBus.emit('manager:changeTrack');
        });
    }

    eventBus.on('manager:changeTrack', () => {
        const themeKey = currentTheme || 'modern';
        const widgetData = (config.widgetsData || {})[themeKey];
        const token = widgetData && widgetData.token ? widgetData.token : config.token;
        if (!token) return;

        // Önce iframe'e "changeTrack" mesajı gönder, widget içi next/transition tetiklensin.
        if (elements.previewFrame && elements.previewFrame.contentWindow) {
            elements.previewFrame.contentWindow.postMessage({ type: 'changeTrack' }, '*');
        }
    });

    // Modal açılırken ve kapanırken durum yönetimi
    if (elements.themeStudioModal) {
        // Modal kapanınca içeriği gizle ki bir sonraki açılışta "flash" olmasın
        elements.themeStudioModal.addEventListener('hidden.bs.modal', () => {
            if (elements.iframeWrapper) {
                elements.iframeWrapper.style.transition = 'none'; // Animasyonsuz hemen gizle
                elements.iframeWrapper.style.opacity = '0';
            }

            // Eğer modal son olarak kayıtlı bir widget kartından açıldıysa,
            // bir sonraki açılışta eski içeriğin tek kare bile görünmemesi için
            // iframe'i tamamen sıfırla.
            if (lastOpenSource === 'saved') {
                if (elements.previewFrame) {
                    elements.previewFrame.src = 'about:blank';
                }
                if (elements.previewContainer) {
                    elements.previewContainer.classList.remove('is-loading');
                }
                pendingPreviewUrl = null;
            }
        });

        elements.themeStudioModal.addEventListener('show.bs.modal', () => {
            // Modal açılmaya başlarken içeriği KESİN olarak gizle
            if (elements.iframeWrapper) {
                elements.iframeWrapper.style.transition = 'none'; // Geçiş efekti olmadan anında gizle
                elements.iframeWrapper.style.opacity = '0';
            }
        });

        elements.themeStudioModal.addEventListener('shown.bs.modal', () => {
            // Modal animasyonu bitti, şimdi içeriği göster (varsa)
            
            // Transition'ı geri aç
            if (elements.iframeWrapper) {
                // Force reflow
                void elements.iframeWrapper.offsetWidth;
                elements.iframeWrapper.style.transition = 'opacity 0.4s ease';
            }

            const themeKey = currentTheme || 'modern';

            // Eğer tıklama sırasında ertelenmiş bir önizleme URL'i varsa,
            // öncelik her zaman ondadır (kayıtlı widget kartları için).
            if (pendingPreviewUrl) {
                const urlToLoad = pendingPreviewUrl;
                pendingPreviewUrl = null;

                // İlgili tema boyutlarını uygula ve yeni URL'i yükle.
                previewService.updateDimensions(themeKey);
                // refresh() metodu yükleme bitince opacity'yi 1 yapacak
                // (modal şu an açık olduğu için offsetParent null değil).
                previewService.refresh(urlToLoad, true);
                return;
            }

            // Eğer henüz bir URL yüklenmediyse veya boşsa, güncel tema için demo önizlemeyi başlat
            const currentSrc = elements.previewFrame ? elements.previewFrame.src : '';
            const isFrameEmpty = !currentSrc || currentSrc === 'about:blank' || currentSrc.endsWith('about:blank');
            
            // Yeniden ölçekle (her durumda, boyut doğru olsun)
            const dims = previewService.widgetDimensions[themeKey] || previewService.widgetDimensions['modern'];
            previewService.fitToContainer(dims.width, dims.height);

            if (isFrameEmpty) {
                // Zaten yükleniyorsa tekrar refresh yapma
                if (elements.previewContainer && elements.previewContainer.classList.contains('is-loading')) {
                    return;
                }

                const widgetData = (config.widgetsData || {})[themeKey];
                const token = widgetData && widgetData.token ? widgetData.token : config.token;

                if (token) {
                    const baseUrl = config.widgetBaseUrl.replace('TOKEN_PLACEHOLDER', token);
                    const previewUrl = `${baseUrl}?demo=1`;
                    previewService.updateDimensions(themeKey);
                    // refresh() metodu yükleme bitince opacity'yi 1 yapacak
                    previewService.refresh(previewUrl);
                }
            } else {
                // Eğer zaten bir içerik varsa ve yüklenmiyorsa, opacity'yi aç
                if (elements.iframeWrapper && elements.previewContainer && !elements.previewContainer.classList.contains('is-loading')) {
                    elements.iframeWrapper.style.opacity = '1';
                }
            }
        });
    }

    // Initial Setup – resolve and apply starting theme (for preview modal)
    const startTheme = currentTheme || 'modern';
    applyThemeChange(startTheme, false);

    // Initialize active token from the selected theme
    if (config.widgetsData && config.widgetsData[startTheme] && config.widgetsData[startTheme].token) {
        activeWidgetToken = config.widgetsData[startTheme].token;
        activeWidgetIsThemeDefault = true;
    }

    // Saved widgets galeriyi doldur
    buildSavedWidgetsGallery();

    // İlk yüklemede, sayfa boyutu için temel bir ölçek hesabı yap
    setTimeout(() => {
        if (!elements.iframeWrapper || !elements.previewContainer) return;
        const dims = previewService.widgetDimensions[startTheme] || previewService.widgetDimensions['modern'];
        previewService.fitToContainer(dims.width, dims.height);

        // Hazır temalar için de preset önizleme sınıflarını uygula
        Object.keys(config.widgetsData || {}).forEach(themeKey => {
            applyPresetPreviewForTheme(themeKey);
        });
    }, 300);
});
