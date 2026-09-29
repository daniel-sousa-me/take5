# Take 5 botanical PnP - project handoff

**Snapshot date:** 24 September 2026  
**Status:** visual system in development; plant asset library is the most current finished work.

## 1. Project goal

Create a custom print-and-play interpretation of the number-row game *Take 5 / 6 nimmt!* with a broad-appeal botanical theme. The intended production setup is a Canon GX5050 printing on 250 gsm uncoated A4 stock, with hand cutting.

The visual target is **flat editorial botanical illustration**: warm, refined, clearly stylised rather than photorealistic, with low-to-moderate ink coverage and excellent table readability.

## 2. Design decisions that should be preserved

- **No trim-following perimeter border.** A rectangular/card-edge border makes +/-1 mm hand-cut drift obvious.
- Use **full-bleed or edge-crossing organic colour fields** and open botanical ornament instead.
- The face must be **readable at 180 degrees**. Duplicate the primary number/information at opposite ends or use an equivalent rotationally neutral solution.
- **Penalty value should be shown as repeated penalty symbols**, not as a symbol plus a numeric penalty count. The numeric-count experiment was rejected.
- The card number is the most important information and must read from across a large table.
- Keep the plant art visually rich but subordinate to gameplay information.
- Flat colour, simplified shapes and controlled linework are preferred to generated painterly/photoreal plant art.
- The cream / olive / terracotta / sage palette is deliberate because it is forgiving on uncoated stock.

## 3. Current card-size direction

The latest size discussion moved away from tightly packing 8 cards per A4. The current leading candidate is **59 x 110 mm finished**, intended to fit the **61 x 112 mm French-Tarot sleeve family** while remaining larger and more readable than poker cards.

Working print geometry for the size test:

- Finished card: **59 x 110 mm**
- Nominal bleed: **1.5 mm** each side
- Printed card envelope: **62 x 113 mm**
- Grid: **3 x 2 on A4**
- Artwork block: **186 x 226 mm**
- A4 side margin: roughly **12 mm**
- A4 top/bottom margin: roughly **35.5 mm**

This is a **working candidate, not an irrevocably locked specification**. The point of the change was to stay comfortably away from printer/driver margins instead of optimising sheet yield.

The size-test file includes a 100 mm calibration line and should be printed at **Actual Size / 100%** before committing cardstock.

## 4. Printer / production constraints

- Canon GX5050 / GX5000-series A4 theoretical printable area is about 200 x 287 mm (5 mm physical edge margin), but the driver can be conservative and may scale or warn near limits.
- Do **not** design to the theoretical boundary. The current 3 x 2 geometry intentionally leaves much more space.
- Target stock: **250 gsm uncoated**.
- Use rear feed / thick-paper handling as appropriate for the printer and stock.
- Avoid relying on automatic duplex for heavy stock; manual front/back feeding is safer for registration.
- Avoid borderless mode for final production because it can enlarge/crop artwork and undermine exact card size.
- Crop references should live in scrap/gutter areas, not as visible card-edge rules.

## 5. Botanical asset system

Current library: **14 real plant species** as editable SVGs.

1. Aloe vera
2. Anthurium andraeanum
3. Begonia maculata
4. Calathea ornata
5. Dracaena trifasciata
6. Epipremnum aureum
7. Ficus elastica
8. Ficus lyrata
9. Monstera deliciosa
10. Oxalis triangularis
11. Pilea peperomioides
12. Spathiphyllum
13. Strelitzia reginae
14. Zamioculcas zamiifolia

The intended final library is roughly **24 species**. That is enough variety for a 104-card deck while still allowing a consistent illustration system. Repeating each species across 4-5 cards with controlled variants is preferable to 104 unrelated species.

### SVG visual grammar

- Canvas: 600 x 800 viewBox, transparent background.
- Shared terracotta-pot family with small silhouette variations.
- Leaves built from filled vector shapes, typically 2-4 tonal levels.
- Veins/patterns are thin and lower contrast than silhouettes.
- Species recognition should come from silhouette and internal pattern, not labels.
- Avoid perfect radial symmetry and mechanically even spacing.
- Prefer overlap and foreground/background hierarchy to exposed stem networks.
- Pot should anchor the illustration, not dominate it.

### Palette

See `source/palette.json`. Core colours are warm cream, dark olive/forest greens, sage/light greens, terracotta, mustard, muted blush/burgundy and off-white pattern marks.

## 6. Current quality assessment

The current v3 set is a useful production base, not final art. Stronger assets include Monstera, Pilea, snake plant, Calathea, Begonia and Oxalis. The main remaining weaknesses are:

- Pothos still feels mechanically draped.
- ZZ plant remains visually tangled.
- Bird of paradise needs larger, lusher overlapping paddle leaves.
- Fiddle-leaf fig still reads slightly diagrammatic.
- Several plants can benefit from more irregular leaf size, overlap and secondary tonal shapes.

The requested direction is **not** to replace the construction method. Keep the existing clean SVG approach and improve shapes/details within it.

## 7. Card-face status

The most recent frame prototype in the package is `modern_seed_house_v7_64x99.*`, but its **64 x 99 mm geometry is obsolete**. Preserve only its useful conceptual ideas:

- cream base
- organic botanical edge fragments instead of a trim border
- rotational readability
- large central/primary number hierarchy
- botanical ornament kept away from cut edge

Do not continue the v7 layout blindly. A new face should be rebuilt for the eventual final card size, with a cleaner alignment grid and no accidental overlaps.

## 8. Gameplay visual language still to implement

- Large number 1-104.
- Same value readable from opposite orientation.
- Penalty amount represented by **repeated wilted-leaf symbols**.
- High-penalty cards can use more visually striking plants/variants as a subtle secondary cue, but the penalty symbols remain authoritative.
- Avoid non-gameplay text such as plant names on the face unless later testing shows it adds value.

## 9. Recommended next steps

1. Print and physically cut the 59 x 110 mm test on inexpensive stock; sleeve-test it.
2. Lock the finished size only after that physical test.
3. Refine the four weakest SVG plants while preserving the v3 style.
4. Add roughly 10 more species to reach a balanced 24-species library.
5. Rebuild the card face from scratch at the locked size using a strict layout grid.
6. Design the wilted-leaf penalty glyph as a dedicated SVG symbol and test 1/2/3/5/7-symbol groupings.
7. Create a low-ink card back with an all-over botanical pattern; avoid a framed back because manual duplex registration will vary.
8. Produce a one-sheet colour/registration proof on the real 250 gsm stock before generating the full deck.

## 10. Package structure

- `current/` - latest production-relevant artifacts.
- `reference/` - prior/reference files useful for design continuity, explicitly not current specs.
- `source/` - exact reproduction source, palette and dependencies.
- `HANDOFF.docx` / `HANDOFF.md` - this project summary.
- `MANIFEST.sha256` - file integrity hashes.

## 11. Reproduction

Install the packages listed in `source/requirements.txt`, then run:

```bash
python source/rebuild_current_assets.py
```

That script contains the exact final SVG text and rebuilds the 14 SVG files, contact sheet and ZIP without any external image assets.

## 12. Rights / distribution note

This is an original fan-made visual redesign inspired by an existing commercial game system. The package intentionally avoids official logos and artwork. Before public distribution, sale or publication, review the applicable rights and licensing situation separately. For personal prototyping, keep the project clearly separated from official branding.
