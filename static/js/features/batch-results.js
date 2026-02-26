/**
 * BatchResults — Post-Scan Results Module
 * ========================================
 * v6.2.0: New IIFE providing filter system, drill-down viewer,
 * and filtered export for batch/folder/SharePoint scan results.
 *
 * Public API:
 *   BatchResults.init(data)    — Initialize with scan results data
 *   BatchResults.show()        — Render and display results view
 *   BatchResults.hide()        — Hide results view
 *   BatchResults.getFilters()  — Return active filter state
 *   BatchResults.exportFiltered() — Export only issues matching filters
 *   BatchResults.destroy()     — Clean up state and DOM
 */
window.BatchResults = (function () {
    'use strict';

    // ── State ───────────────────────────────────────────────────
    const State = {
        allDocuments: [],
        filteredDocuments: [],
        allIssues: [],        // Flattened from all documents
        filteredIssues: [],   // After filters
        activeFilters: {
            severities: [],
            categories: [],
            grades: [],
            fileTypes: []
        },
        presets: {
            'all': { label: 'All Issues', severities: [], categories: [] },
            'requirements': {
                label: 'Requirements Focus',
                categories: [
                    'Requirement Traceability', 'INCOSE Compliance', 'Requirement Ambiguity',
                    'Requirement Quality', 'Cross-Reference', 'Directive Verb', 'Verification Method',
                    'Ambiguous Scope', 'Vague Quantifier', 'Requirement Completeness'
                ]
            },
            'technical': {
                label: 'Technical Writing',
                categories: [
                    'Formatting', 'Structure', 'Consistency', 'Terminology', 'Clarity',
                    'Readability', 'Document Structure', 'Table Formatting'
                ]
            },
            'grammar': {
                label: 'Grammar & Style',
                categories: [
                    'Grammar', 'Spelling', 'Punctuation', 'Style', 'Passive Voice',
                    'Sentence Complexity', 'Word Choice'
                ]
            }
        },
        activePreset: 'all',
        selectedDocIndex: -1,
        sort: { field: 'score', direction: 'asc' },
        initialized: false,
        containerEl: null
    };

    // ── Severity ordering ───────────────────────────────────────
    const SEV_ORDER = ['Critical', 'High', 'Medium', 'Low', 'Info'];
    const SEV_COLORS = {
        'Critical': '#ef4444',
        'High': '#ea580c',
        'Medium': '#ca8a04',
        'Low': '#16a34a',
        'Info': '#3b82f6'
    };
    const GRADE_COLORS = {
        'A': '#16a34a', 'B': '#22c55e', 'C': '#ca8a04', 'D': '#f97316', 'F': '#ef4444'
    };

    // ── Helpers ─────────────────────────────────────────────────
    function _esc(str) {
        if (!str) return '';
        var d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }

    function _el(id) {
        return document.getElementById(id);
    }

    function _flattenIssues(documents) {
        var issues = [];
        documents.forEach(function (doc, docIdx) {
            if (doc.error || !doc.issues) return;
            doc.issues.forEach(function (issue) {
                issues.push(Object.assign({}, issue, {
                    _docIndex: docIdx,
                    _filename: doc.filename,
                    _filepath: doc.filepath,
                    _docScore: doc.score,
                    _docGrade: doc.grade
                }));
            });
        });
        return issues;
    }

    function _getUnique(issues, field) {
        var map = {};
        issues.forEach(function (i) {
            var val = i[field] || 'Unknown';
            map[val] = (map[val] || 0) + 1;
        });
        return map;
    }

    function _getFileType(filename) {
        if (!filename) return 'Unknown';
        var ext = filename.split('.').pop().toLowerCase();
        if (ext === 'pdf') return 'PDF';
        if (ext === 'docx' || ext === 'doc') return 'DOCX';
        if (ext === 'xlsx' || ext === 'xls') return 'XLSX';
        return ext.toUpperCase();
    }

    // ── Filter Logic ────────────────────────────────────────────
    function _applyFilters() {
        var f = State.activeFilters;
        var hasFilter = f.severities.length > 0 || f.categories.length > 0 ||
                        f.grades.length > 0 || f.fileTypes.length > 0;

        if (!hasFilter) {
            State.filteredIssues = State.allIssues.slice();
            State.filteredDocuments = State.allDocuments.slice();
        } else {
            // Filter issues: OR within dimension, AND across dimensions
            State.filteredIssues = State.allIssues.filter(function (issue) {
                if (f.severities.length > 0 && f.severities.indexOf(issue.severity || 'Info') === -1) return false;
                if (f.categories.length > 0 && f.categories.indexOf(issue.category || 'Unknown') === -1) return false;
                if (f.grades.length > 0 && f.grades.indexOf(issue._docGrade || 'C') === -1) return false;
                if (f.fileTypes.length > 0 && f.fileTypes.indexOf(_getFileType(issue._filename)) === -1) return false;
                return true;
            });

            // Filter documents: only show docs that have matching issues (or docs with errors)
            var docIndices = {};
            State.filteredIssues.forEach(function (i) { docIndices[i._docIndex] = true; });
            State.filteredDocuments = State.allDocuments.filter(function (doc, idx) {
                return docIndices[idx] || doc.error;
            });
        }

        _renderFilterSummary();
        _renderDocumentTable();
        _renderSeverityChart();
    }

    function _toggleFilter(dimension, value) {
        var arr = State.activeFilters[dimension];
        var idx = arr.indexOf(value);
        if (idx === -1) {
            arr.push(value);
        } else {
            arr.splice(idx, 1);
        }
        // If preset was active and user manually toggles, clear preset
        State.activePreset = '';
        _applyFilters();
        _syncChipUI();
    }

    function _applyPreset(presetKey) {
        var preset = State.presets[presetKey];
        if (!preset) return;

        State.activePreset = presetKey;
        State.activeFilters.severities = (preset.severities || []).slice();

        if (presetKey === 'all') {
            State.activeFilters.categories = [];
        } else {
            // For category presets, only activate categories that actually exist in results
            var existingCats = _getUnique(State.allIssues, 'category');
            State.activeFilters.categories = (preset.categories || []).filter(function (c) {
                return existingCats[c];
            });
        }

        State.activeFilters.grades = [];
        State.activeFilters.fileTypes = [];
        _applyFilters();
        _syncChipUI();
    }

    function _clearAllFilters() {
        State.activeFilters = { severities: [], categories: [], grades: [], fileTypes: [] };
        State.activePreset = 'all';
        _applyFilters();
        _syncChipUI();
    }

    function _syncChipUI() {
        var container = State.containerEl;
        if (!container) return;

        // Sync severity chips
        container.querySelectorAll('.br-filter-chip[data-severity]').forEach(function (chip) {
            var sev = chip.dataset.severity;
            chip.classList.toggle('active', State.activeFilters.severities.indexOf(sev) !== -1);
        });

        // Sync category chips
        container.querySelectorAll('.br-filter-chip[data-category]').forEach(function (chip) {
            var cat = chip.dataset.category;
            chip.classList.toggle('active', State.activeFilters.categories.indexOf(cat) !== -1);
        });

        // Sync grade chips
        container.querySelectorAll('.br-filter-chip[data-grade]').forEach(function (chip) {
            var grade = chip.dataset.grade;
            chip.classList.toggle('active', State.activeFilters.grades.indexOf(grade) !== -1);
        });

        // Sync file type chips
        container.querySelectorAll('.br-filter-chip[data-filetype]').forEach(function (chip) {
            var ft = chip.dataset.filetype;
            chip.classList.toggle('active', State.activeFilters.fileTypes.indexOf(ft) !== -1);
        });

        // Sync preset buttons
        container.querySelectorAll('.br-preset-btn').forEach(function (btn) {
            btn.classList.toggle('active', btn.dataset.preset === State.activePreset);
        });
    }

    // ── Rendering ───────────────────────────────────────────────

    function _renderHeroStats() {
        var container = _el('br-hero-stats');
        if (!container) return;

        var totalDocs = State.allDocuments.length;
        var errorDocs = State.allDocuments.filter(function (d) { return d.error; }).length;
        var totalIssues = State.allIssues.length;
        var avgScore = 0;
        var scoredDocs = State.allDocuments.filter(function (d) { return !d.error && d.score != null; });
        if (scoredDocs.length > 0) {
            avgScore = Math.round(scoredDocs.reduce(function (s, d) { return s + d.score; }, 0) / scoredDocs.length);
        }

        var critCount = State.allIssues.filter(function (i) { return i.severity === 'Critical'; }).length;
        var highCount = State.allIssues.filter(function (i) { return i.severity === 'High'; }).length;
        var rolesFound = {};
        State.allDocuments.forEach(function (d) {
            if (d.roles_found) {
                Object.keys(d.roles_found).forEach(function (r) { rolesFound[r] = true; });
            }
        });

        container.innerHTML =
            '<div class="br-stat-card">' +
                '<div class="br-stat-value">' + totalDocs + '</div>' +
                '<div class="br-stat-label">Documents</div>' +
                (errorDocs > 0 ? '<div class="br-stat-sub" style="color:#ef4444;">' + errorDocs + ' errors</div>' : '') +
            '</div>' +
            '<div class="br-stat-card">' +
                '<div class="br-stat-value">' + totalIssues + '</div>' +
                '<div class="br-stat-label">Total Issues</div>' +
                '<div class="br-stat-sub">' + critCount + ' critical, ' + highCount + ' high</div>' +
            '</div>' +
            '<div class="br-stat-card">' +
                '<div class="br-stat-value">' + avgScore + '%</div>' +
                '<div class="br-stat-label">Avg Score</div>' +
            '</div>' +
            '<div class="br-stat-card">' +
                '<div class="br-stat-value">' + Object.keys(rolesFound).length + '</div>' +
                '<div class="br-stat-label">Unique Roles</div>' +
            '</div>';
    }

    function _renderFilterPanel() {
        var container = _el('br-filters');
        if (!container) return;

        var sevCounts = {};
        SEV_ORDER.forEach(function (s) { sevCounts[s] = 0; });
        State.allIssues.forEach(function (i) {
            var sev = i.severity || 'Info';
            sevCounts[sev] = (sevCounts[sev] || 0) + 1;
        });

        var catCounts = _getUnique(State.allIssues, 'category');
        var sortedCats = Object.keys(catCounts).sort(function (a, b) { return catCounts[b] - catCounts[a]; });

        var gradeCounts = {};
        State.allDocuments.forEach(function (d) {
            if (!d.error) {
                var g = d.grade || 'C';
                gradeCounts[g] = (gradeCounts[g] || 0) + 1;
            }
        });

        var ftCounts = {};
        State.allDocuments.forEach(function (d) {
            var ft = _getFileType(d.filename);
            ftCounts[ft] = (ftCounts[ft] || 0) + 1;
        });

        var html = '';

        // Preset buttons
        html += '<div class="br-filter-section">' +
            '<div class="br-filter-label">Quick Filters</div>' +
            '<div class="br-preset-row">';
        Object.keys(State.presets).forEach(function (key) {
            var p = State.presets[key];
            var active = State.activePreset === key ? ' active' : '';
            html += '<button class="br-preset-btn' + active + '" data-preset="' + key + '">' + _esc(p.label) + '</button>';
        });
        html += '<button class="br-preset-btn br-clear-btn" data-action="clear"><i data-lucide="x" style="width:12px;height:12px;"></i> Clear All</button>';
        html += '</div></div>';

        // Severity chips
        html += '<div class="br-filter-section">' +
            '<div class="br-filter-label">Severity</div>' +
            '<div class="br-chip-row">';
        SEV_ORDER.forEach(function (sev) {
            if (sevCounts[sev] > 0) {
                html += '<div class="br-filter-chip" data-severity="' + sev + '">' +
                    sev + ' <span class="br-chip-count">(' + sevCounts[sev] + ')</span></div>';
            }
        });
        html += '</div></div>';

        // Grade chips
        if (Object.keys(gradeCounts).length > 1) {
            html += '<div class="br-filter-section">' +
                '<div class="br-filter-label">Grade</div>' +
                '<div class="br-chip-row">';
            ['A', 'B', 'C', 'D', 'F'].forEach(function (g) {
                if (gradeCounts[g]) {
                    html += '<div class="br-filter-chip" data-grade="' + g + '">' +
                        'Grade ' + g + ' <span class="br-chip-count">(' + gradeCounts[g] + ')</span></div>';
                }
            });
            html += '</div></div>';
        }

        // File type chips (only if multiple types)
        if (Object.keys(ftCounts).length > 1) {
            html += '<div class="br-filter-section">' +
                '<div class="br-filter-label">File Type</div>' +
                '<div class="br-chip-row">';
            Object.keys(ftCounts).sort().forEach(function (ft) {
                html += '<div class="br-filter-chip" data-filetype="' + ft + '">' +
                    ft + ' <span class="br-chip-count">(' + ftCounts[ft] + ')</span></div>';
            });
            html += '</div></div>';
        }

        // Category chips (collapsible, show top 10 by default)
        html += '<div class="br-filter-section">' +
            '<div class="br-filter-label">Category <span class="br-cat-toggle" id="br-cat-toggle">' +
            (sortedCats.length > 10 ? '(show all ' + sortedCats.length + ')' : '') + '</span></div>' +
            '<div class="br-chip-row" id="br-cat-chips">';
        sortedCats.forEach(function (cat, idx) {
            var hidden = idx >= 10 ? ' style="display:none;" data-overflow="true"' : '';
            html += '<div class="br-filter-chip" data-category="' + _esc(cat) + '"' + hidden + '>' +
                _esc(cat) + ' <span class="br-chip-count">(' + catCounts[cat] + ')</span></div>';
        });
        html += '</div></div>';

        container.innerHTML = html;

        // Attach chip click handlers via delegation
        container.addEventListener('click', function (e) {
            var chip = e.target.closest('.br-filter-chip');
            if (chip) {
                if (chip.dataset.severity) _toggleFilter('severities', chip.dataset.severity);
                else if (chip.dataset.category) _toggleFilter('categories', chip.dataset.category);
                else if (chip.dataset.grade) _toggleFilter('grades', chip.dataset.grade);
                else if (chip.dataset.filetype) _toggleFilter('fileTypes', chip.dataset.filetype);
                return;
            }
            var presetBtn = e.target.closest('.br-preset-btn');
            if (presetBtn) {
                if (presetBtn.dataset.action === 'clear') {
                    _clearAllFilters();
                } else if (presetBtn.dataset.preset) {
                    _applyPreset(presetBtn.dataset.preset);
                }
                return;
            }
            var catToggle = e.target.closest('#br-cat-toggle');
            if (catToggle) {
                var overflow = container.querySelectorAll('[data-overflow="true"]');
                var hidden = overflow.length > 0 && overflow[0].style.display === 'none';
                overflow.forEach(function (el) { el.style.display = hidden ? '' : 'none'; });
                catToggle.textContent = hidden ? '(show less)' : '(show all ' + (overflow.length + 10) + ')';
            }
        });

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function _renderFilterSummary() {
        var el = _el('br-filter-summary');
        if (!el) return;

        var hasFilter = State.activeFilters.severities.length > 0 ||
                        State.activeFilters.categories.length > 0 ||
                        State.activeFilters.grades.length > 0 ||
                        State.activeFilters.fileTypes.length > 0;

        if (!hasFilter) {
            el.textContent = 'Showing all ' + State.allIssues.length + ' issues across ' +
                State.allDocuments.length + ' documents';
        } else {
            var docCount = State.filteredDocuments.filter(function (d) { return !d.error; }).length;
            el.textContent = 'Showing ' + State.filteredIssues.length + ' of ' +
                State.allIssues.length + ' issues across ' + docCount + ' documents';
        }
    }

    function _renderSeverityChart() {
        var canvas = _el('br-severity-chart');
        if (!canvas || typeof Chart === 'undefined') return;

        // Destroy previous chart if exists
        if (canvas._brChart) {
            canvas._brChart.destroy();
        }

        var counts = {};
        SEV_ORDER.forEach(function (s) { counts[s] = 0; });
        State.filteredIssues.forEach(function (i) {
            var sev = i.severity || 'Info';
            counts[sev] = (counts[sev] || 0) + 1;
        });

        var labels = [];
        var data = [];
        var colors = [];
        SEV_ORDER.forEach(function (s) {
            if (counts[s] > 0) {
                labels.push(s);
                data.push(counts[s]);
                colors.push(SEV_COLORS[s]);
            }
        });

        canvas._brChart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: 'var(--text-primary)', font: { size: 11 } } }
                },
                cutout: '65%'
            }
        });
    }

    function _renderDocumentTable() {
        var container = _el('br-doc-table');
        if (!container) return;

        var docs = State.filteredDocuments;
        var sortField = State.sort.field;
        var sortDir = State.sort.direction;

        // Sort documents
        var sorted = docs.slice().sort(function (a, b) {
            var va, vb;
            if (sortField === 'filename') { va = a.filename || ''; vb = b.filename || ''; }
            else if (sortField === 'score') { va = a.score || 0; vb = b.score || 0; }
            else if (sortField === 'issues') { va = a.issue_count || 0; vb = b.issue_count || 0; }
            else if (sortField === 'roles') { va = a.role_count || 0; vb = b.role_count || 0; }
            else if (sortField === 'words') { va = a.word_count || 0; vb = b.word_count || 0; }
            else { va = 0; vb = 0; }

            if (typeof va === 'string') {
                var cmp = va.toLowerCase().localeCompare(vb.toLowerCase());
                return sortDir === 'asc' ? cmp : -cmp;
            }
            return sortDir === 'asc' ? va - vb : vb - va;
        });

        var arrow = function (field) {
            if (field !== sortField) return '';
            return sortDir === 'asc' ? ' ▲' : ' ▼';
        };

        var html = '<table class="br-table">' +
            '<thead><tr>' +
            '<th class="br-sortable" data-sort="filename">Document' + arrow('filename') + '</th>' +
            '<th class="br-sortable" data-sort="score">Score' + arrow('score') + '</th>' +
            '<th class="br-sortable" data-sort="issues">Issues' + arrow('issues') + '</th>' +
            '<th class="br-sortable" data-sort="roles">Roles' + arrow('roles') + '</th>' +
            '<th class="br-sortable" data-sort="words">Words' + arrow('words') + '</th>' +
            '<th>Severity</th>' +
            '<th>Actions</th>' +
            '</tr></thead><tbody>';

        sorted.forEach(function (doc) {
            var origIdx = State.allDocuments.indexOf(doc);
            var issuesByDoc = State.filteredIssues.filter(function (i) { return i._docIndex === origIdx; });
            var sevMini = _buildSevMiniBar(issuesByDoc);

            html += '<tr class="br-doc-row' + (doc.error ? ' br-error-row' : '') + '" data-doc-index="' + origIdx + '">' +
                '<td>' +
                    '<span class="br-doc-name">' + _esc(doc.filename) + '</span>' +
                    '<span class="br-doc-type">' + _getFileType(doc.filename) + '</span>' +
                '</td>' +
                '<td>' + (doc.error ? '<span class="br-badge br-badge-error">Error</span>' :
                    '<span class="br-grade grade-' + (doc.grade || 'c').toLowerCase() + '">' + (doc.score || 0) + '%</span>') +
                '</td>' +
                '<td>' + (doc.error ? '-' : (doc.issue_count || 0)) + '</td>' +
                '<td>' + (doc.error ? '-' : (doc.role_count || 0)) + '</td>' +
                '<td>' + (doc.error ? '-' : (doc.word_count || 0).toLocaleString()) + '</td>' +
                '<td>' + sevMini + '</td>' +
                '<td>' +
                    (doc.error
                        ? '<span class="br-badge br-badge-error" title="' + _esc(doc.error_message || 'Processing error') + '">Error</span>'
                        : '<button class="btn btn-sm btn-primary br-view-btn" data-doc-index="' + origIdx + '">' +
                            '<i data-lucide="eye" style="width:13px;height:13px;"></i> View</button>') +
                '</td>' +
            '</tr>';
        });

        html += '</tbody></table>';
        container.innerHTML = html;

        // Attach sort handlers
        container.querySelectorAll('.br-sortable').forEach(function (th) {
            th.addEventListener('click', function () {
                var field = th.dataset.sort;
                if (State.sort.field === field) {
                    State.sort.direction = State.sort.direction === 'asc' ? 'desc' : 'asc';
                } else {
                    State.sort.field = field;
                    State.sort.direction = 'asc';
                }
                _renderDocumentTable();
            });
        });

        // Attach view button handlers
        container.querySelectorAll('.br-view-btn').forEach(function (btn) {
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                var idx = parseInt(btn.dataset.docIndex, 10);
                _showDocDrillDown(idx);
            });
        });

        // Row click for drill-down
        container.querySelectorAll('.br-doc-row:not(.br-error-row)').forEach(function (row) {
            row.addEventListener('click', function () {
                var idx = parseInt(row.dataset.docIndex, 10);
                _showDocDrillDown(idx);
            });
        });

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function _buildSevMiniBar(issues) {
        if (!issues || issues.length === 0) return '<span class="br-sev-empty">—</span>';
        var counts = {};
        issues.forEach(function (i) {
            var sev = i.severity || 'Info';
            counts[sev] = (counts[sev] || 0) + 1;
        });
        var html = '<div class="br-sev-mini">';
        SEV_ORDER.forEach(function (s) {
            if (counts[s]) {
                html += '<span class="br-sev-dot" style="background:' + SEV_COLORS[s] + ';" title="' + s + ': ' + counts[s] + '">' + counts[s] + '</span>';
            }
        });
        html += '</div>';
        return html;
    }

    // ── Drill-Down View ─────────────────────────────────────────

    function _showDocDrillDown(docIndex) {
        var doc = State.allDocuments[docIndex];
        if (!doc || doc.error) return;

        State.selectedDocIndex = docIndex;
        var drillDown = _el('br-drill-down');
        var mainView = _el('br-main-view');
        if (!drillDown || !mainView) return;

        mainView.style.display = 'none';
        drillDown.style.display = 'flex';

        // Render drill-down header
        var header = _el('br-dd-header');
        if (header) {
            header.innerHTML =
                '<button class="btn btn-sm btn-ghost br-dd-back" id="br-dd-back">' +
                    '<i data-lucide="arrow-left" style="width:14px;height:14px;"></i> Back to Results</button>' +
                '<div class="br-dd-title">' +
                    '<span class="br-dd-filename">' + _esc(doc.filename) + '</span>' +
                    '<span class="br-grade grade-' + (doc.grade || 'c').toLowerCase() + '">' + (doc.score || 0) + '%</span>' +
                '</div>' +
                '<button class="btn btn-sm btn-primary br-dd-full-review" data-filepath="' + _esc(doc.filepath) + '" data-filename="' + _esc(doc.filename) + '">' +
                    '<i data-lucide="maximize-2" style="width:13px;height:13px;"></i> Full Review</button>';

            header.querySelector('#br-dd-back').addEventListener('click', _hideDocDrillDown);
            var fullBtn = header.querySelector('.br-dd-full-review');
            if (fullBtn) {
                fullBtn.addEventListener('click', function () {
                    if (typeof loadBatchDocument === 'function') {
                        loadBatchDocument(doc.filepath, doc.filename);
                    } else if (typeof window.loadBatchDocument === 'function') {
                        window.loadBatchDocument(doc.filepath, doc.filename);
                    } else {
                        console.warn('[BatchResults] loadBatchDocument not available');
                    }
                });
            }
        }

        // Render issues list
        _renderDrillDownIssues(docIndex);

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function _renderDrillDownIssues(docIndex) {
        var container = _el('br-dd-issues');
        if (!container) return;

        var doc = State.allDocuments[docIndex];
        var issues = State.filteredIssues.filter(function (i) { return i._docIndex === docIndex; });

        // Group by category
        var groups = {};
        issues.forEach(function (i) {
            var cat = i.category || 'Unknown';
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(i);
        });

        var sortedGroups = Object.keys(groups).sort(function (a, b) {
            return groups[b].length - groups[a].length;
        });

        var html = '<div class="br-dd-summary">' +
            '<span>' + issues.length + ' issues' + (issues.length !== (doc.issue_count || 0) ? ' (filtered from ' + doc.issue_count + ')' : '') + '</span>' +
            '</div>';

        sortedGroups.forEach(function (cat) {
            var catIssues = groups[cat];
            html += '<div class="br-dd-category">' +
                '<div class="br-dd-cat-header">' +
                    '<span class="br-dd-cat-name">' + _esc(cat) + '</span>' +
                    '<span class="br-dd-cat-count">' + catIssues.length + '</span>' +
                '</div>';

            catIssues.forEach(function (issue) {
                var sevClass = (issue.severity || 'Info').toLowerCase();
                html += '<div class="br-dd-issue">' +
                    '<div class="br-dd-issue-header">' +
                        '<span class="br-dd-sev sev-' + sevClass + '">' + _esc(issue.severity || 'Info') + '</span>' +
                        (issue.rule_id ? '<span class="br-dd-rule">' + _esc(issue.rule_id) + '</span>' : '') +
                    '</div>' +
                    '<div class="br-dd-issue-msg">' + _esc(issue.message || '') + '</div>' +
                    (issue.flagged_text ? '<div class="br-dd-flagged">"' + _esc(issue.flagged_text.substring(0, 200)) + '"</div>' : '') +
                    (issue.suggestion ? '<div class="br-dd-suggestion"><i data-lucide="lightbulb" style="width:12px;height:12px;"></i> ' + _esc(issue.suggestion) + '</div>' : '') +
                '</div>';
            });

            html += '</div>';
        });

        container.innerHTML = html;
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function _hideDocDrillDown() {
        State.selectedDocIndex = -1;
        var drillDown = _el('br-drill-down');
        var mainView = _el('br-main-view');
        if (drillDown) drillDown.style.display = 'none';
        if (mainView) mainView.style.display = '';
    }

    // ── Export ───────────────────────────────────────────────────

    function _exportFiltered(format) {
        format = format || 'csv';
        var issues = State.filteredIssues;
        if (issues.length === 0) {
            if (window.showToast) window.showToast('No issues to export with current filters', 'warning');
            return;
        }

        if (format === 'csv') {
            _exportCSV(issues);
        } else if (format === 'json') {
            _exportJSON(issues);
        }
    }

    function _exportCSV(issues) {
        var headers = ['Document', 'Score', 'Grade', 'Severity', 'Category', 'Rule', 'Message', 'Flagged Text', 'Suggestion', 'Paragraph'];
        var rows = [headers.join(',')];

        issues.forEach(function (i) {
            var row = [
                '"' + (i._filename || '').replace(/"/g, '""') + '"',
                i._docScore || 0,
                '"' + (i._docGrade || '') + '"',
                '"' + (i.severity || '') + '"',
                '"' + (i.category || '') + '"',
                '"' + (i.rule_id || '') + '"',
                '"' + (i.message || '').replace(/"/g, '""') + '"',
                '"' + (i.flagged_text || '').replace(/"/g, '""').substring(0, 500) + '"',
                '"' + (i.suggestion || '').replace(/"/g, '""') + '"',
                i.paragraph_index || 0
            ];
            rows.push(row.join(','));
        });

        var csv = rows.join('\n');
        var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'batch_results_filtered_' + new Date().toISOString().slice(0, 10) + '.csv';
        a.click();
        URL.revokeObjectURL(url);
        if (window.showToast) window.showToast('Exported ' + issues.length + ' issues to CSV', 'success');
    }

    function _exportJSON(issues) {
        var data = {
            export_date: new Date().toISOString(),
            filters: Object.assign({}, State.activeFilters),
            total_issues: State.allIssues.length,
            filtered_issues: issues.length,
            issues: issues.map(function (i) {
                return {
                    document: i._filename,
                    score: i._docScore,
                    grade: i._docGrade,
                    severity: i.severity,
                    category: i.category,
                    rule_id: i.rule_id,
                    message: i.message,
                    flagged_text: i.flagged_text,
                    suggestion: i.suggestion,
                    paragraph_index: i.paragraph_index
                };
            })
        };

        var json = JSON.stringify(data, null, 2);
        var blob = new Blob([json], { type: 'application/json;charset=utf-8;' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'batch_results_filtered_' + new Date().toISOString().slice(0, 10) + '.json';
        a.click();
        URL.revokeObjectURL(url);
        if (window.showToast) window.showToast('Exported ' + issues.length + ' issues to JSON', 'success');
    }

    // ── Main Container Build ────────────────────────────────────

    function _buildContainer() {
        var existing = _el('br-container');
        if (existing) {
            State.containerEl = existing;
            return existing;
        }

        // Build the batch results container inside #batch-results
        var batchResults = _el('batch-results');
        if (!batchResults) {
            console.warn('[BatchResults] #batch-results container not found');
            return null;
        }

        var container = document.createElement('div');
        container.id = 'br-container';
        container.className = 'br-container';

        container.innerHTML =
            '<!-- Main View -->' +
            '<div id="br-main-view" class="br-main-view">' +
                '<!-- Hero Stats -->' +
                '<div id="br-hero-stats" class="br-hero-stats"></div>' +

                '<!-- Filter Panel -->' +
                '<div class="br-filter-panel">' +
                    '<div class="br-filter-header">' +
                        '<span class="br-filter-title"><i data-lucide="filter" style="width:14px;height:14px;"></i> Filters</span>' +
                        '<span class="br-filter-summary" id="br-filter-summary"></span>' +
                    '</div>' +
                    '<div id="br-filters" class="br-filters"></div>' +
                '</div>' +

                '<!-- Content area: chart + table -->' +
                '<div class="br-content">' +
                    '<div class="br-chart-col">' +
                        '<div class="br-chart-card">' +
                            '<div class="br-chart-title">Issue Severity Distribution</div>' +
                            '<div class="br-chart-wrap"><canvas id="br-severity-chart"></canvas></div>' +
                        '</div>' +
                        '<!-- Export -->' +
                        '<div class="br-export-row">' +
                            '<button class="btn btn-sm btn-ghost br-export-btn" data-format="csv">' +
                                '<i data-lucide="file-text" style="width:13px;height:13px;"></i> Export CSV</button>' +
                            '<button class="btn btn-sm btn-ghost br-export-btn" data-format="json">' +
                                '<i data-lucide="braces" style="width:13px;height:13px;"></i> Export JSON</button>' +
                        '</div>' +
                    '</div>' +
                    '<div class="br-table-col" id="br-doc-table"></div>' +
                '</div>' +
            '</div>' +

            '<!-- Drill-Down View -->' +
            '<div id="br-drill-down" class="br-drill-down" style="display:none;">' +
                '<div id="br-dd-header" class="br-dd-header"></div>' +
                '<div class="br-dd-body">' +
                    '<div id="br-dd-issues" class="br-dd-issues"></div>' +
                '</div>' +
            '</div>';

        // Replace existing batch-summary and batch-documents with our container
        var summary = _el('batch-summary');
        var docs = _el('batch-documents');
        if (summary) summary.style.display = 'none';
        if (docs) docs.style.display = 'none';

        batchResults.appendChild(container);
        State.containerEl = container;

        // Export button handlers
        container.querySelectorAll('.br-export-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                _exportFiltered(btn.dataset.format);
            });
        });

        return container;
    }

    // ── Public API ──────────────────────────────────────────────

    function init(data) {
        if (!data || !data.documents) {
            console.warn('[BatchResults] init() called with invalid data');
            return;
        }

        State.allDocuments = data.documents || [];
        State.allIssues = _flattenIssues(State.allDocuments);
        State.filteredDocuments = State.allDocuments.slice();
        State.filteredIssues = State.allIssues.slice();
        State.activeFilters = { severities: [], categories: [], grades: [], fileTypes: [] };
        State.activePreset = 'all';
        State.selectedDocIndex = -1;
        State.sort = { field: 'score', direction: 'asc' };
        State.initialized = true;

        console.log('[BatchResults] Initialized with', State.allDocuments.length, 'documents,', State.allIssues.length, 'issues');
    }

    function show() {
        if (!State.initialized) {
            console.warn('[BatchResults] show() called before init()');
            return;
        }

        var container = _buildContainer();
        if (!container) return;

        container.style.display = '';
        _hideDocDrillDown();

        _renderHeroStats();
        _renderFilterPanel();
        _renderFilterSummary();
        _renderDocumentTable();
        _renderSeverityChart();

        if (typeof lucide !== 'undefined') lucide.createIcons();
    }

    function hide() {
        if (State.containerEl) {
            State.containerEl.style.display = 'none';
        }
        _hideDocDrillDown();
    }

    function getFilters() {
        return {
            activeFilters: Object.assign({}, State.activeFilters),
            activePreset: State.activePreset,
            filteredCount: State.filteredIssues.length,
            totalCount: State.allIssues.length
        };
    }

    function destroy() {
        if (State.containerEl && State.containerEl.parentNode) {
            State.containerEl.parentNode.removeChild(State.containerEl);
        }
        // Restore original containers
        var summary = _el('batch-summary');
        var docs = _el('batch-documents');
        if (summary) summary.style.display = '';
        if (docs) docs.style.display = '';

        State.allDocuments = [];
        State.allIssues = [];
        State.filteredDocuments = [];
        State.filteredIssues = [];
        State.containerEl = null;
        State.initialized = false;
        State.selectedDocIndex = -1;
    }

    return {
        init: init,
        show: show,
        hide: hide,
        getFilters: getFilters,
        exportFiltered: _exportFiltered,
        destroy: destroy
    };

})();
