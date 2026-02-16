// v3.0.97: Fix Assistant v2 - Report Client
// WP10: Client-side report generation and download

const ReportClient = (function() {
    'use strict';
    
    /**
     * Generate and download PDF report
     * @param {Object} options Configuration
     * @returns {Promise<{success: boolean, error?: string}>}
     */
    async function generateReport(options) {
        const { documentName, reviewerName, reviewData, onProgress, onError } = options;
        
        try {
            if (onProgress) onProgress('Generating report...');
            
            const response = await fetch('/api/report/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': getCSRFToken()
                },
                body: JSON.stringify({
                    document_name: documentName,
                    reviewer_name: reviewerName,
                    review_data: reviewData,
                    options: {
                        include_rejected_details: true,
                        include_flagged_details: true,
                        max_rejected_shown: 20,
                        max_flagged_shown: 20
                    }
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || 'Report generation failed');
            }
            
            if (onProgress) onProgress('Downloading...');
            
            // Download the PDF
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `TWR_Report_${documentName.replace(/\./g, '_')}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            if (onProgress) onProgress('Complete!');
            return { success: true };
            
        } catch (error) {
            console.error('[ReportClient] Error:', error);
            if (onError) onError(error.message);
            return { success: false, error: error.message };
        }
    }
    
    /**
     * Build review data from current Fix Assistant state
     * @param {Object} state - FixAssistantState reference
     * @param {number} sessionStartTime - When review started (timestamp)
     * @param {number} scoreBefore - Document score before review
     * @returns {Object} - Data formatted for report generation
     */
    function buildReviewData(state, sessionStartTime, scoreBefore) {
        const stats = state.getStatistics();
        const exportData = state.getExportData();
        const decisions = state.getAllDecisions();
        
        const durationSeconds = Math.round((Date.now() - sessionStartTime) / 1000);
        const acceptedCount = exportData.accepted.length;
        const totalFixable = stats.total - (exportData.pending?.filter(p => !p.suggestion).length || 0);
        const improvementPercent = totalFixable > 0 ? (acceptedCount / totalFixable) * 0.3 : 0;
        const scoreAfter = Math.min(100, Math.round(scoreBefore * (1 + improvementPercent)));
        
        // Build category breakdown
        const byCategory = {};
        const processCategory = (items, type) => {
            items.forEach(f => {
                const cat = f.category || 'Other';
                if (!byCategory[cat]) byCategory[cat] = { total: 0, accepted: 0, rejected: 0, flagged: 0 };
                byCategory[cat][type]++;
                byCategory[cat].total++;
            });
        };
        processCategory(exportData.accepted, 'accepted');
        processCategory(exportData.rejected, 'rejected');
        processCategory(exportData.pending.filter(f => !f.suggestion), 'flagged');
        
        // Build severity breakdown
        const bySeverity = {};
        ['Critical', 'High', 'Medium', 'Low', 'Info'].forEach(sev => {
            bySeverity[sev] = { total: 0, accepted: 0 };
        });
        exportData.accepted.forEach(f => {
            const sev = f.severity || 'Medium';
            if (bySeverity[sev]) { bySeverity[sev].accepted++; bySeverity[sev].total++; }
        });
        exportData.rejected.forEach(f => {
            const sev = f.severity || 'Medium';
            if (bySeverity[sev]) bySeverity[sev].total++;
        });
        exportData.pending.forEach(f => {
            const sev = f.severity || 'Medium';
            if (bySeverity[sev]) bySeverity[sev].total++;
        });
        
        // Collect reviewer notes
        const reviewerNotes = [];
        const generalNotesEl = document.getElementById('fav2-session-notes');
        if (generalNotesEl && generalNotesEl.value.trim()) {
            generalNotesEl.value.trim().split('\n').forEach(note => {
                if (note.trim()) reviewerNotes.push(note.trim());
            });
        }
        
        return {
            duration_seconds: durationSeconds,
            score_before: scoreBefore,
            score_after: scoreAfter,
            total_issues: stats.total,
            accepted: exportData.accepted.map(f => ({
                page: f.page, category: f.category, flagged_text: f.flagged_text,
                suggestion: f.suggestion, note: decisions.get(f.index)?.note || ''
            })),
            rejected: exportData.rejected.map(f => ({
                page: f.page, category: f.category, flagged_text: f.flagged_text,
                suggestion: f.suggestion, note: decisions.get(f.index)?.note || ''
            })),
            flagged: exportData.pending.filter(f => !f.suggestion).map(f => ({
                page: f.page, category: f.category, message: f.message
            })),
            by_category: byCategory,
            by_severity: bySeverity,
            reviewer_notes: reviewerNotes
        };
    }
    
    function getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.getAttribute('content');
        if (window.State && State.csrfToken) return State.csrfToken;
        return '';
    }
    
    return { generateReport, buildReviewData };
})();

window.ReportClient = ReportClient;
console.log('[TWR ReportClient] Module loaded v3.0.97');
