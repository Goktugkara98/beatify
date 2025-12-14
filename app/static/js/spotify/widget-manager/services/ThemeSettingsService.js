class ThemeSettingsService {
    constructor(container, config, onUpdate) {
        this.container = container;
        this.config = config; // Full theme config object
        this.onUpdate = onUpdate; // Callback when settings change
        this.defaultConfig = this._getDefaultConfig();
        // Ayar paneli çok sekmeli: Genel + animasyon setleri + Gelişmiş
        this.activeTab = 'general';
        this.selectedComponent = null;
        this.selectedSectionId = null;
        this.studioSelection = null;
        
        // Merge provided config with default to ensure structure
        this.currentConfig = this._mergeConfig(this.defaultConfig, this.config);
        
        this._render();
    }

    updateConfig(newConfig) {
        this.currentConfig = this._mergeConfig(this.defaultConfig, newConfig);
        this._render();
    }

    _mergeConfig(def, current) {
        // Simple deep merge or fallback
        if (!current) return JSON.parse(JSON.stringify(def));
        
        // Clone current to avoid mutating reference
        const merged = JSON.parse(JSON.stringify(current));
        
        // Ensure components exist
        if (!merged.components) merged.components = {};
        
        // Merge components from default
        Object.keys(def.components).forEach(key => {
            if (!merged.components[key]) {
                merged.components[key] = JSON.parse(JSON.stringify(def.components[key]));
            } else {
                // Deep merge sets
                ['set_a', 'set_b'].forEach(set => {
                    if (!merged.components[key][set]) {
                        merged.components[key][set] = JSON.parse(JSON.stringify(def.components[key][set]));
                    } else {
                        // Ensure animations object exists
                        if (!merged.components[key][set].animations) {
                            merged.components[key][set].animations = {};
                        }
                    }
                });
            }
        });

        // Animasyon şeması normalizasyonu:
        // - Her animType için objenin varlığını garanti et (intro/transitionIn/transitionOut/outro)
        // - `animation` ve `type` alanlarını senkronla (GSAP `type` okuyor)
        // - duration/delay değerlerini sayıya çevir
        const animTypes = ['intro', 'transitionIn', 'transitionOut', 'outro'];
        Object.keys(merged.components).forEach((componentName) => {
            const comp = merged.components[componentName];
            if (!comp) return;
            ['set_a', 'set_b'].forEach((setKey) => {
                const setData = comp[setKey];
                if (!setData) return;
                if (!setData.animations) setData.animations = {};

                animTypes.forEach((animType) => {
                    if (!setData.animations[animType]) {
                        setData.animations[animType] = { animation: 'none', type: 'none', duration: 0, delay: 0 };
                    }
                    const a = setData.animations[animType] || {};

                    const name = (a.type || a.animation || 'none');
                    a.type = a.type || name;
                    a.animation = a.animation || name;

                    a.duration = typeof a.duration === 'number' ? a.duration : parseInt(a.duration || 0);
                    if (Number.isNaN(a.duration)) a.duration = 0;
                    a.delay = typeof a.delay === 'number' ? a.delay : parseInt(a.delay || 0);
                    if (Number.isNaN(a.delay)) a.delay = 0;

                    setData.animations[animType] = a;
                });
            });
        });
        
        return merged;
    }

    _render() {
        this.container.innerHTML = '';

        // Sekme başlıkları (Genel + Animasyon Setleri + Gelişmiş)
        const tabsNav = document.createElement('div');
        tabsNav.className = 'settings-tabs-nav mb-3';

        const tabs = [
            { id: 'general', label: 'Genel', description: 'Hızlı stil seçimi' },
            { id: 'fade', label: 'Fade Setleri', description: 'Yumuşak ve uzun geçişler' },
            { id: 'slide', label: 'Slide Setleri', description: 'Yönlü ve hareketli' },
            { id: 'zoom', label: 'Derinlik', description: 'Zoom tabanlı odak' },
            { id: 'blur', label: 'Bulanıklık', description: 'Blur ile yumuşak geçiş' },
            { id: 'reveal', label: 'Açılış', description: 'Maske/çizgi ile reveal' },
            { id: 'hybrid', label: 'Karma / Spotlight', description: 'Sahne ve karma mix' },
            { id: 'advanced', label: 'Gelişmiş', description: 'Detaylı kontrol' }
        ];

        tabs.forEach(tab => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'settings-tab-button';
            if (this.activeTab === tab.id) {
                btn.classList.add('active');
            }
            btn.textContent = tab.label;
            btn.addEventListener('click', () => {
                if (this.activeTab === tab.id) return;
                this.activeTab = tab.id;

                // Aktif sekme stilini güncelle
                Array.from(tabsNav.children).forEach(child => {
                    child.classList.remove('active');
                });
                btn.classList.add('active');

                this._renderActiveTab();
            });
            tabsNav.appendChild(btn);
        });

        // Sekme içerik alanı
        this.tabContent = document.createElement('div');
        this.tabContent.className = 'settings-tab-content';

        this.container.appendChild(tabsNav);
        this.container.appendChild(this.tabContent);

        this._renderActiveTab();
    }

    _renderActiveTab() {
        if (!this.tabContent) return;
        this.tabContent.innerHTML = '';

        // Modal sağ panelde preset sekmelerinde scroll olmasın, sadece advanced'da scroll açılsın.
        // (CSS tarafında .is-advanced-tab ile kontrol ediyoruz.)
        if (this.container) {
            if (this.activeTab === 'advanced') {
                this.container.classList.add('is-advanced-tab');
            } else {
                this.container.classList.remove('is-advanced-tab');
            }
        }

        if (this.activeTab === 'general') {
            this._renderPresetTab('general');
        } else if (this.activeTab === 'fade') {
            this._renderPresetTab('fade');
        } else if (this.activeTab === 'slide') {
            this._renderPresetTab('slide');
        } else if (this.activeTab === 'zoom') {
            this._renderPresetTab('zoom');
        } else if (this.activeTab === 'blur') {
            this._renderPresetTab('blur');
        } else if (this.activeTab === 'reveal') {
            this._renderPresetTab('reveal');
        } else if (this.activeTab === 'hybrid') {
            this._renderPresetTab('hybrid');
        } else if (this.activeTab === 'advanced') {
            this._renderAdvancedTab();
        }
    }

    /**
     * 1. Sekme: Genel / Preset tabanlı ayarlar
     */
    _renderPresetTab(category = 'general') {
        const wrapper = document.createElement('div');
        wrapper.className = 'preset-wrapper';

        const info = document.createElement('p');
        info.className = 'text-muted small mb-3';
        const infoMap = {
            general: 'Başlangıç için genel animasyon tarzı seç. Seçimin anında kaydedilir.',
            fade: 'Fade ağırlıklı setler: uzun, yumuşak veya kısa fade kombinasyonları.',
            slide: 'Yönlü slide setleri: sol/sağ/aşağı/yukarı hareketli geçişler.',
            zoom: 'Derinlik setleri: yakınlaşma/uzaklaşma ile odak ve “depth” hissi.',
            blur: 'Bulanıklık setleri: blur ile giriş/çıkış; yumuşak ve göz yormayan.',
            reveal: 'Açılış setleri: clip/underline gibi maske efektleriyle “reveal”.',
            hybrid: 'Karma setler: spotlight, mix veya sahne etkisi için kombinasyonlar.'
        };
        info.textContent = infoMap[category] || infoMap.general;
        wrapper.appendChild(info);

        const grid = document.createElement('div');
        grid.className = 'preset-grid';

        const corePresets = window.WidgetPresets && window.WidgetPresets.core
            ? window.WidgetPresets.core
            : null;
        const presets = corePresets && corePresets.getPresetCatalog
            ? corePresets.getPresetCatalog(category)
            : [];

        const activePreset = this._getCurrentPresetId();

        // Aktif temayı (modern / classic) tahmin et – silhouette seçimi için
        const themeName = (this.currentConfig && this.currentConfig.theme && this.currentConfig.theme.name) || 'modern';
        const isClassic = themeName === 'classic';

        presets.forEach(preset => {
            const card = document.createElement('button');
            card.type = 'button';
            card.className = 'preset-card';
            card.setAttribute('data-preset', preset.id);
            if (preset.id === activePreset) {
                card.classList.add('is-active');
            }
            // Silüet HTML'ini seç
            const silhouetteHtml = isClassic
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

            // Preset'e göre hover animasyon sınıfı
            const previewClass =
                corePresets && corePresets.getPresetPreviewClass
                    ? corePresets.getPresetPreviewClass(preset.id)
                    : null;
            if (previewClass) {
                card.classList.add(previewClass);
            }

            const badgeHtml = preset.id === 'fade-soft' 
                ? `<span class="preset-badge">Önerilen</span>` 
                : '';

            card.innerHTML = `
                <div class="preset-visual">${silhouetteHtml}</div>
                <div class="preset-title">${preset.title}</div>
                <div class="preset-desc">${preset.description}</div>
                ${badgeHtml}
                <div class="preset-check">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <polyline points="20 6 9 17 4 12"/>
                    </svg>
                </div>
            `;

            card.addEventListener('click', () => {
                this._applyPreset(preset.id);
            });

            grid.appendChild(card);
        });

        wrapper.appendChild(grid);
        this.tabContent.appendChild(wrapper);
    }

    _renderAdvancedTab() {
        // Gelişmiş sekmede sadece 3. adım (Stüdyo) gösterilsin:
        // doğrudan stüdyo matrisi + detay modali.
        this._renderStudioTab();
    }

    _renderSectionsTab() {
        const components = this.currentConfig.components || {};
        const componentNames = Object.keys(components);

        if (!componentNames.length) {
            const empty = document.createElement('p');
            empty.className = 'text-muted small';
            empty.textContent = 'Düzenlenebilir bileşen bulunamadı.';
            this.tabContent.appendChild(empty);
            return;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'studio-wrapper';

        const info = document.createElement('p');
        info.className = 'text-muted small mb-3';
        info.textContent = 'Bu ekran orta seviye kontroldür: Her satır bir bileşen, her sütun bir durumdur. Hücrelerden fade veya slide gibi basit animasyon tipleri seçebilirsin. Emin değilsen bu sekmeyi kullanmak zorunda değilsin.';
        wrapper.appendChild(info);

        const grid = document.createElement('div');
        grid.className = 'studio-grid';

        const states = [
            { id: 'intro', label: 'Giriş' },
            { id: 'transition', label: 'Geçiş' },
            { id: 'outro', label: 'Çıkış' }
        ];

        // Başlık satırı
        const headerRow = document.createElement('div');
        headerRow.className = 'studio-row studio-header-row';

        const firstHeaderCell = document.createElement('div');
        firstHeaderCell.className = 'studio-cell studio-cell-label';
        firstHeaderCell.textContent = 'Sınıf';
        headerRow.appendChild(firstHeaderCell);

        states.forEach(state => {
            const cell = document.createElement('div');
            cell.className = 'studio-cell studio-cell-header';
            cell.textContent = state.label;
            headerRow.appendChild(cell);
        });

        grid.appendChild(headerRow);

        // Satırlar
        componentNames.forEach(componentName => {
            const row = document.createElement('div');
            row.className = 'studio-row';

            const labelCell = document.createElement('div');
            labelCell.className = 'studio-cell studio-cell-label';
            labelCell.textContent = this._formatComponentName(componentName);
            row.appendChild(labelCell);

            states.forEach(state => {
                const cell = document.createElement('div');
                cell.className = 'studio-cell';

                const select = document.createElement('select');
                select.className = 'form-select form-select-sm';

                const options = [
                    { value: 'inherit', label: 'Varsayılan' },
                    { value: 'none', label: 'Yok' },
                    { value: 'fade', label: 'Fade' },
                    { value: 'slide-left', label: 'Slide Left' },
                    { value: 'slide-right', label: 'Slide Right' },
                    { value: 'slide-up', label: 'Slide Up' },
                    { value: 'slide-down', label: 'Slide Down' }
                ];

                const current = this._getComponentStateSimpleType(componentName, state.id);

                options.forEach(opt => {
                    const optEl = document.createElement('option');
                    optEl.value = opt.value;
                    optEl.textContent = opt.label;
                    if (opt.value === current) {
                        optEl.selected = true;
                    }
                    select.appendChild(optEl);
                });

                select.addEventListener('change', (e) => {
                    const value = e.target.value;
                    if (value === 'inherit') return;
                    this._applyComponentStateType(componentName, state.id, value);
                });

                cell.appendChild(select);
                row.appendChild(cell);
            });

            grid.appendChild(row);
        });

        wrapper.appendChild(grid);
        this.tabContent.appendChild(wrapper);
    }

    /**
     * 3. Sekme: Stüdyo - her sınıf x durum için tablo, ham config değerleri + modal detay
     */
    _renderStudioTab() {
        const components = this.currentConfig.components || {};
        const componentNames = Object.keys(components);

        if (!componentNames.length) {
            const empty = document.createElement('p');
            empty.className = 'text-muted small';
            empty.textContent = 'Düzenlenebilir bileşen bulunamadı.';
            this.tabContent.appendChild(empty);
            return;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'studio-wrapper';

        const info = document.createElement('p');
        info.className = 'text-muted small mb-3';
        info.textContent = 'Bu ekran ileri seviye kullanıcılar içindir: Veritabanındaki gerçek animasyon isimlerini gösterir. Hücrelere tıklayarak ayrıntılı süre ve gecikme ayarları yapabilirsin. Tasarımın bozulmasından endişe ediyorsan bu sekmeyi atlayabilirsin.';
        wrapper.appendChild(info);

        const grid = document.createElement('div');
        grid.className = 'studio-grid';

        const states = [
            { id: 'intro', label: 'Giriş' },
            { id: 'transition', label: 'Geçiş' },
            { id: 'outro', label: 'Çıkış' }
        ];

        // Başlık satırı
        const headerRow = document.createElement('div');
        headerRow.className = 'studio-row studio-header-row';

        const firstHeaderCell = document.createElement('div');
        firstHeaderCell.className = 'studio-cell studio-cell-label';
        firstHeaderCell.textContent = 'Sınıf';
        headerRow.appendChild(firstHeaderCell);

        states.forEach(state => {
            const cell = document.createElement('div');
            cell.className = 'studio-cell studio-cell-header';
            cell.textContent = state.label;
            headerRow.appendChild(cell);
        });

        grid.appendChild(headerRow);

        // Satırlar
        componentNames.forEach(componentName => {
            const row = document.createElement('div');
            row.className = 'studio-row';

            const labelCell = document.createElement('div');
            labelCell.className = 'studio-cell studio-cell-label';
            labelCell.textContent = this._formatComponentName(componentName);
            row.appendChild(labelCell);

            states.forEach(state => {
                const cell = document.createElement('div');
                cell.className = 'studio-cell';

                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'studio-cell-button';
                btn.textContent = this._getComponentStateRawLabel(componentName, state.id);

                btn.addEventListener('click', () => {
                    this._openStudioModal(componentName, state.id);
                });

                cell.appendChild(btn);
                row.appendChild(cell);
            });

            grid.appendChild(row);
        });

        wrapper.appendChild(grid);
        this.tabContent.appendChild(wrapper);
    }

    _renderComponentSettings(componentName, options = { mode: 'full' }) {
        this.settingsContainer.innerHTML = '';
        const componentData = this.currentConfig.components[componentName];
        if (!componentData) return;

        const mode = options.mode || 'full';

        const setsToRender = mode === 'simple' ? ['set_a'] : ['set_a', 'set_b'];
        const requiredAnimTypes = mode === 'simple'
            ? ['intro', 'outro']
            : ['intro', 'outro', 'transitionIn', 'transitionOut'];

        setsToRender.forEach(set => {
            if (!componentData[set]) return;

            const details = document.createElement('details');
            details.className = 'settings-details mb-2';
            details.open = true; // Tek set veya kullanıcı odaklı görünüm için açık gelsin
            
            const summary = document.createElement('summary');
            summary.className = 'settings-summary';
            summary.textContent = set === 'set_a' ? 'Aktif kart (Set A)' : 'Geçiş kartı (Set B)';
            details.appendChild(summary);

            const content = document.createElement('div');
            content.className = 'settings-content p-2';

            // Animations
            const animations = componentData[set].animations || {};
            
            requiredAnimTypes.forEach(animType => {
                // Eğer animasyon objesi yoksa varsayılan boş bir obje oluştur
                if (!animations[animType]) {
                    animations[animType] = { animation: 'none', duration: 0, delay: 0 };
                }
                this._renderAnimationGroup(content, componentName, set, animType, animations[animType]);
            });

            details.appendChild(content);
            this.settingsContainer.appendChild(details);
        });
    }

    _renderStudioComponentStateEditor(container, componentName, stateId) {
        const componentData = this.currentConfig.components[componentName];
        if (!componentData) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'studio-component-group mb-3';

        const title = document.createElement('h6');
        title.className = 'mb-2 small text-uppercase text-muted';
        title.textContent = this._formatComponentName(componentName);
        wrapper.appendChild(title);

        const sets = ['set_a', 'set_b'];
        const stateToAnimTypes = {
            intro: ['intro'],
            transition: ['transitionIn', 'transitionOut'],
            outro: ['outro']
        };
        const animTypes = stateToAnimTypes[stateId] || ['intro'];

        sets.forEach(set => {
            if (!componentData[set]) return;

            const details = document.createElement('details');
            details.className = 'settings-details mb-2';
            details.open = set === 'set_a';

            const summary = document.createElement('summary');
            summary.className = 'settings-summary';
            summary.textContent = set === 'set_a' ? 'Aktif kart (Set A)' : 'Geçiş kartı (Set B)';
            details.appendChild(summary);

            const content = document.createElement('div');
            content.className = 'settings-content p-2';

            const animations = componentData[set].animations || (componentData[set].animations = {});

            animTypes.forEach(animType => {
                if (!animations[animType]) {
                    animations[animType] = { animation: 'none', duration: 0, delay: 0 };
                }
                this._renderAnimationGroup(content, componentName, set, animType, animations[animType]);
            });

            details.appendChild(content);
            wrapper.appendChild(details);
        });

        container.appendChild(wrapper);
    }

    _renderAnimationGroup(container, componentName, set, animType, animData) {
        const wrapper = document.createElement('div');
        wrapper.className = 'animation-group mb-3 border-bottom pb-2';
        
        const title = document.createElement('h6');
        title.className = 'text-muted mb-2 font-size-sm text-uppercase';
        title.textContent = this._formatAnimType(animType);
        wrapper.appendChild(title);

        // Animation Type (Select)
        const typeGroup = this._createInputGroup('Animasyon', 'select', animData.animation || animData.type, (val) => {
            animData.animation = val; // Support both 'animation' and 'type' keys if schema varies
            animData.type = val;
            this._triggerUpdate();
        }, [
            { val: 'none', label: 'Yok' },
            { val: 'fade-in', label: 'Fade In' },
            { val: 'fade-out', label: 'Fade Out' },
            { val: 'slide-up', label: 'Slide Up' },
            { val: 'slide-down', label: 'Slide Down' },
            { val: 'slide-left', label: 'Slide Left' },
            { val: 'slide-right', label: 'Slide Right' },
            { val: 'slide-up-out', label: 'Slide Up Out' },
            { val: 'slide-down-out', label: 'Slide Down Out' },
            { val: 'slide-left-out', label: 'Slide Left Out' },
            { val: 'slide-right-out', label: 'Slide Right Out' }
        ]);
        wrapper.appendChild(typeGroup);

        // Duration (Range/Number)
        const durationGroup = this._createInputGroup('Süre (ms)', 'number', animData.duration, (val) => {
            animData.duration = parseInt(val);
            this._triggerUpdate();
        });
        wrapper.appendChild(durationGroup);

        // Delay (Range/Number)
        const delayGroup = this._createInputGroup('Gecikme (ms)', 'number', animData.delay, (val) => {
            animData.delay = parseInt(val);
            this._triggerUpdate();
        });
        wrapper.appendChild(delayGroup);

        container.appendChild(wrapper);
    }

    _createInputGroup(label, type, value, onChange, options = []) {
        const group = document.createElement('div');
        group.className = 'mb-2';
        
        const labelEl = document.createElement('label');
        labelEl.className = 'form-label small mb-1';
        labelEl.textContent = label;
        group.appendChild(labelEl);

        let input;
        if (type === 'select') {
            input = document.createElement('select');
            input.className = 'form-select form-select-sm';
            options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.val;
                option.textContent = opt.label;
                if (opt.val === value) option.selected = true;
                input.appendChild(option);
            });
        } else {
            input = document.createElement('input');
            input.type = type;
            input.className = 'form-control form-control-sm';
            input.value = value;
        }

        input.addEventListener('change', (e) => onChange(e.target.value));
        group.appendChild(input);

        return group;
    }

    _triggerUpdate() {
        if (this.onUpdate) {
            this.onUpdate(this.currentConfig);
        }
    }

    _formatComponentName(name) {
        const map = {
            'AlbumArtBackground': 'Arka Plan',
            'GradientOverlay': 'Gradyan Kaplama',
            'Cover': 'Albüm Kapağı',
            'TrackName': 'Şarkı Adı',
            'ArtistName': 'Sanatçı Adı',
            'ProgressBar': 'İlerleme Çubuğu',
            'CurrentTime': 'Şu Anki Süre',
            'TotalTime': 'Toplam Süre',
            'ProviderBadge': 'Logo'
        };
        return map[name] || name;
    }

    _formatAnimType(type) {
        const map = {
            'intro': 'Giriş (Intro)',
            'outro': 'Çıkış (Outro)',
            'transitionIn': 'Geçiş: Giriş',
            'transitionOut': 'Geçiş: Çıkış'
        };
        return map[type] || type;
    }

    _getDefaultConfig() {
        // Fallback structure based on user provided JSON
        return {
            "components": {
                "AlbumArtBackground": { "set_a": { "animations": {} }, "set_b": { "animations": {} } },
                "GradientOverlay": { "set_a": { "animations": {} }, "set_b": { "animations": {} } },
                "Cover": { "set_a": { "animations": {} }, "set_b": { "animations": {} } },
                "TrackName": { "set_a": { "animations": {} }, "set_b": { "animations": {} } },
                "ArtistName": { "set_a": { "animations": {} }, "set_b": { "animations": {} } },
                "ProgressBar": { "set_a": { "animations": {} }, "set_b": { "animations": {} } },
                "CurrentTime": { "set_a": { "animations": {} }, "set_b": { "animations": {} } },
                "TotalTime": { "set_a": { "animations": {} }, "set_b": { "animations": {} } },
                "ProviderBadge": { "set_a": { "animations": {} }, "set_b": { "animations": {} } }
            }
        };
    }

    /**
     * Preset seçildiğinde mevcut config üzerine uygular.
     * Basit ama öngörülebilir bir haritalama kullanıyoruz.
     */
    _applyPreset(presetId) {
        const components = this.currentConfig.components || {};
        const allComponentNames = Object.keys(components);
        const corePresets = window.WidgetPresets && window.WidgetPresets.core
            ? window.WidgetPresets.core
            : null;
        if (corePresets && corePresets.applyPresetToComponents) {
            corePresets.applyPresetToComponents(
                presetId,
                this.currentConfig.components,
                allComponentNames
            );
        }

        // Config değiştiğini bildir
        this._triggerUpdate();
        // Kompakt görünümde sadece preset kartlarını yeniden çizmek yeterli
        this._render();
    }

    /**
     * Mevcut config'ten tahmini preset türünü bulur.
     */
    _getCurrentPresetId() {
        const components = this.currentConfig && this.currentConfig.components
            ? this.currentConfig.components
            : {};
        const names = Object.keys(components);

        for (const name of names) {
            const comp = components[name];
            if (!comp || !comp.set_a || !comp.set_a.animations) continue;
            const anims = comp.set_a.animations;
            const detected = this._classifyPresetFromAnimations(anims);
            if (detected) return detected;
        }

        // Varsayılan: statik
        return 'static';
    }

    /**
     * Belirli bileşen listesine preset uygular (bölümler sekmesi için de kullanılır).
     */
    _applyPresetToComponents(presetId, componentNames) {
        const corePresets = window.WidgetPresets && window.WidgetPresets.core
            ? window.WidgetPresets.core
            : null;
        if (corePresets && corePresets.applyPresetToComponents) {
            corePresets.applyPresetToComponents(
                presetId,
                this.currentConfig.components || {},
                componentNames
            );
        }
    }


    /**
     * Animasyon setine göre preset id tahmini yapar.
     */
    _classifyPresetFromAnimations(anims = {}) {
        const corePresets = window.WidgetPresets && window.WidgetPresets.core
            ? window.WidgetPresets.core
            : null;
        if (corePresets && corePresets.classifyPresetFromAnimations) {
            return corePresets.classifyPresetFromAnimations(anims);
        }
        return null;
    }

    /**
     * Bölüm için tahmini preset türünü döndürür (ilk ilgili bileşene bakarak).
     */
    _getSectionPreset(section) {
        const components = this.currentConfig.components || {};
        for (const componentName of section.components) {
            const comp = components[componentName];
            if (!comp || !comp.set_a || !comp.set_a.animations || !comp.set_a.animations.intro) continue;
            const detected = this._classifyPresetFromAnimations(comp.set_a.animations);
            if (detected) return detected;
        }
        return 'static';
    }

    /**
     * Mantıksal bölümleri tanımlar (Arka Plan, İçerik, Zaman & İlerleme, Logo).
     */
    _getSectionsDefinition() {
        const baseSections = [
            {
                id: 'background',
                title: 'Arka Plan',
                description: 'Bulanık albüm kapağı ve gradyan arka plan.',
                components: ['AlbumArtBackground', 'GradientOverlay']
            },
            {
                id: 'content',
                title: 'İçerik',
                description: 'Albüm kapağı, şarkı adı ve sanatçı bilgisi.',
                components: ['Cover', 'TrackName', 'ArtistName']
            },
            {
                id: 'time',
                title: 'Zaman & İlerleme',
                description: 'İlerleme çubuğu ve süre göstergeleri.',
                components: ['ProgressBar', 'CurrentTime', 'TotalTime']
            },
            {
                id: 'branding',
                title: 'Logo',
                description: 'Spotify logosu ve marka alanı.',
                components: ['ProviderBadge']
            }
        ];

        const components = this.currentConfig.components || {};
        const allComponentNames = Object.keys(components);
        const used = new Set();

        const sections = baseSections
            .map(section => {
                const present = section.components.filter(name => {
                    if (components[name]) {
                        used.add(name);
                        return true;
                    }
                    return false;
                });
                return { ...section, components: present };
            })
            .filter(section => section.components.length > 0);

        const others = allComponentNames.filter(name => !used.has(name));
        if (others.length) {
            sections.push({
                id: 'other',
                title: 'Diğer',
                description: 'Diğer widget bileşenleri.',
                components: others
            });
        }

        return sections;
    }

    /**
     * Stüdyo matrisi içinde bir bölüm + durum için kısa özet metni döndürür.
     */
    _getSectionStateSummary(section, stateId) {
        const components = this.currentConfig.components || {};
        const stateToAnimTypes = {
            intro: ['intro'],
            transition: ['transitionIn', 'transitionOut'],
            outro: ['outro']
        };
        const animTypes = stateToAnimTypes[stateId] || ['intro'];

        for (const componentName of section.components) {
            const comp = components[componentName];
            if (!comp || !comp.set_a || !comp.set_a.animations) continue;

            for (const animType of animTypes) {
                const anim = comp.set_a.animations[animType];
                if (!anim) continue;
                const name = anim.animation || anim.type;
                if (!name || name === 'none') continue;

                if (name.startsWith('fade')) {
                    return 'Yumuşak';
                }
                return 'Dinamik';
            }
        }

        return 'Kapalı';
    }

    /**
     * Belirli bir bileşen + durum için sade animasyon tipini (fade / slide vb.) döndürür.
     * 2. adım (basit tablo) için kullanılır.
     */
    _getComponentStateSimpleType(componentName, stateId) {
        const components = this.currentConfig.components || {};
        const comp = components[componentName];
        if (!comp || !comp.set_a || !comp.set_a.animations) {
            return 'inherit';
        }

        const stateToAnimTypes = {
            intro: ['intro'],
            transition: ['transitionIn', 'transitionOut'],
            outro: ['outro']
        };
        const animTypes = stateToAnimTypes[stateId] || ['intro'];

        for (const animType of animTypes) {
            const anim = comp.set_a.animations[animType];
            if (!anim) continue;
            const name = anim.animation || anim.type;
            if (!name) continue;
            if (name === 'none') return 'none';
            if (name.includes('fade')) return 'fade';
            if (name.includes('left')) return 'slide-left';
            if (name.includes('right')) return 'slide-right';
            if (name.includes('up')) return 'slide-up';
            if (name.includes('down')) return 'slide-down';
        }

        return 'inherit';
    }

    /**
     * Belirli bir bileşen + durum için sade tip uygular (fade / slide vb.).
     * Sadece ilgili animasyon tiplerini (intro / transitionIn/Out / outro) günceller.
     */
    _applyComponentStateType(componentName, stateId, type) {
        const components = this.currentConfig.components || {};
        const comp = components[componentName];
        if (!comp) return;

        const stateToAnimTypes = {
            intro: ['intro'],
            transition: ['transitionIn', 'transitionOut'],
            outro: ['outro']
        };
        const animTypes = stateToAnimTypes[stateId] || ['intro'];

        ['set_a', 'set_b'].forEach(setKey => {
            const setData = comp[setKey];
            if (!setData) return;

            if (!setData.animations) {
                setData.animations = {};
            }

            animTypes.forEach(animType => {
                if (!setData.animations[animType]) {
                    setData.animations[animType] = { animation: 'none', duration: 0, delay: 0 };
                }

                const anim = setData.animations[animType];
                let animName = 'none';

                if (type === 'fade') {
                    animName = (animType === 'intro' || animType === 'transitionIn') ? 'fade-in' : 'fade-out';
                } else if (type === 'slide-left') {
                    animName = (animType === 'intro' || animType === 'transitionIn') ? 'slide-left' : 'slide-left-out';
                } else if (type === 'slide-right') {
                    animName = (animType === 'intro' || animType === 'transitionIn') ? 'slide-right' : 'slide-right-out';
                } else if (type === 'slide-up') {
                    animName = (animType === 'intro' || animType === 'transitionIn') ? 'slide-up' : 'slide-up-out';
                } else if (type === 'slide-down') {
                    animName = (animType === 'intro' || animType === 'transitionIn') ? 'slide-down' : 'slide-down-out';
                } else if (type === 'none') {
                    animName = 'none';
                }

                anim.animation = animName;
                anim.type = animName;
            });
        });

        this._triggerUpdate();
        this._renderActiveTab();
    }

    /**
     * 3. adım tablosu için: bileşen + durum için ham config animasyon isimlerini döndürür.
     */
    _getComponentStateRawLabel(componentName, stateId) {
        const components = this.currentConfig.components || {};
        const comp = components[componentName];
        if (!comp || !comp.set_a || !comp.set_a.animations) {
            return '-';
        }

        const stateToAnimTypes = {
            intro: ['intro'],
            transition: ['transitionIn', 'transitionOut'],
            outro: ['outro']
        };
        const animTypes = stateToAnimTypes[stateId] || ['intro'];

        const names = [];
        animTypes.forEach(animType => {
            const anim = comp.set_a.animations[animType];
            if (!anim) return;
            const name = anim.animation || anim.type;
            if (!name) return;
            names.push(name);
        });

        if (!names.length) return '-';
        return names.join(' / ');
    }

    /**
     * Stüdyo modali açar: seçilen bileşen + durum için tüm ilgili animasyonları düzenler.
     */
    _openStudioModal(componentName, stateId) {
        this._closeStudioModal();

        const backdrop = document.createElement('div');
        backdrop.className = 'studio-modal-backdrop';

        const modal = document.createElement('div');
        modal.className = 'studio-modal';

        const stateLabels = {
            intro: 'Giriş',
            transition: 'Geçiş',
            outro: 'Çıkış'
        };

        const header = document.createElement('div');
        header.className = 'studio-modal-header';
        header.innerHTML = `
            <h6 class="mb-0">${this._formatComponentName(componentName)} · ${stateLabels[stateId] || ''}</h6>
        `;

        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'studio-modal-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', () => this._closeStudioModal());
        header.appendChild(closeBtn);

        const body = document.createElement('div');
        body.className = 'studio-modal-body';
        this._renderStudioComponentStateEditor(body, componentName, stateId);

        const footer = document.createElement('div');
        footer.className = 'studio-modal-footer';
        const closeFooterBtn = document.createElement('button');
        closeFooterBtn.type = 'button';
        closeFooterBtn.className = 'btn btn-sm btn-secondary';
        closeFooterBtn.textContent = 'Kapat';
        closeFooterBtn.addEventListener('click', () => this._closeStudioModal());
        footer.appendChild(closeFooterBtn);

        modal.appendChild(header);
        modal.appendChild(body);
        modal.appendChild(footer);

        backdrop.appendChild(modal);

        backdrop.addEventListener('click', (e) => {
            if (e.target === backdrop) {
                this._closeStudioModal();
            }
        });

        this.container.appendChild(backdrop);
        this.studioModalEl = backdrop;
    }

    _closeStudioModal() {
        if (this.studioModalEl && this.studioModalEl.parentNode) {
            this.studioModalEl.parentNode.removeChild(this.studioModalEl);
        }
        this.studioModalEl = null;
    }

    /**
     * Bir bileşenin (sınıfın) temel animasyon tipini tahmin eder.
     */
    _getComponentBaseType(componentName) {
        const components = this.currentConfig.components || {};
        const comp = components[componentName];
        if (!comp || !comp.set_a || !comp.set_a.animations || !comp.set_a.animations.intro) {
            return 'fade';
        }

        const anim = comp.set_a.animations.intro;
        const name = anim.animation || anim.type;
        if (!name) return 'fade';
        if (name === 'none') return 'none';
        if (name.startsWith('fade')) return 'fade';
        if (name.indexOf('left') !== -1) return 'slide-left';
        if (name.indexOf('right') !== -1) return 'slide-right';
        if (name.indexOf('up') !== -1) return 'slide-up';
        if (name.indexOf('down') !== -1) return 'slide-down';
        return 'fade';
    }

    /**
     * Belirli bir bileşenin tüm animasyon tiplerine (intro, transition, outro)
     * verilen genel animasyon tipini uygular. Süre ve gecikme değerleri korunur.
     */
    _applyComponentType(componentName, type) {
        const components = this.currentConfig.components || {};
        const comp = components[componentName];
        if (!comp) return;

        const animTypes = ['intro', 'transitionIn', 'transitionOut', 'outro'];

        ['set_a', 'set_b'].forEach(setKey => {
            const setData = comp[setKey];
            if (!setData) return;

            if (!setData.animations) {
                setData.animations = {};
            }

            animTypes.forEach(animType => {
                if (!setData.animations[animType]) {
                    setData.animations[animType] = { animation: 'none', duration: 0, delay: 0 };
                }

                const anim = setData.animations[animType];
                let animName = 'none';

                if (type === 'fade') {
                    animName = (animType === 'intro' || animType === 'transitionIn') ? 'fade-in' : 'fade-out';
                } else if (type === 'slide-left') {
                    animName = (animType === 'intro' || animType === 'transitionIn') ? 'slide-left' : 'slide-left-out';
                } else if (type === 'slide-right') {
                    animName = (animType === 'intro' || animType === 'transitionIn') ? 'slide-right' : 'slide-right-out';
                } else if (type === 'slide-up') {
                    animName = (animType === 'intro' || animType === 'transitionIn') ? 'slide-up' : 'slide-up-out';
                } else if (type === 'slide-down') {
                    animName = (animType === 'intro' || animType === 'transitionIn') ? 'slide-down' : 'slide-down-out';
                } else if (type === 'none') {
                    animName = 'none';
                }

                anim.animation = animName;
                anim.type = animName;
            });
        });

        this._triggerUpdate();
        this._renderActiveTab();
    }
}

