# Speed-PDF
A desktop speed-reading app for PDFs.

Speed-PDF shows one word at a time in a fixed reading area while also showing the actual PDF page with a live highlight of the current line.

## Features
- One-word-at-a-time reading display (left panel)
- Embedded PDF viewer with live line highlight (right panel)
- Side-by-side layout for reading + context at the same time
- Adjustable speed slider (WPM)
- Start / Stop controls
- Seekable progress slider (jump backward/forward)
- Manual start after loading a file (no auto-play)

## Requirements
- Python 3.10+
- Dependencies in `requirements.txt`

## Quick Start
1. Create and activate a virtual environment.
2. Install dependencies:
	 - `pip install -r requirements.txt`
3. Run the app:
	 - `python app.py`

## How to Use
1. Click **Open PDF** and choose a `.pdf` file.
2. Use the speed slider to set your desired WPM.
3. Click **Start** to begin word-by-word playback.
4. Use the progress slider to seek to any position.
5. Use **Previous Page** / **Next Page** in the PDF panel if needed.

## Configuration
The app reads settings from `config.yaml`.

Current fields:
- `app.title`
- `app.window_width`, `app.window_height`
- `app.min_width`, `app.min_height`
- `reader.wpm_default`
- `reader.wpm_min`, `reader.wpm_max`

Example:

```yaml
app:
	title: Speed-PDF
	window_width: 1100
	window_height: 700
	min_width: 900
	min_height: 550

reader:
	wpm_default: 300
	wpm_min: 100
	wpm_max: 1000
```

## Notes
- Best results come from text-based PDFs.
- Image-only/scanned PDFs may not provide accurate word extraction.
- Very complex layouts (multi-column papers, heavy tables) can reduce line-tracking accuracy.

## Troubleshooting
- If `fitz` cannot be imported, reinstall dependencies in the active environment:
	- `pip install -r requirements.txt`
- If no words appear, the PDF likely has little/no extractable text.

## Build Desktop Installer (Windows)
This repo includes everything needed to build an installable Windows desktop app with:
- `.exe` app build
- installer wizard
- Start Menu shortcut
- optional Desktop shortcut
- app icon
- uninstall entry in Windows Apps

## Does end user need Python installed?
- **If using the installer (`Speed-PDF-Setup.exe`)**: **No**. Python is not required on the user's machine.
- **If running from source (`python app.py`)**: **Yes**, Python 3.10+ is required.
- **If building installer from source**: **Yes**, Python 3.10+ is required on the build machine.

The installer does **not** install Python system-wide. It installs the packaged app only.

### Prerequisites
1. Python 3.10+
2. Inno Setup 6 (for installer creation)
   - During install, allow `iscc` on PATH, or run `iscc` manually from Inno Setup install folder.

### One-command build
From repo root:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
```

### Build output locations
- `dist/Speed-PDF.exe` (portable one-file executable)
- `dist/installer/Speed-PDF-Setup.exe` (installer, if Inno Setup is available)

What this script does:
1. Creates/uses `.venv`
2. Installs runtime + dev dependencies
3. Generates icon at `assets/app.ico`
4. Builds single-file app with PyInstaller (`dist/Speed-PDF.exe`)
5. Builds installer with Inno Setup (`dist/installer/Speed-PDF-Setup.exe`) if `iscc` is available

If Inno Setup is installed but not on PATH, run manually:

```powershell
iscc installer/SpeedPDF.iss
```

### Fresh clone to installer (full sequence)
```powershell
git clone <your-repo-url>
cd Speed-PDF
powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
```

Then distribute:
- `dist/installer/Speed-PDF-Setup.exe` for standard install/uninstall experience
- or `dist/Speed-PDF.exe` for portable use (no installer)

## Install as Desktop App
1. Run `dist/installer/Speed-PDF-Setup.exe`
2. Follow setup wizard
3. Keep **Create a desktop shortcut** checked if you want desktop icon
4. Launch from Start Menu or desktop shortcut

## Uninstall (remove everything installed)
Use either method:
1. **Windows Settings → Apps → Installed apps → Speed-PDF → Uninstall**
2. Or run uninstaller from Start Menu entry

Uninstall removes installed app files, shortcuts, and uninstall entry.

## Dev Notes
- Build artifacts (`dist/`, `build/`, `*.spec`) are gitignored.
- Local environments (`.venv/`) and editor files are gitignored.

## Packaging Files Included
- `scripts/build_windows.ps1` — full build pipeline
- `scripts/generate_icon.py` — generates `assets/app.ico`
- `installer/SpeedPDF.iss` — Inno Setup installer definition
- `requirements-dev.txt` — packaging dependency (`pyinstaller`)
