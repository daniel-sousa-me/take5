"""Card back — asymmetric botanical spray (after the client's mock-up).

Units: 0.1 mm. Trim = 0..635 x 0..880 (63.5 x 88 mm poker). Bleed 15 units (1.5 mm).
Design rules for hand cutting + manual duplex:
  * no frame, nothing that runs parallel to a cut edge
  * art only crosses the edges at the top-right and bottom-left corners, as organic shapes,
    so a 1-2 mm cut/registration drift just crops a leaf a little differently (check() asserts this and the
    berries' >= 2.0 mm clearance on every build: a manual duplex flip can drift 1-2 mm, and a berry
    must never be cut)
  * paper is left unprinted (white stock) -> no big flat tint to band
  * no colour in the pale speckle band (L* 88-95, C* <= 25): check() asserts it
  * lines >= 0.25 mm, light-on-dark lines >= 0.25 mm (the midribs taper below that only in their last few mm)
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
sys.path.insert(0, str(paths.PLANTS_DIR))
from core import Leaf, leaf_g, cr_path, ribbon, stem, line, T, f, uid, reset_ids
import deck
from print_prep import STOCK, lab, paper_white, speckle_band

G = dict(dark="#3F5A3C", forest="#4B6843", mid="#607B52", sage="#7F9468", light="#9DAE88",
         vein_d="#2F4630", vein_l="#C9D2BC")
# turned-away half of each leaf: a darker solid, the same step as the card-face plants (plants/core.py SHADE)
SHADE = {G["dark"]: "#2E4530", G["forest"]: "#3A5436", G["mid"]: "#4C6441",
         G["sage"]: "#687D55", G["light"]: "#859771"}
BERRY, BERRY_S = "#7E3B3E", "#6A2F33"
MUSTARD, MUSTARD_S = "#D2A13E", "#B98A2E"
ORANGE, ORANGE_S, ORANGE_HI = "#C8744E", "#AF5F3E", "#D68C68"   # a notch softer than the first #CF6A3C so the
                                                                  # lily stays second to the wordmark
RED, RED_S, RED_HI = "#A9463A", "#91392F", "#BE5B4B"
STEM_G, STEM_R = "#4B6843", "#6E3538"

BLEED = 15
W, H = 635, 880


def leaf_shape(L, width=0.26, bend=0.08, tip=0.92):
    # the last node sits wide enough (0.22-0.24 of the width) that the Catmull-Rom outline runs straight into the
    # sharp tip; a narrower last node (0.1-0.12) pinched the tip into a little hook that read as a notch at zoom
    right = [(0, 0), (0.12, width * 0.62), (0.35, width), (0.62, width * 0.82), (0.80, width * 0.52), (tip, width * 0.24)]
    left = [(0, 0), (0.12, width * 0.58), (0.36, width * 0.96), (0.63, width * 0.78), (0.81, width * 0.48), (tip, width * 0.22)]
    return Leaf(L, right, left, bend=bend)


def mix(a, b, t):
    """Solid blend of hex colours a -> b (t = 0..1): tints are pre-blended, never drawn with opacity."""
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02X}" for i in (1, 3, 5))


VEIN_PALE = "#E1E6D6"   # midrib mix target only (a pale sage); the midribs themselves stay at L* <= VEIN_MAX_L
VEIN_DL = 20.0          # every midrib sits this many L* above its leaf, so the veins read alike on every tone ...
VEIN_MAX_L = 87.5       # ... but never above L* 87.5, under the L* 88-95 speckle band (only the lightest leaf, #9DAE88,
                        # is capped: its midrib was #DCE2D0 at L* 89)


def vein_col(col):
    """Pale midrib for a leaf of colour col: the solid mix of col -> VEIN_PALE that is VEIN_DL L* lighter.
    Every leaf on the back gets the same kind of vein (a pale line, like the bottom-left bunch had);
    before, the lighter top-right leaves had dark veins, which read as a smudge at card size."""
    L0 = lab(col)[0]
    lo, hi = 0.0, 1.0
    for _ in range(20):
        t = (lo + hi) / 2
        lo, hi = (t, hi) if lab(mix(col, VEIN_PALE, t))[0] < min(L0 + VEIN_DL, VEIN_MAX_L) else (lo, t)
    return mix(col, VEIN_PALE, hi)


MIDRIB_W0, MIDRIB_W1, MIDRIB_T1 = 4.0, 1.6, 0.86   # 0.40 mm at the leaf base -> 0.16 mm, ending short of the tip


def midrib(lf, col):
    """Tapered pale midrib, as on the card faces: it starts at the leaf base, where the leaf meets the stem (the
    leaf clip trims it to the leaf there, so it runs into the stalk with no end cap), and narrows to a point-like
    end at MIDRIB_T1 of the length. A plain round-capped stroke stopping at both ends read as a floating dash."""
    pts = [lf.axis(-0.04 + (MIDRIB_T1 + 0.04) * i / 8) for i in range(9)]
    return f'<path d="{ribbon(pts, MIDRIB_W0, MIDRIB_W1)}" fill="{col}"/>'


def leaf(x, y, rot, L, col, width=0.26, bend=0.08, side="r", flip=False, vein=True):
    """Leaf with a darker turned-away half (as on the card faces) and a pale tapered midrib (midrib() above)."""
    lf = leaf_shape(L, width, bend)
    vcol = vein_col(col) if vein else None
    return leaf_g(lf, col, shade=SHADE.get(col), side=side,
                  extra=(lambda l: midrib(l, vcol)) if vein else None,
                  transform=T(x, y, rot, 1, -1 if flip else 1))


def dot(x, y, r, col, shade=None):
    s = f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{col}"/>'
    return s


def sprig(base, tips, col, r, dcol, dshade, w=3.2, part="both"):
    """Thin stems from base to each tip, each ending in a dot (part: "both", "stalks" or "dots")."""
    out = []
    for (tx, ty), bend in (tips if part != "dots" else []):
        mx, my = (base[0] + tx) / 2 + bend, (base[1] + ty) / 2
        out.append(line([base, (mx, my), (tx, ty)], w, col))
    for (tx, ty), _ in (tips if part != "stalks" else []):
        rr = r * (0.85 + 0.3 * ((tx * 7 + ty * 3) % 10) / 10)
        out.append(dot(tx, ty, rr, dcol, dshade))
    return "".join(out)


def petal(L, width, bend, tip=0.97):
    right = [(0, 0), (0.18, width * 0.5), (0.45, width), (0.72, width * 0.78), (0.9, width * 0.32)]
    left = [(0, 0), (0.18, width * 0.42), (0.45, width * 0.86), (0.72, width * 0.62), (0.9, width * 0.26)]
    return Leaf(L, right, left, bend=bend, tip_t=tip)


# lily stamens in flower-local units (base at 0,0, opening toward -y): (filament base, bend point, anther, anther
# tilt deg). Deliberately irregular -- lengths, spread and curvature all differ, and one leans to the left -- so they
# don't fan out at equal angle steps with the anthers on a neat arc. The tallest stays left of centre, keeping the
# flower >= 11 mm from the "5" (check() asserts TITLE_GAP).
STAMENS = [((-3, -30), (-30, -120), (-58, -172), 20),
           ((0, -32), (-8, -128), (24, -210), -15),
           ((3, -30), (40, -118), (74, -176), 10),
           ((5, -28), (46, -96), (118, -150), -25),
           ((6, -26), (58, -78), (106, -116), 5)]
# filament width in flower units: 3.2 x the lily's 0.72 scale x 0.1 mm = 0.23 mm printed (mustard is light on the white
# stock, so it gets more than the 0.15 mm dark-line minimum; the old 2.6 printed 0.19 mm and looked faint)
STAMEN_W = 3.2


# lily calyx in flower-local units (petal bases at 0,0, flower opening toward -y). The stem (LILY_STEM) arrives
# from the left, nearly level, and ends inside the receptacle; the outline starts and ends on the stem's edges at
# x = -31 so the green runs on without a step. Sepal tips: left (-31, -31), centre (1, -43), right (33, -27).
CALYX = ("M-31 8.5 C-24 7.9 -18 6 -15 -1 C-20 -10 -26 -19 -31 -31 C-22 -25 -14 -19 -8 -14 "
         "C-6 -23 -3 -33 1 -43 C5 -33 8 -23 9 -14 C16 -20 25 -24 33 -27 C30 -16 24 -2 16 6 "
         "C10 12 0 14.2 -8 14.2 C-16 14.2 -24 14.4 -31 14.8Z")
# turned-away half: the centre sepal's right side, the right sepal and the receptacle's right flank
CALYX_SHADE = ("M1 -43 C5 -33 8 -23 9 -14 C16 -20 25 -24 33 -27 C30 -16 24 -2 16 6 C13.5 8.5 11.5 10 9.5 11 "
               "C6 2 5 -8 3.5 -20 C2.8 -30 1.9 -37 1 -43Z")


def lily(x, y, rot, s, col, shade, hi, stamen_col):
    """Side-view lily opening upward; base at (x, y). Petals are long, pointed and curl outward."""
    g = [f'<g transform="{T(x, y, rot, s)}">']
    # back petals (in shade)
    for r, L, w, b in ((-14, 170, 0.20, 0.06), (22, 165, 0.20, -0.04)):
        g.append(leaf_g(petal(L, w, b), shade, transform=T(0, 0, r)))
    # stamens: STAMENS below -- uneven lengths and spread, one leaning left, anthers as small tilted ovals
    for (bx, by), (mx, my), (tx, ty), _ in STAMENS:
        g.append(line([(bx, by), (mx, my), (tx, ty)], STAMEN_W, stamen_col))
    for (bx, by), (mx, my), (tx, ty), a in STAMENS:
        ang = math.degrees(math.atan2(ty - my, tx - mx)) + 90 + a
        g.append(f'<ellipse cx="{f(tx)}" cy="{f(ty)}" rx="10.5" ry="6" fill="{MUSTARD}" transform="rotate({f(ang)} {f(tx)} {f(ty)})"/>')
    # front petals: two sweeping outward with curled tips, one centre petal in the light tone
    for r, L, w, b, c, sd in ((-36, 175, 0.21, -0.36, col, "l"), (46, 185, 0.21, 0.40, col, "r"),
                              (6, 140, 0.19, 0.10, hi, None)):
        g.append(leaf_g(petal(L, w, b), c, shade=shade if sd else None, side=sd or "r", transform=T(0, 0, r)))
    # calyx: CALYX below -- three pointed sepals cupping the petal bases over a rounded receptacle that narrows into
    # the stem (same green as the stem, so the join is seamless); the right half a shade darker, like the leaves
    g.append(f'<path d="{CALYX}" fill="{G["forest"]}"/><path d="{CALYX_SHADE}" fill="{SHADE[G["forest"]]}"/>')
    g.append("</g>")
    return "".join(g)


def branch(pts, leaves, back_cols, front_cols, width=0.2, angle=46, w0=8, w1=3.2, tip=None, first=1, sides=None):
    """Stem along pts with leaves at arc fractions. leaves = [(frac, L)], sides alternate.
    Leaves on the far side are drawn behind the stem in darker tones, near-side leaves in front."""
    from plants_a import along
    behind, front = [], []
    side = first
    for i, ((p, r), (fr, L)) in enumerate(zip(along(pts, [fr for fr, _ in leaves]), leaves)):
        if sides:
            side = sides[i]
        rot = r + side * angle
        if side > 0:
            front.append(leaf(p[0], p[1], rot, L, front_cols[i % len(front_cols)], width=width, bend=-0.12, side="l"))
        else:
            behind.append(leaf(p[0], p[1], rot, L, back_cols[i % len(back_cols)], width=width, bend=0.12, side="r"))
        side = -side
    out = "".join(behind) + stem(pts, w0, w1, STEM_G) + "".join(front)
    if tip:
        (p, r), = along(pts, [1.0])
        out += leaf(p[0], p[1], r, tip[0], tip[1], width=width, bend=0.1, side="r")
    return out


LILY = (268, 810, -8, 0.72)                              # flower base x, y, rotation, scale
LILY_STEM = [(100, 876), (136, 850), (196, 828), (236, 824), (262, 817)]
BR = [(70, 930), (170, 868), (290, 845), (400, 806), (470, 788), (520, 780), (552, 776)]   # low right sweep
BERRY_R = 17
# the top berry sits in the open paper under the upright's dark lowest leaf (at (38, 770) it lay on that leaf,
# burgundy on dark green: too little contrast); the low one moved a touch right/down to keep a clear gap to it.
# The two left-hand berries moved in from (32, 806) / (36, 848) (1.65 / 1.45 mm from the trim) so every berry is
# >= 2.0 mm inside it (BERRY_MIN; now 2.05 at the closest), keeping ~1 mm of paper to each other and to the leaf
BERRIES = ((104, 852), [((36, 810), 4), ((55, 845), 2), ((80, 814), -3)], STEM_R, BERRY_R, BERRY, BERRY_S)


def build_body():
    return "".join(s for _, s in build_parts())


def build_parts():
    """The back's layers in drawing order as (name, svg) pairs (build_body joins them); names let check()
    measure the paper between neighbouring elements."""
    reset_ids()
    o = _Parts()
    CX = W / 2
    # ---------------------------------------------------------------- top-right spray: one sweep from the corner toward the title
    # kept a step lighter and thinner than the bottom arrangement so the wordmark stays the focal point
    tr = [(700, -60), (618, 30), (538, 100), (460, 148), (380, 178)]
    o.append(branch(tr, [(0.22, 138), (0.36, 132), (0.50, 124), (0.64, 90), (0.78, 90)], sides=[1, -1, 1, -1, 1], w0=6.5,
                    w1=2.8, back_cols=[G["mid"], G["sage"]], front_cols=[G["sage"], G["sage"], G["light"]], tip=(66, G["light"])), "tr")
    # two berries here (the bottom-left mustard sprig and the burgundy cluster have three each), splayed unevenly
    o.append(sprig((462, 147), [((420, 204), -8), ((470, 226), 5)], STEM_G, 11, MUSTARD, MUSTARD_S, w=2.8), "tr_sprig")

    # ---------------------------------------------------------------- bottom-left arrangement
    # One bunch: every stem springs from the bottom-left corner (the only place, with the top-right,
    # where the art crosses the cut) -- the upright sweep, the berries, the lily and the right sweep.
    # right sweep: low arc out to the right, echoing the top-right spray; stays >= 1 mm above the bottom cut
    br = BR
    o.append(branch(br, [(0.52, 98), (0.65, 80), (0.78, 96), (0.90, 62)], angle=38,
                    back_cols=[G["forest"], G["dark"]], front_cols=[G["sage"], G["mid"]], tip=(56, G["light"]), first=1, w0=7, w1=3), "sweep")
    # berries branch off the upright stem (drawn first so the join sits under the stem)
    # all three berries sit fully inside the trim (>= 2.0 mm, see check()), none cut by the left edge; stalks go under the
    # upright stem, the berries themselves are drawn after it so the leaves don't hide them
    berries = BERRIES
    o.append(sprig(*berries, w=3.4, part="stalks"), "berry_stalks")
    # lily stem forks off the upright stem low down, rising steeper than the right sweep so the two splay apart
    # right from the corner instead of running side by side. The flower (LILY) sits high enough and turned a little
    # to the left so its lower right petal no longer runs along the sweep with a ~1 mm sliver of paper (it did at
    # (258, 824, 10deg, 0.74)): now >= 2 mm everywhere (LILY_GAP, asserted in check()), and its left petal
    # decisively overlaps the upright's big leaf instead of grazing it.
    o.append(stem(LILY_STEM, 7, 4, STEM_G), "lily_stem")
    # upright sweep: up the left side, ending in a mustard sprig
    bl = [(85, 945), (106, 830), (100, 720), (108, 620)]
    o.append(branch(bl, [(0.24, 160), (0.43, 136), (0.61, 100), (0.80, 90)],
                    back_cols=[G["dark"], G["forest"]], front_cols=[G["mid"], G["sage"]], first=1, w0=8), "upright")
    o.append(sprig(*berries, w=3.4, part="dots"), "berries")
    o.append(sprig((108, 622), [((72, 566), -6), ((112, 544), 4), ((152, 570), 6)], STEM_G, 16, MUSTARD, MUSTARD_S), "mustard")
    o.append(lily(*LILY, ORANGE, ORANGE_S, ORANGE_HI, "#D9A04A"), "lily")

    # ---------------------------------------------------------------- wordmark
    ink = deck.C["deep"]      # the darkest, largest element on the back: the eye lands here first
    title = ('<g fill="%s">' % ink
             + deck.LABEL_FONT.path("TAKE", 126, 318, 380, track=0.04)
             + "</g>"
             + '<g fill="%s">' % ink + deck.PathFont(deck.FONT).path("5", 218, 318, 540) + "</g>")
    o.append(title, "title")
    return o.items


class _Parts:
    def __init__(self):
        self.items = []

    def append(self, svg, name=""):
        self.items.append((name, svg))


BERRY_MIN = 20       # berries stay >= 2.0 mm inside the trim (manual duplex drift is 1-2 mm; no berry is ever cut)
CORNER_R = 220       # art may reach into the bleed / the 1 mm band inside the cut only within 22 mm of the
EDGE_BAND = 10       # top-right and bottom-left trim corners


def berry_circles():
    """(x, y, r) of the burgundy berries, exactly as sprig() draws them."""
    return [(tx, ty, BERRY_R * (0.85 + 0.3 * ((tx * 7 + ty * 3) % 10) / 10)) for (tx, ty), _ in BERRIES[1]]


LILY_GAP = 20        # >= 2 mm of paper between the lily (flower + stem) and the low sweep wherever they don't overlap
TITLE_GAP = 110      # >= 11 mm of paper between the lily and the "5" (the lily stays second to the wordmark)


def paper_gap(a_names, b_names, box=(60, 650, 560, 880), k=2, excl=20):
    """Shortest paper gap (body units) between layers a and b of the back, rendered at k px per unit inside box,
    ignoring the 'excl' units round any place where they overlap (a decisive crossing is fine; a near miss
    that runs alongside, i.e. a near-tangent, is not). Returns (gap, where, overlap px)."""
    import io, cairosvg, numpy as np
    from PIL import Image, ImageFilter
    parts = dict(build_parts())
    x0, y0, x1, y1 = box

    def mask(names):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{x1 - x0}" height="{y1 - y0}" '
               f'viewBox="{x0} {y0} {x1 - x0} {y1 - y0}">{"".join(parts[n] for n in names)}</svg>')
        return np.array(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=k))).convert("RGBA"))[..., 3] > 128

    def filt(m, flt):
        return np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(flt)) > 0
    a, b = mask(a_names), mask(b_names)
    ov = a & b
    near_ov = filt(ov, ImageFilter.MaxFilter(2 * excl * k + 1)) if ov.any() else np.zeros_like(a)
    ea = a & ~filt(a, ImageFilter.MinFilter(3)) & ~near_ov & ~b
    eb = b & ~filt(b, ImageFilter.MinFilter(3))
    ya, xa = np.nonzero(ea)
    yb, xb = np.nonzero(eb)
    best = (9e9, None)
    for i in range(0, len(xa), 400):
        D = np.hypot(xa[i:i + 400, None] - xb[None], ya[i:i + 400, None] - yb[None]).min(1)
        j = int(D.argmin())
        if D[j] < best[0]:
            best = (float(D[j]), (x0 + xa[i + j] / k, y0 + ya[i + j] / k))
    return best[0] / k, best[1], int(ov.sum())


def check(px_per_mm=10):
    """Assert the edge rules: berries fully inside the trim (>= BERRY_MIN), and ink in the bleed or within
    EDGE_BAND of a cut only near the top-right and bottom-left corners. Returns the berries' clearances (mm)."""
    import io, cairosvg, numpy as np
    from PIL import Image
    clear = []
    for x, y, r in berry_circles():
        c = min(x - r, y - r, W - x - r, H - y - r)
        assert c >= BERRY_MIN, f"berry at ({x}, {y}) only {c / 10:.2f} mm inside the trim"
        clear.append(round(c / 10, 2))
    k = px_per_mm / 10                                          # px per body unit
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W + 2 * BLEED + 200}" height="{H + 2 * BLEED + 200}" '
           f'viewBox="{-BLEED - 100} {-BLEED - 100} {W + 2 * BLEED + 200} {H + 2 * BLEED + 200}">{build_body()}</svg>')
    a = np.array(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=k))).convert("RGBA"))[..., 3] > 40
    ys, xs = np.nonzero(a)
    bx, by = xs / k - BLEED - 100, ys / k - BLEED - 100            # body units
    near_edge = (bx < EDGE_BAND) | (bx > W - EDGE_BAND) | (by < EDGE_BAND) | (by > H - EDGE_BAND)
    d_tr = np.hypot(bx - W, by)
    d_bl = np.hypot(bx, by - H)
    bad = near_edge & (d_tr > CORNER_R) & (d_bl > CORNER_R)
    assert not bad.any(), f"ink at the cut away from the two corners, e.g. {bx[bad][0]:.0f}, {by[bad][0]:.0f}"
    # the lily and the low sweep must not run side by side with a sliver of paper between them
    g, where, _ = paper_gap(["lily", "lily_stem"], ["sweep"])
    assert g >= LILY_GAP - 1, f"lily only {g / 10:.2f} mm from the low sweep near {where}"
    g5, where5, ov5 = paper_gap(["lily"], ["title"], box=(60, 300, 635, 880))
    assert g5 >= TITLE_GAP and not ov5, f"lily only {g5 / 10:.2f} mm from the \"5\" near {where5}"
    # white stock: no near-white that print_prep would send as bare paper, and no pale tint in the speckle band
    # (L* 88-95, C* <= 25), which a pigment inkjet prints as a sparse dither instead of an even tint
    import re
    cols = {c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}\b", build_body())}
    pale = sorted(c for c in cols if paper_white(c) and c != STOCK)   # #FFFFFF itself = no ink, fine
    assert not pale, f"near-white colours on the back (the {STOCK} stock shows through instead): {pale}"
    band = sorted(c for c in cols if speckle_band(c))
    assert not band, f"speckle-band colours (L* 88-95, C* <= 25) on the back: {band}"
    return clear


def back_group():
    """Card-local group in deck units (mm, envelope 0..CW x 0..CH incl. bleed)."""
    s = 0.1
    return f'<g transform="translate({deck.B} {deck.B}) scale({s})">{build_body()}</g>'


def standalone(path, scale_px=8):
    w, h = deck.CW, deck.CH
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">'
           f'<defs><clipPath id="bk"><rect width="{w}" height="{h}"/></clipPath></defs>'
           f'<g clip-path="url(#bk)">{back_group()}</g></svg>')
    open(path, "w").write(svg)
    return svg


if __name__ == "__main__":
    import cairosvg
    print("back edge check ok; berry clearance to the trim (mm):", check(),
          f"; lily-to-sweep paper {paper_gap(['lily', 'lily_stem'], ['sweep'])[0] / 10:.2f} mm"
          f"; lily-to-5 paper {paper_gap(['lily'], ['title'], box=(60, 300, 635, 880))[0] / 10:.2f} mm")
    paths.BUILD.mkdir(exist_ok=True)
    svg = standalone(str(paths.BUILD / "card_back.svg"))
    guide = svg.replace("</svg>", f'<rect x="{deck.B}" y="{deck.B}" width="{deck.TW}" height="{deck.TH}" fill="none" stroke="#f0f" stroke-width="0.12"/></svg>')
    cairosvg.svg2png(bytestring=guide.encode(), write_to=str(paths.BUILD / "card_back_preview.png"), output_width=int(deck.CW * 10), background_color=STOCK)  # preview on the white stock
