(function (window) {
    // Zoom presetleri: zoom-in-soft / zoom-out-soft / card-pop (scale tabanlı)

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

    const ZOOM_PRESET_IDS = [
        'zoom-soft',
        'zoom-cinematic',
        'zoom-pop',
        'zoom-focus-cover',
        'zoom-focus-text',
        'zoom-subtle'
    ];

    const configs = {
        'zoom-soft': {
            intro: { duration: 780, spacing: 70, maxDelay: 520, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionIn: { duration: 720, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' },
            transitionOut: { duration: 680, spacing: 55, maxDelay: 440, easeIn: 'power2.out', easeOut: 'power2.in' },
            outro: { duration: 720, spacing: 60, maxDelay: 480, easeIn: 'power2.out', easeOut: 'power2.in' }
        },
        'zoom-cinematic': {
            intro: { duration: 1200, spacing: 95, maxDelay: 760, easeIn: 'sine.out', easeOut: 'sine.in' },
            transitionIn: { duration: 1100, spacing: 85, maxDelay: 700, easeIn: 'sine.out', easeOut: 'sine.in' },
            transitionOut: { duration: 1050, spacing: 80, maxDelay: 660, easeIn: 'sine.out', easeOut: 'sine.in' },
            outro: { duration: 1150, spacing: 90, maxDelay: 740, easeIn: 'sine.out', easeOut: 'sine.in' }
        },
        'zoom-pop': {
            intro: { duration: 640, spacing: 55, maxDelay: 420, easeIn: 'expo.out', easeOut: 'expo.in' },
            transitionIn: { duration: 600, spacing: 50, maxDelay: 380, easeIn: 'expo.out', easeOut: 'expo.in' },
            transitionOut: { duration: 560, spacing: 45, maxDelay: 360, easeIn: 'expo.out', easeOut: 'expo.in' },
            outro: { duration: 600, spacing: 50, maxDelay: 380, easeIn: 'expo.out', easeOut: 'expo.in' }
        },
        'zoom-focus-cover': {
            intro: { duration: 820, spacing: 70, maxDelay: 520, easeIn: 'power3.out', easeOut: 'power3.in' },
            transitionIn: { duration: 760, spacing: 65, maxDelay: 500, easeIn: 'power3.out', easeOut: 'power3.in' },
            transitionOut: { duration: 720, spacing: 60, maxDelay: 480, easeIn: 'power3.out', easeOut: 'power3.in' },
            outro: { duration: 760, spacing: 65, maxDelay: 500, easeIn: 'power3.out', easeOut: 'power3.in' }
        },
        'zoom-focus-text': {
            intro: { duration: 780, spacing: 70, maxDelay: 520, easeIn: 'power3.out', easeOut: 'power3.in' },
            transitionIn: { duration: 740, spacing: 65, maxDelay: 500, easeIn: 'power3.out', easeOut: 'power3.in' },
            transitionOut: { duration: 700, spacing: 60, maxDelay: 480, easeIn: 'power3.out', easeOut: 'power3.in' },
            outro: { duration: 740, spacing: 65, maxDelay: 500, easeIn: 'power3.out', easeOut: 'power3.in' }
        },
        'zoom-subtle': {
            intro: { duration: 680, spacing: 40, maxDelay: 300, easeIn: 'linear', easeOut: 'linear' },
            transitionIn: { duration: 640, spacing: 35, maxDelay: 280, easeIn: 'linear', easeOut: 'linear' },
            transitionOut: { duration: 620, spacing: 35, maxDelay: 280, easeIn: 'linear', easeOut: 'linear' },
            outro: { duration: 660, spacing: 40, maxDelay: 300, easeIn: 'linear', easeOut: 'linear' }
        }
    };

    const roleType = {
        // Standart zoom giriş/çıkış
        'zoom-soft': { in: 'zoom-in-soft', out: 'zoom-out-soft' },
        'zoom-cinematic': { in: 'zoom-in-soft', out: 'zoom-out-soft' },
        // Pop: girişte card-pop, çıkışta zoom-out-soft
        'zoom-pop': { in: 'card-pop', out: 'zoom-out-soft' },
        // Focus: cover veya text pop yapar
        'zoom-focus-cover': {
            roleIn: {
                background: 'zoom-in-soft',
                overlay: 'zoom-in-soft',
                cover: 'card-pop',
                text: 'zoom-in-soft',
                time: 'zoom-in-soft',
                bar: 'zoom-in-soft',
                badge: 'zoom-in-soft',
                other: 'zoom-in-soft'
            },
            roleOut: {
                background: 'zoom-out-soft',
                overlay: 'zoom-out-soft',
                cover: 'zoom-out-soft',
                text: 'zoom-out-soft',
                time: 'zoom-out-soft',
                bar: 'zoom-out-soft',
                badge: 'zoom-out-soft',
                other: 'zoom-out-soft'
            }
        },
        'zoom-focus-text': {
            roleIn: {
                background: 'zoom-in-soft',
                overlay: 'zoom-in-soft',
                cover: 'zoom-in-soft',
                text: 'card-pop',
                time: 'zoom-in-soft',
                bar: 'zoom-in-soft',
                badge: 'zoom-in-soft',
                other: 'zoom-in-soft'
            },
            roleOut: {
                background: 'zoom-out-soft',
                overlay: 'zoom-out-soft',
                cover: 'zoom-out-soft',
                text: 'zoom-out-soft',
                time: 'zoom-out-soft',
                bar: 'zoom-out-soft',
                badge: 'zoom-out-soft',
                other: 'zoom-out-soft'
            }
        },
        // Subtle: her şey zoom-in-soft ama daha kısa/linear
        'zoom-subtle': { in: 'zoom-in-soft', out: 'zoom-out-soft' }
    };

    function isZoomPreset(presetId) {
        return ZOOM_PRESET_IDS.includes(presetId);
    }

    function getZoomCatalog() {
        return [
            { id: 'zoom-soft', title: 'Yumuşak Derinlik', description: 'Nazik yakınlaşma/uzaklaşma; sakin odak.' },
            { id: 'zoom-cinematic', title: 'Sinematik Derinlik', description: 'Daha uzun ve akışkan zoom geçişleri.' },
            { id: 'zoom-pop', title: 'Pop Derinlik', description: 'Girişte kısa “pop”, çıkışta zoom ile kapanış.' },
            { id: 'zoom-focus-cover', title: 'Kapak Odak', description: 'Kapak öne çıkar: cover pop, diğerleri yumuşak zoom.' },
            { id: 'zoom-focus-text', title: 'Metin Odak', description: 'Şarkı/sanatçı metni öne çıkar; diğerleri zoom ile eşlik eder.' },
            { id: 'zoom-subtle', title: 'Hafif Derinlik', description: 'Neredeyse fark edilmeyen çok hafif zoom.' }
        ];
    }

    function applyZoomPreset(presetId, animType, anim, componentName) {
        if (!isZoomPreset(presetId)) return false;
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
        const typeMap = roleType[presetId] || roleType['zoom-soft'];
        let type;
        if (typeMap.roleIn && typeMap.roleOut) {
            type = isEntrance ? typeMap.roleIn[role] : typeMap.roleOut[role];
        } else {
            type = isEntrance ? typeMap.in : typeMap.out;
        }

        const phase = cfg[animType];
        anim.type = type;
        anim.animation = type;
        anim.duration = phase.duration;
        anim.ease = isEntrance ? (phase.easeIn || 'power2.out') : (phase.easeOut || 'power2.in');

        const spacing = phase.spacing || 0;
        const orderIdx = typeof orderMap[componentName] === 'number' ? orderMap[componentName] : 4;
        anim.delay = Math.min(Math.max(0, orderIdx) * spacing, phase.maxDelay || 1200);

        // Zoom presetleri opacity override kullanmaz
        delete anim.fromOpacity;
        delete anim.toOpacity;

        return true;
    }

    window.WidgetPresets = window.WidgetPresets || {};
    window.WidgetPresets.zoom = {
        isZoomPreset,
        applyZoomPreset,
        getZoomCatalog,
        ZOOM_PRESET_IDS
    };
})(window);


