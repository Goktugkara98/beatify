/**
 * @file widget_modern.js
 * @description (TAM SÜRÜM) Dinamik Z-Index, Cross-Fade, Gecikme ve Hata Düzeltmelerini içerir.
 */

document.addEventListener('DOMContentLoaded', () => {
    const widgetElement = document.getElementById('spotifyWidgetModern');
    if (!widgetElement || typeof SpotifyWidgetCore === 'undefined') {
        console.error("[Modern.js] HATA: Core bileşenler (widgetElement veya SpotifyWidgetCore) bulunamadı.");
        return;
    }
    console.log("[Modern.js] Dinamik Z-Index Motoru başlatılıyor.");

    // --- Z-Index Durum Yönetimi ---
    let zIndexConfig = {
        AlbumArtBackgroundElement: { a: 3, b: 1 },
        CoverElement:              { a: 4, b: 2 },
        default:                   { a: 6, b: 5 }
    };

    function flipZIndexConfig() {
        console.log('%c[DEBUG] Z-INDEX durumu tersine çevriliyor...', 'color: magenta; font-weight: bold;');
        for (const key in zIndexConfig) {
            const temp = zIndexConfig[key].a;
            zIndexConfig[key].a = zIndexConfig[key].b;
            zIndexConfig[key].b = temp;
        }
        console.log('%c[DEBUG] Yeni Z-INDEX durumu:', 'color: magenta; font-weight: bold;', zIndexConfig);
    }

    // --- YARDIMCI FONKSİYONLAR ---

    function applyStaticStyles(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const baseName = elementId.substring(0, elementId.lastIndexOf('_'));
        const setLetter = elementId.slice(-1);

        const mapping = zIndexConfig[baseName] || zIndexConfig.default;
        const zIndex = mapping[setLetter];

        if (typeof zIndex !== 'undefined') {
            element.style.zIndex = zIndex;
            console.log(`%c[DEBUG] Z-INDEX -> ELEMENT: [${elementId}], Z-INDEX: ${zIndex}`, 'color: orange;');
        }
    }

    function waitForImages(elementIds) {
        const imageElements = elementIds
            .map(id => document.getElementById(id))
            .filter(el => el && el.tagName === 'IMG' && el.src);

        if (imageElements.length === 0) return Promise.resolve();
        
        console.log(`[DEBUG] ${imageElements.length} adet görselin yüklenmesi bekleniyor...`);
        const promises = imageElements.map(img => {
            return new Promise((resolve) => {
                if (img.complete) {
                    resolve();
                    return;
                }
                const loadHandler = () => { cleanup(); resolve(); };
                const errorHandler = () => { cleanup(); resolve(); };
                const cleanup = () => {
                    img.removeEventListener('load', loadHandler);
                    img.removeEventListener('error', errorHandler);
                };
                img.addEventListener('load', loadHandler);
                img.addEventListener('error', errorHandler);
            });
        });
        return Promise.all(promises);
    }

    function applyAnimation(elementId, phase, onEndCallback = null) {
        const element = document.getElementById(elementId);
        const config = window.spotifyWidget?.config;
        if (!element || !config || !config[elementId] || !config[elementId][phase]) return 0;
        
        const animConfig = config[elementId][phase];
        const { animation, duration, delay } = animConfig; 
        
        if (typeof animation === 'undefined') return 0;

        if (animation === 'none') {
            const isOutPhase = phase === 'transitionOut' || phase === 'outro';
            const effectiveDelay = delay || 0;
            const effectiveDuration = duration || 0;
            if (isOutPhase) {
                console.log(`%c[DEBUG] 'none' [${elementId}] çıkış fazında sahnede kalacak. Süre: ${effectiveDuration}ms`, 'color: violet;');
                return effectiveDuration + effectiveDelay;
            } else {
                element.style.opacity = '0';
                setTimeout(() => { element.style.opacity = '1'; }, effectiveDelay);
                return effectiveDelay;
            }
        }

        if (typeof duration === 'undefined' || typeof delay === 'undefined') return 0;
        
        const durationSec = duration / 1000;
        const delaySec = delay / 1000; 
        const easing = (phase === 'transitionOut' || phase === 'outro') ? 'ease-in' : 'ease-out';
        const animationCssString = `${animation} ${durationSec}s ${easing} ${delaySec}s both`;
        
        console.log(`%c[DEBUG] CSS uygulanıyor -> ELEMENT: [${elementId}], STYLE: "animation: ${animationCssString}"`, 'color: cornflowerblue;');
        element.style.animation = animationCssString;

        element.addEventListener('animationend', function handleAnimationEnd(event) {
            if (event.target !== element) return;
            console.log(`%c[DEBUG] Animasyon bitti -> ELEMENT: [${elementId}]. Stil temizleniyor.`, 'color: lightgreen;');
            element.style.animation = '';
    
            // --- YENİ EKLENEN KISIM ---
            if (onEndCallback) { // <-- 2. Eğer bir callback varsa
                onEndCallback(element); // <-- 3. Bu callback'i çalıştır
            }
        }, { once: true });

        return duration + delay; 
    }

    function getAllElementsInSet(set) {
        return widgetElement.querySelectorAll(`[data-set="${set}"]`);
    }

    // --- OLAY DİNLEYİCİLERİ ---

    widgetElement.addEventListener('widget:intro', async (event) => {
        const { set } = event.detail;
        const config = window.spotifyWidget?.config;
        if (!config || !config.elements) return;

        const introElementIds = config.elements.filter(id => id.endsWith(`_${set}`));
        
        introElementIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.remove('passive');
                el.closest('[class*="AnimationContainer"]')?.classList.remove('passive');
                applyStaticStyles(id);
            }
        });
        
        await waitForImages(introElementIds);
        widgetElement.classList.remove('widget-inactive');
        
        introElementIds.forEach(id => {
            applyAnimation(id, 'intro');
        });
    });

    widgetElement.addEventListener('widget:transition', async (event) => {
        const { activeSet, passiveSet } = event.detail;
    
        flipZIndexConfig();
    
        const config = window.spotifyWidget?.config;
        if (!config || !config.elements) return;
        
        const outgoingElementIds = config.elements.filter(id => id.endsWith(`_${activeSet}`));
        const incomingElementIds = config.elements.filter(id => id.endsWith(`_${passiveSet}`));
        
        // --- GİDEN 'a' SETİ İÇİN STATİK STİLLER UYGULANIYOR ---
        outgoingElementIds.forEach(id => applyStaticStyles(id));
    
        // --- ADIM 1: GELEN 'b' SETİNİ GÖRÜNMEZ ŞEKİLDE HAZIRLA ---
        // (Henüz animasyon yok, sadece hazırlık)
        incomingElementIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.add('is-preparing');
                el.classList.remove('passive');
                el.closest('[class*="AnimationContainer"]')?.classList.remove('passive');
                applyStaticStyles(id);
            }
        });
        
        // --- ADIM 2: GÖRSELLERİN YÜKLENMESİNİ GÜVENLE BEKLE ---
        // (Elemanlar hala opacity:0 olduğu için flash riski yok)
        await waitForImages(incomingElementIds);
    
        // --- ADIM 3: KONTROLÜ DEVRET VE ANİMASYONLARI BAŞLAT ---
        let maxTransitionTime = 0;
        
        // GİDEN 'a' SETİNİN ANİMASYONU BAŞLIYOR (Bireysel temizlik ile)
        outgoingElementIds.forEach(id => {
            const cleanupCallback = (el) => {
                el.classList.add('passive');
            };
            const time = applyAnimation(id, 'transitionOut', cleanupCallback); 
            if (time > maxTransitionTime) maxTransitionTime = time;
        });
        
        // GELEN 'b' SETİNİN ANİMASYONU BAŞLIYOR (Kusursuz sıralama ile)
        incomingElementIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                // Animasyon başlamadan HEMEN ÖNCE .is-preparing sınıfını kaldırarak
                // kontrolü animasyona devrediyoruz.
                el.classList.remove('is-preparing');
            }
            
            const totalTime = applyAnimation(id, 'transitionIn');
            if (totalTime > maxTransitionTime) maxTransitionTime = totalTime;
        });
    
        // --- ADIM 4: GENEL TEMİZLİK ---
        setTimeout(() => {
            window.spotifyWidget.finalizeTransition(passiveSet);
            // .is-preparing sınıfını temizleme koduna burada artık ihtiyaç yok çünkü
            // animasyon başlamadan önce zaten kaldırıldı.
            console.log('[Modern.js] ----- Geçiş döngüsü tamamlandı -----');
        }, maxTransitionTime);
    });
});