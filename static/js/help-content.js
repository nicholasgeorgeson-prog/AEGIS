/**
 * AEGIS Help Content Renderer
 * ======================================
 * Handles help modal rendering, navigation, and search
 * Version: 3.2.4
 *
 * Fixed: Better initialization, error handling, and HelpDocs integration
 */

'use strict';

const HelpContent = {
    version: '3.2.4',
    currentSection: 'welcome',
    scrollPositions: {},
    initialized: false,
    
    // Initialize help system
    init: function() {
        console.log('[HelpContent] Initializing v' + this.version);
        
        // Check if HelpDocs is available
        if (!window.HelpDocs) {
            console.error('[HelpContent] HelpDocs not loaded! Retrying in 100ms...');
            setTimeout(() => this.init(), 100);
            return;
        }
        
        // Check if HelpDocs.content has entries
        const contentKeys = Object.keys(HelpDocs.content);
        console.log('[HelpContent] HelpDocs.content has', contentKeys.length, 'sections');
        
        if (contentKeys.length === 0) {
            console.error('[HelpContent] HelpDocs.content is empty! Check help-docs.js');
            return;
        }
        
        this.bindEvents();
        this.buildNavigation();
        
        // Render initial section
        const initialSection = contentKeys.includes('welcome') ? 'welcome' : contentKeys[0];
        console.log('[HelpContent] Rendering initial section:', initialSection);
        this.renderSection(initialSection);
        
        this.initialized = true;
        console.log('[HelpContent] Initialized successfully');
    },
    
    // Build sidebar navigation from HelpDocs structure
    buildNavigation: function() {
        const sidebar = document.querySelector('.help-sidebar');
        if (!sidebar || !window.HelpDocs) {
            console.warn('[HelpContent] Cannot build navigation - sidebar or HelpDocs missing');
            return;
        }
        
        console.log('[HelpContent] Building navigation from', HelpDocs.navigation.length, 'sections');
        
        // Clear existing navigation
        sidebar.innerHTML = '';
        
        // Build from HelpDocs.navigation
        const nav = HelpDocs.navigation;
        
        nav.forEach(section => {
            const sectionEl = document.createElement('div');
            sectionEl.className = 'help-nav-section';
            
            // Section title (not clickable if has subsections)
            if (section.subsections && section.subsections.length > 0) {
                const titleEl = document.createElement('div');
                titleEl.className = 'help-nav-title';
                titleEl.textContent = section.title;
                sectionEl.appendChild(titleEl);
                
                // Add subsection buttons
                section.subsections.forEach(sub => {
                    const btn = this.createNavButton(sub.id, sub.title, sub.icon);
                    sectionEl.appendChild(btn);
                });
            } else {
                // Single section without subsections
                const btn = this.createNavButton(section.id, section.title, section.icon);
                sectionEl.appendChild(btn);
            }
            
            sidebar.appendChild(sectionEl);
        });
        
        // Add footer
        const footer = document.createElement('div');
        footer.className = 'help-nav-footer';
        footer.innerHTML = `
            <span class="help-version">v${HelpDocs.version}</span>
            <span class="help-credit">Nicholas Georgeson</span>
        `;
        sidebar.appendChild(footer);

        // BUG-M30 FIX: Re-initialize icons with requestAnimationFrame to avoid blocking
        if (typeof lucide !== 'undefined') {
            requestAnimationFrame(() => {
                try {
                    lucide.createIcons({ attrs: { class: 'lucide-icon' } });
                } catch (e) {
                    console.warn('[HelpContent] Lucide icon initialization error:', e);
                }
            });
        }
    },
    
    // Create navigation button
    createNavButton: function(id, title, icon) {
        const btn = document.createElement('button');
        btn.className = 'help-tab';
        btn.setAttribute('data-tab', id);
        btn.innerHTML = `<i data-lucide="${icon || 'file'}"></i> <span>${title}</span>`;
        
        btn.addEventListener('click', () => {
            this.navigateTo(id);
        });
        
        return btn;
    },
    
    // Navigate to a section
    navigateTo: function(sectionId) {
        console.log('[HelpContent] Navigating to:', sectionId);
        
        // Save current scroll position
        const mainContent = document.querySelector('.help-main');
        if (mainContent && this.currentSection) {
            this.scrollPositions[this.currentSection] = mainContent.scrollTop;
        }
        
        // Update active state
        document.querySelectorAll('.help-tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.getAttribute('data-tab') === sectionId) {
                tab.classList.add('active');
            }
        });
        
        // Render section
        this.renderSection(sectionId);
        this.currentSection = sectionId;
        
        // Restore scroll position if we've been here before
        if (mainContent && this.scrollPositions[sectionId]) {
            mainContent.scrollTop = this.scrollPositions[sectionId];
        } else if (mainContent) {
            mainContent.scrollTop = 0;
        }
    },
    
    // Render a section
    renderSection: function(sectionId) {
        const mainContent = document.querySelector('.help-main');
        if (!mainContent) {
            console.error('[HelpContent] .help-main element not found!');
            return;
        }
        
        if (!window.HelpDocs) {
            console.error('[HelpContent] HelpDocs not available!');
            mainContent.innerHTML = `
                <div class="help-section">
                    <div class="help-article-header">
                        <h1>Error Loading Help</h1>
                    </div>
                    <div class="help-article-content">
                        <p>Help documentation failed to load. Please refresh the page.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        const section = HelpDocs.content[sectionId];
        if (!section) {
            console.warn('[HelpContent] Section not found:', sectionId);
            console.log('[HelpContent] Available sections:', Object.keys(HelpDocs.content));
            mainContent.innerHTML = `
                <div class="help-section">
                    <div class="help-article-header">
                        <h1>Section Not Found</h1>
                    </div>
                    <div class="help-article-content">
                        <p>The help section "${sectionId}" could not be found.</p>
                        <p>Available sections: ${Object.keys(HelpDocs.content).join(', ')}</p>
                    </div>
                </div>
            `;
            return;
        }
        
        console.log('[HelpContent] Rendering section:', sectionId, '- Title:', section.title);

        mainContent.innerHTML = `
            <div class="help-section" id="help-${sectionId}">
                <div class="help-article-header">
                    <h1>${section.title}</h1>
                    ${section.subtitle ? `<p class="help-subtitle">${section.subtitle}</p>` : ''}
                </div>
                <div class="help-article-content">
                    ${section.html}
                </div>
            </div>
        `;

        // BUG-M30 FIX: Only re-initialize Lucide icons within the main content area
        // Using requestAnimationFrame to avoid blocking the main thread
        if (typeof lucide !== 'undefined') {
            requestAnimationFrame(() => {
                try {
                    lucide.createIcons({ attrs: { class: 'lucide-icon' } });
                } catch (e) {
                    console.warn('[HelpContent] Lucide icon initialization error:', e);
                }
            });
        }
    },
    
    // Bind events
    bindEvents: function() {
        // Search input
        const searchInput = document.getElementById('help-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
            
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    searchInput.value = '';
                    this.closeSearchResults();
                }
            });
        }
        
        // Print button
        const printBtn = document.getElementById('btn-help-print');
        if (printBtn) {
            printBtn.addEventListener('click', () => this.printSection());
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            // Only if help modal is visible
            const helpModal = document.getElementById('modal-help');
            if (!helpModal || !helpModal.classList.contains('active')) return;
            
            if (e.key === 'Escape') {
                // Close help modal
                helpModal.classList.remove('active');
            }
        });
        
        // Close search results when clicking outside
        document.addEventListener('click', (e) => {
            const searchContainer = document.querySelector('.help-search-container');
            if (searchContainer && !searchContainer.contains(e.target)) {
                this.closeSearchResults();
            }
        });
    },
    
    // Handle search
    handleSearch: function(query) {
        if (!query || query.length < 2) {
            this.closeSearchResults();
            return;
        }
        
        if (!window.HelpDocs || !HelpDocs.search) return;
        
        const results = HelpDocs.search(query);
        this.showSearchResults(results, query);
    },
    
    // Show search results
    showSearchResults: function(results, query) {
        let dropdown = document.querySelector('.help-search-results');
        
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.className = 'help-search-results';
            const searchContainer = document.querySelector('.help-search-container');
            if (searchContainer) {
                searchContainer.appendChild(dropdown);
            }
        }
        
        if (results.length === 0) {
            dropdown.innerHTML = `
                <div class="help-search-empty">
                    No results found for "${query}"
                </div>
            `;
        } else {
            dropdown.innerHTML = results.map(r => `
                <div class="help-search-result" data-section="${r.id}">
                    <div class="help-search-result-title">${r.title}</div>
                    ${r.subtitle ? `<div class="help-search-result-subtitle">${r.subtitle}</div>` : ''}
                </div>
            `).join('');
            
            // Add click handlers
            dropdown.querySelectorAll('.help-search-result').forEach(item => {
                item.addEventListener('click', () => {
                    const sectionId = item.getAttribute('data-section');
                    this.navigateTo(sectionId);
                    this.closeSearchResults();
                    const searchInput = document.getElementById('help-search-input');
                    if (searchInput) searchInput.value = '';
                });
            });
        }
        
        dropdown.classList.add('active');
    },
    
    // Close search results
    closeSearchResults: function() {
        const dropdown = document.querySelector('.help-search-results');
        if (dropdown) {
            dropdown.classList.remove('active');
        }
    },
    
    // Open help to specific section
    openToSection: function(sectionId) {
        const helpModal = document.getElementById('modal-help');
        if (helpModal) {
            helpModal.classList.add('active');
            
            // Initialize if needed
            if (!this.initialized) {
                this.init();
            }
            
            this.navigateTo(sectionId);
        }
    },
    
    // Print current section
    printSection: function() {
        const content = document.querySelector('.help-main');
        if (!content) return;

        const sectionData = HelpDocs.content[this.currentSection];
        const title = sectionData ? sectionData.title : 'Help';

        const printWindow = window.open('', '_blank');

        // BUG-M27 FIX: Check if popup was blocked
        if (!printWindow || !printWindow.document) {
            console.error('[HelpContent] Print popup blocked - please allow popups for this site');
            alert('Unable to open print window. Please allow popups for this site and try again.');
            return;
        }

        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>AEGIS Help - ${title}</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
                    h1 { color: #1a1a1a; font-size: 28px; }
                    h2 { color: #333; margin-top: 24px; font-size: 20px; }
                    h3 { color: #444; font-size: 16px; }
                    p { line-height: 1.6; color: #555; }
                    table { border-collapse: collapse; width: 100%; margin: 16px 0; }
                    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
                    th { background: #f5f5f5; font-weight: 600; }
                    code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
                    kbd { background: #eee; padding: 2px 6px; border-radius: 3px; border: 1px solid #ccc; font-family: monospace; }
                    ul, ol { padding-left: 24px; line-height: 1.8; }
                    .help-callout { background: #f0f7ff; border-left: 4px solid #3b82f6; padding: 12px 16px; margin: 16px 0; }
                    .help-hero { display: none; }
                    svg, i[data-lucide] { display: none; }
                </style>
            </head>
            <body>
                ${content.innerHTML}
                <hr style="margin-top: 40px; border: none; border-top: 1px solid #ddd;">
                <p style="color: #999; font-size: 12px;">Printed from AEGIS v${HelpDocs.version} Help</p>
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }
};

// Initialize on DOM ready
if (typeof window !== 'undefined') {
    window.HelpContent = HelpContent;
    
    // Wait for DOM and HelpDocs
    const initWhenReady = function() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                // Give HelpDocs time to fully load
                setTimeout(() => HelpContent.init(), 50);
            });
        } else {
            // DOM already ready, wait a tick for HelpDocs
            setTimeout(() => HelpContent.init(), 50);
        }
    };
    
    initWhenReady();
}

console.log('[HelpContent] Module loaded v3.2.4');
