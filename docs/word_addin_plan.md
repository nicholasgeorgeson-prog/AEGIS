# Word Add-in for AEGIS: Planning Document

**Document Version:** 1.0
**Created:** February 15, 2026
**Status:** Planning Phase
**Project:** AEGIS Document Review System Integration

---

## Executive Summary

This document outlines a feasible approach to integrate AEGIS into Microsoft Word via an Office.js web-based add-in. The solution enables users to run document reviews directly within Word without requiring administrator privileges, while maintaining full integration with the existing AEGIS Flask backend running at localhost:5050.

**Key Finding:** Office.js (web-based) add-ins are the only viable no-admin solution for this use case. VSTO and COM add-ins both require admin installation. Office.js add-ins can be sideloaded at the user level with no admin involvement.

---

## Part 1: Word Add-in Type Analysis

### 1.1 VSTO (Visual Studio Tools for Office)

**What it is:** Native .NET-based add-in using C# compiled to DLL/VSIX format

**Installation:**
- Requires admin privileges
- Installation at system/user level via Windows installer
- Creates registry entries
- Loads into Word process as native plugin

**Advantages:**
- Direct access to Word object model
- Full support for all Word features
- No browser/internet requirement
- Better performance for complex operations

**Disadvantages:**
- ❌ Requires admin install
- ❌ Requires .NET Framework/Runtime
- ❌ Difficult to distribute
- ❌ Single platform (Windows only)
- ❌ Requires Visual Studio for development

**Verdict for AEGIS:** NOT SUITABLE. Admin requirement disqualifies it.

---

### 1.2 COM (Component Object Model) Add-in

**What it is:** Legacy C++/COM-based extension registered in Windows registry

**Installation:**
- Requires admin privileges
- Windows registry modification
- Complex setup process
- Legacy technology

**Advantages:**
- Direct Word object access
- Historical compatibility

**Disadvantages:**
- ❌ Requires admin install
- ❌ Obsolete technology (deprecated by Microsoft)
- ❌ Very difficult to develop/maintain
- ❌ Poor documentation
- ❌ No modern tooling support

**Verdict for AEGIS:** NOT SUITABLE. Deprecated and requires admin.

---

### 1.3 Office.js Web Add-in (Recommended)

**What it is:** HTML/CSS/JavaScript-based add-in served from a web URL, runs in a sandboxed browser context within Word

**Installation:**
- ✅ User-level sideloading (no admin required)
- ✅ Manifest.xml + web server
- ✅ Optional: Centralized deployment via Microsoft 365 admin center (but not required)

**Sideloading Methods (No Admin):**

1. **Shared Folder Method** (Most Practical for AEGIS)
   - Add network path in Word: File → Options → Trust Center → Trusted Add-in Catalogs
   - Point to shared folder containing manifest.xml files
   - Word auto-discovers and lists add-ins
   - No admin approval needed

2. **User-Level Registry** (Windows Only)
   - Add registry entry to HKCU\Software\Microsoft\Office\16.0\WEF\Developer
   - Manifest path stored locally
   - Persistent across Word sessions
   - No admin required

3. **Upload to SharePoint** (If Available)
   - Upload manifest.xml to SharePoint document library
   - User uploads via Word UI
   - No admin required for user-level upload

**Advantages:**
- ✅ No admin privileges required
- ✅ Cross-platform (Windows, Mac, Web)
- ✅ Easy to develop (HTML/CSS/JS)
- ✅ Can communicate with local Flask server
- ✅ User-level installation
- ✅ Easy to update (just reload)

**Disadvantages:**
- Runs in sandboxed iframe (limited DOM access)
- Cannot directly modify document until user approves
- HTTPS required (even for localhost)
- CORS restrictions with local server
- Requires localhost certificate setup
- Network latency (vs native solution)

**Verdict for AEGIS:** SUITABLE AND RECOMMENDED. This is the only no-admin option.

---

## Part 2: Office.js Web Add-in Technical Architecture

### 2.1 How Office.js Add-ins Work

```
┌─────────────────────────────────────────────────────────┐
│  Microsoft Word Desktop Application                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Word UI Shell                                   │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  Document                                  │  │  │
│  │  │  (DOCX content)                            │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  │                                                   │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  TaskPane (Sandboxed iframe)               │  │  │
│  │  │  ┌──────────────────────────────────────┐  │  │  │
│  │  │  │ HTML/CSS/JavaScript (from localhost) │  │  │  │
│  │  │  │ - AEGIS UI Panel                     │  │  │  │
│  │  │  │ - Review Results Display             │  │  │  │
│  │  │  │ - Issue List + Comments              │  │  │  │
│  │  │  └──────────────────────────────────────┘  │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  API Bridge (Office.js)                                │
│  - Word.run() context for document access              │
│  - User gesture approval for edits                      │
│  - Postmessage communication                            │
│  ─────────────────────────────────────────────────     │
│  localhost:5050/task-pane.html (AEGIS Flask)           │
│  localhost:5050/api/review (Review API)                │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Component Structure

#### A. Manifest.xml (Add-in Metadata)

The manifest.xml file describes the add-in to Word. Minimum viable manifest:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1">
  <Id>12345678-1234-1234-1234-123456789012</Id>
  <Version>1.0.0.0</Version>
  <ProviderName>AEGIS</ProviderName>
  <DefaultLocale>en-US</DefaultLocale>
  <DisplayName DefaultValue="AEGIS Document Review"/>
  <Description DefaultValue="AI-powered technical writing review directly in Word"/>

  <Hosts>
    <Host Name="Document"/>  <!-- Word only -->
  </Hosts>

  <DefaultSettings>
    <SourceLocation DefaultValue="https://localhost:7050/task-pane.html"/>
  </DefaultSettings>

  <Permissions>
    <Permission>ReadWriteDocument</Permission>  <!-- Read/write doc content -->
  </Permissions>
</OfficeApp>
```

**Key Elements:**
- `Id`: Unique GUID (generated once, never change)
- `SourceLocation`: URL of task pane (must be HTTPS)
- `Permissions`: ReadWriteDocument allows reading document content and inserting comments
- `Host Name="Document"`: This is a Word document add-in

#### B. Task Pane (HTML UI)

The task pane is the sidebar panel in Word that displays the AEGIS UI:

```html
<!-- task-pane.html served from localhost:5050 -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <title>AEGIS</title>
  <script src="https://appsforoffice.microsoft.com/lib/1/hosted/office.js"></script>
  <link rel="stylesheet" href="/task-pane.css">
</head>
<body>
  <div id="aegis-container">
    <!-- AEGIS UI will be loaded here -->
    <h2>AEGIS Document Review</h2>
    <button id="scan-button">Scan Document</button>
    <div id="review-results"></div>
  </div>

  <script src="/task-pane.js"></script>
</body>
</html>
```

#### C. Task Pane JavaScript (Office.js API Bridge)

The task pane JavaScript implements the Office.js API to interact with Word:

```javascript
// task-pane.js
Office.onReady(async (info) => {
  if (info.host === Office.HostType.Word) {
    console.log("AEGIS add-in loaded in Word");

    // Set up event handlers
    document.getElementById('scan-button').onclick = scanDocument;
  }
});

async function scanDocument() {
  try {
    // User gesture required - this click handler provides it
    await Word.run(async (context) => {
      // Load document body
      const body = context.document.body;
      body.load('text');

      await context.sync();

      // Get document content
      const documentText = body.text;
      const documentLength = documentText.length;

      console.log(`Document has ${documentLength} characters`);

      // Send to AEGIS backend
      const reviewResults = await sendToAEGISBackend(documentText);

      // Display results in task pane
      displayResults(reviewResults);

      // Optionally: Insert comments into document
      if (reviewResults.issues && reviewResults.issues.length > 0) {
        await insertCommentsIntoDocument(context, reviewResults.issues);
      }
    });
  } catch (error) {
    console.error("Error scanning document:", error);
  }
}

async function sendToAEGISBackend(documentText) {
  // This calls the AEGIS /api/review endpoint
  const response = await fetch('https://localhost:7050/api/review', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      content: documentText,
      filename: "word-document.docx",
      format: 'text'
    })
  });

  return response.json();
}

async function insertCommentsIntoDocument(context, issues) {
  // Insert comments at issue locations
  for (const issue of issues) {
    const searchResults = context.document.body.getRange().getRange('Start').search(
      issue.snippet,
      { matchCase: false }
    );

    searchResults.load('items');
    await context.sync();

    if (searchResults.items.length > 0) {
      const range = searchResults.items[0];
      range.font.highlightColor = '#FFFF00';  // Highlight the issue

      // Insert comment (Word 2016 API)
      const comment = range.insertComment(issue.message);
      await context.sync();
    }
  }
}

function displayResults(reviewResults) {
  // Display results in task pane HTML
  const resultsDiv = document.getElementById('review-results');
  resultsDiv.innerHTML = `
    <h3>Review Results</h3>
    <p>Found ${reviewResults.issue_count} issues</p>
    <ul>
      ${reviewResults.issues.map(issue => `
        <li>
          <strong>${issue.category}</strong>: ${issue.message}
          <code>${issue.snippet}</code>
        </li>
      `).join('')}
    </ul>
  `;
}
```

### 2.3 Network Architecture: AEGIS Backend Integration

#### Problem: localhost Security Requirements

Office.js add-ins must load from HTTPS, even for localhost development. This requires:

1. **Self-Signed Certificate for localhost**
   - Create certificate: `openssl req -x509 -newkey rsa:2048 -nodes -out cert.pem -keyout key.pem -days 365`
   - Install certificate in Windows trusted store (one-time)
   - Flask serves task pane over HTTPS on port 7050

2. **CORS Configuration**
   - AEGIS Flask must include CORS headers for browser requests
   - Add `Access-Control-Allow-Origin: https://localhost:7050` to /api/review responses
   - Required so task pane JavaScript can call the review API

3. **Network Flow**

```
Word Document (running locally)
    ↓
    ├─ Office.js API (local process)
    │   • Read document text
    │   • Insert comments/highlights
    │   • Manage document changes
    │
    └─ Task Pane Browser Context (iframe)
       ↓
       fetch('https://localhost:7050/api/review')
       ↓
    AEGIS Flask (localhost:5050, proxy via 7050)
       ↓
       • PDF extraction
       • Run checkers
       • Generate issues
       ↓
    Return JSON response
       ↓
    Task Pane JavaScript
       • Display results
       • Insert Word comments
```

### 2.4 AEGIS Backend Modifications

Minimal changes needed to existing AEGIS Flask app:

#### A. HTTPS Wrapper (wrapper_https.py)

Create a simple HTTPS proxy that wraps the existing localhost:5050 server:

```python
# wrapper_https.py
from flask import Flask, request
import requests
import ssl

https_app = Flask(__name__)

AEGIS_BACKEND = 'http://localhost:5050'

@https_app.route('/api/review', methods=['POST'])
def proxy_review():
    """Proxy /api/review requests to AEGIS backend."""
    response = requests.post(
        f'{AEGIS_BACKEND}/api/review',
        json=request.json,
        headers=request.headers
    )

    # Add CORS headers
    result = response.json()
    result['headers'] = {
        'Access-Control-Allow-Origin': 'https://localhost:7050',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    return result

@https_app.route('/task-pane.html')
def task_pane():
    """Serve task pane HTML."""
    return open('word_addin/task-pane.html').read()

@https_app.route('/task-pane.js')
def task_pane_js():
    """Serve task pane JavaScript."""
    return open('word_addin/task-pane.js').read()

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')
    https_app.run(host='127.0.0.1', port=7050, ssl_context=context, debug=False)
```

#### B. Alternative: Embedded HTTPS in app.py

Modify app.py to serve HTTPS directly:

```python
# In app.py
import ssl

# ... existing Flask setup ...

if __name__ == '__main__':
    # Run Flask on 5050 (HTTP) for browser access
    # Run separate HTTPS wrapper on 7050 for Word add-in

    import subprocess
    import threading

    # Start main Flask app (HTTP)
    def run_http():
        app.run(host='127.0.0.1', port=5050, debug=False)

    # Start HTTPS wrapper
    def run_https():
        subprocess.run(['python', 'wrapper_https.py'])

    t1 = threading.Thread(target=run_http, daemon=True)
    t2 = threading.Thread(target=run_https, daemon=True)

    t1.start()
    t2.start()

    # Keep alive
    while True:
        time.sleep(1)
```

### 2.5 Office.js API Capabilities

#### Reading Document Content

```javascript
// Read all text from document
await Word.run(async (context) => {
  const body = context.document.body;
  body.load('text');
  await context.sync();

  const fullText = body.text;
});

// Read by paragraph (more granular)
await Word.run(async (context) => {
  const paragraphs = context.document.body.paragraphs;
  paragraphs.load('text');
  await context.sync();

  paragraphs.items.forEach(para => {
    console.log(para.text);
  });
});

// Read by range selection
await Word.run(async (context) => {
  const range = context.document.body.getRange('Start');
  range.load('text');
  await context.sync();
});
```

#### Inserting Comments/Tracking Changes

```javascript
// Insert comment at location
await Word.run(async (context) => {
  const body = context.document.body;

  // Find text matching issue
  const searchResults = body.search(issueSnippet, { matchCase: false });
  searchResults.load('items');
  await context.sync();

  if (searchResults.items.length > 0) {
    const range = searchResults.items[0];

    // Insert comment
    const comment = range.insertComment(
      `AEGIS: ${issueSeverity} - ${issueMessage}`
    );
    await context.sync();
  }
});

// Highlight text
await Word.run(async (context) => {
  const body = context.document.body;
  const searchResults = body.search(issueText, { matchCase: false });
  searchResults.load('items');
  await context.sync();

  for (const range of searchResults.items) {
    range.font.highlightColor = '#FFFF00';  // Yellow for warnings
  }

  await context.sync();
});

// Track changes (requires Office 365)
await Word.run(async (context) => {
  const body = context.document.body;
  context.document.body.revisions.load('items');
  await context.sync();

  // Revisions tracked automatically in Office 365
});
```

#### Constraint: User Gesture Required

All document modifications require a user gesture (click, keyboard event):

```javascript
// ✅ WORKS - called from click handler
document.getElementById('review-button').onclick = async () => {
  await Word.run(async (context) => {
    // Has user gesture - can insert comments
  });
};

// ❌ FAILS - called from async callback
async function reviewFromAPI() {
  const results = await fetch('/api/review');

  // User gesture lost after await - cannot modify document
  await Word.run(async (context) => {
    // Will fail - no user gesture
  });
}

// ✅ WORKAROUND - manual user interaction
async function reviewWithUserGesture() {
  const results = await fetch('/api/review');

  // Store results
  window.pendingResults = results;

  // Show "Apply Results" button requiring manual click
  document.getElementById('apply-button').style.display = 'block';
}

document.getElementById('apply-button').onclick = () => {
  // Now has user gesture
  applyResults(window.pendingResults);
};
```

---

## Part 3: Implementation Architecture

### 3.1 Directory Structure

```
TechWriterReview/
├── app.py                          (existing, unchanged)
├── routes/
│   ├── review_routes.py            (existing)
│   └── ...
├── word_addin/                     (NEW)
│   ├── manifest.xml                (Add-in metadata)
│   ├── task-pane.html              (UI for task pane)
│   ├── task-pane.js                (Office.js integration)
│   ├── task-pane.css               (Styling)
│   ├── aegis-integration.js         (AEGIS API client)
│   ├── document-parser.js           (Extract doc structure)
│   └── issue-renderer.js            (Display results)
├── wrapper_https.py                (NEW - HTTPS proxy, optional)
├── cert.pem                        (self-signed cert, NEW)
├── key.pem                         (private key, NEW)
└── docs/
    └── WORD_ADDIN_SETUP.md         (Installation guide, NEW)
```

### 3.2 File Descriptions

| File | Purpose | Size |
|------|---------|------|
| `word_addin/manifest.xml` | Add-in metadata, permissions, source location | ~1KB |
| `word_addin/task-pane.html` | Task pane UI structure | ~3KB |
| `word_addin/task-pane.js` | Office.js integration + main logic | ~8KB |
| `word_addin/task-pane.css` | Task pane styling (responsive) | ~4KB |
| `word_addin/aegis-integration.js` | API client for /api/review | ~3KB |
| `word_addin/document-parser.js` | Extract content in correct format | ~2KB |
| `word_addin/issue-renderer.js` | Format & display review results | ~4KB |
| `wrapper_https.py` | HTTPS proxy wrapper | ~2KB |
| `cert.pem` + `key.pem` | Self-signed certificate (generated) | |

### 3.3 Development Workflow

#### Setup Phase (One-time)

```bash
# 1. Generate self-signed certificate
openssl req -x509 -newkey rsa:2048 -nodes \
  -out word_addin/cert.pem \
  -keyout word_addin/key.pem \
  -days 365 \
  -subj "/CN=localhost"

# 2. Install certificate in Windows trusted store
# (User must do this once - will get browser warning first time)
# Open cert.pem, click "Install Certificate..." button
# Select "Local Machine" and place in "Trusted Root Certification Authorities"

# 3. Create GUID for manifest.xml
# (Use any online GUID generator or: python -c "import uuid; print(uuid.uuid4())")

# 4. Update manifest.xml with GUID
# Place manifest.xml at a user-accessible location or network share
```

#### Development Workflow

```bash
# Terminal 1: Start AEGIS main app (existing)
cd ~/Desktop/Work_Tools/TechWriterReview
python3 app.py --debug

# Terminal 2: Start HTTPS wrapper
cd ~/Desktop/Work_Tools/TechWriterReview
python3 wrapper_https.py

# Word: Sideload the add-in
# File → Options → Trust Center → Trusted Add-in Catalogs
# Click "Manage Catalogs" → Add network path to folder containing manifest.xml
# Or use User-Level Registry method (see Sideloading section)
```

#### Code Hot-Reload

- **HTML/CSS/JS in task pane:** Reload by closing and reopening task pane panel
- **Python changes:** Restart `app.py` (only needed for backend /api/review changes)
- **HTTPS certificate:** Restart `wrapper_https.py` only if certificate is regenerated

### 3.4 Sideloading Implementation (User Level, No Admin)

#### Method A: Shared Folder Sideloading (Recommended)

Most practical for end users:

**Setup:**
1. Place manifest.xml in a shared folder (local or network): `C:\AEGIS\manifest.xml`
2. Ensure manifest's `SourceLocation` points to `https://localhost:7050/task-pane.html`
3. In Word: File → Options → Trust Center → Trusted Add-in Catalogs
4. Click "Manage Catalogs"
5. Add catalog: `file:///C:/AEGIS/` (must be file:// URL)
6. Word automatically discovers and lists all manifest.xml files in that folder
7. User can install with one click, no admin approval

**Pros:**
- No registry modification
- Works across all Word versions
- Easy to distribute manifest
- One-click installation

**Cons:**
- Folder path must be accessible to user
- Folder-level discovery (not file-level)

#### Method B: User-Level Registry (Windows Only)

Direct registry approach without folder requirement:

**Registry Key:**
```
HKCU\Software\Microsoft\Office\16.0\WEF\Developer
```

**Steps:**
1. Create registry key if it doesn't exist:
```powershell
New-Item -Path "HKCU:\Software\Microsoft\Office\16.0\WEF\Developer" -Force
```

2. Add entry for AEGIS add-in:
```powershell
New-ItemProperty -Path "HKCU:\Software\Microsoft\Office\16.0\WEF\Developer" `
  -Name "AEGISManifest" `
  -Value "file:///C:/Users/[UserName]/AppData/Local/AEGIS/manifest.xml" `
  -PropertyType String
```

3. Restart Word
4. Add-in appears in "My Add-ins" → "Developer" section

**Pros:**
- Direct control
- No shared folder needed
- Flexible manifest location

**Cons:**
- Requires PowerShell or registry editor
- Less discoverable to non-technical users

#### Method C: SharePoint Upload (If Organization Uses SharePoint)

If user has access to SharePoint:

**Steps:**
1. Upload manifest.xml to SharePoint document library
2. In Word: Insert → Get Add-ins → My Add-ins → "Upload My Add-in"
3. Select manifest.xml from SharePoint
4. Word validates and installs

**Pros:**
- Centralized management
- Persistent storage

**Cons:**
- Requires SharePoint
- Requires admin to enable user uploads

### 3.5 Recommended Approach for End Users

**For AEGIS internal use (technical team):**
- Use Method B (Registry) with PowerShell script
- Ship script in installation package
- One-line installation

**For broader deployment:**
- Use Method A (Shared Folder)
- Create shared folder on network
- Link in documentation
- Easy for IT to manage if needed

---

## Part 4: Sideloading Without Admin Privileges

### 4.1 Verification: No Admin Required

Office.js web add-ins sideloading does NOT require:
- ❌ Administrator account privileges
- ❌ Windows admin approval
- ❌ System-wide installation
- ❌ Registry modification (for Methods A & C)
- ❌ App Store/Microsoft approval
- ❌ Code signing

Required (user-level only):
- ✅ Local user account with Word installed
- ✅ File system access (to manifest location)
- ✅ Network access (to connect to localhost:7050)

### 4.2 User Installation Checklist

```
AEGIS Word Add-in Installation (No Admin)
==========================================

PREREQUISITE:
[ ] Word 2016 or later (Office 365 or standalone)
[ ] Python 3.9+ with Flask installed (for localhost:5050)
[ ] AEGIS already running on localhost:5050

STEP 1 - Certificate Trust (One-time)
[ ] Download AEGIS certificate file (word_addin/cert.pem)
[ ] Double-click cert.pem
[ ] Select "Install Certificate"
[ ] Choose "Current User" (NOT "Local Machine" - no admin needed)
[ ] Select "Place all certificates in the following store"
[ ] Browse and select "Trusted Root Certification Authorities"
[ ] Click OK

STEP 2 - HTTPS Proxy (One-time)
[ ] Start HTTPS wrapper (wrapper_https.py)
[ ] Verify running on https://localhost:7050
[ ] Keep running while using add-in

STEP 3 - Sideload Manifest (Choose ONE method)

  METHOD A - Shared Folder (Easiest):
  [ ] Copy manifest.xml to C:\AEGIS\manifest.xml
  [ ] In Word: File → Options → Trust Center
  [ ] Click "Trusted Add-in Catalogs"
  [ ] Add catalog: file:///C:/AEGIS/
  [ ] Restart Word
  [ ] Go to Insert → Get Add-ins → My Add-ins → AEGIS

  METHOD B - User Registry (Most Flexible):
  [ ] Open PowerShell (no admin needed, run as self)
  [ ] Paste script: (provided separately)
  [ ] Restart Word
  [ ] Go to Insert → My Add-ins → Developer → AEGIS

STEP 4 - Verify Installation
[ ] Open Word document
[ ] Click "AEGIS" in task pane
[ ] Click "Scan Document"
[ ] Verify review results appear
```

### 4.3 Troubleshooting No-Admin Issues

**Problem: Certificate warning in browser console**
- Solution: Certificate installed but not trusted
- Action: Follow Step 1 of checklist above, select Trusted Root store

**Problem: CORS error when calling /api/review**
- Solution: Wrapper not running or wrapper.py misconfigured
- Action: Start wrapper_https.py, verify port 7050 listening

**Problem: Add-in doesn't appear in Word**
- Solution A: Manifest not discovered
- Action: Verify file:///C:/AEGIS/ path exists and contains manifest.xml
- Solution B: Registry path wrong (Method B)
- Action: Verify HKCU not HKLM (current user, not machine)

**Problem: "Cannot run Office scripts" error**
- Solution: User gesture not provided before document modification
- Action: Click "Apply Results" button instead of auto-applying

---

## Part 5: Limitations & Constraints

### 5.1 Technical Limitations

#### Localhost HTTPS Requirement

**Issue:** Office.js mandates HTTPS even for localhost
**Impact:**
- Extra setup complexity (certificate generation)
- Certificate warnings first time (user must accept)
- Certificate renewal every 365 days (or auto-rotate)

**Mitigation:**
- Provide clear setup documentation
- Auto-generate certificate during installation
- Implement certificate renewal reminder in wrapper_https.py

#### CORS Restrictions

**Issue:** Browser sandbox prevents cross-origin requests
**Impact:**
- Cannot directly call http://localhost:5050 from task pane (mixed content)
- Requires HTTPS proxy on separate port (7050)

**Mitigation:**
- Wrapper_https.py handles proxying
- CORS headers configured in proxy responses
- Transparent to end user

#### User Gesture Requirement

**Issue:** Word security model requires user interaction to modify document
**Impact:**
- Cannot auto-apply all issues without user confirmation
- Buttons required for each major action (Scan, Apply, Insert Comments)

**Mitigation:**
- Design UI with clear action buttons
- Batch operations (apply all issues at once)
- Show progress indicators

#### Document Content Limitations

**Issue:** Office.js reads document as plain text (loses formatting, images, tables)
**Impact:**
- Issues in tables/images/headers not detected precisely
- Character position mapping becomes complex
- Inline formatting not preserved in extracted text

**Mitigation:**
- Extract full XML if needed (advanced API)
- Use paragraph-level analysis instead of character-level
- Document limitations in user guide

#### Platform Limitations

**Office.js Support:**
- Windows: Word 2016 SP1 or later, Office 365
- Mac: Word 2016 or later, Office 365
- Web: Word Online (full support)
- ❌ Not available: Word 2013 or earlier

**Network Limitations:**
- Requires localhost accessible (no proxy bypass)
- Cannot work on VPN with IP restrictions
- No offline mode (must connect to AEGIS)

### 5.2 Functional Limitations

#### Issue Location Precision

**Challenge:** Mapping AEGIS issues back to Word locations

Current Approach:
```javascript
// Find snippet in document
const searchResults = body.search(issue.snippet, {matchCase: false});

// Limitation: Works for unique snippets only
// If text appears multiple times, may select wrong instance
```

**Improved Approach:**
```javascript
// Use paragraph + offset instead of full-text search
const paragraphs = body.paragraphs;
for (let i = 0; i < paragraphs.length; i++) {
  if (paragraphs[i].text.includes(issue.snippet)) {
    // Found in paragraph i
    // Could use character offset within paragraph
  }
}
```

#### Comment Limitations

**Constraint:** Word comment API has limitations:
- Comments always attached to paragraphs (not character ranges)
- Cannot delete comments via Office.js (read-only)
- No custom styling (uses Word's default comment style)

**Workaround:** Use highlighting + comments combined:
```javascript
// 1. Highlight the problematic text
range.font.highlightColor = '#FFFF00';

// 2. Insert comment at paragraph level
range.insertComment('AEGIS: Grammar issue - missing article "the"');
```

#### Version Compatibility

**Version Support:**
- Word 2016: Basic support (some APIs unavailable)
- Word 2019: Full support
- Office 365: Full support (most features)
- Word Online: Full support in modern browsers

**Incompatible:**
- Word 2013 or earlier
- Word Starter Edition
- Office for Mac (older versions)

---

## Part 6: AEGIS API Integration

### 6.1 Required API Endpoints

Existing AEGIS endpoints already support add-in needs:

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/review` | POST | Submit document text for review | Existing |
| `/api/version` | GET | Get AEGIS version | Existing |
| `/api/checkers` | GET | List available checkers | Existing |
| `/api/config` | GET | Get checker configuration | Existing |

### 6.2 Add-in Integration Points

#### A. Document Upload & Review

Currently, AEGIS `/api/review` expects file upload (multipart/form-data). For Word add-in:

**Current endpoint:**
```
POST /api/upload
Content-Type: multipart/form-data
file: [binary DOCX file]
→ Response: {word_count, issues[], ...}
```

**Word add-in approach:**
```javascript
// Extract text from Word document
const text = document.body.text;

// Send as JSON (not file)
const response = await fetch('https://localhost:7050/api/review', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    content: text,
    filename: document.filename,
    format: 'text'
  })
});
```

**Required modification to app.py:**

Add `/api/review` endpoint that accepts JSON content:

```python
@app.route('/api/review-text', methods=['POST'])
def review_text():
    """Review plain text content (for Word add-in)."""
    data = request.json
    content = data.get('content', '')
    filename = data.get('filename', 'document.txt')

    # Create temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Run AEGIS review on content
        engine = AEGISEngine()
        results = engine.review_document(temp_path)
        return jsonify(results)
    finally:
        os.unlink(temp_path)
```

#### B. Results Format Mapping

AEGIS returns issue structure:
```json
{
  "issue_id": "CHK_001",
  "category": "grammar",
  "severity": "high",
  "message": "Missing article",
  "snippet": "system requires user",
  "paragraph_index": 5,
  "line_number": 12
}
```

Word add-in renders:
```javascript
function formatIssue(issue) {
  const severityColor = {
    'high': '#FF0000',
    'medium': '#FFA500',
    'low': '#FFFF00'
  };

  return {
    text: issue.snippet,
    comment: `[${issue.severity.toUpperCase()}] ${issue.message}`,
    highlightColor: severityColor[issue.severity]
  };
}
```

### 6.3 Backward Compatibility

**No breaking changes needed:** AEGIS /api/upload still works for browser
**New endpoint:** `/api/review-text` for add-in (separate, doesn't affect existing functionality)
**Wrapper proxy:** Routes requests appropriately based on content-type

---

## Part 7: Implementation Roadmap

### Phase 1: MVP (Minimum Viable Product)

**Goal:** Basic document review in Word without admin

**Timeline:** 2-3 weeks

**Deliverables:**

1. ✅ **Setup & Infrastructure** (Week 1)
   - [ ] Generate self-signed certificate
   - [ ] Create wrapper_https.py HTTPS proxy
   - [ ] Verify certificate trust setup works
   - [ ] Create manifest.xml template

2. ✅ **Minimal Task Pane** (Week 1-2)
   - [ ] Basic HTML structure (task-pane.html)
   - [ ] Office.js initialization
   - [ ] "Scan Document" button
   - [ ] Plain text extraction from Word

3. ✅ **AEGIS Integration** (Week 2)
   - [ ] Add /api/review-text endpoint to app.py
   - [ ] Task pane calls API with document text
   - [ ] Display results as HTML list
   - [ ] Test end-to-end in Word

4. ✅ **Sideloading Setup** (Week 2-3)
   - [ ] Create shared folder manifest discovery
   - [ ] Document user installation steps
   - [ ] Test on fresh Windows VM (no admin)
   - [ ] Provide PowerShell script for automated setup

**Success Criteria:**
- [ ] User can sideload add-in with no admin
- [ ] "Scan Document" works end-to-end
- [ ] Issues display in task pane
- [ ] Certificate setup documented clearly

### Phase 2: Full Integration

**Goal:** Production-ready with comments and highlighting

**Timeline:** 2-3 additional weeks

**Deliverables:**

1. ✅ **Advanced Document Integration**
   - [ ] Implement snippet search and highlighting
   - [ ] Insert comments at issue locations
   - [ ] "Apply All" button for batch operations
   - [ ] Test comment positioning accuracy

2. ✅ **Enhanced UI**
   - [ ] Filter issues by severity/category
   - [ ] Search/jump to specific issues
   - [ ] Dark mode support
   - [ ] Responsive design for narrow task pane

3. ✅ **Settings & Preferences**
   - [ ] Checker selection (which checkers to run)
   - [ ] Severity threshold filtering
   - [ ] Save settings locally
   - [ ] Multi-document sessions

4. ✅ **Stability & Error Handling**
   - [ ] Timeout handling for long documents
   - [ ] Network error recovery
   - [ ] CORS error diagnostics
   - [ ] Certificate expiry warnings

5. ✅ **Documentation & Deployment**
   - [ ] User installation guide (PDF + video)
   - [ ] Troubleshooting guide
   - [ ] Admin guide (for org-wide deployment)
   - [ ] Release package (installer or zip)

**Success Criteria:**
- [ ] Comments inserted accurately
- [ ] Highlighting works across document
- [ ] No crashes on large documents
- [ ] Certificate and CORS issues resolved
- [ ] Ready for beta testing

### Phase 3: Future Enhancements

**Optional long-term features:**

- Real-time scanning as user types (requires architecture change)
- Auto-fix suggestions with one-click apply
- Style guide integration (track compliance)
- Collaborative review (multiple reviewers)
- Track changes integration
- DOCX-native parsing (preserve formatting)
- Cloud-based AEGIS (no localhost requirement)
- Offline mode with sync

---

## Part 8: Security & Trust Considerations

### 8.1 Certificate Management

#### Self-Signed Certificate Risks

**Risk:** Self-signed certificates are not trusted by default
**Mitigation:**
- User explicitly imports certificate (one-time)
- Clear documentation with screenshots
- Browser warning is normal and expected
- No data transmission risk (localhost only)

**Certificate Rotation:**
```bash
# Certificates expire after 365 days
# Wrapper should detect and warn user:

def check_certificate_expiry():
    import ssl
    from datetime import datetime, timedelta

    cert = ssl.DER_cert_to_PEM_cert(
        open('cert.pem', 'rb').read()
    )

    # Parse expiry date
    # If within 30 days: show warning dialog
```

#### Certificate Pinning

For enhanced security, Word add-in could pin certificate:

```javascript
// task-pane.js
const EXPECTED_CERT_FINGERPRINT = 'abc123def456...';

async function verifyAEGISCertificate() {
  const response = await fetch('https://localhost:7050/api/version');
  const certFingerprint = response.headers.get('X-Cert-Fingerprint');

  if (certFingerprint !== EXPECTED_CERT_FINGERPRINT) {
    console.error('Certificate mismatch - possible MITM attack');
    return false;
  }

  return true;
}
```

### 8.2 Network Security

#### localhost Isolation

**Assumption:** localhost:5050 and 7050 only accessible from same machine
**Validation:**
- AEGIS listens on 127.0.0.1 (not 0.0.0.0)
- Network access restricted to local loopback
- No exposure to external network

#### CORS Policy

Wrapper sets restrictive CORS headers:

```python
# wrapper_https.py
@https_app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://localhost:7050'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response
```

### 8.3 Data Privacy

#### Document Content Scope

**Important:** Word add-in has access to entire document content

**Privacy Implications:**
- Document text sent to localhost AEGIS process
- AEGIS stores analyzed documents in local database
- No cloud transmission (stays on machine)
- User controls what documents are scanned

**User Control:**
- Add-in only runs when user clicks "Scan"
- Can review document before scanning
- Can exclude specific documents
- Can clear history from settings

#### AEGIS Backend Security

No changes needed to existing AEGIS security:
- No public network exposure
- localhost access only
- Same CSRF/authentication as browser version
- Session handling unchanged

---

## Part 9: Installation & Distribution

### 9.1 Distribution Package Contents

```
AEGIS-Word-Addin-v1.0.zip
├── README.md
│   ├── Quick Start
│   ├── System Requirements
│   └── Troubleshooting
├── INSTALLATION.md
│   ├── Step-by-step guide (with screenshots)
│   ├── Method A: Shared Folder
│   ├── Method B: PowerShell Registry
│   └── Method C: SharePoint (optional)
├── setup.ps1
│   ├── Automated installation script
│   ├── No admin required
│   └── Optional: Generate certificate
├── manifest.xml
│   └── Ready-to-use, update SourceLocation if needed
├── word_addin/
│   ├── task-pane.html
│   ├── task-pane.js
│   ├── task-pane.css
│   ├── aegis-integration.js
│   ├── document-parser.js
│   ├── issue-renderer.js
│   └── cert.pem (self-signed certificate)
├── wrapper_https.py
│   └── Standalone HTTPS proxy
├── TROUBLESHOOTING.md
│   ├── Common issues
│   ├── Solution steps
│   └── Log file locations
└── VIDEO_WALKTHROUGH.mp4 (optional)
    └── 5-minute installation guide
```

### 9.2 Installation Methods for End Users

#### Automatic Installation (PowerShell)

```powershell
# setup.ps1 - One-click installation
# Run as: powershell -ExecutionPolicy Bypass -File setup.ps1

param(
    [switch]$SkipCertificate,
    [string]$ManifestPath = "C:\AEGIS\manifest.xml"
)

# Step 1: Verify Word is installed
$wordApp = Get-Process WINWORD -ErrorAction SilentlyContinue
if (-not $wordApp) {
    Write-Host "Word is not running. Please open Word first." -ForegroundColor Yellow
    exit
}

# Step 2: Generate certificate if needed
if (-not $SkipCertificate) {
    Write-Host "Installing certificate..." -ForegroundColor Green

    # Check if cert.pem exists
    if (-not (Test-Path "cert.pem")) {
        Write-Host "Certificate not found. Please extract cert.pem from the package." -ForegroundColor Red
        exit
    }

    # Import certificate into Trusted Root (user store, no admin needed)
    $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2("cert.pem")
    $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
    $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
    $store.Add($cert)
    $store.Close()

    Write-Host "Certificate installed in CurrentUser store" -ForegroundColor Green
}

# Step 3: Copy manifest.xml
Write-Host "Setting up add-in manifest..." -ForegroundColor Green
$manifestDir = Split-Path -Path $ManifestPath
if (-not (Test-Path $manifestDir)) {
    New-Item -ItemType Directory -Path $manifestDir -Force | Out-Null
}

Copy-Item "manifest.xml" -Destination $ManifestPath -Force
Write-Host "Manifest copied to $ManifestPath" -ForegroundColor Green

# Step 4: Add to Word trusted catalogs
Write-Host "Registering add-in with Word..." -ForegroundColor Green

$registryPath = "HKCU:\Software\Microsoft\Office\16.0\WEF\Catalogs\UserDefinedWebCatalogs"
if (-not (Test-Path $registryPath)) {
    New-Item -Path $registryPath -Force | Out-Null
}

$catalogUrl = "file:///" + $manifestDir.Replace("\", "/") + "/"
New-ItemProperty -Path $registryPath -Name "AEGIS" -Value $catalogUrl -Force | Out-Null

Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart Microsoft Word"
Write-Host "2. Open a document"
Write-Host "3. Go to Insert → My Add-ins → AEGIS"
Write-Host "4. Click to install"
Write-Host ""
Write-Host "Make sure AEGIS is running on localhost:5050"
```

#### Manual Installation (Shared Folder Method)

```
1. Copy manifest.xml to C:\AEGIS\manifest.xml

2. In Word:
   File → Options → Trust Center

3. Click "Trusted Add-in Catalogs"

4. Add Catalog:
   file:///C:/AEGIS/

5. Restart Word

6. Insert → My Add-ins → AEGIS
```

### 9.3 Distribution Scenarios

#### Scenario A: Individual Users (Self-Service)

- Provide zip file on website/documentation
- Users run setup.ps1 or follow manual steps
- No admin required
- Updates: re-run setup.ps1 with new files

#### Scenario B: Small Teams (Shared Folder)

- Place manifest.xml on network share
- Users point Word to that share
- Centralized update: replace manifest on share
- No client-side changes needed

#### Scenario C: Enterprise (Microsoft 365 Admin Center)

- Enterprise admin uploads manifest to M365
- Auto-deploys to all users (admin can control)
- Requires M365 subscription
- Out of scope for Phase 1 (user sideloading only)

---

## Part 10: Testing & Quality Assurance

### 10.1 Test Matrix

| Test Case | Phase 1 | Phase 2 | Notes |
|-----------|---------|---------|-------|
| Sideload on Windows 10/11 (no admin) | ✓ | ✓ | Primary scenario |
| Sideload on Mac (no admin) | - | ✓ | Different process |
| Document scan (small doc <1MB) | ✓ | ✓ | Performance baseline |
| Document scan (large doc >10MB) | - | ✓ | Timeout handling |
| Certificate warning handling | ✓ | ✓ | User experience |
| CORS error recovery | - | ✓ | Network resilience |
| Issue highlighting accuracy | - | ✓ | Core functionality |
| Comment insertion edge cases | - | ✓ | Multiple issues per para |
| Character encoding (UTF-8) | ✓ | ✓ | International docs |
| Dark mode task pane | - | ✓ | UI polish |

### 10.2 Test Environment Setup

```
VM Configuration:
- Windows 11 (clean install)
- Office 365 subscription (latest Word)
- No elevated privileges (standard user account)
- Python 3.9+ for AEGIS backend
- Network: Localhost only (no external network)

Test Documents:
- Small sample.docx (5KB, 100 words)
- Medium report.docx (500KB, 10,000 words)
- Large spec.docx (5MB, 50,000 words)
- Special chars: Chinese, Arabic, emoji
- Complex formatting: tables, headers, footers
```

### 10.3 Acceptance Criteria

#### Phase 1 MVP Acceptance

- [ ] Add-in loads without admin privileges
- [ ] Certificate can be installed by standard user
- [ ] "Scan Document" button scans document and displays results
- [ ] No unhandled errors in console
- [ ] Installation documented and tested
- [ ] Manifest.xml is valid XML
- [ ] HTTPS proxy starts without errors

#### Phase 2 Full Integration

- [ ] Comments inserted at correct locations (90%+ accuracy)
- [ ] Highlighting displays for all issue types
- [ ] No crashes on documents >10MB
- [ ] CORS errors are handled gracefully
- [ ] Settings persist across sessions
- [ ] Troubleshooting guide covers 90% of issues
- [ ] Performance: scan <5 seconds for typical document

---

## Part 11: Limitations Summary & Decision Matrix

### 11.1 Constraint Comparison

| Constraint | VSTO | COM | Office.js |
|-----------|------|-----|-----------|
| Admin required | ✓ | ✓ | ✗ |
| Cross-platform | ✗ | ✗ | ✓ |
| Development difficulty | Hard | Very Hard | Easy |
| Native performance | ✓ | ✓ | ✗ (slight) |
| Easy to update | ✗ | ✗ | ✓ |
| HTTPS required | ✗ | ✗ | ✓ |

**Verdict:** Office.js is the only viable choice for a no-admin solution.

### 11.2 Known Issues & Workarounds

| Issue | Impact | Workaround |
|-------|--------|-----------|
| Certificate expires after 365 days | User can't connect | Renewal script or auto-renewal |
| HTTPS self-signed certificate | Trust setup required | Clear documentation with screenshots |
| Document text extracted as plain | Loss of formatting | Use Office.js XML API for tables |
| Comments not deletable via API | User must manually delete | Document limitation in user guide |
| User gesture required for edits | Can't auto-apply all fixes | Require manual "Apply" button click |
| Snippets may match wrong location | Issue highlighting inaccurate | Improve search with paragraph context |
| Localhost only (no cloud) | No multi-device access | Out of scope for Phase 1 |

### 11.3 Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Certificate trust issues | Medium | Low | Clear setup guide, automated script |
| CORS blocking all requests | Low | High | Thorough testing, proxy verification |
| Document scan timeout (large files) | Medium | Medium | Timeout handling, progress indicator |
| Issue location search fails | Medium | Medium | Improve snippet matching algorithm |
| Word version incompatibility | Low | Medium | Test on Word 2016+, document min versions |

---

## Part 12: Configuration & Customization

### 12.1 Manifest.xml Customization

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OfficeApp xmlns="http://schemas.microsoft.com/office/appforoffice/1.1">
  <Id>12345678-1234-1234-1234-123456789012</Id>  <!-- CHANGE THIS GUID -->
  <Version>1.0.0.0</Version>
  <ProviderName>Your Organization</ProviderName>
  <DefaultLocale>en-US</DefaultLocale>

  <DisplayName DefaultValue="AEGIS Document Review"/>
  <Description DefaultValue="AI-powered technical writing review directly in Word"/>

  <Hosts>
    <Host Name="Document"/>
  </Hosts>

  <DefaultSettings>
    <!-- CHANGE THIS URL if using different server/port -->
    <SourceLocation DefaultValue="https://localhost:7050/task-pane.html"/>
  </DefaultSettings>

  <Permissions>
    <Permission>ReadWriteDocument</Permission>
  </Permissions>

  <!-- Optional: Brand customization -->
  <VersionOverrides xmlns="http://schemas.microsoft.com/office/appforoffice/1.1">
    <Hosts>
      <Host xsi:type="Document">
        <DesktopFormFactor>
          <GetStarted>
            <Title>Get started with AEGIS</Title>
            <Description>Click the button to begin</Description>
            <LearnMoreUrl>https://aegis-docs.example.com</LearnMoreUrl>
          </GetStarted>
        </DesktopFormFactor>
      </Host>
    </Hosts>
  </VersionOverrides>
</OfficeApp>
```

### 12.2 Configuration Files

#### config.json (in word_addin/)

```json
{
  "api": {
    "endpoint": "https://localhost:7050/api/review-text",
    "timeout": 30000,
    "retryAttempts": 3
  },
  "ui": {
    "darkMode": "auto",
    "taskPaneWidth": 400,
    "maxIssuesDisplay": 100
  },
  "document": {
    "autoExtract": true,
    "highlightColor": "FFFF00",
    "commentPrefix": "AEGIS"
  },
  "checkers": {
    "enabled": [
      "grammar",
      "clarity",
      "consistency"
    ],
    "severityFilter": "low"
  }
}
```

---

## Part 13: Success Metrics & KPIs

### 13.1 Phase 1 Success Metrics

```
Installation Success:
- 95%+ successful installations without admin
- <5 minutes to install (with clear instructions)
- <5% user support issues related to installation

Functionality:
- 100% of documents scanned successfully
- 99%+ uptime of HTTPS proxy
- <30 second scan time for typical documents

Quality:
- 0 unhandled JavaScript errors in console
- 0 certificate/CORS issues after initial setup
- User satisfaction rating ≥ 4/5
```

### 13.2 Phase 2 Success Metrics

```
Accuracy:
- 95%+ accuracy of issue highlighting
- 95%+ accuracy of comment insertion location
- 90%+ user agreement with issue detection

Performance:
- 90%+ of documents scanned in <5 seconds
- <100MB memory usage for add-in
- <1MB memory per open comment

Adoption:
- 50%+ of target users installed
- 30%+ weekly active usage
- <5% crash/error rate in production
```

---

## Part 14: Conclusion & Recommendations

### 14.1 Key Findings

1. **Office.js is the only viable path** for no-admin Word integration with AEGIS
2. **Minimal AEGIS backend changes needed** — mostly HTTPS wrapper and new API endpoint
3. **Sideloading is feasible without admin** using either shared folder or user registry method
4. **Self-signed certificate setup is the primary UX hurdle** — needs clear documentation
5. **Phase 1 MVP is achievable in 2-3 weeks** with basic functionality
6. **Phase 2 adds polish and full integration** (additional 2-3 weeks)

### 14.2 Recommended Next Steps

1. **Immediate (Next Session)**
   - Create word_addin/ directory structure
   - Generate self-signed certificate
   - Build minimal task-pane.html + task-pane.js
   - Test Office.js "Hello World" in Word

2. **Short-term (1-2 Weeks)**
   - Implement wrapper_https.py HTTPS proxy
   - Add /api/review-text endpoint to app.py
   - Connect task pane to AEGIS backend
   - Test end-to-end scan functionality

3. **Medium-term (2-4 Weeks)**
   - Implement comment insertion and highlighting
   - Create comprehensive setup guide
   - Test on multiple Windows 10/11 VMs
   - Beta test with small user group

4. **Long-term (Month 2+)**
   - Full UI polish and feature completeness
   - Enterprise distribution setup
   - Cloud-based AEGIS option (Phase 3)
   - Mobile integration (Word Online)

### 14.3 Critical Success Factors

**Must Have:**
- ✅ Zero admin privilege requirement
- ✅ Clear, tested installation process
- ✅ Reliable HTTPS certificate handling
- ✅ Full integration with existing AEGIS backend
- ✅ Comprehensive troubleshooting documentation

**Should Have:**
- Accurate issue highlighting
- Comment insertion at correct locations
- Good performance on large documents
- Dark mode support

**Nice to Have:**
- Real-time scanning as user types
- Auto-fix suggestions
- Offline mode
- Cloud-based AEGIS option

### 14.4 Go/No-Go Decision

**Recommendation: GO** ✅

Office.js web-based approach is:
- Technically feasible
- No admin required (solves primary constraint)
- Minimal impact on existing AEGIS codebase
- Clear development path
- Reasonable timeline and complexity

Proceed with Phase 1 implementation.

---

## Appendix A: References & Resources

### Office.js Documentation
- [Office.js API Reference](https://docs.microsoft.com/en-us/javascript/api/office)
- [Word API Guide](https://docs.microsoft.com/en-us/javascript/api/word)
- [Office Add-ins Platform Overview](https://docs.microsoft.com/en-us/office/dev/add-ins/overview/office-add-ins)

### Manifest & Deployment
- [Add-in Manifest XML Format](https://docs.microsoft.com/en-us/office/dev/add-ins/develop/add-in-manifest)
- [Sideload Office Add-ins for Testing](https://docs.microsoft.com/en-us/office/dev/add-ins/testing/test-debug-office-add-ins)
- [Centralized Deployment via Microsoft 365](https://docs.microsoft.com/en-us/microsoft-365/admin/manage/manage-deployment-of-add-ins)

### Security & HTTPS
- [Self-Signed Certificates for Development](https://docs.microsoft.com/en-us/azure/cloud-services/cloud-services-certs-create)
- [CORS in Office Add-ins](https://docs.microsoft.com/en-us/office/dev/add-ins/develop/cors)
- [Secure Your Add-in](https://docs.microsoft.com/en-us/office/dev/add-ins/concepts/security-considerations)

### Tools
- [Office Script Lab](https://docs.microsoft.com/en-us/office/dev/scripts/overview/excel) — Testing environment
- [Yo Office Generator](https://github.com/OfficeDev/generator-office) — Project scaffolding
- [Office Add-ins validator](https://docs.microsoft.com/en-us/office/dev/add-ins/testing/troubleshoot-manifest)

---

## Appendix B: Sample Code

### Complete task-pane.js Example

```javascript
/*
 * AEGIS Word Add-in - Task Pane JavaScript
 * Handles Office.js integration and AEGIS API communication
 */

const CONFIG = {
  API_ENDPOINT: 'https://localhost:7050/api/review-text',
  API_TIMEOUT: 30000
};

Office.onReady(async (info) => {
  if (info.host === Office.HostType.Word) {
    console.log('AEGIS add-in loaded');
    setupUI();
  }
});

async function setupUI() {
  document.getElementById('scan-btn').addEventListener('click', scanDocument);
  document.getElementById('apply-btn').addEventListener('click', applyResults);
  document.getElementById('settings-btn').addEventListener('click', showSettings);
}

async function scanDocument() {
  try {
    showStatus('Extracting document...');

    await Word.run(async (context) => {
      const body = context.document.body;
      body.load('text');
      await context.sync();

      const documentText = body.text;

      showStatus('Sending to AEGIS...');
      const results = await sendToAEGIS(documentText);

      window.lastResults = results;
      displayResults(results);
      showStatus('Scan complete');
    });
  } catch (error) {
    handleError(error);
  }
}

async function sendToAEGIS(documentText) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT);

  try {
    const response = await fetch(CONFIG.API_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: documentText,
        filename: 'document.docx',
        format: 'text'
      }),
      signal: controller.signal
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

function displayResults(results) {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = `
    <h3>Found ${results.issues?.length || 0} issues</h3>
    <ul>
      ${(results.issues || []).map((issue, idx) => `
        <li data-idx="${idx}" class="issue-${issue.severity}">
          <strong>${issue.category}</strong>: ${issue.message}
          <code>${truncate(issue.snippet, 50)}</code>
        </li>
      `).join('')}
    </ul>
    ${results.issues?.length > 0 ? '<button id="apply-btn">Apply Fixes</button>' : ''}
  `;

  document.getElementById('apply-btn')?.addEventListener('click', applyResults);
}

async function applyResults() {
  if (!window.lastResults?.issues) return;

  try {
    showStatus('Applying fixes...');

    await Word.run(async (context) => {
      for (const issue of window.lastResults.issues) {
        // Highlight the issue
        const searchResults = context.document.body.search(
          issue.snippet,
          { matchCase: false }
        );
        searchResults.load('items');
        await context.sync();

        if (searchResults.items.length > 0) {
          const range = searchResults.items[0];
          range.font.highlightColor = getSeverityColor(issue.severity);
          range.insertComment(`AEGIS: ${issue.message}`);
        }
      }

      await context.sync();
    });

    showStatus('Fixes applied');
  } catch (error) {
    handleError(error);
  }
}

function getSeverityColor(severity) {
  const colors = { high: '#FF0000', medium: '#FFA500', low: '#FFFF00' };
  return colors[severity] || '#FFFF00';
}

function showStatus(message) {
  document.getElementById('status').textContent = message;
}

function handleError(error) {
  console.error('AEGIS Error:', error);
  const msg = error.message === 'The operation timed out'
    ? 'Document scan timed out. Try a smaller document.'
    : `Error: ${error.message}`;
  showStatus(msg);
  document.getElementById('status').style.color = 'red';
}

function truncate(str, len) {
  return str.length > len ? str.substring(0, len) + '...' : str;
}
```

---

**Document Created:** 2026-02-15
**Next Review:** Upon completion of Phase 1 implementation
