(function (window) {
    // Reveal presetleri: clip-up / clip-left / underline-sweep / tilt-in / float-up kombinasyonları

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

    const REVEAL_PRESET_IDS = [
        'reveal-clip-up',
        'reveal-clip-left',
        'reveal-underline',
        'reveal-tilt',
        'reveal-float',
        'reveal-mix'
    ];

    const configs = {
        'reveal-clip-up': {
            intro: { duration: 820, spacing: 75, maxDelay: 560, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionIn: { duration: 760, spacing: 65, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionOut: { duration: 700, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' },
            outro: { duration: 760, spacing: 65, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' }
        },
        'reveal-clip-left': {
            intro: { duration: 820, spacing: 75, maxDelay: 560, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionIn: { duration: 760, spacing: 65, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionOut: { duration: 700, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' },
            outro: { duration: 760, spacing: 65, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' }
        },
        'reveal-underline': {
            intro: { duration: 720, spacing: 70, maxDelay: 520, easeIn: 'power3.out', easeOut: 'power3.in' },
            transitionIn: { duration: 680, spacing: 60, maxDelay: 480, easeIn: 'power3.out', easeOut: 'power3.in' },
            transitionOut: { duration: 640, spacing: 55, maxDelay: 440, easeIn: 'power3.out', easeOut: 'power3.in' },
            outro: { duration: 680, spacing: 60, maxDelay: 480, easeIn: 'power3.out', easeOut: 'power3.in' }
        },
        'reveal-tilt': {
            intro: { duration: 760, spacing: 70, maxDelay: 520, easeIn: 'power3.out', easeOut: 'power3.in' },
            transitionIn: { duration: 720, spacing: 65, maxDelay: 500, easeIn: 'power3.out', easeOut: 'power3.in' },
            transitionOut: { duration: 680, spacing: 60, maxDelay: 480, easeIn: 'power3.out', easeOut: 'power3.in' },
            outro: { duration: 720, spacing: 65, maxDelay: 500, easeIn: 'power3.out', easeOut: 'power3.in' }
        },
        'reveal-float': {
            intro: { duration: 820, spacing: 75, maxDelay: 560, easeIn: 'sine.out', easeOut: 'sine.in' },
            transitionIn: { duration: 760, spacing: 65, maxDelay: 520, easeIn: 'sine.out', easeOut: 'sine.in' },
            transitionOut: { duration: 700, spacing: 60, maxDelay: 480, easeIn: 'sine.out', easeOut: 'sine.in' },
            outro: { duration: 760, spacing: 65, maxDelay: 520, easeIn: 'sine.out', easeOut: 'sine.in' }
        },
        'reveal-mix': {
            intro: { duration: 780, spacing: 75, maxDelay: 560, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionIn: { duration: 740, spacing: 65, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionOut: { duration: 700, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' },
            outro: { duration: 740, spacing: 65, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' }
        }
    };

    const types = {
        'reveal-clip-up': { in: 'clip-up', out: 'fade-out' },
        'reveal-clip-left': { in: 'clip-left', out: 'fade-out' },
        // underline-sweep özellikle bar/text için güzel; diğerlerine clip
        'reveal-underline': {
            roleIn: {
                background: 'clip-up',
                overlay: 'clip-up',
                cover: 'clip-up',
                text: 'underline-sweep',
                time: 'underline-sweep',
                bar: 'underline-sweep',
                badge: 'clip-up',
                other: 'clip-up'
            },
            roleOut: {
                background: 'fade-out',
                overlay: 'fade-out',
                cover: 'fade-out',
                text: 'fade-out',
                time: 'fade-out',
                bar: 'fade-out',
                badge: 'fade-out',
                other: 'fade-out'
            }
        },
        'reveal-tilt': { in: 'tilt-in', out: 'fade-out' },
        'reveal-float': { in: 'float-up', out: 'fade-out' },
        'reveal-mix': {
            roleIn: {
                background: 'clip-up',
                overlay: 'clip-up',
                cover: 'tilt-in',
                text: 'underline-sweep',
                time: 'float-up',
                bar: 'clip-left',
                badge: 'float-up',
                other: 'clip-up'
            },
            roleOut: {
                background: 'fade-out',
                overlay: 'fade-out',
                cover: 'fade-out',
                text: 'fade-out',
                time: 'fade-out',
                bar: 'fade-out',
                badge: 'fade-out',
                other: 'fade-out'
            }
        }
    };

    function isRevealPreset(presetId) {
        return REVEAL_PRESET_IDS.includes(presetId);
    }

    function getRevealCatalog() {
        return [
            { id: 'reveal-clip-up', title: 'Maske: Yukarı', description: 'Clip maskesi yukarı açılır; temiz reveal.' },
            { id: 'reveal-clip-left', title: 'Maske: Soldan', description: 'Clip maskesi soldan açılır; yatay reveal.' },
            { id: 'reveal-underline', title: 'Çizgi Açılış', description: 'Metin/bar çizgiyle gelir; diğerleri clip ile açılır.' },
            { id: 'reveal-tilt', title: 'Tilt Açılış', description: 'Hafif tilt ile sahneye giriş, fade ile kapanış.' },
            { id: 'reveal-float', title: 'Süzülme Açılış', description: 'Yumuşak yukarı süzülme, fade ile kapanış.' },
            { id: 'reveal-mix', title: 'Karma Açılış', description: 'Clip + çizgi + süzülme karışımı; daha karakterli.' }
        ];
    }

    function applyRevealPreset(presetId, animType, anim, componentName) {
        if (!isRevealPreset(presetId)) return false;
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
        const map = types[presetId] || types['reveal-clip-up'];

        let type;
        if (map.roleIn && map.roleOut) {
            type = isEntrance ? map.roleIn[role] : map.roleOut[role];
        } else {
            type = isEntrance ? map.in : map.out;
        }

        anim.type = type;
        anim.animation = type;
        anim.duration = phase.duration;
        anim.ease = isEntrance ? (phase.easeIn || 'power2.out') : (phase.easeOut || 'power2.in');

        const spacing = phase.spacing || 0;
        const orderIdx = typeof orderMap[componentName] === 'number' ? orderMap[componentName] : 4;
        anim.delay = Math.min(Math.max(0, orderIdx) * spacing, phase.maxDelay || 1200);

        // Reveal presetleri opacity override kullanmaz
        delete anim.fromOpacity;
        delete anim.toOpacity;

        return true;
    }

    window.WidgetPresets = window.WidgetPresets || {};
    window.WidgetPresets.reveal = {
        isRevealPreset,
        applyRevealPreset,
        getRevealCatalog,
        REVEAL_PRESET_IDS
    };
})(window);


