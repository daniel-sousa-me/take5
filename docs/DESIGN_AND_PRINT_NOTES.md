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
- `print_prep.py` makes a print copy of each plant, measured at that plant's own scale on the card
  (`deck.plant_scales()`, the smallest it is drawn anywhere in the deck; plants run 0.050–0.065 mm per unit),
  through every transform and `<use>`. Minimums: dark lines ≥ 0.15 mm, light-on-dark lines ≥ 0.20 mm; dots
  and filled slivers ≥ 0.175 mm dark / ≥ 0.225 mm light (these are the plant policy's 3.0 / 4.0 / 3.5 / 4.5
  units at 0.050 mm/unit). A line under its minimum is:
  - **dropped** if it is translucent (element × stroke × every ancestor group/`<use>` opacity < 1): widening a
    see-through line only makes a pale wash with ghost end caps;
  - **widened** if it is opaque, by at most 1.6× (2.0× when every copy of it sits inside a clip-path, i.e. inside
    its leaf, so it cannot spill); one that needs more is **dropped** (a fattened hairline reads as a bar).
  A filled shape only loses its stroke; an outline in the shape's own fill colour is left alone. Dots and slivers
  are never changed, only reported. The plant masters are drawn to these rules, so a compliant master passes
  through unchanged (`ok (unchanged)` in the build output); `python deck/print_prep.py -v` lists the rest.
- **Paper-white.** The stock is ivory (`STOCK` = `#F3EBDA` in `print_prep.py`, L* ≈ 93). Ink only darkens paper, so a
  colour at or lighter than the stock can't print as drawn: the driver leaves it blank or dithers a sparse speckle
  into it. `print_prep.py` sets every fill / stroke / stop colour with L* ≥ the stock's and chroma C* ≤ 15 (a near-
  neutral cream or white) to `#FFFFFF`, i.e. no ink, bare stock. Today that is `#FBF6EA` (`PAL["ivory"]`): chlorophytum's
  cream stripes (12 shapes), pilea (4), spathiphyllum's light spathe half (3), tradescantia (3), senecio's pearl
  highlight (1). It's informational, not a rule break: the masters keep their colour (right on screen), the plant still
  reports `ok (unchanged)` for the line rules, and the count is shown beside it as `[paper-white: N]` (`-v` lists the
  colours). Darker creams such as `#E8E2D1` (L* 90) print as a real tint and are left alone. The card face itself
  has nothing lighter than the stock (tier fields are L* ≤ 87; `PAPER_BG` is off, so `C["cream"]` `#F5EDDD` is unused;
  the sheet background is `#fff` = no ink); the shared pot ground shadow is `deep` at 11 % opacity, ≈ `#E8EBE9` over
  paper, just under the stock's L* and meant as a faint shadow, so it stays. The back has no paper-white colour
  (`back.check()` asserts it).
- The pot band (`pot(band=True)` in `plants/core.py`) is an opaque pre-blended line 4 units wide (a step
  darker again over the pot's shaded side), so masters and cards match.
- The proof page tests line weights, the leaf-green steps (plus four burgundy pairs that meet on the cards:
  Tradescantia's leaf-band tiers and the oxalis / tradescantia wine–burgundy–plum steps, `BURG_PAIRS` in
  `deck/proof.py`, which warns if those colours leave the plant art), the corner tints and solid colours, a row of near-paper tints (`TINTS` in `deck/proof.py`: `#FFFFFF`, `#FBF6EA`, `#F6EFDF`,
  `#F0E6D2`, `#EADFC8`, each as a patch on bare paper inside grey corner ticks and as a stripe down a leaf-green bar,
  printed as drawn; `*` marks the ones at or lighter than the stock, which the plant print copies send as no ink —
  check whether the unstarred `#F0E6D2` / `#EADFC8` print as a clean tint or as speckle), the
  scale, the 3-digit numerals at 100 % (the top-left 30 × 24 mm of real cards 100 and 104, the tightest digit pairs in the deck,
  so digit spacing can be judged on the real stock; the print-setting reminders that stood beside the scale test
  moved into the intro lines), and shows the neighbouring tiers side by side: the top 30.5 mm of real cards 25, 30, 22 and 55 (tiers 2, 3, 5, 7), drawn with
  the deck's own `info_block` / `field_blob` / `sprig` exactly as on the card (number top-left, marks 3 over 2 and
  4 over 3, field top-right; plant and label left out), at 68 % so four fit inside the recommended area. The proof's text is set in the deck's
  own fonts, drawn as paths (DM Serif Display for the title and headings, Fraunces for the rest — Medium for the
  bold labels, a Regular opsz-9 instance made once into `build/fonts`), so it needs no installed font and every line's
  width is exact: `proof.fits()` asserts that each label and note ends inside its column. Sections have ≥ 2.5 mm of
  paper between a caption and the next heading, and around the near-paper tint row (whose note is 2.2 mm text, the
  same as the other labels). If a green
  pair merges on the real card (most likely night/deep or deep/forest), lift the darks in `plants/core.py`
  `PAL`/`SHADE` and rebuild.

## Card face

- Number (DM Serif Display, ~13.6 mm cap) centred on an axis 0.5 mm outside the ¼ line (`NUM_AXIS`; the most
  that keeps 88/99 off the 5 mm EDGE, and it moves the bottom-right block that much further from the pot),
  5 mm from the top cut; its 180° twin at the bottom right. 100–104 are too wide and shift in just enough to
  keep 5 mm clear. 100–104 use a size step smaller (`NUM_SIZE_3` 18.5, cap ~12 mm) with tighter tracking,
  and their plant is lifted (≈ 0.5 mm) so the pot clears the bottom-right number by `POT_GAP` = 4 mm; before, the
  wide numeral sat ~2 mm under the pot as if the pot stood on it.
- Digit spacing (`pair_advance` in `deck/deck.py`): advance + tracking (−0.02 em; −0.045 on 100–104), then
  each neighbouring pair is opened just enough to leave `DIGIT_GAP` = 0.6 mm of paper between the two glyphs'
  ink (0.5 mm minimum + 0.1 mm for ink spread on uncoated card), measured as the true shortest distance between
  the outlines. On 100–104 every pair is also closed to at most 1.0 mm (`DIGIT_GAP_MAX_3`), so the loose 1|0
  (1.44 mm before) doesn't split "100" into "1 00" and the numeral stays as wide as it was. Before this the
  two zeros of 100 overlapped and 104's 4 ran into the 0. Tightest pairs now: 71, 77, 100 (0|0), 104 (0|4) at
  0.60 mm, 11 at 0.61; every other pair is wider. `deck.py` asserts the minimum on every build and prints the
  tightest five; `deck.digit_gaps(n)` gives the gaps of any number. 6/9-style ambiguous numbers get a conventional underline: the full width of the numeral ink
  (less 0.3 mm each end), centred, 0.7 mm thick.
- Penalty = repeated wilted-leaf marks centred under the number: 1–3 in one row, 5 as 3 over 2, 7 as 4 over 3
  (4.0 mm marks, 0.8 mm apart, rows 0.7 mm apart; a row never crosses the EDGE line).
  The mark is a stem that bends over at the top with a broad ovate leaf hanging limp from the bend, widest near
  its stalk and tapering to a pointed tip straight down, plus a small drooping leaf lower on the stem; solid
  silhouette, stroke 0.34 mm, no inner midrib (a paper-coloured midrib made an early mark read as a coffee bean
  at card size). It replaced a narrower crook-and-pod mark that read as a cane at small sizes.
  Rules: 55 → 7, other multiples of 11 → 5, multiples of 10 → 3, other multiples of 5 → 2, else 1.
- Colour corners (top-right and bottom-left, opposite the numbers) show the penalty tier; organic shapes that
  cross the cut so drift is invisible. No frame anywhere. Five hue families so a tier reads at a glance:
  1 sage `#D8DDBF`, 2 ochre `#EFD8A0`, 3 terracotta `#F0C4A4`, 5 dusty rose `#D8A3B0` (burgundy number
  `#6A3A45`; the rose is ~10 L* darker and redder than tier 3 — ΔE ≈ 25 — so the two can't drift together on
  uncoated stock), and 55 alone in bird-of-paradise orange `#E38E62` with a burnt-orange number and marks `#A8452A`.
  Numbers on 1–3 are deep green; each tier's marks take a darker shade of its field hue. The small sprig in
  each field is a visibly darker (or, on 55, lighter) tone of the field, not a 5 % step that vanishes in print.
- Plant: every pot stands on the same base point (bottom centre at x = 31.75, y = 68.6 mm card-local incl.
  bleed, just left of centre so the bottom-right block lands beside the narrow pot rather than under the leaves).
  Size is normalised per plant from its ink box: a blend of height-fit (0.6) and area-fit (0.4), damped
  (^0.8) and clamped to 0.92–1.2 × the reference scale of 0.054 mm/unit (≈ 40 mm for the full 740-unit canvas,
  ≈ 35.5 mm of actual ink for a typical plant), with the pot rim capped at 13.5 mm so squat plants in wide
  bowls don't balloon. Each plant is then checked against the ink boxes of the numbers, marks, underline,
  name label and corner fields of every card it appears on (≥ 1.2 mm from numbers, underline and label,
  ≥ 2.0 mm from the penalty marks, and inside the 5 mm EDGE) and
  takes the largest scale that fits all of them, so a species is the same size everywhere; a plant blocked
  by the bottom-right block may slide up to 3 mm left instead of shrinking (string of pearls, spider plant, wax plant).
  Card 55 is the one exception to "same size everywhere" (`SHOWPIECE`): its bird of paradise is drawn as large as
  fits, up to 1.15× its species size, still checked against the same obstacles, with 2.0 mm (`SHOWPIECE_MARK_CLEAR`)
  round the top-left marks and 3.5 mm (`SHOWPIECE_BR_CLEAR`) round the whole bottom-right block (number and its
  7 marks), which sits right beside the pot on the busiest card (currently ≈ 1.05×, pot on the standard base point;
  ≈ 4.6 mm of ink-to-ink paper to the bottom-right marks, ≈ 3.4 mm from the pot rim to the nearest mark column,
  ≈ 3.7 mm to the top-left marks; before, at 1.08× with the pot 1 mm right, the bottom-right corner felt crowded).
- Plant name (common + botanical, Fraunces) runs up the right edge, 5 mm from the cut. Common name in forest
  green `#405D43`; botanical name in italic warm grey-brown `#625444` (darker than the first `#7A6A58`, which was
  too faint on ivory stock).
- Showy plants go on the high-penalty cards (bird of paradise on 55; flowering/striking plants on the other
  multiples of 11). Other plants cycle; no two consecutive numbers share a plant; each plant appears 4–5 times.

## Card back

- Asymmetric spray: one sweep in from the top-right corner (five leaves, and three mustard berries fanned
  on stalks into open space below the stem, clear of the hanging leaves), and one
  bunch rising from the bottom-left corner: an upright stem with a mustard sprig, burgundy berries on stalks that
  branch off it, a lily stem forking off it low down, and a low sweep arcing out to the right. Every stem of the
  bunch springs from the corner, so nothing floats and nothing crosses the bottom cut mid-width. Leaves are
  placed along their stems at a constant angle, alternating sides and shrinking to the tip. Like the card-face
  plants, each leaf has a darker turned-away half (a solid, about the same step as `plants/core.py` `SHADE`) and an
  opaque pre-blended midrib 0.3 mm wide; no opacity anywhere on the back. Every midrib is a pale line 20 L* above its
  leaf (`vein_col()`: a solid mix toward `VEIN_PALE` `#E1E6D6`, still darker than the stock). Before, the lighter
  top-right leaves had dark midribs and the bottom-left bunch pale ones; the pale line reads crisper at card size.
- The lily (`LILY` = base (268, 810), −8°, 0.72 in 0.1 mm units) sits a little higher and turned slightly left of its
  first place, so its lower right petal no longer runs along the low sweep with ~1 mm of paper between them (a
  near-tangent): now ≥ 2 mm of paper everywhere between the lily (flower + stem) and the sweep (2.2 mm at the closest;
  `LILY_GAP`, asserted by `back.check()` via `paper_gap()`, which ignores the paper right beside a decisive overlap), its
  left petal clearly overlaps the upright's big leaf, and it stays ≥ 11 mm from the "5" (11.5 mm now; `TITLE_GAP`,
  also asserted by `back.check()`).
- Lily stamens (`STAMENS` in `deck/back.py`): five, deliberately irregular — different lengths, spread and curvature,
  one leaning left, the tallest left of centre (away from the "5") — with small tilted oval anthers, instead of four
  fanned to one side at equal angle steps with round anthers on a neat arc.
- Leaf outline (`leaf_shape()`): the last node before the sharp tip sits at ~0.22–0.24 of the leaf width, so the
  outline runs straight into the point; the old narrower node (0.10–0.12) pinched the tip into a small hook that
  read as a notch at zoom.
- The three burgundy berries sit fully inside the trim (≥ 1.2 mm; currently 1.8 mm at the closest), fanned out on
  stalks from one point on the upright stem, drawn in front of the upright stem's leaves.
- Art only crosses the cut at those two corners (within 22 mm of them), and only as leaves and stems (no berry is
  cut in half); everything else stays ≥ 1 mm inside,
  so cutting or duplex drift just crops a leaf differently. `back.check()` asserts both rules on every build
  (rasterises the back and looks for ink in the bleed or the 1 mm band inside the cut away from the two corners).
- The "TAKE 5" wordmark is the focal point: deep green (`#314B37`), the largest and darkest element. The
  top-right sweep is drawn a step lighter (mid/sage/light greens), with shorter leaves and a thinner stem than
  the bottom arrangement, and the lily is a little smaller, sits low (≥ 11 mm from the "5") and is a
  softer orange (`#C8744E`, shade `#AF5F3E`) than its first `#CF6A3C`, so neither competes with the title.

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
