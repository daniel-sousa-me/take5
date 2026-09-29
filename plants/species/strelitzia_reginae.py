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
    vc = vein_col or P["pale"]
    vv = []
    t = 0.06
    while t < 0.84:
        for side, sg in (("r", 1), ("l", -1)):
            p0, p1, p2 = vein_ctrl(lf, t, sg, side)
            vv.append(f"M{f(p0[0])} {f(p0[1])}Q{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])}")
        t += 0.031
    # a few stronger "fold" lines, irregularly spaced, like the real leaf's pleats
    folds = []
    for side, sg, ts in (("r", 1, (0.21, 0.43, 0.58)), ("l", -1, (0.30, 0.52, 0.71))):
        for t0 in ts:
            p0, p1, p2 = vein_ctrl(lf, t0, sg, side)
            folds.append(f"M{f(p0[0])} {f(p0[1])}Q{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])}")
    mid = [lf.axis(i / 8 * 0.97) for i in range(9)]
    out = [f'<g transform="{T(x, y, rot, 1.0, sx)}">',
           f'<clipPath id="{cid}"><path d="{d}"/></clipPath>',
           f'<path d="{d}" fill="{fill}"/>',
           f'<g clip-path="url(#{cid})">',
           f'<path d="{lf.half_region("r")}" fill="{shade}"/>',
           f'<path d="{"".join(vv)}" fill="none" stroke="{vc}" stroke-width="0.8" opacity=".15"/>',
           f'<path d="{"".join(folds)}" fill="none" stroke="{P["night"]}" stroke-width="1.1" opacity=".16"/>',
           f'<path d="{ribbon(mid, 5.2, 1.0)}" fill="{P["pale"]}" opacity=".78"/>',
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
def flower(x, y, rot, s=1.0):
    """Flower head in local coords: peduncle meets the spathe at (0,0); the beak
    points to +x. Returns svg group."""
    spathe = [(-4, 3), (12, 8), (45, 9), (82, 3), (126, -12),
              (84, -12), (48, -17), (14, -20), (-6, -16), (-12, -6)]
    sp = cr_path(spathe, closed=True, sharp={4})
    sid = uid("sp")
    # burgundy flush along the keel + a pale lip on the upper edge
    keel = cr_path([(-30, -1), (-8, 1), (20, 1), (60, 0), (100, -5), (140, -12), (140, 30), (-30, 30)],
                   closed=True, sharp={0, 5, 6, 7})
    lip = cr_path([(-30, -12), (-6, -17), (16, -20), (50, -16), (86, -11), (130, -13)], closed=False)
    # sepals: (base, angle, length, half-width, colour) -- back to front
    sep = [((18, -16), -18, 76, 12, P["terra"]),
           ((26, -17), 6, 88, 13, P["terra2"]),
           ((38, -16), 36, 74, 11.5, P["amber"])]
    parts = []
    for (bx, by), ang, Ls, hw, col in sep:
        pts = [(0, 6), (hw * 0.75, -Ls * 0.18), (hw, -Ls * 0.45), (hw * 0.6, -Ls * 0.78), (0, -Ls),
               (-hw * 0.55, -Ls * 0.78), (-hw * 0.9, -Ls * 0.45), (-hw * 0.7, -Ls * 0.18)]
        d = cr_path(pts, closed=True, sharp={0, 4})
        cl = uid("sc")
        parts.append(f'<g transform="{T(bx, by, ang)}"><clipPath id="{cl}"><path d="{d}"/></clipPath>'
                     f'<path d="{d}" fill="{col}"/>'
                     f'<path clip-path="url(#{cl})" d="M0 4L0 {f(-Ls * 0.95)}" stroke="{P["terra_dark"]}" '
                     f'stroke-width="1.2" opacity=".35" fill="none"/>'
                     f'<path clip-path="url(#{cl})" d="M{f(hw * 0.2)} 0L{f(hw * 1.5)} 0L{f(hw * 1.5)} {f(-Ls)}L{f(hw * 0.2)} {f(-Ls)}Z" '
                     f'fill="{P["terra_dark"]}" opacity=".18"/></g>')
    # blue arrow petal, emerging between the front sepals, pointing up-forward
    arrow = [(0, 4), (4, -22), (4.5, -44), (7, -47), (1.5, -66), (0, -70), (-1.5, -66), (-4.5, -50),
             (-3.5, -44), (-3.5, -22)]
    ad = cr_path(arrow, closed=True, sharp={0, 3, 5, 8})
    arrow_g = (f'<g transform="{T(34, -17, 17)}"><path d="{ad}" fill="{P["sky"]}"/>'
               f'<path d="M0.3 -4L0.3 -64" stroke="{P["ivory"]}" stroke-width="1.2" opacity=".35"/></g>')
    out = [f'<g transform="{T(x, y, rot, s)}">']
    out += parts
    out.append(arrow_g)
    out += [f'<clipPath id="{sid}"><path d="{sp}"/></clipPath>',
            f'<path d="{sp}" fill="{P["sage"]}"/>',
            f'<g clip-path="url(#{sid})"><path d="{keel}" fill="{P["plum"]}" opacity=".85"/>'
            f'<path d="{lip}" fill="none" stroke="{P["pale"]}" stroke-width="3" opacity=".7"/></g>',
            "</g>"]
    return "".join(out)


# ------------------------------------------------------------------ build
def build():
    reset_ids()
    back, front = pot("classic", cx=CX, rim_y=RIM_Y, rx=100, base_w=70, band=True)
    Y0 = RIM_Y + 8  # petioles start inside the soil opening
    G = []
    # --- back layer (dark)
    G.append(leaf_unit((292, Y0), (270, 318), -9, 252, P["deep"], P["forest"], bend=-0.04,
                       tears=(("r", 0.46, 0.62, 5), ("r", 0.63, 0.5, 4)), pw=(10, 7), a0=-2))
    G.append(leaf_unit((310, Y0), (356, 332), 24, 238, P["forest"], P["mid"], bend=0.05, pw=(10, 7),
                       flip=True, a0=6))
    # --- mid layer
    G.append(leaf_unit((284, Y0), (196, 424), -49, 196, P["deep"], P["mid"], bend=-0.07, pw=(9, 6),
                       a0=-10))
    G.append(leaf_unit((316, Y0), (410, 446), 58, 170, P["mid"], P["sage"], bend=0.08, pw=(9, 6),
                       tears=(("l", 0.50, 0.62, 6),), flip=True, a0=12))
    # --- front layer (light / warm)
    G.append(leaf_unit((294, Y0), (232, 396), -26, 214, P["mid"], P["sage"], bend=-0.03, pw=(10, 7),
                       a0=-6))
    G.append(leaf_unit((304, Y0), (318, 408), 9, 196, P["sage"], P["light"], bend=0.04, pw=(10, 7),
                       flip=True, a0=2))
    stalk = petiole(arc_pts((318, Y0), (392, 354), 55, a0=6, k0=0.55, k1=0.22)[:-1], 8, 6.5, P["light"])
    G.append(stalk)
    # --- young front leaf, low, covers the petiole bundle
    G.append(leaf_unit((308, Y0), (332, 512), 47, 150, P["light"], P["sage"], bend=0.05, pw=(8, 6),
                       a0=10, flip=True))
    plant = "".join(G)
    # flower stalk + head (peduncle leaves the soil, arcs out, meets the spathe's heel)
    head = flower(392, 352, -10, 1.28)
    # clasping leaf-base sheaths at soil level (lanceolate, pointed)
    def sheath(x0, x1, tipx, tipy, col):
        d = cr_path([(x0, 604), (x0 + (tipx - x0) * 0.6 - 2, 560), (tipx, tipy), (x1 - (x1 - tipx) * 0.45 + 1, 562), (x1, 604)],
                    closed=True, sharp={0, 2, 4})
        return f'<path d="{d}" fill="{col}"/>'
    sheaths = (sheath(278, 302, 285, 544, P["light"]) + sheath(298, 328, 317, 552, P["pale"]))
    body = back + plant + head + sheaths + front
    return body


def main():
    svg = svg_doc(build(), "Strelitzia reginae (bird of paradise)")
    out = os.path.join(os.path.dirname(HERE), "out", "strelitzia_reginae.svg")
    with open(out, "w") as fh:
        fh.write(svg)
    print(out, len(svg))


if __name__ == "__main__":
    main()
