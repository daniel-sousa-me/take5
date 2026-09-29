# Botanical SVG v4 — illustrator brief (read fully before drawing)

Project: print-and-play card game (Take 5 / 6 nimmt! re-theme). Each card shows one potted
house plant. Final art prints ~40 mm tall on uncoated 250 gsm card, so it must read clearly
small, but it will also be inspected large. The client wants it to look **professional,
editorial flat botanical illustration** — think a well-made plant poster, not clip art.

The client's complaint about the last attempt: "The shapes aren't meeting where they should.
Objects with the same colour are overlapping, making a mishmash." Treat every join, overlap and
colour adjacency as a deliberate design decision.

## Files
- `/home/claude/work/v4/core.py` — shared helpers (Catmull-Rom paths, `Leaf` class, tapered
  `stem`/`ribbon`, `leaf_g` renderer with half-leaf shading + clip, shared `pot()`), palette
  `PAL`, `SHADE` map. **Do not edit core.py** (others use it in parallel). If you need a
  variant of a helper, copy it into your own file.
- `/home/claude/work/v4/plants_a.py` — the previous attempt at monstera/pothos (reference only).
- Originals (v3) to improve on: `/home/claude/work/take5_botanical_handoff_2026-09-24/current/plants/<name>.svg`
  and the contact sheet `.../current/botanical_svg_set_v3_refined_contact_sheet.png`.
- Handoff notes: `/home/claude/work/take5_botanical_handoff_2026-09-24/HANDOFF.md` (section 5/6).
- Render: `python3 /home/claude/work/v4/render.py out.png file.svg` (cream background, 600x800).
  For detail checks, render bigger / crop with cairosvg + PIL (e.g. `cairosvg.svg2png(url=..., output_width=1800)` then crop regions and view them).

## Your deliverable
- Generator: `/home/claude/work/v4/species/<name>.py` exposing `build() -> str` (SVG body) —
  or hand-write the SVG directly if that's cleaner. Either is fine.
- Output: `/home/claude/work/v4/out/<name>.svg` — full SVG document, `viewBox="0 0 600 800"`,
  width 600 height 800, transparent background, a `<title>`.
- Use only your own filenames; never touch other species' files.

## Hard rules
- Canvas 600×800, transparent. Plant + pot centred on x≈300. Pot bottom ≈ y 752, rim ≈ y 570–600.
  Keep everything inside x 30–570, y 40–785 (small breathing room).
- Use the shared `pot()` from core (pass `kind`, `rx`, `rim_y`, `base_w`, `band` for small
  silhouette variation). Draw order: pot back (lip + soil) → plant → pot front → anything
  that genuinely drapes in front of the pot.
- Flat colour only: no gradients, filters, blur, masks. clipPath and even-odd fills are fine.
  Opacity only for subtle tonal overlays (veins, shading), never to fake a colour.
- Palette: `PAL` in core.py (greens deep→pale, terracottas, soil, mustard, burgundy, blush,
  cream, etc.). Stay in this family.
- No text, no outlines around everything, no drop shadows beyond the pot's ground shadow.

## Craft checklist (verify each one on a zoomed render before finishing)
1. **Joins**: every petiole/stem must visibly start inside the soil opening (hidden by the rim)
   and end *tucked under* its leaf base / sinus — never stopping in mid-air, never poking out
   past a leaf, never floating a leaf off its stem. Stem width should taper and match the
   size of what it holds.
2. **Colour separation**: two shapes that overlap or touch must differ clearly in tone
   (≥1–2 palette steps) — typically back leaves darker, front leaves lighter/warmer. No two
   same-colour leaves overlapping into one blob. Check stems against the leaves behind them
   too (a mid-green stem across a mid-green leaf disappears).
3. **Overlap decisively or not at all**: avoid tangents (edges just kissing), slivers, and
   tiny awkward gaps. Overlaps should read as clear foreground/background.
4. **Silhouette & rhythm**: asymmetric but balanced; varied leaf sizes and angles; no
   mechanical even spacing or mirror symmetry; a clear focal mass. Negative space between
   leaves should be pleasant shapes.
5. **Detail hierarchy**: veins/patterns thinner and lower contrast than silhouettes; pattern
   marks sit inside leaves (clip them), follow the leaf's structure (veins radiate from the
   midrib toward the tip, etc.), and are consistent in weight across the image.
6. **Readability small**: render at 150 px wide and confirm the species is recognisable and
   not a muddy mass.
7. **Clean geometry**: no self-intersecting outlines, no kinks/cusps unless intended (leaf
   tips), smooth curves, sensible node count. Keep file size reasonable (< ~60 KB).
8. Botanical plausibility: leaves attach the way the real plant's do.

## Process
Iterate: draw → render full size → render 2–3× zoom crops of the joins and overlaps → fix →
repeat. Do at least 3 review passes. Be your own harsh art director. When done, write a
final render to `/home/claude/work/v4/out/<name>.png` (600x800 on cream) and reply with a
3–5 line summary of what you did and any residual concerns.

## Addendum — set expansion (new species)
The 14-plant v4 set is finished and approved in direction. See the contact sheet
`/home/claude/work/v4/v4_contact_sheet.png` and look at 2–3 finished generators in
`/home/claude/work/v4/species/` (e.g. `spathiphyllum.py`, `epipremnum_aureum.py`,
`strelitzia_reginae.py`) plus their SVGs in `out/`. Your new plant must sit in that set
seamlessly: same pot family and scale, same flat half-leaf shading language, same line
weights for veins/midribs, similar overall plant mass and height, same tonal-depth logic.
It should also have a **distinct silhouette** from the existing 14 so cards are
distinguishable at a glance.
Scratch files: use only your own subfolder `<scratchpad>/<name>/` — other agents work in parallel.
Keep the SVG under ~60 KB (reusing shapes via `<use href>` is fine).
