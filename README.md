# tnh-font
Font built from Thich Nhat Hanh's calligraphy (Lullberry design). Keep this repo private until licensing is cleared with Plum Village.

## Layout
- `source/svg/` — alphabet sheets (abc, def, … wxyz, punctuation, v2/v5 full alphabets) as SVG
- `source/svg/strengths/` — 20 character-strength words as SVG
- `source/ai/` — Illustrator originals
- `reference/traced/` — scans of his writings already traced into the alphabet
- `reference/not-traced/` — scans not yet traced
- `docs/` — notes (`list.txt`, `open.pdf`)

## Plan
1. Split the v5 alphabet sheet into one SVG per glyph
2. Study scans vs. current letters (weight, slant, baseline, joins)
3. 2–3 variants per letter, reviewed on a contact sheet (Inkscape on the Mac works on the SVGs)
4. Build TTF/OTF/WOFF2 with fontTools, with alternates (ss01, calt) and a specimen page

Note: Inkscape is not available in the cloud session; edit SVGs in Inkscape locally, commit, and pull.
