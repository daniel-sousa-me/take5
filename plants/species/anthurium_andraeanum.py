"""Anthurium andraeanum (flamingo flower) -- v4 botanical card art.

Run:  python3 species/anthurium_andraeanum.py   -> out/anthurium_andraeanum.svg
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from core import PAL, SHADE, Leaf, leaf_g, stem, line, cr_path, pot, svg_doc, T, f, uid, reset_ids  # noqa

P = PAL
RED = P["red"]            # spathe
RED_DK = "#9C4640"        # deeper red for the turned-away half / veins
RED_HI = "#E3AFA6"        # pale glossy highlight (blush, lifted)
SPADIX = "#EFE3BC"        # ivory-cream spadix
SPADIX_SH = P["mustard"]


def world(x, y, rot, sx, s, lx, ly):
    """Local leaf coords -> world, matching T(x, y, rot, s, sx)."""
    lx, ly = lx * sx, ly * s
    a = math.radians(rot)
    return (x + lx * math.cos(a) - ly * math.sin(a), y + lx * math.sin(a) + ly * math.cos(a))


# ------------------------------------------------------------------ shapes
def anth_leaf(L, bend=0.0, lobe=1.0):
    """Cordate leaf with drip tip. Open sinus at t=0.14, rounded lobes reach t=-0.07."""
    r = [(0.14, 0), (0.07, 0.10 * lobe), (-0.02, 0.17), (-0.07, 0.25), (-0.03, 0.335), (0.11, 0.385),
         (0.32, 0.36), (0.55, 0.27), (0.76, 0.145), (0.92, 0.045)]
    l = [(0.14, 0), (0.08, 0.105 * lobe), (-0.01, 0.18), (-0.06, 0.26), (-0.01, 0.34), (0.13, 0.38),
         (0.34, 0.35), (0.57, 0.26), (0.77, 0.135), (0.92, 0.04)]
    return Leaf(L, r, l, bend=bend, cordate=True, tip_t=1.0)


def spathe(L, bend=0.0):
    """Broad heart-shaped spathe, sinus at t=0.10."""
    r = [(0.10, 0), (0.0, 0.13), (0.01, 0.30), (0.12, 0.42), (0.30, 0.46), (0.50, 0.40),
         (0.70, 0.27), (0.87, 0.12), (0.96, 0.035)]
    l = [(0.10, 0), (0.005, 0.14), (0.02, 0.31), (0.14, 0.43), (0.32, 0.455), (0.52, 0.39),
         (0.71, 0.26), (0.87, 0.11), (0.96, 0.03)]
    return Leaf(L, r, l, bend=bend, cordate=True, tip_t=1.0)


# ------------------------------------------------------------------ leaves
def draw_leaf(spec):
    x, y, rot, L, col = spec["x"], spec["y"], spec["rot"], spec["L"], spec["col"]
    sx = spec.get("sx", 1.0)
    lf = anth_leaf(L, spec.get("bend", 0.0))
    shade = SHADE[col]
    vein_col = P["pale"] if col in (P["night"], P["deep"], P["forest"]) else P["pale"]

    def extra(leaf):
        # arching lateral veins that run up toward the tip + a submarginal collector
        out = []
        for t in (0.24, 0.42, 0.60):
            for sg, side in ((1, "r"), (-1, "l")):
                p0 = leaf.axis(t)
                w1 = leaf.width(t + 0.08, side) * 0.55
                w2 = leaf.width(t + 0.32, side) * 0.80
                p1 = leaf.pt(t + 0.08, sg * w1)
                p2 = leaf.pt(min(t + 0.32, 0.95), sg * w2)
                out.append(f"M{f(p0[0])} {f(p0[1])}Q{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])}")
        # basal veins curving into the lobes
        for sg, side in ((1, "r"), (-1, "l")):
            p0 = leaf.axis(0.15)
            p1 = leaf.pt(0.04, sg * 0.20)
            p2 = leaf.pt(0.02, sg * 0.31)
            out.append(f"M{f(p0[0])} {f(p0[1])}Q{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])}")
        return (f'<path d="{"".join(out)}" fill="none" stroke="{vein_col}" stroke-width="{f(1.5 / sx)}" '
                f'stroke-linecap="round" opacity=".17"/>')

    return leaf_g(lf, col, shade=shade, side=spec.get("side", "r"),
                  midrib=(vein_col, 2.4, 0.42, 0.14, 0.96), extra=extra,
                  transform=T(x, y, rot, 1.0, sx)), lf


def petiole(spec, lf, base, via, w0=7.5, w1=5.0, col=None):
    x, y, rot = spec["x"], spec["y"], spec["rot"]
    sx = spec.get("sx", 1.0)
    L = lf.L
    sinus = world(x, y, rot, sx, 1, 0, -0.08 * L)
    inside = world(x, y, rot, sx, 1, 0, -0.23 * L)
    pts = [base] + via + [sinus, inside]
    return stem(pts, w0, w1, col or P["sage"])


# ------------------------------------------------------------------ flowers
def draw_flower(spec):
    x, y, rot, L = spec["x"], spec["y"], spec["rot"], spec["L"]
    sx = spec.get("sx", 1.0)
    sp = spathe(L, spec.get("bend", 0.0))
    d = sp.path()
    side = spec.get("side", "r")

    def extra(leaf):
        out = []
        # puckered veins: fan from the sinus, curving out and up toward the margin
        vv = []
        for sg, s in ((1, "r"), (-1, "l")):
            for k, t in enumerate((0.16, 0.26, 0.38, 0.52, 0.67, 0.80)):
                p0 = leaf.axis(0.11 + 0.012 * k)
                wt = leaf.width(t, s)
                p1 = leaf.pt(t - 0.06, sg * wt * 0.45)
                p2 = leaf.pt(t + 0.06, sg * wt * 0.93)
                vv.append(f"M{f(p0[0])} {f(p0[1])}Q{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])}")
        out.append(f'<path d="{"".join(vv)}" fill="none" stroke="{RED_DK}" stroke-width="{f(1.3 / sx)}" '
                   f'stroke-linecap="round" opacity=".55"/>')
        # glossy highlight: a soft lens on the lit lobe
        hs = -1 if side == "r" else 1
        h = [leaf.pt(0.20, hs * 0.13), leaf.pt(0.30, hs * 0.25), leaf.pt(0.48, hs * 0.27),
             leaf.pt(0.62, hs * 0.19), leaf.pt(0.50, hs * 0.19), leaf.pt(0.33, hs * 0.18)]
        out.append(f'<path d="{cr_path(h, sharp={0, 3})}" fill="{RED_HI}" opacity=".85"/>')
        return "".join(out)

    body = leaf_g(sp, RED, shade=RED_DK, side=side, extra=extra, transform=T(x, y, rot, 1.0, sx))
    # spadix: rises from the sinus, leaning and curving away from the spathe face
    ang = spec.get("spadix_rot", 12)
    Ls = L * spec.get("spadix_len", 0.55)
    base = world(x, y, rot, sx, 1, 0, -0.125 * L)
    a = math.radians(rot + ang)
    ux, uy = math.sin(a), -math.cos(a)
    nx, ny = -uy, ux
    curl = spec.get("curl", 0.10)
    pts = [base]
    for u in (0.35, 0.7, 1.0):
        c = curl * Ls * u * u
        pts.append((base[0] + ux * Ls * u + nx * c, base[1] + uy * Ls * u + ny * c))
    w0 = L * 0.085
    sd = stem(pts, w0, w0 * 0.55, SPADIX)
    sid = uid("sp")
    from core import ribbon
    rd = ribbon(pts, w0, w0 * 0.55)
    # shaded flank + a few tiny floret dots
    sh = [(p[0] + nx * w0 * 0.30, p[1] + ny * w0 * 0.30) for p in pts]
    dots = []
    for i, u in enumerate([0.14 + 0.085 * k for k in range(10)]):
        for j, o in enumerate((-0.22, 0.12)):
            c = curl * Ls * u * u
            off = o + (0.08 if i % 2 else 0)
            px = base[0] + ux * Ls * u + nx * (c + off * w0)
            py = base[1] + uy * Ls * u + ny * (c + off * w0)
            dots.append(f"M{f(px)} {f(py)}h.01")
    cap = f'<circle cx="{f(base[0])}" cy="{f(base[1])}" r="{f(w0 * 0.5)}" fill="{SPADIX}"/>'
    spad = (cap + sd + f'<clipPath id="{sid}"><path d="{rd}"/></clipPath><g clip-path="url(#{sid})">'
            + line(sh, w0 * 0.55, SPADIX_SH, 0.55)
            + f'<path d="{"".join(dots)}" stroke="{P["mustard"]}" stroke-width="{f(w0 * 0.2)}" '
              f'stroke-linecap="round" opacity=".45"/>' + "</g>")
    return body + spad, sp


def fstalk(spec, sp, base, via, w0=5.5, w1=4.0):
    x, y, rot = spec["x"], spec["y"], spec["rot"]
    sx = spec.get("sx", 1.0)
    L = sp.L
    sinus = world(x, y, rot, sx, 1, 0, -0.10 * L)
    inside = world(x, y, rot, sx, 1, 0, -0.19 * L)
    return stem([base] + via + [sinus, inside], w0, w1, P["light"])


# ------------------------------------------------------------------ build
def build():
    reset_ids()
    back, front = pot(kind="classic", cx=300, rim_y=586, rx=100, rim_h=30, base_w=70, band=True)
    out = [back]

    # leaves, back -> front.  x,y = sinus anchor (local origin); rot 0 = tip up.
    leaves = [
        # back layer (deep) -- A right crown, B far left
        dict(x=334, y=336, rot=20, L=232, col=P["deep"], side="r", bend=-0.03,
             base=(308, 590), via=[(318, 470)]),
        dict(x=222, y=430, rot=-72, L=186, col=P["deep"], side="l", bend=0.05, sx=0.92,
             base=(288, 594), via=[(262, 500)]),
        # middle layer (mid) -- C upper left, D right
        dict(x=266, y=360, rot=-30, L=212, col=P["mid"], side="r", bend=0.04,
             base=(296, 592), via=[(282, 470)]),
        dict(x=388, y=440, rot=74, L=166, col=P["mid"], side="l", bend=0.05, sx=0.92,
             base=(314, 592), via=[(344, 490)]),
        # front: G young centre leaf, E/F drooping low
        dict(x=292, y=490, rot=5, L=126, col=P["sage"], side="r", bend=0.06, sx=0.9,
             base=(298, 594), via=[(295, 548)]),
        dict(x=352, y=518, rot=100, L=112, col=P["sage"], side="l", bend=0.08, sx=0.8,
             base=(312, 596), via=[(330, 556)]),
        dict(x=246, y=508, rot=-122, L=150, col=P["sage"], side="r", bend=-0.05, sx=0.86,
             base=(292, 596), via=[(270, 556)]),
    ]
    flowers = [
        # face-on, highest
        dict(x=300, y=210, rot=4, L=144, side="r", spadix_rot=22, curl=0.16,
             base=(298, 592), via=[(292, 420), (298, 290)], z=1),
        # tilted, left
        dict(x=164, y=300, rot=-44, L=124, sx=0.7, side="l", spadix_rot=28, curl=0.32,
             base=(292, 592), via=[(258, 440), (180, 330)], z=2),
        # low, right, turned
        dict(x=458, y=322, rot=40, L=112, sx=0.62, side="r", spadix_rot=-36, curl=-0.32,
             base=(306, 594), via=[(326, 490), (372, 404), (432, 352)], z=3),
    ]

    def leaf_item(s):
        g, lf = draw_leaf(s)
        pc = {P["deep"]: P["sage"], P["mid"]: P["light"], P["sage"]: P["mid"]}[s["col"]]
        return petiole(s, lf, s["base"], s["via"], 7.0 if s["L"] > 150 else 6.0,
                       4.6 if s["L"] > 150 else 3.8, pc) + g

    def flower_item(s):
        g, sp = draw_flower(s)
        return fstalk(s, sp, s["base"], s["via"]) + g

    order = [leaf_item(leaves[0]), leaf_item(leaves[1]), leaf_item(leaves[2]), leaf_item(leaves[3]),
             flower_item(flowers[0]), flower_item(flowers[1]), flower_item(flowers[2]),
             leaf_item(leaves[4]), leaf_item(leaves[5]), leaf_item(leaves[6])]
    out += order
    out.append(front)
    return "".join(out)


def main():
    body = build()
    svg = svg_doc(body, "Anthurium andraeanum (flamingo flower)")
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    p = os.path.join(ROOT, "out", "anthurium_andraeanum.svg")
    with open(p, "w") as fh:
        fh.write(svg)
    print(p, len(svg))


if __name__ == "__main__":
    main()
