# Shelfie GUI Scaffold

Shelfie is a PySide6 desktop shell that showcases the planned library and reader experience for the offline-first PDF manager. It ships with a toolbar-driven main window, drag-and-drop library surface, reader placeholder, and a bottom TTS mini-player. A headless CLI fallback is available for sandboxes where PySide6 cannot be installed.

## Quick Start

1. Create and activate a virtual environment.
2. Install the dependencies.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: . .venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Launch the GUI (requires PySide6):

   *Double-click* `BookLibraryApp.py` or run it directly:

```bash
python BookLibraryApp.py
```

   Pass `--headless` when you just want to exercise the CLI wiring from tests:

```bash
python BookLibraryApp.py --headless
```

## What’s Included

- **Toolbar + sidebar navigation** seeded with the genre list you provided.
- **Grid and list views** backed by a lightweight Qt model with drag-and-drop PDF import.
- **Book details dock** for quick metadata review, cover swapping, and delete/read actions.
- **Reader view** that renders PDFs inline with PyMuPDF when available and surfaces guidance otherwise.
- **Bottom TTS bar UI** exposing voice, speed, and pitch controls (UI only).
- **Context menus and status toasts** for import, delete, and navigation feedback.

## Tests

The automated checks run without PySide6:

```bash
pytest
```

## Project Layout

```
BookLibraryApp.py
src/
  shelfie/
    ... (modular app scaffold retained for future expansion)
```

Additional planning material—including the Codex Build Runbook and the UI/UX blueprint—lives in `docs/SHELFIE_PROMPT.md`.
