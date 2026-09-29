"""Strelitzia reginae (bird of paradise) -- v4 botanical card art.

Run:  python3 species/strelitzia_reginae.py   -> out/strelitzia_reginae.svg
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, SHADE, uid, f, cr_path, cr_sample, ribbon, Leaf, T, pot, svg_doc, reset_ids  # noqa

P = PAL
CX, RIM_Y = 300, 586


# ------------------------------------------------------------------ helpers
def lerp(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def qpt(p0, p1, p2, s):
    return tuple((1 - s) ** 2 * p0[j] + 2 * (1 - s) * s * p1[j] + s * s * p2[j] for j in (0, 1))


def mix(a, b, t):
    """Opaque pre-blend of hex colour b over a at strength t (print policy: no translucent detail)."""
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02X}" for i in (1, 3, 5))


def lum(c):
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def world(x, y, rot, p):
    a = math.radians(rot)
    c, s = math.cos(a), math.sin(a)
    return (x + p[0] * c - p[1] * s, y + p[0] * s + p[1] * c)


# ------------------------------------------------------------------ leaf
# Oblong paddle: rounded (slightly oblique) base, near-parallel sides, blunt point.
RIGHT = [(0.012, 0.050), (0.05, 0.118), (0.12, 0.162), (0.25, 0.184), (0.45, 0.190),
         (0.64, 0.180), (0.79, 0.148), (0.90, 0.096), (0.965, 0.040)]
LEFT = [(0.012, 0.044), (0.06, 0.110), (0.14, 0.152), (0.28, 0.172), (0.47, 0.178),
        (0.66, 0.167), (0.80, 0.136), (0.91, 0.086), (0.967, 0.036)]
VDT = 0.085  # how far (in t) a lateral vein climbs between midrib and margin


def vein_ctrl(leaf, t0, sg, side):
    t2 = min(t0 + VDT, 0.985)
    p0 = leaf.axis(t0)
    p1 = leaf.pt(t0 + VDT * 0.30, sg * leaf.width(t0 + VDT * 0.30, side) * 0.55)
    p2 = leaf.pt(t2, sg * leaf.width(t2, side) * 1.08)
    return p0, p1, p2


def blade_outline(leaf, tears=()):
    """Outline with optional tears. tears: list of (side, t_margin, depth, gap)."""
    base = leaf.axis(0.0)
    tip = leaf.axis(1.0)
    sides = {}
    for side, sg in (("r", 1), ("l", -1)):
        nodes = list(leaf.right if side == "r" else leaf.left)
        pts = [(t, leaf.pt(t, sg * w), False) for t, w in nodes]
        for s_, tm, depth, gap in tears:
            if s_ != side:
                continue
            p0, p1, p2 = vein_ctrl(leaf, tm - VDT, sg, side)
            inner = qpt(p0, p1, p2, 1 - depth)
            dt = gap / leaf.L
            a = leaf.pt(tm - dt * 0.5, sg * leaf.width(tm - dt * 0.5, side))
            # distal flap sags a touch outward -> reads as a real split
            b = leaf.pt(tm + dt * 0.5, sg * (leaf.width(tm + dt * 0.5, side) + 0.004))
            pts = [q for q in pts if abs(q[0] - tm) > dt * 1.6]
            pts += [(tm - dt * 0.5, a, True), (tm, inner, True), (tm + dt * 0.5, b, True)]
        pts.sort(key=lambda q: q[0])
        sides[side] = pts
    ring = [(base, True)]
    ring += [(p, s) for _, p, s in sides["r"]]
    ring.append((tip, True))
    ring += [(p, s) for _, p, s in sides["l"][::-1]]
    sharp = {i for i, (_, s) in enumerate(ring) if s}
    return cr_path([p for p, _ in ring], closed=True, sharp=sharp)


def blade(x, y, rot, L, fill, bend=0.0, tears=(), vein_col=None, sx=1.0, flip=False):
    """Paddle leaf; petiole joins at (x, y); rot in degrees (0 = straight up)."""
    right, left = (LEFT, RIGHT) if flip else (RIGHT, LEFT)
    lf = Leaf(L, right, left, bend=bend)
    d = blade_outline(lf, tears)
    cid = uid("lc")
    shade = SHADE.get(fill, fill)
    # Print policy: the dense hairline lateral veins cannot print, so they are gone; the few irregular
    # pleat folds carry the leaf's texture instead, opaque (pre-blended per half) at print-safe weight.
    folds = {}
    for side, sg, ts in (("r", 1, (0.21, 0.43, 0.58)), ("l", -1, (0.30, 0.52, 0.71))):
        for t0 in ts:
            p0, p1, p2 = vein_ctrl(lf, t0, sg, side)
            folds.setdefault(side, []).append(f"M{f(p0[0])} {f(p0[1])}Q{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])}")
    fold_svg = ""
    for sd, base in (("r", shade), ("l", fill)):
        col = mix(base, P["night"], 0.13)
        # print_prep grades any line lighter than lum 0.55 as a knockout (needs 4 units)
        fw = 4 if lum(col) > 0.55 else 3
        fold_svg += (f'<path d="{"".join(folds[sd])}" fill="none" stroke="{col}" '
                     f'stroke-width="{fw}" stroke-linecap="round"/>')
    mid = [lf.axis(i / 8 * 0.97) for i in range(9)]
    out = [f'<g transform="{T(x, y, rot, 1.0, sx)}">',
           f'<clipPath id="{cid}"><path d="{d}"/></clipPath>',
           f'<path d="{d}" fill="{fill}"/>',
           f'<g clip-path="url(#{cid})">',
           f'<path d="{lf.half_region("r")}" fill="{shade}"/>',
           fold_svg,
           f'<path d="{ribbon(mid, 5.2, 1.0)}" fill="{mix(fill, P["pale"], 0.78)}"/>',
           "</g></g>"]
    return "".join(out), lf


def petiole(pts, w0, w1, color):
    return f'<path d="{ribbon(pts, w0, w1)}" fill="{color}"/>'


def bez(p0, p1, p2, p3, n=10):
    out = []
    for i in range(n + 1):
        u = i / n
        out.append(tuple((1 - u) ** 3 * p0[j] + 3 * (1 - u) ** 2 * u * p1[j] + 3 * (1 - u) * u * u * p2[j]
                         + u ** 3 * p3[j] for j in (0, 1)))
    return out


def arc_pts(base, joint, rot, a0=None, k0=0.38, k1=0.30):
    """Smooth rigid petiole: leaves the soil at angle a0, arrives along the blade axis."""
    a = math.radians(rot)
    a0 = math.radians(rot * 0.3 if a0 is None else a0)
    ln = math.dist(base, joint)
    p1 = (base[0] + math.sin(a0) * ln * k0, base[1] - math.cos(a0) * ln * k0)
    p2 = (joint[0] - math.sin(a) * ln * k1, joint[1] + math.cos(a) * ln * k1)
    tuck = (joint[0] + math.sin(a) * 14, joint[1] - math.cos(a) * 14)
    return bez(base, p1, p2, joint, 8) + [tuck]


def leaf_unit(base, joint, rot, L, fill, pet_col, bend=0.0, tears=(), pw=(9, 6), sx=1.0,
              flip=False, a0=None):
    """Petiole from `base` (in soil) to `joint`, then blade. The petiole runs a few px
    past the joint along the blade axis so it is tucked under the blade base."""
    pet = petiole(arc_pts(base, joint, rot, a0), pw[0], pw[1], pet_col)
    b, _ = blade(joint[0], joint[1], rot, L, fill, bend=bend, tears=tears, sx=sx, flip=flip)
    return pet + b


# ------------------------------------------------------------------ flower
SEPAL_SH = P["terra_dark"]
TONGUE, TONGUE_SH = P["sky"], "#56707E"


def sepal(bx, by, ang, Ls, hw, col, lean=0.0):
    """Lanceolate, slightly keeled sepal; base at (bx, by), pointing `ang` deg from up."""
    pts = [(0, 8), (hw * 0.8, -Ls * 0.16), (hw, -Ls * 0.42), (hw * 0.62 + lean * 0.5, -Ls * 0.76),
           (lean, -Ls), (-hw * 0.5 + lean * 0.5, -Ls * 0.78), (-hw * 0.88, -Ls * 0.45), (-hw * 0.72, -Ls * 0.16)]
    d = cr_path(pts, closed=True, sharp={0, 4})
    cl = uid("sc")
    keel = cr_path([(0, 6), (lean * 0.3, -Ls * 0.5), (lean, -Ls * 0.99)], closed=False)
    return (f'<g transform="{T(bx, by, ang)}"><clipPath id="{cl}"><path d="{d}"/></clipPath>'
            f'<path d="{d}" fill="{col}"/><g clip-path="url(#{cl})">'
            f'<path d="{keel}L{f(hw * 2)} {f(-Ls)}L{f(hw * 2)} 10Z" fill="{mix(col, SEPAL_SH, 0.2)}"/>'
            # keel line: opaque, 2.0 local = 3.0 units at the flower's 1.5 scale (print minimum)
            f'<path d="{keel}" fill="none" stroke="{mix(col, SEPAL_SH, 0.32)}" stroke-width="2"/>'
            f"</g></g>")


def flower(x, y, rot, s=1.0):
    """Crane-head flower in local coords: the peduncle meets the spathe heel at
    (0,0); the beak points to +x. Returns svg group."""
    # long boat-shaped spathe: rounded heel, gently rising keel, slender beak
    spathe = [(-6, 6), (14, 11), (50, 11), (92, 4), (138, -12),
              (96, -11), (58, -16), (20, -21), (-4, -19), (-14, -8)]
    sp = cr_path(spathe, closed=True, sharp={4})
    sid = uid("sp")
    # burgundy flush along the keel + a pale lip on the upper edge
    keel = cr_path([(-30, 0), (-8, 3), (24, 4), (66, 1), (108, -5), (150, -14), (150, 30), (-30, 30)],
                   closed=True, sharp={0, 5, 6, 7})
    lip = cr_path([(-30, -13), (-4, -19), (20, -21), (58, -16), (96, -11), (140, -13)], closed=False)
    parts = []
    # sepals: back to front, fanning up and forward out of the spathe mouth
    parts.append(sepal(14, -17, -30, 68, 10, P["terra_dark"], lean=-3))
    parts.append(sepal(22, -18, -9, 92, 12.5, P["terra"], lean=-2))
    parts.append(sepal(32, -18, 13, 90, 12, P["terra2"], lean=2))
    parts.append(sepal(42, -17, 34, 76, 11, P["amber"], lean=3))
    # blue petal tongue in front of the sepals, arrow-headed, pointing forward
    # softly spear-shaped (no barbs): swells gently toward the upper third and
    # narrows to a blunt point, curving a little forward like the real petal
    arrow = [(0, 6), (3.2, -14), (4.6, -34), (5.4, -50), (3.6, -62), (0.8, -70), (-2.6, -62),
             (-4.4, -48), (-3.8, -30), (-2.8, -12)]
    ad = cr_path(arrow, closed=True, sharp={0, 5})
    half = "M0 6L0 -70L10 -70L10 6Z"
    aid = uid("ac")
    parts.append(f'<g transform="{T(50, -16, 50)}"><clipPath id="{aid}"><path d="{ad}"/></clipPath>'
                 f'<path d="{ad}" fill="{TONGUE}"/><path clip-path="url(#{aid})" d="{half}" fill="{TONGUE_SH}"/></g>')
    out = [f'<g transform="{T(x, y, rot, s)}">']
    out += parts
    out += [f'<clipPath id="{sid}"><path d="{sp}"/></clipPath>',
            f'<path d="{sp}" fill="{P["sage"]}"/>',
            f'<g clip-path="url(#{sid})"><path d="{keel}" fill="{mix(P["sage"], P["plum"], 0.85)}"/>'
            f'<path d="{lip}" fill="none" stroke="{mix(P["sage"], P["pale"], 0.7)}" stroke-width="3"/></g>',
            "</g>"]
    return "".join(out)


# ------------------------------------------------------------------ build
def build():
    reset_ids()
    back, front = pot("classic", cx=CX, rim_y=RIM_Y, rx=100, base_w=70, band=True)
    Y0 = RIM_Y + 18  # petioles start below the rim front edge (ends never show)
    G = []

    # clasping leaf bases at soil level: each one is its own petiole swelling
    # toward the soil (same colour, same centre line), so it tapers seamlessly
    # into the petiole instead of standing up as a separate pale "tooth"
    def sheath(base, joint, rot, a0, col, w_soil, w_top, y_top):
        pts = [p for p in arc_pts(base, joint, rot, a0)[:-1]]
        dense = cr_sample(pts, 12)
        run = [q for q in dense if q[1] >= y_top]
        run = [(run[0][0] - (run[1][0] - run[0][0]) * 2.5, base[1] + 14)] + run
        return f'<path d="{ribbon(run[::8] + [run[-1]], w_soil, w_top, per=3)}" fill="{col}"/>'
    # --- back layer (dark): the tall leaf fills the upper left; the upper right
    # is kept open for the flower
    G.append(leaf_unit((292, Y0), (262, 322), -12, 254, P["deep"], P["forest"], bend=-0.04,
                       tears=(("r", 0.46, 0.62, 5), ("r", 0.63, 0.5, 4)), pw=(10, 7), a0=-2))
    G.append(leaf_unit((310, Y0), (392, 452), 50, 196, P["forest"], P["mid"], bend=-0.05, pw=(10, 7),
                       flip=True, a0=8, tears=(("l", 0.55, 0.55, 5),)))
    # swollen bases of the two back leaves (same depth as their petioles)
    G.append(sheath((292, Y0), (262, 322), -12, -2, P["forest"], 30, 7, 540))
    G.append(sheath((310, Y0), (392, 452), 50, 8, P["mid"], 26, 7, 552))
    # --- mid layer
    G.append(leaf_unit((284, Y0), (200, 432), -52, 200, P["deep"], P["mid"], bend=-0.07, pw=(9, 6),
                       a0=-10))
    G.append(leaf_unit((316, Y0), (398, 502), 74, 160, P["mid"], P["sage"], bend=0.07, pw=(9, 6),
                       flip=True, a0=14))
    # --- flower stalk: rises almost straight between the leaves, clear of them
    # at the top, and meets the spathe heel from below
    HX, HY = 356, 262
    stalk = arc_pts((312, Y0), (HX, HY + 6), 6, a0=3, k0=0.4, k1=0.35)[:-1]
    G.append(petiole(stalk, 10, 7.5, P["light"]))
    # the peduncle swells slightly where it turns into the spathe heel
    tail = stalk[-4:]
    G.append(petiole(tail + [(HX - 3, HY - 2)], 7.5, 17, P["light"]))
    # --- front layer (light / warm)
    G.append(leaf_unit((294, Y0), (236, 400), -30, 214, P["mid"], P["sage"], bend=-0.03, pw=(10, 7),
                       a0=-6))
    G.append(leaf_unit((302, Y0), (290, 420), -10, 188, P["sage"], P["light"], bend=0.05, pw=(10, 7),
                       flip=True, a0=-1))
    # --- young front leaf, low, covers the petiole bundle
    G.append(leaf_unit((308, Y0), (338, 516), 44, 150, P["light"], P["sage"], bend=0.05, pw=(8, 6),
                       a0=10, flip=True))
    plant = "".join(G)
    head = flower(HX, HY, -10, 1.5)

    body = back + plant + head + front
    return body


def main():
    svg = svg_doc(build(), "Strelitzia reginae (bird of paradise)")
    out = os.path.join(os.path.dirname(HERE), "out", "strelitzia_reginae.svg")
    with open(out, "w") as fh:
        fh.write(svg)
    print(out, len(svg))


if __name__ == "__main__":
    main()
