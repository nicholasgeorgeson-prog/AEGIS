/*
CinematicLoader v2.1 — AEGIS-style cinematic loader
Rive-inspired molten glow with white-hot leading edge,
intense particle effects, circuit traces, and cosmic atmosphere.

Exports: window.CinematicLoader.mount(selector, opts)

Controller methods:
- setProgress(p01)  // 0..1
- setStatus(text)
- complete()        // cinematic completion + fade
- error()           // cinematic error shake
- destroy()
*/
(function (global) {
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const prefersReducedMotion =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Color palette - Rive-inspired molten theme
  const COLORS = {
    blue: '#33B8FF',
    blueGlow: 'rgba(51, 184, 255, 0.8)',
    gold: '#D6A84A',
    goldGlow: 'rgba(214, 168, 74, 0.8)',
    orange: '#FF8C42',
    orangeGlow: 'rgba(255, 140, 66, 0.9)',
    white: '#FFFFFF',
    cyan: '#00FFFF',
    cyanGlow: 'rgba(0, 255, 255, 0.6)',
    // Molten palette
    moltenWhite: '#FFFAF0',
    moltenYellow: '#FFE066',
    moltenOrange: '#FF9F40',
    moltenAmber: '#FF7B25',
    moltenDeep: '#E65C00',
    moltenYellowGlow: 'rgba(255, 224, 102, 0.85)',
    moltenOrangeGlow: 'rgba(255, 159, 64, 0.85)',
    moltenAmberGlow: 'rgba(255, 123, 37, 0.80)'
  };

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
    const reflectionSpot = root.querySelector(".aegis-bar .reflection-spot");
    const pctEl = root.querySelector("#aegisPct");
    const statusEl = root.querySelector("#aegisStatus");

    // ----- background canvas -----
    const ctx = bg.getContext("2d", { alpha: true });
    let W = 0, H = 0, DPR = 1;

    // Particle systems
    const particles = [];
    const sparks = [];
    const circuitTraces = [];
    const burstParticles = [];
    const PCOUNT = prefersReducedMotion ? 0 : 300; // More particles
    let targetX = 0.15, targetY = 0.50;
    let currentProgress = 0;
    let lastBurstProgress = 0;

    // Initialize main particles
    for (let i = 0; i < PCOUNT; i++) {
      particles.push(createParticle());
    }

    function createParticle() {
      const isWarm = Math.random() < 0.4;
      const isBright = Math.random() < 0.15;
      return {
        x: Math.random(),
        y: Math.random(),
        vx: (Math.random() - 0.5) * 0.002,
        vy: (Math.random() - 0.5) * 0.002,
        t: Math.random() * 10,
        size: isBright ? Math.random() * 3 + 2 : Math.random() * 2 + 0.5,
        warm: isWarm,
        bright: isBright,
        alpha: isBright ? 0.9 : Math.random() * 0.6 + 0.2,
        pulseSpeed: Math.random() * 0.05 + 0.02,
        pulsePhase: Math.random() * Math.PI * 2
      };
    }

    // Create circuit traces
    function createCircuitTrace(startX, startY, direction) {
      const segments = [];
      let x = startX;
      let y = startY;
      const length = Math.floor(Math.random() * 8) + 4;

      for (let i = 0; i < length; i++) {
        const nextX = x + (direction === 'left' ? -1 : 1) * (Math.random() * 0.03 + 0.01);
        const nextY = y + (Math.random() - 0.5) * 0.04;
        segments.push({ x1: x, y1: y, x2: nextX, y2: nextY });
        x = nextX;
        y = nextY;
        // Random turns
        if (Math.random() < 0.3) {
          const turnY = y + (Math.random() - 0.5) * 0.06;
          segments.push({ x1: x, y1: y, x2: x, y2: turnY });
          y = turnY;
        }
      }

      // More orange/amber dominated for molten theme
      const colorRoll = Math.random();
      let color, glowColor;
      if (colorRoll < 0.4) {
        color = COLORS.moltenOrange;
        glowColor = COLORS.moltenOrangeGlow;
      } else if (colorRoll < 0.7) {
        color = COLORS.moltenAmber;
        glowColor = COLORS.moltenAmberGlow;
      } else if (colorRoll < 0.85) {
        color = COLORS.moltenYellow;
        glowColor = COLORS.moltenYellowGlow;
      } else {
        color = COLORS.cyan;
        glowColor = COLORS.cyanGlow;
      }
      return {
        segments,
        life: 1,
        decay: Math.random() * 0.015 + 0.008,
        color: color,
        glowColor: glowColor
      };
    }

    // Create spark burst - molten orange theme
    function createSparkBurst(x, y, count = 20) {
      for (let i = 0; i < count; i++) {
        const angle = (i / count) * Math.PI * 2 + Math.random() * 0.5;
        const speed = Math.random() * 0.015 + 0.005;
        const colorRoll = Math.random();
        let color;
        if (colorRoll < 0.4) color = COLORS.moltenYellow;
        else if (colorRoll < 0.75) color = COLORS.moltenOrange;
        else if (colorRoll < 0.9) color = COLORS.moltenAmber;
        else color = COLORS.white;
        sparks.push({
          x, y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          life: 1,
          decay: Math.random() * 0.03 + 0.015,
          size: Math.random() * 3 + 1,
          color: color,
          trail: []
        });
      }
    }

    // Create burst particles (large explosion effect) - molten theme
    function createBurstParticles(x, y, count = 40) {
      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 0.02 + 0.008;
        const colorRoll = Math.random();
        let color, glow;
        if (colorRoll < 0.3) {
          color = COLORS.moltenYellow;
          glow = COLORS.moltenYellowGlow;
        } else if (colorRoll < 0.65) {
          color = COLORS.moltenOrange;
          glow = COLORS.moltenOrangeGlow;
        } else if (colorRoll < 0.9) {
          color = COLORS.moltenAmber;
          glow = COLORS.moltenAmberGlow;
        } else {
          color = COLORS.white;
          glow = 'rgba(255, 255, 255, 0.9)';
        }
        burstParticles.push({
          x, y,
          vx: Math.cos(angle) * speed * (0.3 + Math.random() * 0.7),
          vy: Math.sin(angle) * speed * (0.3 + Math.random() * 0.7),
          life: 1,
          decay: Math.random() * 0.012 + 0.006,
          size: Math.random() * 5 + 2,
          color: color,
          glow: glow
        });
      }
    }

    function resize() {
      DPR = Math.min(cfg.maxDpr, window.devicePixelRatio || 1);
      W = Math.floor(root.clientWidth * DPR);
      H = Math.floor(root.clientHeight * DPR);
      bg.width = W;
      bg.height = H;
    }

    function drawBg(dt) {
      // Dark base with slight transparency for layering
      ctx.fillStyle = 'rgba(4, 8, 18, 0.15)';
      ctx.fillRect(0, 0, W, H);

      // Cosmic nebula gradients
      drawNebulaBackground();

      // Hex grid
      drawHexGrid();

      // Circuit traces
      drawCircuitTraces(dt);

      // Update and draw main particles
      drawParticles(dt);

      // Draw sparks
      drawSparks(dt);

      // Draw burst particles
      drawBurstParticles(dt);

      // Draw intense glow at progress edge
      drawProgressGlow();
    }

    function drawNebulaBackground() {
      // Deep blue nebula (top-left) - subtle
      const g0 = ctx.createRadialGradient(W * 0.2, H * 0.3, 0, W * 0.2, H * 0.3, W * 0.6);
      g0.addColorStop(0, 'rgba(51, 100, 180, 0.08)');
      g0.addColorStop(0.5, 'rgba(30, 60, 120, 0.04)');
      g0.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = g0;
      ctx.fillRect(0, 0, W, H);

      // Molten orange nebula (center-right, near progress) - more intense
      const px = targetX * W;
      const g1 = ctx.createRadialGradient(px, H * 0.5, 0, px, H * 0.5, W * 0.45);
      g1.addColorStop(0, 'rgba(255, 224, 102, 0.18)');
      g1.addColorStop(0.2, 'rgba(255, 159, 64, 0.14)');
      g1.addColorStop(0.4, 'rgba(255, 123, 37, 0.10)');
      g1.addColorStop(0.7, 'rgba(230, 92, 0, 0.05)');
      g1.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = g1;
      ctx.fillRect(0, 0, W, H);

      // Subtle warm accent (bottom)
      const g2 = ctx.createRadialGradient(W * 0.6, H * 0.75, 0, W * 0.6, H * 0.75, W * 0.4);
      g2.addColorStop(0, 'rgba(255, 123, 37, 0.06)');
      g2.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = g2;
      ctx.fillRect(0, 0, W, H);
    }

    function drawHexGrid() {
      ctx.save();
      ctx.globalAlpha = 0.08;
      ctx.strokeStyle = COLORS.cyan;
      ctx.lineWidth = 1 * DPR;

      const hexSize = 40 * DPR;
      const hexHeight = hexSize * Math.sqrt(3);
      const hexWidth = hexSize * 2;

      for (let row = -1; row < H / hexHeight + 1; row++) {
        for (let col = -1; col < W / (hexWidth * 0.75) + 1; col++) {
          const x = col * hexWidth * 0.75;
          const y = row * hexHeight + (col % 2 ? hexHeight / 2 : 0);

          // Only draw some hexes for sparse effect
          if (Math.random() < 0.3) {
            drawHex(x, y, hexSize * 0.8);
          }
        }
      }
      ctx.restore();
    }

    function drawHex(cx, cy, size) {
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const angle = (i * 60 - 30) * Math.PI / 180;
        const x = cx + size * Math.cos(angle);
        const y = cy + size * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
    }

    function drawCircuitTraces(dt) {
      // Spawn new traces near progress edge
      if (Math.random() < 0.08 && currentProgress > 0.05) {
        const px = targetX;
        const py = 0.5 + (Math.random() - 0.5) * 0.15;
        circuitTraces.push(createCircuitTrace(px, py, 'left'));
        circuitTraces.push(createCircuitTrace(px, py, 'right'));
      }

      // Update and draw traces
      for (let i = circuitTraces.length - 1; i >= 0; i--) {
        const trace = circuitTraces[i];
        trace.life -= trace.decay;

        if (trace.life <= 0) {
          circuitTraces.splice(i, 1);
          continue;
        }

        ctx.save();
        ctx.globalAlpha = trace.life * 0.7;
        ctx.strokeStyle = trace.color;
        ctx.shadowColor = trace.glowColor;
        ctx.shadowBlur = 15 * DPR;
        ctx.lineWidth = 2 * DPR;
        ctx.lineCap = 'round';

        ctx.beginPath();
        trace.segments.forEach((seg, idx) => {
          const segAlpha = 1 - (idx / trace.segments.length) * 0.5;
          if (idx === 0) {
            ctx.moveTo(seg.x1 * W, seg.y1 * H);
          }
          ctx.lineTo(seg.x2 * W, seg.y2 * H);
        });
        ctx.stroke();

        // Inner bright line
        ctx.shadowBlur = 0;
        ctx.strokeStyle = COLORS.white;
        ctx.lineWidth = 1 * DPR;
        ctx.globalAlpha = trace.life * 0.4;
        ctx.stroke();

        ctx.restore();
      }
    }

    function drawParticles(dt) {
      const tx = targetX * W;
      const ty = targetY * H;

      for (const p of particles) {
        p.t += dt * 0.001;
        p.pulsePhase += p.pulseSpeed;

        // Attraction to progress edge
        const ax = (tx - p.x * W) * 0.0000012;
        const ay = (ty - p.y * H) * 0.0000012;
        p.vx = (p.vx + ax) * 0.988;
        p.vy = (p.vy + ay) * 0.988;
        p.x += p.vx * dt;
        p.y += p.vy * dt;

        // Wrap around
        if (p.x < -0.1) p.x = 1.1;
        if (p.x > 1.1) p.x = -0.1;
        if (p.y < -0.1) p.y = 1.1;
        if (p.y > 1.1) p.y = -0.1;

        const px = p.x * W;
        const py = p.y * H;
        const dist = Math.sqrt((px - tx) ** 2 + (py - ty) ** 2);
        const nearProgress = dist < 150 * DPR;

        // Pulse effect
        const pulse = Math.sin(p.pulsePhase) * 0.3 + 0.7;
        const size = p.size * pulse * DPR;

        // Color based on warmth and proximity - molten theme near progress
        let color, glowColor;
        if (p.warm) {
          if (nearProgress) {
            color = Math.random() < 0.6 ? COLORS.moltenOrange : COLORS.moltenYellow;
            glowColor = Math.random() < 0.6 ? COLORS.moltenOrangeGlow : COLORS.moltenYellowGlow;
          } else {
            color = COLORS.moltenAmber;
            glowColor = COLORS.moltenAmberGlow;
          }
        } else {
          color = nearProgress ? COLORS.moltenYellow : COLORS.blue;
          glowColor = nearProgress ? COLORS.moltenYellowGlow : COLORS.blueGlow;
        }

        // Draw glow
        ctx.save();
        ctx.globalAlpha = p.alpha * (nearProgress ? 1 : 0.6) * pulse;

        if (p.bright || nearProgress) {
          ctx.shadowColor = glowColor;
          ctx.shadowBlur = (p.bright ? 20 : 12) * DPR;
        }

        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(px, py, size, 0, Math.PI * 2);
        ctx.fill();

        // Bright core for special particles
        if (p.bright) {
          ctx.fillStyle = COLORS.white;
          ctx.globalAlpha = p.alpha * 0.8;
          ctx.beginPath();
          ctx.arc(px, py, size * 0.4, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.restore();

        // Draw connecting lines to nearby particles
        if (nearProgress && Math.random() < 0.02) {
          for (const p2 of particles) {
            if (p2 === p) continue;
            const p2x = p2.x * W;
            const p2y = p2.y * H;
            const d = Math.sqrt((px - p2x) ** 2 + (py - p2y) ** 2);
            if (d < 80 * DPR && d > 10 * DPR) {
              ctx.save();
              ctx.globalAlpha = 0.15 * (1 - d / (80 * DPR));
              ctx.strokeStyle = color;
              ctx.lineWidth = 0.5 * DPR;
              ctx.beginPath();
              ctx.moveTo(px, py);
              ctx.lineTo(p2x, p2y);
              ctx.stroke();
              ctx.restore();
              break;
            }
          }
        }
      }
    }

    function drawSparks(dt) {
      for (let i = sparks.length - 1; i >= 0; i--) {
        const s = sparks[i];

        // Store trail
        s.trail.unshift({ x: s.x, y: s.y });
        if (s.trail.length > 8) s.trail.pop();

        s.x += s.vx * dt;
        s.y += s.vy * dt;
        s.vy += 0.00005 * dt; // Slight gravity
        s.life -= s.decay;

        if (s.life <= 0) {
          sparks.splice(i, 1);
          continue;
        }

        // Draw trail
        ctx.save();
        for (let t = 1; t < s.trail.length; t++) {
          const pt = s.trail[t];
          const prevPt = s.trail[t - 1];
          ctx.globalAlpha = s.life * (1 - t / s.trail.length) * 0.5;
          ctx.strokeStyle = s.color;
          ctx.lineWidth = s.size * (1 - t / s.trail.length) * DPR;
          ctx.beginPath();
          ctx.moveTo(prevPt.x * W, prevPt.y * H);
          ctx.lineTo(pt.x * W, pt.y * H);
          ctx.stroke();
        }

        // Draw spark
        ctx.globalAlpha = s.life;
        ctx.fillStyle = s.color;
        ctx.shadowColor = s.color;
        ctx.shadowBlur = 10 * DPR;
        ctx.beginPath();
        ctx.arc(s.x * W, s.y * H, s.size * s.life * DPR, 0, Math.PI * 2);
        ctx.fill();

        // White core
        ctx.fillStyle = COLORS.white;
        ctx.globalAlpha = s.life * 0.8;
        ctx.shadowBlur = 0;
        ctx.beginPath();
        ctx.arc(s.x * W, s.y * H, s.size * s.life * 0.4 * DPR, 0, Math.PI * 2);
        ctx.fill();

        ctx.restore();
      }
    }

    function drawBurstParticles(dt) {
      for (let i = burstParticles.length - 1; i >= 0; i--) {
        const p = burstParticles[i];

        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.vx *= 0.995;
        p.vy *= 0.995;
        p.life -= p.decay;

        if (p.life <= 0) {
          burstParticles.splice(i, 1);
          continue;
        }

        ctx.save();
        ctx.globalAlpha = p.life * 0.8;
        ctx.fillStyle = p.color;
        ctx.shadowColor = p.glow;
        ctx.shadowBlur = 20 * DPR;
        ctx.beginPath();
        ctx.arc(p.x * W, p.y * H, p.size * p.life * DPR, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    function drawProgressGlow() {
      const px = targetX * W;
      const py = targetY * H;

      // Large outer glow - molten orange
      const g0 = ctx.createRadialGradient(px, py, 0, px, py, 250 * DPR);
      g0.addColorStop(0, 'rgba(255, 224, 102, 0.28)');
      g0.addColorStop(0.2, 'rgba(255, 159, 64, 0.22)');
      g0.addColorStop(0.4, 'rgba(255, 123, 37, 0.15)');
      g0.addColorStop(0.7, 'rgba(230, 92, 0, 0.08)');
      g0.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = g0;
      ctx.fillRect(px - 250 * DPR, py - 250 * DPR, 500 * DPR, 500 * DPR);

      // Intense white-hot inner glow
      const g1 = ctx.createRadialGradient(px, py, 0, px, py, 80 * DPR);
      g1.addColorStop(0, 'rgba(255, 255, 255, 0.55)');
      g1.addColorStop(0.15, 'rgba(255, 250, 240, 0.45)');
      g1.addColorStop(0.3, 'rgba(255, 224, 102, 0.35)');
      g1.addColorStop(0.5, 'rgba(255, 159, 64, 0.22)');
      g1.addColorStop(0.7, 'rgba(255, 123, 37, 0.12)');
      g1.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = g1;
      ctx.fillRect(px - 80 * DPR, py - 80 * DPR, 160 * DPR, 160 * DPR);
    }

    // Animation loop
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

    // GSAP sheen animation - SLOW cinematic sweep
    let sheenTL = null;
    if (!prefersReducedMotion && sheen) {
      sheenTL = gsap.to(sheen, {
        x: () => (bar.clientWidth + 320),
        duration: 2.8,
        ease: "power1.inOut",
        repeat: -1,
        repeatDelay: 0.6
      });
    }

    // Progress state
    let current = 0;

    function setPct(p01) {
      if (pctEl) pctEl.textContent = `${Math.round(clamp01(p01) * 100)}%`;
    }

    function updateEdge(p01) {
      const w = bar.clientWidth;
      const edge = w * clamp01(p01);

      if (fill) fill.style.width = `${(clamp01(p01) * 100).toFixed(3)}%`;
      if (orb) orb.style.left = `${edge}px`;

      if (trail) {
        const trailLen = Math.max(100, Math.min(280, 140 + (p01 * 140)));
        trail.style.width = `${trailLen}px`;
        trail.style.left = `${Math.max(0, edge - trailLen)}px`;
      }

      // Update reflection spot position to follow orb
      if (reflectionSpot) reflectionSpot.style.left = `${edge}px`;

      // Update target for particle attraction
      const hero = root.querySelector(".aegis-hero");
      if (hero) {
        const heroRect = hero.getBoundingClientRect();
        const edgeNorm = (heroRect.left + (heroRect.width * 0.07) + (heroRect.width * 0.86 * p01)) / window.innerWidth;
        targetX = Math.max(0, Math.min(1, edgeNorm));
      }
      targetY = 0.50;
      currentProgress = p01;

      // Trigger bursts at milestones
      if (p01 - lastBurstProgress >= 0.15) {
        lastBurstProgress = p01;
        createSparkBurst(targetX, targetY, 25);
        createBurstParticles(targetX, targetY, 30);
      }
    }

    function setProgress(p01) {
      const target = clamp01(p01);
      gsap.to({ v: current }, {
        v: target,
        duration: 0.45,
        ease: "power2.out",
        onUpdate() {
          current = this.targets()[0].v;
          setPct(current);
          updateEdge(current);
        }
      });
    }

    function setStatus(text) {
      if (typeof text === "string" && statusEl) statusEl.textContent = text;
    }

    function complete() {
      setStatus("Complete");

      // Big finale burst
      createSparkBurst(targetX, targetY, 50);
      createBurstParticles(targetX, targetY, 80);

      gsap.timeline()
        .to(fill, { filter: "brightness(1.5) saturate(1.4)", duration: 0.15 })
        .to(fill, { filter: "brightness(1.0) saturate(1.2)", duration: 0.4 })
        .to(root, { opacity: 0, duration: 0.5, ease: "power2.out", delay: 0.3,
          onComplete: () => {
            // Prevent blocking clicks after fade completes
            root.style.pointerEvents = 'none';
            root.style.display = 'none';
            running = false;
          }
        });
    }

    function error() {
      setStatus("Error");
      const panel = root.querySelector(".aegis-center");
      if (panel) {
        gsap.timeline()
          .to(panel, { x: -8, duration: 0.05 })
          .to(panel, { x: 8, duration: 0.05, repeat: 4, yoyo: true })
          .to(panel, { x: 0, duration: 0.05 });
      }
    }

    function destroy() {
      running = false;
      if (sheenTL) sheenTL.kill();
      ro.disconnect();
    }

    // Resize handling
    const ro = new ResizeObserver(() => {
      resize();
      setPct(current);
      updateEdge(current);
    });
    ro.observe(root);

    resize();
    setPct(0);
    updateEdge(0);

    // Initial burst
    setTimeout(() => {
      createSparkBurst(0.1, 0.5, 15);
    }, 200);

    if (!prefersReducedMotion) requestAnimationFrame(loop);

    return { setProgress, setStatus, complete, error, destroy };
  }

  global.CinematicLoader = { mount };
})(window);
