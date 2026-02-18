# AEGIS Guide System Integration Guide

**Version:** 1.0.0
**Date:** 2026-02-16
**Status:** Production Ready

## Overview

The AEGIS Guide System is a comprehensive cinematic help and guided tour system that provides:

1. **Floating Help Beacon** - Always-visible "?" button in the bottom-right corner with subtle pulse animation
2. **Contextual Help Panel** - Right-side slideout panel with glass-morphism backdrop showing section-specific help
3. **Guided Tours** - Spotlight overlay tours with step-by-step guidance and smooth animations
4. **Getting Started Card** - Prominent landing page card with quick access to full tour
5. **Modal Help Buttons** - Small "?" icons in modal headers for quick help access

## Files Created/Modified

### New Files

1. **`static/js/features/guide-system.js`** (~1000 lines)
   - Main JavaScript module containing all guide system logic
   - `AEGISGuide` namespace with all public methods
   - Section definitions with help content and tour steps
   - Spotlight overlay generation with SVG cutout
   - Responsive positioning logic

2. **`static/css/features/guide-system.css`** (~700 lines)
   - Complete styling for all guide system components
   - Animations: beacon pulse, tooltip pop, progress dots, etc.
   - Dark mode support via `[data-theme="dark"]` selector
   - Responsive adjustments for mobile/tablet
   - Accessibility focus states and reduced-motion support

### Modified Files

1. **`templates/index.html`**
   - Added CSS link: `<link rel="stylesheet" href="/static/css/features/guide-system.css">`
   - Added script: `<script src="/static/js/features/guide-system.js"></script>`
   - Added Getting Started card HTML (lines 85-94)

2. **`static/js/features/landing-page.js`**
   - Added event handler for Getting Started card (lines 598-607)
   - Calls `AEGISGuide.startFullTour()` when clicked

## Architecture

### `AEGISGuide` Public API

```javascript
// Initialize (called automatically on page load)
AEGISGuide.init()

// Open help panel for current or specific section
AEGISGuide.togglePanel(sectionId)
AEGISGuide.openPanel(sectionId)
AEGISGuide.closePanel()

// Start tours
AEGISGuide.startTour()           // Section-specific tour
AEGISGuide.startFullTour()       // Full app tour
AEGISGuide.endTour()

// Tour navigation
AEGISGuide.nextStep()
AEGISGuide.previousStep()
AEGISGuide.showStep(index)

// Integration helpers
AEGISGuide.openSectionHelp(sectionId)
AEGISGuide.addHelpButton(modalElement, sectionId)

// Context detection
AEGISGuide.detectCurrentSection()
```

### Section Definitions

Each section in `AEGISGuide.sections` contains:

```javascript
{
    id: 'landing',                    // Unique section ID
    title: 'Dashboard',               // Display title
    icon: 'layout-dashboard',         // Lucide icon name
    whatIsThis: '...',               // 1-2 sentence description
    keyActions: [
        {icon: 'file-text', text: '...'}, // Action list
        ...
    ],
    proTips: ['...', '...'],          // Array of tips
    tourSteps: [
        {
            target: '.selector',      // CSS selector for element
            title: '...',            // Step title
            description: '...',      // Step description
            position: 'bottom',      // top|bottom|left|right
            offset: {x: 0, y: 20}    // Optional offset
        },
        ...
    ]
}
```

### Spotlight Overlay Technology

The spotlight uses SVG masks for pixel-perfect cutouts:

1. Creates SVG with full-screen overlay rect
2. Applies mask with rectangular cutout around target element
3. Positions tooltip relative to target with viewport boundary checks
4. Smooth 400ms transitions between steps
5. Scrolls target into view before showing spotlight

## Using the Guide System

### Default Behavior

The guide system **initializes automatically** when the page loads:
- Beacon appears immediately in bottom-right corner
- Contextual panel is hidden until clicked
- Tours are triggered by user interaction only

### For End Users

1. **Click the "?" Beacon**
   - Opens contextual help for current section
   - Shows description, key actions, pro tips
   - "Watch Demo" button starts section-specific tour
   - "Take Tour" button starts full application tour

2. **Getting Started Card (Dashboard)**
   - Click to launch full guided tour
   - 20+ steps covering all major features
   - Can be skipped at any time

3. **Modal Help Buttons** (when added)
   - Small "?" in modal headers
   - Click for quick help specific to that modal

### For Developers

#### Add Help Button to a Modal

```javascript
// In modal initialization code:
const modal = document.getElementById('modal-review');
if (window.AEGISGuide) {
    window.AEGISGuide.addHelpButton(modal, 'review');
}
```

The help button:
- Automatically positioned before close button
- Styled to match the design system
- Opens contextual panel with section help

#### Open Help Panel Programmatically

```javascript
// From anywhere in the app:
if (window.AEGISGuide) {
    window.AEGISGuide.openPanel('roles');
}
```

#### Add New Section

1. Add entry to `AEGISGuide.sections`:

```javascript
myfeature: {
    id: 'myfeature',
    title: 'My Feature',
    icon: 'star',
    whatIsThis: 'Description...',
    keyActions: [
        {icon: 'zap', text: 'Action 1'},
        {icon: 'zap', text: 'Action 2'}
    ],
    proTips: ['Tip 1', 'Tip 2'],
    tourSteps: [
        {
            target: '.my-element',
            title: 'Step 1',
            description: 'Description',
            position: 'bottom'
        }
    ]
}
```

2. Ensure CSS selectors in `tourSteps` exist in your HTML
3. Test with `AEGISGuide.openPanel('myfeature')`

#### Customize Section Help Button Position

By default, help button is inserted before the close button. To customize:

```javascript
const modal = document.getElementById('modal-myfeature');
const helpBtn = document.createElement('button');
helpBtn.className = 'modal-help-btn';
helpBtn.innerHTML = '?';
helpBtn.addEventListener('click', () => {
    if (window.AEGISGuide) {
        window.AEGISGuide.openPanel('myfeature');
    }
});
// Insert wherever you want
modalHeader.insertBefore(helpBtn, someElement);
```

## Current Sections Covered

1. **Landing** - Dashboard overview, metrics, feature tiles
2. **Review** - Document upload, checker config, running reviews
3. **Roles** - Roles Studio tabs, network graph, RACI matrix
4. **Forge** - Statement search, history, source viewer
5. **Validator** - Hyperlink validation single/batch/deep
6. **Metrics** - Analytics charts, quality trends
7. **Settings** - Appearance, checkers, data management
8. **Compare** - Side-by-side document comparison

## Design & Styling

### CSS Variables Used

- `--aegis-blue` / `--aegis-blue-dark` - Primary brand color
- `--aegis-gold` - Accent color
- `--text-primary` / `--text-secondary` / `--text-inverse` - Text colors
- `--bg-primary` - Panel background
- All standard AEGIS color variables in base.css

### Dark Mode Support

All components automatically adapt to dark mode via `[data-theme="dark"]` selector:
- Panel backgrounds adjust opacity
- Text colors invert appropriately
- Beacon and button colors remain consistent
- Spotlight overlay is theme-agnostic (always dark)

### Z-Index Stack

```
Toast notifications:      2500
Guide beacon:            1500
Guide panel:             1450
Spotlight overlay:       1400
Modals:                  1000
```

The guide system sits between modals and toast notifications, allowing toasts to show above tours.

## Animations

### Beacon
- **Pulse**: Expands ring every 2 seconds
- **Bounce**: Subtle vertical bounce
- **Hover**: 10% scale increase

### Panel
- **Slide-in**: 300ms from right with easing
- **Smooth transitions**: All interactive elements

### Tour Tooltip
- **Pop**: 300ms scale + opacity animation
- **Progress dots**: Smooth color transition on step change
- **Spotlight**: 400ms smooth transition between steps

### Getting Started Card
- **Glow**: Subtle shadow pulse animation
- **Rotate**: Gradient border rotation (8s loop)
- **Icon float**: Vertical floating animation

All animations respect `prefers-reduced-motion` media query.

## Accessibility

### Keyboard Support

- Focus-visible states on all buttons (outline with 2px offset)
- Proper `aria-label` on all interactive elements
- Semantic HTML structure
- WCAG 2.1 AA compliance target

### Screen Reader Support

- Beacon: `aria-label="Open help and guided tour"`
- Tour steps: Step counter announced
- Close buttons: `aria-label` on all close actions
- Help buttons: Clear `aria-label` and `title` attributes

### Motion

- `prefers-reduced-motion: reduce` disables all animations
- Instant transitions for users with motion sensitivity

## Performance

### Optimizations

1. **Lazy initialization** - Guide system inits on first load only
2. **DOM efficiency** - Single panel element reused for all sections
3. **CSS animations** - Hardware-accelerated with `transform` and `opacity`
4. **SVG caching** - Spotlight SVG is replaced, not appended
5. **Event delegation** - Panel click handlers don't bubble unnecessarily

### Bundle Impact

- **guide-system.js**: ~40KB unminified, ~12KB minified+gzipped
- **guide-system.css**: ~28KB unminified, ~8KB minified+gzipped
- **Total**: ~20KB network impact

## Browser Support

- **Modern browsers** (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
- **CSS features**: CSS variables, CSS Grid, flexbox, backdrop-filter, SVG masks
- **Graceful degradation**: If JS fails, beacon is hidden; core app unaffected

## Testing Checklist

- [ ] Beacon appears in bottom-right on all pages
- [ ] Beacon pulse animation plays continuously
- [ ] Clicking beacon opens panel for current section
- [ ] Panel slides in from right smoothly
- [ ] "Watch Demo" starts section tour with spotlight
- [ ] "Take Tour" starts full app tour
- [ ] Tour can navigate forward/back with buttons
- [ ] Tour can be skipped at any time
- [ ] Spotlight overlay covers full viewport with cutout around target
- [ ] Tooltip positions correctly (not off-screen)
- [ ] Progress dots update with each step
- [ ] Dark mode applies to all guide components
- [ ] Getting Started card appears on dashboard
- [ ] Getting Started card triggers full tour
- [ ] Help buttons appear in modal headers
- [ ] Help buttons open correct section help
- [ ] All animations work smoothly (60fps)
- [ ] Mobile: Beacon stays visible on smaller screens
- [ ] Mobile: Panel width adapts (full width on mobile)
- [ ] Mobile: Tooltip fits in viewport
- [ ] Accessibility: All buttons have focus states
- [ ] Accessibility: Screen reader announces steps
- [ ] Print: Guide system doesn't appear in print preview

## Troubleshooting

### Beacon not visible

1. Check z-index: `console.log($('.aegis-guide-beacon').css('z-index'))`
2. Verify CSS file is loaded: Check Network tab in DevTools
3. Check for CSS conflicts: Inspect element for overriding styles

### Panel content not showing

1. Verify `AEGISGuide.sections` has the section ID
2. Check console for errors: `console.log(AEGISGuide.sections)`
3. Ensure lucide icons are loaded: `window.lucide.createIcons()`

### Spotlight target not found

1. Check CSS selector exists: `document.querySelector(selector)`
2. Verify element is visible on page
3. Wait for dynamic content to load before starting tour

### Tour step tooltip off-screen

- The system automatically repositions tooltip to stay in viewport
- If still off-screen, check that target element is on page
- Mobile: Ensure viewport height is sufficient

### Dark mode colors not applying

1. Check that `[data-theme="dark"]` is on `<html>` element
2. Verify CSS file is loaded after dark-mode.css
3. Clear browser cache and hard refresh

## Future Enhancements

Potential improvements for future versions:

1. **Persistent tour state** - Resume partial tours
2. **Multilingual support** - Translations for tour content
3. **Custom themes** - Allow customization of beacon color/position
4. **Analytics** - Track which tours are started/completed
5. **Conditional tours** - Show tours based on user role/permissions
6. **Video integration** - Embed video demos in tour steps
7. **Smart targeting** - Auto-detect section changes and offer relevant tours
8. **Community tours** - Crowdsourced tour content for specific workflows

## Support

For issues or questions about the guide system:

1. Check console for errors: `AEGISGuide.state` and `AEGISGuide.refs`
2. Verify all files are loaded: Check Network tab
3. Test in private/incognito window (rules out cache issues)
4. Review relevant sections in this documentation

## Version History

### v1.0.0 (2026-02-16)
- Initial release
- Floating beacon with animations
- Contextual help panel with glass-morphism
- Full application spotlight tour system
- 8 pre-configured section tours
- Dark mode support
- Mobile responsive design
- Full accessibility support
- Getting Started landing card integration
