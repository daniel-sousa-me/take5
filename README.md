# Take 5 · Botanical — print-and-play source package

Everything needed to rebuild the 104-card deck, the card backs, the printer proof and the
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
| `deck/deck.py` | Card face + A4 sheet layout, rules (penalties), plant assignment, plant names |
| `deck/print_prep.py` | Print pass for pigment ink on white uncoated card: widens thin opaque lines a little, drops thin translucent ones, reports under-size dots, sends near-whites (L* ≥ 95) as no ink and warns about pale tints in the L* 90–95 speckle band (`-v` for details) |
| `deck/back.py` | Card back artwork |
| `deck/backs_sheet.py` | A4 sheet of 8 backs, positioned for a long-edge flip |
| `deck/proof.py` | One-page printer / paper proof |
| `deck/paths.py` | All paths (package-relative) and font instancing |
| `deck/preview.py`, `deck/coverage.py` | Dev tools: PNG preview of chosen cards; rough ink-coverage estimate |
| `fonts/` | DM Serif Display (numbers, title, proof headings) and Fraunces (plant names, proof text, sheet headers), SIL Open Font License |
| `docs/` | Design + print notes, and the original 24 Sep handoff for history |
| `dist/` | Current finished outputs |

## Common edits

- **Card face layout** — constants at the top of the card section in `deck/deck.py`:
  `EDGE` (clear space to the cut, 5 mm), `NUM_SIZE` / `NUM_SIZE_3` (100–104), `TWIN_NUM_SCALE` (bottom-right number, 0.8), `COMMON_SIZE` / `LATIN_SIZE` (name label), `DIGIT_GAP` (min paper between digits), `NUM_AXIS`, `POT_GAP`, `GLYPH_Q` (mark size), `FIELD_SCALE`, `PEN_STYLE`
  (`"quarter"` is current; `"under"`, `"beside"`, `"rosette"`, `"corner"` are the explored alternatives).
- **Which plant is on which card** — `ORDER`, `SHOWY_55`, `SHOWY_11` and `assign()` in `deck/deck.py`
  (`NOT_ON_ROSE`: burgundy/pink plants that must never land on a tier-5 or tier-7 card, asserted);
  `SHOWPIECE` lets a card (55) draw its plant larger than the species size.
- **Plant names** — `NAMES` in `deck/deck.py`.
- **Plant size** — `PLANT_S` (reference scale, 0.054 mm/unit ≈ 40 mm for the full canvas), `PLANT_REF`,
  `PLANT_FIT`, `PLANT_CLAMP`, `POT_MAX`, `PLANT_X/PLANT_Y` (pot base point), `PLANT_CLEAR` / `MARK_CLEAR` / `MARK_CLEAR_2ROW` (tier-5 two-row mark blocks) in `deck/deck.py`.
  Each plant is measured from its master SVG and fitted automatically; it shrinks only if it would touch a
  number, mark or label on one of its cards. `python -c "import sys; sys.path.insert(0,'deck'); import deck; print(deck.plant_scales())"` lists the result.
- **Penalty colours** — `TIER` in `deck/deck.py`: (field, field accent, sprig ornament, number, marks) per tier.
- **Penalty mark** — `WILT` (wilted-leaf glyph, 10 × 10 box) in `deck/deck.py`.
- **Tinted background instead of bare paper** — set `PAPER_BG` in `deck/deck.py` (not recommended: a full-bleed
  tint bands and uses ink). The stock is white, so the tint must be L* ≤ 90 (e.g. `#EAE1D3`); a paler cream such
  as `#F5EDDD` (L* 94) sits in the speckle band and the build refuses it (`deck.face_colour_check()`).
- **A plant drawing** — edit `plants/species/<name>.py`, then `python plants/build_plants.py <name>` and
  `python build_all.py`. The card size of each plant is recomputed from the SVG, and `print_prep.py` takes
  each plant's actual scale from `deck.plant_scales()`, so nothing else needs updating. Check the plant's
  line in the `print_prep.py` output: a master that follows the print rules reports `ok (unchanged)`;
  `python deck/print_prep.py -v` lists every widened or dropped line and every dot under the minimum.
  Colours: the card stock is **white**. A colour meant to look white should be `#FFFFFF` (no ink); a visible pale
  tint should be L* ≤ 90. Near-neutral colours at L* 90–95 print as a sparse speckle and are reported as
  `[speckle-band: N]`; near-whites at L* ≥ 95 are sent as bare paper and counted as `[paper-white: N]`.

## Printing

See `docs/DESIGN_AND_PRINT_NOTES.md`. Short version: print `take5_print_proof_A4.pdf` first on the real
white card; rear tray, 100 % / Actual size, "Prevent paper abrasion" on. Then `take5_botanical_deck_63x88_A4.pdf`:
26 pages (13 sheets of 8 cards), each front sheet followed by its back, for double-sided printing flipped on the long edge (by hand: print
the odd pages, turn the stack over left-to-right, print the even pages).

## Rights

Fan-made re-theme for personal use. "Take 5" / "6 nimmt!" are Amigo's names; no official artwork or
logo is used. Check the licensing situation before sharing or selling. Fonts are OFL (licences in `fonts/`).
