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


def rubber_leaf(L, bend=0.0, asym=0.0, wide=1.0, apex=0.0, sway=0.0):
    """wide scales breadth; apex > 0 shifts the broadest part toward the tip
    (more obovate), < 0 toward the base (more ovate)."""
    r = [(0.035, 0.095), (0.13, 0.190), (0.30, 0.250), (0.48, 0.262), (0.62, 0.240),
         (0.73, 0.198), (0.82, 0.142), (0.895, 0.084), (0.95, 0.040), (0.985, 0.012)]
    # steady taper over the last third: a clean ~70 deg point that still reads as pointed when
    # the blade is tilted or bent (a short concave drip tip on a broad end reads as chopped off)
    r = [(t, w * wide * (1 + apex * (t - 0.45) * 1.4)) for t, w in r]
    l = [(t, w * (1 - asym)) for t, w in r]
    if bend < 0:
        # the narrower half must sit on the outside of the midrib's curve, or one margin runs
        # dead straight into the tip and the point looks chopped off
        r, l = l, r
    return Leaf(L, r, l, bend=bend, tip_sharp=True, base_sharp=False, sway=sway)


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


def bez(p0, c1, c2, p1, n=7):
    out = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        out.append(tuple(u ** 3 * p0[j] + 3 * u * u * t * c1[j] + 3 * u * t * t * c2[j] + t ** 3 * p1[j] for j in (0, 1)))
    return out


def petiole(p0, a, length, w, leaf_rot, L):
    """short thick petiole leaving the stem at angle a and arcing round to meet the leaf
    along its own axis (leaf_rot), ending tucked 0.07L inside the leaf base.
    Returns (svg, leaf base point)."""
    d = dir_of(a)
    ld = dir_of(leaf_rot)
    # chord heads between the two directions; the arc then turns smoothly into the leaf
    m = dir_of((a + leaf_rot) / 2)
    q = (p0[0] + m[0] * length, p0[1] + m[1] * length)
    c1 = (p0[0] + d[0] * length * 0.45, p0[1] + d[1] * length * 0.45)
    c2 = (q[0] - ld[0] * length * 0.4, q[1] - ld[1] * length * 0.4)
    arc = bez(p0, c1, c2, q, 6)
    inside = (q[0] + ld[0] * L * 0.07, q[1] + ld[1] * L * 0.07)
    # start inside the stem, but on the leaf's side of the stem's centre line: a petiole
    # heading left must not reach back across the stem's shaded right half (its square
    # butt would show there); drawn in the stem colour, the join is then seamless
    k = 2.5 if d[0] < 0 else -4
    back = (p0[0] + d[0] * k, p0[1] + d[1] * k)
    return f'<path d="{ribbon([back] + arc[1:] + [inside], w, w * 0.78)}" fill="{STEM}"/>', q


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
S1 = [(280, 612), (278, 530), (267, 440), (261, 350), (267, 262), (282, 200), (296, 164)]   # main stem: slight S lean
S2 = [(327, 612), (340, 550), (362, 496), (388, 452), (408, 426), (420, 410)]               # second stem: leaves the soil apart, leans out

# (stem, y, side, petiole angle, petiole len, leaf rot, L, tone, z, bend, asym, wide, apex, sway)
#   z < 0.5 = behind the stems. bend sign = droop (right-pointing leaves +, left -):
#   old low leaves are big and heavy and hang well below level; young ones near the tips are
#   small, stand up and stay flat. wide < 0.85 = leaf turned on its axis (foreshortened).
LEAVES = [
    (S1, 500, -1, -96, 28, -124, 178, "front", 3, -0.13, 0.04, 1.0, -0.1, 0.05),
    (S1, 426, -1, -72, 24, -112, 148, "back", 0.2, -0.12, 0.0, 0.9, 0.14, -0.04),
    (S1, 398, +1, 40, 18, 52, 100, "deep", 0.1, 0.07, 0.04, 0.92, 0.06, 0.03),
    (S1, 306, +1, 52, 20, 66, 124, "back", 0.1, 0.09, 0.08, 1.06, 0.0, -0.04),
    (S1, 340, -1, -42, 18, -40, 108, "front", 2, -0.07, 0.10, 0.74, 0.1, 0.06),
    (S1, 238, +1, 34, 14, 40, 76, "deep", 1, 0.05, 0.0, 0.96, -0.12, 0.0),
    (S1, 212, -1, -18, 10, -12, 56, "young", 2.5, -0.03, 0.04, 0.84, 0.0, 0.0),
    (S2, 492, +1, 100, 26, 124, 146, "front", 2, 0.14, 0.05, 0.98, 0.1, 0.03),
    (S2, 452, +1, 56, 20, 78, 110, "deep", 1.5, 0.10, 0.0, 1.1, -0.08, 0.05),
    (S2, 432, -1, -32, 14, -14, 74, "front", 2.2, -0.04, 0.06, 0.8, 0.06, 0.0),
    (S2, 416, +1, 34, 10, 26, 56, "young", 1.8, 0.03, 0.06, 0.86, 0.06, 0.0),
]


def build():
    back, front = pot("classic", rx=98, rim_y=586, base_w=69, band=True)
    lay = []
    pets = []
    nodes = []
    for (S, y, side, pa, pl, lr, L, tone, z, bend, asym, wide, apex, sway) in LEAVES:
        p0, _ = at_y(S, y)
        # a strongly bent midrib folds the outer margin round the tip (a chopped-off point);
        # keep the blade's own curve gentle and put the rest of the droop into its rotation
        b2 = max(-0.07, min(0.07, bend))
        lr += math.degrees(math.atan(bend)) - math.degrees(math.atan(b2))   # same chord direction
        lf = rubber_leaf(L, bend=b2, asym=asym, wide=wide, apex=apex, sway=max(-0.03, min(0.03, sway)))
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
    for S, w0, w1 in ((S2, 14, 5), (S1, 22, 5.5)):   # real taper: thick at the soil, slim at the tip
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
        if 0.5 <= z < 3:
            out += [ps, ls]
    out.append(front)
    # the big old lowest leaf hangs out over the rim, in front of the pot
    for z, ps, ls in lay:
        if z >= 3:
            out += [ps, ls]
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
