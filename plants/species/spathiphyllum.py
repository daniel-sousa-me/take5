"""Spathiphyllum (peace lily) - v4 botanical card art.

Run:  python3 species/spathiphyllum.py   -> out/spathiphyllum.svg
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, SHADE, Leaf, leaf_g, ribbon, line, cr_path, pot, svg_doc, T, f, uid, reset_ids  # noqa: E402

P = PAL
SOIL_Y = 612          # petioles start here, below the rim front (hidden by the pot)
SPADIX = "#E4D493"    # cream-yellow (between PAL cream and yellow_edge)
SPADIX_SH = "#CDBB6C"
# The spathe must read WHITE on ivory card, but anything at/above the stock's lightness prints
# as bare paper. So the lit half is a cool, very pale green-white just under the stock's L*
# (it takes a trace of ink and looks cleaner/cooler than the warm paper), the cupped half a
# cool pale grey-green; no outline -- the dark leaves placed behind carry the silhouette.
SPATHE_LT = "#E8ECE0"    # L* 92.8 < stock 93.2: printable
SPATHE_SH = "#D3D9CB"    # cupped half
SPATHE_VEIN = "#C3C8B0"  # pale green midvein, pre-blended solid


def rot_pt(x, y, deg):
    a = math.radians(deg)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


def world(bx, by, deg, p, sx=1.0):
    q = rot_pt(p[0] * sx, p[1], deg)
    return (bx + q[0], by + q[1])


# ------------------------------------------------------------------ leaves
def lily_leaf(L, bend, wide=1.0, lean=0.0):
    """Glossy elliptic-lanceolate blade, cuneate base, acuminate tip."""
    r = [(0.0, 0.0), (0.06, 0.07), (0.2, 0.155), (0.4, 0.2), (0.6, 0.18),
         (0.78, 0.11), (0.9, 0.05), (0.96, 0.018)]
    right = [(t, w * wide * (1 + lean)) for t, w in r]
    left = [(t, w * wide * (1 - lean)) for t, w in r]
    right[0] = left[0] = (0.0, 0.0)
    return Leaf(L, right, left, bend=bend)


def half(lf, side, reach=3.0):
    """Light-weight version of Leaf.half_region (fewer nodes, same look)."""
    sg = 1 if side == "r" else -1
    ts = [-0.3, 0.0, 0.25, 0.5, 0.75, 1.0, 1.25]
    mid = [lf.axis(t) for t in ts]
    far = [lf.pt(t, sg * reach) for t in ts]
    pts = mid + far[::-1]
    return cr_path(pts, closed=True, sharp={0, len(mid) - 1, len(mid), len(pts) - 1})


def mix(a, b, k):
    """pre-blend hex a toward b by k (flat opaque colour)."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * k):02X}" for x, y in zip(ca, cb))


SHADE_X = dict(SHADE, **{P["night"]: "#1F3024"})
VEIN_T = (0.2, 0.4, 0.6)      # three laterals per side on every leaf
VEIN_W = 3.4                  # widest point (at the midrib), dark-on-light min is 3.0
MIDRIB_W = (4.6, 1.4)         # light (knockout) midrib: >= 4 at the base


def taper(p0, p1, p2, w0, w1):
    """Quadratic centre line drawn as a filled taper, w0 at p0 -> w1 at p2."""
    def nrm(a, b, h):
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        return -dy / m * h, dx / m * h
    n0, n2 = nrm(p0, p1, w0 / 2), nrm(p1, p2, w1 / 2)
    nm = nrm(p0, p2, (w0 + w1) / 2)
    return (f"M{f(p0[0] + n0[0])} {f(p0[1] + n0[1])}Q{f(p1[0] + nm[0])} {f(p1[1] + nm[1])} "
            f"{f(p2[0] + n2[0])} {f(p2[1] + n2[1])}L{f(p2[0] - n2[0])} {f(p2[1] - n2[1])}"
            f"Q{f(p1[0] - nm[0])} {f(p1[1] - nm[1])} {f(p0[0] - n0[0])} {f(p0[1] - n0[1])}Z")


def veins(lf, fill, side):
    """Opaque vein system, identical on every leaf: three curved laterals per side,
    one tone step darker than the half they sit on, plus a light midrib."""
    sh = SHADE_X.get(fill, "#1F3024")
    tone = {side: mix(sh, "#000000", 0.16), ("l" if side == "r" else "r"): sh}
    out = []
    for s, sg in (("r", 1), ("l", -1)):
        d = []
        for t in VEIN_T:
            dt = 0.17
            t2 = min(t + dt, 0.98)
            p0 = lf.axis(t)
            p1 = lf.pt(t + dt * 0.45, sg * lf.width(t + dt * 0.45, s) * 0.5)
            p2 = lf.pt(t2, sg * lf.width(t2, s) * 0.86)
            d.append(taper(p0, p1, p2, VEIN_W, 1.0))
        out.append(f'<path d="{"".join(d)}" fill="{tone[s]}"/>')
    rib = mix(fill, P["pale"], 0.45)
    a, b, c = lf.axis(0.0), lf.axis(0.45), lf.axis(0.9)
    out.append(f'<path d="{taper(a, b, c, *MIDRIB_W)}" fill="{rib}"/>')
    return "".join(out)


def leaf_svg(lf, bx, by, deg, fill, side, sx=1.0):
    sh = SHADE_X.get(fill, "#1F3024")
    return leaf_g(
        lf, fill, extra=lambda l: f'<path d="{half(l, side)}" fill="{sh}"/>' + veins(l, fill, side),
        transform=T(bx, by, deg, 1, sx))


class Plant:
    def __init__(self):
        self.parts = []

    def leaf(self, x0, bx, by, deg, L, fill, bend=0.0, side="r", ctrl=None, sx=1.0,
             pet=None, wide=1.0, lean=0.0, pw=(8.5, 5.0), pre_k=0.16):
        lf = lily_leaf(L, bend, wide, lean)
        # petiole: soil -> ctrl -> just below blade base, tangent to blade, ending inside blade
        d = rot_pt(0, -1, deg)
        pre = (bx - d[0] * L * pre_k, by - d[1] * L * pre_k)
        inside = world(bx, by, deg, lf.axis(0.07), sx)
        if ctrl is None:  # rise from the soil, then sweep out into the blade
            ctrl = (x0 + (pre[0] - x0) * 0.4, pre[1] + (SOIL_Y - pre[1]) * 0.5)
        pts = [(x0, SOIL_Y), ctrl, pre, inside]
        pcol = pet or P["mid"]
        s = f'<path d="{ribbon(pts, pw[0], pw[1], per=4)}" fill="{pcol}"/>'
        return s, leaf_svg(lf, bx, by, deg, fill, side, sx)


# ------------------------------------------------------------------ flower
def spathe_svg(bx, by, deg, H, bend=0.06, flip=False, open_=1.0):
    """White spathe (hood) with cream-yellow spadix. base at (bx,by)."""
    wr = 0.245 * open_
    right = [(0.0, 0.03), (0.1, 0.12), (0.32, wr), (0.52, wr * 1.02),
             (0.72, wr * 0.8), (0.88, wr * 0.4)]
    left = [(0.0, 0.03), (0.1, 0.11), (0.32, wr * 0.9), (0.52, wr * 0.95),
            (0.72, wr * 0.74), (0.88, wr * 0.38)]
    sp = Leaf(H, right, left, bend=bend, base_sharp=False)
    sx = -1 if flip else 1
    d = sp.path()
    cid = uid("sp")
    g = [f'<g transform="{T(bx, by, deg, 1, sx)}">',
         f'<clipPath id="{cid}"><path d="{d}"/></clipPath>',
         f'<path d="{d}" fill="{SPATHE_LT}"/>',
         f'<g clip-path="url(#{cid})">']
    # cupped half: warm off-white shade on one side of the midvein
    g.append(f'<path d="{half(sp, "r")}" fill="{SPATHE_SH}"/>')
    # green throat: a slim wedge from the spathe base narrowing up the midvein into the
    # midvein itself (straight-ish concave sides, no rounded blob behind the spadix)
    b0, bl, br, tp = sp.axis(-0.05), sp.pt(0.0, -0.085), sp.pt(0.0, 0.085), sp.axis(0.4)
    ql, qr = sp.pt(0.14, -0.03), sp.pt(0.14, 0.03)
    throat = (f"M{f(bl[0])} {f(bl[1])}Q{f(ql[0])} {f(ql[1])} {f(tp[0])} {f(tp[1])}"
              f"Q{f(qr[0])} {f(qr[1])} {f(br[0])} {f(br[1])}L{f(b0[0])} {f(b0[1])}Z")
    g.append(f'<path d="{throat}" fill="{SPATHE_VEIN}"/>')
    # pale green midvein up the spathe
    g.append(f'<path d="{taper(sp.axis(0.02), sp.axis(0.42), sp.axis(0.82), 3.4, 1.0)}" fill="{SPATHE_VEIN}"/>')
    g.append("</g>")
    # spadix: upright capsule rising from the throat, slightly off-axis
    sl, sw = H * 0.36, H * 0.062
    sb = sp.axis(0.1)
    sd = cr_path([(sb[0] - sw * 0.6, sb[1]), (sb[0] - sw, sb[1] - sl * 0.45),
                  (sb[0] - sw * 0.55, sb[1] - sl * 0.92), (sb[0] + sw * 0.1, sb[1] - sl),
                  (sb[0] + sw * 0.75, sb[1] - sl * 0.9), (sb[0] + sw, sb[1] - sl * 0.45),
                  (sb[0] + sw * 0.6, sb[1])], closed=True, sharp={0, 6})
    sdc = uid("sd")
    g.append(f'<clipPath id="{sdc}"><path d="{sd}"/></clipPath><path d="{sd}" fill="{SPADIX}"/>')
    g.append(f'<g clip-path="url(#{sdc})"><rect x="{f(sb[0] + sw * 0.15)}" y="{f(sb[1] - sl - 5)}" '
             f'width="{f(sw * 2)}" height="{f(sl + 10)}" fill="{SPADIX_SH}"/></g>')
    g.append("</g>")
    return "".join(g)


def flower(x0, pts, H, deg, bend=0.06, flip=False, open_=1.0, w=(5.2, 3.4), col=None):
    """Stalk from soil through pts, spathe base at pts[-1]; stalk ends under the base."""
    bx, by = pts[-1]
    d = rot_pt(0, -1, deg)
    inside = (bx + d[0] * H * 0.06, by + d[1] * H * 0.06)
    stalk = f'<path d="{ribbon([(x0, SOIL_Y)] + pts + [inside], w[0], w[1], per=4)}" fill="{col or P["light"]}"/>'
    return stalk, spathe_svg(bx, by, deg, H, bend, flip, open_)


# ------------------------------------------------------------------ build
def build():
    back, front = pot("classic", rx=102, rim_y=588, base_w=72, band=True)
    pl = Plant()
    D, F, M, S = P["deep"], P["forest"], P["mid"], P["sage"]
    layers = {k: [] for k in ("back", "flow", "mid", "front", "drape")}

    def add(layer, pair):
        layers[layer].append(pair)

    def fan(layer, a, r, L, fill, bend=0.05, lean=1.25, wide=1.0, pet=None, x0=None):
        """Leaf placed on a fan around the crown: petiole direction a (deg),
        blade leaning out a bit more than its petiole (arching habit)."""
        ra = math.radians(a)
        bx, by = 300 + math.sin(ra) * r * 0.8, 604 - math.cos(ra) * r
        side = "l" if a < 0 else "r"
        sg = -1 if a < 0 else 1
        x0 = 300 + a * 0.22 if x0 is None else x0
        add(layer, pl.leaf(x0, bx, by, a * lean, L, fill, bend=sg * bend, side=side,
                           wide=wide, pet=pet))

    N = P["night"]
    # --- back: tall dark leaves, the backdrop for the spathes
    fan("back", -34, 222, 180, D, 0.07, lean=1.62, pet=F)
    fan("back", 44, 196, 160, D, 0.06, lean=1.45, pet=F)
    add("back", pl.leaf(292, 252, 362, -29, 196, N, bend=-0.03, side="l", pet=F))
    add("back", pl.leaf(310, 386, 366, 38, 196, N, bend=0.04, side="r", pet=F))
    add("back", pl.leaf(300, 308, 334, 3, 228, D, bend=-0.03, side="r", pet=F, wide=0.92))
    # --- flowers (stalks behind the foliage, spathes on top of it)
    add("flow", flower(296, [(290, 470), (268, 384), (240, 330), (227, 300)], 98, -25, bend=0.06, flip=True))
    add("flow", flower(308, [(318, 470), (314, 350), (312, 262)], 114, -1, bend=-0.05))
    add("flow", flower(310, [(352, 500), (416, 414), (430, 336)], 90, 20, bend=0.07, open_=0.85))
    # --- mid: forest leaves filling the clump
    fan("mid", -25, 192, 164, M, 0.05, lean=1.3, pet=M)
    fan("mid", 15, 184, 156, F, 0.05, lean=1.55, pet=M)
    # --- front: lighter, lower, arching out
    fan("front", -54, 128, 182, M, 0.14, lean=1.32, pet=S)
    fan("front", -4, 150, 132, S, 0.04, lean=2.2, pet=S)
    fan("front", 34, 138, 142, M, 0.07, lean=1.4, pet=S)
    fan("front", 60, 118, 150, S, 0.15, lean=1.38, pet=S)
    # --- drape: short leaves flopping over the rim, hiding the crown
    fan("front", 8, 76, 96, P["light"], 0.05, lean=2.7, pet=S)
    # deliberately unequal: a long leaf flopping low over the left rim, a short one
    # pushing out almost level on the right (no mirrored "bow tie")
    add("drape", pl.leaf(276, 262, 592, -128, 132, S, bend=0.12, side="r", pet=S, pw=(7, 5),
                         ctrl=(272, 604), pre_k=0.02))
    add("drape", pl.leaf(328, 350, 584, 106, 98, M, bend=-0.06, side="l", pet=S, pw=(6.5, 4.5),
                         ctrl=(334, 596), pre_k=0.02))

    g = []
    for layer in ("back", "flow", "mid", "front"):
        for st, lv in layers[layer]:
            g += [st] if layer == "flow" else [st, lv]
    # spathes sit on top of the foliage so the whites are never cut
    g += [lv for st, lv in layers["flow"]]
    # drape stems stay behind the rim; their blades lie over it
    g += [st for st, lv in layers["drape"]]
    return back + "".join(g) + front + "".join(lv for st, lv in layers["drape"])


if __name__ == "__main__":
    reset_ids()
    out = os.path.join(os.path.dirname(HERE), "out", "spathiphyllum.svg")
    open(out, "w").write(svg_doc(build(), "Spathiphyllum"))
    print("wrote", out, os.path.getsize(out))
