# Contributing to AEGIS

## Development Setup

### Prerequisites
- Python 3.10+ (3.12+ recommended)
- pip package manager
- Git

### Quick Start
```bash
# Clone the repository
git clone <repo-url>
cd TechWriterReview

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
python3 app.py

# Open http://localhost:5050
```

### Running Tests
```bash
# All tests
python3 -m pytest tests/ -v

# Specific test file
python3 -m pytest tests/test_e2e_comprehensive.py -v

# NLP tests
python3 -m pytest tests/test_nlp/ -v

# Root-level integration tests
python3 -m pytest tests.py -v
```

## Architecture Overview

### Backend (Python/Flask)
- **app.py** - Main Flask routes (~10K lines, 157 routes)
- **core.py** - AEGISEngine: document extraction + checker pipeline
- **scan_history.py** - SQLite database operations
- **Blueprints**: `hyperlink_validator/`, `statement_forge/`, `portfolio/`, `document_compare/`

### Frontend (Vanilla JS)
- **No framework** - Pure JavaScript with IIFE module pattern
- **Namespace**: `window.TWR.*` for modules, `window.AEGIS.*` for utilities
- **Icons**: Lucide icons (call `refreshIcons()` after DOM updates)
- **Charts**: Chart.js (bar/line/doughnut), D3.js (heatmaps, network graphs)
- **CSS**: Custom properties for theming, `body.dark-mode` class for dark theme

### Database
- **SQLite** with WAL mode enabled
- **scan_history.db** - Main database (scans, roles, statements, function tags)
- **CSRF required** on all POST/PUT/DELETE via `X-CSRF-Token` header

### Key Patterns
- CSRF token: `document.querySelector('meta[name="csrf-token"]')?.content`
- Toast notifications: `showToast('success', 'Message')`
- Icon refresh: `if (typeof lucide !== 'undefined') lucide.createIcons()`
- Theme check: `document.body.classList.contains('dark-mode')`

## Code Style

### Python
- Use `except Exception:` (never bare `except:`)
- Use `@handle_api_errors` decorator on all API routes
- Return consistent JSON: `{ success: true/false, data: ..., error: ... }`

### JavaScript
- IIFE module pattern with `TWR.*` namespace
- No ES6 imports (scripts loaded via index.html)
- Use CSS custom variables for colors (`--bg-surface`, `--text-primary`, etc.)

## Server Configuration

Environment variables:
| Variable | Default | Description |
|----------|---------|-------------|
| `TWR_PORT` | 5050 | Server port |
| `TWR_AUTH` | false | Enable authentication |
| `TWR_CSRF` | true | Enable CSRF protection |
| `TWR_DEBUG` | false | Debug mode |
| `TWR_SECRET_KEY` | (generated) | Flask secret key |
| `TWR_RATE_LIMIT` | true | Rate limiting |

## Pull Request Guidelines

1. Run tests before submitting: `python3 -m pytest tests/ -v`
2. Update CHANGELOG.md with your changes
3. Update version.json if releasing a new version
4. Test in both light and dark mode
