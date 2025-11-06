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

*Last updated: generated by project assistant.*
