# SHELFIE — Python PDF Book Manager

This document captures the working product vision, architecture plans, and implementation prompts for Shelfie. It serves as a living kit to guide delivery from idea to production.

---

## 1. Product North Star

**Goal:** Build a fast, offline-first desktop application that helps readers organize, read, and listen to PDF books with drag-and-drop import, smart metadata, powerful search, and natural-sounding text-to-speech (including user-recorded voices).

### Non-negotiables

- Drag-and-drop PDF import (single and batch).
- Library grid/list with covers, reading progress, and user-defined categories.
- Embedded PDF reader with zoom, table of contents, bookmarks, highlights, notes, and last-page resume.
- Text-to-speech with selectable voices (local or pre-made) that can play from the current page/selection and remember speed and pitch.
- Private by default: local storage, no uploads unless a user opts in to a future cloud add-on.

### Nice-to-haves (Phase 2+)

- Automatic cover extraction and metadata lookup (title, author, ISBN, year).
- Full-text indexing and semantic search.
- OCR for scanned PDFs.
- Manual collections and rule-based smart collections.
- Reading statistics (time read, pages/day, streaks).
- Quote clipping into a notes vault with highlight export.
- Multi-format add-on support (EPUB/CBZ) through plugins.

---

## 2. Core User Stories (MVP)

- **Import:** “As a reader, I drag folders of PDFs onto the app and they appear with covers and titles automatically.”
- **Organize:** “I assign custom genres and tags; I can filter/sort quickly.”
- **Read:** “I open any book in a built-in reader and resume where I left off.”
- **Listen:** “I hit Play to listen from cursor/selection; I can switch voices and speeds.”
- **Search:** “I search by title/author/tags instantly (phase 1), full-text later (phase 2).”

---

## 3. Architecture & Technology Options

### UI Framework (desktop, cross-platform)

- **PySide6 / Qt** *(recommended)*: Mature toolkit with native feel, strong drag-and-drop, docking, and model-view features.
- **Toga**: Pure Python approach, but less proven for complex PDF workflows.
- **Electron + Python backend**: Highly flexible yet heavier footprint.

### PDF Rendering

- **PyMuPDF (fitz)** *(preferred)*: Fast rendering, TOC access, text extraction, highlighting—ideal for search and TTS synchronization.
- **Alternatives:** PDFium via wrappers or pdf.js inside a webview (requires JS bridge work).

### Data & Indexing

- **SQLite** (extend with FTS5 in phase 2) to store books, files, genres, tags, notes, highlights, reading progress, and TTS preferences.
- Cache covers and thumbnails on disk; store the file paths in the database.

### Text-to-Speech Engines

- **Local (offline):** Piper (lightweight, good quality), Coqui-TTS/XTTS (higher quality with voice cloning), pyttsx3 (system voices, easiest to integrate).
- **Cloud (opt-in):** Azure/Edge TTS, Google Cloud TTS, Amazon Polly, ElevenLabs.

### Packaging

- PyInstaller or Briefcase for single-file/folder builds on Windows, macOS, and Linux.

### Plugin Surface (Phase 2)

- Extensible providers for metadata, file formats, TTS engines, and semantic search.

---

## 4. Data Model (MVP)

Tables

- `books(id, title, author, year, isbn, file_path, file_hash, pages, added_at, updated_at)`
- `book_assets(book_id, cover_path, thumb_path)`
- `genres(id, name)`
- `book_genres(book_id, genre_id)`
- `tags(id, name)` and `book_tags(book_id, tag_id)`
- `reading_state(book_id, last_page, percent, last_opened_at, total_read_minutes)`
- `highlights(id, book_id, page, rect_json, text, color, note, created_at)`
- `settings(key, value)` storing JSON values
- `tts_prefs(book_id, voice_id, speed, pitch, last_position_ms)`

Indexes

- `idx_books_title_author`, `idx_book_tags`, `idx_highlights_text` for phase 1 simple LIKE search; upgrade to FTS5 in phase 2.

---

## 5. File Handling Flow

1. **Drop** files/folders → deduplicate via `file_hash` → copy into `~/Shelfie/Library/YYYY/Title` (or keep links, per user preference).
2. **Extract** basic metadata with PyMuPDF → attempt filename parsing → optional online lookup in later phases.
3. **Cover** creation: render first page → generate thumbnail.
4. **Index**: store title/author (phase 1) and full-text (phase 2) for search.

---

## 6. Text-to-Speech Flow

- Select engine (local or cloud) and voice, then configure speed/pitch.
- From the reader, play from cursor, paragraph, or page with auto-scroll sync.
- Save per-book TTS settings and last playback position.
- Optional: user-provided voice cloning via Coqui XTTS (opt-in).

---

## 7. UX Sketch (MVP)

### Main Window

- **Top bar:** Global search, Import action, View toggle (grid/list), Filters (Genres/Tags), Settings.
- **Left sidebar:** Library, Genres, Collections, Recently Added, In Progress, Finished.
- **Content area:** Book cards showing cover, title, author, progress ring, badges, and context menu actions.

### Reader View

- **Header:** Title, page x/y, zoom controls, fit width, themes (light/dark/sepia).
- **Left panel:** Table of contents.
- **Right panel:** Notes/Highlights.
- **Bottom:** TTS mini-player (Play/Pause, voice selection, speed, progress scrubber).

### Accessibility

- Full keyboard navigation, font scaling, high-contrast themes, and screen-reader-friendly labels.

---

## 8. MVP Milestones (2–3 sprints)

1. **Sprint 1 — Foundation**
   - Project scaffold, database schema, import pipeline (hashing, copy/link choice), cover and thumbnail cache.
   - Library grid/list with sorting and basic filters. Basic settings screen.
2. **Sprint 2 — Reader + TTS**
   - PDF viewer with resume support, bookmarks, simple highlights.
   - Local TTS (pyttsx3 or Piper) with mini-player; read selection/page.
3. **Sprint 3 — Polish**
   - Genre/tag management, quick filters, basic search.
   - Packaging for Windows/macOS, crash logging, autosave.

**Phase 2 — Power Features**

- FTS5 indexing, OCR for scanned PDFs, semantic search, cloud TTS, voice cloning, reading stats, quote export.

---

## 9. Risk & Mitigation

- **Large PDFs slow to render:** Use incremental page caching and pre-render adjacent pages.
- **Mixed scan/text PDFs:** Provide optional on-demand OCR.
- **TTS quality variance:** Ship with one reliable local engine and optional premium connectors.
- **Deduplication edge cases:** Combine hash, size, and path heuristics.

---

## 10. Prompt Library

Reusable prompts for specialized workstreams:

1. **Architecture & Scaffold** — design the project structure, dependencies, schema, import pseudocode, UI outline, and packaging plan.
2. **UI Wireframes → Qt Widgets** — produce PySide6 stubs for the main window, drag-and-drop handling, and model/view integration.
3. **PDF Reader** — implement the ReaderWidget with PyMuPDF, caching, highlights, and resume behavior.
4. **TTS Engine (Local First)** — build a TTSService abstraction with Piper and pyttsx3 backends and integrate with the reader.
5. **Import & Metadata** — hash files, parse metadata, render covers, store results in SQLite, handle duplicates, emit model updates.
6. **Search (Phase 1) & FTS (Phase 2)** — implement LIKE queries, then upgrade to FTS5 for full-text search with snippets.
7. **Packaging & Updates** — deliver PyInstaller specs, code-signing notes, and auto-update strategy with minimized binaries.
8. **QA Scenarios** — draft test cases for duplicates, huge PDFs, scans, corrupt files, drag-and-drop stress, highlight persistence, TTS resume, and packaging smoke tests.

---

## 11. Configurable Settings (MVP)

- Library location (copy versus link files).
- Default view (grid/list), card size, and theme (light/dark/sepia).
- TTS defaults: engine, voice, speed, pitch, with per-book overrides.
- Metadata fetching toggle and provider selection.

---

## 12. Team Inputs (Current)

### Genre List (with icons)

1. 🚀 **Sci-Fi Explorations**
2. 🐉 **Epic Fantasy**
3. 🕵️‍♀️ **Mystery & Thrillers**
4. 📘 **Non-Fiction Insights**
5. 🌱 **Self-Improvement**
6. 🖥️ **Technology & Programming**
7. 🏛️ **Literary Classics**
8. 🎨 **Graphic Novels & Comics**
9. 🧠 **Philosophy & Thought**
10. ✒️ **Poetry & Essays**

### Voice Plan

- Prioritize **local-first** voices for privacy and offline support.
- Ship with **Piper** for high-quality offline synthesis and **pyttsx3** as a lightweight fallback.
- Offer an **opt-in cloud connector** for Azure Neural TTS in phase 2 to unlock premium voices.
- Default voice preference: a warm, neutral-feminine voice with natural pacing; allow speed and pitch adjustments per user.

### Platform Priority

- Target **Windows** first due to user base size and packaging maturity.
- Maintain parallel support for **macOS** to ensure parity for creative professionals.
- Validate Linux builds opportunistically once Windows/macOS installers are stable.

### Branding Vibe

- Keep the name **“Shelfie.”**
- Color palette: deep teal `#0A3D62` (primary), soft coral `#FF6F61` (accent), warm light gray `#F5F5F5` (background).
- Logo concept: a minimal bookshelf silhouette forming the letter “S,” with a subtle page-turn motif to hint at reading and audio.
- Overall tone: modern, cozy, and welcoming—something that feels like a personal reading nook.

---

*Last updated: generated by project assistant; Codex Build Runbook added for guided implementation.*

---

## 13. Codex Build Runbook

Use this runbook when you are ready to turn the Shelfie specification into a working codebase with the help of an AI coding partner such as "Codex" (Cursor, Copilot, Claude, etc.). It captures the end-to-end workflow, required terminal setup, the target folder layout, and copy-ready prompt blocks for each major build stage.

### 13.1 Quickstart Terminal Commands

```bash
# 1) Create and activate a fresh virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2) Upgrade core tooling
python -m pip install --upgrade pip wheel setuptools

# 3) Install base dependencies for the scaffold phase
pip install pyside6 pymupdf pillow python-dotenv

# 4) Initialize the project workspace
mkdir -p shelfie && cd shelfie
git init

# 5) Create initial commit checkpoints as you complete each Codex prompt
git add .
git commit -m "chore: bootstrap shelfie workspace"
```

> Tip: if you are pairing with an AI assistant inside an IDE (e.g., Cursor), keep the runbook open in a split view. After each prompt session, run `pytest` or the relevant command from the generated instructions before committing.

### 13.2 Recommended Folder Structure

```
shelfie/
├── README.md
├── requirements.txt
├── pyproject.toml            # optional; generated during scaffold prompt
├── src/
│   └── shelfie/
│       ├── __init__.py
│       ├── app.py            # application entry point (PySide6)
│       ├── database/
│       │   ├── __init__.py
│       │   └── schema.sql
│       ├── importers/
│       │   ├── __init__.py
│       │   └── pipeline.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── library_model.py
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_window.py
│       │   ├── library_view.py
│       │   └── reader_view.py
│       └── tts/
│           ├── __init__.py
│           ├── base.py
│           ├── piper_backend.py
│           └── pyttsx_backend.py
├── tests/
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_import_pipeline.py
│   └── test_tts.py
└── assets/
    ├── icons/
    └── sample_books/
```

Adjust module names as needed, but keep the overall separation between core app logic, import pipeline, UI components, and TTS backends to stay aligned with the spec.

### 13.3 AI Assistant Prompt Blocks

Paste the following prompts sequentially into your AI coding assistant. Each prompt references the agreed-upon architecture and should result in runnable, testable code chunks. Review, run, and commit after each stage.

**Prompt A — Project Scaffold & Configuration**

```
Role: Senior Python Architect

Design the initial Shelfie project scaffold using Python 3.11, PySide6, PyMuPDF, and SQLite. Deliver:
1. `pyproject.toml` with tool configuration (black, isort, mypy placeholders).
2. `requirements.txt` synchronized with the pyproject dependencies.
3. `src/shelfie/app.py` that bootstraps a PySide6 `QApplication` and main window shell.
4. `src/shelfie/database/schema.sql` defining the MVP tables and indexes from the Shelfie spec.
5. `README.md` quickstart instructions for installing, running, and testing the app.
Keep modules small, include type hints, and ensure the code paths are ready for unit testing.
```

**Prompt B — Import Pipeline & Metadata**

```
Role: Data Pipeline Engineer

Implement the Shelfie import pipeline. Provide:
1. `src/shelfie/importers/pipeline.py` with classes/functions to hash PDFs, deduplicate by hash, copy or link files, extract metadata with PyMuPDF, generate cover thumbnails, and persist rows via SQLite (using the schema from schema.sql).
2. `tests/test_import_pipeline.py` covering hashing, duplicate detection, and metadata persistence.
3. Necessary utility modules (e.g., `src/shelfie/utils/filesystem.py`).
Ensure the API integrates with the library model signals and emits progress events for the UI.
```

**Prompt C — Library UI & Models**

```
Role: Senior Qt Engineer

Create the library user interface. Deliver:
1. `src/shelfie/ui/main_window.py` with a top toolbar (search, import action, view toggle), left sidebar (library, genres, collections), and central stacked widget switching between library grid/list and reader.
2. `src/shelfie/models/library_model.py` implementing a `QAbstractTableModel` (or proxy) that surfaces book metadata, covers, progress, and filters.
3. Drag-and-drop handlers in the main window that forward dropped PDFs to the import pipeline.
4. Tests for the model sorting/filtering logic (`tests/test_library_model.py`).
Favor signals/slots, dependency injection for services, and docstrings describing expected interactions.
```

**Prompt D — Reader View & Highlights**

```
Role: PDF Rendering Specialist

Build `src/shelfie/ui/reader_view.py` backed by PyMuPDF. Include:
- Page rendering with zoom controls and continuous scroll using cached pixmaps.
- Table of contents navigation, bookmark toggling, and highlight creation.
- Persistence hooks for highlights and last-page resume via the database layer.
- Unit tests or integration tests for highlight persistence (`tests/test_reader_highlights.py`).
Optimize rendering by preloading adjacent pages and caching tiles.
```

**Prompt E — Text-to-Speech Service**

```
Role: Audio/TTS Engineer

Implement the TTS subsystem. Provide:
1. `src/shelfie/tts/base.py` defining a `TTSService` protocol with `speak`, `stop`, and `configure_voice` methods plus progress callbacks.
2. `src/shelfie/tts/piper_backend.py` and `src/shelfie/tts/pyttsx_backend.py` implementing the protocol and persisting per-book preferences.
3. Reader integration that exposes play/pause controls in the mini-player and remembers the last playback position in `tts_prefs`.
4. Tests covering preference storage and backend selection (`tests/test_tts_preferences.py`).
Document how to add future cloud connectors via plugins.
```

> Optional follow-ups: reuse the earlier prompt library for search, packaging, and QA once the five Codex prompts land.

---

## 13. UI/UX Blueprint (Copy-Paste Ready)

The following section condenses the latest Canvas planning session into a blueprint you can hand directly to any coding partner or AI assistant.

### 13.1 Visual Layouts

#### Library Window

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Top Toolbar                                                                  │
│ [☰ Library] [Import ▼] [Grid • List] [Search ▢───────────────] [Genre ▼] [⚙] │
├────────────┬──────────────────────────────────────────────────────────────────┤
│ Sidebar    │ Library Grid/List                                                │
│ ┌────────┐ │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │
│ │ Library│ │ │ Cover      │ │ Cover      │ │ Cover      │                   │
│ │ Genres │ │ │ Title      │ │ Title      │ │ Title      │                   │
│ │ Tags   │ │ │ Author     │ │ Author     │ │ Author     │                   │
│ │ Recent │ │ │ Progress ○ │ │ Progress ○ │ │ Progress ○ │                   │
│ │ In Prog│ │ └─────────────┘ └─────────────┘ └─────────────┘                   │
│ │ Finished│ │                                                      Drag PDFs ↑  │
│ └────────┘ │ (List view switches to QTreeView-style rows with cover, badges)  │
└────────────┴──────────────────────────────────────────────────────────────────┘
```

Drag-and-drop overlay: translucent panel saying **“Drop PDFs to import”** with an icon, activated when files hover over the central area.

#### Reader Window

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Header: [⬅ Back] Title | Page 3 / 250 | Zoom - 100% + | Theme: Light ▼        │
├────────────┬──────────────────────────────────────────────┬────────────────────┤
│ TOC Panel  │ PDF Canvas (continuous scroll, current page) │ Notes / Highlights │
│ (tree view)│                                              │ (list + editor)    │
├────────────┴──────────────────────────────────────────────┴────────────────────┤
│ TTS Mini-Player: [▶︎] Voice ▼ Speed ▼ Pitch ▼ [⏹] [Bookmark] [Highlight]      │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 13.2 Qt Class & Object Map

| Component              | Class                | `objectName`            | Notes |
|------------------------|----------------------|-------------------------|-------|
| Main window            | `MainWindow`         | `mainWindow`            | Hosts toolbar, sidebar, stacked views. |
| Top toolbar            | `QToolBar`           | `libraryToolbar`        | Contains actions: `actionImport`, `actionToggleView`, search, genre combo, settings. |
| Global search          | `QLineEdit`          | `searchField`           | Emits `searchSubmitted(str)` signal. |
| Genre filter           | `QComboBox`          | `genreFilter`           | Populated from seeded genres. |
| Sidebar list           | `QListWidget`        | `navigationList`        | Items: Library, Genres, Tags, Recently Added, In Progress, Finished. |
| Library grid view      | `QListView`          | `libraryGrid`           | Uses `LibraryProxyModel` with icon mode. |
| Library list view      | `QTreeView`          | `libraryTable`          | Column headers: Cover, Title, Author, Progress, Added. |
| Drag overlay           | `QFrame`             | `dropOverlay`           | Shown on drag enter, hidden on leave/drop. |
| Reader stack           | `QStackedWidget`     | `readerStack`           | Switches between placeholder and `ReaderView`. |
| Reader canvas          | `ReaderCanvas`       | `readerCanvas`          | Emits `pageChanged(int)` and `textSelected(str)`. |
| TOC tree               | `QTreeWidget`        | `tocTree`               | Jumps to selected outline entry. |
| Highlights panel       | `QListWidget`        | `highlightsList`        | Shows saved highlights with double-click navigation. |
| Notes editor           | `QTextEdit`          | `notesEditor`           | Inline note editing synced to DB. |
| Mini-player            | `TTSBar`             | `ttsBar`                | Buttons: `playButton`, `pauseButton`, `voiceCombo`, `speedSpin`, `pitchSpin`. |
| Settings dialog        | `SettingsDialog`     | `settingsDialog`        | Tabs: General, Library, TTS. |
| Genre picker dialog    | `GenrePickerDialog`  | `genrePickerDialog`     | Multi-select, search-as-you-type. |

### 13.3 Cards, Lists, Filters & Interactions

- **Card layout:** 3:4 cover ratio, show title (elided), author, progress ring (QProgressBar in circular style), badges for tags.
- **List layout:** Columns sized to content, progress rendered via `QStyledItemDelegate` with inline bar.
- **Sorting:** Toolbar toggle for Title/Author/Added date; persists via settings.
- **Filtering:** Genre dropdown drives proxy filter; sidebar Genres node opens `GenrePickerDialog` for multi-select.
- **Drag & drop:** Accepts folders/files, forwards absolute paths to import pipeline, displays overlay and toast upon completion.
- **Context menu:** Right-click book → Open, Reveal in Finder/Explorer, Edit Metadata, Remove.

### 13.4 Keyboard Shortcuts

- `Ctrl+O` / `Cmd+O` → Trigger import dialog.
- `Ctrl+F` / `Cmd+F` → Focus global search.
- `Ctrl+1` / `Cmd+1` → Switch to Library; `Ctrl+2` / `Cmd+2` → Reader.
- `Ctrl+L` / `Cmd+L` → Toggle list/grid view.
- Reader: `[` / `]` adjust zoom, `Ctrl+Shift+H` adds highlight, `Space` toggles TTS playback.

### 13.5 Theming Tokens

- Core palette tokens: `--color-bg`, `--color-bg-alt`, `--color-surface`, `--color-border`, `--color-accent`, `--color-text`, `--color-muted`.
- Theme presets:
  - **Light:** Soft beige background (`#F4F1EA`), accent teal (`#2A9D8F`).
  - **Dark:** Deep charcoal (`#1E1E24`), accent amber (`#F4A261`).
  - **Sepia:** Warm parchment (`#F2E3C6`), accent burnt orange (`#E76F51`).
- Apply via `QPalette` plus stylesheet snippets for cards, toolbar, and drag overlay.

### 13.6 Accessibility Rules

- Ensure 4.5:1 contrast for text vs background across all themes.
- Provide keyboard focus rings on interactive controls and maintain tab order between sidebar → toolbar → content.
- Expose accessibility names/roles for cards and reader controls; announce TTS status changes.
- Allow font scaling via settings slider (applies to library cards/list and reader notes panel).

### 13.7 TTS & Notes Behavior

- TTS mini-player persists last voice/speed/pitch per book and resumes from stored timestamp.
- Selecting text in the reader enables the Highlight button and auto-populates the notes editor.
- Highlights list entries show color chip, snippet, and timestamp; double-click jumps to selection.
- Notes autosave on focus loss; unsaved changes indicator appears in dialog title.

### 13.8 Acceptance Criteria

1. Launching `python -m shelfie` opens `MainWindow` with populated sidebar, toolbar actions, and empty library grid placeholder.
2. Dragging PDFs onto the library area displays the overlay and calls the import pipeline once the drop occurs.
3. Selecting a book in the library updates the reader preview metadata and enables the Open action.
4. Double-clicking a book opens `ReaderView`, loads the correct page, and synchronizes sidebar selection.
5. TTS mini-player reflects the active backend state (play/pause, disabled when no backend available) and writes preferences back to `tts_prefs`.
6. Theme toggle instantly updates palettes without restarting the app.

### 13.9 Codex Prompts

Use these prompts verbatim (swap “Codex” for your assistant of choice) to scaffold the implementation stages:

**Prompt 1 — UI First Pass (PySide6)**

```
Role: Senior Qt Engineer

Build Shelfie’s primary UI scaffolding.
- Create MainWindow with toolbar (`searchField`, `genreFilter`, import action, list/grid toggle), sidebar navigation list, and central `QStackedWidget` hosting `LibraryView` (grid + list) and `ReaderView`.
- Implement dragEnterEvent/dropEvent on the main window that accept local PDF files/folders and emit `filesDropped(list[str])`.
- Stub out `SettingsDialog`, `GenrePickerDialog`, and `TTSBar` classes with signals/slots wired to toolbar actions.
- Register object names listed in the blueprint table so tests and themes can target them.
Generate well-documented stubs that compile with PySide6 but defer business logic to later steps.
```

**Prompt 2 — Reader Canvas & Highlights**

```
Role: PDF Rendering Specialist

Implement ReaderView internals.
- Add a `ReaderCanvas` widget that accepts a `fitz.Document` (stub friendly) and renders pages with zoom and continuous scroll.
- Emit `pageChanged(int)` when the visible page changes and `textSelected(str)` when the user highlights text.
- Provide highlight creation/removal hooks, persistence callbacks, and pre-render next/previous page caches.
- Keep fallbacks in place when PyMuPDF is unavailable so tests can run with mocks.
```

**Prompt 3 — Styling & Themes**

```
Role: Qt Styling Specialist

Add application-wide styling.
- Define QPalette + stylesheet assets for light, dark, and sepia themes using the token palette above.
- Style library cards, list rows, sidebar selection, drag overlay, and TTS mini-player to match the blueprint.
- Ensure focus outlines, accessible contrast, and theme switching via settings are covered.
- Include unit-test friendly hooks (e.g., helper returning the stylesheet per theme).
```

These prompts extend the original runbook and should replace the older UI-focused prompts once adopted.
