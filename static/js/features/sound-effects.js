// v3.0.97: Fix Assistant v2 - Sound Effects
// WP8: Optional audio feedback using Web Audio API (no external files)
// ═══════════════════════════════════════════════════════════════════════════════

const SoundEffects = (function() {
    'use strict';
    
    let enabled = false;
    let audioContext = null;
    
    // ═══════════════════════════════════════════════════════════════════════════
    // SOUND DEFINITIONS
    // ═══════════════════════════════════════════════════════════════════════════
    
    const sounds = {
        accept: {
            // Rising two-note chord (positive feedback)
            notes: [
                { freq: 523.25, start: 0, duration: 0.08 },      // C5
                { freq: 659.25, start: 0.05, duration: 0.1 }     // E5
            ],
            type: 'sine',
            volume: 0.1
        },
        reject: {
            // Falling note (negative but not harsh)
            notes: [
                { freq: 392, start: 0, duration: 0.15 }          // G4
            ],
            type: 'sine',
            volume: 0.1
        },
        skip: {
            // Quick neutral blip
            notes: [
                { freq: 440, start: 0, duration: 0.05 }          // A4
            ],
            type: 'sine',
            volume: 0.08
        },
        undo: {
            // Descending sweep
            notes: [
                { freq: 600, start: 0, duration: 0.1, endFreq: 400 }
            ],
            type: 'sine',
            volume: 0.1
        },
        complete: {
            // Celebratory chord
            notes: [
                { freq: 523.25, start: 0, duration: 0.15 },      // C5
                { freq: 659.25, start: 0.05, duration: 0.15 },   // E5
                { freq: 783.99, start: 0.1, duration: 0.2 }      // G5
            ],
            type: 'sine',
            volume: 0.12
        },
        navigate: {
            // Very subtle tick
            notes: [
                { freq: 800, start: 0, duration: 0.02 }
            ],
            type: 'sine',
            volume: 0.05
        }
    };
    
    // ═══════════════════════════════════════════════════════════════════════════
    // PUBLIC API
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Initialize sound system, load user preference
     * @returns {boolean} Current enabled state
     */
    function init() {
        const saved = localStorage.getItem('twr_sounds_enabled');
        enabled = saved === 'true';
        return enabled;
    }
    
    /**
     * Enable or disable sounds
     * @param {boolean} value - true to enable, false to disable
     */
    function setEnabled(value) {
        enabled = !!value;
        localStorage.setItem('twr_sounds_enabled', enabled.toString());
        
        // Play test sound when enabling
        if (enabled) {
            play('navigate');
        }
    }
    
    /**
     * Check if sounds are enabled
     * @returns {boolean}
     */
    function isEnabled() {
        return enabled;
    }
    
    /**
     * Play a sound effect
     * @param {string} name - 'accept' | 'reject' | 'skip' | 'undo' | 'complete' | 'navigate'
     */
    function play(name) {
        if (!enabled) return;
        
        const sound = sounds[name];
        if (!sound) {
            console.warn('[SoundEffects] Unknown sound:', name);
            return;
        }
        
        try {
            // Create audio context on first use (browser requirement)
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            // Resume if suspended (browser autoplay policy)
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
            
            playSound(sound);
            
        } catch (e) {
            console.warn('[SoundEffects] Audio error:', e);
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // PRIVATE METHODS
    // ═══════════════════════════════════════════════════════════════════════════
    
    /**
     * Generate and play sound using Web Audio API
     */
    function playSound(sound) {
        const now = audioContext.currentTime;
        
        sound.notes.forEach(note => {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.type = sound.type || 'sine';
            oscillator.frequency.setValueAtTime(note.freq, now + note.start);
            
            // Frequency sweep if specified
            if (note.endFreq) {
                oscillator.frequency.linearRampToValueAtTime(
                    note.endFreq, 
                    now + note.start + note.duration
                );
            }
            
            // Volume envelope: quick attack, exponential decay
            gainNode.gain.setValueAtTime(0, now + note.start);
            gainNode.gain.linearRampToValueAtTime(sound.volume, now + note.start + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.001, now + note.start + note.duration);
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.start(now + note.start);
            oscillator.stop(now + note.start + note.duration + 0.1);
        });
    }
    
    // ═══════════════════════════════════════════════════════════════════════════
    // EXPORTS
    // ═══════════════════════════════════════════════════════════════════════════
    
    return {
        init,
        setEnabled,
        isEnabled,
        play
    };
})();

// Register global
window.SoundEffects = SoundEffects;
console.log('[TWR SoundEffects] Module loaded v3.0.97');
