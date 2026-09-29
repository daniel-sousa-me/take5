"""Card back — asymmetric botanical spray (after the client's mock-up).

Units: 0.1 mm. Trim = 0..635 x 0..880 (63.5 x 88 mm poker). Bleed 15 units (1.5 mm).
Design rules for hand cutting + manual duplex:
  * no frame, nothing that runs parallel to a cut edge
  * art only crosses the edges at the top-right and bottom-left corners, as organic shapes,
    so a 1-2 mm cut/registration drift just crops a leaf a little differently (check() asserts this and the
    berries' >= 1.2 mm clearance on every build)
  * paper is left unprinted (use ivory stock for the cream look) -> no big flat tint to band
  * lines >= 0.25 mm, light-on-dark lines >= 0.25 mm
"""
import os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
sys.path.insert(0, str(paths.PLANTS_DIR))
from core import Leaf, leaf_g, cr_path, ribbon, stem, line, T, f, uid, reset_ids
import deck

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
    right = [(0, 0), (0.12, width * 0.62), (0.35, width), (0.62, width * 0.82), (0.84, width * 0.42), (tip, width * 0.12)]
    left = [(0, 0), (0.12, width * 0.58), (0.36, width * 0.96), (0.63, width * 0.78), (0.85, width * 0.38), (tip, width * 0.1)]
    return Leaf(L, right, left, bend=bend)


def mix(a, b, t):
    """Solid blend of hex colours a -> b (t = 0..1): tints are pre-blended, never drawn with opacity."""
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02X}" for i in (1, 3, 5))


def leaf(x, y, rot, L, col, width=0.26, bend=0.08, side="r", flip=False, vein=True):
    """Leaf with a darker turned-away half (as on the card faces) and an opaque midrib 0.3 mm wide."""
    lf = leaf_shape(L, width, bend)
    light = col in (G["dark"], G["forest"], G["mid"])
    vcol = mix(col, G["vein_l"], 0.5) if light else mix(col, G["vein_d"], 0.4)
    return leaf_g(lf, col, shade=SHADE.get(col), side=side,
                  midrib=(vcol, 3.0, None, 0.08, 0.8) if vein else None,
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


def lily(x, y, rot, s, col, shade, hi, stamen_col):
    """Side-view lily opening upward; base at (x, y). Petals are long, pointed and curl outward."""
    g = [f'<g transform="{T(x, y, rot, s)}">']
    # back petals (in shade)
    for r, L, w, b in ((-14, 170, 0.20, 0.06), (22, 165, 0.20, -0.04)):
        g.append(leaf_g(petal(L, w, b), shade, transform=T(0, 0, r)))
    # stamens: long, arching up-right, anthers as small dots
    tips = [(40, -205), (78, -192), (108, -168), (128, -136)]
    for tx, ty in tips:
        g.append(line([(2, -30), (tx * 0.35, ty * 0.6), (tx, ty)], 2.6, stamen_col))
    for tx, ty in tips:
        g.append(dot(tx, ty, 8.5, MUSTARD))
    # front petals: two sweeping outward with curled tips, one centre petal in the light tone
    for r, L, w, b, c, sd in ((-36, 175, 0.21, -0.36, col, "l"), (46, 185, 0.21, 0.40, col, "r"),
                              (6, 140, 0.19, 0.10, hi, None)):
        g.append(leaf_g(petal(L, w, b), c, shade=shade if sd else None, side=sd or "r", transform=T(0, 0, r)))
    # calyx cup
    g.append(f'<path d="M-24 4 C-22 -16 -10 -26 0 -26 C10 -26 22 -16 24 4 C12 14 -12 14 -24 4Z" fill="{G["forest"]}"/>')
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


BERRY_R = 17
BERRIES = ((104, 852), [((38, 770), -20), ((34, 845), 2), ((80, 814), -3)], STEM_R, BERRY_R, BERRY, BERRY_S)


def build_body():
    reset_ids()
    o = []
    CX = W / 2
    # ---------------------------------------------------------------- top-right spray: one sweep from the corner toward the title
    # kept a step lighter and thinner than the bottom arrangement so the wordmark stays the focal point
    tr = [(700, -60), (618, 30), (538, 100), (460, 148), (380, 178)]
    o.append(branch(tr, [(0.22, 138), (0.36, 132), (0.50, 124), (0.64, 108), (0.78, 90)], sides=[1, -1, 1, -1, 1], w0=6.5,
                    w1=2.8, back_cols=[G["mid"], G["sage"]], front_cols=[G["sage"], G["sage"], G["light"]], tip=(66, G["light"])))
    o.append(sprig((470, 144), [((440, 206), -5), ((474, 222), 5), ((506, 204), 6)], STEM_G, 11, MUSTARD, MUSTARD_S, w=2.8))

    # ---------------------------------------------------------------- bottom-left arrangement
    # One bunch: every stem springs from the bottom-left corner (the only place, with the top-right,
    # where the art crosses the cut) -- the upright sweep, the berries, the lily and the right sweep.
    # right sweep: low arc out to the right, echoing the top-right spray; stays >= 1 mm above the bottom cut
    br = [(70, 930), (170, 856), (290, 830), (400, 804), (470, 788), (520, 780), (552, 776)]
    o.append(branch(br, [(0.52, 98), (0.65, 80), (0.78, 96), (0.90, 62)], angle=38,
                    back_cols=[G["forest"], G["dark"]], front_cols=[G["sage"], G["mid"]], tip=(56, G["light"]), first=1, w0=7, w1=3))
    # berries branch off the upright stem (drawn first so the join sits under the stem)
    # all three berries sit fully inside the trim (>= 1.2 mm, see check()), none cut by the left edge; stalks go under the
    # upright stem, the berries themselves are drawn after it so the leaves don't hide them
    berries = BERRIES
    o.append(sprig(*berries, w=3.4, part="stalks"))
    # lily stem forks off the upright stem low down
    o.append(stem([(100, 890), (150, 862), (212, 842), (256, 818)], 7, 4, STEM_G))
    # upright sweep: up the left side, ending in a mustard sprig
    bl = [(85, 945), (106, 830), (100, 720), (108, 620)]
    o.append(branch(bl, [(0.24, 160), (0.43, 136), (0.61, 100), (0.80, 90)],
                    back_cols=[G["dark"], G["forest"]], front_cols=[G["mid"], G["sage"]], first=1, w0=8))
    o.append(sprig(*berries, w=3.4, part="dots"))
    o.append(sprig((108, 622), [((72, 566), -6), ((112, 544), 4), ((152, 570), 6)], STEM_G, 16, MUSTARD, MUSTARD_S))
    o.append(lily(258, 824, 10, 0.74, ORANGE, ORANGE_S, ORANGE_HI, "#D9A04A"))

    # ---------------------------------------------------------------- wordmark
    ink = deck.C["deep"]      # the darkest, largest element on the back: the eye lands here first
    title = ('<g fill="%s">' % ink
             + deck.LABEL_FONT.path("TAKE", 126, 318, 380, track=0.04)
             + "</g>"
             + '<g fill="%s">' % ink + deck.PathFont(deck.FONT).path("5", 218, 318, 540) + "</g>")
    o.append(title)
    return "".join(o)


BERRY_MIN = 12       # berries stay >= 1.2 mm inside the trim
CORNER_R = 220       # art may reach into the bleed / the 1 mm band inside the cut only within 22 mm of the
EDGE_BAND = 10       # top-right and bottom-left trim corners


def berry_circles():
    """(x, y, r) of the burgundy berries, exactly as sprig() draws them."""
    return [(tx, ty, BERRY_R * (0.85 + 0.3 * ((tx * 7 + ty * 3) % 10) / 10)) for (tx, ty), _ in BERRIES[1]]


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
    print("back edge check ok; berry clearance to the trim (mm):", check())
    paths.BUILD.mkdir(exist_ok=True)
    svg = standalone(str(paths.BUILD / "card_back.svg"))
    guide = svg.replace("</svg>", f'<rect x="{deck.B}" y="{deck.B}" width="{deck.TW}" height="{deck.TH}" fill="none" stroke="#f0f" stroke-width="0.12"/></svg>')
    cairosvg.svg2png(bytestring=guide.encode(), write_to=str(paths.BUILD / "card_back_preview.png"), output_width=int(deck.CW * 10), background_color="#FBF6EA")
