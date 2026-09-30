# Take 5 · Botanical — print-and-play source package

Everything needed to rebuild the 104-card deck (plus 4 player aids), the card backs, the printer proof and the
24 plant illustrations from source. Nothing is downloaded at build time.

## Quick start

```bash
pip install -r requirements.txt        # needs the Cairo system library (see requirements.txt)
python build_all.py                    # deck + backs + proof from the master plant SVGs  (~1 min)
python build_all.py --plants           # also regenerate the 24 plant SVGs from their generators first
```

Results go to `build/`. Ready-made copies of the current outputs are in `dist/`.
A clean rebuild reproduces the files in `dist/` exactly.

## What's in here

| Path | What it is |
|---|---|
| `build_all.py` | Runs the whole pipeline in order |
| `plants/species/*.py` | One generator per plant (24). Each writes `plants/out/<name>.svg` |
| `plants/core.py` | Shared drawing helpers: spline paths, `Leaf`, tapered stems, the terracotta `pot()`, palette |
| `plants/plants_a.py` | Older helpers; `along()` is still used by the card back |
| `plants/build_plants.py` | Runs every generator, namespaces SVG ids, draws `build/plants_contact_sheet.png` |
| `plants/out/*.svg` | **Master plant art** (600 × 800, transparent, flat colour) |
| `plants/BRIEF.md` | The illustration brief the plants were drawn to (style rules + craft checklist) |
| `deck/deck.py` | Card face + A4 sheet layout, rules (penalties), plant assignment, plant names, player aid |
| `deck/print_prep.py` | Print pass for pigment ink on uncoated card (line minimums, drops faint hairlines) |
| `deck/back.py` | Card back artwork |
| `deck/backs_sheet.py` | A4 sheet of 6 backs, positioned for a long-edge flip |
| `deck/proof.py` | One-page printer / paper proof |
| `deck/paths.py` | All paths (package-relative) and font instancing |
| `deck/preview.py`, `deck/coverage.py` | Dev tools: PNG preview of chosen cards; rough ink-coverage estimate |
| `fonts/` | DM Serif Display (numbers, title) and Fraunces (plant names), SIL Open Font License |
| `docs/` | Design + print notes, and the original 24 Sep handoff for history |
| `dist/` | Current finished outputs |

## Common edits

- **Card face layout** — constants at the top of the card section in `deck/deck.py`:
  `EDGE` (clear space to the cut, 5 mm), `NUM_SIZE`, `PLANT_H`, `FIELD_SCALE`, `PEN_STYLE`
  (`"quarter"` is current; `"under"`, `"beside"`, `"rosette"`, `"corner"` are the explored alternatives).
- **Which plant is on which card** — `ORDER`, `SHOWY_55`, `SHOWY_11` and `assign()` in `deck/deck.py`.
- **Plant names** — `NAMES` in `deck/deck.py`.
- **Penalty colours** — `TIER` in `deck/deck.py`.
- **Player aid text** — `AID_KEY`, `AID_STEPS`, `AID_SETUP`, `AID_END` in `deck/deck.py`.
- **Cream background instead of bare paper** — set `PAPER_BG = "#F5EDDD"` in `deck/deck.py`
  (not recommended for print; use ivory stock instead — see docs).
- **A plant drawing** — edit `plants/species/<name>.py`, then `python plants/build_plants.py <name>` and
  `python build_all.py`. If you change the plant size on the card, update `MM_PER_UNIT` in
  `deck/print_prep.py` (= `PLANT_H / 740`).

## Printing

See `docs/DESIGN_AND_PRINT_NOTES.md`. Short version: print `take5_print_proof_A4.pdf` first on the real
card; rear tray, 100 % / Actual size, borderless off, "Prevent paper abrasion" on; then the 18 deck sheets;
then the back sheet 18× on the reverse, flipping each sheet on its long edge.

## Rights

Fan-made re-theme for personal use. "Take 5" / "6 nimmt!" are Amigo's names; no official artwork or
logo is used. Check the licensing situation before sharing or selling. Fonts are OFL (licences in `fonts/`).
