"""PDF → text / page images helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


def pdf_to_text(pdf_path: Path) -> str:
    """Prefer pdftotext -layout; fall back to PyMuPDF."""
    try:
        out = subprocess.check_output(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        if out.strip():
            return out
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    import fitz

    doc = fitz.open(pdf_path)
    return "\n".join(page.get_text("text") for page in doc)


def pdf_to_png_pages(pdf_path: Path, out_dir: Path, dpi: int = 150) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "page"
    # clean prior
    for old in out_dir.glob("page-*.png"):
        old.unlink()
    subprocess.check_call(
        ["pdftoppm", "-png", "-r", str(dpi), str(pdf_path), str(prefix)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    pages = sorted(out_dir.glob("page-*.png"))
    if not pages:
        raise RuntimeError(f"pdftoppm produced no pages for {pdf_path}")
    return pages


def page_count(pdf_path: Path) -> int:
    out = subprocess.check_output(["pdfinfo", str(pdf_path)], text=True)
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":")[1].strip())
    raise RuntimeError(f"Could not read page count for {pdf_path}")
