// v3.0.97: Fix Assistant v2 - Learning Client
// WP7: Pattern tracking and prediction client (NO AI/ML)
/**
 * LearnerClient - Frontend API integration for the Decision Learner system.
 * Tracks user decisions and retrieves predictions for fix patterns.
 * Works completely offline - no external API calls.
 */
const LearnerClient = (function() {
    'use strict';

    const API_BASE = '/api/learner';
    const VERSION = '3.0.97';

    /**
     * Get CSRF token from State or meta tag
     */
    function getCSRFToken() {
        // Try State object first (TWR standard)
        if (typeof State !== 'undefined' && State.csrfToken) {
            return State.csrfToken;
        }
        // Fallback to meta tag
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    /**
     * Make API request with error handling
     */
    async function apiRequest(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCSRFToken(),
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({ error: 'Request failed' }));
                console.error(`[LearnerClient] API error: ${error.error || response.statusText}`);
                return null;
            }

            return await response.json();
        } catch (e) {
            console.error(`[LearnerClient] Network error:`, e);
            return null;
        }
    }

    /**
     * Record a user decision for learning
     * @param {Object} fix - Fix object with flagged_text, suggestion, category
     * @param {string} decision - 'accepted' or 'rejected'
     * @param {string} note - Optional reviewer note
     * @param {string} documentId - Optional document identifier
     * @returns {Promise<boolean>} Success status
     */
    async function recordDecision(fix, decision, note = '', documentId = null) {
        const result = await apiRequest('/record', {
            method: 'POST',
            body: JSON.stringify({
                fix,
                decision,
                note,
                document_id: documentId
            })
        });
        return result?.success === true;
    }

    /**
     * Get prediction for a fix based on learned patterns
     * @param {Object} fix - Fix object with flagged_text, suggestion, category
     * @returns {Promise<Object|null>} Prediction with confidence and reason
     */
    async function getPrediction(fix) {
        return await apiRequest('/predict', {
            method: 'POST',
            body: JSON.stringify({ fix })
        });
    }

    /**
     * Get predictions for multiple fixes (batch)
     * @param {Array<Object>} fixes - Array of fix objects
     * @returns {Promise<Array<Object>>} Array of predictions
     */
    async function getPredictions(fixes) {
        const predictions = [];
        for (const fix of fixes) {
            const pred = await getPrediction(fix);
            predictions.push(pred || {
                prediction: null,
                confidence: 0,
                reason: 'Error getting prediction'
            });
        }
        return predictions;
    }

    /**
     * Get all learned patterns
     * @param {string} category - Optional category filter
     * @returns {Promise<Array>} Array of pattern objects
     */
    async function getPatterns(category = null) {
        const endpoint = category ? `/patterns?category=${encodeURIComponent(category)}` : '/patterns';
        const result = await apiRequest(endpoint, { method: 'GET' });
        return result?.patterns || [];
    }

    /**
     * Add term to custom dictionary (auto-skip)
     * @param {string} term - Term to add
     * @param {string} category - Category: 'acronym', 'proper_noun', 'technical', 'custom'
     * @param {string} notes - Optional notes
     * @returns {Promise<boolean>} Success status
     */
    async function addToDictionary(term, category = 'custom', notes = '') {
        const result = await apiRequest('/dictionary', {
            method: 'POST',
            body: JSON.stringify({ term, category, notes })
        });
        return result?.success === true;
    }

    /**
     * Remove term from custom dictionary
     * @param {string} term - Term to remove
     * @returns {Promise<boolean>} Success status
     */
    async function removeFromDictionary(term) {
        const result = await apiRequest('/dictionary', {
            method: 'DELETE',
            body: JSON.stringify({ term })
        });
        return result?.success === true;
    }

    /**
     * Get all custom dictionary terms
     * @returns {Promise<Array>} Array of dictionary entries
     */
    async function getDictionary() {
        const result = await apiRequest('/dictionary', { method: 'GET' });
        return result?.dictionary || [];
    }

    /**
     * Clear all learned patterns (keeps dictionary)
     * @returns {Promise<boolean>} Success status
     */
    async function clearPatterns() {
        const result = await apiRequest('/patterns/clear', { method: 'POST' });
        return result?.success === true;
    }

    /**
     * Get learning statistics
     * @returns {Promise<Object>} Statistics object
     */
    async function getStatistics() {
        return await apiRequest('/statistics', { method: 'GET' }) || {};
    }

    /**
     * Export all learning data for backup
     * @returns {Promise<Object>} Export data object
     */
    async function exportData() {
        return await apiRequest('/export', { method: 'GET' }) || {};
    }

    /**
     * Import learning data from backup
     * @param {Object} data - Previously exported data
     * @returns {Promise<boolean>} Success status
     */
    async function importData(data) {
        const result = await apiRequest('/import', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        return result?.success === true;
    }

    /**
     * Check if a fix has a strong prediction (for auto-apply features)
     * @param {Object} prediction - Prediction result from getPrediction
     * @param {number} threshold - Confidence threshold (default 0.8)
     * @returns {boolean} True if prediction is strong enough
     */
    function hasStrongPrediction(prediction, threshold = 0.8) {
        return prediction &&
               prediction.prediction !== null &&
               prediction.confidence >= threshold;
    }

    /**
     * Enhance fixes array with predictions
     * @param {Array<Object>} fixes - Array of fix objects
     * @returns {Promise<Array<Object>>} Fixes with prediction data added
     */
    async function enhanceWithPredictions(fixes) {
        const enhanced = [];
        for (const fix of fixes) {
            const prediction = await getPrediction(fix);
            enhanced.push({
                ...fix,
                _prediction: prediction
            });
        }
        return enhanced;
    }

    // Public API
    return {
        // Core operations
        recordDecision,
        getPrediction,
        getPredictions,
        getPatterns,

        // Dictionary management
        addToDictionary,
        removeFromDictionary,
        getDictionary,

        // Data management
        clearPatterns,
        getStatistics,
        exportData,
        importData,

        // Helpers
        hasStrongPrediction,
        enhanceWithPredictions,

        // Version info
        VERSION
    };
})();

// Export to window
window.LearnerClient = LearnerClient;

console.log(`[TWR LearnerClient] Module loaded v${LearnerClient.VERSION}`);
