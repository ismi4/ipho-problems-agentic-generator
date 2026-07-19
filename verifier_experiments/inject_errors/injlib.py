"""Helpers to surgically edit text inside a PDF while preserving layout.

Strategy: locate characters via rawdict, redact exactly their bounding boxes,
then re-draw replacement text at the same origin using a Unicode-complete font.
Redactions for a page must all be applied before any insertion, otherwise the
freshly inserted glyphs are themselves removed.
"""
from pathlib import Path

import fitz

# Prefer Cambria on Windows; fall back to DejaVu / Liberation on Linux VMs.
_FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/cambria.ttc"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
    Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
FONTFILE = next((str(p) for p in _FONT_CANDIDATES if p.exists()), None)
if FONTFILE is None:
    raise RuntimeError("No suitable TTF font found for PDF injection")


def _int_to_rgb(c):
    return ((c >> 16) & 255) / 255, ((c >> 8) & 255) / 255, (c & 255) / 255


def line_chars(page, bi, li):
    """Flat list of char dicts for one line, carrying span size/colour."""
    l = page.get_text("rawdict")["blocks"][bi]["lines"][li]
    out = []
    for s in l["spans"]:
        for c in s["chars"]:
            out.append(
                {
                    "c": c["c"],
                    "bbox": fitz.Rect(c["bbox"]),
                    "origin": c["origin"],
                    "size": s["size"],
                    "color": _int_to_rgb(s["color"]),
                }
            )
    return out


class Editor:
    def __init__(self, path):
        self.doc = fitz.open(path)
        self.redactions = {}  # pno -> [rect]
        self.inserts = {}  # pno -> [(point, text, size, color)]

    def _q(self, pno, rects, ins):
        self.redactions.setdefault(pno, []).extend(rects)
        self.inserts.setdefault(pno, []).extend(ins)

    def replace(self, pno, bi, li, match, repl, size=None, occ=0, dx=0.0, dy=0.0):
        """Replace `match` (restricted to chars of `size`, if given) with `repl`."""
        page = self.doc[pno]
        chars = line_chars(page, bi, li)
        idx = [i for i, c in enumerate(chars) if size is None or abs(c["size"] - size) < 0.05]
        text = "".join(chars[i]["c"] for i in idx)
        starts = []
        p = text.find(match)
        while p != -1:
            starts.append(p)
            p = text.find(match, p + 1)
        if len(starts) <= occ:
            raise SystemExit(f"p{pno} b{bi} l{li}: {match!r} occ {occ} not found in {text!r}")
        sel = [chars[i] for i in idx[starts[occ] : starts[occ] + len(match)]]
        rect = sel[0]["bbox"]
        for c in sel[1:]:
            rect |= c["bbox"]
        rect = fitz.Rect(rect.x0 + 0.05, rect.y0 - 0.6, rect.x1 - 0.05, rect.y1 + 0.6)
        pt = fitz.Point(sel[0]["origin"][0] + dx, sel[0]["origin"][1] + dy)
        self._q(pno, [rect], [(pt, repl, sel[0]["size"], sel[0]["color"])])
        return rect

    def replace_search(self, needle: str, repl: str, *, pages=None, occ_global: int = 0, fontsize=None):
        """Replace the occ_global-th occurrence of needle found via search_for."""
        hits = []
        for pno, page in enumerate(self.doc):
            if pages is not None and pno not in pages:
                continue
            for rect in page.search_for(needle):
                hits.append((pno, rect))
        if len(hits) <= occ_global:
            raise SystemExit(f"search {needle!r}: occ {occ_global} not found ({len(hits)} hits)")
        pno, rect = hits[occ_global]
        page = self.doc[pno]
        # origin ≈ bottom-left of rect
        size = fontsize or max(8.0, rect.height * 0.85)
        pt = fitz.Point(rect.x0, rect.y1 - 0.15 * rect.height)
        self._q(pno, [rect], [(pt, repl, size, (0, 0, 0))])
        return pno, rect

    def blank(self, pno, rect):
        self._q(pno, [fitz.Rect(rect)], [])

    def draw(self, pno, x, y, text, size, color=(0, 0, 0)):
        self._q(pno, [], [(fitz.Point(x, y), text, size, color)])

    def commit(self, out):
        for pno, rects in self.redactions.items():
            page = self.doc[pno]
            for r in rects:
                page.add_redact_annot(r, fill=(1, 1, 1))
            page.apply_redactions(
                images=fitz.PDF_REDACT_IMAGE_NONE,
                graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
            )
        font = fitz.Font(fontfile=FONTFILE)
        for pno, ins in self.inserts.items():
            page = self.doc[pno]
            tw = fitz.TextWriter(page.rect)
            wrote = False
            for pt, text, size, color in ins:
                if not text:
                    continue
                tw.append(pt, text, font=font, fontsize=size)
                wrote = True
            if wrote:
                tw.write_text(page)
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(out, garbage=3, deflate=True)
        print("wrote", out, "font=", FONTFILE)
