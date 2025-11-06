from __future__ import annotations

from pathlib import Path

from shelfie.utils.importing import collect_pdf_paths


def test_collect_pdf_paths_deduplicates_and_resolves(tmp_path: Path) -> None:
    first = tmp_path / "one.pdf"
    first.write_bytes(b"%PDF-1.4")
    (tmp_path / "sub").mkdir()
    duplicate = tmp_path / "sub" / ".." / "one.pdf"

    second = tmp_path / "two.PDF"
    second.write_bytes(b"%PDF-1.4")

    result = collect_pdf_paths([str(first), str(second), str(duplicate)])

    assert len(result) == 2
    assert result[0] == str(first.resolve())
    assert result[1] == str(second.resolve())


def test_collect_pdf_paths_expands_directories(tmp_path: Path) -> None:
    nested_dir = tmp_path / "folder"
    nested_dir.mkdir()
    (nested_dir / "keep.pdf").write_bytes(b"%PDF-1.4")
    (nested_dir / "ignore.txt").write_text("nope")
    deep = nested_dir / "deep"
    deep.mkdir()
    (deep / "inner.pdf").write_bytes(b"%PDF-1.4")

    paths = collect_pdf_paths([str(nested_dir)])

    expected = {
        str((nested_dir / "keep.pdf").resolve()),
        str((deep / "inner.pdf").resolve()),
    }
    assert set(paths) == expected
