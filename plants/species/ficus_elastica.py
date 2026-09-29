"""Ficus elastica (rubber plant) — v4 generator.

Two upright stems, thick glossy elliptic leaves alternating up the stems on short
thick petioles, burgundy/red rolled stipule sheaths at each growing tip.
Run:  python3 species/ficus_elastica.py   -> out/ficus_elastica.svg
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from core import PAL, Leaf, cr_path, cr_sample, ribbon, f, uid, pot, svg_doc, reset_ids  # noqa: E402

P = PAL
# leaf tone sets: (fill, turned-away half, sheen opacity)
TONES = {
    "back":  ("#27392C", "#1F3025", 0.10),   # night
    "deep":  ("#314B37", "#27392C", 0.12),
    "front": ("#405D43", "#34503A", 0.13),   # forest
    "young": ("#5B7458", "#4B6349", 0.14),   # new leaf, a touch lighter
}
STEM = "#7F9273"        # sage: reads against every leaf tone
STEM_SH = "#6A7E60"
MIDRIB = "#DDB9AE"      # pale, faintly pink (cream x blush)


def rad(a):
    return math.radians(a)


def dir_of(a):
    """unit vector for angle a (deg, clockwise from straight up)"""
    return (math.sin(rad(a)), -math.cos(rad(a)))


def rot_pt(p, a, o=(0, 0)):
    c, s = math.cos(rad(a)), math.sin(rad(a))
    return (o[0] + p[0] * c - p[1] * s, o[1] + p[0] * s + p[1] * c)


def at_y(pts, y):
    """point + tangent angle on a (mostly vertical) spline at height y"""
    s = cr_sample(pts, 16)
    for a, b in zip(s, s[1:]):
        if (a[1] - y) * (b[1] - y) <= 0:
            u = (y - a[1]) / ((b[1] - a[1]) or 1)
            p = (a[0] + (b[0] - a[0]) * u, y)
            return p, math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1])))
    return s[-1], 0


def rubber_leaf(L, bend=0.0, asym=0.0):
    r = [(0.035, 0.095), (0.13, 0.190), (0.30, 0.250), (0.50, 0.262), (0.68, 0.232),
         (0.83, 0.158), (0.925, 0.070), (0.972, 0.022)]
    l = [(t, w * (1 - asym)) for t, w in r]
    return Leaf(L, r, l, bend=bend, tip_sharp=True, base_sharp=False)


def leaf_svg(lf, tone, x, y, rot, shade_side="r"):
    fill, sh, sheen_op = TONES[tone]
    d = lf.path()
    cid = uid("lc")
    L = lf.L
    o = [f'<g transform="translate({f(x)} {f(y)}) rotate({f(rot)})">',
         f'<clipPath id="{cid}"><path d="{d}"/></clipPath>',
         f'<path d="{d}" fill="{fill}"/>', f'<g clip-path="url(#{cid})">']
    o.append(f'<path d="{lf.half_region(shade_side)}" fill="{sh}"/>')
    # restrained gloss: one soft lens on the lit half, parallel to the margin
    lit = "l" if shade_side == "r" else "r"
    sg = 1 if lit == "r" else -1
    a = [lf.pt(t, sg * lf.width(t, lit) * 0.62) for t in (0.22, 0.36, 0.52, 0.66)]
    b = [lf.pt(t, sg * lf.width(t, lit) * 0.40) for t in (0.60, 0.46, 0.32)]
    o.append(f'<path d="{cr_path(a + b, closed=True, sharp={0, 3})}" fill="#F5EDDD" opacity="{sheen_op}"/>')
    # faint, fine lateral veins (rubber-plant veins are almost parallel, steep)
    vv = []
    for s in ("r", "l"):
        g = 1 if s == "r" else -1
        for i in range(9):
            t = 0.1 + i * 0.075
            p0 = lf.axis(t)
            pm = lf.pt(t + 0.03, g * lf.width(t + 0.03, s) * 0.5)
            p1 = lf.pt(t + 0.07, g * lf.width(t + 0.07, s) * 0.86)
            vv.append(f"M{f(p0[0])} {f(p0[1])}Q{f(pm[0])} {f(pm[1])} {f(p1[0])} {f(p1[1])}")
    o.append(f'<path d="{"".join(vv)}" fill="none" stroke="#C9D2BC" stroke-width="{f(max(0.8, L * 0.005))}" '
             f'stroke-linecap="round" opacity=".09"/>')
    # midrib: tapered, pale-pink
    mid = [lf.axis(t) for t in (-0.02, 0.2, 0.45, 0.7, 0.93)]
    o.append(f'<path d="{ribbon(mid, L * 0.022, L * 0.004)}" fill="{MIDRIB}" opacity=".62"/>')
    o.append("</g></g>")
    return "".join(o)


def petiole(p0, a, length, w, leaf_rot, L):
    """short thick petiole from stem point p0 heading at angle a, ending tucked
    0.07L inside the leaf base. Returns (svg, leaf base point)."""
    d = dir_of(a)
    q = (p0[0] + d[0] * length, p0[1] + d[1] * length)
    ld = dir_of(leaf_rot)
    mid = (p0[0] + d[0] * length * 0.55, p0[1] + d[1] * length * 0.55)
    inside = (q[0] + ld[0] * L * 0.07, q[1] + ld[1] * L * 0.07)
    back = (p0[0] - d[0] * 4, p0[1] - d[1] * 4)  # start inside the stem
    return f'<path d="{ribbon([back, mid, q, inside], w, w * 0.8)}" fill="{STEM}"/>', q


def sheath(x, y, a, L, w):
    """rolled stipule: slender, slightly curved cone; red with a wine turned half and a
    thin spiral seam."""
    lf = Leaf(L, [(0.0, w * 0.5), (0.14, w * 0.95), (0.35, w * 1.0), (0.6, w * 0.8), (0.82, w * 0.45), (0.95, w * 0.12)],
              bend=0.06, tip_sharp=True, base_sharp=False)
    d = lf.path()
    cid = uid("sc")
    seam = [lf.pt(t, s * lf.width(t) * 0.8) for t, s in ((0.1, -1), (0.35, 0.2), (0.62, 0.9))]
    return (f'<g transform="translate({f(x)} {f(y)}) rotate({f(a)})">'
            f'<clipPath id="{cid}"><path d="{d}"/></clipPath><path d="{d}" fill="{P["red"]}"/>'
            f'<g clip-path="url(#{cid})"><path d="{lf.half_region("r")}" fill="{P["burgundy"]}"/>'
            f'<path d="{cr_path(seam, closed=False)}" fill="none" stroke="{P["wine"]}" stroke-width="1.6" '
            f'stroke-linecap="round" opacity=".55"/></g></g>')


# ------------------------------------------------------------------ layout
S1 = [(292, 612), (289, 520), (284, 420), (282, 320), (285, 230), (290, 168)]   # main stem
S2 = [(312, 612), (320, 530), (336, 460), (350, 400), (360, 346)]              # second stem

# (stem, y, side, petiole angle, petiole len, leaf rot, L, tone, z, bend)
#   z < 0.5 = behind the stems
LEAVES = [
    (S1, 502, -1, -112, 20, -99, 172, "front", 3, 0.05),
    (S1, 486, +1, 105, 18, 92, 150, "back", 0, -0.04),
    (S1, 416, -1, -76, 20, -63, 158, "back", 0.2, -0.04),
    (S1, 356, +1, 62, 18, 50, 138, "back", 0.1, 0.04),
    (S1, 298, -1, -52, 18, -42, 128, "front", 2, -0.03),
    (S1, 250, +1, 50, 16, 40, 104, "deep", 1, 0.03),
    (S1, 206, -1, -50, 14, -40, 80, "young", 2.5, -0.02),
    (S2, 494, +1, 120, 18, 109, 150, "front", 2, -0.05),
    (S2, 440, +1, 88, 16, 78, 132, "deep", 1.5, 0.04),
    (S2, 392, +1, 48, 12, 36, 88, "young", 1.8, 0.02),
]


def build():
    back, front = pot("classic", rx=100, rim_y=586, base_w=70, band=True)
    lay = []
    pets = []
    nodes = []
    for (S, y, side, pa, pl, lr, L, tone, z, bend) in LEAVES:
        p0, _ = at_y(S, y)
        lf = rubber_leaf(L, bend=bend)
        psvg, q = petiole(p0, pa, pl, max(5.0, L * 0.042), lr, L)
        shade_side = "r" if side > 0 else "l"
        lay.append((z, psvg, leaf_svg(lf, tone, q[0], q[1], lr, shade_side)))
        nodes.append((p0, pa))
    out = [back]
    # back leaves (their petioles first)
    lay.sort(key=lambda r: r[0])
    for z, ps, ls in lay:
        if z < 0.5:
            out += [ps, ls]
    # stems: taper to the tip, a darker shaded right edge, node scars
    for S, w0, w1 in ((S2, 11, 6), (S1, 14, 7)):
        out.append(f'<path d="{ribbon(S, w0, w1)}" fill="{STEM}"/>')
        sh = [(x + w0 * 0.22 - (w0 - w1) * 0.22 * i / (len(S) - 1), y) for i, (x, y) in enumerate(S)]
        out.append(f'<path d="{ribbon(sh, w0 * 0.35, w1 * 0.3)}" fill="{STEM_SH}"/>')
    for (p0, pa) in nodes:
        out.append(f'<path d="M{f(p0[0] - 6)} {f(p0[1] + 5)}Q{f(p0[0])} {f(p0[1] + 8)} {f(p0[0] + 6)} {f(p0[1] + 5)}" '
                   f'fill="none" stroke="{P["wine"]}" stroke-width="1.4" opacity=".35"/>')
    # sheaths at the two growing tips (drawn before the front leaves so the youngest
    # leaf can sit over the sheath base)
    tip1, a1 = S1[-1], at_y(S1, S1[-1][1] + 2)[1]
    tip2, a2 = S2[-1], at_y(S2, S2[-1][1] + 2)[1]
    out.append(sheath(tip1[0], tip1[1] + 8, a1, 92, 0.13))
    out.append(sheath(tip2[0], tip2[1] + 6, a2, 70, 0.13))
    for z, ps, ls in lay:
        if z >= 0.5:
            out += [ps, ls]
    out.append(front)
    return "".join(out)


def main():
    reset_ids()
    svg = svg_doc(build(), "Ficus elastica (rubber plant)")
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    with open(os.path.join(ROOT, "out", "ficus_elastica.svg"), "w") as fh:
        fh.write(svg)
    print(len(svg), "bytes")


if __name__ == "__main__":
    main()
