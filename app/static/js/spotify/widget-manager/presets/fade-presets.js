(function(window) {
    const fadeOrderMap = {
        AlbumArtBackground: 0,
        GradientOverlay: 1,
        Cover: 2,
        TrackName: 3,
        ArtistName: 4,
        ProgressBar: 5,
        CurrentTime: 6,
        TotalTime: 7,
        ProviderBadge: 8
    };

    const FADE_PRESET_IDS = [
        'fade-soft',
        'fade-long',
        'fade-pulse',
        'fade-stagger',
        'fade-text-first',
        'fade-subtle'
    ];

    // Geriye dönük uyumluluk: eski preset id -> yeni id
    const FADE_PRESET_ALIASES = {
        'mellow-fade': 'fade-soft'
    };

    // Bazı presetler sadece fade olmasına rağmen farklı bir "sahne sırası" ister.
    // Buradaki değerler, spacing ile çarpılıp delay üretmekte kullanılır.
    const fadeOrderOverrides = {
        'fade-text-first': {
            AlbumArtBackground: 0,
            GradientOverlay: 1,
            Cover: 2,
            ProgressBar: 3,
            CurrentTime: 4,
            TotalTime: 5,
            ProviderBadge: 6,
            // İstek: text önce değil sonra olsun (text en son gelsin)
            TrackName: 7,
            ArtistName: 8
        },
        'fade-pulse': {
            // "Pulse" hissi: önce temel içerik/cover/controls, arka plan/overlay daha sonra gelir.
            // Text yine en sonlara yakın (ilk değil).
            Cover: 0,
            ProgressBar: 1,
            CurrentTime: 2,
            TotalTime: 3,
            ProviderBadge: 4,
            AlbumArtBackground: 5,
            GradientOverlay: 6,
            TrackName: 7,
            ArtistName: 8
        }
    };

    const fadeConfigs = {
        'fade-soft': {
            intro:        { duration: 900,  spacing: 80, maxDelay: 640, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionIn: { duration: 720,  spacing: 70, maxDelay: 560, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionOut:{ duration: 680,  spacing: 55, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' },
            outro:        { duration: 820,  spacing: 70, maxDelay: 560, easeIn: 'power2.out', easeOut: 'power2.in' },
        },
        'fade-long': {
            intro:        { duration: 1300, spacing: 110, maxDelay: 900, easeIn: 'sine.out', easeOut: 'sine.in' },
            transitionIn: { duration: 1200, spacing: 100, maxDelay: 850, easeIn: 'sine.out', easeOut: 'sine.in' },
            transitionOut:{ duration: 1100, spacing: 90,  maxDelay: 800, easeIn: 'sine.out', easeOut: 'sine.in' },
            outro:        { duration: 1300, spacing: 110, maxDelay: 900, easeIn: 'sine.out', easeOut: 'sine.in' },
        },
        'fade-pulse': {
            intro:        { duration: 650,  spacing: 70, maxDelay: 480, easeIn: 'expo.out', easeOut: 'expo.in' },
            transitionIn: { duration: 580,  spacing: 60, maxDelay: 420, easeIn: 'expo.out', easeOut: 'expo.in' },
            transitionOut:{ duration: 540,  spacing: 55, maxDelay: 380, easeIn: 'expo.out', easeOut: 'expo.in' },
            outro:        { duration: 580,  spacing: 70, maxDelay: 480, easeIn: 'expo.out', easeOut: 'expo.in' },
        },
        'fade-stagger': {
            intro:        { duration: 800,  spacing: 130, maxDelay: 900, easeIn: 'power3.out', easeOut: 'power3.in' },
            transitionIn: { duration: 720,  spacing: 110, maxDelay: 800, easeIn: 'power3.out', easeOut: 'power3.in' },
            transitionOut:{ duration: 720,  spacing: 110, maxDelay: 800, easeIn: 'power3.out', easeOut: 'power3.in' },
            outro:        { duration: 820,  spacing: 130, maxDelay: 900, easeIn: 'power3.out', easeOut: 'power3.in' },
        },
        'fade-text-first': {
            intro:        { duration: 820,  spacing: 85,  maxDelay: 650, easeIn: 'sine.out', easeOut: 'sine.in', roleEaseOverrides: { text: 'power4.out', time: 'power4.out' } },
            transitionIn: { duration: 760,  spacing: 80,  maxDelay: 620, easeIn: 'sine.out', easeOut: 'sine.in', roleEaseOverrides: { text: 'power4.out', time: 'power4.out' } },
            transitionOut:{ duration: 720,  spacing: 80,  maxDelay: 580, easeIn: 'sine.out', easeOut: 'sine.in', roleEaseOverrides: { text: 'power4.in', time: 'power4.in' } },
            outro:        { duration: 760,  spacing: 85,  maxDelay: 650, easeIn: 'sine.out', easeOut: 'sine.in', roleEaseOverrides: { text: 'power4.in', time: 'power4.in' } },
        },
        'fade-subtle': {
            // "Subtle" hissi: herkes fade kullanır ama arka plan/overlay daha belirgin,
            // diğerleri çok kısa süreyle neredeyse anlık görünür/kapanır.
            intro: {
                duration: 650,
                spacing: 30,
                maxDelay: 260,
                easeIn: 'linear',
                easeOut: 'linear',
                roleDurationMultipliers: {
                    background: 1,
                    overlay: 0.95,
                    cover: 0.25,
                    text: 0.25,
                    time: 0.22,
                    bar: 0.22,
                    badge: 0.25,
                    other: 0.25
                },
                roleOpacity: {
                    // Arka plan belirgin; diğerleri "yumuşakça var" gibi başlar.
                    background: { from: 0, to: 1 },
                    overlay: { from: 0, to: 1 },
                    cover: { from: 0.55, to: 1 },
                    text: { from: 0.55, to: 1 },
                    time: { from: 0.55, to: 1 },
                    bar: { from: 0.55, to: 1 },
                    badge: { from: 0.55, to: 1 },
                    other: { from: 0.55, to: 1 }
                }
            },
            transitionIn: {
                duration: 580,
                spacing: 25,
                maxDelay: 240,
                easeIn: 'linear',
                easeOut: 'linear',
                roleDurationMultipliers: {
                    background: 1,
                    overlay: 0.95,
                    cover: 0.25,
                    text: 0.25,
                    time: 0.22,
                    bar: 0.22,
                    badge: 0.25,
                    other: 0.25
                },
                roleOpacity: {
                    background: { from: 0, to: 1 },
                    overlay: { from: 0, to: 1 },
                    cover: { from: 0.55, to: 1 },
                    text: { from: 0.55, to: 1 },
                    time: { from: 0.55, to: 1 },
                    bar: { from: 0.55, to: 1 },
                    badge: { from: 0.55, to: 1 },
                    other: { from: 0.55, to: 1 }
                }
            },
            transitionOut: {
                duration: 560,
                spacing: 25,
                maxDelay: 240,
                easeIn: 'linear',
                easeOut: 'linear',
                roleDurationMultipliers: {
                    background: 1,
                    overlay: 0.95,
                    cover: 0.25,
                    text: 0.25,
                    time: 0.22,
                    bar: 0.22,
                    badge: 0.25,
                    other: 0.25
                },
                roleOpacity: {
                    // Çıkışta hepsi gerçekten kaybolsun
                    background: { to: 0 },
                    overlay: { to: 0 },
                    cover: { to: 0 },
                    text: { to: 0 },
                    time: { to: 0 },
                    bar: { to: 0 },
                    badge: { to: 0 },
                    other: { to: 0 }
                }
            },
            outro: {
                duration: 620,
                spacing: 30,
                maxDelay: 260,
                easeIn: 'linear',
                easeOut: 'linear',
                roleDurationMultipliers: {
                    background: 1,
                    overlay: 0.95,
                    cover: 0.25,
                    text: 0.25,
                    time: 0.22,
                    bar: 0.22,
                    badge: 0.25,
                    other: 0.25
                },
                roleOpacity: {
                    background: { to: 0 },
                    overlay: { to: 0 },
                    cover: { to: 0 },
                    text: { to: 0 },
                    time: { to: 0 },
                    bar: { to: 0 },
                    badge: { to: 0 },
                    other: { to: 0 }
                }
            }
        }
    };

    const fadeRoleAnimations = {
        // Tamamen fade tabanlı presetler: sadece fade-in / fade-out kullanılır.
        'fade-soft': {
            intro: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionIn: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionOut: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            },
            outro: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            }
        },
        'fade-long': {
            intro: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionIn: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionOut: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            },
            outro: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            }
        },
        'fade-pulse': {
            intro: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionIn: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionOut: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            },
            outro: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            }
        },
        'fade-stagger': {
            intro: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionIn: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionOut: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            },
            outro: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            }
        },
        'fade-text-first': {
            intro: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionIn: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionOut: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            },
            outro: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            }
        },
        'fade-subtle': {
            intro: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionIn: {
                background: 'fade-in',
                overlay:    'fade-in',
                cover:      'fade-in',
                text:       'fade-in',
                time:       'fade-in',
                bar:        'fade-in',
                badge:      'fade-in',
                other:      'fade-in',
            },
            transitionOut: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            },
            outro: {
                background: 'fade-out',
                overlay:    'fade-out',
                cover:      'fade-out',
                text:       'fade-out',
                time:       'fade-out',
                bar:        'fade-out',
                badge:      'fade-out',
                other:      'fade-out',
            }
        }
    };

    function isFadePreset(presetId) {
        if (!presetId) return false;
        if (FADE_PRESET_IDS.includes(presetId)) return true;
        return Boolean(FADE_PRESET_ALIASES[presetId]);
    }

    function normalizeFadePresetId(presetId) {
        return FADE_PRESET_ALIASES[presetId] || presetId;
    }

    function applyFadePreset(presetId, animType, anim, componentName) {
        if (!isFadePreset(presetId)) return false;
        const normalizedPresetId = normalizeFadePresetId(presetId);

        const config = fadeConfigs[normalizedPresetId] || fadeConfigs['fade-soft'];
        const animCfg = config[animType];
        if (!animCfg) return false;

        const role = (() => {
            switch (componentName) {
                case 'AlbumArtBackground': return 'background';
                case 'GradientOverlay':    return 'overlay';
                case 'Cover':              return 'cover';
                case 'TrackName':
                case 'ArtistName':         return 'text';
                case 'ProgressBar':        return 'bar';
                case 'CurrentTime':
                case 'TotalTime':          return 'time';
                case 'ProviderBadge':      return 'badge';
                default:                   return 'other';
            }
        })();

        const isEntrance = (animType === 'intro' || animType === 'transitionIn');
        const baseName = isEntrance ? 'fade-in' : 'fade-out';

        const presetRoles = fadeRoleAnimations[normalizedPresetId] || fadeRoleAnimations['fade-soft'];
        const phaseRoles = presetRoles[animType] || presetRoles['intro'];
        const advancedType = (phaseRoles && phaseRoles[role]) || baseName;

        anim.animation = baseName;
        anim.type = advancedType;

        const baseDuration = typeof animCfg.duration === 'number' ? animCfg.duration : 0;
        const mult =
            animCfg.roleDurationMultipliers &&
            typeof animCfg.roleDurationMultipliers[role] === 'number'
                ? animCfg.roleDurationMultipliers[role]
                : 1;
        const computedDuration = Math.max(60, Math.round(baseDuration * mult));
        anim.duration = computedDuration;

        // Ease: sadece fade olmasına rağmen presetleri farklı hissettiren ana parametre.
        const defaultEase = isEntrance ? (animCfg.easeIn || 'power2.out') : (animCfg.easeOut || 'power2.in');
        const roleEase =
            animCfg.roleEaseOverrides && typeof animCfg.roleEaseOverrides[role] === 'string'
                ? animCfg.roleEaseOverrides[role]
                : null;
        anim.ease = roleEase || defaultEase;

        // (Opsiyonel) Opacity aralığı – sadece fade, ama daha "subtle" his için.
        if (animCfg.roleOpacity && animCfg.roleOpacity[role]) {
            const ro = animCfg.roleOpacity[role];
            if (typeof ro.from === 'number') anim.fromOpacity = ro.from;
            if (typeof ro.to === 'number') anim.toOpacity = ro.to;
        } else {
            // Varsayılanları temizle ki başka preset'ten kalmasın
            delete anim.fromOpacity;
            delete anim.toOpacity;
        }

        const spacing = animCfg.spacing || 0;
        const overrideOrderMap = fadeOrderOverrides[normalizedPresetId] || null;
        const orderIdx = overrideOrderMap && typeof overrideOrderMap[componentName] === 'number'
            ? overrideOrderMap[componentName]
            : (typeof fadeOrderMap[componentName] === 'number' ? fadeOrderMap[componentName] : 4);
        const rawDelay = Math.max(0, orderIdx) * spacing;
        const maxDelay = animCfg.maxDelay || 1200;
        anim.delay = Math.min(rawDelay, maxDelay);

        return true;
    }

    function getFadeCatalog() {
        return [
            {
                id: 'fade-soft',
                title: 'Yumuşak Katmanlı Fade',
                description: 'Dengeli zincir: arka plan/overlay → kapak → kontroller → en sonda metin. Yumuşak easing ile premium his.'
            },
            {
                id: 'fade-long',
                title: 'Sinematik Fade',
                description: 'Uzun ve akışkan: arka plan daha uzun açılır; kapak ve kontroller sahne gibi oturur, metin en sonda netleşir.'
            },
            {
                id: 'fade-pulse',
                title: 'Nabız Fade',
                description: 'Kısa ve canlı: önce kapak/kontroller gelir; arka plan/overlay arkadan yetişir. Metin hiçbir zaman ilk gelmez.'
            },
            {
                id: 'fade-stagger',
                title: 'Merdivenli Fade',
                description: 'Belirgin ardışık giriş/çıkış: katmanlar tek tek, net gecikmelerle ilerler. Metin en sonda tamamlanır.'
            },
            {
                id: 'fade-text-first',
                title: 'Metin En Son',
                description: 'Önce görseller/zemin ve kontroller oturur; en son şarkı adı + sanatçı metni görünür (okunabilirlik odaklı).'
            },
            {
                id: 'fade-subtle',
                title: 'Hafif Fade',
                description: 'Neredeyse statik: her katman fade alır ama arka plan/overlay belirgin, diğerleri çok kısa ve düşük başlangıç opaklığıyla gelir.'
            }
        ];
    }

    window.WidgetPresets = window.WidgetPresets || {};
    window.WidgetPresets.fade = {
        isFadePreset,
        applyFadePreset,
        getFadeCatalog,
        FADE_PRESET_IDS
    };
})(window);


