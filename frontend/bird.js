/* Floating bird: hidden over the hero and the footer. In between, it glides along the
   right side of the screen in back-to-back S curves as the page scrolls (down in an S,
   up in an S, down again…), easing gently behind the scroll instead of jumping with it. */
(function () {
  const bird = document.querySelector('.floating-bird');
  const hero = document.querySelector('.first');
  const footer = document.querySelector('.site-footer');
  if (!bird || !hero) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const TOP = 0.12;         // start near the top of the viewport…
  const BOTTOM = 0.72;      // …and finish near the bottom
  const EASE = 0.045;       // lower = softer, lazier follow
  const LEG = 1.2;          // screens of scrolling per S (one trip down or up)

  // --- show only between the hero and the footer ---
  if ('IntersectionObserver' in window) {
    const inView = new Map([[hero, true], [footer, false]]);
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => inView.set(entry.target, entry.isIntersecting));
      bird.classList.toggle('is-visible', !inView.get(hero) && !inView.get(footer));
    });
    observer.observe(hero);
    if (footer) observer.observe(footer);
  }

  // --- scroll-driven S path ---
  // phase counts S curves scrolled since the hero left the screen: 0→1 is the first
  // trip down, 1→2 the trip back up, and so on
  function targetProgress() {
    const start = hero.offsetTop + hero.offsetHeight;
    return Math.max(window.scrollY - start, 0) / (window.innerHeight * LEG);
  }

  function place(phase) {
    const vh = window.innerHeight;
    const depth = (1 - Math.cos(phase * Math.PI)) / 2;      // 0→1→0… eases at top and bottom
    const y = vh * (TOP + (BOTTOM - TOP) * depth);
    const sway = Math.min(70, window.innerWidth * 0.06);   // px each side; smaller on phones
    const x = -sway * Math.sin(phase * Math.PI * 2);       // one full sway per trip = an S
    const lean = -6 * Math.cos(phase * Math.PI * 2);       // lean into each bend
    bird.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) rotate(${lean.toFixed(2)}deg)`;
  }

  let current = targetProgress();
  let ticking = false;

  function step() {
    const target = targetProgress();
    current += (target - current) * (reduceMotion ? 1 : EASE);
    place(current);
    if (Math.abs(target - current) > 0.001) {
      requestAnimationFrame(step);
    } else {
      ticking = false;
    }
  }

  function wake() {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(step);
    }
  }

  place(current);
  window.addEventListener('scroll', wake, { passive: true });
  window.addEventListener('resize', wake);
})();
