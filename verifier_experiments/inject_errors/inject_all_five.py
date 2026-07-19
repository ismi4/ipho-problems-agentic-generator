#!/usr/bin/env python3
"""Build faulty twins for all five mechanics solutions used in the expanded bench.

Paths are relative to verifier_experiments/pdfs/.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
PDFS = ROOT / "pdfs"
FAULTS = PDFS / "faulty"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from injlib import Editor  # noqa: E402


def run_legacy(script: str, cwd: Path) -> None:
    subprocess.check_call([sys.executable, str(Path(__file__).parent / script)], cwd=str(cwd))


def inject_2023() -> None:
    # Prefer regenerating; fall back to existing artifact.
    try:
        run_legacy("inject_s3.py", PDFS)
    except Exception as e:
        src = FAULTS / "IPhO_2023_S3_FAULTY.pdf"
        if src.exists():
            print("inject_s3 failed, keeping existing:", e)
        else:
            raise


def inject_2021() -> None:
    try:
        run_legacy("inject_s1.py", PDFS)
    except Exception as e:
        print("inject_s1 failed:", e)
        raise


def inject_2020() -> None:
    """Anisotropic Friction — three clear numeric / extremum faults."""
    e = Editor(str(PDFS / "IPhO_2020_S2.pdf"))
    # A1: power max at α=0 → claim α=π/2 (wrong friction-anisotropy extremum)
    e.replace_search("α = 0", "α = π/2", pages=[0], occ_global=1, fontsize=10.8)
    # A3: vx = 0.125 → 0.250 (dropped factor of 1/2 in anisotropic drag integration)
    e.replace_search("0.125", "0.250", pages=[0], occ_global=0, fontsize=10.8)
    # C2: v0max = 2.2 → 3.1 (used μx instead of μy under sqrt)
    e.replace_search("2.2", "3.1", pages=[2], occ_global=0, fontsize=10.8)
    e.commit(str(FAULTS / "IPhO_2020_S2_FAULTY.pdf"))


def inject_2024() -> None:
    """Black Widow Pulsar — Lagrange point + temperature faults."""
    e = Editor(str(PDFS / "IPhO_2024_S3.pdf"))
    # A-3 boxed: 0.36 → 0.25 (wrong Lagrange-point root)
    e.replace_search("0.36", "0.25", pages=[1], occ_global=2, fontsize=11)
    # A-6 boxed temperature: 9 × 103 → 9 × 102 (missed square-root / Stefan scaling)
    # There are two similar lines; change the boxed one (later on page 3).
    hits_before = []
    doc = fitz.open(PDFS / "IPhO_2024_S3.pdf")
    for rect in doc[3].search_for("9 × 103"):
        hits_before.append(rect)
    doc.close()
    if hits_before:
        e.replace_search("9 × 103", "9 × 102", pages=[3], occ_global=len(hits_before) - 1, fontsize=11)
    else:
        e.replace_search("9 × 10", "9 × 10", pages=[3], occ_global=0)  # noop fallback
        # try alternate glyph spacing
        e.replace_search("103", "102", pages=[3], occ_global=0, fontsize=8)
    e.commit(str(FAULTS / "IPhO_2024_S3_FAULTY.pdf"))


def inject_2025() -> None:
    """Cox's Timepiece — threshold ξ⋆ and regime boundary faults.

    Mathematical-italic glyphs don't survive DejaVu redraw, so we blank the
    original spans and rewrite as unambiguous ASCII.
    """
    doc = fitz.open(PDFS / "IPhO_2025_S2.pdf")
    r_xi = doc[10].search_for("𝜉⋆= 2")
    r_gt = doc[14].search_for("𝜉+2𝜆> 2")
    r_lt = doc[14].search_for("𝜉+ 2𝜆< 2")
    doc.close()
    if not (r_xi and r_gt and r_lt):
        raise SystemExit(f"2025 locate failed: xi={len(r_xi)} gt={len(r_gt)} lt={len(r_lt)}")
    e = Editor(str(PDFS / "IPhO_2025_S2.pdf"))
    # union the fragmented search hits for ξ⋆=2 (glyph-split)
    u = r_xi[0]
    for r in r_xi[1:]:
        u |= r
    e.blank(10, fitz.Rect(u.x0 - 2, u.y0 - 2, u.x1 + 8, u.y1 + 2))
    e.draw(10, u.x0, u.y1 - 1, "xi* = 1", 10)
    e.blank(14, fitz.Rect(r_gt[0].x0 - 2, r_gt[0].y0 - 2, r_gt[-1].x1 + 8, r_gt[0].y1 + 2))
    e.draw(14, r_gt[0].x0, r_gt[0].y1 - 1, "xi + 2 lambda > 1", 10)
    e.blank(14, fitz.Rect(r_lt[0].x0 - 2, r_lt[0].y0 - 2, r_lt[-1].x1 + 8, r_lt[0].y1 + 2))
    e.draw(14, r_lt[0].x0, r_lt[0].y1 - 1, "xi + 2 lambda < 1", 10)
    e.commit(str(FAULTS / "IPhO_2025_S2_FAULTY.pdf"))


def verify_extracts() -> None:
    checks = {
        "IPhO_2020_S2_FAULTY.pdf": ["0.250", "3.1"],
        "IPhO_2024_S3_FAULTY.pdf": ["0.25"],
        "IPhO_2025_S2_FAULTY.pdf": ["ξ⋆= 1", "ξ⋆=1"],
        "IPhO_2021_S1_FAULTY.pdf": ["h′ = h", "h' = h", "δ= 3", "δ=3"],
        "IPhO_2023_S3_FAULTY.pdf": ["0.31", "1/3"],
    }
    for name, needles in checks.items():
        path = FAULTS / name
        if not path.exists():
            print("MISSING", path)
            continue
        text = Path(path).read_bytes()  # ensure readable
        doc = fitz.open(path)
        full = "\n".join(p.get_text("text") for p in doc)
        ok = any(n in full for n in needles)
        print(f"verify {name}: {'OK' if ok else 'CHECK'} hits={[n for n in needles if n in full]}")


def main() -> None:
    FAULTS.mkdir(parents=True, exist_ok=True)
    # Ensure clean sources exist
    for f in [
        "IPhO_2020_S2.pdf",
        "IPhO_2021_S1.pdf",
        "IPhO_2023_S3.pdf",
        "IPhO_2024_S3.pdf",
        "IPhO_2025_S2.pdf",
    ]:
        assert (PDFS / f).exists(), f

    print("=== 2023 ===")
    inject_2023()
    print("=== 2021 ===")
    inject_2021()
    print("=== 2020 ===")
    inject_2020()
    print("=== 2024 ===")
    inject_2024()
    print("=== 2025 ===")
    inject_2025()
    print("=== verify ===")
    verify_extracts()
    print("Faulty PDFs:", sorted(p.name for p in FAULTS.glob("*_FAULTY.pdf")))


if __name__ == "__main__":
    main()
