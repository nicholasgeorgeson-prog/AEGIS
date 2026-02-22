/**
 * AEGIS Cinematic Technology Showcase
 * Full-screen Canvas-animated video showcasing AEGIS capabilities
 * Cyberpunk HUD aesthetic — Iron Man's JARVIS meets Tron
 *
 * @version 1.0.0
 * @author AEGIS Team
 */
window.CinematicVideo = (function() {
    'use strict';

    // =========================================================================
    // EASING FUNCTIONS
    // =========================================================================
    var Ease = {
        linear: function(t) { return t; },
        inQuad: function(t) { return t * t; },
        outQuad: function(t) { return t * (2 - t); },
        inOutQuad: function(t) { return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t; },
        inCubic: function(t) { return t * t * t; },
        outCubic: function(t) { var t1 = t - 1; return t1 * t1 * t1 + 1; },
        inOutCubic: function(t) { return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1; },
        outElastic: function(t) {
            if (t === 0 || t === 1) return t;
            return Math.pow(2, -10 * t) * Math.sin((t - 0.1) * 5 * Math.PI) + 1;
        },
        outBack: function(t) { var s = 1.70158; var t1 = t - 1; return t1 * t1 * ((s + 1) * t1 + s) + 1; },
        outExpo: function(t) { return t === 1 ? 1 : 1 - Math.pow(2, -10 * t); },
        inExpo: function(t) { return t === 0 ? 0 : Math.pow(2, 10 * (t - 1)); }
    };

    // =========================================================================
    // ENGINE — Core animation state and RAF loop
    // =========================================================================
    var Engine = {
        canvas: null,
        ctx: null,
        dpr: 1,
        W: 0,
        H: 0,
        playing: false,
        paused: false,
        speed: 1,
        startTime: 0,
        elapsed: 0,
        pausedAt: 0,
        sceneIndex: 0,
        sceneStartTime: 0,
        sceneLocalTime: 0,
        rafId: null,
        scenes: [],
        particleSystems: [],
        // Camera
        camera: { x: 0, y: 0, zoom: 1, targetX: 0, targetY: 0, targetZoom: 1, speed: 0.03 },
        // Transition
        transition: { active: false, type: 'fade', progress: 0, duration: 800, startTime: 0 },
        // Overlays
        scanlinePattern: null,
        // Audio
        audioEl: null,
        audioManifest: null,
        narrationPlaying: false,
        // Subtitle
        subtitleText: '',
        subtitleOpacity: 0,
        // Offscreen caches
        _offscreenCircuit: null,
        _offscreenScanlines: null
    };

    // =========================================================================
    // INIT / RESIZE
    // =========================================================================
    function init() {
        Engine.canvas = document.getElementById('cinema-canvas');
        if (!Engine.canvas) { console.error('[Cinema] No canvas found'); return false; }
        Engine.ctx = Engine.canvas.getContext('2d');
        Engine.dpr = Math.min(window.devicePixelRatio || 1, 2);
        _resize();
        _buildScanlinePattern();
        _buildCircuitCache();
        window.addEventListener('resize', _resize);
        return true;
    }

    function _resize() {
        var c = Engine.canvas;
        var parent = c.parentElement || document.body;
        Engine.W = parent.clientWidth || window.innerWidth;
        Engine.H = parent.clientHeight || window.innerHeight;
        c.width = Engine.W * Engine.dpr;
        c.height = Engine.H * Engine.dpr;
        c.style.width = Engine.W + 'px';
        c.style.height = Engine.H + 'px';
        Engine.ctx.setTransform(Engine.dpr, 0, 0, Engine.dpr, 0, 0);
        // Rebuild offscreen caches on resize
        _buildScanlinePattern();
        _buildCircuitCache();
    }

    // =========================================================================
    // OFFSCREEN CACHES
    // =========================================================================
    function _buildScanlinePattern() {
        var oc = document.createElement('canvas');
        oc.width = 4; oc.height = 4;
        var octx = oc.getContext('2d');
        octx.fillStyle = 'rgba(0,0,0,0.04)';
        octx.fillRect(0, 0, 4, 2);
        Engine._offscreenScanlines = oc;
        Engine.scanlinePattern = Engine.ctx.createPattern(oc, 'repeat');
    }

    function _buildCircuitCache() {
        var w = Math.max(Engine.W, 400);
        var h = Math.max(Engine.H, 300);
        var oc = document.createElement('canvas');
        oc.width = w; oc.height = h;
        var ctx = oc.getContext('2d');
        ctx.strokeStyle = 'rgba(214,168,74,0.06)';
        ctx.lineWidth = 1;
        var spacing = 40;
        // Horizontal lines
        for (var y = 0; y < h; y += spacing) {
            ctx.beginPath();
            var x = 0;
            while (x < w) {
                var seg = 20 + Math.random() * 60;
                ctx.moveTo(x, y);
                ctx.lineTo(Math.min(x + seg, w), y);
                x += seg + 10 + Math.random() * 30;
            }
            ctx.stroke();
        }
        // Vertical lines
        for (var x2 = 0; x2 < w; x2 += spacing) {
            ctx.beginPath();
            var y2 = 0;
            while (y2 < h) {
                var seg2 = 10 + Math.random() * 40;
                ctx.moveTo(x2, y2);
                ctx.lineTo(x2, Math.min(y2 + seg2, h));
                y2 += seg2 + 10 + Math.random() * 20;
            }
            ctx.stroke();
        }
        // Nodes at intersections
        ctx.fillStyle = 'rgba(214,168,74,0.1)';
        for (var i = 0; i < 30; i++) {
            var nx = Math.random() * w;
            var ny = Math.random() * h;
            ctx.beginPath();
            ctx.arc(nx, ny, 2, 0, Math.PI * 2);
            ctx.fill();
        }
        Engine._offscreenCircuit = oc;
    }

    // =========================================================================
    // RAF LOOP
    // =========================================================================
    function _tick(timestamp) {
        if (!Engine.playing) return;
        if (Engine.paused) {
            Engine.rafId = requestAnimationFrame(_tick);
            return;
        }

        // Update elapsed
        if (!Engine.startTime) Engine.startTime = timestamp;
        Engine.elapsed = (timestamp - Engine.startTime) * Engine.speed;
        Engine.sceneLocalTime = Engine.elapsed - Engine.sceneStartTime;

        var scene = Engine.scenes[Engine.sceneIndex];
        if (!scene) { stop(); return; }

        // Check scene duration
        var sceneDur = scene.duration || 20000;
        if (Engine.sceneLocalTime >= sceneDur && !Engine.transition.active) {
            _advanceScene();
            Engine.rafId = requestAnimationFrame(_tick);
            return;
        }

        // Fire beats
        if (scene.beats) {
            for (var i = 0; i < scene.beats.length; i++) {
                var beat = scene.beats[i];
                if (!beat._fired && Engine.sceneLocalTime >= beat.time) {
                    beat._fired = true;
                    try { beat.fn(Engine); } catch(e) { console.warn('[Cinema] Beat error:', e); }
                }
            }
        }

        // Update camera (lerp)
        Engine.camera.x += (Engine.camera.targetX - Engine.camera.x) * Engine.camera.speed;
        Engine.camera.y += (Engine.camera.targetY - Engine.camera.y) * Engine.camera.speed;
        Engine.camera.zoom += (Engine.camera.targetZoom - Engine.camera.zoom) * Engine.camera.speed;

        // Update particles
        for (var p = Engine.particleSystems.length - 1; p >= 0; p--) {
            var ps = Engine.particleSystems[p];
            ps.update(Engine.sceneLocalTime);
            if (ps.dead) Engine.particleSystems.splice(p, 1);
        }

        // Render
        var ctx = Engine.ctx;
        ctx.save();
        ctx.setTransform(Engine.dpr, 0, 0, Engine.dpr, 0, 0);

        // Clear
        ctx.fillStyle = '#020408';
        ctx.fillRect(0, 0, Engine.W, Engine.H);

        // Circuit board background (subtle)
        if (Engine._offscreenCircuit) {
            ctx.globalAlpha = 0.5;
            ctx.drawImage(Engine._offscreenCircuit, 0, 0, Engine.W, Engine.H);
            ctx.globalAlpha = 1;
        }

        // Apply camera transform
        ctx.save();
        var cx = Engine.W / 2, cy = Engine.H / 2;
        ctx.translate(cx, cy);
        ctx.scale(Engine.camera.zoom, Engine.camera.zoom);
        ctx.translate(-cx - Engine.camera.x, -cy - Engine.camera.y);

        // Render scene
        if (scene.render) {
            try { scene.render(ctx, Engine.sceneLocalTime, Engine.W, Engine.H, Engine); }
            catch(e) { console.error('[Cinema] Scene render error:', e); }
        }

        // Render particles
        for (var j = 0; j < Engine.particleSystems.length; j++) {
            Engine.particleSystems[j].render(ctx);
        }

        ctx.restore(); // camera

        // Overlays (not affected by camera)
        _renderScanlines(ctx);
        _renderVignette(ctx);
        _renderHUDCorners(ctx, Engine.sceneLocalTime);
        _renderTransition(ctx);

        ctx.restore(); // dpr

        // Update subtitle
        _updateSubtitle();

        // Performance throttle
        Engine.rafId = requestAnimationFrame(_tick);
    }

    // =========================================================================
    // SCENE MANAGEMENT
    // =========================================================================
    function _advanceScene() {
        var oldScene = Engine.scenes[Engine.sceneIndex];
        if (oldScene && oldScene.teardown) {
            try { oldScene.teardown(Engine); } catch(e) { console.warn('[Cinema] Teardown error:', e); }
        }

        Engine.sceneIndex++;
        if (Engine.sceneIndex >= Engine.scenes.length) {
            stop();
            return;
        }

        // Start transition
        Engine.transition.active = true;
        Engine.transition.progress = 0;
        Engine.transition.startTime = Engine.elapsed;
        Engine.transition.duration = 800;
        Engine.transition.type = 'fade';

        // Reset beat flags and scene timer
        var newScene = Engine.scenes[Engine.sceneIndex];
        Engine.sceneStartTime = Engine.elapsed;
        Engine.sceneLocalTime = 0;
        if (newScene.beats) {
            for (var i = 0; i < newScene.beats.length; i++) {
                newScene.beats[i]._fired = false;
            }
        }

        // Setup new scene
        if (newScene.setup) {
            try { newScene.setup(Engine); } catch(e) { console.warn('[Cinema] Setup error:', e); }
        }

        // Play narration
        if (newScene.narration) {
            _playNarration(newScene.narration, newScene.id, Engine.sceneIndex);
        }

        // Reset camera for new scene
        Engine.camera.speed = 0.03;
    }

    // =========================================================================
    // OVERLAYS — Scanlines, Vignette, HUD Corners, Transition
    // =========================================================================
    function _renderScanlines(ctx) {
        if (!Engine.scanlinePattern) return;
        ctx.fillStyle = Engine.scanlinePattern;
        ctx.fillRect(0, 0, Engine.W, Engine.H);
    }

    function _renderVignette(ctx) {
        var cx = Engine.W / 2, cy = Engine.H / 2;
        var r = Math.max(Engine.W, Engine.H) * 0.7;
        var grad = ctx.createRadialGradient(cx, cy, r * 0.3, cx, cy, r);
        grad.addColorStop(0, 'rgba(2,4,8,0)');
        grad.addColorStop(1, 'rgba(2,4,8,0.85)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, Engine.W, Engine.H);
    }

    function _renderHUDCorners(ctx, t) {
        var len = 40;
        var margin = 20;
        var pulse = 0.4 + 0.6 * (0.5 + 0.5 * Math.sin(t / 500));
        ctx.strokeStyle = 'rgba(214,168,74,' + (0.3 * pulse) + ')';
        ctx.lineWidth = 1.5;

        // Top-left
        ctx.beginPath();
        ctx.moveTo(margin, margin + len);
        ctx.lineTo(margin, margin);
        ctx.lineTo(margin + len, margin);
        ctx.stroke();

        // Top-right
        ctx.beginPath();
        ctx.moveTo(Engine.W - margin - len, margin);
        ctx.lineTo(Engine.W - margin, margin);
        ctx.lineTo(Engine.W - margin, margin + len);
        ctx.stroke();

        // Bottom-left
        ctx.beginPath();
        ctx.moveTo(margin, Engine.H - margin - len);
        ctx.lineTo(margin, Engine.H - margin);
        ctx.lineTo(margin + len, Engine.H - margin);
        ctx.stroke();

        // Bottom-right
        ctx.beginPath();
        ctx.moveTo(Engine.W - margin - len, Engine.H - margin);
        ctx.lineTo(Engine.W - margin, Engine.H - margin);
        ctx.lineTo(Engine.W - margin, Engine.H - margin - len);
        ctx.stroke();
    }

    function _renderTransition(ctx) {
        if (!Engine.transition.active) return;
        var elapsed = Engine.elapsed - Engine.transition.startTime;
        var p = Math.min(elapsed / Engine.transition.duration, 1);

        if (Engine.transition.type === 'fade') {
            // Fade out first half, fade in second half
            var alpha;
            if (p < 0.5) {
                alpha = p * 2; // 0 → 1
            } else {
                alpha = 2 - p * 2; // 1 → 0
            }
            ctx.fillStyle = 'rgba(2,4,8,' + alpha + ')';
            ctx.fillRect(0, 0, Engine.W, Engine.H);
        }

        if (p >= 1) {
            Engine.transition.active = false;
        }
    }

    // =========================================================================
    // NARRATION SYSTEM
    // =========================================================================
    function _playNarration(text, sceneId, sceneIndex) {
        Engine.subtitleText = text;
        Engine.subtitleOpacity = 1;
        Engine.narrationPlaying = true;

        // Try pre-generated audio first
        var audioFile = _getCinemaAudioFile(sceneId, sceneIndex);
        if (audioFile) {
            _playAudioClip(audioFile).then(function() {
                Engine.narrationPlaying = false;
                _fadeSubtitle();
            }).catch(function() {
                Engine.narrationPlaying = false;
                _fadeSubtitle();
            });
            return;
        }

        // Web Speech API fallback
        if (window.speechSynthesis) {
            try {
                window.speechSynthesis.cancel();
                var utter = new SpeechSynthesisUtterance(text);
                utter.rate = Engine.speed;
                utter.pitch = 1.05;
                utter.onend = function() { Engine.narrationPlaying = false; _fadeSubtitle(); };
                utter.onerror = function() { Engine.narrationPlaying = false; _fadeSubtitle(); };
                window.speechSynthesis.speak(utter);
                return;
            } catch(e) { /* fall through */ }
        }

        // Silent timer fallback
        Engine.narrationPlaying = false;
        setTimeout(function() { _fadeSubtitle(); }, 3000 / Engine.speed);
    }

    function _getCinemaAudioFile(sceneId, sceneIndex) {
        if (!Engine.audioManifest || !Engine.audioManifest.scenes) return null;
        var section = Engine.audioManifest.scenes[sceneId];
        if (!section || !section.steps || !section.steps[0]) return null;
        return '/static/audio/cinema/' + section.steps[0].file;
    }

    function _playAudioClip(url) {
        return new Promise(function(resolve, reject) {
            try {
                if (!Engine.audioEl) {
                    Engine.audioEl = new Audio();
                }
                var audio = Engine.audioEl;
                audio.src = url;
                audio.playbackRate = Engine.speed;
                audio.volume = _getVolume();
                audio.onended = resolve;
                audio.onerror = reject;
                audio.play().catch(reject);
            } catch(e) { reject(e); }
        });
    }

    function _fadeSubtitle() {
        // Fade over 500ms via render loop check
        Engine.subtitleOpacity = 0;
    }

    function _updateSubtitle() {
        var el = document.getElementById('cinema-subtitle');
        if (!el) return;
        if (Engine.subtitleText && Engine.subtitleOpacity > 0) {
            el.textContent = Engine.subtitleText;
            el.style.opacity = '1';
            el.style.display = 'block';
        } else {
            el.style.opacity = '0';
        }
    }

    function _loadAudioManifest() {
        return fetch('/static/audio/cinema/manifest.json')
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(data) { Engine.audioManifest = data; })
            .catch(function() { Engine.audioManifest = null; });
    }

    function _getVolume() {
        try {
            var v = parseFloat(localStorage.getItem('aegis-cinema-volume'));
            return isNaN(v) ? 0.8 : v;
        } catch(e) { return 0.8; }
    }

    // =========================================================================
    // VISUAL COMPONENTS — Reusable canvas drawing functions
    // =========================================================================

    /** Draw glowing text with bloom effect */
    function drawGlowText(ctx, text, x, y, opts) {
        var fontSize = (opts && opts.fontSize) || 32;
        var color = (opts && opts.color) || '#D6A84A';
        var glowColor = (opts && opts.glowColor) || 'rgba(214,168,74,0.6)';
        var align = (opts && opts.align) || 'center';
        var baseline = (opts && opts.baseline) || 'middle';
        var font = (opts && opts.font) || ('bold ' + fontSize + 'px "Courier New", monospace');
        var alpha = (opts && opts.alpha !== undefined) ? opts.alpha : 1;

        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.font = font;
        ctx.textAlign = align;
        ctx.textBaseline = baseline;

        // Glow pass
        ctx.shadowColor = glowColor;
        ctx.shadowBlur = 20;
        ctx.fillStyle = color;
        ctx.fillText(text, x, y);

        // Crisp pass
        ctx.shadowBlur = 0;
        ctx.fillText(text, x, y);
        ctx.restore();
    }

    /** Draw animated HUD-style brackets around a rect */
    function drawHUDBrackets(ctx, x, y, w, h, progress, opts) {
        var cornerLen = (opts && opts.cornerLen) || 15;
        var color = (opts && opts.color) || 'rgba(214,168,74,0.7)';
        var lineWidth = (opts && opts.lineWidth) || 1.5;
        var p = Math.min(progress, 1);

        ctx.save();
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;

        var len = cornerLen * p;

        // Top-left
        ctx.beginPath();
        ctx.moveTo(x, y + len); ctx.lineTo(x, y); ctx.lineTo(x + len, y);
        ctx.stroke();
        // Top-right
        ctx.beginPath();
        ctx.moveTo(x + w - len, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + len);
        ctx.stroke();
        // Bottom-left
        ctx.beginPath();
        ctx.moveTo(x, y + h - len); ctx.lineTo(x, y + h); ctx.lineTo(x + len, y + h);
        ctx.stroke();
        // Bottom-right
        ctx.beginPath();
        ctx.moveTo(x + w - len, y + h); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w, y + h - len);
        ctx.stroke();

        ctx.restore();
    }

    /** Matrix-style data stream — falling gold characters */
    function DataStream(x, speed, chars) {
        this.x = x;
        this.speed = speed || 80;
        this.chars = chars || 'AEGIS01DATA<>{}[]#$%SCAN';
        this.columns = [];
        this._initColumns();
    }
    DataStream.prototype._initColumns = function() {
        var count = 1 + Math.floor(Math.random() * 2);
        for (var i = 0; i < count; i++) {
            this.columns.push({
                y: -Math.random() * 200,
                chars: [],
                speed: this.speed * (0.5 + Math.random() * 0.5)
            });
            // Fill chars
            var col = this.columns[i];
            for (var j = 0; j < 15; j++) {
                col.chars.push(this.chars[Math.floor(Math.random() * this.chars.length)]);
            }
        }
    };
    DataStream.prototype.update = function(dt) {
        for (var i = 0; i < this.columns.length; i++) {
            var col = this.columns[i];
            col.y += col.speed * (dt / 1000);
            // Randomize chars occasionally
            if (Math.random() < 0.02) {
                var idx = Math.floor(Math.random() * col.chars.length);
                col.chars[idx] = this.chars[Math.floor(Math.random() * this.chars.length)];
            }
        }
    };
    DataStream.prototype.render = function(ctx, H) {
        var fontSize = 12;
        ctx.font = fontSize + 'px "Courier New", monospace';
        ctx.textAlign = 'center';
        for (var i = 0; i < this.columns.length; i++) {
            var col = this.columns[i];
            for (var j = 0; j < col.chars.length; j++) {
                var cy = col.y + j * fontSize * 1.2;
                if (cy < 0 || cy > H) continue;
                var alpha = 1 - (j / col.chars.length);
                ctx.fillStyle = 'rgba(214,168,74,' + (alpha * 0.5) + ')';
                ctx.fillText(col.chars[j], this.x + i * 14, cy);
            }
        }
    };

    /** Animated counter with dramatic count-up */
    function drawAnimatedCounter(ctx, x, y, current, target, opts) {
        var fontSize = (opts && opts.fontSize) || 64;
        var color = (opts && opts.color) || '#D6A84A';
        var label = (opts && opts.label) || '';
        var prefix = (opts && opts.prefix) || '';

        var value = Math.floor(current);
        var text = prefix + value.toLocaleString();

        drawGlowText(ctx, text, x, y, {
            fontSize: fontSize,
            color: color,
            glowColor: 'rgba(214,168,74,0.8)'
        });

        if (label) {
            drawGlowText(ctx, label, x, y + fontSize * 0.8, {
                fontSize: Math.floor(fontSize * 0.35),
                color: 'rgba(214,168,74,0.6)',
                glowColor: 'rgba(214,168,74,0.3)'
            });
        }
    }

    /** Radar sweep — rotating sonar cone */
    function drawRadarSweep(ctx, cx, cy, radius, angle, opts) {
        var color = (opts && opts.color) || 'rgba(214,168,74,0.3)';
        var ringColor = (opts && opts.ringColor) || 'rgba(214,168,74,0.15)';
        var sweepAngle = (opts && opts.sweepAngle) || 0.5;

        ctx.save();
        // Rings
        ctx.strokeStyle = ringColor;
        ctx.lineWidth = 0.5;
        for (var i = 1; i <= 3; i++) {
            ctx.beginPath();
            ctx.arc(cx, cy, radius * (i / 3), 0, Math.PI * 2);
            ctx.stroke();
        }
        // Cross hairs
        ctx.beginPath();
        ctx.moveTo(cx - radius, cy); ctx.lineTo(cx + radius, cy);
        ctx.moveTo(cx, cy - radius); ctx.lineTo(cx, cy + radius);
        ctx.stroke();

        // Sweep cone
        var grad = ctx.createConicalGradient ? null : null; // Not supported, use arc
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, radius, angle - sweepAngle, angle);
        ctx.closePath();
        ctx.fill();

        // Sweep line
        ctx.strokeStyle = '#D6A84A';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
        ctx.stroke();

        ctx.restore();
    }

    /** Progress ring — circular gauge */
    function drawProgressRing(ctx, cx, cy, radius, progress, opts) {
        var bgColor = (opts && opts.bgColor) || 'rgba(214,168,74,0.1)';
        var fgColor = (opts && opts.fgColor) || '#D6A84A';
        var lineWidth = (opts && opts.lineWidth) || 4;
        var label = (opts && opts.label) || '';

        ctx.save();
        // Background ring
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.strokeStyle = bgColor;
        ctx.lineWidth = lineWidth;
        ctx.stroke();

        // Progress arc
        var startAngle = -Math.PI / 2;
        var endAngle = startAngle + Math.PI * 2 * Math.min(progress, 1);
        ctx.beginPath();
        ctx.arc(cx, cy, radius, startAngle, endAngle);
        ctx.strokeStyle = fgColor;
        ctx.lineWidth = lineWidth;
        ctx.lineCap = 'round';
        ctx.stroke();

        // Center text
        if (label) {
            drawGlowText(ctx, label, cx, cy, {
                fontSize: Math.floor(radius * 0.6),
                color: fgColor
            });
        }

        ctx.restore();
    }

    /** Wireframe document outline with dog-ear corner */
    function drawWireframeDoc(ctx, x, y, w, h, opts) {
        var color = (opts && opts.color) || 'rgba(214,168,74,0.5)';
        var fillColor = (opts && opts.fill) || 'rgba(214,168,74,0.03)';
        var earSize = (opts && opts.earSize) || 15;
        var alpha = (opts && opts.alpha !== undefined) ? opts.alpha : 1;

        ctx.save();
        ctx.globalAlpha = alpha;

        // Doc shape with dog-ear
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + w - earSize, y);
        ctx.lineTo(x + w, y + earSize);
        ctx.lineTo(x + w, y + h);
        ctx.lineTo(x, y + h);
        ctx.closePath();
        ctx.fillStyle = fillColor;
        ctx.fill();
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Dog-ear fold
        ctx.beginPath();
        ctx.moveTo(x + w - earSize, y);
        ctx.lineTo(x + w - earSize, y + earSize);
        ctx.lineTo(x + w, y + earSize);
        ctx.strokeStyle = color;
        ctx.stroke();

        // Text lines
        ctx.fillStyle = color;
        var lineY = y + earSize + 10;
        var lineH = 3;
        var lineGap = 8;
        while (lineY + lineH < y + h - 10) {
            var lineW = w * (0.4 + Math.random() * 0.4);
            ctx.fillRect(x + 10, lineY, lineW, lineH);
            lineY += lineH + lineGap;
        }

        ctx.restore();
    }

    /** Animated connection line with traveling particle */
    function drawConnectionLine(ctx, x1, y1, x2, y2, progress, opts) {
        var color = (opts && opts.color) || 'rgba(214,168,74,0.4)';
        var dotColor = (opts && opts.dotColor) || '#D6A84A';
        var dotRadius = (opts && opts.dotRadius) || 3;
        var lineWidth = (opts && opts.lineWidth) || 1;

        ctx.save();

        // Draw line up to progress point
        var dx = x2 - x1, dy = y2 - y1;
        var px = x1 + dx * Math.min(progress, 1);
        var py = y1 + dy * Math.min(progress, 1);

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(px, py);
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.stroke();

        // Traveling dot
        if (progress > 0 && progress <= 1) {
            ctx.beginPath();
            ctx.arc(px, py, dotRadius, 0, Math.PI * 2);
            ctx.fillStyle = dotColor;
            ctx.shadowColor = 'rgba(214,168,74,0.8)';
            ctx.shadowBlur = 8;
            ctx.fill();
        }

        ctx.restore();
    }

    // =========================================================================
    // PARTICLE SYSTEM
    // =========================================================================
    function ParticleSystem(opts) {
        this.particles = [];
        this.x = (opts && opts.x) || 0;
        this.y = (opts && opts.y) || 0;
        this.type = (opts && opts.type) || 'ambient'; // ambient, burst, trail
        this.color = (opts && opts.color) || 'rgba(214,168,74,';
        this.maxParticles = (opts && opts.maxParticles) || 50;
        this.dead = false;
        this.createdAt = 0;
        this.lifetime = (opts && opts.lifetime) || Infinity;
        this._lastEmit = 0;
        this._emitRate = (opts && opts.emitRate) || 200; // ms between emits

        if (this.type === 'burst') {
            this._emitBurst(opts);
        }
    }

    ParticleSystem.prototype._emitBurst = function(opts) {
        var count = (opts && opts.count) || 30;
        for (var i = 0; i < count; i++) {
            var angle = (Math.PI * 2 / count) * i + Math.random() * 0.3;
            var speed = 30 + Math.random() * 80;
            this.particles.push({
                x: this.x, y: this.y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                life: 1,
                decay: 0.005 + Math.random() * 0.01,
                size: 1 + Math.random() * 2
            });
        }
    };

    ParticleSystem.prototype.update = function(t) {
        if (this.dead) return;

        // Check system lifetime
        if (!this.createdAt) this.createdAt = t;
        if (t - this.createdAt > this.lifetime) {
            this.dead = true;
            return;
        }

        var dt = 1 / 60; // assume 60fps for physics

        // Emit for ambient type
        if (this.type === 'ambient' && t - this._lastEmit > this._emitRate) {
            if (this.particles.length < this.maxParticles) {
                this.particles.push({
                    x: this.x + (Math.random() - 0.5) * 200,
                    y: this.y + (Math.random() - 0.5) * 200,
                    vx: (Math.random() - 0.5) * 10,
                    vy: -5 - Math.random() * 15,
                    life: 1,
                    decay: 0.003 + Math.random() * 0.005,
                    size: 0.5 + Math.random() * 1.5
                });
            }
            this._lastEmit = t;
        }

        // Update particles
        for (var i = this.particles.length - 1; i >= 0; i--) {
            var p = this.particles[i];
            p.x += p.vx * dt;
            p.y += p.vy * dt;
            p.life -= p.decay;
            if (p.life <= 0) {
                this.particles.splice(i, 1);
            }
        }

        // Mark dead if burst type and all particles gone
        if (this.type === 'burst' && this.particles.length === 0) {
            this.dead = true;
        }
    };

    ParticleSystem.prototype.render = function(ctx) {
        for (var i = 0; i < this.particles.length; i++) {
            var p = this.particles[i];
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = this.color + (p.life * 0.8) + ')';
            ctx.fill();
        }
    };

    // =========================================================================
    // HELPER: Typewriter text for narration reveals
    // =========================================================================
    function drawTypewriterText(ctx, text, x, y, progress, opts) {
        var chars = Math.floor(text.length * Math.min(progress, 1));
        var visible = text.substring(0, chars);
        drawGlowText(ctx, visible, x, y, opts);

        // Blinking cursor
        if (progress < 1 && Math.sin(Date.now() / 300) > 0) {
            var metrics = ctx.measureText ? null : null;
            // Approximate cursor position
            ctx.save();
            var fontSize = (opts && opts.fontSize) || 32;
            ctx.font = (opts && opts.font) || ('bold ' + fontSize + 'px "Courier New", monospace');
            ctx.textAlign = (opts && opts.align) || 'center';
            var measuredW = ctx.measureText(visible).width;
            var cursorX = x;
            if (ctx.textAlign === 'center') {
                cursorX = x - ctx.measureText(text.substring(0, chars)).width / 2 + measuredW;
            } else if (ctx.textAlign === 'left') {
                cursorX = x + measuredW;
            }
            ctx.fillStyle = '#D6A84A';
            ctx.fillRect(cursorX + 2, y - fontSize / 2, 2, fontSize);
            ctx.restore();
        }
    }

    // =========================================================================
    // HELPER: Draw AEGIS shield logo
    // =========================================================================
    function drawAEGISShield(ctx, cx, cy, size, progress, opts) {
        var color = (opts && opts.color) || '#D6A84A';
        var glowColor = (opts && opts.glowColor) || 'rgba(214,168,74,0.5)';
        var p = Ease.outCubic(Math.min(progress, 1));

        ctx.save();
        ctx.translate(cx, cy);
        ctx.scale(p, p);

        // Shield shape
        ctx.beginPath();
        ctx.moveTo(0, -size);
        ctx.bezierCurveTo(size * 0.8, -size * 0.7, size * 0.9, 0, size * 0.7, size * 0.5);
        ctx.lineTo(0, size);
        ctx.lineTo(-size * 0.7, size * 0.5);
        ctx.bezierCurveTo(-size * 0.9, 0, -size * 0.8, -size * 0.7, 0, -size);
        ctx.closePath();

        // Fill
        ctx.fillStyle = 'rgba(214,168,74,0.08)';
        ctx.fill();

        // Stroke with glow
        ctx.shadowColor = glowColor;
        ctx.shadowBlur = 15;
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Inner chevron
        var innerSize = size * 0.5;
        ctx.beginPath();
        ctx.moveTo(0, -innerSize);
        ctx.lineTo(innerSize * 0.6, 0);
        ctx.lineTo(0, innerSize * 0.6);
        ctx.lineTo(-innerSize * 0.6, 0);
        ctx.closePath();
        ctx.strokeStyle = 'rgba(214,168,74,0.4)';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.restore();
    }

    // =========================================================================
    // HELPER: Draw severity bar chart
    // =========================================================================
    function drawBarChart(ctx, x, y, w, h, data, progress, opts) {
        var barGap = (opts && opts.barGap) || 6;
        var colors = (opts && opts.colors) || ['#ef4444', '#f59e0b', '#3b82f6', '#6b7280'];
        var labels = (opts && opts.labels) || [];
        var maxVal = 0;
        for (var i = 0; i < data.length; i++) { if (data[i] > maxVal) maxVal = data[i]; }
        if (maxVal === 0) maxVal = 1;

        var barW = (w - barGap * (data.length - 1)) / data.length;
        var p = Ease.outCubic(Math.min(progress, 1));

        for (var j = 0; j < data.length; j++) {
            var barH = (data[j] / maxVal) * h * p;
            var bx = x + j * (barW + barGap);
            var by = y + h - barH;

            ctx.fillStyle = colors[j % colors.length];
            ctx.globalAlpha = 0.8;
            ctx.fillRect(bx, by, barW, barH);
            ctx.globalAlpha = 1;

            // Label
            if (labels[j]) {
                ctx.font = '10px "Courier New", monospace';
                ctx.fillStyle = 'rgba(214,168,74,0.6)';
                ctx.textAlign = 'center';
                ctx.fillText(labels[j], bx + barW / 2, y + h + 14);
            }
        }
    }

    // =========================================================================
    // SCENE HELPERS — shared animation primitives for scenes
    // =========================================================================

    /** Create an array of wireframe document objects for animation */
    function _makeDocArray(count, W, H) {
        var docs = [];
        for (var i = 0; i < count; i++) {
            docs.push({
                x: W / 2 + (Math.random() - 0.5) * 40,
                y: H / 2 + (Math.random() - 0.5) * 40,
                targetX: (Math.random() - 0.5) * W * 1.5 + W / 2,
                targetY: (Math.random() - 0.5) * H * 1.5 + H / 2,
                w: 50 + Math.random() * 30,
                h: 65 + Math.random() * 35,
                speed: 0.01 + Math.random() * 0.02,
                rotation: (Math.random() - 0.5) * 0.3,
                delay: i * 80,
                hasWarning: Math.random() < 0.3
            });
        }
        return docs;
    }

    /** Draw a warning marker blinking red */
    function _drawWarningMarker(ctx, x, y, t) {
        var blink = Math.sin(t / 200) > 0 ? 1 : 0.3;
        ctx.save();
        ctx.fillStyle = 'rgba(239,68,68,' + blink + ')';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowColor = 'rgba(239,68,68,0.6)';
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.restore();
    }

    /** Draw text that types in standard names */
    function _drawStandardLabel(ctx, text, x, y, progress, color) {
        var chars = Math.floor(text.length * Math.min(progress, 1));
        ctx.font = '13px "Courier New", monospace';
        ctx.fillStyle = color || 'rgba(214,168,74,0.7)';
        ctx.textAlign = 'left';
        ctx.fillText(text.substring(0, chars), x, y);
    }

    /** Draw crack/fracture lines radiating from center */
    function _drawCracks(ctx, cx, cy, progress, count) {
        ctx.save();
        ctx.strokeStyle = 'rgba(239,68,68,' + (0.6 * progress) + ')';
        ctx.lineWidth = 1.5;
        for (var i = 0; i < count; i++) {
            var angle = (Math.PI * 2 / count) * i + 0.2;
            var len = 50 + progress * 200;
            var segments = 4;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            var px = cx, py = cy;
            for (var s = 0; s < segments; s++) {
                var a = angle + (Math.random() - 0.5) * 0.6;
                var segLen = len / segments;
                px += Math.cos(a) * segLen;
                py += Math.sin(a) * segLen;
                ctx.lineTo(px, py);
            }
            ctx.stroke();
        }
        ctx.restore();
    }

    /** Draw a hexagonal fortress shape */
    function _drawHexFortress(ctx, cx, cy, radius, progress, opts) {
        var sides = 6;
        var color = (opts && opts.color) || '#D6A84A';
        var p = Ease.outCubic(Math.min(progress, 1));
        var r = radius * p;

        ctx.save();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.shadowColor = 'rgba(214,168,74,0.4)';
        ctx.shadowBlur = 10;

        ctx.beginPath();
        for (var i = 0; i <= sides; i++) {
            var angle = (Math.PI * 2 / sides) * i - Math.PI / 2;
            var x = cx + Math.cos(angle) * r;
            var y = cy + Math.sin(angle) * r;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fillStyle = 'rgba(214,168,74,0.04)';
        ctx.fill();
        ctx.stroke();

        // Inner hex
        ctx.beginPath();
        for (var j = 0; j <= sides; j++) {
            var a2 = (Math.PI * 2 / sides) * j - Math.PI / 2;
            var x2 = cx + Math.cos(a2) * r * 0.6;
            var y2 = cy + Math.sin(a2) * r * 0.6;
            if (j === 0) ctx.moveTo(x2, y2);
            else ctx.lineTo(x2, y2);
        }
        ctx.closePath();
        ctx.strokeStyle = 'rgba(214,168,74,0.3)';
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.restore();
    }

    // =========================================================================
    // SCENE DEFINITIONS
    // =========================================================================
    function _buildScenes() {
        Engine.scenes = [];

        // =================================================================
        // ACT 1: THE PROBLEM (~65s)
        // =================================================================

        // Scene 1.1 — Document Chaos (22s)
        Engine.scenes.push({
            id: 'doc_chaos',
            duration: 22000,
            narration: 'Aerospace teams are drowning in documents. Thousands of pages across hundreds of deliverables. Each one could contain a mission-grounding error hidden in plain sight.',
            _docs: null,
            _counter: 0,
            _dataStreams: null,
            setup: function(eng) {
                this._docs = _makeDocArray(25, eng.W, eng.H);
                this._counter = 0;
                this._dataStreams = [];
                for (var i = 0; i < 5; i++) {
                    this._dataStreams.push(new DataStream(eng.W * 0.1 + i * eng.W * 0.2, 60));
                }
                eng.particleSystems.push(new ParticleSystem({
                    x: eng.W / 2, y: eng.H / 2, type: 'ambient',
                    maxParticles: 40, lifetime: 22000
                }));
            },
            beats: [
                { time: 2000, fn: function(eng) { /* docs start exploding outward */ } },
                { time: 15000, fn: function(eng) {
                    eng.particleSystems.push(new ParticleSystem({
                        x: eng.W * 0.75, y: eng.H * 0.2, type: 'burst', count: 15
                    }));
                }}
            ],
            render: function(ctx, t, W, H, eng) {
                // Data streams background
                for (var d = 0; d < this._dataStreams.length; d++) {
                    this._dataStreams[d].update(16);
                    this._dataStreams[d].render(ctx, H);
                }

                // Documents exploding outward from center
                var explodeStart = 2000;
                for (var i = 0; i < this._docs.length; i++) {
                    var doc = this._docs[i];
                    var docT = Math.max(0, t - doc.delay - explodeStart);
                    var p = Math.min(docT / 3000, 1);
                    var ep = Ease.outBack(p);
                    var dx = doc.x + (doc.targetX - doc.x) * ep;
                    var dy = doc.y + (doc.targetY - doc.y) * ep;

                    ctx.save();
                    ctx.translate(dx, dy);
                    ctx.rotate(doc.rotation * ep);
                    drawWireframeDoc(ctx, -doc.w / 2, -doc.h / 2, doc.w, doc.h, {
                        alpha: Math.min(p * 3, 0.7)
                    });
                    if (doc.hasWarning && p > 0.5) {
                        _drawWarningMarker(ctx, doc.w / 2 - 5, -doc.h / 2 + 5, t);
                    }
                    ctx.restore();
                }

                // Counter: DOCUMENTS PENDING
                this._counter = Math.min(t / 18000, 1) * 2847;
                drawAnimatedCounter(ctx, W * 0.75, H * 0.18, this._counter, 2847, {
                    fontSize: 48, label: 'DOCUMENTS PENDING'
                });

                // Title fade in
                if (t < 4000) {
                    var titleAlpha = Ease.outCubic(Math.min(t / 2000, 1));
                    drawGlowText(ctx, 'THE PROBLEM', W / 2, H * 0.08, {
                        fontSize: 18, alpha: titleAlpha * 0.5,
                        color: 'rgba(239,68,68,0.8)', glowColor: 'rgba(239,68,68,0.3)'
                    });
                }
            },
            teardown: function(eng) { this._docs = null; this._dataStreams = null; }
        });

        // Scene 1.2 — Standards Wall (22s)
        Engine.scenes.push({
            id: 'standards_wall',
            duration: 22000,
            narration: 'The standards are endless. MIL-STD-498. DO-178C. IEEE 830. AS9100. Manual review takes weeks and still misses twenty percent of critical issues.',
            _standards: null,
            _progressVal: 0,
            setup: function(eng) {
                this._standards = [
                    'MIL-STD-498', 'DO-178C', 'IEEE 830', 'AS9100D',
                    'MIL-STD-1521', 'DO-254', 'ISO 9001', 'CMMI-DEV',
                    'SAE ARP4754', 'ECSS-E-ST-40C', 'MIL-STD-882E', 'ISO 15288'
                ];
                this._progressVal = 0;
            },
            render: function(ctx, t, W, H) {
                // Arrange documents into a wall
                var cols = 4, rows = 3;
                var docW = 100, docH = 130, gap = 20;
                var wallW = cols * (docW + gap) - gap;
                var wallH = rows * (docH + gap) - gap;
                var startX = (W - wallW) / 2;
                var startY = (H - wallH) / 2 - 30;

                for (var r = 0; r < rows; r++) {
                    for (var c = 0; c < cols; c++) {
                        var idx = r * cols + c;
                        if (idx >= this._standards.length) break;
                        var dx = startX + c * (docW + gap);
                        var dy = startY + r * (docH + gap);

                        // Slide in animation
                        var slideP = Ease.outCubic(Math.min(Math.max(t - idx * 300, 0) / 1500, 1));
                        dy = dy + 100 * (1 - slideP);

                        drawWireframeDoc(ctx, dx, dy, docW, docH, { alpha: slideP * 0.6 });

                        // Type in standard name
                        var typeP = Math.min(Math.max(t - idx * 300 - 800, 0) / 1200, 1);
                        _drawStandardLabel(ctx, this._standards[idx], dx + 8, dy + 25, typeP);
                    }
                }

                // Progress bar — stuck at 20%
                this._progressVal = Math.min(t / 15000, 0.20);
                var barX = W * 0.3, barY = H * 0.85, barW = W * 0.4, barH = 12;
                ctx.fillStyle = 'rgba(214,168,74,0.1)';
                ctx.fillRect(barX, barY, barW, barH);
                ctx.fillStyle = 'rgba(239,68,68,0.7)';
                ctx.fillRect(barX, barY, barW * this._progressVal, barH);
                drawHUDBrackets(ctx, barX - 5, barY - 5, barW + 10, barH + 10, Math.min(t / 1000, 1));

                // "20%" counter in red
                if (t > 10000) {
                    var cAlpha = Ease.outCubic(Math.min((t - 10000) / 2000, 1));
                    drawGlowText(ctx, '20%', W * 0.75, H * 0.85, {
                        fontSize: 36, color: 'rgba(239,68,68,0.9)',
                        glowColor: 'rgba(239,68,68,0.5)', alpha: cAlpha
                    });
                    drawGlowText(ctx, 'ISSUES MISSED', W * 0.75, H * 0.85 + 30, {
                        fontSize: 14, color: 'rgba(239,68,68,0.6)',
                        glowColor: 'rgba(239,68,68,0.3)', alpha: cAlpha
                    });
                }
            },
            teardown: function() { this._standards = null; }
        });

        // Scene 1.3 — Breaking Point (21s)
        Engine.scenes.push({
            id: 'breaking_point',
            duration: 21000,
            narration: 'A missed requirement cascades. A defective deliverable ships. The cost to fix grows ten times with every phase. The old way is broken.',
            _shakeIntensity: 0,
            _crackProgress: 0,
            _cursorBlink: true,
            setup: function(eng) {
                this._shakeIntensity = 0;
                this._crackProgress = 0;
            },
            render: function(ctx, t, W, H, eng) {
                // Crack formation
                if (t > 2000 && t < 12000) {
                    this._crackProgress = Math.min((t - 2000) / 8000, 1);
                    _drawCracks(ctx, W / 2, H / 2, this._crackProgress, 8);
                }

                // Screen shake effect via camera
                if (t > 4000 && t < 10000) {
                    this._shakeIntensity = Math.min((t - 4000) / 3000, 1) * 8;
                    eng.camera.targetX = (Math.random() - 0.5) * this._shakeIntensity;
                    eng.camera.targetY = (Math.random() - 0.5) * this._shakeIntensity;
                    eng.camera.speed = 0.3;
                }
                if (t > 10000) {
                    eng.camera.targetX = 0;
                    eng.camera.targetY = 0;
                    eng.camera.speed = 0.05;
                }

                // Scattered doc debris
                if (t > 6000) {
                    var debrisAlpha = Math.min((t - 6000) / 3000, 0.5);
                    for (var i = 0; i < 15; i++) {
                        var seed = i * 7919;
                        var dx = W / 2 + Math.sin(seed) * (100 + (t - 6000) * 0.03 * ((seed % 5) + 1));
                        var dy = H / 2 + Math.cos(seed * 1.3) * (80 + (t - 6000) * 0.02 * ((seed % 4) + 1));
                        var rot = Math.sin(seed * 0.7 + t / 1000) * 0.5;
                        ctx.save();
                        ctx.translate(dx, dy);
                        ctx.rotate(rot);
                        ctx.globalAlpha = debrisAlpha * (1 - Math.min((t - 6000) / 10000, 0.8));
                        drawWireframeDoc(ctx, -20, -26, 40, 52, { color: 'rgba(239,68,68,0.4)' });
                        ctx.restore();
                    }
                }

                // "10X" cost multiplier
                if (t > 8000 && t < 16000) {
                    var tenXAlpha = Ease.outElastic(Math.min((t - 8000) / 2000, 1));
                    drawGlowText(ctx, '10X', W / 2, H * 0.3, {
                        fontSize: 80, color: 'rgba(239,68,68,0.9)',
                        glowColor: 'rgba(239,68,68,0.6)', alpha: tenXAlpha
                    });
                    drawGlowText(ctx, 'COST TO FIX', W / 2, H * 0.3 + 55, {
                        fontSize: 16, color: 'rgba(239,68,68,0.5)', alpha: tenXAlpha * 0.7
                    });
                }

                // Fade to single gold cursor blinking
                if (t > 15000) {
                    var fadeP = Math.min((t - 15000) / 3000, 1);
                    ctx.fillStyle = 'rgba(2,4,8,' + (fadeP * 0.9) + ')';
                    ctx.fillRect(0, 0, W, H);

                    // Blinking cursor
                    if (Math.sin(t / 400) > 0) {
                        ctx.fillStyle = 'rgba(214,168,74,' + fadeP + ')';
                        ctx.fillRect(W / 2 - 1, H / 2 - 12, 2, 24);
                    }
                }
            },
            teardown: function(eng) {
                eng.camera.targetX = 0;
                eng.camera.targetY = 0;
                eng.camera.speed = 0.03;
            }
        });

        // =================================================================
        // ACT 2: THE SOLUTION (~60s)
        // =================================================================

        // Scene 2.1 — AEGIS Boot (20s)
        Engine.scenes.push({
            id: 'aegis_boot',
            duration: 20000,
            narration: 'Introducing AEGIS. The Aerospace Engineering Governance and Inspection System. Built for classified networks. Zero cloud dependency. One hundred percent air-gapped.',
            _letterReveal: 0,
            setup: function(eng) {
                this._letterReveal = 0;
                eng.camera.targetZoom = 1;
            },
            render: function(ctx, t, W, H, eng) {
                var cx = W / 2, cy = H / 2;

                // Cursor expands to horizontal line
                if (t < 3000) {
                    var lineP = Ease.outExpo(Math.min(t / 2500, 1));
                    var lineW = lineP * W * 0.4;
                    ctx.strokeStyle = '#D6A84A';
                    ctx.lineWidth = 1.5;
                    ctx.shadowColor = 'rgba(214,168,74,0.6)';
                    ctx.shadowBlur = 10;
                    ctx.beginPath();
                    ctx.moveTo(cx - lineW / 2, cy);
                    ctx.lineTo(cx + lineW / 2, cy);
                    ctx.stroke();
                    ctx.shadowBlur = 0;
                }

                // Shield draws itself
                if (t > 2000) {
                    var shieldP = Math.min((t - 2000) / 3000, 1);
                    drawAEGISShield(ctx, cx, cy - 30, 80, shieldP);
                }

                // A-E-G-I-S letters
                if (t > 4000) {
                    var letters = ['A', 'E', 'G', 'I', 'S'];
                    var spacing = 50;
                    var startX = cx - (letters.length - 1) * spacing / 2;
                    for (var i = 0; i < letters.length; i++) {
                        var lp = Math.min(Math.max(t - 4000 - i * 400, 0) / 800, 1);
                        var ep = Ease.outBack(lp);
                        drawGlowText(ctx, letters[i], startX + i * spacing, cy + 80, {
                            fontSize: 42, alpha: ep,
                            glowColor: 'rgba(214,168,74,0.8)'
                        });
                    }
                }

                // HUD corners activate
                if (t > 6000) {
                    var hudP = Math.min((t - 6000) / 2000, 1);
                    var m = 60;
                    drawHUDBrackets(ctx, m, m, W - m * 2, H - m * 2, hudP, {
                        cornerLen: 30, color: 'rgba(214,168,74,' + (0.5 * hudP) + ')'
                    });
                }

                // Subtitle: tagline
                if (t > 12000) {
                    var tagP = Ease.outCubic(Math.min((t - 12000) / 2000, 1));
                    drawGlowText(ctx, 'AEROSPACE ENGINEERING GOVERNANCE & INSPECTION SYSTEM', cx, cy + 130, {
                        fontSize: 13, alpha: tagP * 0.6,
                        color: 'rgba(214,168,74,0.6)'
                    });
                }
            },
            teardown: function() {}
        });

        // Scene 2.2 — HUD Activates (20s)
        Engine.scenes.push({
            id: 'hud_activates',
            duration: 20000,
            narration: 'One hundred and five quality checkers activate. Four extraction strategies. Twelve integrated modules working in concert. The system comes alive.',
            _radarAngle: 0,
            _dataStreams: null,
            setup: function(eng) {
                this._radarAngle = 0;
                this._dataStreams = [];
                for (var i = 0; i < 8; i++) {
                    this._dataStreams.push(new DataStream(
                        eng.W * 0.05 + i * eng.W * 0.12, 40 + Math.random() * 40
                    ));
                }
            },
            render: function(ctx, t, W, H) {
                var cx = W / 2, cy = H / 2;

                // Data streams cascade
                for (var d = 0; d < this._dataStreams.length; d++) {
                    this._dataStreams[d].update(16);
                    this._dataStreams[d].render(ctx, H);
                }

                // Shield zooms out to corner
                var shrinkP = Ease.outCubic(Math.min(t / 3000, 1));
                var shieldX = cx + (W * 0.82 - cx) * shrinkP;
                var shieldY = cy + (H * 0.15 - cy) * shrinkP;
                var shieldSize = 80 - 45 * shrinkP;
                drawAEGISShield(ctx, shieldX, shieldY, shieldSize, 1);

                // 4 quadrant HUD panels
                if (t > 2000) {
                    var panelP = Ease.outCubic(Math.min((t - 2000) / 2000, 1));
                    var panels = [
                        { x: W * 0.12, y: H * 0.15, label: 'DOCUMENT\nREVIEW' },
                        { x: W * 0.12, y: H * 0.55, label: 'STATEMENT\nFORGE' },
                        { x: W * 0.55, y: H * 0.55, label: 'ROLES\nSTUDIO' },
                        { x: W * 0.55, y: H * 0.15, label: 'HYPERLINK\nVALIDATOR' }
                    ];
                    var panelW = W * 0.3, panelH = H * 0.28;
                    for (var i = 0; i < panels.length; i++) {
                        var pp = Math.min(Math.max(t - 2000 - i * 400, 0) / 1500, 1);
                        var ep = Ease.outCubic(pp);
                        ctx.globalAlpha = ep;
                        drawHUDBrackets(ctx, panels[i].x, panels[i].y, panelW, panelH, ep, {
                            cornerLen: 20
                        });
                        var lines = panels[i].label.split('\n');
                        for (var l = 0; l < lines.length; l++) {
                            drawGlowText(ctx, lines[l], panels[i].x + panelW / 2, panels[i].y + panelH / 2 - 8 + l * 22, {
                                fontSize: 14, alpha: ep * 0.7
                            });
                        }
                        ctx.globalAlpha = 1;
                    }
                }

                // Radar sweep
                if (t > 5000) {
                    this._radarAngle += 0.02;
                    drawRadarSweep(ctx, W * 0.5, H * 0.48, 60, this._radarAngle, {
                        color: 'rgba(214,168,74,0.15)'
                    });
                }

                // "105 CHECKERS" counter
                if (t > 8000) {
                    var countP = Math.min((t - 8000) / 4000, 1);
                    var val = Ease.outExpo(countP) * 105;
                    drawAnimatedCounter(ctx, cx, H * 0.88, val, 105, {
                        fontSize: 44, label: 'QUALITY CHECKERS ONLINE'
                    });
                }
            },
            teardown: function() { this._dataStreams = null; }
        });

        // Scene 2.3 — Document Scan (20s)
        Engine.scenes.push({
            id: 'document_scan',
            duration: 20000,
            narration: 'Drop a document. AEGIS dissects every sentence. Grammar. Compliance. Ambiguity. Acronyms. Over one hundred categories, analyzed in under sixty seconds.',
            _scanY: 0,
            _issueMarkers: null,
            _scoreVal: 0,
            setup: function(eng) {
                this._scanY = 0;
                this._issueMarkers = [];
                this._scoreVal = 0;
            },
            render: function(ctx, t, W, H, eng) {
                var cx = W / 2, cy = H / 2;

                // Document descends from top
                var docW = 140, docH = 190;
                var docTargetY = cy - docH / 2;
                var docY = -docH + (docTargetY + docH) * Ease.outCubic(Math.min(t / 3000, 1));
                drawWireframeDoc(ctx, cx - docW / 2, docY, docW, docH, { alpha: 0.8 });

                // Scan beam sweeps down the document
                if (t > 3000 && t < 12000) {
                    this._scanY = ((t - 3000) / 8000) * docH;
                    var beamY = docY + this._scanY;
                    ctx.save();
                    ctx.strokeStyle = '#D6A84A';
                    ctx.lineWidth = 2;
                    ctx.shadowColor = 'rgba(214,168,74,0.8)';
                    ctx.shadowBlur = 15;
                    ctx.beginPath();
                    ctx.moveTo(cx - docW / 2 - 20, beamY);
                    ctx.lineTo(cx + docW / 2 + 20, beamY);
                    ctx.stroke();
                    ctx.restore();

                    // Emit issue markers at beam position
                    if (Math.random() < 0.08 && this._issueMarkers.length < 20) {
                        var severity = Math.random();
                        this._issueMarkers.push({
                            x: cx + (Math.random() - 0.5) * docW,
                            y: beamY,
                            targetX: W * 0.8,
                            targetY: H * 0.3 + this._issueMarkers.length * 18,
                            progress: 0,
                            color: severity < 0.3 ? 'rgba(239,68,68,0.8)' :
                                   severity < 0.6 ? 'rgba(245,158,11,0.8)' :
                                   'rgba(59,130,246,0.8)'
                        });
                    }
                }

                // Animate issue markers flying to severity bar
                for (var i = 0; i < this._issueMarkers.length; i++) {
                    var m = this._issueMarkers[i];
                    m.progress = Math.min(m.progress + 0.02, 1);
                    var mp = Ease.outCubic(m.progress);
                    var mx = m.x + (m.targetX - m.x) * mp;
                    var my = m.y + (m.targetY - m.y) * mp;
                    ctx.beginPath();
                    ctx.arc(mx, my, 3, 0, Math.PI * 2);
                    ctx.fillStyle = m.color;
                    ctx.fill();
                }

                // Severity bar chart
                if (t > 8000) {
                    var chartP = Math.min((t - 8000) / 3000, 1);
                    drawBarChart(ctx, W * 0.72, H * 0.2, 120, 150,
                        [12, 23, 38, 15], chartP, {
                            labels: ['Critical', 'Major', 'Minor', 'Info'],
                            colors: ['#ef4444', '#f59e0b', '#3b82f6', '#6b7280']
                        });
                }

                // Quality score gauge
                if (t > 12000) {
                    this._scoreVal = Ease.outCubic(Math.min((t - 12000) / 4000, 1)) * 87;
                    drawProgressRing(ctx, W * 0.2, cy, 55, this._scoreVal / 100, {
                        label: Math.floor(this._scoreVal) + '',
                        fgColor: this._scoreVal > 80 ? '#22c55e' : this._scoreVal > 60 ? '#f59e0b' : '#ef4444'
                    });
                    drawGlowText(ctx, 'QUALITY SCORE', W * 0.2, cy + 75, {
                        fontSize: 12, color: 'rgba(214,168,74,0.5)'
                    });
                }
            },
            teardown: function() { this._issueMarkers = null; }
        });

        // =================================================================
        // ACT 3: DEEP DIVE (~180s)
        // =================================================================

        // Scene 3.1 — Review Engine (30s)
        Engine.scenes.push({
            id: 'review_engine',
            duration: 30000,
            narration: 'Seventy-four configurable quality checkers. Grammar, compliance, style, readability, acronyms, cross-references. Every issue deduplicated and severity-graded. Typical review: under sixty seconds.',
            _nodes: null,
            setup: function(eng) {
                var categories = [
                    'Grammar', 'Spelling', 'Style', 'Readability',
                    'Compliance', 'Acronyms', 'Cross-Ref', 'Ambiguity',
                    'Requirements', 'Terminology', 'Figures', 'Tables'
                ];
                this._nodes = categories.map(function(name, i) {
                    var angle = (Math.PI * 2 / categories.length) * i - Math.PI / 2;
                    return { name: name, angle: angle, radius: 0 };
                });
            },
            render: function(ctx, t, W, H) {
                var cx = W / 2, cy = H / 2;

                // Central document
                drawWireframeDoc(ctx, cx - 50, cy - 65, 100, 130, { alpha: 0.6 });

                // Scan rings around document
                if (t > 2000) {
                    var ringP = Math.min((t - 2000) / 3000, 1);
                    for (var r = 1; r <= 3; r++) {
                        ctx.beginPath();
                        ctx.arc(cx, cy, 80 + r * 40, 0, Math.PI * 2 * ringP);
                        ctx.strokeStyle = 'rgba(214,168,74,' + (0.15 / r) + ')';
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }
                }

                // Checker category nodes in radial layout
                if (t > 4000) {
                    var maxR = Math.min(W, H) * 0.32;
                    for (var i = 0; i < this._nodes.length; i++) {
                        var node = this._nodes[i];
                        var np = Math.min(Math.max(t - 4000 - i * 300, 0) / 2000, 1);
                        node.radius = maxR * Ease.outBack(np);
                        var nx = cx + Math.cos(node.angle) * node.radius;
                        var ny = cy + Math.sin(node.angle) * node.radius;

                        // Connection line to center
                        drawConnectionLine(ctx, cx, cy, nx, ny, np, {
                            color: 'rgba(214,168,74,0.2)'
                        });

                        // Node circle + label
                        ctx.beginPath();
                        ctx.arc(nx, ny, 24, 0, Math.PI * 2);
                        ctx.fillStyle = 'rgba(214,168,74,0.08)';
                        ctx.fill();
                        ctx.strokeStyle = 'rgba(214,168,74,0.5)';
                        ctx.lineWidth = 1;
                        ctx.stroke();

                        drawGlowText(ctx, node.name, nx, ny, {
                            fontSize: 10, alpha: np * 0.8
                        });
                    }
                }

                // Triage cards sorting animation
                if (t > 15000) {
                    var triageP = Math.min((t - 15000) / 5000, 1);
                    var cards = ['Critical', 'Major', 'Minor', 'Info'];
                    var colors = ['#ef4444', '#f59e0b', '#3b82f6', '#6b7280'];
                    for (var c = 0; c < cards.length; c++) {
                        var cp = Math.min(Math.max(triageP - c * 0.15, 0) / 0.6, 1);
                        var cardX = W * 0.75;
                        var cardY = H * 0.2 + c * 55;
                        var slideX = cardX + 100 * (1 - Ease.outCubic(cp));
                        ctx.fillStyle = colors[c];
                        ctx.globalAlpha = cp * 0.15;
                        ctx.fillRect(slideX, cardY, 130, 42);
                        ctx.globalAlpha = 1;
                        ctx.strokeStyle = colors[c];
                        ctx.lineWidth = 1;
                        ctx.strokeRect(slideX, cardY, 130, 42);
                        drawGlowText(ctx, cards[c], slideX + 65, cardY + 21, {
                            fontSize: 13, color: colors[c], alpha: cp
                        });
                    }
                }
            },
            teardown: function() { this._nodes = null; }
        });

        // Scene 3.2 — Statement Forge (30s)
        Engine.scenes.push({
            id: 'statement_forge',
            duration: 30000,
            narration: 'Statement Forge extracts every shall, must, and will statement. Categorizes by directive type. Assigns responsible roles. Compares across document versions to track what changed.',
            setup: function() {},
            render: function(ctx, t, W, H) {
                var cx = W / 2, cy = H / 2;

                // Doc feeds into funnel
                var docAlpha = Math.min(t / 2000, 0.7);
                drawWireframeDoc(ctx, W * 0.15, H * 0.2, 100, 130, { alpha: docAlpha });

                // Funnel shape
                if (t > 2000) {
                    var fp = Ease.outCubic(Math.min((t - 2000) / 2000, 1));
                    ctx.save();
                    ctx.strokeStyle = 'rgba(214,168,74,' + (0.5 * fp) + ')';
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    ctx.moveTo(cx - 60, cy - 80);
                    ctx.lineTo(cx + 60, cy - 80);
                    ctx.lineTo(cx + 15, cy + 20);
                    ctx.lineTo(cx - 15, cy + 20);
                    ctx.closePath();
                    ctx.stroke();
                    ctx.fillStyle = 'rgba(214,168,74,0.03)';
                    ctx.fill();
                    ctx.restore();
                }

                // Statement cards emerge below funnel
                if (t > 6000) {
                    var directives = [
                        { text: 'SHALL', color: '#ef4444' },
                        { text: 'MUST', color: '#f59e0b' },
                        { text: 'WILL', color: '#3b82f6' },
                        { text: 'SHOULD', color: '#22c55e' }
                    ];
                    for (var i = 0; i < directives.length; i++) {
                        var sp = Math.min(Math.max(t - 6000 - i * 1500, 0) / 2000, 1);
                        var cardY = cy + 40 + Ease.outBack(sp) * (i * 50);
                        var cardX = cx - 70 + (i % 2) * 20;

                        ctx.fillStyle = directives[i].color;
                        ctx.globalAlpha = sp * 0.12;
                        ctx.fillRect(cardX, cardY, 140, 38);
                        ctx.globalAlpha = 1;

                        ctx.strokeStyle = directives[i].color;
                        ctx.lineWidth = 1;
                        ctx.strokeRect(cardX, cardY, 140, 38);

                        drawGlowText(ctx, directives[i].text, cardX + 70, cardY + 19, {
                            fontSize: 14, color: directives[i].color, alpha: sp
                        });
                    }
                }

                // Diff view with green/red highlights
                if (t > 18000) {
                    var diffP = Math.min((t - 18000) / 4000, 1);
                    var dX = W * 0.65, dY = H * 0.25;
                    drawHUDBrackets(ctx, dX, dY, 200, 250, diffP, { cornerLen: 12 });

                    var diffLines = [
                        { text: '+ Added requirement 4.3.1', color: '#22c55e' },
                        { text: '- Removed obsolete clause', color: '#ef4444' },
                        { text: '~ Modified delivery date', color: '#f59e0b' },
                        { text: '  Unchanged section 2.1', color: 'rgba(214,168,74,0.4)' }
                    ];
                    for (var d = 0; d < diffLines.length; d++) {
                        var dlp = Math.min(Math.max(diffP - d * 0.15, 0) / 0.5, 1);
                        ctx.font = '11px "Courier New", monospace';
                        ctx.fillStyle = diffLines[d].color;
                        ctx.globalAlpha = dlp;
                        ctx.textAlign = 'left';
                        ctx.fillText(diffLines[d].text, dX + 15, dY + 40 + d * 28);
                        ctx.globalAlpha = 1;
                    }
                }
            },
            teardown: function() {}
        });

        // Scene 3.3 — Roles Studio (30s)
        Engine.scenes.push({
            id: 'roles_studio',
            duration: 30000,
            narration: 'Every role discovered. Project Manager. Systems Engineer. Quality Lead. A living dictionary built automatically. Adjudication, RACI matrix, inheritance mapping. Zero manual data entry.',
            _graphNodes: null,
            setup: function(eng) {
                var roles = [
                    'Project Manager', 'Systems Engineer', 'Quality Lead',
                    'Test Engineer', 'Safety Officer', 'Config Manager',
                    'SW Lead', 'HW Lead'
                ];
                this._graphNodes = roles.map(function(name, i) {
                    var angle = (Math.PI * 2 / roles.length) * i - Math.PI / 2;
                    var r = Math.min(eng.W, eng.H) * 0.25;
                    return {
                        name: name, angle: angle,
                        x: eng.W / 2 + Math.cos(angle) * r,
                        y: eng.H / 2 + Math.sin(angle) * r,
                        connections: [Math.floor(Math.random() * roles.length)]
                    };
                });
            },
            render: function(ctx, t, W, H) {
                var cx = W / 2, cy = H / 2;

                // Network graph — nodes appear
                for (var i = 0; i < this._graphNodes.length; i++) {
                    var node = this._graphNodes[i];
                    var np = Math.min(Math.max(t - i * 500, 0) / 2000, 1);
                    var ep = Ease.outBack(np);

                    // Connection lines
                    for (var c = 0; c < node.connections.length; c++) {
                        var target = this._graphNodes[node.connections[c]];
                        if (target && np > 0.5) {
                            drawConnectionLine(ctx, node.x, node.y, target.x, target.y,
                                Math.min((np - 0.5) * 2, 1), { color: 'rgba(214,168,74,0.15)' });
                        }
                    }

                    // Node
                    ctx.save();
                    ctx.translate(node.x, node.y);
                    ctx.scale(ep, ep);

                    ctx.beginPath();
                    ctx.arc(0, 0, 30, 0, Math.PI * 2);
                    ctx.fillStyle = 'rgba(214,168,74,0.06)';
                    ctx.fill();
                    ctx.strokeStyle = 'rgba(214,168,74,0.5)';
                    ctx.lineWidth = 1;
                    ctx.stroke();

                    drawGlowText(ctx, node.name.split(' ')[0], 0, -4, {
                        fontSize: 10, alpha: np
                    });
                    if (node.name.split(' ').length > 1) {
                        drawGlowText(ctx, node.name.split(' ').slice(1).join(' '), 0, 10, {
                            fontSize: 9, alpha: np * 0.7
                        });
                    }

                    ctx.restore();
                }

                // RACI grid fills in
                if (t > 15000) {
                    var raciP = Math.min((t - 15000) / 6000, 1);
                    var gx = W * 0.05, gy = H * 0.75;
                    var cellW = 28, cellH = 20;
                    var raciLabels = ['R', 'A', 'C', 'I'];
                    var raciColors = ['#22c55e', '#3b82f6', '#f59e0b', '#6b7280'];

                    drawGlowText(ctx, 'RACI MATRIX', gx + 80, gy - 15, {
                        fontSize: 11, color: 'rgba(214,168,74,0.5)', align: 'left'
                    });

                    for (var row = 0; row < 4; row++) {
                        for (var col = 0; col < 6; col++) {
                            var cellP = Math.min(Math.max(raciP - (row * 6 + col) * 0.02, 0) / 0.3, 1);
                            if (cellP <= 0) continue;
                            var rVal = raciLabels[Math.floor(Math.random() * 4)];
                            var rIdx = raciLabels.indexOf(rVal);
                            ctx.fillStyle = raciColors[rIdx];
                            ctx.globalAlpha = cellP * 0.3;
                            ctx.fillRect(gx + col * cellW, gy + row * cellH, cellW - 2, cellH - 2);
                            ctx.globalAlpha = cellP;
                            ctx.font = '10px "Courier New", monospace';
                            ctx.textAlign = 'center';
                            ctx.fillStyle = raciColors[rIdx];
                            ctx.fillText(rVal, gx + col * cellW + cellW / 2, gy + row * cellH + cellH / 2 + 3);
                            ctx.globalAlpha = 1;
                        }
                    }
                }
            },
            teardown: function() { this._graphNodes = null; }
        });

        // Scene 3.4 — Proposal Compare (30s)
        Engine.scenes.push({
            id: 'proposal_compare',
            duration: 30000,
            narration: 'Side-by-side proposal analysis. Financial extraction from any format. Red flag detection per FAR 15.404. Deviation heatmaps. Vendor scores from A through F. All data, no guesswork.',
            setup: function() {},
            render: function(ctx, t, W, H) {
                var cx = W / 2, cy = H / 2;

                // Two proposals converge to center comparison engine
                var convP = Ease.outCubic(Math.min(t / 4000, 1));
                drawWireframeDoc(ctx, W * 0.15 + (cx - W * 0.15 - 60) * convP * 0.3, H * 0.3, 80, 105, { alpha: 0.6 });
                drawWireframeDoc(ctx, W * 0.7 - (W * 0.7 - cx - 20) * convP * 0.3, H * 0.3, 80, 105, { alpha: 0.6 });

                // Comparison engine box
                if (t > 3000) {
                    var engP = Ease.outCubic(Math.min((t - 3000) / 2000, 1));
                    drawHUDBrackets(ctx, cx - 50, cy - 30, 100, 60, engP, { cornerLen: 12 });
                    drawGlowText(ctx, 'COMPARE', cx, cy, { fontSize: 14, alpha: engP * 0.7 });
                }

                // Tornado chart
                if (t > 8000) {
                    var tp = Math.min((t - 8000) / 4000, 1);
                    var torX = W * 0.15, torY = H * 0.65;
                    drawGlowText(ctx, 'COST VARIANCE', torX + 80, torY - 10, {
                        fontSize: 11, color: 'rgba(214,168,74,0.5)', align: 'center'
                    });
                    var categories = ['Labor', 'Material', 'Travel', 'Software', 'ODC'];
                    for (var i = 0; i < categories.length; i++) {
                        var barP = Math.min(Math.max(tp - i * 0.1, 0) / 0.5, 1);
                        var barW = (30 + Math.random() * 60) * Ease.outCubic(barP);
                        var barY = torY + i * 22;
                        // Left bar (Vendor A)
                        ctx.fillStyle = 'rgba(59,130,246,0.5)';
                        ctx.fillRect(torX + 80 - barW, barY, barW, 16);
                        // Right bar (Vendor B)
                        ctx.fillStyle = 'rgba(239,68,68,0.5)';
                        ctx.fillRect(torX + 82, barY, barW * 0.8, 16);
                        // Label
                        ctx.font = '9px "Courier New", monospace';
                        ctx.fillStyle = 'rgba(214,168,74,0.6)';
                        ctx.textAlign = 'right';
                        ctx.fillText(categories[i], torX + 80 - barW - 5, barY + 12);
                    }
                }

                // Vendor scorecards with letter grades
                if (t > 16000) {
                    var sp = Math.min((t - 16000) / 4000, 1);
                    var grades = [
                        { vendor: 'VENDOR A', grade: 'A', color: '#22c55e' },
                        { vendor: 'VENDOR B', grade: 'B', color: '#3b82f6' },
                        { vendor: 'VENDOR C', grade: 'D', color: '#f59e0b' }
                    ];
                    for (var g = 0; g < grades.length; g++) {
                        var gp = Math.min(Math.max(sp - g * 0.2, 0) / 0.5, 1);
                        var gx = W * 0.55 + g * 110;
                        var gy = H * 0.62;
                        drawHUDBrackets(ctx, gx, gy, 90, 80, gp, { cornerLen: 10 });
                        drawGlowText(ctx, grades[g].grade, gx + 45, gy + 30, {
                            fontSize: 36, color: grades[g].color, alpha: gp
                        });
                        drawGlowText(ctx, grades[g].vendor, gx + 45, gy + 60, {
                            fontSize: 9, color: 'rgba(214,168,74,0.5)', alpha: gp
                        });
                    }
                }
            },
            teardown: function() {}
        });

        // Scene 3.5 — Hyperlink Validator (30s)
        Engine.scenes.push({
            id: 'hyperlink_validator',
            duration: 30000,
            narration: 'Every URL tested. HEAD, GET, SSL bypass, SSO authentication, headless browser for military and government sites. Six thousand links validated with zero false positives.',
            _urlDots: null,
            setup: function(eng) {
                this._urlDots = [];
                for (var i = 0; i < 30; i++) {
                    this._urlDots.push({
                        x: eng.W * 0.2 + Math.random() * eng.W * 0.2,
                        y: eng.H * 0.15 + Math.random() * eng.H * 0.6,
                        targetX: eng.W * 0.65 + Math.random() * eng.W * 0.25,
                        targetY: eng.H * 0.2 + Math.random() * eng.H * 0.5,
                        status: Math.random() < 0.7 ? 'ok' : Math.random() < 0.5 ? 'broken' : 'auth',
                        delay: i * 300,
                        progress: 0
                    });
                }
            },
            render: function(ctx, t, W, H) {
                // Document with URL markers on left
                drawWireframeDoc(ctx, W * 0.15, H * 0.2, 120, 160, { alpha: 0.5 });

                // URL dots traveling to globe
                var statusColors = { ok: '#22c55e', broken: '#ef4444', auth: '#f59e0b' };
                for (var i = 0; i < this._urlDots.length; i++) {
                    var dot = this._urlDots[i];
                    if (t < dot.delay) continue;
                    dot.progress = Math.min((t - dot.delay) / 3000, 1);
                    var dp = Ease.outCubic(dot.progress);
                    var dx = dot.x + (dot.targetX - dot.x) * dp;
                    var dy = dot.y + (dot.targetY - dot.y) * dp;

                    // Trail
                    ctx.beginPath();
                    ctx.moveTo(dot.x, dot.y);
                    ctx.lineTo(dx, dy);
                    ctx.strokeStyle = statusColors[dot.status];
                    ctx.globalAlpha = 0.15;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                    ctx.globalAlpha = 1;

                    // Dot
                    ctx.beginPath();
                    ctx.arc(dx, dy, 3, 0, Math.PI * 2);
                    ctx.fillStyle = statusColors[dot.status];
                    ctx.fill();

                    // Status icon at destination
                    if (dot.progress >= 1) {
                        var icon = dot.status === 'ok' ? '\u2713' : dot.status === 'broken' ? '\u2717' : '!';
                        ctx.font = '10px sans-serif';
                        ctx.fillStyle = statusColors[dot.status];
                        ctx.textAlign = 'center';
                        ctx.fillText(icon, dot.targetX, dot.targetY + 12);
                    }
                }

                // Globe icon representation
                if (t > 2000) {
                    var gp = Ease.outCubic(Math.min((t - 2000) / 2000, 1));
                    var gcx = W * 0.75, gcy = H * 0.45;
                    ctx.beginPath();
                    ctx.arc(gcx, gcy, 40 * gp, 0, Math.PI * 2);
                    ctx.strokeStyle = 'rgba(214,168,74,0.3)';
                    ctx.lineWidth = 1;
                    ctx.stroke();
                    // Longitude lines
                    for (var l = 0; l < 3; l++) {
                        ctx.beginPath();
                        ctx.ellipse(gcx, gcy, (15 + l * 12) * gp, 40 * gp, 0, 0, Math.PI * 2);
                        ctx.stroke();
                    }
                    // Latitude line
                    ctx.beginPath();
                    ctx.moveTo(gcx - 40 * gp, gcy);
                    ctx.lineTo(gcx + 40 * gp, gcy);
                    ctx.stroke();
                }

                // Counter: 6,000
                if (t > 15000) {
                    var countP = Math.min((t - 15000) / 5000, 1);
                    drawAnimatedCounter(ctx, W / 2, H * 0.88, Ease.outExpo(countP) * 6000, 6000, {
                        fontSize: 40, label: 'LINKS VALIDATED'
                    });
                }

                // Headless browser icon
                if (t > 20000) {
                    var hbP = Math.min((t - 20000) / 3000, 1);
                    var hbx = W * 0.5, hby = H * 0.15;
                    drawHUDBrackets(ctx, hbx - 45, hby - 18, 90, 36, hbP, { cornerLen: 8 });
                    drawGlowText(ctx, 'HEADLESS', hbx, hby, {
                        fontSize: 12, alpha: hbP * 0.7,
                        color: 'rgba(139,92,246,0.8)', glowColor: 'rgba(139,92,246,0.4)'
                    });
                }
            },
            teardown: function() { this._urlDots = null; }
        });

        // Scene 3.6 — Learning System (30s)
        Engine.scenes.push({
            id: 'learning_system',
            duration: 30000,
            narration: 'Five learning modules that remember your corrections. Document review. Statement forge. Roles. Hyperlink validator. Proposal compare. Every pattern stored locally. Zero data ever leaves your machine.',
            _brainPulse: 0,
            setup: function() { this._brainPulse = 0; },
            render: function(ctx, t, W, H) {
                var cx = W / 2, cy = H / 2;

                // Brain wireframe (simplified as connected circles)
                var brainP = Ease.outCubic(Math.min(t / 3000, 1));
                this._brainPulse = 0.7 + 0.3 * Math.sin(t / 800);

                ctx.save();
                ctx.translate(cx, cy - 20);
                ctx.scale(brainP, brainP);

                // Brain outline — two hemispheres
                ctx.strokeStyle = 'rgba(214,168,74,' + (0.5 * this._brainPulse) + ')';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.arc(-20, 0, 45, Math.PI * 0.5, Math.PI * 1.5);
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(20, 0, 45, -Math.PI * 0.5, Math.PI * 0.5);
                ctx.stroke();
                // Bridge
                ctx.beginPath();
                ctx.moveTo(-20, -45); ctx.lineTo(20, -45);
                ctx.moveTo(-20, 45); ctx.lineTo(20, 45);
                ctx.strokeStyle = 'rgba(214,168,74,0.3)';
                ctx.stroke();

                ctx.restore();

                // 5 orbiting satellite nodes (learning modules)
                if (t > 4000) {
                    var modules = [
                        { name: 'Document\nReview', color: '#3b82f6' },
                        { name: 'Statement\nForge', color: '#f59e0b' },
                        { name: 'Roles', color: '#a855f7' },
                        { name: 'Hyperlink\nValidator', color: '#22c55e' },
                        { name: 'Proposal\nCompare', color: '#f43f5e' }
                    ];
                    var orbitR = Math.min(W, H) * 0.3;
                    for (var i = 0; i < modules.length; i++) {
                        var mp = Math.min(Math.max(t - 4000 - i * 800, 0) / 2000, 1);
                        var angle = (Math.PI * 2 / modules.length) * i - Math.PI / 2 + t / 15000;
                        var mx = cx + Math.cos(angle) * orbitR * Ease.outBack(mp);
                        var my = (cy - 20) + Math.sin(angle) * orbitR * 0.6 * Ease.outBack(mp);

                        // Orbit path
                        if (mp > 0.5) {
                            drawConnectionLine(ctx, cx, cy - 20, mx, my, 1, {
                                color: 'rgba(214,168,74,0.1)', dotRadius: 0
                            });
                        }

                        // Module node
                        ctx.beginPath();
                        ctx.arc(mx, my, 28, 0, Math.PI * 2);
                        ctx.fillStyle = modules[i].color;
                        ctx.globalAlpha = mp * 0.1;
                        ctx.fill();
                        ctx.globalAlpha = 1;
                        ctx.strokeStyle = modules[i].color;
                        ctx.lineWidth = 1;
                        ctx.globalAlpha = mp * 0.6;
                        ctx.stroke();
                        ctx.globalAlpha = 1;

                        var lines = modules[i].name.split('\n');
                        for (var l = 0; l < lines.length; l++) {
                            drawGlowText(ctx, lines[l], mx, my - 4 + l * 14, {
                                fontSize: 9, alpha: mp * 0.8, color: modules[i].color,
                                glowColor: modules[i].color.replace(')', ',0.3)')
                            });
                        }
                    }
                }

                // Data stream flowing into brain
                if (t > 12000) {
                    var streamP = Math.min((t - 12000) / 3000, 1);
                    for (var s = 0; s < 8; s++) {
                        var sy = cy + 100 + s * 15;
                        var sx = cx - 80 + Math.sin(t / 500 + s) * 30;
                        var stx = cx, sty = cy - 20;
                        drawConnectionLine(ctx, sx, sy, stx, sty,
                            Math.min(streamP + Math.sin(t / 300 + s) * 0.3, 1), {
                                color: 'rgba(214,168,74,0.15)', dotColor: '#D6A84A', dotRadius: 2
                            });
                    }
                }

                // Lock icon — privacy
                if (t > 20000) {
                    var lockP = Ease.outBack(Math.min((t - 20000) / 2000, 1));
                    var lx = cx, ly = H * 0.85;
                    ctx.save();
                    ctx.translate(lx, ly);
                    ctx.scale(lockP, lockP);
                    // Padlock body
                    ctx.fillStyle = 'rgba(214,168,74,0.2)';
                    ctx.fillRect(-12, 0, 24, 18);
                    ctx.strokeStyle = '#D6A84A';
                    ctx.lineWidth = 1.5;
                    ctx.strokeRect(-12, 0, 24, 18);
                    // Shackle
                    ctx.beginPath();
                    ctx.arc(0, 0, 10, Math.PI, 0);
                    ctx.stroke();
                    ctx.restore();

                    drawGlowText(ctx, 'ALL DATA STAYS LOCAL', lx, ly + 30, {
                        fontSize: 11, alpha: lockP * 0.6, color: 'rgba(214,168,74,0.5)'
                    });
                }
            },
            teardown: function() {}
        });

        // =================================================================
        // ACTS 4-6 will be added via Edit in Part 4
        // =================================================================
        _buildScenesAct4to6();
    }

    /** Acts 4-6 scene definitions */
    function _buildScenesAct4to6() {

        // =================================================================
        // ACT 4: THE NUMBERS (~55s)
        // =================================================================

        // Scene 4.1 — Stat Cascade (30s)
        Engine.scenes.push({
            id: 'stat_cascade',
            duration: 30000,
            narration: 'One hundred and five checkers. One hundred ninety-three API endpoints. Five hundred forty-five audio narration clips. One hundred thirty-seven version releases. Twelve integrated modules. Seven file formats. Four extraction strategies.',
            _stats: null,
            _dataStreams: null,
            setup: function(eng) {
                this._stats = [
                    { value: 105, label: 'QUALITY CHECKERS', delay: 1000 },
                    { value: 193, label: 'API ENDPOINTS', delay: 4000 },
                    { value: 545, label: 'AUDIO CLIPS', delay: 7000 },
                    { value: 137, label: 'VERSION RELEASES', delay: 10000 },
                    { value: 12, label: 'MODULES', delay: 13000 },
                    { value: 7, label: 'FILE FORMATS', delay: 16000 },
                    { value: 4, label: 'EXTRACTION STRATEGIES', delay: 19000 }
                ];
                this._dataStreams = [];
                for (var i = 0; i < 10; i++) {
                    this._dataStreams.push(new DataStream(i * eng.W * 0.1 + 20, 30 + Math.random() * 50));
                }
            },
            render: function(ctx, t, W, H, eng) {
                // Background data rain
                for (var d = 0; d < this._dataStreams.length; d++) {
                    this._dataStreams[d].update(16);
                    this._dataStreams[d].render(ctx, H);
                }

                // Stats appear one at a time with burst transitions
                var activeIdx = -1;
                for (var i = this._stats.length - 1; i >= 0; i--) {
                    if (t >= this._stats[i].delay) { activeIdx = i; break; }
                }

                if (activeIdx >= 0) {
                    var stat = this._stats[activeIdx];
                    var elapsed = t - stat.delay;
                    var countP = Ease.outExpo(Math.min(elapsed / 2000, 1));
                    var scaleP = Ease.outBack(Math.min(elapsed / 800, 1));

                    ctx.save();
                    ctx.translate(W / 2, H / 2 - 20);
                    ctx.scale(scaleP, scaleP);

                    drawGlowText(ctx, Math.floor(stat.value * countP).toLocaleString(), 0, 0, {
                        fontSize: 90, glowColor: 'rgba(214,168,74,0.9)'
                    });
                    drawGlowText(ctx, stat.label, 0, 65, {
                        fontSize: 18, color: 'rgba(214,168,74,0.5)',
                        glowColor: 'rgba(214,168,74,0.2)'
                    });

                    ctx.restore();

                    // Burst particles on reveal
                    if (elapsed < 100 && elapsed > 0) {
                        eng.particleSystems.push(new ParticleSystem({
                            x: W / 2, y: H / 2, type: 'burst', count: 25, lifetime: 2000
                        }));
                    }
                }

                // Faded previous stats along the bottom
                for (var j = 0; j < activeIdx; j++) {
                    var sx = W * 0.1 + j * (W * 0.8 / Math.max(activeIdx, 1));
                    drawGlowText(ctx, this._stats[j].value + '', sx, H * 0.88, {
                        fontSize: 20, alpha: 0.3
                    });
                    ctx.font = '8px "Courier New", monospace';
                    ctx.fillStyle = 'rgba(214,168,74,0.2)';
                    ctx.textAlign = 'center';
                    ctx.fillText(this._stats[j].label, sx, H * 0.88 + 18);
                }
            },
            teardown: function() { this._stats = null; this._dataStreams = null; }
        });

        // Scene 4.2 — Architecture Overview (25s)
        Engine.scenes.push({
            id: 'architecture_overview',
            duration: 25000,
            narration: 'Pure Flask and vanilla JavaScript. No frameworks. No dependencies you cannot control. SQLite for persistence. Canvas for visualization. Every single line of code serves one purpose.',
            _layers: null,
            setup: function(eng) {
                this._layers = [
                    { name: 'FLASK SERVER', y: 0.15, color: '#3b82f6', w: 0.7 },
                    { name: 'ROUTE BLUEPRINTS', y: 0.30, color: '#8b5cf6', w: 0.65 },
                    { name: '105 QUALITY CHECKERS', y: 0.45, color: '#f59e0b', w: 0.55 },
                    { name: 'NLP PIPELINE', y: 0.60, color: '#22c55e', w: 0.45 },
                    { name: 'VANILLA JS FRONTEND', y: 0.75, color: '#D6A84A', w: 0.6 },
                    { name: 'SQLITE + LEARNING', y: 0.87, color: '#6b7280', w: 0.5 }
                ];
            },
            render: function(ctx, t, W, H) {
                // Architecture layers animate in from left
                for (var i = 0; i < this._layers.length; i++) {
                    var layer = this._layers[i];
                    var lp = Math.min(Math.max(t - i * 1200, 0) / 2000, 1);
                    var ep = Ease.outCubic(lp);
                    var lx = W * (0.5 - layer.w / 2);
                    var lw = W * layer.w;
                    var ly = H * layer.y;
                    var lh = 35;

                    // Slide in from left
                    var slideX = lx - W * (1 - ep);

                    ctx.fillStyle = layer.color;
                    ctx.globalAlpha = ep * 0.1;
                    ctx.fillRect(slideX, ly, lw, lh);
                    ctx.globalAlpha = ep * 0.6;
                    ctx.strokeStyle = layer.color;
                    ctx.lineWidth = 1;
                    ctx.strokeRect(slideX, ly, lw, lh);
                    ctx.globalAlpha = 1;

                    drawGlowText(ctx, layer.name, slideX + lw / 2, ly + lh / 2, {
                        fontSize: 12, color: layer.color, alpha: ep * 0.8,
                        glowColor: layer.color.replace(')', ',0.3)').replace('rgb', 'rgba')
                    });

                    // Connection arrows between layers
                    if (i > 0 && ep > 0.5) {
                        var prevLayer = this._layers[i - 1];
                        ctx.beginPath();
                        ctx.moveTo(W / 2, H * prevLayer.y + 35);
                        ctx.lineTo(W / 2, ly);
                        ctx.strokeStyle = 'rgba(214,168,74,0.15)';
                        ctx.lineWidth = 1;
                        ctx.stroke();
                    }
                }

                // Code scroll effect on right side
                if (t > 10000) {
                    var codeP = Math.min((t - 10000) / 5000, 1);
                    var codeLines = [
                        'app = Flask(__name__)',
                        'engine = AEGISEngine()',
                        'results = engine.review(doc)',
                        'score = calculate_quality()',
                        'db.save_scan(results)',
                        'return jsonify(data)'
                    ];
                    var codeX = W * 0.78;
                    for (var c = 0; c < codeLines.length; c++) {
                        var cp = Math.min(Math.max(codeP - c * 0.1, 0) / 0.4, 1);
                        ctx.font = '11px "Courier New", monospace';
                        ctx.fillStyle = 'rgba(214,168,74,' + (cp * 0.5) + ')';
                        ctx.textAlign = 'left';
                        ctx.fillText(codeLines[c], codeX, H * 0.25 + c * 22);
                    }
                }
            },
            teardown: function() { this._layers = null; }
        });

        // =================================================================
        // ACT 5: AIR-GAPPED (~50s)
        // =================================================================

        // Scene 5.1 — Fortress (25s)
        Engine.scenes.push({
            id: 'fortress',
            duration: 25000,
            narration: 'No internet required. No cloud dependency. No telemetry. One hundred ninety-five prepackaged wheel files. Complete offline installation. Your data never leaves the building.',
            _cloudIcons: null,
            setup: function(eng) {
                this._cloudIcons = [];
                for (var i = 0; i < 5; i++) {
                    this._cloudIcons.push({
                        x: eng.W * 0.2 + i * eng.W * 0.15,
                        y: eng.H * 0.15 + Math.random() * eng.H * 0.1,
                        pushed: false
                    });
                }
            },
            render: function(ctx, t, W, H) {
                var cx = W / 2, cy = H / 2;

                // Hexagonal fortress
                var fortP = Ease.outCubic(Math.min(t / 4000, 1));
                _drawHexFortress(ctx, cx, cy, Math.min(W, H) * 0.25, fortP);

                // Cloud icons being pushed away
                if (t > 3000) {
                    var pushP = Math.min((t - 3000) / 3000, 1);
                    for (var i = 0; i < this._cloudIcons.length; i++) {
                        var cloud = this._cloudIcons[i];
                        var pushDist = pushP * 200;
                        var cx2 = cloud.x + (cloud.x < W / 2 ? -pushDist : pushDist);
                        var cy2 = cloud.y - pushDist * 0.5;
                        var alpha = 1 - pushP;

                        // Simple cloud shape
                        ctx.save();
                        ctx.globalAlpha = alpha * 0.4;
                        ctx.fillStyle = 'rgba(100,100,120,0.5)';
                        ctx.beginPath();
                        ctx.arc(cx2, cy2, 18, 0, Math.PI * 2);
                        ctx.arc(cx2 + 14, cy2 + 3, 14, 0, Math.PI * 2);
                        ctx.arc(cx2 - 12, cy2 + 4, 12, 0, Math.PI * 2);
                        ctx.fill();
                        ctx.restore();

                        // X mark
                        if (pushP > 0.5) {
                            ctx.strokeStyle = 'rgba(239,68,68,' + ((pushP - 0.5) * 2 * alpha) + ')';
                            ctx.lineWidth = 2;
                            ctx.beginPath();
                            ctx.moveTo(cx2 - 8, cy2 - 8); ctx.lineTo(cx2 + 8, cy2 + 8);
                            ctx.moveTo(cx2 + 8, cy2 - 8); ctx.lineTo(cx2 - 8, cy2 + 8);
                            ctx.stroke();
                        }
                    }
                }

                // Padlock grows in center of fortress
                if (t > 6000) {
                    var lockP = Ease.outBack(Math.min((t - 6000) / 2000, 1));
                    ctx.save();
                    ctx.translate(cx, cy);
                    ctx.scale(lockP, lockP);
                    // Padlock body
                    ctx.fillStyle = 'rgba(214,168,74,0.15)';
                    ctx.fillRect(-18, 5, 36, 26);
                    ctx.strokeStyle = '#D6A84A';
                    ctx.lineWidth = 2;
                    ctx.strokeRect(-18, 5, 36, 26);
                    // Shackle
                    ctx.beginPath();
                    ctx.arc(0, 5, 14, Math.PI, 0);
                    ctx.stroke();
                    // Keyhole
                    ctx.beginPath();
                    ctx.arc(0, 16, 4, 0, Math.PI * 2);
                    ctx.fillStyle = '#D6A84A';
                    ctx.fill();
                    ctx.restore();
                }

                // "195 WHEELS" counter
                if (t > 12000) {
                    var wheelP = Math.min((t - 12000) / 4000, 1);
                    drawAnimatedCounter(ctx, cx, H * 0.82, Ease.outExpo(wheelP) * 195, 195, {
                        fontSize: 44, label: 'OFFLINE WHEEL PACKAGES'
                    });
                }

                // NO INTERNET / NO CLOUD / NO TELEMETRY labels
                if (t > 16000) {
                    var labels = ['NO INTERNET', 'NO CLOUD', 'NO TELEMETRY'];
                    for (var l = 0; l < labels.length; l++) {
                        var lp = Math.min(Math.max(t - 16000 - l * 1200, 0) / 1500, 1);
                        drawGlowText(ctx, labels[l], W * 0.15 + l * W * 0.35, H * 0.15, {
                            fontSize: 14, alpha: Ease.outCubic(lp) * 0.6,
                            color: 'rgba(239,68,68,0.7)', glowColor: 'rgba(239,68,68,0.3)'
                        });
                    }
                }
            },
            teardown: function() { this._cloudIcons = null; }
        });

        // Scene 5.2 — Classified Ready (25s)
        Engine.scenes.push({
            id: 'classified_ready',
            duration: 25000,
            narration: 'Deployed inside classified enclaves. DoD facilities. Northrop Grumman secure networks. Windows SSO authentication. SharePoint integration. Built for the environments that need it most.',
            setup: function() {},
            render: function(ctx, t, W, H) {
                var cx = W / 2, cy = H / 2;

                // Network boundary diagram
                var outerP = Ease.outCubic(Math.min(t / 3000, 1));
                // Outer boundary (classified)
                ctx.strokeStyle = 'rgba(239,68,68,0.4)';
                ctx.lineWidth = 2;
                ctx.setLineDash([8, 4]);
                ctx.beginPath();
                ctx.rect(cx - W * 0.35, cy - H * 0.35, W * 0.7, H * 0.6);
                ctx.globalAlpha = outerP;
                ctx.stroke();
                ctx.setLineDash([]);
                ctx.globalAlpha = 1;

                drawGlowText(ctx, 'CLASSIFIED NETWORK BOUNDARY', cx, cy - H * 0.35 - 12, {
                    fontSize: 11, color: 'rgba(239,68,68,0.6)', alpha: outerP
                });

                // Inner network with AEGIS at center
                if (t > 2000) {
                    var innerP = Ease.outCubic(Math.min((t - 2000) / 2000, 1));
                    drawAEGISShield(ctx, cx, cy, 40, innerP);

                    // Connected nodes
                    var nodes = [
                        { label: 'WINDOWS\nSSO', x: cx - 160, y: cy - 60 },
                        { label: 'SHAREPOINT', x: cx + 160, y: cy - 60 },
                        { label: 'SQLITE', x: cx - 130, y: cy + 80 },
                        { label: 'LOCAL\nFILES', x: cx + 130, y: cy + 80 }
                    ];
                    for (var i = 0; i < nodes.length; i++) {
                        var np = Math.min(Math.max(t - 3000 - i * 600, 0) / 1500, 1);
                        drawConnectionLine(ctx, cx, cy, nodes[i].x, nodes[i].y, np, {
                            color: 'rgba(214,168,74,0.2)'
                        });
                        drawHUDBrackets(ctx, nodes[i].x - 45, nodes[i].y - 20, 90, 40,
                            Ease.outCubic(np), { cornerLen: 8 });
                        var lines = nodes[i].label.split('\n');
                        for (var l = 0; l < lines.length; l++) {
                            drawGlowText(ctx, lines[l], nodes[i].x, nodes[i].y - 4 + l * 14, {
                                fontSize: 10, alpha: np * 0.7
                            });
                        }
                    }
                }

                // CLASSIFIED stamps
                if (t > 12000) {
                    var stampP = Ease.outBack(Math.min((t - 12000) / 1500, 1));
                    ctx.save();
                    ctx.translate(W * 0.78, H * 0.75);
                    ctx.rotate(-0.15);
                    ctx.scale(stampP, stampP);
                    ctx.strokeStyle = 'rgba(239,68,68,0.6)';
                    ctx.lineWidth = 3;
                    ctx.strokeRect(-55, -15, 110, 30);
                    drawGlowText(ctx, 'CLASSIFIED', 0, 0, {
                        fontSize: 18, color: 'rgba(239,68,68,0.7)',
                        glowColor: 'rgba(239,68,68,0.4)'
                    });
                    ctx.restore();
                }

                // SSO flow animation
                if (t > 16000) {
                    var ssoP = Math.min((t - 16000) / 4000, 1);
                    var steps = ['USER', 'NTLM/SPNEGO', 'AEGIS', 'VALIDATED'];
                    var stepColors = ['#6b7280', '#f59e0b', '#D6A84A', '#22c55e'];
                    for (var s = 0; s < steps.length; s++) {
                        var sp = Math.min(Math.max(ssoP - s * 0.2, 0) / 0.4, 1);
                        var sx = W * 0.2 + s * W * 0.2;
                        var sy = H * 0.88;

                        drawGlowText(ctx, steps[s], sx, sy, {
                            fontSize: 11, color: stepColors[s], alpha: sp
                        });

                        if (s < steps.length - 1 && sp > 0.5) {
                            drawConnectionLine(ctx, sx + 30, sy, sx + W * 0.2 - 30, sy,
                                Math.min((sp - 0.5) * 2, 1), {
                                    color: 'rgba(214,168,74,0.3)', dotRadius: 2
                                });
                        }
                    }
                }
            },
            teardown: function() {}
        });

        // =================================================================
        // ACT 6: FINALE (~40s)
        // =================================================================

        // Scene 6.1 — Convergence (20s)
        Engine.scenes.push({
            id: 'convergence',
            duration: 20000,
            narration: 'Twelve modules. One hundred and five checkers. Five learning systems. One mission. Helping engineers write better documents. Faster. More accurately. Every single time.',
            _moduleIcons: null,
            setup: function(eng) {
                var modules = [
                    'Document Review', 'Statement Forge', 'Roles Studio',
                    'Hyperlink Validator', 'Proposal Compare', 'Metrics',
                    'Data Explorer', 'Portfolio', 'Learning System',
                    'Export Suite', 'Fix Assistant', 'Guide System'
                ];
                this._moduleIcons = modules.map(function(name, i) {
                    var angle = (Math.PI * 2 / modules.length) * i - Math.PI / 2;
                    var r = Math.min(eng.W, eng.H) * 0.38;
                    return {
                        name: name.split(' ')[0],
                        fullName: name,
                        x: eng.W / 2 + Math.cos(angle) * r,
                        y: eng.H / 2 + Math.sin(angle) * r,
                        angle: angle,
                        r: r
                    };
                });
            },
            render: function(ctx, t, W, H, eng) {
                var cx = W / 2, cy = H / 2;

                // Module icons start at edges, converge toward center
                var convergeP = Ease.inOutCubic(Math.min(t / 12000, 1));

                for (var i = 0; i < this._moduleIcons.length; i++) {
                    var icon = this._moduleIcons[i];
                    var ip = Math.min(Math.max(t - i * 200, 0) / 2000, 1);
                    var ep = Ease.outCubic(ip);

                    // Current position (converging toward center)
                    var currentR = icon.r * (1 - convergeP * 0.65);
                    var ix = cx + Math.cos(icon.angle + t / 20000) * currentR;
                    var iy = cy + Math.sin(icon.angle + t / 20000) * currentR;

                    // Connection to center
                    if (ep > 0.3) {
                        drawConnectionLine(ctx, ix, iy, cx, cy, ep, {
                            color: 'rgba(214,168,74,0.1)', dotRadius: 0
                        });
                    }

                    // Icon node
                    ctx.beginPath();
                    ctx.arc(ix, iy, 20, 0, Math.PI * 2);
                    ctx.fillStyle = 'rgba(214,168,74,' + (ep * 0.08) + ')';
                    ctx.fill();
                    ctx.strokeStyle = 'rgba(214,168,74,' + (ep * 0.4) + ')';
                    ctx.lineWidth = 1;
                    ctx.stroke();

                    drawGlowText(ctx, icon.name, ix, iy, {
                        fontSize: 9, alpha: ep * (1 - convergeP * 0.8)
                    });
                }

                // Central shield grows as icons converge
                if (t > 5000) {
                    var shieldSize = 30 + convergeP * 50;
                    drawAEGISShield(ctx, cx, cy, shieldSize, Math.min((t - 5000) / 3000, 1));
                }

                // Ring forms around shield
                if (convergeP > 0.6) {
                    var ringAlpha = (convergeP - 0.6) / 0.4;
                    ctx.beginPath();
                    ctx.arc(cx, cy, icon.r * 0.35, 0, Math.PI * 2);
                    ctx.strokeStyle = 'rgba(214,168,74,' + (ringAlpha * 0.4) + ')';
                    ctx.lineWidth = 1.5;
                    ctx.stroke();
                }

                // Converge to single bright light at end
                if (t > 16000) {
                    var lightP = Math.min((t - 16000) / 4000, 1);
                    var grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, 100 * lightP);
                    grad.addColorStop(0, 'rgba(214,168,74,' + (lightP * 0.6) + ')');
                    grad.addColorStop(1, 'rgba(214,168,74,0)');
                    ctx.fillStyle = grad;
                    ctx.fillRect(cx - 100, cy - 100, 200, 200);
                }
            },
            teardown: function() { this._moduleIcons = null; }
        });

        // Scene 6.2 — Logo Reveal (20s)
        Engine.scenes.push({
            id: 'logo_reveal',
            duration: 20000,
            narration: 'AEGIS. Built by engineers. For engineers.',
            _maxParticles: false,
            setup: function(eng) {
                this._maxParticles = false;
                // Initial burst
                eng.particleSystems.push(new ParticleSystem({
                    x: eng.W / 2, y: eng.H / 2, type: 'burst', count: 50, lifetime: 5000
                }));
            },
            render: function(ctx, t, W, H, eng) {
                var cx = W / 2, cy = H / 2;

                // Light expands from center
                if (t < 4000) {
                    var expandP = Ease.outExpo(Math.min(t / 3000, 1));
                    var grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, expandP * Math.max(W, H) * 0.5);
                    grad.addColorStop(0, 'rgba(214,168,74,' + (0.3 * (1 - expandP)) + ')');
                    grad.addColorStop(1, 'rgba(214,168,74,0)');
                    ctx.fillStyle = grad;
                    ctx.fillRect(0, 0, W, H);
                }

                // AEGIS shield at full size
                if (t > 2000) {
                    var shieldP = Ease.outElastic(Math.min((t - 2000) / 3000, 1));
                    drawAEGISShield(ctx, cx, cy - 40, 100, shieldP);
                }

                // Title: AEGIS
                if (t > 4000) {
                    var titleP = Ease.outCubic(Math.min((t - 4000) / 2000, 1));
                    drawGlowText(ctx, 'A E G I S', cx, cy + 90, {
                        fontSize: 52, alpha: titleP,
                        glowColor: 'rgba(214,168,74,0.9)'
                    });
                }

                // Tagline
                if (t > 7000) {
                    var tagP = Ease.outCubic(Math.min((t - 7000) / 2000, 1));
                    drawGlowText(ctx, 'Aerospace Engineering Governance & Inspection System', cx, cy + 135, {
                        fontSize: 14, alpha: tagP * 0.6,
                        color: 'rgba(214,168,74,0.6)'
                    });
                }

                // "Built by engineers. For engineers."
                if (t > 9000) {
                    var mottoP = Ease.outCubic(Math.min((t - 9000) / 2000, 1));
                    drawGlowText(ctx, 'Built by engineers. For engineers.', cx, cy + 170, {
                        fontSize: 16, alpha: mottoP * 0.8,
                        font: 'italic 16px "Courier New", monospace'
                    });
                }

                // Maximum particle density
                if (t > 5000 && !this._maxParticles) {
                    this._maxParticles = true;
                    eng.particleSystems.push(new ParticleSystem({
                        x: cx, y: cy, type: 'ambient',
                        maxParticles: 80, lifetime: 15000, emitRate: 80
                    }));
                }

                // Fade to black at very end
                if (t > 16000) {
                    var fadeP = Math.min((t - 16000) / 4000, 1);
                    ctx.fillStyle = 'rgba(2,4,8,' + fadeP + ')';
                    ctx.fillRect(0, 0, W, H);
                }
            },
            teardown: function() {}
        });
    }

    // =========================================================================
    // CONTROL BAR WIRING
    // =========================================================================
    function _wireControls() {
        // Play/Pause
        var btnPlay = document.getElementById('cinema-btn-play');
        if (btnPlay) {
            btnPlay.addEventListener('click', function() {
                if (Engine.paused) { resume(); } else { pause(); }
            });
        }

        // Close
        var btnClose = document.getElementById('cinema-btn-close');
        if (btnClose) {
            btnClose.addEventListener('click', function() { stop(); });
        }

        // Volume
        var volSlider = document.getElementById('cinema-volume');
        if (volSlider) {
            volSlider.addEventListener('input', function() {
                var v = parseFloat(this.value);
                try { localStorage.setItem('aegis-cinema-volume', v); } catch(e) {}
                if (Engine.audioEl) Engine.audioEl.volume = v;
            });
        }

        // Progress bar
        var progressBar = document.getElementById('cinema-progress');
        if (progressBar) {
            progressBar.addEventListener('click', function(e) {
                var rect = this.getBoundingClientRect();
                var pct = (e.clientX - rect.left) / rect.width;
                seek(pct);
            });
        }

        // Fullscreen
        var btnFS = document.getElementById('cinema-btn-fullscreen');
        if (btnFS) {
            btnFS.addEventListener('click', function() {
                var modal = document.getElementById('cinema-modal');
                if (!modal) return;
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                } else {
                    modal.requestFullscreen().catch(function() {});
                }
            });
        }

        // Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && Engine.playing) {
                stop();
            }
            if (e.key === ' ' && Engine.playing) {
                e.preventDefault();
                if (Engine.paused) resume(); else pause();
            }
        });
    }

    function _updateProgressBar() {
        var fill = document.getElementById('cinema-progress-fill');
        if (!fill) return;
        var total = _getTotalDuration();
        var pct = total > 0 ? (Engine.elapsed / total) * 100 : 0;
        fill.style.width = Math.min(pct, 100) + '%';
    }

    function _getTotalDuration() {
        var total = 0;
        for (var i = 0; i < Engine.scenes.length; i++) {
            total += Engine.scenes[i].duration || 20000;
        }
        return total;
    }

    // =========================================================================
    // PUBLIC API
    // =========================================================================
    function play() {
        if (Engine.playing) return;

        var modal = document.getElementById('cinema-modal');
        if (!modal) { console.error('[Cinema] No modal found'); return; }

        modal.style.display = 'flex';
        if (!init()) return;

        _buildScenes();
        _wireControls();
        _loadAudioManifest();

        Engine.playing = true;
        Engine.paused = false;
        Engine.sceneIndex = 0;
        Engine.startTime = 0;
        Engine.elapsed = 0;
        Engine.sceneStartTime = 0;
        Engine.sceneLocalTime = 0;
        Engine.particleSystems = [];
        Engine.camera = { x: 0, y: 0, zoom: 1, targetX: 0, targetY: 0, targetZoom: 1, speed: 0.03 };

        // Setup first scene
        var first = Engine.scenes[0];
        if (first) {
            if (first.setup) first.setup(Engine);
            if (first.narration) _playNarration(first.narration, first.id, 0);
            if (first.beats) {
                for (var i = 0; i < first.beats.length; i++) first.beats[i]._fired = false;
            }
        }

        Engine.rafId = requestAnimationFrame(_tick);
        console.log('[Cinema] Playing — ' + Engine.scenes.length + ' scenes');
    }

    function pause() {
        if (!Engine.playing || Engine.paused) return;
        Engine.paused = true;
        Engine.pausedAt = performance.now();
        if (Engine.audioEl) { try { Engine.audioEl.pause(); } catch(e){} }
        if (window.speechSynthesis) { try { window.speechSynthesis.pause(); } catch(e){} }
        var btn = document.getElementById('cinema-btn-play');
        if (btn) btn.innerHTML = '<i data-lucide="play"></i>';
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function resume() {
        if (!Engine.playing || !Engine.paused) return;
        // Adjust startTime to account for paused duration
        var pausedDuration = performance.now() - Engine.pausedAt;
        Engine.startTime += pausedDuration;
        Engine.paused = false;
        if (Engine.audioEl) { try { Engine.audioEl.play(); } catch(e){} }
        if (window.speechSynthesis) { try { window.speechSynthesis.resume(); } catch(e){} }
        var btn = document.getElementById('cinema-btn-play');
        if (btn) btn.innerHTML = '<i data-lucide="pause"></i>';
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function stop() {
        Engine.playing = false;
        Engine.paused = false;
        if (Engine.rafId) cancelAnimationFrame(Engine.rafId);
        Engine.rafId = null;

        // Cleanup audio
        if (Engine.audioEl) {
            try { Engine.audioEl.pause(); Engine.audioEl.src = ''; } catch(e){}
        }
        if (window.speechSynthesis) {
            try { window.speechSynthesis.cancel(); } catch(e){}
        }

        // Teardown current scene
        var scene = Engine.scenes[Engine.sceneIndex];
        if (scene && scene.teardown) {
            try { scene.teardown(Engine); } catch(e){}
        }

        // Clear state
        Engine.particleSystems = [];
        Engine.scenes = [];
        Engine.subtitleText = '';
        Engine.subtitleOpacity = 0;

        // Hide modal
        var modal = document.getElementById('cinema-modal');
        if (modal) modal.style.display = 'none';

        // Remove resize listener
        window.removeEventListener('resize', _resize);

        console.log('[Cinema] Stopped');
    }

    function seek(pct) {
        // Approximate seek by jumping to scene at percentage
        var total = _getTotalDuration();
        var targetTime = total * pct;
        var accumulated = 0;
        for (var i = 0; i < Engine.scenes.length; i++) {
            var dur = Engine.scenes[i].duration || 20000;
            if (accumulated + dur > targetTime) {
                // Jump to this scene
                if (Engine.sceneIndex !== i) {
                    var oldScene = Engine.scenes[Engine.sceneIndex];
                    if (oldScene && oldScene.teardown) oldScene.teardown(Engine);
                    Engine.sceneIndex = i;
                    var s = Engine.scenes[i];
                    if (s.setup) s.setup(Engine);
                    if (s.beats) s.beats.forEach(function(b) { b._fired = false; });
                }
                Engine.elapsed = targetTime;
                Engine.sceneStartTime = accumulated;
                Engine.sceneLocalTime = targetTime - accumulated;
                break;
            }
            accumulated += dur;
        }
    }

    // =========================================================================
    // RETURN PUBLIC API
    // =========================================================================
    return {
        play: play,
        pause: pause,
        resume: resume,
        stop: stop,
        seek: seek,
        // Expose for scene building (will be used in Parts 3 & 4)
        _Engine: Engine,
        _Ease: Ease,
        _drawGlowText: drawGlowText,
        _drawHUDBrackets: drawHUDBrackets,
        _drawTypewriterText: drawTypewriterText,
        _drawAEGISShield: drawAEGISShield,
        _drawAnimatedCounter: drawAnimatedCounter,
        _drawRadarSweep: drawRadarSweep,
        _drawProgressRing: drawProgressRing,
        _drawWireframeDoc: drawWireframeDoc,
        _drawConnectionLine: drawConnectionLine,
        _drawBarChart: drawBarChart,
        _DataStream: DataStream,
        _ParticleSystem: ParticleSystem
    };
})();
