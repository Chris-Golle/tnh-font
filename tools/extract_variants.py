"""Extract glyph variants from an alphabet sheet into Inkscape-ready SVGs.

Each variant is placed on a 1000-unit em grid (y down, as in Inkscape):
  ascender y=0 · x-height y=300 · baseline y=750 · descender y=1000
`bowl` is the fraction of the source shape's height (from its top) that sits
between x-height and baseline; the rest (tails) hangs below or beside.
Usage: python3 tools/extract_variants.py
"""
from pathlib import Path as P
from svgelements import SVG, Shape, Path, Matrix

ROOT = P(__file__).resolve().parent.parent
EM, BASE, XH, ASC, DESC = 1000, 750, 300, 0, 1000
SB = 40  # side bearing

LETTERS = {
    "a": {
        "source": "source/svg/abc.svg",
        "variants": [
            # (name, path index in source, bowl fraction, note)
            ("a-01-classic-tail", 135, 0.62, "open bowl, long diagonal exit; the signature TNH a"),
            ("a-02-bold-curl",     79, 0.78, "heavy brush, short curled exit"),
            ("a-03-round-joining",148, 0.92, "smooth two-part a, upright stem, ready to join"),
            ("a-04-wide-flat-exit",147, 0.90, "bold, low horizontal exit for connecting"),
            ("a-05-pointed",       32, 0.88, "pointed bowl, flat sweeping exit"),
            ("a-06-dry-brush",     76, 0.95, "dry-brush texture, cursive joining a"),
        ],
    }
}

def shapes(src):
    svg = SVG.parse(str(ROOT / src), reify=True)
    return [e for e in svg.elements() if isinstance(e, Shape)]

def metrics_layer(w):
    lines = [(ASC, "ascender"), (XH, "x-height"), (BASE, "baseline"), (DESC, "descender")]
    out = ['<g inkscape:groupmode="layer" inkscape:label="metrics" sodipodi:insensitive="true" style="opacity:0.5">']
    for y, lab in lines:
        c = "#e0306a" if lab == "baseline" else "#2a8bd6"
        out.append(f'<line x1="-200" x2="{w+200}" y1="{y}" y2="{y}" stroke="{c}" stroke-width="2"/>'
                   f'<text x="-195" y="{y-6}" font-size="22" font-family="sans-serif" fill="{c}">{lab}</text>')
    for x in (0, w):
        out.append(f'<line x1="{x}" x2="{x}" y1="-50" y2="{DESC+50}" stroke="#999" stroke-width="2" stroke-dasharray="8 8"/>')
    out.append('</g>')
    return "".join(out)

def place(shape, bowl):
    """Return path d and advance width with the shape fitted to the grid."""
    p = Path(shape)
    x0, y0, x1, y1 = p.bbox()
    s = (BASE - XH) / ((y1 - y0) * bowl)
    p = p * Matrix(f"translate({-x0},{-y0})") * Matrix(f"scale({s})") * Matrix(f"translate({SB},{XH})")
    p.reify()
    bx0, by0, bx1, by1 = p.bbox()
    return p.d(), round(bx1 + SB)

def doc(d, w, title, note):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
     width="{w}" height="{EM}" viewBox="0 0 {w} {EM}">
<title>{title}</title>
<desc>{note}. Grid: em {EM}, baseline y={BASE}, x-height y={XH}. Advance = page width.</desc>
{metrics_layer(w)}
<g inkscape:groupmode="layer" inkscape:label="glyph" id="glyph">
<path id="{title}" d="{d}" fill="#1b2328"/>
</g>
</svg>
'''

def main():
    for letter, cfg in LETTERS.items():
        outdir = ROOT / "glyphs" / letter
        outdir.mkdir(parents=True, exist_ok=True)
        src = shapes(cfg["source"])
        placed = []
        for name, idx, bowl, note in cfg["variants"]:
            d, w = place(src[idx], bowl)
            (outdir / f"{name}.svg").write_text(doc(d, w, name, note))
            placed.append((name, d, w, note))
        # contact sheet: each variant on the grid, plus a word built from it
        gap, x, cells = 120, 0, []
        for name, d, w, note in placed:
            cells.append(f'<g transform="translate({x},0)">{metrics_layer(w)}'
                         f'<path d="{d}" fill="#1b2328"/>'
                         f'<text x="0" y="{DESC+70}" font-size="34" font-family="sans-serif" fill="#333">{name}</text></g>')
            x += max(w, 520) + gap
        W = x
        (outdir / "_sheet.svg").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
            f'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" '
            f'viewBox="-260 -60 {W+300} {EM+180}"><rect x="-260" y="-60" width="{W+300}" height="{EM+180}" fill="#fff"/>'
            + "".join(cells) + "</svg>\n")
        print(f"{letter}: {len(placed)} variants -> {outdir.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
