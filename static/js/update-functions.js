/**
 * AEGIS Update Functions - Fixed Version
 * ==================================================
 * These functions replace the broken update functions in app.js
 * They use the correct element IDs from index.html
 * 
 * Version: 3.0.52
 */

// Override the broken checkForUpdates function
window.checkForUpdates = async function() {
    console.log('[TWR] checkForUpdates called');
    
    // Get the UI elements from index.html
    const checkingDiv = document.getElementById('update-checking');
    const noUpdatesDiv = document.getElementById('no-updates');
    const updatesAvailableDiv = document.getElementById('updates-available');
    const updateCountSpan = document.getElementById('update-count');
    const updateListDiv = document.getElementById('update-list');
    
    // Also support the legacy update-status div if it exists
    const legacyStatusDiv = document.getElementById('update-status');
    
    // Show checking state
    if (checkingDiv) checkingDiv.style.display = 'flex';
    if (noUpdatesDiv) noUpdatesDiv.style.display = 'none';
    if (updatesAvailableDiv) updatesAvailableDiv.style.display = 'none';
    
    if (legacyStatusDiv) {
        legacyStatusDiv.innerHTML = '<p><i data-lucide="loader" class="spin"></i> Checking for updates...</p>';
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
    
    try {
        console.log('[TWR] Calling /api/updates/check...');
        const result = await api('/updates/check', 'GET');
        console.log('[TWR] Update check result:', result);
        
        // Hide checking state
        if (checkingDiv) checkingDiv.style.display = 'none';
        
        if (result && result.success) {
            const data = result.data || {};
            console.log('[TWR] Update data:', data);
            
            if (data.has_updates && data.updates && data.updates.length > 0) {
                // Updates available
                console.log('[TWR] Updates found:', data.updates.length);
                
                if (noUpdatesDiv) noUpdatesDiv.style.display = 'none';
                if (updatesAvailableDiv) updatesAvailableDiv.style.display = 'block';
                if (updateCountSpan) updateCountSpan.textContent = data.count || data.updates.length;
                
                // Populate update list
                if (updateListDiv) {
                    updateListDiv.innerHTML = data.updates.map(u => `
                        <div class="update-item" style="display: flex; justify-content: space-between; align-items: center; padding: 8px; background: var(--bg-surface); border-radius: var(--radius-md); margin-bottom: 4px;">
                            <div>
                                <strong style="font-size: 13px;">${u.dest_name || u.source_name}</strong>
                                <span class="help-text" style="margin-left: 8px;">${u.category || 'app'}</span>
                                ${u.is_new ? '<span class="badge badge-info" style="margin-left: 8px; font-size: 10px;">NEW</span>' : ''}
                            </div>
                            <span class="help-text">${formatBytes(u.size || 0)}</span>
                        </div>
                    `).join('');
                }
                
                // Legacy support
                if (legacyStatusDiv) {
                    legacyStatusDiv.innerHTML = `
                        <div class="update-available" style="padding: 12px; background: var(--success-emphasis); border-radius: 8px; color: white;">
                            <strong>${data.count || data.updates.length} update(s) available</strong>
                            <button class="btn btn-sm" onclick="applyUpdates()" style="margin-left: 12px;">Apply Updates</button>
                        </div>
                    `;
                }
                
                if (typeof toast === 'function') {
                    toast('info', `${data.count || data.updates.length} update(s) found!`);
                }
            } else {
                // No updates
                console.log('[TWR] No updates found');
                
                if (noUpdatesDiv) {
                    noUpdatesDiv.style.display = 'flex';
                    // Update the text to show last checked time
                    const pEl = noUpdatesDiv.querySelector('p:first-of-type');
                    if (pEl) pEl.textContent = 'No updates available';
                }
                if (updatesAvailableDiv) updatesAvailableDiv.style.display = 'none';
                
                // Legacy support
                if (legacyStatusDiv) {
                    legacyStatusDiv.innerHTML = `
                        <div style="display: flex; align-items: center; gap: 8px; color: var(--success);">
                            <i data-lucide="check-circle"></i>
                            <span>No updates available. Last checked: ${new Date().toLocaleString()}</span>
                        </div>
                    `;
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                }
            }
        } else {
            // API call failed
            console.warn('[TWR] Update check failed:', result);
            
            if (noUpdatesDiv) {
                noUpdatesDiv.style.display = 'flex';
                const pEl = noUpdatesDiv.querySelector('p:first-of-type');
                if (pEl) pEl.textContent = 'Could not check for updates';
            }
            
            if (legacyStatusDiv) {
                legacyStatusDiv.innerHTML = '<p style="color: var(--warning);">Could not check for updates. Server may not support this feature.</p>';
            }
            
            if (typeof toast === 'function') {
                toast('warning', result?.error || 'Could not check for updates');
            }
        }
    } catch (e) {
        console.error('[TWR] Update check error:', e);
        
        if (checkingDiv) checkingDiv.style.display = 'none';
        if (noUpdatesDiv) {
            noUpdatesDiv.style.display = 'flex';
            const pEl = noUpdatesDiv.querySelector('p:first-of-type');
            if (pEl) pEl.textContent = 'Error checking for updates';
        }
        
        if (legacyStatusDiv) {
            legacyStatusDiv.innerHTML = '<p style="color: var(--warning);">Could not check for updates.</p>';
        }
        
        if (typeof toast === 'function') {
            toast('error', 'Error checking for updates: ' + e.message);
        }
    }
};

// Override the broken applyUpdates function
window.applyUpdates = async function() {
    console.log('[TWR] applyUpdates called');
    
    if (!confirm('Apply all available updates? The server will restart automatically.')) {
        return;
    }
    
    const checkingDiv = document.getElementById('update-checking');
    const noUpdatesDiv = document.getElementById('no-updates');
    const updatesAvailableDiv = document.getElementById('updates-available');
    const resultDiv = document.getElementById('update-result');
    const legacyStatusDiv = document.getElementById('update-status');
    
    // Get backup preference
    const backupCheckbox = document.getElementById('update-create-backup');
    const createBackup = backupCheckbox ? backupCheckbox.checked : true;
    
    // Show applying state
    if (checkingDiv) {
        checkingDiv.style.display = 'flex';
        const span = checkingDiv.querySelector('span');
        if (span) span.textContent = 'Applying updates...';
    }
    if (updatesAvailableDiv) updatesAvailableDiv.style.display = 'none';
    
    if (legacyStatusDiv) {
        legacyStatusDiv.innerHTML = `
            <div style="padding: 16px; background: var(--bg-secondary); border-radius: 8px;">
                <p><i data-lucide="loader" class="spin"></i> Applying updates...</p>
            </div>
        `;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
    
    try {
        console.log('[TWR] Calling /api/updates/apply...');
        const result = await api('/updates/apply', 'POST', { create_backup: createBackup });
        console.log('[TWR] Apply result:', result);
        
        if (checkingDiv) checkingDiv.style.display = 'none';
        
        if (result && result.success) {
            // Show success and prepare for restart
            if (resultDiv) {
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = `
                    <div style="text-align: center; padding: 20px;">
                        <i data-lucide="check-circle" style="width: 48px; height: 48px; color: var(--success);"></i>
                        <p style="margin-top: 12px; font-weight: 600;">Updates applied successfully!</p>
                        <p class="help-text">Server is restarting... Page will refresh automatically.</p>
                        <div class="spinner-small" style="margin-top: 12px;"></div>
                    </div>
                `;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
            
            if (legacyStatusDiv) {
                legacyStatusDiv.innerHTML = `
                    <div style="padding: 16px; background: var(--success-emphasis); border-radius: 8px; color: white; text-align: center;">
                        <p><strong>Updates applied successfully!</strong></p>
                        <p>Server is restarting... Please wait.</p>
                    </div>
                `;
            }
            
            if (typeof toast === 'function') {
                toast('success', 'Updates applied! Restarting server...');
            }
            
            // Trigger restart and poll for server
            console.log('[TWR] Triggering server restart...');
            try {
                await api('/updates/restart', 'POST');
            } catch (e) {
                // Expected - server is restarting
                console.log('[TWR] Restart triggered (connection lost is expected)');
            }
            
            // Poll for server to come back
            setTimeout(() => pollServerRestart(), 2000);
            
        } else {
            // Apply failed
            console.error('[TWR] Apply failed:', result);
            
            if (resultDiv) {
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = `
                    <div style="text-align: center; padding: 20px; color: var(--danger);">
                        <i data-lucide="x-circle" style="width: 48px; height: 48px;"></i>
                        <p style="margin-top: 12px; font-weight: 600;">Update failed</p>
                        <p class="help-text">${result?.error || 'Unknown error'}</p>
                    </div>
                `;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
            
            if (legacyStatusDiv) {
                legacyStatusDiv.innerHTML = `<p style="color: var(--danger);">Update failed: ${result?.error || 'Unknown error'}</p>`;
            }
            
            if (typeof toast === 'function') {
                toast('error', result?.error || 'Failed to apply updates');
            }
        }
    } catch (e) {
        console.error('[TWR] Apply error:', e);
        
        if (checkingDiv) checkingDiv.style.display = 'none';
        
        if (resultDiv) {
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = `
                <div style="text-align: center; padding: 20px; color: var(--danger);">
                    <i data-lucide="x-circle" style="width: 48px; height: 48px;"></i>
                    <p style="margin-top: 12px; font-weight: 600;">Update error</p>
                    <p class="help-text">${e.message}</p>
                </div>
            `;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
        
        if (typeof toast === 'function') {
            toast('error', 'Error applying updates: ' + e.message);
        }
    }
};

// Poll for server restart
async function pollServerRestart(attempts = 0, maxAttempts = 30) {
    console.log('[TWR] Polling for server restart, attempt', attempts + 1);
    
    if (attempts >= maxAttempts) {
        console.error('[TWR] Server did not restart in time');
        if (typeof toast === 'function') {
            toast('warning', 'Server is taking longer than expected. Please refresh manually.');
        }
        return;
    }
    
    try {
        const response = await fetch('/api/updates/health', { 
            method: 'GET',
            cache: 'no-store'
        });
        
        if (response.ok) {
            console.log('[TWR] Server is back! Reloading...');
            if (typeof toast === 'function') {
                toast('success', 'Server restarted! Refreshing...');
            }
            setTimeout(() => window.location.reload(), 500);
            return;
        }
    } catch (e) {
        // Server not ready yet
    }
    
    // Try again
    setTimeout(() => pollServerRestart(attempts + 1, maxAttempts), 1000);
}

// Helper function for formatting bytes
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Show rollback confirmation
window.showRollbackConfirm = async function() {
    console.log('[TWR] showRollbackConfirm called');
    
    // First load available backups
    try {
        const result = await api('/updates/backups', 'GET');
        if (!result || !result.success || !result.data || result.data.length === 0) {
            if (typeof toast === 'function') {
                toast('warning', 'No backups available to rollback to');
            }
            return;
        }
        
        const backups = result.data;
        const latestBackup = backups[0]; // Assume sorted by date, newest first
        
        if (!confirm(`Rollback to backup: ${latestBackup.name}?\n\nThis will restore files from ${latestBackup.created_at || 'the latest backup'}.\n\nThe server will restart after rollback.`)) {
            return;
        }
        
        // Perform rollback
        const rollbackResult = await api('/updates/rollback', 'POST', { 
            backup_name: latestBackup.name 
        });
        
        if (rollbackResult && rollbackResult.success) {
            if (typeof toast === 'function') {
                toast('success', 'Rollback successful! Restarting server...');
            }
            
            // Trigger restart
            try {
                await api('/updates/restart', 'POST');
            } catch (e) {
                // Expected - server is restarting
            }
            
            // Poll for server restart
            setTimeout(() => pollServerRestart(), 2000);
        } else {
            if (typeof toast === 'function') {
                toast('error', rollbackResult?.error || 'Rollback failed');
            }
        }
    } catch (e) {
        console.error('[TWR] Rollback error:', e);
        if (typeof toast === 'function') {
            toast('error', 'Error during rollback: ' + e.message);
        }
    }
};

console.log('[TWR] Update functions loaded (fixed version)');
