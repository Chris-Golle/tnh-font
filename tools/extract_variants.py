"""Extract glyph variants from the alphabet sheets into Inkscape-ready SVGs.

Grid (1000-unit em, y down as in Inkscape):
  ascender y=0 · cap height y=100 · x-height y=300 · baseline y=750 · descender y=1000

Each variant: (name, source path index, top, base_frac, cut, note)
  top        y where the top of the shape lands (XH, ASC_B, CAP)
  base_frac  fraction of the shape's height, from its top, that sits above
             the baseline (anything below is a tail)
  cut        None, or (x0, x1) in source units: keep only that vertical slice
             (to lift a letter out of a joined word)

Usage: python3 tools/extract_variants.py
"""
from pathlib import Path as P

import pathops
from fontTools.pens.svgPathPen import SVGPathPen
from svgelements import SVG, Shape, Path, Matrix

ROOT = P(__file__).resolve().parent.parent
EM, BASE, XH, CAP, ASC, DESC = 1000, 750, 300, 100, 0, 1000
ASC_B = 40  # where b's ascender lands
SB = 40     # side bearing
INK = "#1b2328"
ABC = "source/svg/abc.svg"

LETTERS = {
    "a": [
        ("a-01-classic-tail",    135, XH, 0.62, None, "open bowl, long diagonal exit; the signature TNH a"),
        ("a-02-bold-curl",        79, XH, 0.78, None, "heavy brush, short curled exit"),
        ("a-03-round-joining",   148, XH, 0.92, None, "smooth two-part a, upright stem, ready to join"),
        ("a-04-wide-flat-exit",  147, XH, 0.90, None, "bold, low horizontal exit for connecting"),
        ("a-05-pointed",          32, XH, 0.88, None, "pointed bowl, flat sweeping exit"),
        ("a-06-dry-brush",        76, XH, 0.95, None, "dry-brush texture, cursive joining a"),
    ],
    "b": [
        ("b-01-smooth-loop",     149, ASC_B, 1.00, None, "smooth, looped bowl"),
        ("b-02-smooth-open",     150, ASC_B, 1.00, None, "smooth, bowl open at the stem"),
        ("b-03-bold-hook",       146, ASC_B, 1.00, None, "heavy, hooked top"),
        ("b-04-bold-closed",      58, ASC_B, 1.00, None, "heavy, closed bowl"),
        ("b-05-brush-open",        3, ASC_B, 1.00, None, "brush texture, open bowl"),
        ("b-06-dry-brush",         2, ASC_B, 1.00, None, "dry brush, rough edges"),
    ],
    "c": [
        ("c-01-round",            88, XH, 0.97, None, "round, heavy, ball top"),
        ("c-02-round-alt",        89, XH, 0.97, None, "round, slightly narrower"),
        ("c-03-from-co",          72, XH, 0.97, (0, 269),   "lifted from 'co'; tidy the right edge"),
        ("c-04-from-ce",         144, XH, 0.97, (0, 253),   "lifted from 'ce'; tidy the right edge"),
        ("c-05-from-ce-light",   141, XH, 0.97, (-30, -10), "lifted from 'ce'; tidy the right edge"),
    ],
    "B": [
        ("B-01-loop",            131, CAP, 0.97, None, "standalone B, closed lower loop"),
        ("B-02-brush",            21, CAP, 0.97, None, "standalone B, brush texture"),
        ("B-03-from-Be-smooth",   66, CAP, 0.92, (0, 161),   "lifted from 'Be'; tidy the right edge"),
        ("B-04-from-Be-curl",      7, CAP, 0.92, (0, 134.5), "lifted from 'Be'; tall stem, curled bowl"),
        ("B-05-from-Bre",         27, CAP, 0.92, (0, 137),   "lifted from 'Bre'; double-line brush"),
    ],
    "C": [
        ("C-01-ball",             87, CAP, 0.97, None, "standalone C, ball terminal"),
        ("C-02-from-Cha",         31, CAP, 0.95, (0, 225),   "lifted from 'Cha'; looped top"),
        ("C-03-from-Comp",       110, CAP, 0.97, (0, 213.5), "lifted from 'Comp'; looped top"),
    ],
}

# No capital A exists in the traced sheets or scans: offer enlarged lowercase
# forms (his capitals are often larger minuscules) until one is traced.
LETTERS["A"] = [
    (f"A-0{i}-provisional-{n[5:]}", idx, CAP, frac, cut,
     f"PROVISIONAL: {n} enlarged to cap height (no traced capital A yet)")
    for i, (n, idx, _, frac, cut, _) in enumerate(
        [LETTERS["a"][0], LETTERS["a"][2], LETTERS["a"][1]], start=1)
]

_cache = {}


def shapes(src):
    if src not in _cache:
        svg = SVG.parse(str(ROOT / src), reify=True)
        _cache[src] = [e for e in svg.elements() if isinstance(e, Shape)]
    return _cache[src]


def slice_path(shape, x0, x1):
    """Keep the part of shape between x0 and x1 (curves preserved)."""
    sk = pathops.Path()
    pen = sk.getPen()
    for seg in Path(shape).segments():
        n = type(seg).__name__
        if n == "Move":
            pen.moveTo((seg.end.x, seg.end.y))
        elif n == "Line":
            pen.lineTo((seg.end.x, seg.end.y))
        elif n == "CubicBezier":
            pen.curveTo((seg.control1.x, seg.control1.y), (seg.control2.x, seg.control2.y), (seg.end.x, seg.end.y))
        elif n == "QuadraticBezier":
            pen.qCurveTo((seg.control.x, seg.control.y), (seg.end.x, seg.end.y))
        elif n == "Arc":
            for c in seg.as_cubic_curves():
                pen.curveTo((c.control1.x, c.control1.y), (c.control2.x, c.control2.y), (c.end.x, c.end.y))
        elif n == "Close":
            pen.closePath()
    _, y0, _, y1 = Path(shape).bbox()
    box = pathops.Path()
    bp = box.getPen()
    bp.moveTo((x0, y0 - 5)); bp.lineTo((x1, y0 - 5)); bp.lineTo((x1, y1 + 5)); bp.lineTo((x0, y1 + 5)); bp.closePath()
    out = pathops.op(sk, box, pathops.PathOp.INTERSECTION)
    svgpen = SVGPathPen(None)
    out.draw(svgpen)
    return Path(svgpen.getCommands())


def place(idx, top, frac, cut, src=ABC):
    """Fit a source shape to the grid; return (path d, advance width)."""
    shape = shapes(src)[idx]
    p = slice_path(shape, *cut) if cut else Path(shape)
    x0, y0, x1, y1 = p.bbox()
    s = (BASE - top) / ((y1 - y0) * frac)
    p = p * Matrix(f"translate({-x0},{-y0})") * Matrix(f"scale({s})") * Matrix(f"translate({SB},{top})")
    p.reify()
    return p.d(), round(p.bbox()[2] + SB)


def metrics_layer(w, upper=False):
    lines = [(ASC, "ascender"), (CAP, "cap height") if upper else None, (XH, "x-height"),
             (BASE, "baseline"), (DESC, "descender")]
    out = ['<g inkscape:groupmode="layer" inkscape:label="metrics" sodipodi:insensitive="true" style="opacity:0.5">']
    for y, lab in filter(None, lines):
        c = "#e0306a" if lab == "baseline" else "#2a8bd6"
        out.append(f'<line x1="-200" x2="{w+200}" y1="{y}" y2="{y}" stroke="{c}" stroke-width="2"/>'
                   f'<text x="-195" y="{y-6}" font-size="22" font-family="sans-serif" fill="{c}">{lab}</text>')
    for x in (0, w):
        out.append(f'<line x1="{x}" x2="{x}" y1="-50" y2="{DESC+50}" stroke="#999" stroke-width="2" stroke-dasharray="8 8"/>')
    out.append('</g>')
    return "".join(out)


NS = ('xmlns="http://www.w3.org/2000/svg" '
      'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
      'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"')


def glyph_doc(d, w, name, note, upper):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg {NS} width="{w}" height="{EM}" viewBox="0 0 {w} {EM}">
<title>{name}</title>
<desc>{note}. Grid: em {EM}, baseline y={BASE}, x-height y={XH}, cap y={CAP}. Advance = page width.</desc>
{metrics_layer(w, upper)}
<g inkscape:groupmode="layer" inkscape:label="glyph" id="glyph">
<path id="{name}" d="{d}" fill="{INK}"/>
</g>
</svg>
'''


def letter_dir(letter):
    # separate folders for upper/lower so case-insensitive filesystems (macOS) don't merge them
    return ROOT / "glyphs" / (f"{letter}-upper" if letter.isupper() else letter)


def build():
    """Write every variant SVG plus a per-letter sheet; return {letter: [(name, d, w, note)]}."""
    out = {}
    for letter, variants in LETTERS.items():
        d_ = letter_dir(letter)
        d_.mkdir(parents=True, exist_ok=True)
        for old in d_.glob("*.svg"):
            old.unlink()
        upper = letter.isupper()
        placed = []
        for name, idx, top, frac, cut, note in variants:
            d, w = place(idx, top, frac, cut)
            (d_ / f"{name}.svg").write_text(glyph_doc(d, w, name, note, upper))
            placed.append((name, d, w, note))
        x, cells = 0, []
        for name, d, w, note in placed:
            cells.append(f'<g transform="translate({x},0)">{metrics_layer(w, upper)}<path d="{d}" fill="{INK}"/>'
                         f'<text x="0" y="{DESC+70}" font-size="34" font-family="sans-serif" fill="#333">{name}</text></g>')
            x += max(w, 520) + 120
        (d_ / "_sheet.svg").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<svg {NS} viewBox="-260 -60 {x+300} {EM+180}">'
            f'<rect x="-260" y="-60" width="{x+300}" height="{EM+180}" fill="#fff"/>' + "".join(cells) + "</svg>\n")
        out[letter] = placed
        print(f"{letter}: {len(placed)} variants -> {d_.relative_to(ROOT)}")
    return out


if __name__ == "__main__":
    build()
