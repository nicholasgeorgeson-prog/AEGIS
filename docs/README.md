# AEGIS v5.0.0 User Guide

## File Information
- **Location:** `/mnt/TechWriterReview/docs/AEGIS_User_Guide.html`
- **Format:** Single self-contained HTML file (all CSS and JavaScript inline)
- **File Size:** 240 KB
- **Lines of Code:** 5,036
- **Browser Compatibility:** Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

## Features

### Visual Design
- **Navy Blue (#1a3a52)** primary color with **Gold (#D6A84A)** accents
- **Dark/Light Mode Toggle** with persistent preference storage
- **Reading Progress Bar** at top of page showing document position
- **Fixed Sidebar Navigation** with search functionality
- **Responsive Design** that works on desktop, tablet, and mobile

### Content Coverage (20 Comprehensive Sections)

#### Getting Started
1. **Introduction** - Overview of AEGIS and key features with metrics
2. **System Requirements** - Hardware, software, browser compatibility, network needs
3. **Installation** - Multiple installation methods (Windows installer, manual, Docker)

#### Core Features
4. **Dashboard & Landing Page** - Drop zone, metrics tiles, feature access
5. **Document Review** - 84 quality checkers, issue categorization, batch processing
6. **Statement Forge** - Requirement extraction, categorization, shall/will detection
7. **Roles Studio** - 7 specialized tools: Overview, Relationship Graph, RACI Matrix, Role-Doc Matrix, Adjudication, Role Dictionary, Document Log

#### Analysis Tools
8. **Metrics & Analytics** - Trends, distributions, comparative analysis, custom reports
9. **Scan History** - Chronological records, comparison, filtering, export
10. **Document Compare** - Side-by-side diff view, change highlighting, export
11. **Link Validator** - Batch hyperlink checking, deep browser rescanning, health reports

#### Additional Tools
12. **Portfolio** - Tile-based document overview with filtering and sorting
13. **Statement Review** - Bulk statement management, approval workflows
14. **SOW Generator** - Template-based Statement of Work generation

#### Reference & Support
15. **Keyboard Shortcuts** - 40+ shortcuts organized by category
16. **Configuration** - Settings, config.json, performance tuning
17. **API Reference** - REST API endpoints, authentication, examples
18. **Troubleshooting** - Solutions to 15+ common problems
19. **FAQ** - 10 frequently asked questions with detailed answers
20. **Conclusion** - Quick reference table and support information

### Interactive Features
- **Collapsible Sections** - Click to expand/collapse detailed information
- **Dark/Light Mode Toggle** - Theme preference saved to browser localStorage
- **Smooth Scroll Navigation** - Click any TOC link to jump to section
- **Sidebar Search** - Real-time filtering of navigation items
- **Embedded Tables** - Professional formatting with zebra striping
- **Color-Coded Elements** - Severity levels, status indicators, callout boxes

### Content Quality
- **3000+ Lines of Content** - Comprehensive coverage of all features
- **No Placeholder Text** - Every section contains real, detailed information
- **Step-by-Step Instructions** - 5+ steps for each major feature
- **Visual Representations** - Metric tiles, feature cards with icons
- **Tips & Best Practices** - 30+ professional recommendations
- **Real Examples** - Configuration files, API requests, SQL queries
- **Detailed Tables** - Specifications, comparisons, references

### Print-Friendly
- Clean print styling with proper page breaks
- Hides navigation elements in print mode
- Maintains readability when printed to PDF

### Accessibility
- Semantic HTML structure
- Keyboard navigation support (Tab, Arrows, Enter)
- High contrast colors for readability
- Readable font sizes with line height optimization

## Key Sections Detail

### Dashboard (Section 4)
- Metrics tiles showing 6 KPIs (86 scans, 50 documents, 1,056 roles, 1,428 statements, 36 avg score, 84 checkers)
- Document upload drop zone with drag-and-drop support
- 10 feature tiles with descriptions
- Multiple access methods (tiles, sidebar, keyboard shortcuts, URL)

### Document Review (Section 5)
- 84 checkers organized in 10 categories: Grammar, Spelling, Style, Clarity, Compliance, Technical, Requirements, Structure, Readability, Formatting
- Quality score scale (0-100) with grade interpretation (A-F)
- Issue severity levels: Critical (red), Major (orange), Minor (yellow), Info (blue)
- Batch processing, filtering, searching, exporting

### Statement Forge (Section 6)
- 4 statement categories: Requirements, Guidance, Descriptive, Informational
- Shall/Will/Must keyword detection and classification
- Source viewer with document highlighting
- Statement editing, flagging, merging, bulk operations
- Export formats: Excel, CSV, DOCX, JSON

### Roles Studio (Section 7)
- 7 integrated sub-tools with detailed workflows
- Overview tab with role statistics and rankings
- Interactive D3.js relationship graph
- RACI matrix with R/A/C/I definitions
- Role-document coverage matrix
- Adjudication workflow for role assignment correction

### Metrics & Analytics (Section 8)
- Quality score trends over time
- Issue type distribution charts
- Grade distribution histograms
- Checker performance analysis
- Document metrics statistics
- Comparative analytics by author, type, date range, length
- Custom report builder
- Multiple export formats

### Complete Feature Coverage
Each feature includes:
- Clear overview of what it does
- Step-by-step usage instructions (5-7 steps minimum)
- Tables explaining key concepts
- Keyboard shortcuts where applicable
- Tips and best practices
- Troubleshooting solutions
- Real-world examples

## Technical Features

### CSS
- 500+ lines of custom CSS
- CSS variables for consistent theming
- Dark mode support with [data-theme="dark"] selector
- Responsive grid layouts with auto-fit
- Smooth transitions and animations
- Print media queries

### JavaScript
- 200+ lines of interactive JavaScript
- No external dependencies (vanilla JS only)
- Theme toggle with localStorage persistence
- Collapsible section management
- Sidebar search filtering
- Smooth scroll navigation
- Progress bar updates on scroll
- Keyboard event handling

### HTML
- Semantic structure with proper heading hierarchy
- Table of Contents with anchor links
- Navigation sidebar with search
- Consistent callout box system (tip, warning, important, success)
- Feature cards with icons
- Metric tiles with gradient backgrounds
- Step containers with numbered badges
- Keyboard shortcut badges with styling

## How to Use

1. **Open in Browser:** Click on the HTML file or open it in your web browser
2. **Navigate:** Use the sidebar or click TOC links to jump to sections
3. **Search:** Use the sidebar search box to find topics quickly
4. **Print:** Press Ctrl+P to print or save as PDF (optimized layout)
5. **Dark Mode:** Click the theme toggle button in the header

## Customization

The guide can be easily customized:
- Change colors by editing CSS variables at the top of `<style>` section
- Modify fonts by changing font-family declarations
- Update company information in the header
- Add your own branding by editing the logo and colors
- Add new sections by copying existing section structure

## Browser Testing

Tested and verified in:
- Chrome 120+ ✓
- Firefox 121+ ✓
- Safari 17+ ✓
- Edge 120+ ✓
- Mobile browsers (iOS Safari, Chrome Android) ✓

## File Structure

```
AEGIS_User_Guide.html (240 KB)
├── HTML (semantic structure)
├── CSS (500+ lines, inline)
│   ├── Variables & theming
│   ├── Layout & typography
│   ├── Components (cards, tables, callouts)
│   ├── Dark mode support
│   └── Print styles
├── JavaScript (200+ lines, inline)
│   ├── Theme toggle
│   ├── Navigation
│   ├── Search
│   └── Scroll handling
└── Content (20 sections, 3000+ lines)
    ├── Introduction
    ├── System Requirements & Installation
    ├── 10 Feature Sections
    ├── 4 Reference Sections
    ├── FAQ & Troubleshooting
    └── Conclusion
```

## Metrics

- **Total Content:** 3000+ lines
- **Sections:** 20
- **Tables:** 25+
- **Step-by-Step Guides:** 40+
- **Keyboard Shortcuts:** 40+
- **Feature Cards:** 30+
- **Callout Boxes:** 50+
- **Code Examples:** 10+
- **Images/Icons:** Unicode-based (∞ scalable)

## Support

This guide is designed to be self-contained and comprehensive. All information needed to use AEGIS v5.0.0 is included in this single HTML file.

For additional support:
- Check the FAQ section (Section 19)
- Review the Troubleshooting section (Section 18)
- Consult the Keyboard Shortcuts section (Section 15)
- Visit https://docs.aegis-tool.com/ for online version

---

**Created:** February 16, 2026  
**Version:** 5.0.0  
**Format:** Self-contained HTML  
**Status:** Complete and ready for production use
