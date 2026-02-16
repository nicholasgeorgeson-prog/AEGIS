/**
 * Cinematic Progress Animation System - Enhanced
 * AEGIS v3.1.7
 *
 * Combines Lottie + GSAP + Rive + Canvas particle effects
 * for true cinematic-quality progress indicators.
 *
 * v3.1.7 Enhancements:
 * - Particle trails with fading history
 * - Particle connections (web effect)
 * - Milestone celebrations (25%, 50%, 75%, 100%)
 * - Enhanced energy trail with sparks
 * - Faster Matrix data streams with depth
 * - Lightning bolts for Circuit theme
 * - Star field for Cosmic theme
 * - Ember particles for Fire theme
 * - Ripple effects at progress head
 * - Grand finale explosion at 100%
 */

const CinematicProgress = (function() {
    'use strict';

    // ========================================
    // Configuration
    // ========================================
    const CONFIG = {
        particleCount: 120,
        glowIntensity: 1.8,
        trailLength: 20,
        animationSpeed: 1,
        soundEnabled: false,
        // New v3.1.7 settings
        particleTrailLength: 5,
        connectionDistance: 80,
        milestones: [0.25, 0.50, 0.75, 1.0],
        sparkCount: 8,
        lightningFrequency: 0.02,
        starCount: 50,
        emberCount: 30,
        matrixStreamCount: 25
    };

    // Cinematic color palettes
    const PALETTES = {
        circuit: {
            primary: '#ff9500',
            secondary: '#ffb347',
            accent: '#00ff88',
            glow: 'rgba(255, 149, 0, 0.8)',
            background: '#0a1520',
            particles: ['#ff9500', '#ffb347', '#ffffff', '#00ff88'],
            lightning: '#ffffff'
        },
        cosmic: {
            primary: '#8b5cf6',
            secondary: '#a78bfa',
            accent: '#06b6d4',
            glow: 'rgba(139, 92, 246, 0.8)',
            background: '#0f0f23',
            particles: ['#8b5cf6', '#a78bfa', '#06b6d4', '#ffffff', '#f472b6'],
            stars: ['#ffffff', '#e0e7ff', '#c7d2fe', '#a5b4fc']
        },
        energy: {
            primary: '#00ff88',
            secondary: '#22c55e',
            accent: '#06b6d4',
            glow: 'rgba(0, 255, 136, 0.8)',
            background: '#0a1a10',
            particles: ['#00ff88', '#22c55e', '#ffffff', '#88ffcc', '#4ade80']
        },
        matrix: {
            primary: '#00ff00',
            secondary: '#00cc00',
            accent: '#88ff88',
            glow: 'rgba(0, 255, 0, 0.7)',
            background: '#000000',
            particles: ['#00ff00', '#00cc00', '#00ff00', '#88ff88'],
            chars: '01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン'.split('')
        },
        fire: {
            primary: '#ff4500',
            secondary: '#ff6b35',
            accent: '#ffd700',
            glow: 'rgba(255, 69, 0, 0.8)',
            background: '#1a0a00',
            particles: ['#ff4500', '#ff6b35', '#ffd700', '#ffffff', '#ff8c00'],
            embers: ['#ff4500', '#ff6b00', '#ff8c00', '#ffa500', '#ffcc00']
        }
    };

    // ========================================
    // Enhanced Particle Class with Trails
    // ========================================
    class Particle {
        constructor(canvas, palette, options = {}) {
            this.canvas = canvas;
            this.palette = palette;
            this.hasTrail = options.hasTrail || false;
            this.trail = [];
            this.maxTrailLength = CONFIG.particleTrailLength;
            this.reset(options);
        }

        reset(options = {}) {
            this.x = options.x !== undefined ? options.x : Math.random() * this.canvas.width;
            this.y = options.y !== undefined ? options.y : Math.random() * this.canvas.height;
            this.vx = options.vx !== undefined ? options.vx : (Math.random() - 0.5) * 2;
            this.vy = options.vy !== undefined ? options.vy : (Math.random() - 0.5) * 2;
            this.size = options.size !== undefined ? options.size : Math.random() * 3 + 1;
            this.alpha = options.alpha !== undefined ? options.alpha : Math.random() * 0.5 + 0.3;
            this.color = options.color || this.palette.particles[Math.floor(Math.random() * this.palette.particles.length)];
            this.life = options.life !== undefined ? options.life : 1;
            this.decay = options.decay !== undefined ? options.decay : Math.random() * 0.01 + 0.005;
            this.isBurst = options.isBurst || false;
            this.trail = [];
        }

        update(progress, attractToProgress = true) {
            // Store trail position
            if (this.hasTrail && this.trail.length < this.maxTrailLength) {
                this.trail.unshift({ x: this.x, y: this.y, alpha: this.alpha });
            } else if (this.hasTrail) {
                this.trail.pop();
                this.trail.unshift({ x: this.x, y: this.y, alpha: this.alpha });
            }

            this.x += this.vx;
            this.y += this.vy;
            this.life -= this.decay;

            // Attract particles toward progress position
            if (attractToProgress) {
                const progressX = this.canvas.width * progress;
                const dx = progressX - this.x;
                const dy = this.canvas.height / 2 - this.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist > 0 && dist < 200) {
                    this.vx += (dx / dist) * 0.05;
                    this.vy += (dy / dist) * 0.05;
                }
            }

            // Apply friction
            this.vx *= 0.99;
            this.vy *= 0.99;

            // Boundary check
            if (!this.isBurst && (
                this.x < 0 || this.x > this.canvas.width ||
                this.y < 0 || this.y > this.canvas.height ||
                this.life <= 0
            )) {
                const progressX = this.canvas.width * progress;
                this.reset();
                // Spawn near progress edge more often
                if (Math.random() > 0.4) {
                    this.x = progressX + (Math.random() - 0.5) * 60;
                    this.y = this.canvas.height / 2 + (Math.random() - 0.5) * 50;
                }
            }

            return this.life > 0;
        }

        draw(ctx) {
            // Draw trail first
            if (this.hasTrail && this.trail.length > 1) {
                ctx.save();
                for (let i = 1; i < this.trail.length; i++) {
                    const t = this.trail[i];
                    const prevT = this.trail[i - 1];
                    const trailAlpha = (1 - i / this.trail.length) * 0.3;
                    ctx.globalAlpha = trailAlpha * this.life;
                    ctx.strokeStyle = this.color;
                    ctx.lineWidth = this.size * (1 - i / this.trail.length);
                    ctx.beginPath();
                    ctx.moveTo(prevT.x, prevT.y);
                    ctx.lineTo(t.x, t.y);
                    ctx.stroke();
                }
                ctx.restore();
            }

            // Draw particle
            ctx.save();
            ctx.globalAlpha = this.alpha * this.life;
            ctx.fillStyle = this.color;
            ctx.shadowColor = this.color;
            ctx.shadowBlur = 10;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }

    // ========================================
    // Spark Class (for energy trail)
    // ========================================
    class Spark {
        constructor(x, y, palette) {
            this.x = x;
            this.y = y;
            this.palette = palette;
            this.angle = Math.random() * Math.PI * 2;
            this.speed = Math.random() * 4 + 2;
            this.vx = Math.cos(this.angle) * this.speed;
            this.vy = Math.sin(this.angle) * this.speed;
            this.size = Math.random() * 2 + 1;
            this.life = 1;
            this.decay = Math.random() * 0.05 + 0.03;
            this.color = palette.primary;
        }

        update() {
            this.x += this.vx;
            this.y += this.vy;
            this.vy += 0.1; // Gravity
            this.life -= this.decay;
            return this.life > 0;
        }

        draw(ctx) {
            ctx.save();
            ctx.globalAlpha = this.life;
            ctx.fillStyle = this.color;
            ctx.shadowColor = this.palette.glow;
            ctx.shadowBlur = 5;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size * this.life, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }

    // ========================================
    // Lightning Bolt Class (Circuit theme)
    // ========================================
    class LightningBolt {
        constructor(canvas, startX, startY, endX, endY, palette) {
            this.canvas = canvas;
            this.startX = startX;
            this.startY = startY;
            this.endX = endX;
            this.endY = endY;
            this.palette = palette;
            this.segments = [];
            this.life = 1;
            this.decay = 0.08;
            this.generateSegments();
        }

        generateSegments() {
            const dx = this.endX - this.startX;
            const dy = this.endY - this.startY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const segmentCount = Math.floor(dist / 15) + 2;

            let x = this.startX;
            let y = this.startY;
            this.segments = [{ x, y }];

            for (let i = 1; i < segmentCount; i++) {
                const t = i / segmentCount;
                x = this.startX + dx * t + (Math.random() - 0.5) * 30;
                y = this.startY + dy * t + (Math.random() - 0.5) * 20;
                this.segments.push({ x, y });
            }
            this.segments.push({ x: this.endX, y: this.endY });
        }

        update() {
            this.life -= this.decay;
            return this.life > 0;
        }

        draw(ctx) {
            if (this.segments.length < 2) return;

            ctx.save();
            ctx.globalAlpha = this.life;
            ctx.strokeStyle = this.palette.lightning || '#ffffff';
            ctx.shadowColor = this.palette.glow;
            ctx.shadowBlur = 20;
            ctx.lineWidth = 2;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            ctx.beginPath();
            ctx.moveTo(this.segments[0].x, this.segments[0].y);
            for (let i = 1; i < this.segments.length; i++) {
                ctx.lineTo(this.segments[i].x, this.segments[i].y);
            }
            ctx.stroke();

            // Inner glow
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1;
            ctx.globalAlpha = this.life * 0.8;
            ctx.stroke();

            ctx.restore();
        }
    }

    // ========================================
    // Star Class (Cosmic theme)
    // ========================================
    class Star {
        constructor(canvas, palette) {
            this.canvas = canvas;
            this.palette = palette;
            this.reset();
        }

        reset() {
            this.x = Math.random() * this.canvas.width;
            this.y = Math.random() * this.canvas.height;
            this.size = Math.random() * 2 + 0.5;
            this.twinkleSpeed = Math.random() * 0.05 + 0.02;
            this.twinklePhase = Math.random() * Math.PI * 2;
            this.baseAlpha = Math.random() * 0.5 + 0.3;
            this.color = this.palette.stars ?
                this.palette.stars[Math.floor(Math.random() * this.palette.stars.length)] :
                '#ffffff';
        }

        update(progress, time) {
            this.twinklePhase += this.twinkleSpeed;

            // Move slowly toward progress
            const progressX = this.canvas.width * progress;
            if (this.x < progressX - 50) {
                this.x += 0.3;
            }
        }

        draw(ctx, time) {
            const twinkle = Math.sin(this.twinklePhase) * 0.3 + 0.7;
            const alpha = this.baseAlpha * twinkle;

            ctx.save();
            ctx.globalAlpha = alpha;
            ctx.fillStyle = this.color;
            ctx.shadowColor = this.color;
            ctx.shadowBlur = 5;

            // Draw star shape
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();

            // Add cross shine for larger stars
            if (this.size > 1.5) {
                ctx.globalAlpha = alpha * 0.5;
                ctx.strokeStyle = this.color;
                ctx.lineWidth = 0.5;
                ctx.beginPath();
                ctx.moveTo(this.x - this.size * 2, this.y);
                ctx.lineTo(this.x + this.size * 2, this.y);
                ctx.moveTo(this.x, this.y - this.size * 2);
                ctx.lineTo(this.x, this.y + this.size * 2);
                ctx.stroke();
            }

            ctx.restore();
        }
    }

    // ========================================
    // Ember Class (Fire theme)
    // ========================================
    class Ember {
        constructor(canvas, palette, x, y) {
            this.canvas = canvas;
            this.palette = palette;
            this.reset(x, y);
        }

        reset(x, y) {
            this.x = x !== undefined ? x : Math.random() * this.canvas.width;
            this.y = y !== undefined ? y : this.canvas.height + 10;
            this.vx = (Math.random() - 0.5) * 2;
            this.vy = -Math.random() * 3 - 1;
            this.size = Math.random() * 3 + 1;
            this.life = 1;
            this.decay = Math.random() * 0.015 + 0.008;
            this.color = this.palette.embers ?
                this.palette.embers[Math.floor(Math.random() * this.palette.embers.length)] :
                this.palette.primary;
            this.wobbleSpeed = Math.random() * 0.1 + 0.05;
            this.wobblePhase = Math.random() * Math.PI * 2;
        }

        update(progress) {
            this.wobblePhase += this.wobbleSpeed;
            this.x += this.vx + Math.sin(this.wobblePhase) * 0.5;
            this.y += this.vy;
            this.vy *= 0.99;
            this.life -= this.decay;

            // Pull toward progress position
            const progressX = this.canvas.width * 0.1 + this.canvas.width * 0.8 * progress;
            const dx = progressX - this.x;
            if (Math.abs(dx) < 100) {
                this.vx += dx * 0.001;
            }

            if (this.y < -10 || this.life <= 0) {
                this.reset(progressX + (Math.random() - 0.5) * 100, this.canvas.height + 10);
            }

            return this.life > 0;
        }

        draw(ctx) {
            ctx.save();
            ctx.globalAlpha = this.life * 0.8;

            // Gradient for ember
            const gradient = ctx.createRadialGradient(
                this.x, this.y, 0,
                this.x, this.y, this.size * 2
            );
            gradient.addColorStop(0, '#ffffff');
            gradient.addColorStop(0.3, this.color);
            gradient.addColorStop(1, 'transparent');

            ctx.fillStyle = gradient;
            ctx.shadowColor = this.color;
            ctx.shadowBlur = 10;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size * this.life, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();
        }
    }

    // ========================================
    // Enhanced Energy Trail Class
    // ========================================
    class EnergyTrail {
        constructor(canvas, palette) {
            this.canvas = canvas;
            this.palette = palette;
            this.points = [];
            this.maxPoints = CONFIG.trailLength;
            this.sparks = [];
            this.lastSparkTime = 0;
        }

        update(progress) {
            const x = this.canvas.width * 0.1 + this.canvas.width * 0.8 * progress;
            const y = this.canvas.height / 2;

            this.points.unshift({ x, y, alpha: 1 });

            if (this.points.length > this.maxPoints) {
                this.points.pop();
            }

            this.points.forEach((point, i) => {
                point.alpha = 1 - (i / this.maxPoints);
            });

            // Generate sparks periodically
            const now = Date.now();
            if (now - this.lastSparkTime > 50 && this.points.length > 0) {
                this.lastSparkTime = now;
                for (let i = 0; i < CONFIG.sparkCount; i++) {
                    this.sparks.push(new Spark(
                        this.points[0].x,
                        this.points[0].y + (Math.random() - 0.5) * 10,
                        this.palette
                    ));
                }
            }

            // Update sparks
            this.sparks = this.sparks.filter(spark => spark.update());
        }

        draw(ctx) {
            // Draw sparks
            this.sparks.forEach(spark => spark.draw(ctx));

            if (this.points.length < 2) return;

            ctx.save();

            // Draw outer glow trail
            for (let i = 1; i < this.points.length; i++) {
                const p1 = this.points[i - 1];
                const p2 = this.points[i];

                const gradient = ctx.createLinearGradient(p1.x, p1.y, p2.x, p2.y);
                gradient.addColorStop(0, this.palette.primary);
                gradient.addColorStop(1, this.palette.secondary);

                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.strokeStyle = gradient;
                ctx.lineWidth = (this.maxPoints - i) * 1.2;
                ctx.globalAlpha = p2.alpha * 0.5;
                ctx.shadowColor = this.palette.glow;
                ctx.shadowBlur = 25;
                ctx.stroke();
            }

            // Draw inner bright trail
            ctx.globalCompositeOperation = 'lighter';
            for (let i = 1; i < Math.min(this.points.length, 8); i++) {
                const p1 = this.points[i - 1];
                const p2 = this.points[i];

                ctx.beginPath();
                ctx.moveTo(p1.x, p1.y);
                ctx.lineTo(p2.x, p2.y);
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = (8 - i) * 0.5;
                ctx.globalAlpha = (1 - i / 8) * 0.6;
                ctx.stroke();
            }

            // Draw leading orb with ripple
            if (this.points.length > 0) {
                const lead = this.points[0];

                // Ripple effect
                const time = Date.now() * 0.005;
                for (let r = 0; r < 3; r++) {
                    const rippleSize = 20 + r * 8 + Math.sin(time + r) * 5;
                    ctx.globalAlpha = (0.3 - r * 0.1) * (1 + Math.sin(time + r * 0.5) * 0.3);
                    ctx.strokeStyle = this.palette.primary;
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.arc(lead.x, lead.y, rippleSize, 0, Math.PI * 2);
                    ctx.stroke();
                }

                // Core orb
                const orbGradient = ctx.createRadialGradient(lead.x, lead.y, 0, lead.x, lead.y, 18);
                orbGradient.addColorStop(0, '#ffffff');
                orbGradient.addColorStop(0.2, this.palette.primary);
                orbGradient.addColorStop(0.6, this.palette.secondary);
                orbGradient.addColorStop(1, 'transparent');

                ctx.globalAlpha = 1;
                ctx.globalCompositeOperation = 'source-over';
                ctx.fillStyle = orbGradient;
                ctx.shadowColor = this.palette.glow;
                ctx.shadowBlur = 30;
                ctx.beginPath();
                ctx.arc(lead.x, lead.y, 18, 0, Math.PI * 2);
                ctx.fill();
            }

            ctx.restore();
        }
    }

    // ========================================
    // Enhanced Data Stream Class (Matrix)
    // ========================================
    class DataStream {
        constructor(canvas, palette, x) {
            this.canvas = canvas;
            this.palette = palette;
            this.x = x;
            this.chars = palette.chars || '01アイウエオカキクケコ'.split('');
            this.drops = [];
            this.depth = Math.random(); // 0 = far, 1 = near
            this.initDrops();
        }

        initDrops() {
            const count = Math.floor(Math.random() * 8) + 5;
            for (let i = 0; i < count; i++) {
                this.drops.push({
                    y: Math.random() * this.canvas.height - this.canvas.height,
                    speed: (Math.random() * 2 + 1.5) * (0.5 + this.depth * 0.5),
                    char: this.chars[Math.floor(Math.random() * this.chars.length)],
                    alpha: (Math.random() * 0.5 + 0.5) * (0.3 + this.depth * 0.7),
                    changeRate: Math.random() * 0.1
                });
            }
        }

        update(progress) {
            const progressX = this.canvas.width * 0.1 + this.canvas.width * 0.8 * progress;

            this.drops.forEach(drop => {
                drop.y += drop.speed;

                // Random character change
                if (Math.random() < drop.changeRate) {
                    drop.char = this.chars[Math.floor(Math.random() * this.chars.length)];
                }

                if (drop.y > this.canvas.height + 20) {
                    drop.y = -20;
                    drop.char = this.chars[Math.floor(Math.random() * this.chars.length)];
                }

                // Intensify near progress line
                const distToProgress = Math.abs(this.x - progressX);
                if (distToProgress < 50) {
                    drop.alpha = Math.min(1, drop.alpha + 0.15);
                    drop.speed = Math.min(10, drop.speed + 0.1);
                } else {
                    drop.alpha = Math.max(0.1 + this.depth * 0.2, drop.alpha - 0.03);
                }
            });
        }

        draw(ctx) {
            ctx.save();
            const fontSize = 12 + this.depth * 6;
            ctx.font = `${fontSize}px monospace`;

            this.drops.forEach((drop, index) => {
                // Head character (brightest)
                ctx.globalAlpha = drop.alpha;
                ctx.fillStyle = index === 0 ? '#ffffff' : this.palette.primary;
                ctx.shadowColor = this.palette.glow;
                ctx.shadowBlur = 8 + this.depth * 8;
                ctx.fillText(drop.char, this.x, drop.y);

                // Trail of previous characters
                if (index === 0) {
                    for (let t = 1; t < 6; t++) {
                        ctx.globalAlpha = drop.alpha * (1 - t * 0.18);
                        ctx.fillStyle = this.palette.primary;
                        const trailChar = this.chars[Math.floor(Math.random() * this.chars.length)];
                        ctx.fillText(trailChar, this.x, drop.y - t * fontSize);
                    }
                }
            });

            ctx.restore();
        }
    }

    // ========================================
    // Milestone Celebration Class
    // ========================================
    class MilestoneCelebration {
        constructor(canvas, palette, x, y, milestone) {
            this.canvas = canvas;
            this.palette = palette;
            this.x = x;
            this.y = y;
            this.milestone = milestone;
            this.particles = [];
            this.rings = [];
            this.life = 1;
            this.decay = milestone === 1.0 ? 0.008 : 0.015;
            this.createEffects();
        }

        createEffects() {
            const particleCount = this.milestone === 1.0 ? 100 : 40;

            // Burst particles
            for (let i = 0; i < particleCount; i++) {
                const angle = (i / particleCount) * Math.PI * 2;
                const speed = Math.random() * 8 + 4;
                this.particles.push({
                    x: this.x,
                    y: this.y,
                    vx: Math.cos(angle) * speed * (0.5 + Math.random() * 0.5),
                    vy: Math.sin(angle) * speed * (0.5 + Math.random() * 0.5),
                    size: Math.random() * 4 + 2,
                    color: this.palette.particles[Math.floor(Math.random() * this.palette.particles.length)],
                    life: 1,
                    decay: Math.random() * 0.02 + 0.01
                });
            }

            // Expanding rings
            for (let i = 0; i < 3; i++) {
                this.rings.push({
                    radius: 10 + i * 5,
                    maxRadius: 100 + i * 30,
                    alpha: 1 - i * 0.2,
                    lineWidth: 3 - i
                });
            }
        }

        update() {
            this.life -= this.decay;

            // Update particles
            this.particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;
                p.vy += 0.15; // Gravity
                p.vx *= 0.98;
                p.life -= p.decay;
            });

            // Update rings
            this.rings.forEach(ring => {
                ring.radius += (ring.maxRadius - ring.radius) * 0.1;
                ring.alpha *= 0.95;
            });

            return this.life > 0;
        }

        draw(ctx) {
            ctx.save();

            // Draw rings
            this.rings.forEach(ring => {
                ctx.globalAlpha = ring.alpha * this.life;
                ctx.strokeStyle = this.palette.primary;
                ctx.lineWidth = ring.lineWidth;
                ctx.shadowColor = this.palette.glow;
                ctx.shadowBlur = 20;
                ctx.beginPath();
                ctx.arc(this.x, this.y, ring.radius, 0, Math.PI * 2);
                ctx.stroke();
            });

            // Draw particles
            this.particles.forEach(p => {
                if (p.life <= 0) return;
                ctx.globalAlpha = p.life * this.life;
                ctx.fillStyle = p.color;
                ctx.shadowColor = p.color;
                ctx.shadowBlur = 10;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
                ctx.fill();
            });

            // Draw milestone text for 100%
            if (this.milestone === 1.0 && this.life > 0.5) {
                ctx.globalAlpha = (this.life - 0.5) * 2;
                ctx.font = 'bold 24px sans-serif';
                ctx.fillStyle = '#ffffff';
                ctx.textAlign = 'center';
                ctx.shadowColor = this.palette.glow;
                ctx.shadowBlur = 20;
                ctx.fillText('COMPLETE!', this.x, this.y - 40);
            }

            ctx.restore();
        }
    }

    // ========================================
    // Main CinematicProgressBar Class
    // ========================================
    class CinematicProgressBar {
        constructor(container, options = {}) {
            this.container = typeof container === 'string'
                ? document.querySelector(container)
                : container;

            if (!this.container) {
                console.error('[CinematicProgress] Container not found');
                return;
            }

            this.options = {
                theme: 'matrix',
                width: options.width || this.container.offsetWidth || 600,
                height: options.height || 100,
                showPercentage: true,
                showParticles: true,
                showTrail: true,
                showGlow: true,
                showDataStreams: false,
                showConnections: true,
                showLightning: true,
                showStars: true,
                showEmbers: true,
                lottieAnimation: null,
                riveAnimation: null,
                riveStateMachine: null,
                onProgress: null,
                onComplete: null,
                onMilestone: null,
                ...options
            };

            this.progress = 0;
            this.targetProgress = 0;
            this.palette = PALETTES[this.options.theme] || PALETTES.circuit;
            this.particles = [];
            this.dataStreams = [];
            this.stars = [];
            this.embers = [];
            this.lightningBolts = [];
            this.celebrations = [];
            this.milestonesReached = new Set();
            this.isAnimating = false;
            this.gsapTimeline = null;
            this.lottieInstance = null;
            this.riveInstance = null;
            this.animationTime = 0;

            this.init();
        }

        init() {
            this.createDOM();
            this.createCanvas();
            this.initParticles();
            this.initThemeEffects();
            this.initGSAP();

            if (this.options.lottieAnimation) {
                this.initLottie();
            }

            if (this.options.riveAnimation) {
                this.initRive();
            }

            if (this.options.showDataStreams || this.options.theme === 'matrix') {
                this.initDataStreams();
            }

            this.startAnimation();
        }

        createDOM() {
            this.container.innerHTML = '';
            this.container.style.position = 'relative';
            this.container.style.width = this.options.width + 'px';
            this.container.style.height = this.options.height + 'px';
            this.container.style.overflow = 'hidden';
            this.container.style.borderRadius = '8px';
            this.container.style.background = this.palette.background;

            // Canvas layer
            this.canvasContainer = document.createElement('div');
            this.canvasContainer.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;';
            this.container.appendChild(this.canvasContainer);

            // Lottie layer
            this.lottieContainer = document.createElement('div');
            this.lottieContainer.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;';
            this.container.appendChild(this.lottieContainer);

            // Molten progress bar
            this.track = document.createElement('div');
            this.track.className = 'molten-progress molten-small molten-with-reflection';
            this.track.style.cssText = `
                position: absolute;
                top: 50%;
                left: 10%;
                width: 80%;
                transform: translateY(-50%);
            `;
            this.container.appendChild(this.track);

            // Rail
            const rail = document.createElement('div');
            rail.className = 'molten-rail';
            this.track.appendChild(rail);

            // Progress bar fill
            this.fill = document.createElement('div');
            this.fill.className = 'molten-fill';
            this.fill.style.width = '0%';
            this.track.appendChild(this.fill);

            // Orb
            this.orb = document.createElement('div');
            this.orb.className = 'molten-orb';
            this.orb.style.left = '0%';
            this.track.appendChild(this.orb);

            // Percentage display
            if (this.options.showPercentage) {
                this.percentDisplay = document.createElement('div');
                this.percentDisplay.style.cssText = `
                    position: absolute;
                    top: 50%;
                    right: 10%;
                    transform: translate(50%, -50%);
                    font-family: 'JetBrains Mono', 'Fira Code', monospace;
                    font-size: 28px;
                    font-weight: bold;
                    color: ${this.palette.primary};
                    text-shadow: 0 0 15px ${this.palette.glow};
                `;
                this.percentDisplay.textContent = '0%';
                this.container.appendChild(this.percentDisplay);
            }
        }

        createCanvas() {
            this.canvas = document.createElement('canvas');
            this.canvas.width = this.options.width;
            this.canvas.height = this.options.height;
            this.canvas.style.cssText = 'position:absolute;top:0;left:0;';
            this.canvasContainer.appendChild(this.canvas);
            this.ctx = this.canvas.getContext('2d');
        }

        initParticles() {
            if (!this.options.showParticles) return;

            for (let i = 0; i < CONFIG.particleCount; i++) {
                this.particles.push(new Particle(this.canvas, this.palette, {
                    hasTrail: i < CONFIG.particleCount * 0.3 // 30% have trails
                }));
            }

            if (this.options.showTrail) {
                this.trail = new EnergyTrail(this.canvas, this.palette);
            }
        }

        initThemeEffects() {
            const theme = this.options.theme;

            // Cosmic theme: add stars
            if (theme === 'cosmic' && this.options.showStars) {
                for (let i = 0; i < CONFIG.starCount; i++) {
                    this.stars.push(new Star(this.canvas, this.palette));
                }
            }

            // Fire theme: add embers
            if (theme === 'fire' && this.options.showEmbers) {
                for (let i = 0; i < CONFIG.emberCount; i++) {
                    this.embers.push(new Ember(this.canvas, this.palette));
                }
            }
        }

        initDataStreams() {
            const streamCount = CONFIG.matrixStreamCount;
            const spacing = this.canvas.width / streamCount;
            for (let i = 0; i < streamCount; i++) {
                this.dataStreams.push(new DataStream(
                    this.canvas,
                    this.palette,
                    i * spacing + Math.random() * spacing * 0.5
                ));
            }
        }

        initGSAP() {
            if (typeof gsap === 'undefined') {
                console.warn('[CinematicProgress] GSAP not loaded, using fallback animations');
                return;
            }

            this.gsapTimeline = gsap.timeline({ paused: true });

            this.gsapTimeline.from(this.track, {
                scaleX: 0,
                duration: 0.5,
                ease: 'power2.out'
            });

            if (this.percentDisplay) {
                this.gsapTimeline.from(this.percentDisplay, {
                    opacity: 0,
                    scale: 0.5,
                    duration: 0.4,
                    ease: 'back.out(2)'
                }, '-=0.2');
            }
        }

        initLottie() {
            if (typeof lottie === 'undefined') {
                console.warn('[CinematicProgress] Lottie not loaded');
                return;
            }

            this.lottieInstance = lottie.loadAnimation({
                container: this.lottieContainer,
                renderer: 'svg',
                loop: true,
                autoplay: false,
                path: this.options.lottieAnimation
            });

            this.lottieInstance.addEventListener('DOMLoaded', () => {
                console.log('[CinematicProgress] Lottie animation loaded');
            });
        }

        initRive() {
            if (typeof rive === 'undefined' && typeof Rive === 'undefined') {
                console.warn('[CinematicProgress] Rive runtime not loaded');
                return;
            }

            const RiveLib = typeof Rive !== 'undefined' ? Rive : rive;

            this.riveCanvas = document.createElement('canvas');
            this.riveCanvas.width = this.options.width;
            this.riveCanvas.height = this.options.height;
            this.riveCanvas.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;';
            this.container.insertBefore(this.riveCanvas, this.container.firstChild);

            try {
                this.riveInstance = new RiveLib.Rive({
                    src: this.options.riveAnimation,
                    canvas: this.riveCanvas,
                    autoplay: true,
                    stateMachines: this.options.riveStateMachine || 'State Machine 1',
                    onLoad: () => {
                        console.log('[CinematicProgress] Rive animation loaded');
                        if (this.riveInstance.stateMachineInputs) {
                            this.riveInputs = this.riveInstance.stateMachineInputs(
                                this.options.riveStateMachine || 'State Machine 1'
                            );
                            this.riveProgressInput = this.riveInputs?.find(
                                i => i.name.toLowerCase().includes('progress')
                            );
                        }
                    },
                    onLoadError: (err) => {
                        console.warn('[CinematicProgress] Rive load error:', err);
                    }
                });
            } catch (err) {
                console.warn('[CinematicProgress] Rive initialization error:', err);
            }
        }

        startAnimation() {
            this.isAnimating = true;

            if (this.gsapTimeline) {
                this.gsapTimeline.play();
            }

            if (this.lottieInstance) {
                this.lottieInstance.play();
            }

            if (this.riveInstance && this.riveInstance.play) {
                this.riveInstance.play();
            }

            this.animate();
        }

        animate() {
            if (!this.isAnimating) return;

            this.animationTime++;

            // Clear canvas
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            // Smooth progress interpolation
            this.progress += (this.targetProgress - this.progress) * 0.08;

            // Check milestones
            this.checkMilestones();

            // Draw theme-specific background effects
            this.drawThemeEffects();

            // Update and draw data streams (Matrix theme)
            this.dataStreams.forEach(stream => {
                stream.update(this.progress);
                stream.draw(this.ctx);
            });

            // Draw particle connections
            if (this.options.showConnections && this.options.theme !== 'matrix') {
                this.drawConnections();
            }

            // Update and draw particles
            this.particles.forEach(particle => {
                particle.update(this.progress);
                particle.draw(this.ctx);
            });

            // Update and draw lightning (Circuit theme)
            if (this.options.theme === 'circuit' && this.options.showLightning) {
                this.updateLightning();
            }

            // Update and draw trail
            if (this.trail) {
                this.trail.update(this.progress);
                this.trail.draw(this.ctx);
            }

            // Draw glow effect at progress edge
            if (this.options.showGlow) {
                this.drawProgressGlow();
            }

            // Update and draw celebrations
            this.celebrations = this.celebrations.filter(c => {
                const alive = c.update();
                c.draw(this.ctx);
                return alive;
            });

            // Update fill width and orb position
            const percent = this.progress * 100;
            this.fill.style.width = percent + '%';
            if (this.orb) this.orb.style.left = percent + '%';
            // Handle complete state
            if (percent >= 100 && this.track) {
                this.track.classList.add('molten-complete');
            }

            // Update percentage display
            if (this.percentDisplay) {
                const displayPercent = Math.round(this.progress * 100);
                if (typeof gsap !== 'undefined' && this.percentDisplay._gsapTween === undefined) {
                    this.percentDisplay._gsapTween = true;
                    gsap.to(this.percentDisplay, {
                        textContent: displayPercent,
                        duration: 0.3,
                        snap: { textContent: 1 },
                        ease: 'power1.out',
                        onUpdate: () => {
                            this.percentDisplay.textContent = Math.round(parseFloat(this.percentDisplay.textContent) || 0) + '%';
                        },
                        onComplete: () => {
                            this.percentDisplay._gsapTween = undefined;
                        }
                    });
                } else if (typeof gsap === 'undefined') {
                    this.percentDisplay.textContent = displayPercent + '%';
                }
            }

            // Callback
            if (this.options.onProgress) {
                this.options.onProgress(this.progress);
            }

            // Check completion
            if (this.progress >= 0.995 && this.targetProgress >= 1) {
                this.onComplete();
            }

            requestAnimationFrame(() => this.animate());
        }

        drawThemeEffects() {
            const theme = this.options.theme;

            // Cosmic: stars
            if (theme === 'cosmic') {
                this.stars.forEach(star => {
                    star.update(this.progress, this.animationTime);
                    star.draw(this.ctx, this.animationTime);
                });
            }

            // Fire: embers
            if (theme === 'fire') {
                this.embers.forEach(ember => {
                    ember.update(this.progress);
                    ember.draw(this.ctx);
                });
            }
        }

        drawConnections() {
            const ctx = this.ctx;
            ctx.save();

            for (let i = 0; i < this.particles.length; i++) {
                for (let j = i + 1; j < this.particles.length; j++) {
                    const p1 = this.particles[i];
                    const p2 = this.particles[j];
                    const dx = p1.x - p2.x;
                    const dy = p1.y - p2.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < CONFIG.connectionDistance) {
                        const alpha = (1 - dist / CONFIG.connectionDistance) * 0.2 * p1.life * p2.life;
                        ctx.globalAlpha = alpha;
                        ctx.strokeStyle = this.palette.primary;
                        ctx.lineWidth = 0.5;
                        ctx.beginPath();
                        ctx.moveTo(p1.x, p1.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.stroke();
                    }
                }
            }

            ctx.restore();
        }

        updateLightning() {
            // Occasionally spawn lightning
            if (Math.random() < CONFIG.lightningFrequency && this.progress > 0.05) {
                const progressX = this.canvas.width * 0.1 + this.canvas.width * 0.8 * this.progress;
                const startX = progressX - 30 + Math.random() * 60;
                const startY = Math.random() * this.canvas.height * 0.3;
                const endX = progressX + (Math.random() - 0.5) * 40;
                const endY = this.canvas.height / 2 + (Math.random() - 0.5) * 20;

                this.lightningBolts.push(new LightningBolt(
                    this.canvas,
                    startX, startY,
                    endX, endY,
                    this.palette
                ));
            }

            // Update and draw lightning
            this.lightningBolts = this.lightningBolts.filter(bolt => {
                const alive = bolt.update();
                bolt.draw(this.ctx);
                return alive;
            });
        }

        checkMilestones() {
            CONFIG.milestones.forEach(milestone => {
                if (this.progress >= milestone - 0.01 && !this.milestonesReached.has(milestone)) {
                    this.milestonesReached.add(milestone);
                    this.triggerMilestone(milestone);
                }
            });
        }

        triggerMilestone(milestone) {
            const x = this.canvas.width * 0.1 + this.canvas.width * 0.8 * milestone;
            const y = this.canvas.height / 2;

            this.celebrations.push(new MilestoneCelebration(
                this.canvas,
                this.palette,
                x,
                y,
                milestone
            ));

            // GSAP pulse effect
            if (typeof gsap !== 'undefined') {
                gsap.to(this.fill, {
                    boxShadow: `0 0 40px ${this.palette.glow}, 0 0 80px ${this.palette.glow}`,
                    duration: 0.2,
                    yoyo: true,
                    repeat: 1
                });

                if (this.percentDisplay) {
                    gsap.to(this.percentDisplay, {
                        scale: 1.2,
                        duration: 0.15,
                        yoyo: true,
                        repeat: 1,
                        ease: 'back.out(2)'
                    });
                }
            }

            // Callback
            if (this.options.onMilestone) {
                this.options.onMilestone(milestone);
            }

            console.log(`[CinematicProgress] Milestone reached: ${milestone * 100}%`);
        }

        drawProgressGlow() {
            const x = this.canvas.width * 0.1 + (this.canvas.width * 0.8 * this.progress);
            const y = this.canvas.height / 2;

            const gradient = this.ctx.createRadialGradient(x, y, 0, x, y, 80);
            gradient.addColorStop(0, this.palette.glow);
            gradient.addColorStop(0.3, 'rgba(255,255,255,0.15)');
            gradient.addColorStop(1, 'transparent');

            this.ctx.save();
            this.ctx.globalCompositeOperation = 'screen';
            this.ctx.fillStyle = gradient;
            this.ctx.fillRect(x - 80, y - 80, 160, 160);
            this.ctx.restore();
        }

        setProgress(value) {
            this.targetProgress = Math.max(0, Math.min(1, value));

            if (this.lottieInstance) {
                const frame = Math.floor(this.lottieInstance.totalFrames * this.targetProgress);
                this.lottieInstance.goToAndStop(frame, true);
            }

            if (this.riveProgressInput && this.riveProgressInput.value !== undefined) {
                this.riveProgressInput.value = this.targetProgress * 100;
            }
        }

        onComplete() {
            if (this.completed) return;
            this.completed = true;

            console.log('[CinematicProgress] Animation complete!');

            // Grand finale burst
            if (typeof gsap !== 'undefined') {
                gsap.to(this.fill, {
                    boxShadow: `0 0 60px ${this.palette.glow}, 0 0 120px ${this.palette.glow}`,
                    duration: 0.3,
                    yoyo: true,
                    repeat: 3
                });

                gsap.to(this.container, {
                    scale: 1.02,
                    duration: 0.2,
                    yoyo: true,
                    repeat: 1,
                    ease: 'power2.out'
                });
            }

            // Spawn burst particles
            for (let i = 0; i < 80; i++) {
                const angle = (i / 80) * Math.PI * 2;
                const speed = Math.random() * 12 + 5;
                const p = new Particle(this.canvas, this.palette, {
                    x: this.canvas.width * 0.9,
                    y: this.canvas.height / 2,
                    vx: Math.cos(angle) * speed,
                    vy: Math.sin(angle) * speed,
                    size: Math.random() * 5 + 2,
                    decay: 0.02,
                    isBurst: true,
                    hasTrail: true
                });
                this.particles.push(p);
            }

            if (this.options.onComplete) {
                this.options.onComplete();
            }
        }

        setTheme(themeName) {
            if (PALETTES[themeName]) {
                this.options.theme = themeName;
                this.palette = PALETTES[themeName];
                this.container.style.background = this.palette.background;
                this.fill.style.background = `linear-gradient(90deg, ${this.palette.primary}, ${this.palette.secondary})`;
                this.fill.style.boxShadow = `0 0 20px ${this.palette.glow}, 0 0 40px ${this.palette.glow}`;

                if (this.percentDisplay) {
                    this.percentDisplay.style.color = this.palette.primary;
                    this.percentDisplay.style.textShadow = `0 0 15px ${this.palette.glow}`;
                }

                // Update particle colors
                this.particles.forEach(p => {
                    p.palette = this.palette;
                    p.color = this.palette.particles[Math.floor(Math.random() * this.palette.particles.length)];
                });

                if (this.trail) {
                    this.trail.palette = this.palette;
                }

                // Update data streams
                this.dataStreams.forEach(s => {
                    s.palette = this.palette;
                    s.chars = this.palette.chars || '01アイウエオカキクケコ'.split('');
                });

                // Re-init theme-specific effects
                this.stars = [];
                this.embers = [];
                this.lightningBolts = [];

                if (themeName === 'cosmic') {
                    for (let i = 0; i < CONFIG.starCount; i++) {
                        this.stars.push(new Star(this.canvas, this.palette));
                    }
                }

                if (themeName === 'fire') {
                    for (let i = 0; i < CONFIG.emberCount; i++) {
                        this.embers.push(new Ember(this.canvas, this.palette));
                    }
                }

                // Toggle data streams for matrix
                if (themeName === 'matrix' && this.dataStreams.length === 0) {
                    this.initDataStreams();
                } else if (themeName !== 'matrix') {
                    this.dataStreams = [];
                }

                console.log(`[CinematicProgress] Theme changed to: ${themeName}`);
            }
        }

        destroy() {
            this.isAnimating = false;

            if (this.gsapTimeline) {
                this.gsapTimeline.kill();
            }

            if (this.lottieInstance) {
                this.lottieInstance.destroy();
            }

            if (this.riveInstance) {
                this.riveInstance.cleanup();
                this.riveInstance = null;
            }

            this.container.innerHTML = '';
        }

        reset() {
            this.progress = 0;
            this.targetProgress = 0;
            this.completed = false;
            this.milestonesReached.clear();
            this.celebrations = [];
            this.lightningBolts = [];
            this.fill.style.width = '0%';
            if (this.orb) this.orb.style.left = '0%';
            if (this.track) this.track.classList.remove('molten-complete');

            if (this.percentDisplay) {
                this.percentDisplay.textContent = '0%';
            }

            if (this.lottieInstance) {
                this.lottieInstance.goToAndStop(0, true);
            }

            if (this.riveProgressInput) {
                this.riveProgressInput.value = 0;
            }
        }
    }

    // ========================================
    // Preset Factory
    // ========================================
    const createPreset = {
        circuit: (container, options = {}) => {
            return new CinematicProgressBar(container, {
                theme: 'circuit',
                showParticles: true,
                showTrail: true,
                showGlow: true,
                showConnections: true,
                showLightning: true,
                ...options
            });
        },

        cosmic: (container, options = {}) => {
            return new CinematicProgressBar(container, {
                theme: 'cosmic',
                showParticles: true,
                showTrail: true,
                showGlow: true,
                showConnections: true,
                showStars: true,
                ...options
            });
        },

        matrix: (container, options = {}) => {
            return new CinematicProgressBar(container, {
                theme: 'matrix',
                showParticles: false,
                showTrail: false,
                showGlow: true,
                showDataStreams: true,
                showConnections: false,
                ...options
            });
        },

        energy: (container, options = {}) => {
            return new CinematicProgressBar(container, {
                theme: 'energy',
                showParticles: true,
                showTrail: true,
                showGlow: true,
                showConnections: true,
                ...options
            });
        },

        fire: (container, options = {}) => {
            return new CinematicProgressBar(container, {
                theme: 'fire',
                showParticles: true,
                showTrail: true,
                showGlow: true,
                showConnections: true,
                showEmbers: true,
                ...options
            });
        },

        minimal: (container, options = {}) => {
            return new CinematicProgressBar(container, {
                theme: 'circuit',
                showParticles: false,
                showTrail: true,
                showGlow: true,
                showConnections: false,
                showLightning: false,
                ...options
            });
        }
    };

    // ========================================
    // Public API
    // ========================================
    return {
        CinematicProgressBar,
        createPreset,
        PALETTES,
        CONFIG,

        // Quick create methods
        create: (container, options) => new CinematicProgressBar(container, options),
        circuit: (container, options) => createPreset.circuit(container, options),
        cosmic: (container, options) => createPreset.cosmic(container, options),
        matrix: (container, options) => createPreset.matrix(container, options),
        energy: (container, options) => createPreset.energy(container, options),
        fire: (container, options) => createPreset.fire(container, options)
    };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CinematicProgress;
}
