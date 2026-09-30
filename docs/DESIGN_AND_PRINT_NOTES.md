# Design and print notes

Decisions made during the September 2026 sessions, and why. The 24 Sep handoff in this folder is kept
for history; where it disagrees with this file, this file wins (card size and print area changed).

## Printer and paper

- Canon MAXIFY GX5050: four pigment inks, up to 600 × 1200 dpi. Strong on plain/uncoated paper; can show
  slight banding in smooth tints; no borderless mode.
- Canon's GX5000-series A4 figures: printable area 200 × 287 mm (5 mm margin all round). **Recommended**
  area leaves 45.8 mm at the top and 36.8 mm at the bottom, where "feeding precision or print quality may
  be affected". Everything in these files (cards, crop marks, sheet labels) sits inside the recommended area.
- Sheet header lines (deck and backs sheets, `deck.sheet_header()`) are set in Fraunces Regular (opsz 9, the proof's
  body font, `deck.text_font()`) drawn as paths, 2.0 mm, grey, 5.2 mm above the card block; no installed font is
  needed and the header asserts it stays inside the recommended area and ends within the block width.
- Stock: 250 gsm uncoated **white** card, loaded one sheet at a time in the rear tray. Judge every render on white.

## Card size and sheet layout

- Poker size, 63.5 × 88 mm, 1.5 mm bleed on every side → 66.5 × 91 mm per card.
- 6 per A4: 2 columns × 3 rows, cards turned 90°. Block 182 × 199.5 mm, centred in the recommended area
  (x 14–196 mm, y 53.25–252.75 mm). 18 sheets for 104 cards.
- Poker is the largest standard size that fits 6-up inside the recommended area. Sleeves: 66 × 91 mm.
- Crop marks (3 mm long, 1.5 mm off the art) sit outside the cards; neighbouring cards keep their own bleed.

## Ink on uncoated card

- Paper is left unprinted behind the art (no full-bleed tint): less ink, flatter card, no banding in a big
  tint. The card is white; the art is designed and checked on white.
- No transparency on the card face: every tint, shade and shadow is an opaque, pre-blended solid (the card
  fields, the marks, the name labels, the pot band and the pot ground shadow; the pot's remaining shading overlays
  are being pre-blended in `plants/core.py` `pot()` the same way). `print_prep.py` still drops any translucent
  hairline it finds in a plant master (below).
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
- **White stock: paper-white and the speckle band.** The stock is white (`STOCK` = `#FFFFFF` in `print_prep.py`).
  Ink only darkens paper, and a pigment inkjet lays a very light colour down as a sparse dither of dots rather
  than an even tint. So, for every fill / stroke / stop colour:
  - **L* ≥ 95 and C* ≤ 15 → paper-white** (a near-neutral white, cream or pale grey): `print_prep.py` sets it to `#FFFFFF` (no ink, the bare paper shows). A colour meant
    to look white should simply be `#FFFFFF` in the master. Informational, not a rule break: the master keeps its
    colour, the plant still reports `ok (unchanged)` for the line rules, and the count is shown beside it as
    `[paper-white: N]` (`-v` lists the colours).
  - **88 < L* < 95 and C* ≤ 25 → speckle band** (`SPECKLE_MIN_L` / `SPECKLE_MAX_C`): too light for an even tint,
    and not a white to send as paper. It is printed as drawn but reported per plant as a warning,
    `[speckle-band: N]` (`-v` lists each colour with its L* / C*). The fix belongs in the master: move the colour
    to L* ≤ 88 (a real pale tint, e.g. `#E1D9CB`) or to `#FFFFFF`. The band used to be C* ≤ 15 and L* > 90; it was
    widened because pale creams and yellows dither just the same (the anthurium spadix `#EFE3BC`, L* 90.3, C* 21,
    escaped it) and L* 88 leaves a margin under the ≈ L* 90 where the printer starts to lay an even tint. Against the
    masters before the 29 Sep art pass, the wider band flagged every plant (the old pot ground shadow `#DEE2DF`,
    L* 89.5) plus anthurium `#EFE3BC`, echeveria `#D5E1D8` / `#DCE4DC`, hoya `#F0DAD0`, pilea `#DAE0CF` / `#DCE2D1`,
    string of pearls `#DFE1CD`, peace lily `#E3E2D1` and inch plant `#E0E3D3`; those were all moved below L* 88.
  - **otherwise** (L* ≤ 88, or more saturated): prints as a visible, even tint; left alone.
  Current build: no plant reports any paper-white or speckle-band colour (see the `print_prep.py` output). The
  card face has nothing above L* 87 (the lightest is the tier-1 sage field `#D8DDBF`); `deck.face_colour_check()`
  asserts on every build that no tier colour, name label or `PAPER_BG` is a near-white or in the band (`PAPER_BG`
  is off; the old cream `C["cream"]` `#F5EDDD`, L* 94, would now be refused). The sheet background is `#fff` =
  no ink. The back's lightest colour is a midrib at L* 87.6 (`VEIN_MAX_L`); `back.check()` asserts no near-white and
  nothing in the speckle band there. The shared pot ground shadow (`plants/core.py` `pot()`) is an opaque solid,
  `#D8DCD9` (L* 87.4, `deep` over white at ≈ 18 % pre-blended), under every pot: just below the speckle band, so it
  should print as an even pale tint. It replaced `#DEE2DF` (L* 89.5, inside the widened band) and, before that, an
  11 %-opacity `deep` ellipse that landed at ≈ `#E8EBE9` (L* 93).
  Judge it on the proof's tint row (last patch, "pot shadow"); if it still speckles, darken it a step in `pot()`
  and in `POT_SHADOW` in `deck/proof.py`.
- The pot band (`pot(band=True)` in `plants/core.py`) is an opaque pre-blended line 4 units wide (a step
  darker again over the pot's shaded side), so masters and cards match.
- The proof page tests line weights, the leaf-green steps (plus four burgundy pairs that meet on the cards:
  Tradescantia's leaf-band tiers and the oxalis / tradescantia wine–burgundy–plum steps, `BURG_PAIRS` in
  `deck/proof.py`, which warns if those colours leave the plant art), the corner tints and solid colours, a row of near-white cream tints (`TINTS` in `deck/proof.py`, C* ≈ 8 at L* 97, 94, 92, 90, 87:
  `#FEF5E7`, `#F5EDDE`, `#F0E7D9`, `#EAE1D3`, `#E1D9CB`, each as a patch on bare white paper inside grey corner ticks
  and as a stripe down a leaf-green bar, all printed as drawn, followed by the pot ground shadow `#D8DCD9`
  (`POT_SHADOW`, L* 87.4, labelled "pot shadow", its stripe down a terracotta bar as it meets the pot); `*` marks the one at L* ≥ 95 that the plant print copies
  send as no ink, `!` the three in the L* 88–95 speckle band — check where the printer stops speckling and lays an
  even tint: `#E1D9CB` (L* 87) should be clean; if `#EAE1D3` (L* 90) is clean too, `SPECKLE_MIN_L` could move back up
  toward 90; if L* 87 still speckles, lower it and the plant tints accordingly), the
  scale, the 3-digit numerals at 100 % (the top-left 30 × 24 mm of real cards 100 and 104, the tightest digit pairs in the deck,
  so digit spacing can be judged on the real stock; the print-setting reminders that stood beside the scale test
  moved into the intro lines), and shows the neighbouring tiers side by side: the top 30.5 mm of real cards 4, 25, 30, 22 and 55 (tiers 1, 2, 3, 5, 7, so
  1|2 — sage / ochre, the pair met most often in play — is judged too), drawn with
  the deck's own `info_block` / `field_blob` / `sprig` exactly as on the card (number top-left, marks 3 over 2 and
  4 over 3, field top-right; plant and label left out), at 54 % so five fit across inside the recommended area
  (`TIER_CARDS` / `CARD_S`; short labels, with the crop and scale in one note line below). The proof's text is set in the deck's
  own fonts, drawn as paths (DM Serif Display for the title and headings, Fraunces for the rest — Medium for the
  bold labels, a Regular opsz-9 instance made once into `build/fonts`), so it needs no installed font and every line's
  width is exact: `proof.fits()` asserts that each label and note ends inside its column. Sections have ≥ 2.5 mm of
  paper between a caption and the next heading, and around the near-white tint row. In that row each paper patch is 6 mm wide and its hex label
  (1.9 mm text) is asserted to end ≥ 1.5 mm before the next patch's corner ticks; the legend (2.0 mm text) ends
  ≥ 6 mm inside the 196 mm column edge. If a green
  pair merges on the real card (most likely night/deep or deep/forest), lift the darks in `plants/core.py`
  `PAL`/`SHADE` and rebuild.

## Card face

- Number (DM Serif Display, ~13.6 mm cap) centred on an axis 0.5 mm outside the ¼ line (`NUM_AXIS`; the most
  that keeps 88/99 off the 5 mm EDGE, and it moves the bottom-right block that much further from the pot),
  5 mm from the top cut; its 180° twin at the bottom right, drawn at 80 % (`TWIN_NUM_SCALE`; the penalty marks
  keep their full size). The top-left index is the one seen in a hand fan; the twin is read from across the
  table, where 80 % (cap ≈ 10.9 mm) is still large, and it frees the corner beside the pot: spider plant, Boston
  fern and peace lily no longer slide left, wax plant slides 1 mm instead of 3. 100–104 are too wide and shift in just enough to
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
  Numbers on 1–3 are deep green; each tier's marks take a darker shade of its field hue: 1 `#6B7C52`, 2 `#A0722C`,
  3 `#7E4630` (a dark brown-terracotta; the first `#A9583A` was almost the pot's `#B96E4A`, ΔE00 7.8, so on 10, 20
  and 100 the bottom-right marks read as part of the pot, and nearly tier 7's `#A8452A`, ΔE00 5.3; now ΔE00 17.5
  from the pot and 9.4 from tier 7, same hue angle), 5 `#86465A`, 7 `#A8452A`. The small sprig in
  each field is a visibly darker (or, on 55, lighter) tone of the field, not a 5 % step that vanishes in print.
- Plant: every pot stands on the same base point (bottom centre at x = 31.75, y = 68.6 mm card-local incl.
  bleed, just left of centre so the bottom-right block lands beside the narrow pot rather than under the leaves).
  Size is normalised per plant from its ink box: a blend of height-fit (0.6) and area-fit (0.4), damped
  (^0.8) and clamped to 0.92–1.2 × the reference scale of 0.054 mm/unit (≈ 40 mm for the full 740-unit canvas,
  ≈ 35.5 mm of actual ink for a typical plant), with the pot rim capped at 13.5 mm so squat plants in wide
  bowls don't balloon. Because the pot scales with its plant, each generator's `pot(rx=…, base_w=…)` is sized
  against that plant's fitted scale so the printed pots match side by side: every classic pot rim prints at
  10.3–10.9 mm (median ≈ 10.5 mm; the extremes are within ±3 % of the 10.6 mm middle), and the four succulent
  bowls (aloe, jade, echeveria, bunny ears) are allowed ≈ 8 % wider (≈ 11.3–11.4 mm). A plant whose fitted scale
  changes needs its pot `rx` re-checked (printed rim = 2 × rx × scale). Each plant is then checked against the ink boxes of the numbers, marks, underline,
  name label and corner fields of every card it appears on (≥ 1.2 mm from numbers, underline and label,
  ≥ 2.0 mm from the penalty marks — 2.75 mm (`MARK_CLEAR_2ROW`) from a two-row block (tier 5, 3 over 2), which
  looked crowded at 2.0 on 33 and 66 — and inside the 5 mm EDGE) and
  takes the largest scale that fits all of them, so a species is the same size everywhere; a plant blocked
  by the bottom-right block may slide up to 3 mm left instead of shrinking (now spider plant 1 mm; Boston fern, peace lily and Mexican snowball 2 mm;
  wax plant 3 mm; the wax plant is also 2 % smaller than its design size, for the tier-5 clearance on 33).
  Card 55 is the one exception to "same size everywhere" (`SHOWPIECE`): its bird of paradise is drawn as large as
  fits, up to 1.15× its species size, still checked against the same obstacles, with 2.0 mm (`SHOWPIECE_MARK_CLEAR`)
  round the top-left marks and 3.5 mm (`SHOWPIECE_BR_CLEAR`) round the whole bottom-right block (number and its
  7 marks), which sits right beside the pot on the busiest card (currently ≈ 1.05×, pot on the standard base point;
  ≈ 4.6 mm of ink-to-ink paper to the bottom-right marks, ≈ 3.4 mm from the pot rim to the nearest mark column,
  ≈ 3.7 mm to the top-left marks; before, at 1.08× with the pot 1 mm right, the bottom-right corner felt crowded).
- Plant name (common + botanical, Fraunces) runs up the right edge, 5 mm from the cut. Common name 3.3 mm
  (`COMMON_SIZE`, ≈ 9.4 pt, Fraunces Medium) in forest green `#405D43`; botanical name 2.5 mm (`LATIN_SIZE`,
  ≈ 7 pt) in upright Fraunces Regular at its 9 pt optical size, warm grey-brown `#625444`. Upright rather than
  the conventional italic: at this size the italic's thin, sloped strokes soften on uncoated card, and the smaller
  size and softer colour already set it apart. Baselines `LATIN_OFFSET` = 3.55 mm apart, leaving ≥ 0.9 mm of
  paper between the lines on every label (`deck.name_label_gap()`, asserted ≥ `LABEL_MIN_GAP` = 0.8 on every
  build). The common name's ascenders end on the 5 mm EDGE line (`LABEL_ASC`).
- Showy plants go on the high-penalty cards (bird of paradise on 55; flowering/striking plants on the other
  multiples of 11, `SHOWY_11`). Other plants cycle; no two consecutive numbers share a plant; each plant appears
  4–5 times. A predominantly burgundy/pink plant (purple shamrock, inch plant: `NOT_ON_ROSE`) never goes on a
  tier-5 (dusty rose field, burgundy marks) or tier-7 (orange) card — foliage, marks and field would be one hue
  family and the wilted-leaf marks would sink into the leaves; `assign()` asserts it. The purple shamrock used
  to be on 77; the Swiss cheese plant has that card now.

## Card back

- Asymmetric spray: one sweep in from the top-right corner (five leaves, and two mustard berries splayed
  unevenly on stalks into open space below the stem, clear of the hanging leaves — two rather than three so the
  berries-on-stalks motif isn't repeated identically by the bottom-left mustard sprig and burgundy cluster), and one
  bunch rising from the bottom-left corner: an upright stem with a mustard sprig, burgundy berries on stalks that
  branch off it, a lily stem forking off it low down, and a low sweep arcing out to the right. Every stem of the
  bunch springs from the corner, so nothing floats and nothing crosses the bottom cut mid-width. Leaves are
  placed along their stems at a constant angle, alternating sides and shrinking to the tip. Like the card-face
  plants, each leaf has a darker turned-away half (a solid, about the same step as `plants/core.py` `SHADE`) and an
  opaque pre-blended midrib; no opacity anywhere on the back. As on the card faces, each midrib runs from the leaf
  base, where it meets the stem, and tapers toward the tip (`midrib()`: a filled ribbon 0.40 → 0.16 mm ending at
  0.86 of the leaf length, clipped to the leaf so it has no end cap at the base); it replaced a 0.3 mm round-capped
  stroke that stopped inside the leaf at both ends and read as a floating dash. Every midrib is a pale line 20 L* above its
  leaf (`vein_col()`: a solid mix toward `VEIN_PALE` `#E1E6D6`, capped at `VEIN_MAX_L` = L* 87.5 so the lightest
  leaf's midrib, L* 87.6, stays below the L* 88 speckle band). Before, the lighter
  top-right leaves had dark midribs and the bottom-left bunch pale ones; the pale line reads crisper at card size.
- The lily (`LILY` = base (268, 810), −8°, 0.72 in 0.1 mm units) sits a little higher and turned slightly left of its
  first place, so its lower right petal no longer runs along the low sweep with ~1 mm of paper between them (a
  near-tangent): now ≥ 2 mm of paper everywhere between the lily (flower + stem) and the sweep (2.2 mm at the closest;
  `LILY_GAP`, asserted by `back.check()` via `paper_gap()`, which ignores the paper right beside a decisive overlap), its
  left petal clearly overlaps the upright's big leaf, and it stays ≥ 11 mm from the "5" (11.5 mm now; `TITLE_GAP`,
  also asserted by `back.check()`).
- Lily calyx (`CALYX` / `CALYX_SHADE` in `deck/back.py`): three small pointed sepals (left, centre, right) cupping the
  petal bases over a rounded receptacle that narrows into the stem, in the stem's own green so the join is seamless,
  with the right half a solid shade darker like the leaves. It replaced a plain half-disc cap. The lily stem
  (`LILY_STEM`) now ends low inside the receptacle, arriving nearly level from the left, instead of meeting the cap's side.
- Lily stamens (`STAMENS` in `deck/back.py`): five, deliberately irregular — different lengths, spread and curvature,
  one leaning left, the tallest left of centre (away from the "5") — with small tilted oval anthers, instead of four
  fanned to one side at equal angle steps with round anthers on a neat arc. Filaments are `STAMEN_W` = 3.2 units
  (× 0.72 × 0.1 mm = 0.23 mm printed): mustard is light on white card, so they get more than the 0.15 mm line minimum
  (the first 2.6 units, 0.19 mm, looked faint).
- Leaf outline (`leaf_shape()`): the last node before the sharp tip sits at ~0.22–0.24 of the leaf width, so the
  outline runs straight into the point; the old narrower node (0.10–0.12) pinched the tip into a small hook that
  read as a notch at zoom.
- The three burgundy berries sit fully inside the trim (≥ 2.0 mm, `BERRY_MIN`, since a manual duplex flip can drift
  1–2 mm; currently 2.05 mm at the closest, was 1.45 mm; ≈ 1 mm of paper between neighbouring berries), fanned out on
  stalks from one point on the upright stem, drawn in front of the upright stem's leaves. They sit in the open paper
  below the upright's dark lowest leaf; the top one used to lie on that leaf (burgundy on dark green, too little contrast).
- Art only crosses the cut at those two corners (within 22 mm of them), and only as leaves and stems (no berry is
  cut in half); everything else stays ≥ 1 mm inside,
  so cutting or duplex drift just crops a leaf differently. `back.check()` asserts both rules on every build
  (rasterises the back and looks for ink in the bleed or the 1 mm band inside the cut away from the two corners).
- The "TAKE 5" wordmark is the focal point: deep green (`#314B37`), the largest and darkest element. The
  top-right sweep is drawn a step lighter (mid/sage/light greens), with shorter leaves and a thinner stem than
  the bottom arrangement, and the lily is a little smaller, sits low (≥ 11 mm from the "5") and is a
  softer orange (`#C8744E`, shade `#AF5F3E`) than its first `#CF6A3C`, so neither competes with the title.

## Printing sequence

1. `take5_print_proof_A4.pdf` on the real white card; try Plain Paper · High and Matte Photo Paper; tick the box,
   let it dry, judge the blocks. Check the 100 mm line.
2. Deck sheet 1 on the chosen setting; cut one card, try it in a 66 × 91 mm sleeve.
3. All 18 deck sheets. Let them dry fully.
4. Before committing card, test the duplex path on plain paper: mark a corner, print a front, feed it back,
   print the back sheet, and check alignment against a light.
5. Back sheet on the reverse of each deck sheet: turn the sheet over **left-to-right** (long-edge flip),
   same edge leading into the rear tray.
6. Cut on the crop marks.
