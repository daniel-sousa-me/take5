"""One-page A4 print proof for the real printer + stock, to run BEFORE the deck.
All content sits inside Canon's recommended print area for A4 on the GX5000 series
(y 45.8 .. 260.2 mm, x 5 .. 205 mm)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cairosvg, deck, paths
from print_prep import paper_white, speckle_band, lab as cielab

PAL = dict(night="#27392C", deep="#314B37", forest="#405D43", mid="#5B7458", sage="#7F9273",
           light="#A5B296", pale="#C9D2BC", terra="#B96E4A", soil="#5C4331", red="#B95850",
           burgundy="#74464D", blush="#D79C9A", mustard="#C49A41", amber="#D48A4C")
INK = "#333"
X0 = 14
# burgundy tone pairs that sit side by side on the cards: (colour a, colour b, label). Tradescantia zebrina's
# leaf centre bands, back tier -> middle -> front; oxalis_triangularis' leaf ramp steps (also the tradescantia
# undersides). Hex values as they appear in plants/out/*.svg -- update if those plants change.
BURG_PAIRS = [("#4A3441", "#5E3A40", "zebrina 0 / 1"), ("#5E3A40", "#6C4150", "zebrina 1 / 2"),
              ("#5E3A40", "#74464D", "wine / burgundy"), ("#74464D", "#8A5560", "burgundy / plum")]
TIER_CARDS = ((1, 4), (2, 25), (3, 30), (5, 22), (7, 55))   # section 5: one real card per tier, neighbours side by side
CARD_S = 0.54     # section 5 card scale (five trim-wide cards across x 14..196 mm, ~2.6 mm apart)
NUM3_CARDS = (100, 104)   # section 4: 3-digit numbers at 100 %, top-left corner of the trim
NUM3_W, NUM3_H, X3 = 30.0, 24.0, 133   # crop (mm) and left edge of that test
# section 3: near-white cream tints (C* ~8) on the WHITE stock, lightest first: L* 97, 94, 92, 90, 87. The first is
# what print_prep sends as no ink (L* >= 95, "*"), the next two sit in the speckle band (L* 90-95, "!"); 90 and 87
# are the pale tints the plants may use. The proof prints them all as drawn, to show where the printer stops dithering a speckle
# and lays down an even tint.
TINTS = ("#FEF5E7", "#F5EDDE", "#F0E7D9", "#EAE1D3", "#E1D9CB")
# ... plus, last in the row, the pot ground shadow: the opaque pre-blended solid every pot stands on
# (plants/core.py pot(), L* 89.5, just under the speckle band), so it is judged on the real card. Update if pot() changes.
POT_SHADOW = "#DEE2DF"
CROP = 30.5       # section 5: card shown from the top cut down to this depth (mm), just below two rows of marks


# Text is set in the deck's own fonts, drawn as paths (like the card labels, deck.PathFont): DM Serif Display for
# the title and headings, Fraunces for the rest -- a regular-weight instance at the 9 pt optical size, made once
# into build/fonts beside the deck's Medium one. Paths need no installed font and measure exactly (fits() below).
# (deck.text_font(), shared with the sheet headers).


BODY, BOLD, HEAD = deck.text_font(), deck.LABEL_FONT, deck.PathFont(str(paths.DM_SERIF))


def t(x, y, s, size=2.4, font=None):
    return f'<g fill="{INK}">' + (font or BODY).path(s, size, float(x), y, anchor="start") + "</g>"


def tw(s, size=2.4, font=None):
    return (font or BODY).width(s, size)


def h(y, s):
    return t(X0, y, s, 3.4, HEAD)


def card_top(n):
    """Card-local top half of card n exactly as deck.card() draws it (colour field + sprig in the top-right
    corner, number + penalty marks from deck.info_block top-left), without the plant and name label."""
    p = deck.penalty(n)
    tint, acc, spr, ncol, gcol = deck.TIER[p]
    block, _, _ = deck.info_block(n, p, ncol, gcol)
    field = (f'<g transform="translate({deck.CW} 0) scale(-1 1) scale({deck.FIELD_SCALE})">'
             + deck.field_blob(tint, acc) + deck.sprig(spr) + "</g>")
    return field + block


def check_burg_pairs():
    """Warn if a BURG_PAIRS colour no longer occurs in the plants it was read from."""
    src = "".join((paths.PLANTS_SRC / f"{n}.svg").read_text() for n in ("tradescantia_zebrina", "oxalis_triangularis"))
    miss = sorted({c for a, b, _ in BURG_PAIRS for c in (a, b) if c.upper() not in src.upper()})
    if miss:
        print("proof: burgundy test colours no longer in the plant art:", ", ".join(miss))


def fits(s, x0, x1, size, font=None):
    """Assert a line of text set at x0 ends by x1 (text is paths, so its width is exact)."""
    assert x0 + tw(s, size, font) <= x1, f"proof text overruns {x1} mm: {s!r}"


def build():
    check_burg_pairs()
    g = ['<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">',
         '<rect width="210" height="297" fill="#fff"/>']
    y = deck.REC_TOP + 4.6
    g.append(t(X0, y, "Take 5 · Botanical — print proof (GX5050, 250 gsm uncoated)", 5.0, HEAD))
    intro = ("Rear tray, one sheet at a time · 100% / Actual size · borderless OFF · Prevent paper abrasion ON. Print once per",
             "paper-type setting, tick it below, dry 10 min, judge. Then print deck sheet 1 on the same setting: cut one card, try it in a 66 × 91 mm sleeve.")
    for i, s in enumerate(intro):
        g.append(t(X0, y + 5.5 + i * 3.5, s, 2.4))
        fits(s, X0, 196, 2.4)

    # 1 — line weights  (row pitch 8.0: 6.5 mm swatches, 1.5 mm between rows)
    y += 15.5
    g.append(h(y, "1  Line weights (mm) — thinnest line that stays clean and unbroken"))
    ws = [0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30]
    rows = [("dark on paper", "#fff", PAL["deep"]), ("paper on dark", PAL["deep"], "#fff"),
            ("blush on night", PAL["night"], PAL["blush"]), ("pale on forest", PAL["forest"], PAL["pale"])]
    for i, w in enumerate(ws):
        g.append(t(52 + i * 21 + 4, y + 4.5, f"{w:.2f}", 2.2))
    for r, (lab, bg, fg) in enumerate(rows):
        yy = y + 6 + r * 8.0
        g.append(t(X0, yy + 4.4, lab, 2.4))
        for i, w in enumerate(ws):
            x = 52 + i * 21
            g.append(f'<rect x="{x}" y="{yy}" width="18" height="6.5" fill="{bg}"/>')
            g.append("".join(f'<path d="M{x + 2.5 + k * 4.3} {yy + 0.8}v4.9" stroke="{fg}" stroke-width="{w}"/>' for k in range(4)))
    g.append(t(52, y + 39.6, "The artwork uses ≥ 0.15 mm for dark lines and ≥ 0.20 mm for light-on-dark lines.", 2.3))

    # 2 — tone steps: the palette's adjacent leaf greens, then the burgundy pairs that meet on the cards
    # (read from plants/out/tradescantia_zebrina.svg and oxalis_triangularis.svg, see BURG_PAIRS)
    y += 47          # ~3.5 mm of paper between the caption above and this heading
    g.append(h(y, "2  Leaf tone steps — each pair must still read as two different tones"))
    order = ["night", "deep", "forest", "mid", "sage", "light", "pale"]
    pairs = [(PAL[a], PAL[b], f"{a} / {b}") for a, b in zip(order, order[1:])]
    pitch, k, sep = 17.9, 0.75, 3.0          # 6 green + 4 burgundy pairs across x 14..196 mm
    for i, (ca, cb, lab) in enumerate(pairs + BURG_PAIRS):
        x = X0 + i * pitch + (sep if i >= len(pairs) else 0)
        yy = y + 3
        g.append(f'<g transform="translate({x:.2f} {yy}) scale({k})">'
                 f'<path d="M0 15 C0 5 9 2 14 2 C14 11 7 16.5 0 15Z" fill="{ca}"/>'
                 f'<path d="M7 17 C7 8 16 5 22 5 C22 14 14 18.5 7 17Z" fill="{cb}"/></g>')
        g.append(t(f"{x:.2f}", yy + 16.5, lab, 2.0))
        fits(lab, x, x + pitch - 0.6, 2.0)
    note2 = ("If a pair merges (most likely night/deep, deep/forest or the two darkest burgundies), note which — the darks can be lifted.",
             "Burgundies: Tradescantia leaf bands (tiers 0|1, 1|2) and the oxalis / tradescantia leaf ramp (wine|burgundy, burgundy|plum).")
    for i, s in enumerate(note2):
        g.append(t(X0, y + 23.8 + i * 3.2, s, 2.3 - 0.2 * i))
        fits(s, X0, 196, 2.3 - 0.2 * i)

    # 3 — flat fields + solids
    y += 31.8
    g.append(h(y, "3  Flat colour — look for banding or grain; dry-rub the solids; near-white tints (bottom row)"))
    for i, p in enumerate([1, 2, 3, 5, 7]):
        tint, acc, sprig, ncol, gcol = deck.TIER[p]
        x = X0 + i * 37
        g.append(f'<rect x="{x}" y="{y + 3}" width="34" height="13" fill="{tint}"/>'
                 f'<path d="M{x} {y + 16} C{x + 10} {y + 14} {x + 18} {y + 7} {x + 34} {y + 6} V{y + 16}Z" fill="{acc}"/>'
                 f'<rect x="{x + 23}" y="{y + 4.8}" width="9" height="4.3" fill="{gcol}"/>'
                 f'<path d="M{x + 3} {y + 13.2} C{x + 7} {y + 9} {x + 12} {y + 7} {x + 18} {y + 6}" fill="none" '
                 f'stroke="{sprig}" stroke-width="0.45" stroke-linecap="round"/>'
                 f'<rect x="{x + 23}" y="{y + 10.1}" width="9" height="4.3" fill="{ncol}"/>')
        g.append(t(x, y + 19.3, f"penalty {p} field", 2.2))
    for i, k in enumerate(["terra", "soil", "red", "burgundy", "blush", "mustard", "amber", "deep"]):
        g.append(f'<rect x="{X0 + i * 23}" y="{y + 21.3}" width="20" height="6" fill="{PAL[k]}"/>')
        g.append(t(X0 + i * 23, y + 30, k, 2.2))
    # near-white tints, printed as drawn: each as a patch on bare paper (grey corner ticks 0.6 mm outside it) and
    # as a stripe down a leaf-green bar (chlorophytum's cream stripe, the spathe's light half). Tints marked * are
    # near-whites (L* >= 95) that print_prep.py sends as no ink (#FFFFFF) in the plant print copies; ! marks the
    # speckle band (L* 90-95), which it prints as drawn but warns about.
    # (2.5+ mm of paper between the solid labels and the tick marks above the tints)
    # patch 6 wide, green bar 4.4 wide (the pot shadow: a terracotta bar, as it meets the pot), label, then >= 1.5 mm
    # of paper before the next patch's corner ticks (the labels used to run into them); the legend ends >= 6 mm
    # inside x 196
    ty, th, tp, pw, bx, bw, lx, fs = y + 35, 4.5, 24.2, 6.0, 7.2, 4.4, 12.6, 1.9
    row = [(c, c + ("*" if paper_white(c) else "!" if speckle_band(c) else ""), None, PAL["mid"]) for c in TINTS]
    row.append((POT_SHADOW, POT_SHADOW, "pot shadow", PAL["terra"]))
    for i, (c, lbl, sub, bar) in enumerate(row):
        x = X0 + i * tp
        k6, e = 0.6, 1.2
        ticks = "".join(f'M{cx + sx * k6} {cy + sy * k6 - sy * e}v{sy * e}h{-sx * e}'
                        for cx, cy, sx, sy in ((x, ty, -1, -1), (x + pw, ty, 1, -1), (x, ty + th, -1, 1), (x + pw, ty + th, 1, 1)))
        g.append(f'<path d="{ticks}" fill="none" stroke="#999" stroke-width="0.12"/>'
                 f'<rect x="{x}" y="{ty}" width="{pw}" height="{th}" fill="{c}"/>'
                 f'<rect x="{x + bx}" y="{ty}" width="{bw}" height="{th}" fill="{bar}"/>'
                 f'<rect x="{x + bx + (bw - 1.4) / 2}" y="{ty}" width="1.4" height="{th}" fill="{c}"/>')
        end = x + tp - 0.6 - 1.5                       # next patch's ticks start 0.6 mm left of it
        if sub:                                        # two lines: hex, then what it is
            g.append(t(x + lx, ty + 1.9, lbl, fs) + t(x + lx, ty + 4.3, sub, 1.7))
            fits(sub, x + lx, end, 1.7)
        else:
            g.append(t(x + lx, ty + 3.1, lbl, fs))
        fits(lbl, x + lx, end, fs)
    assert not (paper_white(POT_SHADOW) or speckle_band(POT_SHADOW)), POT_SHADOW
    Ls = " · ".join(f"{cielab(c)[0]:.0f}" for c in TINTS) + f" · {cielab(POT_SHADOW)[0]:.1f}"
    lx0 = X0 + len(row) * tp + 1.4
    for i, s in enumerate((f"L* {Ls}", "* no ink on cards · ! speckle band")):
        g.append(t(lx0, ty + 1.7 + i * 2.9, s, 2.0 - 0.2 * i))
        fits(s, lx0, 190, 2.0 - 0.2 * i)

    # 4 — scale + setting log  (heading ~3 mm below the tints' lower tick marks)
    y += 46
    g.append(h(y, "4  Scale"))
    g.append(f'<path d="M{X0} {y + 6}h100M{X0} {y + 4.5}v3M{X0 + 100} {y + 4.5}v3" stroke="#333" stroke-width="0.25"/>')
    g.append(t(X0 + 100 - tw("must measure 100 mm", 2.4), y + 3.6, "must measure 100 mm", 2.4))
    g.append(f'<rect x="{X0}" y="{y + 8.5}" width="30" height="30" fill="none" stroke="#333" stroke-width="0.25"/>')
    g.append(t(X0 + 15 - tw("30 × 30 mm", 2.4) / 2, y + 24.3, "30 × 30 mm", 2.4))
    x5 = 70
    g.append(t(x5, y + 13, "Setting used (tick one):", 2.8, BOLD))
    for i, o in enumerate(["Plain Paper · High", "Plain Paper · Standard", "Matte Photo Paper", "Other: ______________"]):
        yy = y + 19 + i * 5.2
        g.append(f'<rect x="{x5}" y="{yy - 2.8}" width="3.2" height="3.2" fill="none" stroke="#333" stroke-width="0.25"/>')
        g.append(t(x5 + 5, yy, o, 2.4))
    # 3-digit numbers at 100 %: the top-left corner of real cards 100 and 104 (deck.info_block, as on the card),
    # the tightest digit pairs in the deck (0|0 and 0|4, opened to deck.DIGIT_GAP)
    g.append(t(X3, y, "3-digit numbers, 100 % — no digit may touch", 2.5, BOLD))
    fits("3-digit numbers, 100 % — no digit may touch", X3, 196, 2.5, BOLD)
    for j, n in enumerate(NUM3_CARDS):
        x, yy = X3 + j * (NUM3_W + 2), y + 3
        cid = f"n3{n}"
        g.append(f'<defs><clipPath id="{cid}"><rect x="{deck.B}" y="{deck.B}" width="{NUM3_W}" height="{NUM3_H}"/></clipPath></defs>'
                 f'<g transform="translate({x:.3f} {yy:.3f}) translate({-deck.B} {-deck.B})">'
                 f'<g clip-path="url(#{cid})">{card_top(n)}</g></g>'
                 f'<rect x="{x:.3f}" y="{yy:.3f}" width="{NUM3_W}" height="{NUM3_H}" fill="none" stroke="#bbb" stroke-width="0.15"/>')
        g.append(t(x, yy + NUM3_H + 2.8, f"card {n} · {NUM3_W:g} × {NUM3_H:g} mm", 2.2))
    assert X3 + 2 * NUM3_W + 2 <= 196
    # 5 — neighbouring tiers as they really print: the top of real cards, drawn with the deck's own functions
    # (card_top below = the top half of deck.card: field + sprig top-right, number + marks top-left), without
    # the plant and name label, cropped below the marks and shown at CARD_S scale
    y += 42.3
    head5 = "5  Neighbouring tiers — each neighbour (1|2, 2|3, 3|5, 5|55) must read as a different penalty"
    g.append(h(y, head5))
    fits(head5, X0, 196, 3.4, HEAD)
    nc = len(TIER_CARDS)
    pw, ph = deck.TW * CARD_S, CROP * CARD_S
    gap = (196 - X0 - nc * pw) / (nc - 1)
    assert gap >= 2.0, gap
    for j, (p, n) in enumerate(TIER_CARDS):
        x, yy = X0 + j * (pw + gap), y + 3
        cid = f"tc{n}"
        g.append(f'<defs><clipPath id="{cid}"><rect x="{deck.B}" y="{deck.B}" width="{deck.TW}" height="{CROP}"/></clipPath></defs>'
                 f'<g transform="translate({x:.3f} {yy:.3f}) scale({CARD_S}) translate({-deck.B} {-deck.B})">'
                 f'<g clip-path="url(#{cid})">{card_top(n)}</g></g>'
                 f'<rect x="{x:.3f}" y="{yy:.3f}" width="{pw:.3f}" height="{ph:.3f}" fill="none" stroke="#bbb" stroke-width="0.15"/>')
        g.append(t(x, yy + ph + 2.8, f"tier {p} · card {n}", 2.2))
        fits(f"tier {p} · card {n}", x, min(x + pw + gap - 0.8, 196), 2.2)
    note5 = (f"Top {CROP:g} mm of each real card (number, penalty marks, corner field), at {CARD_S * 100:g} %. "
             "1|2 (sage / ochre) is the pair met most often in play.")
    g.append(t(X0, yy + ph + 6.0, note5, 2.1))
    fits(note5, X0, 196, 2.1)
    assert yy + ph + 6.5 <= deck.REC_BOT, yy + ph + 6.5
    g.append("</svg>")
    return "".join(g)


if __name__ == "__main__":
    svg = build()
    paths.BUILD.mkdir(exist_ok=True)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=str(paths.BUILD / "take5_print_proof_A4.pdf"))
