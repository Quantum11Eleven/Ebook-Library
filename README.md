# Shelfie

Shelfie is an offline-first PDF library manager built with Python and PySide6. It lets you import, organize, read, and listen to your PDF collection without leaving your desktop. The project implements the architecture, data model, and workflows captured in `docs/SHELFIE_PROMPT.md` and the Codex Build Runbook.

## Features

- Drag-and-drop PDF import with hashing, deduplication, and cover extraction.
- SQLite database storing books, genres, tags, reading progress, highlights, and TTS preferences.
- Library grid/list views with filtering powered by Qt's model-view architecture.
- Embedded PDF reader using PyMuPDF with bookmarks, highlights, and resume support.
- Text-to-speech service with pluggable backends (Piper and pyttsx3) that remember per-book preferences.

## Getting Started

### Prerequisites

- Python 3.11+
- System packages required by PySide6 and PyMuPDF (consult their documentation for platform specifics).

### Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
python -m pip install -e .
```

### Running Shelfie

```bash
shelfie
```

The `shelfie` command (installed via the project's console script entry point) launches the entire application — UI, import pipeline, and TTS services — in one shot. If you prefer not to install the package, run `python -m shelfie` to achieve the same all-in-one startup. The first launch initializes the SQLite database and creates a `ShelfieLibrary` directory inside your home folder for imported books and cover assets.

### Bundling into a single executable

To distribute Shelfie as a one-click binary, use PyInstaller's one-file mode:

```bash
pyinstaller --name shelfie --onefile --windowed src/shelfie/__main__.py
```

The generated executable launches the same unified entry point, so double-clicking it spins up the UI and all background services without any additional scripts.

### Running Tests

```bash
pytest
```

## Project Layout

```
src/
  shelfie/
    app.py
    database/
      __init__.py
      schema.sql
    importers/
      pipeline.py
    models/
      library_model.py
    ui/
      main_window.py
      library_view.py
      reader_view.py
    tts/
      base.py
      piper_backend.py
      pyttsx_backend.py
    utils/
      filesystem.py
      qt.py
```

Tests live in the `tests/` directory and cover the import pipeline, Qt models, reader persistence, and TTS preference storage.

## Documentation

- [`docs/SHELFIE_PROMPT.md`](docs/SHELFIE_PROMPT.md) — master product brief, architecture plan, and Codex Build Runbook guiding the implementation.

## License

Shelfie is released under the MIT License. See `LICENSE` for details.
