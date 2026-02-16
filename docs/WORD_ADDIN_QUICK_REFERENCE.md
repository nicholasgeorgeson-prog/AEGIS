# Word Add-in for AEGIS: Quick Reference Card

**Planning Document:** `/docs/word_addin_plan.md` (1,905 lines, 57KB)

## TL;DR - Decision Matrix

| Aspect | Decision |
|--------|----------|
| **Technology** | Office.js Web Add-in (only no-admin option) |
| **Installation** | Sideload at user level (no admin) |
| **Server** | HTTPS wrapper on localhost:7050 |
| **Manifest** | XML file (sideloaded from shared folder) |
| **Phase 1** | 2-3 weeks for MVP |
| **Phase 2** | 2-3 weeks for full integration |

## Key Architecture Points

```
Word Document
    ↓
Office.js API (task pane in iframe)
    ↓
fetch() → https://localhost:7050/api/review-text
    ↓
wrapper_https.py (HTTPS proxy)
    ↓
AEGIS Flask (http://localhost:5050)
    ↓
Review results → Display in task pane
    ↓
Insert comments + highlighting in Word
```

## No-Admin Installation (User-Level)

**Method A: Shared Folder (Easiest)**
1. Copy manifest.xml to C:\AEGIS\manifest.xml
2. In Word: File → Options → Trust Center → Trusted Add-in Catalogs
3. Add: file:///C:/AEGIS/
4. Restart Word → Insert → My Add-ins → AEGIS

**Method B: User Registry (PowerShell)**
```powershell
New-Item -Path "HKCU:\Software\Microsoft\Office\16.0\WEF\Developer" -Force
New-ItemProperty -Path "HKCU:\Software\Microsoft\Office\16.0\WEF\Developer" `
  -Name "AEGISManifest" `
  -Value "file:///C:/path/to/manifest.xml" `
  -PropertyType String
```

## Required Files to Create

```
word_addin/
├── manifest.xml              (Add-in metadata)
├── task-pane.html            (UI structure)
├── task-pane.js              (Office.js bridge)
├── task-pane.css             (Styling)
├── aegis-integration.js       (API client)
├── document-parser.js         (Content extraction)
├── issue-renderer.js          (Results display)
├── cert.pem                  (Self-signed certificate)
└── key.pem                   (Private key)

Backend:
├── wrapper_https.py           (HTTPS proxy)
├── routes/review_routes.py    (Add /api/review-text endpoint)
└── app.py                     (Start wrapper alongside main app)
```

## Development Workflow

### Setup (One-time)
```bash
# Generate certificate
openssl req -x509 -newkey rsa:2048 -nodes \
  -out word_addin/cert.pem \
  -keyout word_addin/key.pem \
  -days 365 \
  -subj "/CN=localhost"

# Install certificate in Windows (user interactive):
# Double-click cert.pem → Install Certificate → Current User
```

### Development (Daily)
```bash
# Terminal 1: AEGIS main app
python3 app.py --debug

# Terminal 2: HTTPS wrapper
python3 wrapper_https.py

# Word: Close and reopen task pane to reload (no server restart needed for JS/HTML)
```

## Code Snippets

### manifest.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1">
  <Id>12345678-1234-1234-1234-123456789012</Id>
  <Version>1.0.0.0</Version>
  <ProviderName>AEGIS</ProviderName>
  <DisplayName DefaultValue="AEGIS Document Review"/>
  <Description DefaultValue="AI-powered review directly in Word"/>
  <Hosts>
    <Host Name="Document"/>
  </Hosts>
  <DefaultSettings>
    <SourceLocation DefaultValue="https://localhost:7050/task-pane.html"/>
  </DefaultSettings>
  <Permissions>
    <Permission>ReadWriteDocument</Permission>
  </Permissions>
</OfficeApp>
```

### Key Office.js Operations

**Read document text:**
```javascript
await Word.run(async (context) => {
  const body = context.document.body;
  body.load('text');
  await context.sync();
  const text = body.text;
});
```

**Insert comment at location:**
```javascript
const searchResults = context.document.body.search(issueSnippet);
searchResults.load('items');
await context.sync();
if (searchResults.items.length > 0) {
  const range = searchResults.items[0];
  range.insertComment('AEGIS: ' + issue.message);
}
```

**Highlight text:**
```javascript
range.font.highlightColor = '#FFFF00'; // Yellow for warnings
```

## Known Constraints & Workarounds

| Constraint | Workaround |
|-----------|-----------|
| HTTPS required (even localhost) | Self-signed cert + user import |
| Browser CORS restrictions | Use wrapper_https.py proxy |
| User gesture needed for edits | Require "Apply" button click |
| Snippet search may find wrong location | Include paragraph context |
| Comments not deletable via API | Document in user guide |

## Success Criteria

**Phase 1 MVP:**
- Sideload with no admin (✓ feasible)
- Scan document and display results (✓ feasible)
- No unhandled errors (✓ achievable)
- Clear installation guide (✓ required)

**Phase 2 Full:**
- Comments inserted at correct locations (95%+ accuracy target)
- Highlighting visible for all issues (100% target)
- Large document support (>10MB) (✓ achievable)
- Settings persistence (✓ achievable)

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Certificate trust setup | Clear guide + automated script |
| CORS blocking requests | Test thoroughly, provide diagnostics |
| Large document timeout | Timeout handling + progress indicator |
| Issue location mismatch | Improve search algorithm + paragraph context |

## Timeline

**Phase 1 (MVP):** 2-3 weeks
- Setup & HTTPS proxy
- Basic task pane + Office.js
- AEGIS integration
- Sideload setup & testing

**Phase 2 (Full):** 2-3 additional weeks
- Comment insertion & highlighting
- Enhanced UI + settings
- Comprehensive testing
- Production documentation

## Important Links

- **Planning Document:** `/docs/word_addin_plan.md`
- **Office.js Docs:** https://docs.microsoft.com/en-us/javascript/api/office
- **Word API:** https://docs.microsoft.com/en-us/javascript/api/word
- **Add-in Manifest:** https://docs.microsoft.com/en-us/office/dev/add-ins/develop/add-in-manifest
- **Sideload Testing:** https://docs.microsoft.com/en-us/office/dev/add-ins/testing/test-debug-office-add-ins

## Decision: GO

Office.js web-based approach is:
- Only viable no-admin solution
- Technically feasible
- Clear development path
- Reasonable timeline
- Minimal AEGIS backend impact

**Next Step:** Proceed with Phase 1 implementation
