# AEGIS Packaging - Windows Installer

## What's In This Folder

```
packaging/
├── install_aegis.bat          # Main installer (double-click to run)
├── python-3.10.11-embed-amd64.zip  # Embedded Python runtime (~8MB)
├── get-pip.py                 # pip bootstrapper
├── requirements-windows.txt   # Full Windows dependency list
├── requirements-core.txt      # Core deps (no ML)
├── wheels/                    # Pre-built Windows wheels (126 packages)
│   ├── torch_split/           # PyTorch split into <50MB parts
│   │   ├── torch_part_aa
│   │   ├── torch_part_ab
│   │   └── torch_part_ac
│   ├── reassemble_torch.bat   # Reassembles torch wheel
│   └── *.whl                  # All other dependency wheels
└── README.md                  # This file
```

## For End Users

### Installation

1. Download and unzip the AEGIS package
2. Double-click `install_aegis.bat`
3. Choose your install location (or press Enter for default)
4. Wait for installation to complete (~3-5 minutes)
5. AEGIS desktop shortcut will be created automatically

### Requirements

- Windows 10 or Windows 11 (64-bit)
- No admin privileges needed
- No Python installation needed (embedded)
- ~800MB disk space

### What the Installer Does

1. Extracts Python 3.10.11 embedded runtime
2. Enables pip in embedded Python
3. Reassembles large wheel files (PyTorch was split for GitHub)
4. Installs all 126 dependencies from local wheels (fully offline)
5. Copies AEGIS application files
6. Creates launcher scripts (AEGIS.bat, Restart-AEGIS.bat)
7. Creates desktop shortcut
8. Creates uninstaller

### After Installation

- **Start**: Double-click `AEGIS` shortcut on desktop
- **Restart**: Run `Restart-AEGIS.bat` in install folder
- **Uninstall**: Run `Uninstall-AEGIS.bat` in install folder

## For Developers

### Rebuilding Wheels

To re-download all wheels from scratch:

```bash
pip download --platform win_amd64 --python-version 310 --only-binary :all: --no-deps -r requirements-windows.txt -d wheels/
```

### Large File Handling

PyTorch CPU wheel is ~109MB (exceeds GitHub's 100MB file limit), so it's split into 3 parts under `wheels/torch_split/`. The installer reassembles them automatically. To split manually:

```bash
split -b 49M torch-*.whl torch_part_
```

### Testing the Installer

On a clean Windows machine:
1. Copy the entire `packaging/` folder
2. Run `install_aegis.bat`
3. Verify AEGIS starts at http://localhost:5050
