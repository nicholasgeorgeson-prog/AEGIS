/**
 * AEGIS Run State Fixes
 * =================================
 * Patches review functions to properly update the run-state indicator
 * 
 * Version: 3.0.53
 * 
 * Problem: setRunState() function exists but is never called during review.
 * The indicator stays "Idle" even when processing documents.
 * 
 * Solution: Wrap runReview, processReviewResults, and error paths to call setRunState()
 */

(function() {
    'use strict';
    
    console.log('[TWR] Loading run-state-fixes v3.0.53...');
    
    // Wait for app to be ready
    let initAttempts = 0;
    const maxAttempts = 50; // 5 seconds max wait
    
    function initRunStateFixes() {
        initAttempts++;
        
        // Check if required functions exist
        if (typeof window.runReview !== 'function' || typeof window.setRunState !== 'function') {
            if (initAttempts < maxAttempts) {
                setTimeout(initRunStateFixes, 100);
                return;
            }
            console.error('[TWR] Run state fixes: Required functions not found after timeout');
            return;
        }
        
        console.log('[TWR] Patching review functions for run state updates...');
        
        // Store original functions
        const originalRunReview = window.runReview;
        const originalApi = window.api;
        
        // Track current state for auto-reset
        let resetTimer = null;
        
        /**
         * Schedule reset to idle after completion/error
         */
        function scheduleIdleReset(delay = 5000) {
            if (resetTimer) {
                clearTimeout(resetTimer);
            }
            resetTimer = setTimeout(() => {
                if (typeof window.setRunState === 'function') {
                    window.setRunState('idle');
                    console.log('[TWR] Run state reset to idle');
                }
                resetTimer = null;
            }, delay);
        }
        
        /**
         * Cancel any pending idle reset (e.g., if new review starts)
         */
        function cancelIdleReset() {
            if (resetTimer) {
                clearTimeout(resetTimer);
                resetTimer = null;
            }
        }
        
        /**
         * Wrapped runReview that updates run state
         */
        window.runReview = async function() {
            console.log('[TWR] runReview called - setting extracting state');
            
            // Cancel any pending reset from previous run
            cancelIdleReset();
            
            // Set extracting state immediately
            if (typeof window.setRunState === 'function') {
                window.setRunState('extracting', 'Extracting...');
            }
            
            try {
                // Call original runReview
                const result = await originalRunReview.apply(this, arguments);
                return result;
            } catch (error) {
                console.error('[TWR] runReview error:', error);
                if (typeof window.setRunState === 'function') {
                    window.setRunState('error', 'Error');
                }
                scheduleIdleReset(8000); // Longer delay on error so user sees it
                throw error;
            }
        };
        
        /**
         * Intercept API calls to track review progress phases
         */
        window.api = async function(endpoint, method, data) {
            // Track phase transitions based on API calls
            if (endpoint === '/review' && method === 'POST') {
                // Sync review - set checking state
                if (typeof window.setRunState === 'function') {
                    window.setRunState('checking', 'Analyzing...');
                }
            } else if (endpoint === '/review/start' && method === 'POST') {
                // Async job started
                if (typeof window.setRunState === 'function') {
                    window.setRunState('extracting', 'Starting...');
                }
            }
            
            // Call original API
            const result = await originalApi.apply(this, arguments);
            
            // Handle responses
            if (endpoint === '/review' && method === 'POST') {
                if (result && result.success) {
                    // Review complete
                    if (typeof window.setRunState === 'function') {
                        window.setRunState('complete', 'Complete');
                    }
                    scheduleIdleReset(5000);
                } else if (result && !result.success) {
                    // Review failed
                    if (typeof window.setRunState === 'function') {
                        window.setRunState('error', 'Failed');
                    }
                    scheduleIdleReset(8000);
                }
            } else if (endpoint.startsWith('/job/') && method === 'GET' && !endpoint.includes('/cancel')) {
                // Job polling - update state based on phase
                if (result && result.success && result.job) {
                    const phase = result.job.progress?.phase;
                    const status = result.job.status;
                    
                    if (status === 'complete') {
                        if (typeof window.setRunState === 'function') {
                            window.setRunState('complete', 'Complete');
                        }
                        scheduleIdleReset(5000);
                    } else if (status === 'failed') {
                        if (typeof window.setRunState === 'function') {
                            window.setRunState('error', 'Failed');
                        }
                        scheduleIdleReset(8000);
                    } else if (status === 'cancelled') {
                        if (typeof window.setRunState === 'function') {
                            window.setRunState('idle', 'Cancelled');
                        }
                        scheduleIdleReset(3000);
                    } else if (phase) {
                        // Update based on phase
                        const phaseStates = {
                            'queued': ['extracting', 'Queued...'],
                            'uploading': ['extracting', 'Uploading...'],
                            'extracting': ['extracting', 'Extracting...'],
                            'parsing': ['extracting', 'Parsing...'],
                            'checking': ['checking', 'Checking...'],
                            'postprocessing': ['checking', 'Processing...'],
                            'exporting': ['checking', 'Exporting...']
                        };
                        
                        const stateInfo = phaseStates[phase];
                        if (stateInfo && typeof window.setRunState === 'function') {
                            // Add progress percentage if available
                            const progress = result.job.progress?.overall_progress;
                            let label = stateInfo[1];
                            if (progress !== undefined && progress > 0) {
                                label = `${stateInfo[1].replace('...', '')} ${Math.round(progress)}%`;
                            }
                            window.setRunState(stateInfo[0], label);
                        }
                    }
                }
            } else if (endpoint.startsWith('/review/result/') && method === 'GET') {
                // Final results fetched for async job
                if (result && result.success) {
                    if (typeof window.setRunState === 'function') {
                        window.setRunState('complete', 'Complete');
                    }
                    scheduleIdleReset(5000);
                }
            }
            
            return result;
        };
        
        // Copy over any properties from original api function
        if (originalApi.baseUrl) window.api.baseUrl = originalApi.baseUrl;
        
        /**
         * Also handle upload state
         */
        const originalUploadFile = window.uploadFile;
        if (typeof originalUploadFile === 'function') {
            window.uploadFile = async function() {
                cancelIdleReset();
                
                if (typeof window.setRunState === 'function') {
                    window.setRunState('extracting', 'Uploading...');
                }
                
                try {
                    const result = await originalUploadFile.apply(this, arguments);
                    
                    // If upload succeeds but no review follows, reset to idle
                    if (typeof window.setRunState === 'function') {
                        window.setRunState('idle', 'Ready');
                    }
                    
                    return result;
                } catch (error) {
                    if (typeof window.setRunState === 'function') {
                        window.setRunState('error', 'Upload Failed');
                    }
                    scheduleIdleReset(5000);
                    throw error;
                }
            };
        }
        
        console.log('[TWR] Run state fixes applied successfully');
    }
    
    // Start initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(initRunStateFixes, 200);
        });
    } else {
        setTimeout(initRunStateFixes, 200);
    }
    
})();

console.log('[TWR] Run state fixes module loaded v3.0.53');
