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
# leaf tone sets: (fill, turned-away half, sheen, midrib). Sheen = cream over the
# fill at ~17 %, midrib = MIDRIB over the fill at ~62 %, both pre-blended to solids
# (card face has no transparency; faint overlays vanish in pigment print).
TONES = {
    "back":  ("#27392C", "#1F3025", "#4A584A", "#98887D"),   # night
    "deep":  ("#314B37", "#27392C", "#526753", "#9C8F81"),
    "front": ("#405D43", "#34503A", "#5F755D", "#A19685"),   # forest
    "young": ("#5B7458", "#4B6349", "#75896F", "#AC9F8D"),   # new leaf, a touch lighter
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


def rubber_leaf(L, bend=0.0, asym=0.0, wide=1.0, apex=0.0):
    """wide scales breadth; apex > 0 shifts the broadest part toward the tip
    (more obovate), < 0 toward the base (more ovate)."""
    r = [(0.035, 0.095), (0.13, 0.190), (0.30, 0.250), (0.50, 0.262), (0.68, 0.232),
         (0.83, 0.158), (0.925, 0.070), (0.972, 0.022)]
    r = [(t, w * wide * (1 + apex * (t - 0.45) * 1.4)) for t, w in r]
    l = [(t, w * (1 - asym)) for t, w in r]
    return Leaf(L, r, l, bend=bend, tip_sharp=True, base_sharp=False)


def leaf_svg(lf, tone, x, y, rot, shade_side="r"):
    fill, sh, sheen, rib = TONES[tone]
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
    o.append(f'<path d="{cr_path(a + b, closed=True, sharp={0, 3})}" fill="{sheen}"/>')
    # midrib: tapered, pale-pink
    mid = [lf.axis(t) for t in (-0.02, 0.2, 0.45, 0.7, 0.93)]
    o.append(f'<path d="{ribbon(mid, 4.4, 1.6)}" fill="{rib}"/>')   # print-safe knockout width
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
    # start inside the stem, but on the leaf's side of the stem's centre line: a petiole
    # heading left must not reach back across the stem's shaded right half (its square
    # butt would show there); drawn in the stem colour, the join is then seamless
    k = 2.5 if d[0] < 0 else -4
    back = (p0[0] + d[0] * k, p0[1] + d[1] * k)
    return f'<path d="{ribbon([back, mid, q, inside], w, w * 0.8)}" fill="{STEM}"/>', q


def sheath(x, y, a, L, w):
    """rolled stipule: slender, slightly curved cone; red with a wine turned half and a
    thin spiral seam."""
    lf = Leaf(L, [(0.0, w * 0.5), (0.14, w * 0.95), (0.35, w * 1.0), (0.6, w * 0.8), (0.82, w * 0.45), (0.95, w * 0.12)],
              bend=0.06, tip_sharp=True, base_sharp=False)
    d = lf.path()
    cid = uid("sc")
    return (f'<g transform="translate({f(x)} {f(y)}) rotate({f(a)})">'
            f'<clipPath id="{cid}"><path d="{d}"/></clipPath><path d="{d}" fill="{P["red"]}"/>'
            f'<g clip-path="url(#{cid})"><path d="{lf.half_region("r")}" fill="{P["burgundy"]}"/>'
            f'</g></g>')   # (hairline seam dropped: below print minimum)


# ------------------------------------------------------------------ layout
S1 = [(292, 612), (289, 520), (284, 420), (282, 320), (285, 230), (290, 168)]   # main stem
S2 = [(312, 612), (322, 534), (342, 468), (366, 410), (384, 358)]              # second stem: leans out

# (stem, y, side, petiole angle, petiole len, leaf rot, L, tone, z, bend, asym, wide, apex)
#   z < 0.5 = behind the stems. Internodes, sizes, angles and outlines all vary
#   (older leaves broad and drooping, young ones narrow and upright).
LEAVES = [
    (S1, 502, -1, -114, 22, -99, 176, "front", 3, 0.06, 0.04, 1.02, -0.1),
    (S1, 432, -1, -72, 18, -58, 150, "back", 0.2, -0.05, 0.0, 0.92, 0.12),
    (S1, 356, +1, 64, 18, 53, 146, "back", 0.1, 0.05, 0.08, 1.06, 0.0),
    (S1, 316, -1, -50, 16, -37, 110, "front", 2, -0.04, 0.06, 0.88, 0.1),
    (S1, 262, +1, 58, 14, 50, 96, "deep", 1, 0.03, 0.0, 1.0, -0.12),
    (S1, 216, +1, 34, 10, 20, 68, "young", 2.5, 0.02, 0.04, 0.9, 0.0),
    (S2, 470, +1, 112, 18, 100, 150, "front", 2, -0.05, 0.05, 0.96, 0.1),
    (S2, 428, +1, 72, 15, 58, 118, "deep", 1.5, 0.04, 0.0, 1.1, -0.08),
    (S2, 404, -1, -38, 12, -27, 84, "front", 2.2, -0.03, 0.04, 0.9, 0.06),   # added: crosses the gap, breaks the pairing
    (S2, 378, +1, 46, 10, 34, 68, "young", 1.8, 0.02, 0.06, 0.86, 0.06),
]


def build():
    back, front = pot("classic", rx=98, rim_y=586, base_w=69, band=True)
    lay = []
    pets = []
    nodes = []
    for (S, y, side, pa, pl, lr, L, tone, z, bend, asym, wide, apex) in LEAVES:
        p0, _ = at_y(S, y)
        lf = rubber_leaf(L, bend=bend, asym=asym, wide=wide, apex=apex)
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
    # (hairline node scars dropped: below print minimum)
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
