/* Hero wave: a ribbon of fine white → baby-blue strands that draws in
   from the right edge and keeps drifting toward the left. */
(function () {
  const canvas = document.querySelector('.first-wave');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const STRANDS = 70;
  const REVEAL_MS = 2600;
  let w = 0, h = 0, dpr = 1, start = null;

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    w = canvas.clientWidth;
    h = canvas.clientHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  // y of strand i at horizontal position x (0..1) and time t (seconds)
  function strandY(i, x, t) {
    const s = i / (STRANDS - 1);          // 0..1 across the ribbon
    const spread = s - 0.5;               // -0.5..0.5
    const cy = h * 0.88;
    const amp = h * 0.09;
    // bulges that grow toward the right, like loops opening up
    const bulge = Math.sin(x * Math.PI * 2.2 + t * 0.5 + s * 1.6) * (0.35 + x * 0.9);
    return cy
      + Math.sin(x * 7.5 + t * 0.9 + s * 0.9) * amp * 0.55
      + Math.sin(x * 3.1 + t * 0.4 - s * 0.6) * amp * 0.45
      + spread * amp * 1.4 * bulge;
  }

  function draw(now) {
    if (start === null) start = now;
    const elapsed = now - start;
    const t = reduceMotion ? 0 : elapsed / 1000;
    const p = reduceMotion ? 1 : Math.min(elapsed / REVEAL_MS, 1);
    const reveal = 1 - Math.pow(1 - p, 3); // ease-out

    ctx.clearRect(0, 0, w, h);
    ctx.save();
    // reveal from the right edge toward the left
    const left = w * (1 - reveal);
    ctx.beginPath();
    ctx.rect(left, 0, w - left, h);
    ctx.clip();

    const grad = ctx.createLinearGradient(0, 0, w, 0);
    grad.addColorStop(0, 'rgba(255, 255, 255, 0.0)');
    grad.addColorStop(0.35, 'rgba(255, 255, 255, 0.0)'); // stays clear of the text column
    grad.addColorStop(0.55, 'rgba(255, 255, 255, 0.9)');
    grad.addColorStop(0.75, 'rgba(173, 216, 240, 0.9)');
    grad.addColorStop(1, 'rgba(137, 196, 235, 0.95)');
    ctx.strokeStyle = grad;
    ctx.lineWidth = 0.7;

    const step = Math.max(4, w / 260);
    for (let i = 0; i < STRANDS; i++) {
      ctx.globalAlpha = 0.25 + 0.45 * Math.sin((i / (STRANDS - 1)) * Math.PI);
      ctx.beginPath();
      for (let px = 0; px <= w + step; px += step) {
        const y = strandY(i, px / w, t);
        px === 0 ? ctx.moveTo(px, y) : ctx.lineTo(px, y);
      }
      ctx.stroke();
    }
    ctx.restore();

    if (!reduceMotion) requestAnimationFrame(draw);
  }

  resize();
  window.addEventListener('resize', resize);
  requestAnimationFrame(draw);
})();
