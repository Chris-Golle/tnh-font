"""Build word specimens from the glyph variants.

Writes:
  glyphs/_specimen.svg  one row per style family, set in sample words (Inkscape-friendly)
  glyphs/mixer.html     pick any variant per letter and type a word (open in a browser)

Usage: python3 tools/specimen.py   (runs the extractor first)
"""
import json
from extract_variants import build, ROOT, BASE, INK, NS

TRACK = -40  # cursive letters sit closer than their side bearings
WORDS = ["Bac", "Cab", "abc", "cab", "Abba", "baba"]

# Style families: one variant per letter that belong together.
FAMILIES = {
    "smooth":       {"a": "a-01", "b": "b-01", "c": "c-01", "A": "A-01", "B": "B-03", "C": "C-01"},
    "smooth-join":  {"a": "a-03", "b": "b-02", "c": "c-02", "A": "A-02", "B": "B-01", "C": "C-02"},
    "bold":         {"a": "a-02", "b": "b-04", "c": "c-01", "A": "A-03", "B": "B-03", "C": "C-02"},
    "flat-exit":    {"a": "a-04", "b": "b-03", "c": "c-03", "A": "A-02", "B": "B-04", "C": "C-01"},
    "brush":        {"a": "a-05", "b": "b-05", "c": "c-04", "A": "A-01", "B": "B-05", "C": "C-03"},
    "dry-brush":    {"a": "a-06", "b": "b-06", "c": "c-05", "A": "A-03", "B": "B-02", "C": "C-03"},
}


def set_word(word, pick):
    """Return (svg group, width) for word using pick[letter] -> (d, w)."""
    x, parts = 0, []
    for ch in word:
        d, w = pick[ch]
        parts.append(f'<path transform="translate({x},0)" d="{d}" fill="{INK}"/>')
        x += w + TRACK
    return "".join(parts), x - TRACK


def main():
    glyphs = build()
    by_prefix = {l: {n[:4]: (d, w) for n, d, w, _ in vs} for l, vs in glyphs.items()}

    # --- SVG specimen ---
    row_h, gap, label_w = 1150, 260, 900
    rows, maxw = [], 0
    for r, (fam, sel) in enumerate(FAMILIES.items()):
        pick = {l: by_prefix[l][p] for l, p in sel.items()}
        y, x = r * row_h, label_w
        cells = [f'<text x="0" y="{y+BASE}" font-size="90" font-family="sans-serif" fill="#888">{fam}</text>',
                 f'<text x="0" y="{y+BASE+110}" font-size="44" font-family="sans-serif" fill="#aaa">'
                 + " ".join(sel.values()) + "</text>",
                 f'<line x1="{label_w}" x2="__W__" y1="{y+BASE}" y2="{y+BASE}" stroke="#f3c" stroke-opacity="0.25" stroke-width="3"/>']
        for word in WORDS:
            g, w = set_word(word, pick)
            cells.append(f'<g transform="translate({x},{y})">{g}</g>')
            x += w + gap
        maxw = max(maxw, x)
        rows.append(f'<g inkscape:groupmode="layer" inkscape:label="{fam}">' + "".join(cells) + "</g>")
    H = len(FAMILIES) * row_h
    svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg {NS} viewBox="-100 -100 {maxw+200} {H+200}">'
           f'<rect x="-100" y="-100" width="{maxw+200}" height="{H+200}" fill="#fff"/>'
           + "".join(rows).replace("__W__", str(maxw)) + "</svg>\n")
    (ROOT / "glyphs" / "_specimen.svg").write_text(svg)

    # --- HTML mixer ---
    data = {l: [{"name": n, "d": d, "w": w, "note": note} for n, d, w, note in vs] for l, vs in glyphs.items()}
    html = (ROOT / "tools" / "mixer_template.html").read_text()
    html = html.replace("/*DATA*/null", json.dumps(data)).replace("/*FAMILIES*/null", json.dumps(FAMILIES))
    html = html.replace("/*TRACK*/0", str(TRACK))
    (ROOT / "glyphs" / "mixer.html").write_text(html)
    print("wrote glyphs/_specimen.svg and glyphs/mixer.html")


if __name__ == "__main__":
    main()
