/**
 * AEGIS Demo Simulator v1.0.0
 * ============================
 * Provides mock data injection for Live Demo playback.
 * Injects temporary DOM elements that simulate scan results, progress bars,
 * loading states, and output previews during demo walkthroughs.
 * All injected elements are cleaned up when the demo stops.
 *
 * Used by guide-system.js during demo playback.
 */

'use strict';

const DemoSimulator = (function() {
    const DEMO_CLASS = 'aegis-demo-simulated';
    let _cleanupFns = [];

    // ─── Utility ───────────────────────────────────────────────────────
    function _addCleanup(fn) {
        _cleanupFns.push(fn);
    }

    function cleanupAll() {
        _cleanupFns.forEach(fn => { try { fn(); } catch(e) {} });
        _cleanupFns = [];
        // Remove all simulated elements
        document.querySelectorAll('.' + DEMO_CLASS).forEach(el => el.remove());
    }

    function _wait(ms) {
        return new Promise(r => setTimeout(r, ms));
    }

    // ─── Progress Dashboard Simulation ─────────────────────────────────
    function showProgressDashboard() {
        const overlay = document.getElementById('spd-overlay');
        if (!overlay) return;

        // Show the overlay
        overlay.style.display = 'flex';
        overlay.style.zIndex = '148000';
        overlay.classList.add(DEMO_CLASS);

        // Set filename
        const fnEl = document.getElementById('spd-filename');
        if (fnEl) fnEl.textContent = 'NASA_SE_Handbook_Rev2.docx';

        // Set overall progress to ~65%
        const fill = document.getElementById('spd-overall-fill');
        const pct = document.getElementById('spd-overall-pct');
        if (fill) fill.style.width = '65%';
        if (pct) pct.textContent = '65%';

        // Simulate step cards
        const stepsContainer = document.getElementById('spd-steps');
        if (stepsContainer) {
            stepsContainer.innerHTML = '';
            const steps = [
                { name: 'Upload Document', detail: 'Validated (247 KB)', status: 'done', time: '0.3s' },
                { name: 'Extract Content', detail: 'mammoth → 14,230 words', status: 'done', time: '1.8s' },
                { name: 'Parse Structure', detail: '127 paragraphs, 12 tables, 8 headings', status: 'done', time: '0.5s' },
                { name: 'Run Quality Checks', detail: 'Passive Voice (67/98) — 34 issues found', status: 'active', time: '4.2s' },
                { name: 'NLP Analysis', detail: 'Pending...', status: 'pending', time: '--' },
                { name: 'Extract Roles', detail: 'Pending...', status: 'pending', time: '--' },
                { name: 'Finalize Results', detail: 'Pending...', status: 'pending', time: '--' }
            ];
            steps.forEach(s => {
                const card = document.createElement('div');
                card.className = `spd-step ${s.status === 'done' ? 'spd-step-done' : s.status === 'active' ? 'spd-step-active' : ''}`;
                card.innerHTML = `
                    <div class="spd-step-icon">
                        ${s.status === 'done' ? '<i data-lucide="check-circle"></i>' :
                          s.status === 'active' ? '<i data-lucide="loader" class="spin"></i>' :
                          '<i data-lucide="circle"></i>'}
                    </div>
                    <div class="spd-step-info">
                        <div class="spd-step-name">${s.name}</div>
                        <div class="spd-step-detail">${s.detail}</div>
                    </div>
                    <div class="spd-step-time">${s.time}</div>
                `;
                stepsContainer.appendChild(card);
            });
            if (typeof lucide !== 'undefined' && lucide.createIcons) lucide.createIcons();
        }

        // ETA
        const eta = document.getElementById('spd-eta-value');
        if (eta) eta.textContent = '~8 seconds remaining';

        _addCleanup(() => {
            overlay.style.display = '';
            overlay.style.zIndex = '';
            overlay.classList.remove(DEMO_CLASS);
            if (stepsContainer) stepsContainer.innerHTML = '';
            if (fnEl) fnEl.textContent = '';
            if (fill) fill.style.width = '0%';
            if (pct) pct.textContent = '0%';
            if (eta) eta.textContent = '';
        });
    }

    function hideProgressDashboard() {
        const overlay = document.getElementById('spd-overlay');
        if (overlay) {
            overlay.style.display = '';
            overlay.style.zIndex = '';
        }
    }

    // ─── Results / Stats Bar Simulation ────────────────────────────────
    function showSimulatedResults() {
        // Populate the stats bar with mock data
        const statMap = {
            'stat-words': '14,230',
            'stat-paragraphs': '127',
            'stat-tables': '12',
            'stat-headings': '8',
            'stat-issues': '47',
            'stat-score': '78',
            'stat-grade': 'B+',
            'stat-flesch': '42',
            'stat-fk-grade': '12.3',
            'stat-fog': '14.1'
        };

        const originals = {};
        Object.entries(statMap).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) {
                originals[id] = el.textContent;
                el.textContent = val;
            }
        });

        // Show the stats bar
        const statsBar = document.getElementById('stats-bar');
        if (statsBar) {
            statsBar.style.display = '';
            statsBar.classList.add(DEMO_CLASS);
        }

        // Set grade color
        const gradeEl = document.getElementById('stat-grade');
        if (gradeEl) {
            gradeEl.className = 'grade-b';
        }

        // Animate score ring
        const ring = document.getElementById('score-ring');
        if (ring) {
            const circumference = 2 * Math.PI * 38;
            const offset = circumference - (78 / 100) * circumference;
            ring.style.strokeDasharray = `${circumference}`;
            ring.style.strokeDashoffset = `${offset}`;
        }

        // Animate gauge arcs
        _animateGauge('stat-flesch-arc', 42, 100);
        _animateGauge('stat-fk-arc', 12.3, 20);
        _animateGauge('stat-fog-arc', 14.1, 20);

        // Populate issues container with mock data
        _populateMockIssues();

        _addCleanup(() => {
            Object.entries(originals).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            });
            if (gradeEl) gradeEl.className = '';
            if (ring) {
                ring.style.strokeDasharray = '';
                ring.style.strokeDashoffset = '';
            }
            _clearMockIssues();
        });
    }

    function _animateGauge(arcId, value, max) {
        const arc = document.getElementById(arcId);
        if (!arc) return;
        const pct = Math.min(value / max, 1);
        const totalLength = 100; // approximate path length
        arc.style.strokeDasharray = `${pct * totalLength} ${totalLength}`;
    }

    function _populateMockIssues() {
        const container = document.getElementById('issues-container');
        if (!container) return;

        const mockIssues = [
            { severity: 'Critical', category: 'Requirements Language', desc: '"TBD" placeholder found — requirement incomplete', para: 12 },
            { severity: 'High', category: 'Passive Voice', desc: '"The system shall be designed by the contractor" — consider active voice', para: 15 },
            { severity: 'High', category: 'Undefined Acronyms', desc: '"FMEA" used without prior definition', para: 23 },
            { severity: 'Medium', category: 'Weak Language', desc: '"should" used instead of "shall" in a binding requirement', para: 31 },
            { severity: 'Medium', category: 'Escape Clause', desc: '"as appropriate" weakens requirement — specify criteria', para: 42 },
            { severity: 'Low', category: 'Spelling', desc: '"accomodate" should be "accommodate"', para: 56 },
            { severity: 'Info', category: 'Readability', desc: 'Sentence exceeds 40 words — consider splitting', para: 67 },
            { severity: 'Critical', category: 'Cross-Reference', desc: 'Reference to "Section 4.3.2" not found in document', para: 71 },
            { severity: 'High', category: 'Testability', desc: '"adequate" is not measurable — specify acceptance criteria', para: 84 },
            { severity: 'Medium', category: 'Grammar', desc: 'Subject-verb disagreement: "The systems requires" → "The systems require"', para: 95 }
        ];

        const sevColors = {
            'Critical': '#ef4444', 'High': '#f97316', 'Medium': '#eab308',
            'Low': '#3b82f6', 'Info': '#6b7280'
        };

        // Create a demo table
        const demoTable = document.createElement('div');
        demoTable.className = DEMO_CLASS + ' demo-issues-table';
        demoTable.style.cssText = 'width:100%;';

        const table = document.createElement('table');
        table.className = 'issues-table';
        table.style.cssText = 'width:100%; border-collapse:collapse; font-size:13px;';
        table.innerHTML = `
            <thead>
                <tr style="background:var(--bg-surface, #f9fafb); border-bottom:2px solid var(--border-color, #e5e7eb);">
                    <th style="padding:8px 12px; text-align:left; width:90px;">Severity</th>
                    <th style="padding:8px 12px; text-align:left; width:160px;">Category</th>
                    <th style="padding:8px 12px; text-align:left;">Description</th>
                    <th style="padding:8px 12px; text-align:center; width:60px;">Para</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;

        const tbody = table.querySelector('tbody');
        mockIssues.forEach(issue => {
            const tr = document.createElement('tr');
            tr.style.cssText = 'border-bottom:1px solid var(--border-color, #e5e7eb);';
            tr.innerHTML = `
                <td style="padding:8px 12px;">
                    <span style="display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;color:white;background:${sevColors[issue.severity]};">
                        ${issue.severity}
                    </span>
                </td>
                <td style="padding:8px 12px; color:var(--text-secondary, #6b7280); font-size:12px;">${issue.category}</td>
                <td style="padding:8px 12px; color:var(--text-primary, #111827);">${issue.desc}</td>
                <td style="padding:8px 12px; text-align:center; color:var(--text-secondary, #6b7280);">¶${issue.para}</td>
            `;
            tbody.appendChild(tr);
        });

        demoTable.appendChild(table);
        container.prepend(demoTable);
    }

    function _clearMockIssues() {
        document.querySelectorAll('.demo-issues-table').forEach(el => el.remove());
    }

    // ─── Checker Configuration Panel ───────────────────────────────────
    function expandAdvancedPanel() {
        // Fix: correct ID is 'advanced-panel', not 'advanced-settings-panel'
        const panel = document.getElementById('advanced-panel');
        if (panel) {
            panel.style.display = 'block';
            panel.classList.add(DEMO_CLASS);
            _addCleanup(() => {
                // Only collapse if we expanded it
                panel.style.display = '';
                panel.classList.remove(DEMO_CLASS);
            });
        }
        // Also try clicking the toggle button
        const btn = document.getElementById('btn-toggle-advanced');
        if (btn && panel && panel.style.display !== 'block') {
            btn.click();
        }
    }

    // ─── SOW Generator Output Preview ──────────────────────────────────
    function showSowOutputPreview() {
        // Create a mock SOW HTML output preview
        const modal = document.getElementById('modal-sow-generator');
        if (!modal) return;

        const preview = document.createElement('div');
        preview.className = DEMO_CLASS + ' sow-output-preview';
        preview.style.cssText = `
            position:absolute; top:60px; right:20px; width:340px; max-height:400px;
            overflow-y:auto; background:white; border-radius:12px; padding:20px;
            box-shadow:0 20px 60px rgba(0,0,0,0.3); z-index:148100;
            font-family:Georgia,serif; font-size:12px; color:#111;
        `;
        preview.innerHTML = `
            <div style="text-align:center; border-bottom:2px solid #D6A84A; padding-bottom:12px; margin-bottom:16px;">
                <div style="font-size:10px; color:#888; text-transform:uppercase; letter-spacing:2px;">Statement of Work</div>
                <div style="font-size:16px; font-weight:bold; color:#1a1a2e; margin-top:4px;">Flight Software Verification</div>
                <div style="font-size:10px; color:#666; margin-top:4px;">SOW-2026-0042 | Rev A</div>
            </div>
            <div style="margin-bottom:12px;">
                <div style="font-size:11px; font-weight:bold; color:#D6A84A; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">1.0 Scope</div>
                <p style="font-size:11px; line-height:1.5; color:#333;">The Contractor shall provide flight software verification and validation services for the GN&C subsystem in accordance with DO-178C Level A requirements.</p>
            </div>
            <div style="margin-bottom:12px;">
                <div style="font-size:11px; font-weight:bold; color:#D6A84A; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">2.0 Applicable Roles</div>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">
                    <span style="padding:2px 6px; background:#f0f4ff; border:1px solid #bfdbfe; border-radius:3px; font-size:9px;">Systems Engineer</span>
                    <span style="padding:2px 6px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:3px; font-size:9px;">V&V Lead</span>
                    <span style="padding:2px 6px; background:#fefce8; border:1px solid #fde68a; border-radius:3px; font-size:9px;">Quality Assurance</span>
                </div>
            </div>
            <div style="margin-bottom:12px;">
                <div style="font-size:11px; font-weight:bold; color:#D6A84A; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">3.0 Requirements</div>
                <table style="width:100%; border-collapse:collapse; font-size:10px;">
                    <tr style="background:#f9fafb;">
                        <td style="padding:4px 6px; border:1px solid #e5e7eb; font-weight:bold;">REQ-001</td>
                        <td style="padding:4px 6px; border:1px solid #e5e7eb;">The Contractor shall deliver test procedures within 30 calendar days.</td>
                    </tr>
                    <tr>
                        <td style="padding:4px 6px; border:1px solid #e5e7eb; font-weight:bold;">REQ-002</td>
                        <td style="padding:4px 6px; border:1px solid #e5e7eb;">All test results shall be traceable to parent requirements.</td>
                    </tr>
                </table>
            </div>
            <div style="text-align:center; padding-top:8px; border-top:1px solid #e5e7eb; font-size:9px; color:#999;">
                Generated by AEGIS v5.9.15 | ${new Date().toLocaleDateString()}
            </div>
        `;

        modal.style.position = 'relative';
        modal.appendChild(preview);

        _addCleanup(() => {
            preview.remove();
        });
    }

    // ─── Graph View Drag Simulation ────────────────────────────────────
    async function simulateGraphDrag() {
        const svg = document.querySelector('#roles-graph-container svg');
        if (!svg) return;

        // Find a node circle to "drag"
        const nodes = svg.querySelectorAll('circle.node, circle');
        if (nodes.length < 2) return;

        const targetNode = nodes[Math.min(3, nodes.length - 1)];
        const originalCx = targetNode.getAttribute('cx');
        const originalCy = targetNode.getAttribute('cy');

        // Animate a drag motion
        const startX = parseFloat(originalCx) || 200;
        const startY = parseFloat(originalCy) || 200;
        const endX = startX + 80;
        const endY = startY - 40;

        // Add a visual drag indicator
        const indicator = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        indicator.setAttribute('cx', startX);
        indicator.setAttribute('cy', startY);
        indicator.setAttribute('r', '20');
        indicator.setAttribute('fill', 'rgba(214,168,74,0.3)');
        indicator.setAttribute('stroke', '#D6A84A');
        indicator.setAttribute('stroke-width', '2');
        indicator.setAttribute('class', DEMO_CLASS);
        svg.appendChild(indicator);

        // Animate
        const duration = 1500;
        const startTime = performance.now();

        function animate(time) {
            const elapsed = time - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic

            const cx = startX + (endX - startX) * eased;
            const cy = startY + (endY - startY) * eased;
            indicator.setAttribute('cx', cx);
            indicator.setAttribute('cy', cy);

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                // Pulse at end position
                indicator.setAttribute('fill', 'rgba(214,168,74,0.5)');
                setTimeout(() => indicator.remove(), 2000);
            }
        }
        requestAnimationFrame(animate);

        _addCleanup(() => {
            indicator.remove();
        });
    }

    // ─── Export HTML Preview (standalone HTML output) ───────────────────
    function showHtmlExportPreview(type) {
        const preview = document.createElement('div');
        preview.className = DEMO_CLASS + ' demo-html-export-preview';
        preview.style.cssText = `
            position:fixed; top:50%; left:50%; transform:translate(-50%,-50%);
            width:600px; max-height:500px; overflow-y:auto;
            background:white; border-radius:16px; padding:0;
            box-shadow:0 25px 80px rgba(0,0,0,0.4); z-index:148200;
        `;

        const titles = {
            'sow': 'Statement of Work — Preview',
            'hierarchy': 'Role Inheritance Map — Preview',
            'adjudication': 'Adjudication Board — Preview',
            'graph': 'Graph Export — Preview'
        };

        preview.innerHTML = `
            <div style="background:linear-gradient(135deg,#1a1a2e,#2d2d44); color:white; padding:16px 24px; border-radius:16px 16px 0 0; display:flex; align-items:center; justify-content:space-between;">
                <div>
                    <div style="font-size:11px; color:#D6A84A; text-transform:uppercase; letter-spacing:2px;">Standalone HTML Export</div>
                    <div style="font-size:16px; font-weight:600; margin-top:4px;">${titles[type] || 'Export Preview'}</div>
                </div>
                <div style="font-size:11px; color:rgba(255,255,255,0.5);">Demo Preview</div>
            </div>
            <div style="padding:20px 24px; font-size:12px; color:#333;">
                <div style="display:flex; gap:12px; margin-bottom:16px;">
                    <div style="flex:1; background:#f0f9ff; border:1px solid #bfdbfe; border-radius:8px; padding:12px; text-align:center;">
                        <div style="font-size:20px; font-weight:700; color:#2563eb;">24</div>
                        <div style="font-size:10px; color:#6b7280;">Total Roles</div>
                    </div>
                    <div style="flex:1; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:8px; padding:12px; text-align:center;">
                        <div style="font-size:20px; font-weight:700; color:#16a34a;">18</div>
                        <div style="font-size:10px; color:#6b7280;">Adjudicated</div>
                    </div>
                    <div style="flex:1; background:#fefce8; border:1px solid #fde68a; border-radius:8px; padding:12px; text-align:center;">
                        <div style="font-size:20px; font-weight:700; color:#ca8a04;">6</div>
                        <div style="font-size:10px; color:#6b7280;">Pending</div>
                    </div>
                </div>
                <p style="color:#6b7280; font-size:11px; text-align:center;">
                    This standalone HTML file works offline — share via email, open in any browser, and import decisions back into AEGIS.
                </p>
            </div>
        `;
        document.body.appendChild(preview);

        _addCleanup(() => preview.remove());
    }

    // ─── Batch Results Simulation ──────────────────────────────────────
    function showBatchResults() {
        const modal = document.getElementById('batch-upload-modal');
        if (!modal) return;

        const resultsDiv = document.createElement('div');
        resultsDiv.className = DEMO_CLASS + ' demo-batch-results';
        resultsDiv.style.cssText = 'padding:16px; max-height:300px; overflow-y:auto;';

        const mockDocs = [
            { name: 'Requirements_Spec_v3.docx', grade: 'A', score: 92, issues: 8, words: 12400 },
            { name: 'Test_Plan_Rev2.docx', grade: 'B+', score: 78, issues: 23, words: 8900 },
            { name: 'Design_Description.pdf', grade: 'B', score: 74, issues: 31, words: 15600 },
            { name: 'Interface_Control.docx', grade: 'C+', score: 68, issues: 45, words: 6200 },
            { name: 'Safety_Assessment.pdf', grade: 'A-', score: 88, issues: 12, words: 21000 }
        ];

        const gradeColors = { 'A': '#16a34a', 'A-': '#22c55e', 'B+': '#2563eb', 'B': '#3b82f6', 'C+': '#f59e0b' };

        resultsDiv.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h4 style="margin:0;font-size:14px;color:var(--text-primary,#111);">Batch Scan Results</h4>
                <span style="font-size:12px;color:#16a34a;font-weight:600;">5/5 Complete</span>
            </div>
            ${mockDocs.map(d => `
                <div style="display:flex;align-items:center;gap:12px;padding:10px 12px;border:1px solid var(--border-color,#e5e7eb);border-radius:8px;margin-bottom:8px;background:var(--bg-surface,#fff);">
                    <div style="width:36px;height:36px;border-radius:50%;background:${gradeColors[d.grade]};color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;">${d.grade}</div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-size:13px;font-weight:500;color:var(--text-primary,#111);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${d.name}</div>
                        <div style="font-size:11px;color:var(--text-secondary,#6b7280);">${d.words.toLocaleString()} words · ${d.issues} issues · Score: ${d.score}</div>
                    </div>
                </div>
            `).join('')}
        `;

        const body = modal.querySelector('.modal-body');
        if (body) body.prepend(resultsDiv);

        _addCleanup(() => resultsDiv.remove());
    }

    // ─── Severity Count Badges ─────────────────────────────────────────
    function populateSeverityCounts() {
        const counts = {
            'count-critical': '3',
            'count-high': '8',
            'count-medium': '14',
            'count-low': '12',
            'count-info': '10'
        };
        const originals = {};
        Object.entries(counts).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) {
                originals[id] = el.textContent;
                el.textContent = val;
            }
        });
        _addCleanup(() => {
            Object.entries(originals).forEach(([id, val]) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            });
        });
    }

    // ─── Fix Assistant Mock Data ───────────────────────────────────────
    function populateFixAssistant() {
        const modal = document.getElementById('fav2-modal');
        if (!modal) return;

        const beforeEl = document.getElementById('fav2-change-before');
        const afterEl = document.getElementById('fav2-change-after');
        const progress = document.getElementById('fav2-progress-bar');
        const counter = document.getElementById('fav2-counter');

        if (beforeEl) beforeEl.textContent = 'The system shall be designed by the contractor to meet performance requirements.';
        if (afterEl) afterEl.textContent = 'The contractor shall design the system to meet performance requirements.';
        if (progress) progress.style.width = '30%';
        if (counter) counter.textContent = '3 of 10';

        _addCleanup(() => {
            if (beforeEl) beforeEl.textContent = '';
            if (afterEl) afterEl.textContent = '';
            if (progress) progress.style.width = '0%';
            if (counter) counter.textContent = '';
        });
    }

    // ─── Triage Mode Mock Data ─────────────────────────────────────────
    function populateTriageMode() {
        const msgEl = document.getElementById('triage-message');
        const fill = document.getElementById('triage-progress-fill');

        if (msgEl) {
            msgEl.innerHTML = `
                <div style="margin-bottom:8px;font-size:14px;font-weight:600;color:var(--text-primary,#111);">Passive Voice Detected</div>
                <div style="font-size:13px;color:var(--text-secondary,#555);line-height:1.6;">
                    <strong>Paragraph 15:</strong> "The system <mark style="background:#fef3c7;">shall be designed by the contractor</mark> to meet all performance requirements specified in Section 4.2."
                </div>
                <div style="margin-top:12px;padding:10px;background:var(--bg-surface,#f9fafb);border-radius:8px;font-size:12px;color:var(--text-secondary,#666);">
                    <strong>Suggestion:</strong> "The contractor shall design the system to meet all performance requirements specified in Section 4.2."
                </div>
            `;
        }
        if (fill) fill.style.width = '40%';

        _addCleanup(() => {
            if (msgEl) msgEl.innerHTML = '';
            if (fill) fill.style.width = '0%';
        });
    }

    // ─── Score Breakdown Mock Data ─────────────────────────────────────
    function populateScoreBreakdown() {
        const val = document.getElementById('score-breakdown-value');
        const grade = document.getElementById('score-breakdown-grade');
        const list = document.getElementById('score-improvements-list');

        if (val) val.textContent = '78';
        if (grade) { grade.textContent = 'B+'; grade.className = 'grade-b'; }
        if (list) {
            list.innerHTML = `
                <li>Fix 3 Critical issues for +8 points</li>
                <li>Resolve 8 High-severity passive voice issues for +5 points</li>
                <li>Define 4 undefined acronyms for +3 points</li>
                <li>Strengthen 6 escape clauses for +4 points</li>
            `;
        }

        _addCleanup(() => {
            if (val) val.textContent = '--';
            if (grade) { grade.textContent = '--'; grade.className = ''; }
            if (list) list.innerHTML = '';
        });
    }

    // ─── Scan History Mock Rows ────────────────────────────────────────
    function populateScanHistory() {
        const tbody = document.getElementById('scan-history-body');
        if (!tbody) return;

        // Only inject if empty
        if (tbody.children.length > 0) return;

        const mockScans = [
            { date: '2026-02-17', file: 'Requirements_Spec_v3.docx', grade: 'A', score: 92, issues: 8, stmts: 45 },
            { date: '2026-02-16', file: 'Test_Plan_Rev2.docx', grade: 'B+', score: 78, issues: 23, stmts: 32 },
            { date: '2026-02-15', file: 'NASA_SE_Handbook.pdf', grade: 'B', score: 74, issues: 47, stmts: 89 },
            { date: '2026-02-14', file: 'Safety_Assessment.pdf', grade: 'A-', score: 88, issues: 12, stmts: 56 },
            { date: '2026-02-13', file: 'Interface_Control.docx', grade: 'C+', score: 68, issues: 45, stmts: 28 }
        ];

        const gradeColors = { 'A': '#16a34a', 'A-': '#22c55e', 'B+': '#2563eb', 'B': '#3b82f6', 'C+': '#f59e0b' };

        mockScans.forEach(s => {
            const tr = document.createElement('tr');
            tr.className = DEMO_CLASS;
            tr.innerHTML = `
                <td>${s.date}</td>
                <td>${s.file}</td>
                <td><span style="color:${gradeColors[s.grade]};font-weight:600;">${s.grade}</span></td>
                <td>${s.score}</td>
                <td>${s.issues}</td>
                <td>${s.stmts}</td>
                <td>--</td>
                <td><button class="btn btn-ghost btn-sm" disabled><i data-lucide="eye"></i></button></td>
            `;
            tbody.appendChild(tr);
        });

        if (typeof lucide !== 'undefined' && lucide.createIcons) lucide.createIcons();

        _addCleanup(() => {
            tbody.querySelectorAll('.' + DEMO_CLASS).forEach(el => el.remove());
        });
    }

    // ─── Public API ────────────────────────────────────────────────────
    return {
        cleanupAll,
        showProgressDashboard,
        hideProgressDashboard,
        showSimulatedResults,
        expandAdvancedPanel,
        showSowOutputPreview,
        simulateGraphDrag,
        showHtmlExportPreview,
        showBatchResults,
        populateSeverityCounts,
        populateFixAssistant,
        populateTriageMode,
        populateScoreBreakdown,
        populateScanHistory,
        DEMO_CLASS
    };
})();
