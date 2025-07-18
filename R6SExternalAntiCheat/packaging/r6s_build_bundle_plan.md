# Build Plan

How to zip and structure the project.
# 📦 R6SExternalAntiCheat — Build Bundle Plan (Fully Detailed)

> This guide walks you through setting up, compiling, and packaging the full R6S External Anti-Cheat system. It includes script layout, PyInstaller compilation, NSIS installer building, and GitHub organization.

---

## 📁 Directory Structure

```
R6SExternalAntiCheat/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── scripts/
│   ├── r6s_guard.py
│   ├── r6s_input_tracer.py
│   ├── r6s_alert_viewer.py
│   ├── r6s_local_runner.py
│   ├── r6s_overlay_watcher.py
│   ├── r6s_screen_capture.py
│   ├── r6s_uploader.py
├── packaging/
│   ├── r6s_packaging_checklist.md
│   ├── r6s_build_bundle_plan.md
│   └── r6s_installer_script.nsi
├── installer/
│   ├── r6s_installer.nsi
│   └── icons/
│       └── r6s_icon.ico *(optional)*
├── build/
│   └── *.exe (compiled files go here)
```

---

## 🐍 Step 1: Install Python Requirements
Install all dependencies using pip:

```bash
pip install -r requirements.txt
```

### requirements.txt
```text
psutil
pyautogui
pillow
requests
pywin32
```

---

## ⚙ Step 2: Compile Python Scripts into EXEs
Use PyInstaller to compile each script:

```bash
pip install pyinstaller

pyinstaller --noconsole --onefile scripts/r6s_guard.py
pyinstaller --noconsole --onefile scripts/r6s_input_tracer.py
pyinstaller --noconsole --onefile scripts/r6s_alert_viewer.py
pyinstaller --noconsole --onefile scripts/r6s_local_runner.py
pyinstaller --noconsole --onefile scripts/r6s_overlay_watcher.py
pyinstaller --noconsole --onefile scripts/r6s_screen_capture.py
pyinstaller --noconsole --onefile scripts/r6s_uploader.py
```

### Output:
Move `.exe` files from `dist/` into `build/`:
```bash
mkdir build
move dist\*.exe build\
```

---

## 🧰 Step 3: Build the Windows Installer
Use NSIS to compile the installer:

### 🛠 Requirements:
- [Download NSIS](https://nsis.sourceforge.io/Download)

### 📜 Compile Installer
1. Open NSIS
2. Load `installer/r6s_installer.nsi`
3. Click **Compile**

### 🎯 Output:
Creates `R6S-AntiCheat-Installer.exe`

---

## 🧪 Step 4: Test and Run
1. Run `R6S-AntiCheat-Installer.exe`
2. It installs the system to `C:\Program Files\R6SExternalAC`
3. Automatically launches the runner and opens the alert viewer

---

## 🌐 Step 5: GitHub Deployment
### ✅ Upload These Files:
- `scripts/`
- `packaging/`
- `installer/`
- `README.md`, `LICENSE`, `.gitignore`, `requirements.txt`

### 🛠 Optional CI Automation:
Add `.github/workflows/build.yml` to auto-compile and package on every push (generated separately)

---

## 📦 Final Export Command (Manual)
To zip everything up:
```bash
zip -r R6SExternalAntiCheat.zip R6SExternalAntiCheat/
```

---

## ✅ Recap
| Task                          | Status |
|-------------------------------|--------|
| All scripts written           | ✅     |
| `.exe` files compiled         | ✅     (after PyInstaller)
| Installer built via NSIS      | ✅     (optional icon supported)
| GitHub folder structure ready | ✅     |
| Local testing supported       | ✅     |
| GUI alert viewer included     | ✅     |

---
