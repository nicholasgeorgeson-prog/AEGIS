/**
 * AEGIS Statement Review Lookup Utility
 * ======================================
 * Global utility for statement review status badges and statistics.
 * Mirrors the AEGIS.AdjudicationLookup pattern.
 *
 * @version 4.6.0
 * @module AEGIS.StatementReviewLookup
 */

window.AEGIS = window.AEGIS || {};

AEGIS.StatementReviewLookup = (function() {
    'use strict';

    let _cache = null;
    let _loading = null;
    let _lastFetch = 0;
    const CACHE_TTL = 15000; // 15 seconds

    /**
     * Fetch review stats from API.
     * @param {number} [documentId] - Optional document filter
     * @returns {Promise<Object>}
     */
    async function _fetchStats(documentId) {
        const url = documentId
            ? `/api/scan-history/statements/review-stats?document_id=${documentId}`
            : '/api/scan-history/statements/review-stats';
        try {
            const resp = await fetch(url);
            const data = await resp.json();
            if (data.success) {
                _cache = data.data;
                _lastFetch = Date.now();
            }
        } catch (e) {
            console.warn('[AEGIS StatementReview] Failed to fetch stats:', e);
        }
        return _cache || { total: 0, pending: 0, reviewed: 0, rejected: 0, confirmed: 0 };
    }

    /**
     * Ensure stats are loaded (with TTL cache).
     * @param {boolean} [force] - Force refresh
     * @returns {Promise<Object>}
     */
    async function ensureLoaded(force) {
        if (_cache && !force && (Date.now() - _lastFetch) < CACHE_TTL) {
            return _cache;
        }
        if (!_loading || force) {
            _loading = _fetchStats().finally(() => { _loading = null; });
        }
        return _loading;
    }

    /**
     * Get cached stats synchronously (may be null if not loaded).
     * @returns {Object|null}
     */
    function getStats() {
        return _cache;
    }

    /**
     * Generate HTML badge for a review status.
     * @param {string} reviewStatus - 'pending'|'reviewed'|'rejected'|'unchanged'
     * @param {Object} [options] - { size: 'sm', compact: false }
     * @returns {string} HTML string
     */
    function getBadge(reviewStatus, options) {
        const opts = options || {};
        const size = opts.size === 'sm' ? ' stmt-badge-sm' : '';
        const compact = opts.compact || false;

        switch (reviewStatus) {
            case 'reviewed':
                return `<span class="stmt-badge stmt-reviewed${size}" title="Reviewed">${compact ? '&#10003;' : '&#10003; Reviewed'}</span>`;
            case 'rejected':
                return `<span class="stmt-badge stmt-rejected${size}" title="Rejected">${compact ? '&#10007;' : '&#10007; Rejected'}</span>`;
            case 'confirmed':
                return `<span class="stmt-badge stmt-confirmed${size}" title="Confirmed">${compact ? '&#9733;' : '&#9733; Confirmed'}</span>`;
            case 'unchanged':
                return `<span class="stmt-badge stmt-unchanged${size}" title="Unchanged">${compact ? '&#8213;' : '&#8213; Unchanged'}</span>`;
            default:
                return `<span class="stmt-badge stmt-pending${size}" title="Pending Review">${compact ? '&#9711;' : '&#9711; Pending'}</span>`;
        }
    }

    /**
     * Generate a summary subtitle string (e.g., "12 reviewed · 3 pending").
     * @param {Object} stats - { total, reviewed, pending, rejected, confirmed }
     * @returns {string} HTML string
     */
    function getSummary(stats) {
        if (!stats || !stats.total) return '';
        const parts = [];
        if (stats.reviewed > 0) parts.push(`<span class="stmt-stat-reviewed">${stats.reviewed} reviewed</span>`);
        if (stats.confirmed > 0) parts.push(`<span class="stmt-stat-confirmed">${stats.confirmed} confirmed</span>`);
        if (stats.pending > 0) parts.push(`<span class="stmt-stat-pending">${stats.pending} pending</span>`);
        if (stats.rejected > 0) parts.push(`<span class="stmt-stat-rejected">${stats.rejected} rejected</span>`);
        return parts.join(' &middot; ');
    }

    /**
     * Invalidate cache (call after review status changes).
     */
    function invalidate() {
        _cache = null;
        _lastFetch = 0;
    }

    return {
        ensureLoaded,
        getStats,
        getBadge,
        getSummary,
        invalidate
    };
})();
