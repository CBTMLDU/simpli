/* ------------------------------------------------------------------
   Scroll-triggered video autoplay
   ------------------------------------------------------------------
   Plays a video when it scrolls into view, pauses it when it leaves.

   Usage in Markdown:

     <video class="scroll-play" muted loop playsinline preload="none"
            poster="../assets/video/folding-poster.jpg">
       <source src="../assets/video/folding.mp4" type="video/mp4">
     </video>

   Requirements for autoplay to work at all:
     - muted        browsers block sound-on autoplay, no exceptions
     - playsinline  stops iOS forcing fullscreen
     - loop         keeps it running
     - preload=none videos load only when needed, not all at page load

   Drop this file in  docs/javascripts/  and register it in mkdocs.yml:

     extra_javascript:
       - javascripts/video-autoplay.js
   ------------------------------------------------------------------ */

(function () {
  'use strict';

  var SELECTOR = 'video.scroll-play';

  // Respect the visitor's motion preference — if they have asked the
  // operating system to reduce motion, show controls instead of autoplaying.
  var reduceMotion = window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function setup() {
    var videos = document.querySelectorAll(SELECTOR);
    if (!videos.length) return;

    if (reduceMotion) {
      videos.forEach(function (v) {
        v.setAttribute('controls', '');
        v.removeAttribute('autoplay');
      });
      return;
    }

    // Fallback for very old browsers: just let them play.
    if (!('IntersectionObserver' in window)) {
      videos.forEach(function (v) {
        v.setAttribute('controls', '');
      });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var v = entry.target;

        if (entry.isIntersecting) {
          // Load lazily on first appearance
          if (v.preload === 'none') {
            v.preload = 'auto';
            v.load();
          }
          var p = v.play();
          // play() returns a promise in modern browsers; swallow the
          // rejection that happens if the browser still refuses.
          if (p && typeof p.catch === 'function') {
            p.catch(function () {
              v.setAttribute('controls', '');
            });
          }
        } else {
          v.pause();
        }
      });
    }, {
      // Fire when a quarter of the video is on screen, and start a little
      // before it arrives so playback has begun by the time it is visible.
      threshold: 0.25,
      rootMargin: '100px 0px'
    });

    videos.forEach(function (v) {
      // Enforce the attributes autoplay depends on, in case one was
      // forgotten in the Markdown.
      v.muted = true;
      v.loop = true;
      v.setAttribute('playsinline', '');
      observer.observe(v);
    });
  }

  // Run on first load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setup);
  } else {
    setup();
  }

  // MkDocs Material swaps page content without a full reload when
  // instant navigation is on, so re-run after each page change.
  if (window.document$ && typeof window.document$.subscribe === 'function') {
    window.document$.subscribe(setup);
  }
})();
