/*
CinematicLoader (GSAP-only) — 28px cinematic bar
Exports: window.CinematicLoader.mount(selector, opts)

Controller methods:
- setProgress(p01)  // 0..1
- setStatus(text)
- complete()        // cinematic completion + fade
- error()           // cinematic error shake
- destroy()

Notes:
- Background canvas runs at ~30fps.
- DPR is capped for performance.
*/
(function (global) {
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const prefersReducedMotion =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function mount(selector, opts = {}) {
    const root = typeof selector === "string" ? document.querySelector(selector) : selector;
    if (!root) throw new Error("CinematicLoader: mount root not found");

    const cfg = {
      fps: typeof opts.fps === "number" ? opts.fps : 30,
      maxDpr: typeof opts.maxDpr === "number" ? opts.maxDpr : 1.5,
    };

    const gsap = global.gsap;
    if (!gsap) throw new Error("CinematicLoader: gsap not found (load gsap.min.js first)");

    const bg = root.querySelector(".aegis-bg");
    const bar = root.querySelector(".aegis-bar");
    const fill = root.querySelector(".aegis-bar .fill");
    const sheen = root.querySelector(".aegis-bar .sheen");
    const orb = root.querySelector(".aegis-bar .orb");
    const trail = root.querySelector(".aegis-bar .trail");
    const pctEl = root.querySelector("#aegisPct");
    const statusEl = root.querySelector("#aegisStatus");

    // ----- background canvas (cinematic glow field) -----
    const ctx = bg.getContext("2d", { alpha: true });
    let W = 0, H = 0, DPR = 1;

    const particles = [];
    const PCOUNT = prefersReducedMotion ? 0 : 170;
    let targetX = 0.15, targetY = 0.58; // normalized focus point (tracks progress edge)

    for (let i = 0; i < PCOUNT; i++) {
      particles.push({
        x: Math.random(),
        y: Math.random(),
        vx: (Math.random() - 0.5) * 0.001,
        vy: (Math.random() - 0.5) * 0.001,
        t: Math.random() * 10,
        warm: Math.random() < 0.35,
      });
    }

    function resize() {
      DPR = Math.min(cfg.maxDpr, window.devicePixelRatio || 1);
      W = Math.floor(root.clientWidth * DPR);
      H = Math.floor(root.clientHeight * DPR);
      bg.width = W;
      bg.height = H;
    }

    function drawBg(dt) {
      ctx.clearRect(0, 0, W, H);

      // base gradients
      const g0 = ctx.createRadialGradient(W * 0.25, H * 0.22, 0, W * 0.25, H * 0.22, Math.max(W, H) * 0.85);
      g0.addColorStop(0, "rgba(51,184,255,0.16)");
      g0.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g0;
      ctx.fillRect(0, 0, W, H);

      const g1 = ctx.createRadialGradient(W * 0.78, H * 0.30, 0, W * 0.78, H * 0.30, Math.max(W, H) * 0.75);
      g1.addColorStop(0, "rgba(214,168,74,0.12)");
      g1.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g1;
      ctx.fillRect(0, 0, W, H);

      // subtle grid
      ctx.globalAlpha = 0.16;
      ctx.strokeStyle = "rgba(120,170,255,0.25)";
      ctx.lineWidth = 1 * DPR;
      const step = 64 * DPR;
      ctx.beginPath();
      for (let x = 0; x <= W; x += step) { ctx.moveTo(x, 0); ctx.lineTo(x, H); }
      for (let y = 0; y <= H; y += step) { ctx.moveTo(0, y); ctx.lineTo(W, y); }
      ctx.stroke();
      ctx.globalAlpha = 1;

      const tx = targetX * W;
      const ty = targetY * H;

      if (PCOUNT > 0) {
        for (const p of particles) {
          p.t += dt * 0.001;
          const ax = (tx - p.x * W) * 0.00000085;
          const ay = (ty - p.y * H) * 0.00000085;
          p.vx = (p.vx + ax) * 0.985;
          p.vy = (p.vy + ay) * 0.985;
          p.x += p.vx * dt;
          p.y += p.vy * dt;

          if (p.x < -0.05) p.x = 1.05;
          if (p.x > 1.05) p.x = -0.05;
          if (p.y < -0.05) p.y = 1.05;
          if (p.y > 1.05) p.y = -0.05;

          const px = p.x * W;
          const py = p.y * H;

          // faint trace segment
          ctx.globalAlpha = 0.10;
          ctx.strokeStyle = p.warm ? "rgba(214,168,74,0.35)" : "rgba(51,184,255,0.35)";
          ctx.lineWidth = 1 * DPR;
          ctx.beginPath();
          ctx.moveTo(px, py);
          ctx.lineTo(px + Math.sin(p.t) * 22 * DPR, py + Math.cos(p.t * 1.2) * 18 * DPR);
          ctx.stroke();

          // glow dot
          ctx.globalAlpha = 0.85;
          ctx.fillStyle = p.warm ? "rgba(214,168,74,0.85)" : "rgba(51,184,255,0.85)";
          ctx.shadowBlur = 18 * DPR;
          ctx.shadowColor = p.warm ? "rgba(214,168,74,0.55)" : "rgba(51,184,255,0.55)";
          ctx.beginPath();
          ctx.arc(px, py, (1.3 + (Math.sin(p.t) + 1) * 0.45) * DPR, 0, Math.PI * 2);
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      }
      ctx.globalAlpha = 1;
    }

    // 30fps loop
    let running = true;
    let last = performance.now();
    const FRAME_MS = 1000 / cfg.fps;

    function loop(now) {
      if (!running) return;
      requestAnimationFrame(loop);
      const dt = now - last;
      if (dt < FRAME_MS) return;
      last = now;
      drawBg(dt);
    }

    // ----- GSAP bar animation -----
    // Sheen sweeps continuously
    let sheenTL = null;
    if (!prefersReducedMotion) {
      sheenTL = gsap.to(sheen, {
        x: () => (bar.clientWidth + 240),
        duration: 1.25,
        ease: "sine.inOut",
        repeat: -1
      });
    }

    // internal progress state
    let current = 0;

    function setPct(p01) {
      pctEl.textContent = `${Math.round(clamp01(p01) * 100)}%`;
    }

    function updateEdge(p01) {
      // Compute edge position in pixels within bar
      const w = bar.clientWidth;
      const edge = w * clamp01(p01);

      // Fill width
      fill.style.width = `${(clamp01(p01) * 100).toFixed(3)}%`;

      // Orb position
      orb.style.left = `${edge}px`;

      // Trail behind orb
      const trailLen = Math.max(90, Math.min(240, 120 + (p01 * 120)));
      trail.style.width = `${trailLen}px`;
      trail.style.left = `${Math.max(0, edge - trailLen)}px`;

      // Background focus (normalized)
      const hero = root.querySelector(".aegis-hero");
      const heroRect = hero.getBoundingClientRect();
      const edgeNorm = (heroRect.left + (heroRect.width * 0.07) + (heroRect.width * 0.86 * p01)) / window.innerWidth;
      targetX = Math.max(0, Math.min(1, edgeNorm));
      targetY = 0.50;
    }

    function setProgress(p01) {
      const target = clamp01(p01);
      // Smoothly tween to avoid jitter
      gsap.to({ v: current }, {
        v: target,
        duration: 0.55,
        ease: "power2.out",
        onUpdate() {
          current = this.targets()[0].v;
          setPct(current);
          updateEdge(current);
        }
      });
    }

    function setStatus(text) {
      if (typeof text === "string") statusEl.textContent = text;
    }

    function complete() {
      setStatus("Complete");
      gsap.timeline()
        .to(fill, { filter: "brightness(1.35) saturate(1.35)", duration: 0.12 })
        .to(fill, { filter: "brightness(1.0) saturate(1.2)", duration: 0.35 })
        .to(root, { opacity: 0, duration: 0.35, ease: "power2.out", delay: 0.15 });
    }

    function error() {
      setStatus("Error");
      const panel = root.querySelector(".aegis-center");
      gsap.timeline()
        .to(panel, { x: -6, duration: 0.06 })
        .to(panel, { x: 6, duration: 0.06, repeat: 3, yoyo: true })
        .to(panel, { x: 0, duration: 0.06 });
    }

    function destroy() {
      running = false;
      if (sheenTL) sheenTL.kill();
      ro.disconnect();
    }

    // resize handling
    const ro = new ResizeObserver(() => {
      resize();
      // force redraw focus and edge
      setPct(current);
      updateEdge(current);
    });
    ro.observe(root);

    resize();
    setPct(0);
    updateEdge(0);
    if (!prefersReducedMotion) requestAnimationFrame(loop);

    return { setProgress, setStatus, complete, error, destroy };
  }

  global.CinematicLoader = { mount };
})(window);
