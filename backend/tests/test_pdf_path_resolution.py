import importlib.util
from pathlib import Path


def _load_file_paths_module():
    module_path = (
        Path(__file__).resolve().parents[1] / "athena" / "core" / "file_paths.py"
    )
    spec = importlib.util.spec_from_file_location("file_paths_for_test", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


resolve_data_file_path = _load_file_paths_module().resolve_data_file_path


def test_resolve_pdf_file_path_relative(tmp_path):
    paper_dir = tmp_path / "102"
    paper_dir.mkdir(parents=True)
    pdf = paper_dir / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 test")

    resolved = resolve_data_file_path("102/paper.pdf", tmp_path)
    assert resolved == pdf


def test_resolve_pdf_file_path_legacy_absolute(tmp_path):
    paper_dir = tmp_path / "205"
    paper_dir.mkdir(parents=True)
    pdf = paper_dir / "legacy.pdf"
    pdf.write_bytes(b"%PDF-1.4 legacy")

    resolved = resolve_data_file_path("/data/library/205/legacy.pdf", tmp_path)
    assert resolved == pdf


def test_resolve_pdf_file_path_blocks_traversal(tmp_path):
    outside = tmp_path.parent / "evil.pdf"
    outside.write_bytes(b"not-a-real-pdf")

    resolved = resolve_data_file_path("../evil.pdf", tmp_path)
    assert resolved is None


def test_resolve_stored_file_path_relative(tmp_path):
    paper_dir = tmp_path / "99"
    paper_dir.mkdir(parents=True)
    pdf = paper_dir / "doc.pdf"
    pdf.write_bytes(b"%PDF-1.4 doc")

    resolved = resolve_data_file_path("99/doc.pdf", tmp_path)
    assert resolved == pdf


def test_resolve_stored_file_path_legacy_absolute(tmp_path):
    paper_dir = tmp_path / "77"
    paper_dir.mkdir(parents=True)
    pdf = paper_dir / "legacy.pdf"
    pdf.write_bytes(b"%PDF-1.4 legacy")

    resolved = resolve_data_file_path("/data/library/77/legacy.pdf", tmp_path)
    assert resolved == pdf


def test_resolve_stored_file_path_missing_file(tmp_path):
    resolved = resolve_data_file_path("404/missing.pdf", tmp_path)
    assert resolved is None
