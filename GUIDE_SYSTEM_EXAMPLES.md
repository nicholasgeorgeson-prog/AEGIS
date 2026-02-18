# AEGIS Guide System - Code Examples

Quick reference for common guide system integration tasks.

## Quick Start

### 1. Add Help Button to Modal Header

```javascript
// In your modal initialization code (e.g., in a routes file or module init)

const modal = document.getElementById('modal-myfeat');
if (modal && window.AEGISGuide) {
    AEGISGuide.addHelpButton(modal, 'myfeat');
}
```

The `addHelpButton` method:
- Creates a small circular "?" button
- Positions it before the close button
- Automatically handles clicks to open help panel
- Styles itself to match the AEGIS design system

### 2. Open Help Panel from Code

```javascript
// Open help for a specific section
if (window.AEGISGuide) {
    AEGISGuide.openPanel('roles');
}

// Detect current section and open contextual help
if (window.AEGISGuide) {
    const section = AEGISGuide.detectCurrentSection();
    AEGISGuide.openPanel(section);
}

// Toggle help (open if closed, close if open)
if (window.AEGISGuide) {
    AEGISGuide.togglePanel();
}
```

### 3. Start Guided Tour Programmatically

```javascript
// Start tour for current section
if (window.AEGISGuide) {
    AEGISGuide.startTour();
}

// Start full application tour
if (window.AEGISGuide) {
    AEGISGuide.startFullTour();
}

// End current tour
if (window.AEGISGuide) {
    AEGISGuide.endTour();
}
```

### 4. Add New Section to Guide System

Edit `static/js/features/guide-system.js` and add to `AEGISGuide.sections`:

```javascript
myfeature: {
    id: 'myfeature',
    title: 'My Awesome Feature',
    icon: 'star',  // Lucide icon name
    whatIsThis: 'A one or two sentence description of what this feature does and why users would use it.',
    keyActions: [
        { icon: 'zap', text: 'First key action users can perform' },
        { icon: 'upload', text: 'Second key action' },
        { icon: 'download', text: 'Third key action' }
    ],
    proTips: [
        'First pro tip for advanced users',
        'Second pro tip about a hidden feature',
        'Third tip about performance or best practices'
    ],
    tourSteps: [
        {
            target: '.my-feature-button',
            title: 'Step 1: Getting Started',
            description: 'This button is where you click to start using the feature.',
            position: 'bottom',
            offset: { x: 0, y: 20 }
        },
        {
            target: '.my-feature-options',
            title: 'Step 2: Configure Options',
            description: 'Use these settings to customize the feature behavior.',
            position: 'left',
            offset: { x: -20, y: 0 }
        },
        {
            target: '.my-feature-results',
            title: 'Step 3: View Results',
            description: 'Results appear here. Click any result to see more details.',
            position: 'top',
            offset: { x: 0, y: -20 }
        }
    ]
}
```

**Important:** All CSS selectors in `tourSteps[].target` must exist in your HTML!

### 5. Listen to Tour Events

```javascript
// You can hook into tour state through AEGISGuide.state
const interval = setInterval(() => {
    if (window.AEGISGuide) {
        const state = AEGISGuide.state;
        if (state.tourActive) {
            console.log('Current step:', state.currentTourIndex);
            console.log('Total steps:', state.currentTour.length);
        }
    }
}, 500);

// Clean up when done
// clearInterval(interval);
```

### 6. Custom Help Button (Manual)

If `addHelpButton` doesn't meet your needs, create one manually:

```javascript
// Create the button
const helpBtn = document.createElement('button');
helpBtn.className = 'modal-help-btn';
helpBtn.setAttribute('aria-label', 'Get help for this section');
helpBtn.setAttribute('title', 'Help');
helpBtn.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <path d="M12 16v-4M12 8h.01"></path>
    </svg>
`;

// Add click handler
helpBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    if (window.AEGISGuide) {
        AEGISGuide.openPanel('myfeat');
    }
});

// Insert into modal header
const modalHeader = document.querySelector('.my-modal-header');
const closeBtn = modalHeader.querySelector('.modal-close-btn');
if (closeBtn) {
    modalHeader.insertBefore(helpBtn, closeBtn);
} else {
    modalHeader.appendChild(helpBtn);
}
```

## Full Example: Complete Modal with Guide System

```html
<!-- HTML -->
<div id="modal-documents" class="modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2 class="modal-title">Document Management</h2>
            <!-- Help button will be inserted here -->
            <button class="modal-close-btn" aria-label="Close">×</button>
        </div>
        <div class="modal-body">
            <!-- Modal content -->
        </div>
    </div>
</div>
```

```javascript
// JavaScript - Initialize with guide system
function initDocumentsModal() {
    const modal = document.getElementById('modal-documents');
    if (!modal) return;

    // ... existing initialization code ...

    // Integrate with guide system
    if (window.AEGISGuide && typeof AEGISGuide.addHelpButton === 'function') {
        AEGISGuide.addHelpButton(modal, 'documents');
    }
}

// Call when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDocumentsModal);
} else {
    initDocumentsModal();
}
```

## Adding Guide System Content

### Section with 3 Key Actions and 2 Tips

```javascript
documents: {
    id: 'documents',
    title: 'Document Management',
    icon: 'file-text',
    whatIsThis: 'Upload, organize, and manage your technical documents. View document history, metadata, and status across all scans.',
    keyActions: [
        { icon: 'upload', text: 'Upload new documents via drag & drop or file browser' },
        { icon: 'eye', text: 'View document details and scanning history' },
        { icon: 'trash-2', text: 'Delete or archive documents you no longer need' }
    ],
    proTips: [
        'You can bulk select multiple documents to perform actions on them at once',
        'Documents are automatically scanned for changes when you re-upload a new version'
    ],
    tourSteps: [
        {
            target: '.doc-upload-zone',
            title: 'Upload Documents',
            description: 'Drag documents here or click the upload button. Supports .docx, .doc, and .pdf files.',
            position: 'bottom'
        },
        {
            target: '.doc-list-table',
            title: 'Document List',
            description: 'Each row shows a document with its metadata. Click to select or view details.',
            position: 'top'
        },
        {
            target: '.doc-bulk-actions',
            title: 'Bulk Actions',
            description: 'Select multiple documents, then use these buttons to perform actions on all of them.',
            position: 'left'
        }
    ]
}
```

### Short Tour (2 Steps)

```javascript
search: {
    id: 'search',
    title: 'Search & Filter',
    icon: 'search',
    whatIsThis: 'Quickly find documents, statements, or roles using powerful search filters.',
    keyActions: [
        { icon: 'search', text: 'Type keywords to search' },
        { icon: 'filter', text: 'Use filters to narrow results' }
    ],
    proTips: [
        'Searches are case-insensitive and match partial keywords'
    ],
    tourSteps: [
        {
            target: '.search-input',
            title: 'Enter Search Query',
            description: 'Type what you\'re looking for. Results update as you type.',
            position: 'bottom'
        },
        {
            target: '.search-results',
            title: 'View Results',
            description: 'Matching items appear here. Click any result to open details.',
            position: 'top'
        }
    ]
}
```

### Complex Tour (5+ Steps)

```javascript
workflow: {
    id: 'workflow',
    title: 'Complete Workflow',
    icon: 'workflow',
    whatIsThis: 'End-to-end workflow from document upload through analysis and reporting.',
    keyActions: [
        { icon: 'upload', text: 'Start by uploading your document' },
        { icon: 'sliders-horizontal', text: 'Configure quality checks' },
        { icon: 'play', text: 'Run the analysis' },
        { icon: 'check', text: 'Review the results' },
        { icon: 'download', text: 'Export your report' }
    ],
    proTips: [
        'Quality checks can be customized before each run',
        'You can re-run analysis with different settings on the same document',
        'Reports can be exported in multiple formats'
    ],
    tourSteps: [
        {
            target: '.hero-upload-zone',
            title: 'Step 1: Upload Document',
            description: 'Start by uploading a document. Drag & drop or click to browse.',
            position: 'bottom'
        },
        {
            target: '.checkers-panel',
            title: 'Step 2: Configure Checkers',
            description: 'Choose which quality checks to run. Toggle on/off as needed.',
            position: 'left'
        },
        {
            target: '.run-button',
            title: 'Step 3: Run Analysis',
            description: 'Click to start the scan. This typically takes 10-30 seconds.',
            position: 'bottom'
        },
        {
            target: '.results-section',
            title: 'Step 4: Review Results',
            description: 'Issues are listed here organized by severity. Click to see details.',
            position: 'top'
        },
        {
            target: '.export-section',
            title: 'Step 5: Export Report',
            description: 'Export results as PDF, CSV, or JSON for use in other tools.',
            position: 'top'
        }
    ]
}
```

## CSS Classes for Styling

You can customize guide system appearance by overriding these classes:

```css
/* Beacon customization */
.aegis-guide-beacon {
    background: your-color;
    bottom: 32px;  /* Adjust position */
    right: 32px;
}

/* Panel width */
.aegis-guide-panel {
    width: 380px;  /* Make wider/narrower */
}

/* Button styling */
.panel-btn {
    padding: 10px 16px;  /* Adjust size */
}

/* Tooltip styling */
.spotlight-tooltip {
    max-width: 360px;  /* Make narrower */
}
```

## Positioning Spotlight Steps

The `position` field controls where the tooltip appears relative to the target:

```javascript
// Bottom: Tooltip below element (good for elements at top of page)
{ position: 'bottom', offset: { x: 0, y: 20 } }

// Top: Tooltip above element (good for elements at bottom)
{ position: 'top', offset: { x: 0, y: -20 } }

// Left: Tooltip to the left (good for elements on right side)
{ position: 'left', offset: { x: -20, y: 0 } }

// Right: Tooltip to the right (good for elements on left side)
{ position: 'right', offset: { x: 20, y: 0 } }

// Custom offset: Fine-tune position
{ position: 'bottom', offset: { x: 50, y: 30 } }
```

## Dark Mode

The guide system automatically adapts to dark mode via the `[data-theme="dark"]` attribute on the html element. No additional configuration needed!

To test dark mode:
```javascript
// Toggle dark mode
document.documentElement.classList.toggle('dark-mode');

// Or programmatically
document.documentElement.setAttribute('data-theme', 'dark');
```

## Responsive Behavior

The guide system is fully responsive:

- **Desktop** (>768px): Full panel width, normal beacon
- **Tablet** (480px-768px): Panel adjusts to viewport
- **Mobile** (<480px): Full-width panel, smaller beacon

All adjustments happen automatically through CSS media queries.

## Console Debugging

```javascript
// Check if guide system initialized
console.log(window.AEGISGuide);

// Check current state
console.log(AEGISGuide.state);

// Check all sections
console.log(AEGISGuide.sections);

// Test opening a section
AEGISGuide.openPanel('landing');

// Test starting a tour
AEGISGuide.startTour();

// Check DOM references
console.log(AEGISGuide.refs);

// Get current detected section
console.log(AEGISGuide.detectCurrentSection());
```

## Common Patterns

### Trigger Help from Button

```javascript
document.getElementById('help-button').addEventListener('click', () => {
    if (window.AEGISGuide) {
        AEGISGuide.openPanel();
    }
});
```

### Trigger Tour from Link

```javascript
document.getElementById('start-tour-link').addEventListener('click', (e) => {
    e.preventDefault();
    if (window.AEGISGuide) {
        AEGISGuide.startFullTour();
    }
});
```

### Show Help When Feature is Used for First Time

```javascript
function checkFirstTimeUser() {
    const hasVisited = localStorage.getItem('aegis-visited-roles');
    if (!hasVisited && window.AEGISGuide) {
        AEGISGuide.openPanel('roles');
        localStorage.setItem('aegis-visited-roles', 'true');
    }
}

// Call on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', checkFirstTimeUser);
} else {
    checkFirstTimeUser();
}
```

### Conditional Tour Based on Feature Availability

```javascript
// Only show steps for features that are enabled
const tourSteps = [
    // Always show
    { target: '.basic-feature', title: '...', description: '...' },
    // Only if advanced module is loaded
    ...(window.AdvancedModule ? [{
        target: '.advanced-feature',
        title: '...',
        description: '...'
    }] : [])
];
```

## Performance Tips

1. **Lazy load tours** - Don't create all tour steps on page load
2. **Reuse panel** - The system uses one panel element for all sections
3. **Debounce section detection** - Don't call `detectCurrentSection()` too frequently
4. **Clean up SPOTLIGHTs** - Call `AEGISGuide.endTour()` when modal closes

## Accessibility Considerations

All guide system elements include:

- ARIA labels on buttons
- Proper heading hierarchy in tooltips
- Focus-visible states for keyboard navigation
- Color contrast ratios meeting WCAG AA standards
- Support for `prefers-reduced-motion`

When adding new sections, ensure:
- All target elements are keyboard accessible
- Describe actions in plain language
- Keep descriptions to 1-2 sentences max
