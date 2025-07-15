document.addEventListener('DOMContentLoaded', () => {
    // GSAP initial settings for the theme toggle
    gsap.set("#moon, .star", {opacity: 0});
    gsap.set("#sun, #cloud, #moon", {x: 15});
    gsap.set(".star", {x: 35, y: -5});
    
    // Load theme preference from localStorage
    const currentTheme = localStorage.getItem('theme');
    
    // Apply saved theme on page load
    if (currentTheme === 'dark-theme') {
        document.body.classList.add('dark-theme');
        // Set the toggle to dark mode state
        gsap.set("#sun", {x: -157, opacity: 0});
        gsap.set("#cloud", {opacity: 0});
        gsap.set("#moon", {x: -157, opacity: 1});
        gsap.set(".star", {opacity: 1});
        gsap.set("#night", {background: "#224f6d", borderColor: "#cad4d8"});
        gsap.set("#background", {background: "#0d1f2b"});
        $("#day").css({"pointer-events": "none"});
        $("#night").css({"pointer-events": "all"});
    } else {
        // Light mode is default
        $("#night").css({"pointer-events": "none"});
        $("#day").css({"pointer-events": "all"});
    }
    
    // Day to Night transition
    $("#day").click(function(){
        gsap.to("#sun", 1, {x: -157, opacity: 0, ease: Power1.easeInOut});
        gsap.to("#cloud", .5, {opacity: 0, ease: Power1.easeInOut});
        gsap.to("#moon", 1, {x: -157, rotate: -360, transformOrigin: "center", opacity: 1, ease: Power1.easeInOut});
        gsap.to(".star", .5, {opacity: 1, ease: Power1.easeInOut});
        gsap.to("#night", 1, {background: "#224f6d", borderColor: "#cad4d8", ease: Power1.easeInOut});
        gsap.to("#background", 1, {background: "#0d1f2b", ease: Power1.easeInOut});
        $(this).css({"pointer-events": "none"});
        
        // Add dark-theme class to body and save preference
        document.body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark-theme');
        
        setTimeout(function(){
            $("#night").css({"pointer-events": "all"})
        }, 1000);
    });
    
    // Night to Day transition
    $("#night").click(function(){
        gsap.to("#sun", 1, {x: 15, opacity: 1, ease: Power1.easeInOut});
        gsap.to("#cloud", 1, {opacity: 1, ease: Power1.easeInOut});
        gsap.to("#moon", 1, {opacity: 0, x: 35, rotate: 360, transformOrigin: "center", ease: Power1.easeInOut});
        gsap.to(".star", 1, {opacity: 0, ease: Power1.easeInOut});
        gsap.to("#night", 1, {background: "#9cd6ef", borderColor: "#65c0e7", ease: Power1.easeInOut});
        gsap.to("#background", 1, {background: "#d3edf8", ease: Power1.easeInOut});
        $(this).css({"pointer-events": "none"});
        
        // Remove dark-theme class from body and save preference
        document.body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light-theme');
        
        setTimeout(function(){
            $("#day").css({"pointer-events": "all"})
        }, 1000);
    });
});
