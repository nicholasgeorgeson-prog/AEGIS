/**
 * MoltenProgress v1.0
 * Scalable Rive-inspired molten orange progress bar
 *
 * Usage:
 *   const progress = MoltenProgress.create(container, options);
 *   progress.setProgress(0.5);  // 50%
 *   progress.complete();        // Mark complete
 *   progress.destroy();         // Remove
 *
 * Options:
 *   - size: 'mini' | 'small' | 'medium' | 'large' (default: 'small')
 *   - color: 'orange' | 'blue' | 'green' (default: 'orange')
 *   - withReflection: boolean (default: false)
 *   - withTrail: boolean (default: false)
 *   - indeterminate: boolean (default: false)
 *   - initialProgress: number 0-1 (default: 0)
 */
(function(global) {
  'use strict';

  const MoltenProgress = {
    /**
     * Create a new molten progress bar
     * @param {string|HTMLElement} container - CSS selector or element
     * @param {Object} options - Configuration options
     * @returns {Object} Progress controller
     */
    create: function(container, options = {}) {
      const containerEl = typeof container === 'string'
        ? document.querySelector(container)
        : container;

      if (!containerEl) {
        console.error('MoltenProgress: Container not found');
        return null;
      }

      const config = {
        size: options.size || 'small',
        color: options.color || 'orange',
        withReflection: options.withReflection || false,
        withTrail: options.withTrail || false,
        indeterminate: options.indeterminate || false,
        initialProgress: options.initialProgress || 0
      };

      // Build class list
      const classes = ['molten-progress'];

      if (config.size !== 'small') {
        classes.push(`molten-${config.size}`);
      }

      if (config.color !== 'orange') {
        classes.push(`molten-${config.color}`);
      }

      if (config.withReflection) {
        classes.push('molten-with-reflection');
      }

      if (config.withTrail) {
        classes.push('molten-with-trail');
      }

      if (config.indeterminate) {
        classes.push('molten-indeterminate');
      }

      // Create DOM structure
      const progressEl = document.createElement('div');
      progressEl.className = classes.join(' ');
      progressEl.setAttribute('role', 'progressbar');
      progressEl.setAttribute('aria-valuenow', '0');
      progressEl.setAttribute('aria-valuemin', '0');
      progressEl.setAttribute('aria-valuemax', '100');

      // Rail
      const rail = document.createElement('div');
      rail.className = 'molten-rail';
      progressEl.appendChild(rail);

      // Fill
      const fill = document.createElement('div');
      fill.className = 'molten-fill';
      progressEl.appendChild(fill);

      // Trail (if enabled)
      let trail = null;
      if (config.withTrail) {
        trail = document.createElement('div');
        trail.className = 'molten-trail';
        progressEl.appendChild(trail);
      }

      // Orb
      const orb = document.createElement('div');
      orb.className = 'molten-orb';
      progressEl.appendChild(orb);

      // Add to container
      containerEl.appendChild(progressEl);

      // Current state
      let currentProgress = 0;

      // Controller
      const controller = {
        element: progressEl,

        /**
         * Set progress value
         * @param {number} value - Progress 0-1
         * @param {boolean} animate - Whether to animate (default: true)
         */
        setProgress: function(value, animate = true) {
          if (config.indeterminate) return;

          const clamped = Math.max(0, Math.min(1, value));
          currentProgress = clamped;

          const percent = clamped * 100;

          // Update fill width
          if (!animate) {
            fill.style.transition = 'none';
          }
          fill.style.width = `${percent}%`;
          if (!animate) {
            // Force reflow then restore transition
            fill.offsetHeight;
            fill.style.transition = '';
          }

          // Update orb position
          orb.style.left = `${percent}%`;

          // Update trail position (if present)
          if (trail) {
            const trailWidth = parseFloat(getComputedStyle(trail).width) || 60;
            trail.style.left = `${Math.max(0, (percent / 100) * progressEl.clientWidth - trailWidth)}px`;
          }

          // Update ARIA
          progressEl.setAttribute('aria-valuenow', Math.round(percent));

          return this;
        },

        /**
         * Get current progress
         * @returns {number} Current progress 0-1
         */
        getProgress: function() {
          return currentProgress;
        },

        /**
         * Mark as complete
         */
        complete: function() {
          this.setProgress(1);
          progressEl.classList.add('molten-complete');
          return this;
        },

        /**
         * Reset to beginning
         */
        reset: function() {
          progressEl.classList.remove('molten-complete');
          this.setProgress(0, false);
          return this;
        },

        /**
         * Set indeterminate state
         * @param {boolean} indeterminate
         */
        setIndeterminate: function(indeterminate) {
          config.indeterminate = indeterminate;
          if (indeterminate) {
            progressEl.classList.add('molten-indeterminate');
          } else {
            progressEl.classList.remove('molten-indeterminate');
          }
          return this;
        },

        /**
         * Change color theme
         * @param {string} color - 'orange' | 'blue' | 'green'
         */
        setColor: function(color) {
          progressEl.classList.remove('molten-blue', 'molten-green');
          if (color !== 'orange') {
            progressEl.classList.add(`molten-${color}`);
          }
          config.color = color;
          return this;
        },

        /**
         * Show/hide the progress bar
         * @param {boolean} visible
         */
        setVisible: function(visible) {
          progressEl.style.display = visible ? '' : 'none';
          return this;
        },

        /**
         * Remove from DOM
         */
        destroy: function() {
          if (progressEl.parentNode) {
            progressEl.parentNode.removeChild(progressEl);
          }
        }
      };

      // Set initial progress
      if (config.initialProgress > 0) {
        controller.setProgress(config.initialProgress, false);
      }

      return controller;
    },

    /**
     * Replace an existing element with a molten progress bar
     * @param {string|HTMLElement} target - Element to replace
     * @param {Object} options - Configuration options
     * @returns {Object} Progress controller
     */
    replace: function(target, options = {}) {
      const targetEl = typeof target === 'string'
        ? document.querySelector(target)
        : target;

      if (!targetEl) {
        console.error('MoltenProgress: Target element not found');
        return null;
      }

      // Create wrapper in place
      const wrapper = document.createElement('div');
      wrapper.style.width = '100%';
      targetEl.parentNode.insertBefore(wrapper, targetEl);
      targetEl.style.display = 'none';

      const controller = this.create(wrapper, options);

      // Store reference to original
      controller.originalElement = targetEl;

      // Override destroy to restore original
      const originalDestroy = controller.destroy;
      controller.destroy = function() {
        targetEl.style.display = '';
        wrapper.parentNode.removeChild(wrapper);
      };

      return controller;
    },

    /**
     * Upgrade all progress bars matching a selector
     * @param {string} selector - CSS selector for progress bars to upgrade
     * @param {Object} options - Configuration options
     * @returns {Array} Array of controllers
     */
    upgradeAll: function(selector, options = {}) {
      const elements = document.querySelectorAll(selector);
      const controllers = [];

      elements.forEach(el => {
        // Try to get current value if it's an existing progress bar
        const currentValue = el.getAttribute('aria-valuenow');
        const opts = { ...options };

        if (currentValue) {
          opts.initialProgress = parseFloat(currentValue) / 100;
        }

        const ctrl = this.replace(el, opts);
        if (ctrl) {
          controllers.push(ctrl);
        }
      });

      return controllers;
    }
  };

  // Export
  global.MoltenProgress = MoltenProgress;

})(window);
