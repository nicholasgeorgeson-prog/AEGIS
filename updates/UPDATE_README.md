# AEGIS Update System

## Overview

The AEGIS update system allows you to apply updates by simply dropping files into this folder. Updates are applied through the web interface with automatic backup creation.

## How to Apply Updates

### Step 1: Place Update Files Here

Drop your update files into this `updates/` folder. The system supports three methods:

#### Method 1: Directory Structure (Recommended)

Mirror the application's folder structure:

```
updates/
├── static/
│   ├── js/
│   │   ├── features/
│   │   │   └── roles.js
│   │   └── help-docs.js
│   └── css/
│       └── style.css
├── templates/
│   └── index.html
├── statement_forge/
│   └── export.py
└── role_extractor_v3.py
```

#### Method 2: Flat Files with Prefixes

Use naming prefixes to specify destinations:

| Prefix | Destination |
|--------|-------------|
| `static_js_features_` | `static/js/features/` |
| `static_js_ui_` | `static/js/ui/` |
| `static_js_api_` | `static/js/api/` |
| `static_js_utils_` | `static/js/utils/` |
| `static_js_vendor_` | `static/js/vendor/` |
| `static_js_` | `static/js/` |
| `static_css_` | `static/css/` |
| `templates_` | `templates/` |
| `statement_forge_` | `statement_forge/` |
| `tools_` | `tools/` |
| `data_` | `data/` |
| `images_` | `images/` |

**Examples:**
- `static_js_features_roles.js` → `static/js/features/roles.js`
- `static_css_style.css` → `static/css/style.css`
- `templates_index.html` → `templates/index.html`
- `statement_forge_export.py` → `statement_forge/export.py`

**Special Cases:**
- `index.html` (no prefix) → `templates/index.html`
- `style.css` (no prefix) → `static/css/style.css`
- `*.py` (no prefix) → app root
- `*.json` (no prefix) → app root

#### Method 3: Roles Package (.aegis-roles)

Drop a `.aegis-roles` file to auto-import a team member's role dictionary:

- The file is detected on the next update check
- Roles are imported into your dictionary (new roles added, existing ones skipped)
- Function categories from the package are also imported
- No manual intervention required — the file is processed and removed automatically

`.aegis-roles` files can be created by any AEGIS user via **Adjudication → Share → Email Package**.

### Step 2: Apply Updates via Web Interface

1. Open AEGIS in your browser
2. Click **Help** → **About** → **Settings** or navigate to **Settings** directly
3. Click the **Updates** tab
4. You'll see a list of pending updates
5. Click **Apply Updates** to install them
6. Click **Restart Server** when prompted

### Step 3: Verify Updates

After the server restarts:
1. Check the version number in **Help** → **About**
2. Test the updated features
3. If issues occur, use **Rollback** to restore the previous version

## API Endpoints

The update system provides REST endpoints for automation:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/updates/status` | GET | Get update system status |
| `/api/updates/check` | GET | Check for pending updates |
| `/api/updates/apply` | POST | Apply pending updates |
| `/api/updates/backups` | GET | List available backups |
| `/api/updates/rollback` | POST | Rollback to a backup |
| `/api/updates/restart` | POST | Restart the server |

### Example: Check for Updates (PowerShell)

```powershell
$response = Invoke-RestMethod -Uri "http://localhost:5050/api/updates/check"
$response.data.updates | Format-Table
```

### Example: Apply Updates (PowerShell)

```powershell
$body = @{ create_backup = $true } | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://localhost:5050/api/updates/apply" -Method POST -Body $body -ContentType "application/json"
Write-Host "Applied: $($response.data.applied), Failed: $($response.data.failed)"
```

## Backups

- Backups are automatically created before applying updates
- Stored in the `backups/` folder with timestamps
- Access via **Settings** → **Updates** → **Backups** tab
- Each backup contains the original files that were replaced
- Rollback restores files from the selected backup

## Supported File Types

| Extension | Category |
|-----------|----------|
| `.py` | Python source |
| `.js` | JavaScript |
| `.css` | Stylesheets |
| `.html` | Templates |
| `.json` | Configuration |
| `.md` | Documentation |
| `.ico` | Icons |
| `.ps1` | PowerShell scripts |
| `.bat` | Batch scripts (skipped) |
| `.aegis-roles` | Role dictionary packages (auto-imported) |

## Troubleshooting

### Updates Not Detected

1. Ensure files are directly in `updates/` or in proper subdirectories
2. Check file extensions match supported types
3. Refresh the Updates page in Settings

### Update Failed

1. Check the error message in the UI
2. Verify file permissions
3. Ensure the target directory exists
4. Check `logs/` for detailed error messages

### Rollback Failed

1. Ensure backup folder exists and contains files
2. Check that backup wasn't deleted
3. Verify file permissions

### Server Won't Restart

1. Manually stop the server
2. Run `Run_TWR.bat` or `python app.py`
3. The restart endpoint exits with code 75, which signals the batch file to restart

## Version History

- **v1.6** (4.0.3): Added .aegis-roles package auto-import support
- **v1.5** (3.1.4): Added user data preservation and upgrade packages
- **v1.3** (3.0.91d): Fixed app_dir auto-detection, added flat mode support
- **v1.2** (3.0.73): Added subdirectory routing, .md/.ico support
- **v1.1** (3.0.30): Added vendor routing, statement_forge support
- **v1.0** (3.0.20): Initial release with basic update functionality
