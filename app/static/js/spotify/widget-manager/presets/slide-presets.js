(function (window) {
    // Slide presetleri: sadece slide giriş/çıkış (fade yok).
    // GSAPAnimationService desteklenen tipler:
    // slide-up / slide-down / slide-left / slide-right ve çıkışları:
    // slide-up-out / slide-down-out / slide-left-out / slide-right-out

    const slideOrderMap = {
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

    const SLIDE_PRESET_IDS = [
        'slide-left',
        'slide-right',
        'slide-up',
        'slide-down',
        'slide-smooth',
        'slide-burst'
    ];

    const slideConfigs = {
        'slide-left': {
            intro: { duration: 760, spacing: 70, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionIn: { duration: 700, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionOut: { duration: 650, spacing: 55, maxDelay: 440, easeIn: 'power2.out', easeOut: 'power2.in' },
            outro: { duration: 620, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' }
        },
        'slide-right': {
            intro: { duration: 760, spacing: 70, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionIn: { duration: 700, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionOut: { duration: 650, spacing: 55, maxDelay: 440, easeIn: 'power2.out', easeOut: 'power2.in' },
            outro: { duration: 620, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' }
        },
        'slide-up': {
            intro: { duration: 760, spacing: 70, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionIn: { duration: 700, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionOut: { duration: 650, spacing: 55, maxDelay: 440, easeIn: 'power2.out', easeOut: 'power2.in' },
            outro: { duration: 620, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' }
        },
        'slide-down': {
            intro: { duration: 760, spacing: 70, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionIn: { duration: 700, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionOut: { duration: 650, spacing: 55, maxDelay: 440, easeIn: 'power2.out', easeOut: 'power2.in' },
            outro: { duration: 620, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' }
        },
        'slide-smooth': {
            // Daha "akışkan" ve uzun
            intro: { duration: 1100, spacing: 90, maxDelay: 700, easeIn: 'sine.out', easeOut: 'sine.in' },
            transitionIn: { duration: 980, spacing: 80, maxDelay: 640, easeIn: 'sine.out', easeOut: 'sine.in' },
            transitionOut: { duration: 920, spacing: 75, maxDelay: 600, easeIn: 'sine.out', easeOut: 'sine.in' },
            outro: { duration: 980, spacing: 85, maxDelay: 660, easeIn: 'sine.out', easeOut: 'sine.in' }
        },
        'slide-burst': {
            // Hızlı ve vurucu
            intro: { duration: 520, spacing: 40, maxDelay: 300, easeIn: 'expo.out', easeOut: 'expo.in' },
            transitionIn: { duration: 500, spacing: 35, maxDelay: 260, easeIn: 'expo.out', easeOut: 'expo.in' },
            transitionOut: { duration: 480, spacing: 35, maxDelay: 260, easeIn: 'expo.out', easeOut: 'expo.in' },
            outro: { duration: 520, spacing: 40, maxDelay: 300, easeIn: 'expo.out', easeOut: 'expo.in' }
        }
    };

    // Preset bazında (role -> direction) seçimi.
    // NOT: Yalnızca slide tipleri kullanılır.
    const slideRoleDirections = {
        'slide-left': {
            in: 'slide-left',
            out: 'slide-left-out'
        },
        'slide-right': {
            in: 'slide-right',
            out: 'slide-right-out'
        },
        'slide-up': {
            in: 'slide-up',
            out: 'slide-up-out'
        },
        'slide-down': {
            in: 'slide-down',
            out: 'slide-down-out'
        },
        'slide-smooth': {
            // Katmanlı hissi: arka plan yukarıdan, içerik soldan, süreler sağdan
            roleIn: {
                background: 'slide-down',
                overlay: 'slide-down',
                cover: 'slide-left',
                text: 'slide-left',
                time: 'slide-right',
                bar: 'slide-right',
                badge: 'slide-up',
                other: 'slide-left'
            },
            roleOut: {
                background: 'slide-down-out',
                overlay: 'slide-down-out',
                cover: 'slide-left-out',
                text: 'slide-left-out',
                time: 'slide-right-out',
                bar: 'slide-right-out',
                badge: 'slide-up-out',
                other: 'slide-left-out'
            }
        },
        'slide-burst': {
            // Kısa ve canlı: metinler yukarı, cover soldan, bar sağdan
            roleIn: {
                background: 'slide-up',
                overlay: 'slide-up',
                cover: 'slide-left',
                text: 'slide-up',
                time: 'slide-up',
                bar: 'slide-right',
                badge: 'slide-down',
                other: 'slide-up'
            },
            roleOut: {
                background: 'slide-up-out',
                overlay: 'slide-up-out',
                cover: 'slide-left-out',
                text: 'slide-up-out',
                time: 'slide-up-out',
                bar: 'slide-right-out',
                badge: 'slide-down-out',
                other: 'slide-up-out'
            }
        }
    };

    function isSlidePreset(presetId) {
        return SLIDE_PRESET_IDS.includes(presetId);
    }

    function getSlideCatalog() {
        return [
            { id: 'slide-left', title: 'Sola Kayma', description: 'Tüm katmanlar sağdan gelir, sola doğru çıkar.' },
            { id: 'slide-right', title: 'Sağa Kayma', description: 'Tüm katmanlar soldan gelir, sağa doğru çıkar.' },
            { id: 'slide-up', title: 'Yukarı Kayma', description: 'Dikey hareket: aşağıdan gelir, yukarı çıkar.' },
            { id: 'slide-down', title: 'Aşağı Kayma', description: 'Dikey ters: yukarıdan gelir, aşağı çıkar.' },
            { id: 'slide-smooth', title: 'Akışkan Katmanlar', description: 'Katmanlar farklı yönlerden akışkan gelir; daha yumuşak geçiş.' },
            { id: 'slide-burst', title: 'Hızlı Kayma', description: 'Kısa, hızlı ve vurucu slide kombinasyonu.' }
        ];
    }

    function applySlidePreset(presetId, animType, anim, componentName) {
        if (!isSlidePreset(presetId)) return false;
        const cfg = slideConfigs[presetId];
        if (!cfg || !cfg[animType]) return false;

        const role = (() => {
            switch (componentName) {
                case 'AlbumArtBackground': return 'background';
                case 'GradientOverlay': return 'overlay';
                case 'Cover': return 'cover';
                case 'TrackName':
                case 'ArtistName': return 'text';
                case 'ProgressBar': return 'bar';
                case 'CurrentTime':
                case 'TotalTime': return 'time';
                case 'ProviderBadge': return 'badge';
                default: return 'other';
            }
        })();

        const isEntrance = (animType === 'intro' || animType === 'transitionIn');

        const map = slideRoleDirections[presetId] || slideRoleDirections['slide-left'];
        let type;
        if (map.roleIn && map.roleOut) {
            type = isEntrance ? map.roleIn[role] : map.roleOut[role];
        } else {
            type = isEntrance ? map.in : map.out;
        }

        anim.type = type;
        anim.animation = type;
        anim.duration = cfg[animType].duration;
        anim.ease = isEntrance ? (cfg[animType].easeIn || 'power2.out') : (cfg[animType].easeOut || 'power2.in');

        const spacing = cfg[animType].spacing || 0;
        const orderIdx = typeof slideOrderMap[componentName] === 'number' ? slideOrderMap[componentName] : 4;
        const rawDelay = Math.max(0, orderIdx) * spacing;
        const maxDelay = cfg[animType].maxDelay || 1200;
        anim.delay = Math.min(rawDelay, maxDelay);

        // Slide presetlerinde opacity override kullanmıyoruz
        delete anim.fromOpacity;
        delete anim.toOpacity;

        return true;
    }

    window.WidgetPresets = window.WidgetPresets || {};
    window.WidgetPresets.slide = {
        isSlidePreset,
        applySlidePreset,
        getSlideCatalog,
        SLIDE_PRESET_IDS
    };
})(window);


