# Shelfie

Shelfie is an offline-first PDF library manager built with Python and PySide6. It lets you import, organize, read, and listen to your PDF collection without leaving your desktop. The project implements the architecture, data model, and workflows captured in `docs/SHELFIE_PROMPT.md` and the Codex Build Runbook.

## Features

- Drag-and-drop PDF import with hashing, deduplication, and cover extraction.
- SQLite database storing books, genres, tags, reading progress, highlights, and TTS preferences.
- Library grid/list views with a top toolbar for instant search, genre filtering, and import shortcuts.
- Embedded PDF reader using PyMuPDF with bookmarks, highlights, and resume support.
- Text-to-speech service with pluggable backends (Piper and pyttsx3) that remember per-book preferences.

## Getting Started

### Prerequisites

- Python 3.11+
- System packages required by PySide6 and PyMuPDF (consult their documentation for platform specifics).

### Installation

Run the helper script to prepare a virtual environment and install Shelfie in editable mode:

```bash
bash scripts/setup_env.sh
```

The script creates `.venv/`, upgrades the core packaging tools, installs the runtime dependencies from `requirements.txt`, and
finishes by installing Shelfie in editable mode so the `shelfie` console entry point is available. If you prefer to perform the
steps manually, run:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
python -m pip install -e .
```

### Running Shelfie

1. Activate your virtual environment (see above).
2. Launch Shelfie from the project root:

   ```bash
   python -m shelfie
   ```

   The same entry point is available via the `shelfie` console script if you installed the project in editable mode.

3. On first launch, Shelfie creates a `ShelfieLibrary` directory in your home folder, seeds the genre list you provided (🚀 Sci-Fi Explorations, 🐉 Epic Fantasy, etc.), and opens the main window.

### What you'll see

- **Top toolbar:** Library/Reader toggle, import button, view switcher (list/grid), global search, and genre filter dropdown.
- **Library view:** Table or card layout showing every book in your database. Drag PDFs anywhere onto this surface (or use the Import button) to ingest them.
- **Reader view:** Displays the selected PDF with zoom controls. Double-click a book in the library to open it here.

If nothing happens after running the command, double-check that your virtual environment is active and review any console errors; double-clicking source files such as `sitecustomize.py` or `conftest.py` will not launch the UI.

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
      seeds.py
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
  - Section 13 now adds a copy-pasteable UI/UX blueprint with ASCII wireframes, Qt object map, interaction specs, and refreshed Codex prompts for scaffolding the interface.

## License

Shelfie is released under the MIT License. See `LICENSE` for details.
