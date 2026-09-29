# Design and print notes

Decisions made during the September 2026 sessions, and why. The 24 Sep handoff in this folder is kept
for history; where it disagrees with this file, this file wins (card size and print area changed).

## Printer and paper

- Canon MAXIFY GX5050: four pigment inks, up to 600 × 1200 dpi. Strong on plain/uncoated paper; can show
  slight banding in smooth tints; no borderless mode.
- Canon's GX5000-series A4 figures: printable area 200 × 287 mm (5 mm margin all round). **Recommended**
  area leaves 45.8 mm at the top and 36.8 mm at the bottom, where "feeding precision or print quality may
  be affected". Everything in these files (cards, crop marks, sheet labels) sits inside the recommended area.
- Stock: 250 gsm uncoated, loaded one sheet at a time in the rear tray.

## Card size and sheet layout

- Poker size, 63.5 × 88 mm, 1.5 mm bleed on every side → 66.5 × 91 mm per card.
- 6 per A4: 2 columns × 3 rows, cards turned 90°. Block 182 × 199.5 mm, centred in the recommended area
  (x 14–196 mm, y 53.25–252.75 mm). 18 sheets for 104 cards.
- Poker is the largest standard size that fits 6-up inside the recommended area. Sleeves: 66 × 91 mm.
- Crop marks (3 mm long, 1.5 mm off the art) sit outside the cards; neighbouring cards keep their own bleed.

## Ink on uncoated card

- Paper is left unprinted behind the art (no full-bleed cream): less ink, flatter card, no banding in a big
  tint. Ivory/natural stock gives the cream look.
- No transparency tricks on the card face; tints are pre-blended solids.
- `print_prep.py` makes a print copy of each plant, sized for that plant's own scale on the card
  (`deck.plant_scales()`, the smallest it is drawn anywhere in the deck):
  dark lines ≥ 0.15 mm, light-on-dark lines ≥ 0.20 mm, faint (opacity < 0.34) hairlines under 0.3 mm removed.
- The proof page tests line weights, the leaf-green steps, the corner tints and solid colours. If a green
  pair merges on the real card (most likely night/deep or deep/forest), lift the darks in `plants/core.py`
  `PAL`/`SHADE` and rebuild.

## Card face

- Number (DM Serif Display, ~13.6 mm cap) centred on the ¼ line, 5 mm from the top cut; its 180° twin on
  the ¾ line at the bottom. 100–104 are too wide for the ¼ line and shift in just enough to keep 5 mm clear.
  6/9-style ambiguous numbers get an underline.
- Penalty = repeated wilted-leaf marks centred under the number: 1–3 in one row, 5 as 3 over 2, 7 as 4 over 3.
  The mark (~4.2 mm) is a stem that flops over into a crook with a pointed leaf hanging tip-down, plus a small
  drooping leaf lower on the stem; solid silhouette, no inner midrib (a paper-coloured midrib made the old
  mark read as a coffee bean at card size).
  Rules: 55 → 7, other multiples of 11 → 5, multiples of 10 → 3, other multiples of 5 → 2, else 1.
- Colour corners (top-right and bottom-left, opposite the numbers) show the penalty tier; organic shapes that
  cross the cut so drift is invisible. No frame anywhere. Five hue families so a tier reads at a glance:
  1 sage `#D8DDBF`, 2 ochre `#EFD8A0`, 3 terracotta `#F0C4A4`, 5 dusty rose `#E5B7BE` (burgundy number
  `#6A3A45`), and 55 alone in bird-of-paradise orange `#E38E62` with a burnt-orange number and marks `#A8452A`.
  Numbers on 1–3 are deep green; each tier's marks take a darker shade of its field hue. The small sprig in
  each field is a visibly darker (or, on 55, lighter) tone of the field, not a 5 % step that vanishes in print.
- Plant: every pot stands on the same base point (bottom centre at x = 31.75, y = 68.6 mm card-local incl.
  bleed, just left of centre so the bottom-right block lands beside the narrow pot rather than under the leaves).
  Size is normalised per plant from its ink box: a blend of height-fit (0.6) and area-fit (0.4), damped
  (^0.8) and clamped to 0.92–1.2 × the reference scale of 0.054 mm/unit (≈ 40 mm for the full 740-unit canvas,
  ≈ 35.5 mm of actual ink for a typical plant), with the pot rim capped at 13.5 mm so squat plants in wide
  bowls don't balloon. Each plant is then checked against the ink boxes of the numbers, marks, underline,
  name label and corner fields of every card it appears on (≥ 1.2 mm gap, and inside the 5 mm EDGE) and
  takes the largest scale that fits all of them, so a species is the same size everywhere; a plant blocked
  by the bottom-right block may slide up to 3 mm left instead of shrinking (string of pearls, spider plant, wax plant).
- Plant name (common + botanical, Fraunces) runs up the right edge, 5 mm from the cut.
- Showy plants go on the high-penalty cards (bird of paradise on 55; flowering/striking plants on the other
  multiples of 11). Other plants cycle; no two consecutive numbers share a plant; each plant appears 4–5 times.

## Card back

- Asymmetric spray: one sweep in from the top-right corner, one arrangement rising from the bottom-left,
  one orange lily; leaves placed along their stems at a constant angle, alternating sides and shrinking to the tip.
- Art only crosses the cut at those two corners; everything else stays ≥ 1 mm inside, so cutting or duplex
  drift just crops a leaf differently.
- The "TAKE 5" wordmark is the focal point: deep green (`#314B37`), the largest and darkest element. The
  top-right sweep is drawn a step lighter (mid/sage/light greens), with shorter leaves and a thinner stem than
  the bottom arrangement, and the lily is a little smaller, so neither competes with the title.

## Printing sequence

1. `take5_print_proof_A4.pdf` on the real card; try Plain Paper · High and Matte Photo Paper; tick the box,
   let it dry, judge the blocks. Check the 100 mm line.
2. Deck sheet 1 on the chosen setting; cut one card, try it in a 66 × 91 mm sleeve.
3. All 18 deck sheets. Let them dry fully.
4. Before committing card, test the duplex path on plain paper: mark a corner, print a front, feed it back,
   print the back sheet, and check alignment against a light.
5. Back sheet on the reverse of each deck sheet: turn the sheet over **left-to-right** (long-edge flip),
   same edge leading into the rear tray.
6. Cut on the crop marks.
