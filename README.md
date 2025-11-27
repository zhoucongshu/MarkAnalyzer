# MarkAnalyzer

This repository contains a PyQt5 GUI app to parse TVP/AGA marks from a TXT and generate an HTML report.

## Build locally (Windows)
```bat
python -m venv venv
venv\Scriptsctivate
python -m pip install --upgrade pip
pip install pyinstaller
pip install -r MarkAnalyzer/requirements.txt
cd MarkAnalyzer
pyinstaller mark_analyzer.py --name MarkAnalyzer --noconsole --onefile
```
The exe will be at `MarkAnalyzer/dist/MarkAnalyzer.exe`.

## Build via GitHub Actions
Push this repo to GitHub (default branch `main`). The workflow at `.github/workflows/build.yml` will build on Windows and publish the `MarkAnalyzer.exe` artifact. Trigger it via **Actions → Build MarkAnalyzer EXE → Run workflow**.
