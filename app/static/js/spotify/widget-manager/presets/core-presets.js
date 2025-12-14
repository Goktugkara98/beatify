;(function (window) {
    // Temel preset katalogları (fade dışındaki kategoriler)
    const BASE_PRESET_CATALOG = {
        general: [
            {
                id: 'static',
                title: 'Statik',
                description: 'Animasyonları minimuma indirir, anında ve sakin.'
            },
            {
                id: 'mellow-fade',
                title: 'Yumuşak Fade',
                description: 'Dengeli fade zinciri (legacy). Teknik olarak `fade-soft` ile aynı davranır.'
            },
            {
                id: 'gentle-slide',
                title: 'Nazik Kayma',
                description: 'Yukarıdan hafif giriş, fade kapanış.'
            },
            {
                id: 'pop-spot',
                title: 'Pop Sahne',
                description: 'Aşağıdan giriş, hafif fade geçiş, yukarı çıkış.'
            }
        ],
        slide: [
            {
                id: 'slide-left',
                title: 'Sola Kayma',
                description: 'Sağdan giriş, sola çıkış; yatay hareket.'
            },
            {
                id: 'slide-up',
                title: 'Yukarı Kayma',
                description: 'Aşağıdan giriş, yukarı çıkış; dikey vurgu.'
            },
            {
                id: 'slide-down',
                title: 'Aşağı Kayma',
                description: 'Yukarıdan giriş, aşağı çıkış; ters dikey hareket.'
            },
            {
                id: 'slide-right',
                title: 'Sağa Kayma',
                description: 'Soldan giriş, sağa çıkış; yatay hareket.'
            },
            {
                id: 'slide-smooth',
                title: 'Akışkan Katmanlar',
                description: 'Katmanlar farklı yönlerden akışkan gelir; daha yumuşak slide geçişler.'
            },
            {
                id: 'slide-burst',
                title: 'Hızlı Kayma',
                description: 'Kısa, hızlı ve vurucu slide kombinasyonu.'
            }
        ],
        hybrid: [
            {
                id: 'spotlight',
                title: 'Spotlight',
                description: 'Aşağıdan sahneye giriş, fade geçiş, yukarı kapanış.'
            },
            {
                id: 'drift',
                title: 'Drift Mix',
                description: 'Slide + fade karışımı; yumuşak hareket.'
            },
            {
                id: 'parallax',
                title: 'Parallax',
                description: 'Aşağı giriş, sola geçiş, yukarı çıkış; katmanlı his.'
            },
            {
                id: 'burst-mix',
                title: 'Burst Mix',
                description: 'Hızlı slide + kısa fade kombinasyonu.'
            }
        ]
    };

    // Preset önizleme sınıfları – widget manager ve settings paneli ortak kullanır
    const PRESET_PREVIEW_CLASS_MAP = {
        static: 'preset-static-preview',
        'mellow-fade': 'preset-fade-preview',
        'gentle-slide': 'preset-slide-preview',
        'pop-spot': 'preset-spotlight-preview',

        // Fade presetleri
        'fade-soft': 'preset-fade-preview',
        'fade-long': 'preset-fade-preview',
        'fade-pulse': 'preset-fade-preview',
        'fade-stagger': 'preset-fade-preview',
        'fade-text-first': 'preset-fade-preview',
        'fade-subtle': 'preset-fade-preview',

        // Slide presetleri
        'slide-left': 'preset-slide-preview',
        'slide-up': 'preset-slide-preview',
        'slide-down': 'preset-slide-preview',
        'slide-right': 'preset-slide-preview',
        'slide-smooth': 'preset-slide-preview',
        'slide-burst': 'preset-burst-preview',

        // Zoom presetleri
        'zoom-soft': 'preset-zoom-preview',
        'zoom-cinematic': 'preset-zoom-preview',
        'zoom-pop': 'preset-zoom-preview',
        'zoom-focus-cover': 'preset-zoom-preview',
        'zoom-focus-text': 'preset-zoom-preview',
        'zoom-subtle': 'preset-zoom-preview',

        // Blur presetleri
        'blur-soft': 'preset-blur-preview',
        'blur-cinematic': 'preset-blur-preview',
        'blur-quick': 'preset-blur-preview',
        'blur-text-focus': 'preset-blur-preview',
        'blur-bg-focus': 'preset-blur-preview',
        'blur-subtle': 'preset-blur-preview',

        // Reveal presetleri
        'reveal-clip-up': 'preset-reveal-preview',
        'reveal-clip-left': 'preset-reveal-preview',
        'reveal-underline': 'preset-reveal-preview',
        'reveal-tilt': 'preset-reveal-preview',
        'reveal-float': 'preset-reveal-preview',
        'reveal-mix': 'preset-reveal-preview',

        // Karma / spotlight presetleri
        spotlight: 'preset-spotlight-preview',
        drift: 'preset-spotlight-preview',
        parallax: 'preset-spotlight-preview',
        'burst-mix': 'preset-burst-preview'
    };

    function getPresetCatalog(category) {
        if (category === 'fade') {
            const fadeHelper =
                window.WidgetPresets &&
                window.WidgetPresets.fade &&
                window.WidgetPresets.fade.getFadeCatalog;

            return (fadeHelper && window.WidgetPresets.fade.getFadeCatalog()) || [];
        }

        if (category === 'slide') {
            const slideHelper =
                window.WidgetPresets &&
                window.WidgetPresets.slide &&
                window.WidgetPresets.slide.getSlideCatalog;

            // Slide presetleri artık helper'dan geliyor; yoksa BASE catalog fallback.
            return (slideHelper && window.WidgetPresets.slide.getSlideCatalog()) || (BASE_PRESET_CATALOG.slide || []).slice();
        }

        if (category === 'zoom') {
            const zoomHelper =
                window.WidgetPresets &&
                window.WidgetPresets.zoom &&
                window.WidgetPresets.zoom.getZoomCatalog;
            return (zoomHelper && window.WidgetPresets.zoom.getZoomCatalog()) || [];
        }

        if (category === 'blur') {
            const blurHelper =
                window.WidgetPresets &&
                window.WidgetPresets.blur &&
                window.WidgetPresets.blur.getBlurCatalog;
            return (blurHelper && window.WidgetPresets.blur.getBlurCatalog()) || [];
        }

        if (category === 'reveal') {
            const revealHelper =
                window.WidgetPresets &&
                window.WidgetPresets.reveal &&
                window.WidgetPresets.reveal.getRevealCatalog;
            return (revealHelper && window.WidgetPresets.reveal.getRevealCatalog()) || [];
        }

        const base = BASE_PRESET_CATALOG[category];
        if (Array.isArray(base)) {
            return base.slice();
        }
        // Varsayılan: general
        return BASE_PRESET_CATALOG.general.slice();
    }

    function getPresetPreviewClass(presetId) {
        return PRESET_PREVIEW_CLASS_MAP[presetId] || null;
    }

    function getAllPreviewClasses() {
        const values = Object.values(PRESET_PREVIEW_CLASS_MAP);
        return Array.from(new Set(values));
    }

    /**
     * Animasyon setine göre preset id tahmini yapar.
     * ThemeSettingsService ve main.js ile paylaşılan mantık.
     */
    function classifyPresetFromAnimations(anims) {
        const data = anims || {};

        const normalize = (obj) => {
            if (!obj) return { name: '', duration: 0, delay: 0 };
            const name = (obj.animation || obj.type || '').toLowerCase();
            const duration = typeof obj.duration === 'number' ? obj.duration : 0;
            const delay = typeof obj.delay === 'number' ? obj.delay : 0;
            return { name, duration, delay };
        };

        const intro = normalize(data.intro);
        const transitionIn = normalize(data.transitionIn);
        const transitionOut = normalize(data.transitionOut);
        const outro = normalize(data.outro);

        // Eğer UI üzerinden preset uygulanmışsa, doğrudan presetId'yi kullan
        const directPreset =
            (data.intro && data.intro.presetId) ||
            (data.transitionIn && data.transitionIn.presetId) ||
            (data.transitionOut && data.transitionOut.presetId) ||
            (data.outro && data.outro.presetId);
        if (directPreset) {
            return directPreset;
        }

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
            const spotlightLike =
                intro.name === 'slide-down' &&
                outro.name === 'slide-up-out' &&
                transitionIn.name.startsWith('fade');
            if (spotlightLike) {
                if (intro.duration < 760) return 'pop-spot';
                return 'spotlight';
            }

            const driftLike =
                intro.name === 'slide-left' && transitionIn.name.startsWith('fade');
            if (driftLike) return 'drift';

            const fastSlide = intro.duration && intro.duration <= 540;
            if (fastSlide) return 'slide-burst';

            if (intro.name === 'slide-left') return 'slide-left';
            if (intro.name === 'slide-right') return 'slide-right';
            if (intro.name === 'slide-up') return 'slide-up';
            if (intro.name === 'slide-down') return 'parallax';
        }

        // Karma hızlı mix tespiti
        if (
            intro.name &&
            transitionIn.name.startsWith('fade') &&
            outro.name.startsWith('slide')
        ) {
            return 'burst-mix';
        }

        // Varsayılan fallback
        return 'gentle-slide';
    }

    /**
     * Config içindeki bileşenlere preset uygular.
     * ThemeSettingsService._applyPresetToComponents fonksiyonunun paylaşılan versiyonu.
     */
    function applyPresetToComponents(presetId, components, componentNames) {
        if (!components) return;

        const ensureAnimationContainer = (componentName, setKey, setData) => {
            if (!setData) return;
            if (setData.animationContainer) return;

            const setLetter = setKey === 'set_a' ? 'a' : 'b';
            const map = {
                AlbumArtBackground: `AlbumArtBackgroundAnimationContainer_${setLetter}`,
                GradientOverlay: `GradientOverlayAnimationContainer_${setLetter}`,
                Cover: `CoverAnimationContainer_${setLetter}`,
                TrackName: `TrackNameAnimationContainer_${setLetter}`,
                ArtistName: `ArtistNameAnimationContainer_${setLetter}`,
                ProgressBar: `ProgressBarAnimationContainer_${setLetter}`,
                CurrentTime: `CurrentTimeAnimationContainer_${setLetter}`,
                TotalTime: `TotalTimeAnimationContainer_${setLetter}`,
                ProviderBadge: `ProviderBadgeAnimationContainer_${setLetter}`,
                // Özel: bu component’in container’ı layout container olarak geçiyor
                TimeDisplay: `TimeDisplayLayoutContainer_${setLetter}`
            };

            if (map[componentName]) {
                setData.animationContainer = map[componentName];
            }
        };

        const fadeHelper =
            (window.WidgetPresets && window.WidgetPresets.fade) || null;
        const slideHelper =
            (window.WidgetPresets && window.WidgetPresets.slide) || null;
        const zoomHelper =
            (window.WidgetPresets && window.WidgetPresets.zoom) || null;
        const blurHelper =
            (window.WidgetPresets && window.WidgetPresets.blur) || null;
        const revealHelper =
            (window.WidgetPresets && window.WidgetPresets.reveal) || null;

        const names =
            (Array.isArray(componentNames) && componentNames.length
                ? componentNames
                : Object.keys(components)) || [];

        names.forEach((componentName) => {
            if (!components[componentName]) return;
            const comp = components[componentName];

            ['set_a', 'set_b'].forEach((setKey) => {
                const setData = comp[setKey];
                if (!setData) return;

                if (!setData.animations) {
                    setData.animations = {};
                }

                // Eski/eksik config’lerde ArtistName gibi bileşenler animasyonsuz kalmasın:
                // Animation service, element’i bulmak için animationContainer’a ihtiyaç duyuyor.
                ensureAnimationContainer(componentName, setKey, setData);

                const animTypes = ['intro', 'transitionIn', 'transitionOut', 'outro'];

                animTypes.forEach((animType) => {
                    if (!setData.animations[animType]) {
                        setData.animations[animType] = {
                            animation: 'none',
                            duration: 0,
                            delay: 0
                        };
                    }

                    const anim = setData.animations[animType];

                    // Hangi presetten geldiğini işaretle – tespit için
                    anim.presetId = presetId;

                    if (presetId === 'static') {
                        // Tüm animasyonları devre dışı bırak
                        anim.animation = 'none';
                        anim.type = 'none';
                        anim.duration = 0;
                        anim.delay = 0;
                    } else if (
                        fadeHelper &&
                        fadeHelper.isFadePreset &&
                        fadeHelper.isFadePreset(presetId)
                    ) {
                        fadeHelper.applyFadePreset(
                            presetId,
                            animType,
                            anim,
                            componentName
                        );
                    } else if (
                        slideHelper &&
                        slideHelper.isSlidePreset &&
                        slideHelper.isSlidePreset(presetId)
                    ) {
                        slideHelper.applySlidePreset(
                            presetId,
                            animType,
                            anim,
                            componentName
                        );
                    } else if (
                        zoomHelper &&
                        zoomHelper.isZoomPreset &&
                        zoomHelper.isZoomPreset(presetId)
                    ) {
                        zoomHelper.applyZoomPreset(
                            presetId,
                            animType,
                            anim,
                            componentName
                        );
                    } else if (
                        blurHelper &&
                        blurHelper.isBlurPreset &&
                        blurHelper.isBlurPreset(presetId)
                    ) {
                        blurHelper.applyBlurPreset(
                            presetId,
                            animType,
                            anim,
                            componentName
                        );
                    } else if (
                        revealHelper &&
                        revealHelper.isRevealPreset &&
                        revealHelper.isRevealPreset(presetId)
                    ) {
                        revealHelper.applyRevealPreset(
                            presetId,
                            animType,
                            anim,
                            componentName
                        );
                    } else if (presetId === 'gentle-slide') {
                        if (animType === 'intro') {
                            anim.animation = 'slide-up';
                            anim.type = 'slide-up';
                            anim.duration = 820;
                            anim.delay = 80;
                        } else if (animType === 'transitionIn') {
                            anim.animation = 'fade-in';
                            anim.type = 'fade-in';
                            anim.duration = 700;
                            anim.delay = 80;
                        } else if (animType === 'transitionOut') {
                            anim.animation = 'fade-out';
                            anim.type = 'fade-out';
                            anim.duration = 680;
                            anim.delay = 80;
                        } else {
                            anim.animation = 'fade-out';
                            anim.type = 'fade-out';
                            anim.duration = 680;
                            anim.delay = 60;
                        }
                    } else if (presetId === 'pop-spot') {
                        if (animType === 'intro') {
                            anim.animation = 'slide-down';
                            anim.type = 'slide-down';
                            anim.duration = 720;
                            anim.delay = 60;
                        } else if (animType === 'transitionIn') {
                            anim.animation = 'fade-in';
                            anim.type = 'fade-in';
                            anim.duration = 600;
                            anim.delay = 100;
                        } else if (animType === 'transitionOut') {
                            anim.animation = 'fade-out';
                            anim.type = 'fade-out';
                            anim.duration = 580;
                            anim.delay = 100;
                        } else {
                            anim.animation = 'slide-up-out';
                            anim.type = 'slide-up-out';
                            anim.duration = 650;
                            anim.delay = 120;
                        }
                    } else if (presetId === 'spotlight') {
                        // Sahne etkisi
                        if (animType === 'intro') {
                            anim.animation = 'slide-down';
                            anim.type = 'slide-down';
                            anim.duration = 780;
                            anim.delay = 80;
                        } else if (animType === 'transitionIn') {
                            anim.animation = 'fade-in';
                            anim.type = 'fade-in';
                            anim.duration = 600;
                            anim.delay = 120;
                        } else if (animType === 'transitionOut') {
                            anim.animation = 'fade-out';
                            anim.type = 'fade-out';
                            anim.duration = 580;
                            anim.delay = 140;
                        } else {
                            anim.animation = 'slide-up-out';
                            anim.type = 'slide-up-out';
                            anim.duration = 700;
                            anim.delay = 120;
                        }
                    } else if (presetId === 'drift') {
                        if (animType === 'intro') {
                            anim.animation = 'slide-left';
                            anim.type = 'slide-left';
                            anim.duration = 700;
                            anim.delay = 80;
                        } else if (animType === 'transitionIn') {
                            anim.animation = 'fade-in';
                            anim.type = 'fade-in';
                            anim.duration = 620;
                            anim.delay = 120;
                        } else if (animType === 'transitionOut') {
                            anim.animation = 'fade-out';
                            anim.type = 'fade-out';
                            anim.duration = 600;
                            anim.delay = 140;
                        } else {
                            anim.animation = 'slide-left-out';
                            anim.type = 'slide-left-out';
                            anim.duration = 680;
                            anim.delay = 120;
                        }
                    } else if (presetId === 'parallax') {
                        if (animType === 'intro') {
                            anim.animation = 'slide-down';
                            anim.type = 'slide-down';
                            anim.duration = 760;
                            anim.delay = 70;
                        } else if (animType === 'transitionIn') {
                            anim.animation = 'slide-left';
                            anim.type = 'slide-left';
                            anim.duration = 700;
                            anim.delay = 90;
                        } else if (animType === 'transitionOut') {
                            anim.animation = 'slide-right-out';
                            anim.type = 'slide-right-out';
                            anim.duration = 680;
                            anim.delay = 90;
                        } else {
                            anim.animation = 'slide-up-out';
                            anim.type = 'slide-up-out';
                            anim.duration = 700;
                            anim.delay = 110;
                        }
                    } else if (presetId === 'burst-mix') {
                        if (animType === 'intro') {
                            anim.animation = 'slide-up';
                            anim.type = 'slide-up';
                            anim.duration = 500;
                            anim.delay = 0;
                        } else if (animType === 'transitionIn') {
                            anim.animation = 'fade-in';
                            anim.type = 'fade-in';
                            anim.duration = 520;
                            anim.delay = 40;
                        } else if (animType === 'transitionOut') {
                            anim.animation = 'fade-out';
                            anim.type = 'fade-out';
                            anim.duration = 500;
                            anim.delay = 60;
                        } else {
                            anim.animation = 'slide-up-out';
                            anim.type = 'slide-up-out';
                            anim.duration = 520;
                            anim.delay = 80;
                        }
                    }
                });
            });
        });
    }

    function getPresetIdFromConfig(fullConfig) {
        const components =
            fullConfig && fullConfig.components ? fullConfig.components : {};
        const names = Object.keys(components);

        for (const name of names) {
            const comp = components[name];
            if (!comp || !comp.set_a || !comp.set_a.animations) continue;
            const detected = classifyPresetFromAnimations(comp.set_a.animations);
            if (detected) return detected;
        }

        // Varsayılan: gentle-slide
        return 'gentle-slide';
    }

    window.WidgetPresets = window.WidgetPresets || {};
    window.WidgetPresets.core = {
        getPresetCatalog,
        getPresetPreviewClass,
        getAllPreviewClasses,
        classifyPresetFromAnimations,
        applyPresetToComponents,
        getPresetIdFromConfig
    };
})(window);


