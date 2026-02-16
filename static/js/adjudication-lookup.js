/**
 * AEGIS - Global Adjudication Lookup Utility
 * ============================================
 * v4.0.3: Provides tool-wide adjudication status badges for all role displays.
 *
 * This utility fetches the role dictionary once, caches it, and provides
 * helper functions for any JS file to display adjudication status.
 *
 * Usage:
 *   const cache = await AEGIS.AdjudicationLookup.ensureLoaded();
 *   const badgeHtml = AEGIS.AdjudicationLookup.getBadge('Project Manager');
 *   const stats = AEGIS.AdjudicationLookup.getStats();
 */

'use strict';

window.AEGIS = window.AEGIS || {};

AEGIS.AdjudicationLookup = (function() {
    let _cache = null;       // { normalizedName -> { is_active, source, category, is_deliverable } }
    let _loading = null;     // Promise while loading
    let _lastFetch = 0;      // Timestamp of last fetch
    const CACHE_TTL = 30000; // 30 seconds before re-fetching

    /**
     * Fetch role dictionary and build the lookup cache.
     * Returns a promise that resolves to the cache map.
     */
    async function _fetchDictionary() {
        try {
            const resp = await fetch('/api/roles/dictionary?include_inactive=true');
            const result = await resp.json();
            const map = {};

            if (result.success && result.data?.roles) {
                result.data.roles.forEach(r => {
                    const key = (r.normalized_name || r.role_name || '').toLowerCase().trim();
                    if (key) {
                        map[key] = {
                            is_active: r.is_active,
                            is_deliverable: r.is_deliverable || false,
                            source: r.source || 'manual',
                            category: r.category || ''
                        };
                    }
                });
            }

            _cache = map;
            _lastFetch = Date.now();
            return map;
        } catch (e) {
            console.warn('[AdjLookup] Could not fetch role dictionary:', e);
            _cache = _cache || {};
            return _cache;
        }
    }

    /**
     * Ensure the cache is loaded. Returns the cache map.
     * Multiple callers can await this simultaneously - only one fetch happens.
     */
    async function ensureLoaded(forceRefresh) {
        if (_cache && !forceRefresh && (Date.now() - _lastFetch) < CACHE_TTL) {
            return _cache;
        }

        if (!_loading || forceRefresh) {
            _loading = _fetchDictionary().finally(() => { _loading = null; });
        }

        return _loading;
    }

    /**
     * Synchronous check - returns data if already cached, null otherwise.
     * Use ensureLoaded() for guaranteed data.
     */
    function getCached() {
        return _cache;
    }

    /**
     * Look up a role by name. Returns { is_active, is_deliverable, source, category } or null.
     */
    function lookup(roleName) {
        if (!_cache || !roleName) return null;
        const key = (roleName || '').toLowerCase().trim();
        return _cache[key] || null;
    }

    /**
     * Get an HTML badge for a role's adjudication status.
     * Returns '' if not adjudicated, or an inline badge span.
     *
     * Options:
     *   compact: true  → shorter badge text (icon only)
     *   size: 'sm'     → smaller badge
     */
    function getBadge(roleName, options) {
        const adj = lookup(roleName);
        if (!adj) return '';

        const opts = options || {};
        const sizeClass = opts.size === 'sm' ? ' adj-badge-sm' : '';

        if (adj.is_deliverable) {
            const label = opts.compact ? '★' : '★ Deliverable';
            return `<span class="adj-badge adj-deliverable${sizeClass}" title="Adjudicated - Deliverable">` +
                   `${label}</span>`;
        } else if (adj.is_active) {
            const label = opts.compact ? '✓' : '✓ Adjudicated';
            return `<span class="adj-badge adj-confirmed${sizeClass}" title="Adjudicated - Confirmed">` +
                   `${label}</span>`;
        } else {
            const label = opts.compact ? '✗' : '✗ Rejected';
            return `<span class="adj-badge adj-rejected${sizeClass}" title="Adjudicated - Rejected">` +
                   `${label}</span>`;
        }
    }

    /**
     * Get adjudication statistics from the cache.
     * Returns { total, confirmed, rejected, deliverable }.
     */
    function getStats() {
        if (!_cache) return { total: 0, confirmed: 0, rejected: 0, deliverable: 0 };

        const entries = Object.values(_cache);
        return {
            total: entries.length,
            confirmed: entries.filter(e => e.is_active && !e.is_deliverable).length,
            rejected: entries.filter(e => !e.is_active).length,
            deliverable: entries.filter(e => e.is_deliverable).length
        };
    }

    /**
     * Count how many roles from a given list are adjudicated.
     * @param {string[]} roleNames - Array of role name strings
     * @returns {{ adjudicated: number, total: number, confirmed: number, rejected: number }}
     */
    function countAdjudicated(roleNames) {
        if (!_cache || !roleNames) return { adjudicated: 0, total: 0, confirmed: 0, rejected: 0 };

        let adjudicated = 0, confirmed = 0, rejected = 0;
        roleNames.forEach(name => {
            const adj = lookup(name);
            if (adj) {
                adjudicated++;
                if (adj.is_active) confirmed++;
                else rejected++;
            }
        });

        return { adjudicated, total: roleNames.length, confirmed, rejected };
    }

    /**
     * Invalidate the cache (call after adjudication changes).
     */
    function invalidate() {
        _cache = null;
        _lastFetch = 0;
        _loading = null;
    }

    // Public API
    return {
        ensureLoaded,
        getCached,
        lookup,
        getBadge,
        getStats,
        countAdjudicated,
        invalidate
    };
})();
