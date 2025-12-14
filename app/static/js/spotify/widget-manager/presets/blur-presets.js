(function (window) {
    // Blur presetleri: blur-in (giriş) + blur-fade-out (çıkış)

    const orderMap = {
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

    const BLUR_PRESET_IDS = [
        'blur-soft',
        'blur-cinematic',
        'blur-quick',
        'blur-text-focus',
        'blur-bg-focus',
        'blur-subtle'
    ];

    const configs = {
        'blur-soft': {
            intro: { duration: 820, spacing: 75, maxDelay: 560, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionIn: { duration: 760, spacing: 65, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionOut: { duration: 720, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' },
            outro: { duration: 760, spacing: 65, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' }
        },
        'blur-cinematic': {
            intro: { duration: 1300, spacing: 100, maxDelay: 820, easeIn: 'sine.out', easeOut: 'sine.in' },
            transitionIn: { duration: 1200, spacing: 90, maxDelay: 760, easeIn: 'sine.out', easeOut: 'sine.in' },
            transitionOut: { duration: 1100, spacing: 85, maxDelay: 720, easeIn: 'sine.out', easeOut: 'sine.in' },
            outro: { duration: 1200, spacing: 95, maxDelay: 780, easeIn: 'sine.out', easeOut: 'sine.in' }
        },
        'blur-quick': {
            intro: { duration: 580, spacing: 55, maxDelay: 420, easeIn: 'expo.out', easeOut: 'expo.in' },
            transitionIn: { duration: 540, spacing: 50, maxDelay: 380, easeIn: 'expo.out', easeOut: 'expo.in' },
            transitionOut: { duration: 520, spacing: 45, maxDelay: 360, easeIn: 'expo.out', easeOut: 'expo.in' },
            outro: { duration: 540, spacing: 50, maxDelay: 380, easeIn: 'expo.out', easeOut: 'expo.in' }
        },
        'blur-text-focus': {
            intro: { duration: 820, spacing: 75, maxDelay: 560, easeIn: 'power3.out', easeOut: 'power3.in', roleDurationMultipliers: { text: 1, background: 0.85, overlay: 0.85 } },
            transitionIn: { duration: 760, spacing: 70, maxDelay: 520, easeIn: 'power3.out', easeOut: 'power3.in', roleDurationMultipliers: { text: 1, background: 0.85, overlay: 0.85 } },
            transitionOut: { duration: 720, spacing: 65, maxDelay: 480, easeIn: 'power3.out', easeOut: 'power3.in', roleDurationMultipliers: { text: 1, background: 0.85, overlay: 0.85 } },
            outro: { duration: 760, spacing: 70, maxDelay: 520, easeIn: 'power3.out', easeOut: 'power3.in', roleDurationMultipliers: { text: 1, background: 0.85, overlay: 0.85 } }
        },
        'blur-bg-focus': {
            intro: { duration: 900, spacing: 60, maxDelay: 520, easeIn: 'power3.out', easeOut: 'power3.in', roleDurationMultipliers: { background: 1, overlay: 1, text: 0.85 } },
            transitionIn: { duration: 820, spacing: 55, maxDelay: 480, easeIn: 'power3.out', easeOut: 'power3.in', roleDurationMultipliers: { background: 1, overlay: 1, text: 0.85 } },
            transitionOut: { duration: 780, spacing: 50, maxDelay: 440, easeIn: 'power3.out', easeOut: 'power3.in', roleDurationMultipliers: { background: 1, overlay: 1, text: 0.85 } },
            outro: { duration: 820, spacing: 55, maxDelay: 480, easeIn: 'power3.out', easeOut: 'power3.in', roleDurationMultipliers: { background: 1, overlay: 1, text: 0.85 } }
        },
        'blur-subtle': {
            intro: { duration: 620, spacing: 35, maxDelay: 260, easeIn: 'linear', easeOut: 'linear', roleDurationMultipliers: { background: 1, overlay: 1, cover: 0.4, text: 0.35, time: 0.35, bar: 0.35, badge: 0.35, other: 0.35 } },
            transitionIn: { duration: 580, spacing: 30, maxDelay: 240, easeIn: 'linear', easeOut: 'linear', roleDurationMultipliers: { background: 1, overlay: 1, cover: 0.4, text: 0.35, time: 0.35, bar: 0.35, badge: 0.35, other: 0.35 } },
            transitionOut: { duration: 560, spacing: 30, maxDelay: 240, easeIn: 'linear', easeOut: 'linear', roleDurationMultipliers: { background: 1, overlay: 1, cover: 0.4, text: 0.35, time: 0.35, bar: 0.35, badge: 0.35, other: 0.35 } },
            outro: { duration: 600, spacing: 35, maxDelay: 260, easeIn: 'linear', easeOut: 'linear', roleDurationMultipliers: { background: 1, overlay: 1, cover: 0.4, text: 0.35, time: 0.35, bar: 0.35, badge: 0.35, other: 0.35 } }
        }
    };

    function isBlurPreset(presetId) {
        return BLUR_PRESET_IDS.includes(presetId);
    }

    function getBlurCatalog() {
        return [
            { id: 'blur-soft', title: 'Yumuşak Bulanıklık', description: 'Hafif blur ile yumuşak giriş, blur ile kapanış.' },
            { id: 'blur-cinematic', title: 'Sinematik Bulanıklık', description: 'Daha uzun blur; sahne geçişi hissi.' },
            { id: 'blur-quick', title: 'Hızlı Bulanıklık', description: 'Kısa ve canlı blur geçişleri.' },
            { id: 'blur-text-focus', title: 'Metin Odak Bulanıklık', description: 'Metinler daha belirgin; arka plan daha hızlı toparlanır.' },
            { id: 'blur-bg-focus', title: 'Arka Plan Bulanıklık', description: 'Blur sahnesini arka plan taşır; içerik hızlıca netleşir.' },
            { id: 'blur-subtle', title: 'Hafif Bulanıklık', description: 'Neredeyse fark edilmeyen çok hafif blur.' }
        ];
    }

    function applyBlurPreset(presetId, animType, anim, componentName) {
        if (!isBlurPreset(presetId)) return false;
        const cfg = configs[presetId];
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
        const phase = cfg[animType];

        anim.type = isEntrance ? 'blur-in' : 'blur-fade-out';
        anim.animation = anim.type;

        const mult = phase.roleDurationMultipliers && typeof phase.roleDurationMultipliers[role] === 'number'
            ? phase.roleDurationMultipliers[role]
            : 1;
        anim.duration = Math.max(80, Math.round(phase.duration * mult));
        anim.ease = isEntrance ? (phase.easeIn || 'power2.out') : (phase.easeOut || 'power2.in');

        const spacing = phase.spacing || 0;
        const orderIdx = typeof orderMap[componentName] === 'number' ? orderMap[componentName] : 4;
        anim.delay = Math.min(Math.max(0, orderIdx) * spacing, phase.maxDelay || 1200);

        // Blur presetleri opacity override kullanmaz
        delete anim.fromOpacity;
        delete anim.toOpacity;

        return true;
    }

    window.WidgetPresets = window.WidgetPresets || {};
    window.WidgetPresets.blur = {
        isBlurPreset,
        applyBlurPreset,
        getBlurCatalog,
        BLUR_PRESET_IDS
    };
})(window);


