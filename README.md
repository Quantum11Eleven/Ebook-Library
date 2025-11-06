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

   You can still launch via the package entry point if you prefer:

```bash
python -m src.shelfie.main
```

   Run in headless mode (no PySide6 required) with either entry point:

```bash
python BookLibraryApp.py --headless
# or
python -m src.shelfie.main --headless
```

## What’s Included

- **Toolbar + sidebar navigation** seeded with the genre list you provided.
- **Grid and list views** with demo book cards plus drag-and-drop import stubs.
- **Reader view shell** with zoom/theme controls ready for future PyMuPDF wiring.
- **Bottom TTS bar UI** exposing voice, speed, and pitch controls (UI only).
- **Status toasts** driven by a shared signal hub.
- **Headless CLI stub** to exercise flows in CI without GUI bindings.

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
    __init__.py
    __main__.py
    bootstrap.py
    cli_stub.py
    main.py
    ui/
      dialogs.py
      library_view.py
      main_window.py
      reader_view.py
      styles.qss
      tts_bar.py
    utils/
      __init__.py
      signals.py
```

Additional planning material—including the Codex Build Runbook and the UI/UX blueprint—lives in `docs/SHELFIE_PROMPT.md`.
