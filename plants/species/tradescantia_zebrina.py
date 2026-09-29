"""Tradescantia zebrina (inch plant / wandering dude) -- v4 generator.

Growth logic: a handful of jointed, succulent plum stems leave the soil, arch
outward and flop; the longest spill over the rim and trail down the pot. Along
each stem the ovate pointed leaves alternate at swollen nodes, their clasping
bases wrapping the stem, and they shrink toward the growing tip (internodes
shorten there too), where a small folded pair of bracts may hold a flower.

Upper surface: purple-green centre band, two broad silver stripes, a narrow
green margin -- no dark outline; leaves are separated by tone instead (back
tier dusky, front tier bright silver). A few leaves on the trailing strands
twist to show their plum undersides. Three-petalled blush flowers sit at four
shoot tips.

Leaves are drawn once per (shape, tone) as templates in <defs> (unit length
100, shaded half on local +x) and placed with <use>; flipping keeps the shaded
half on the world-right side, as in the rest of the set.
"""
import math
import re
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import PAL, cr_path, cr_sample, ribbon, f, pot, svg_doc, reset_ids  # noqa: E402

P = PAL
SOIL_Y = 606

# ---------------------------------------------------------------- tones
# upper-surface tiers: margin lit/shade, centre band lit/shade, silver lit/shade
TIERS = {
    0: ("#3A4B3F", "#304036", "#4A3441", "#3E2C37", "#8E9A8B", "#7D897A"),
    1: ("#46604A", "#3B523F", P["wine"], "#4E3036", "#BAC3AE", "#A3AD98"),
    2: ("#55705A", "#48614C", "#6C4150", "#5A3743", "#E0E3D3", "#C8CFBB"),
}
# undersides: lit, shade, midrib
UNDER = {
    0: (P["burgundy"], P["wine"], P["rose"]),
    1: (P["plum"], P["burgundy"], P["blush"]),
}
STEM = {0: P["wine"], 1: P["burgundy"], 2: P["plum"]}
COLLAR = {0: "#4A2F35", 1: P["wine"], 2: P["burgundy"]}

# ---------------------------------------------------------------- leaf template
# half-width profile (t along axis from node 0 -> tip 1, w as fraction of length)
PROF = [(-0.06, 0.0), (-0.045, 0.075), (0.0, 0.14), (0.08, 0.205), (0.2, 0.25),
        (0.34, 0.262), (0.48, 0.243), (0.62, 0.195), (0.76, 0.13), (0.88, 0.062),
        (0.95, 0.024), (1.0, 0.0)]
SHAPES = {  # name: (width scale, tip curl)
    "a": (1.0, 0.0),
    "b": (0.9, 0.07),
    "c": (1.08, -0.05),
}


def hw(t):
    for (t0, w0), (t1, w1) in zip(PROF, PROF[1:]):
        if t0 <= t <= t1:
            return w0 + (w1 - w0) * (t - t0) / ((t1 - t0) or 1)
    return 0.0


class Tmpl:
    def __init__(self, wide, curl):
        self.wide, self.curl = wide, curl

    def p(self, t, x):
        """axis t, signed fraction x of half-width -> template units (L=100)."""
        tt = max(0.0, t)
        return ((x * hw(t) * self.wide + self.curl * tt * tt) * 100, -t * 100)

    def outline(self):
        ts = [t for t, _ in PROF]
        right = [self.p(t, 1) for t in ts[1:-1]]
        left = [self.p(t, -1) for t in ts[1:-1]][::-1]
        pts = [self.p(ts[0], 0)] + right + [self.p(1.0, 0)] + left
        return cr_path(pts, closed=True, sharp={len(right) + 1})

    def half(self, side):
        ts = [t for t, _ in PROF]
        edge = [self.p(t, side) for t in ts[1:-1]]
        pts = [self.p(ts[0], 0)] + edge + [self.p(1.0, 0)]
        d = cr_path(pts, closed=False)
        mid = [self.p(t, 0) for t in (0.75, 0.5, 0.25)]
        return d + "".join(f"L{f(x)} {f(y)}" for x, y in mid) + "Z"

    def region(self, side, t0, t1, lo, hi, taper0=0.12, taper1=0.25, jit=None):
        """strip between fractions lo..hi of the half-width, tapering at both ends."""
        n = 8
        outer, inner = [], []
        for i in range(1, n):
            t = t0 + (t1 - t0) * i / n
            env = min(1.0, (t - t0) / taper0, (t1 - t) / taper1) ** 0.6
            c, h = (lo + hi) / 2, (hi - lo) / 2 * env
            j = jit[i] if jit else 0
            outer.append(self.p(t, side * min(0.975, c + h + j)))
            inner.append(self.p(t, side * (c - h + j * 0.4)))
        a = self.p(t0, side * lo)
        b = self.p(t1, side * (lo + hi) / 2)
        ring = [a] + outer + [b] + inner[::-1]
        return cr_path(ring, closed=True, sharp={0, len(outer) + 1})

    def band(self, side, frac=0.3):
        ts = [0.02, 0.14, 0.3, 0.46, 0.62, 0.78, 0.9]
        edge = [self.p(t, side * frac) for t in ts]
        pts = [self.p(-0.04, 0)] + edge + [self.p(0.985, 0)]
        d = cr_path(pts, closed=False)
        return d + "".join(f"L{f(x)} {f(y)}" for x, y in [self.p(t, 0) for t in (0.6, 0.3)]) + "Z"

    def line(self, x, t0, t1, n=6):
        pts = [self.p(t0 + (t1 - t0) * i / n, x) for i in range(n + 1)]
        return "M" + "L".join(f"{f(a)} {f(b)}" for a, b in pts)


def tmpl_upper(tid, shape, tier, seed):
    wide, curl = SHAPES[shape]
    lf = Tmpl(wide, curl)
    mg, mgs, bd, bds, sv, svs = TIERS[tier]
    rnd = random.Random(seed)
    g = [f'<g id="{tid}"><path d="{lf.outline()}" fill="{mg}"/>',
         f'<path d="{lf.half(1)}" fill="{mgs}"/>']
    # broad silver stripes reaching close to the edge: the margin is a narrow
    # green seam, not an outline
    for side, col in ((-1, sv), (1, svs)):
        jit = [rnd.uniform(-0.03, 0.03) for _ in range(9)]
        g.append(f'<path d="{lf.region(side, 0.0, 0.93, 0.27, 0.975 if side < 0 else 0.93, taper0=0.2, taper1=0.4, jit=jit)}" fill="{col}"/>')
    g.append(f'<path d="{lf.band(-1, 0.32)}" fill="{bd}"/><path d="{lf.band(1, 0.32)}" fill="{bds}"/>')
    # fine longitudinal venation inside the silver (low contrast)
    vl = "".join(lf.line(s * 0.56, 0.1, 0.8) for s in (-1, 1))
    g.append(f'<path d="{vl}" fill="none" stroke="{bds}" stroke-width="1.6" '
             f'stroke-linecap="round" opacity=".2"/>')
    g.append(f'<path d="{lf.line(0, 0.0, 0.9)}" fill="none" stroke="{sv}" stroke-width="2" '
             f'stroke-linecap="round" opacity=".35"/></g>')
    return "".join(g)


def tmpl_under(tid, shape, tone):
    wide, curl = SHAPES[shape]
    lf = Tmpl(wide, curl)
    lit, shd, mid = UNDER[tone]
    vl = "".join(lf.line(s * 0.5, 0.08, 0.82) for s in (-1, 1))
    return (f'<g id="{tid}"><path d="{lf.outline()}" fill="{lit}"/>'
            f'<path d="{lf.half(1)}" fill="{shd}"/>'
            f'<path d="{vl}" fill="none" stroke="{shd}" stroke-width="1.5" stroke-linecap="round" opacity=".35"/>'
            f'<path d="{lf.line(0, 0.0, 0.9)}" fill="none" stroke="{mid}" stroke-width="2.2" '
            f'stroke-linecap="round" opacity=".55"/></g>')


def _ints(svg):
    """template coords are in 1/100 leaf units: integers are plenty."""
    return re.sub(r'd="[^"]*"', lambda d: re.sub(r"-?\d+\.\d+", lambda m: str(round(float(m.group()))),
                                                 d.group()), svg)


def defs():
    out = ["<defs>"]
    k = 0
    for tier in TIERS:
        for s in SHAPES:
            k += 1
            out.append(tmpl_upper(f"z{tier}{s}", s, tier, k))
    for tone in UNDER:
        for s in ("a", "b"):
            out.append(tmpl_under(f"u{tone}{s}", s, tone))
    out.append("</defs>")
    return _ints("".join(out))


def place(tid, x, y, rot, L):
    """shaded half (+x local) must face world right; flip when it would not."""
    flip = math.cos(math.radians(rot)) < 0
    sx = (-1 if flip else 1) * L / 100
    return (f'<use href="#{tid}" transform="translate({f(x)} {f(y)}) rotate({f(rot)}) '
            f'scale({sx:.3f} {L / 100:.3f})"/>')


# ---------------------------------------------------------------- flower
def flower(x, y, r, rot=0):
    """Three broad blush petals, rose eye, cream anthers."""
    out = [f'<g transform="translate({f(x)} {f(y)}) rotate({f(rot)})">']
    tones = ("#EBC3BE", P["blush"], "#E2B1AD")
    pd = cr_path([(0, 0), (r * 0.52, -r * 0.3), (r * 0.6, -r * 0.72), (r * 0.3, -r * 1.02), (0, -r * 1.1),
                  (-r * 0.3, -r * 1.02), (-r * 0.6, -r * 0.72), (-r * 0.52, -r * 0.3)], closed=True, sharp={0})
    for i in range(3):
        out.append(f'<path d="{pd}" fill="{tones[i]}" transform="rotate({i * 120})"/>')
    # a faint crease down each petal
    out.append(f'<path d="' + "".join(
        f"M{f(math.sin(math.radians(i * 120)) * r * 0.3)} {f(-math.cos(math.radians(i * 120)) * r * 0.3)}"
        f"L{f(math.sin(math.radians(i * 120)) * r * 0.85)} {f(-math.cos(math.radians(i * 120)) * r * 0.85)}"
        for i in range(3)) + f'" stroke="{P["rose"]}" stroke-width="1.3" stroke-linecap="round" opacity=".45"/>')
    out.append(f'<circle r="{f(r * 0.3)}" fill="{P["rose"]}"/>')
    for i in range(3):
        a = math.radians(i * 120 + 60)
        out.append(f'<circle cx="{f(math.sin(a) * r * 0.32)}" cy="{f(-math.cos(a) * r * 0.32)}" '
                   f'r="{f(r * 0.12)}" fill="{P["ivory"]}"/>')
    out.append("</g>")
    return "".join(out)


# ---------------------------------------------------------------- shoots
def unit(v):
    m = math.hypot(*v) or 1
    return (v[0] / m, v[1] / m)


def rot_of(u):
    return math.degrees(math.atan2(u[0], -u[1]))


def along(s, frac):
    d = [0.0]
    for p, q in zip(s, s[1:]):
        d.append(d[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    tgt = frac * d[-1]
    for i in range(1, len(s)):
        if d[i] >= tgt:
            u = (tgt - d[i - 1]) / ((d[i] - d[i - 1]) or 1)
            p = (s[i - 1][0] + (s[i][0] - s[i - 1][0]) * u, s[i - 1][1] + (s[i][1] - s[i - 1][1]) * u)
            return p, unit((s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1])), d[-1]
    return s[-1], unit((s[-1][0] - s[-2][0], s[-1][1] - s[-2][1])), d[-1]


def leaf_dir(t, side, ang, up):
    a = math.radians(ang * side)
    dx = t[0] * math.cos(a) - t[1] * math.sin(a)
    dy = t[0] * math.sin(a) + t[1] * math.cos(a)
    return unit((dx, dy - up))


class Shoot:
    """One jointed stem. nodes: (frac, side, L, tid, ang, up)."""

    def __init__(self, pts, w0, w1, st, nodes, tip_flower=None):
        self.pts, self.w0, self.w1, self.st = pts, w0, w1, st
        self.nodes, self.tip_flower = nodes, tip_flower
        self.s = cr_sample(pts, 10)
        self.total = along(self.s, 1.0)[2]

    def stem(self):
        out = [f'<path d="{ribbon(self.pts, self.w0, self.w1, per=4)}" fill="{STEM[self.st]}"/>']
        coll = []
        for fr, *_ in self.nodes:
            if fr > 0.97:
                continue
            p, _, _ = along(self.s, fr)
            q, _, _ = along(self.s, min(1.0, fr + 7 / self.total))
            coll.append(f"M{f(p[0])} {f(p[1])}l{f(q[0] - p[0])} {f(q[1] - p[1])}")
        if coll:
            cw = (self.w0 + self.w1) / 2 * 1.35
            out.append(f'<path d="{"".join(coll)}" stroke="{COLLAR[self.st]}" stroke-width="{f(cw)}" '
                       f'stroke-linecap="round"/>')
        return "".join(out)

    def leaves(self):
        out = []
        for fr, side, L, tid, ang, up in self.nodes:
            p, t, _ = along(self.s, fr)
            out.append(place(tid, p[0], p[1], rot_of(leaf_dir(t, side, ang, up)), L))
        return "".join(out)

    def flower(self):
        if not self.tip_flower:
            return ""
        r, lift, rot = self.tip_flower
        p, t, _ = along(self.s, 1.0)
        # the flower sits just past the terminal bracts, on the stem axis
        return flower(p[0] + t[0] * lift, p[1] + t[1] * lift, r, rot)


def grow(n, L0, L1, tier, first=1, f0=0.2, ang0=58, ang1=26, up=0.25, under=(), utone=1,
         shapes="acbab", seed=0, tier_tip=None, bracts=False):
    """Alternating nodes, leaves shrinking toward the tip, internodes shortening."""
    rnd = random.Random(seed)
    out = []
    side = first
    for i in range(n):
        u = i / max(1, n - 1)
        fr = f0 + (1 - f0) * (1 - (1 - u) ** 1.35)
        if 0 < i < n - 1:
            fr += rnd.uniform(-0.02, 0.02)
        L = (L0 + (L1 - L0) * u ** 0.9) * rnd.uniform(0.93, 1.07)
        a = (ang0 + (ang1 - ang0) * u) * rnd.uniform(0.85, 1.15)
        uu = up * rnd.uniform(0.7, 1.3)
        shp = shapes[i % len(shapes)]
        tr = tier if (tier_tip is None or u < 0.6) else tier_tip
        tid = f"u{utone}{'a' if shp == 'c' else shp}" if i in under else f"z{tr}{shp}"
        out.append((min(fr, 1.0), side, L, tid, a, uu))
        side = -side
    if bracts:  # terminal pair of small folded leaves cupping the flower
        tr = tier if tier_tip is None else tier_tip
        out.append((1.0, side, L1 * 0.72, f"z{tr}b", 34, up))
        out.append((1.0, -side, L1 * 0.62, f"z{tr}a", 30, up))
    return out


# ---------------------------------------------------------------- plant
def build():
    back, front = pot("classic", cx=300, rim_y=590, rx=102, base_w=72, band=True)
    out = [defs(), back]
    Y = SOIL_Y

    # crown, back to front. Stems arch outward and flop; the tallest stand in the
    # back, low bushy ones in front hide the stem bases.
    crown = [
        # --- back tier (dusky)
        Shoot([(297, Y), (292, 530), (282, 450), (278, 370), (286, 296), (304, 236)], 7.0, 3.8, 0,
              grow(7, 96, 44, 0, first=1, f0=0.26, seed=1, ang0=56, up=0.1, tier_tip=1)),
        Shoot([(308, Y), (320, 540), (346, 468), (388, 408), (436, 374), (484, 368)], 6.8, 3.6, 0,
              grow(7, 94, 42, 0, first=-1, f0=0.26, seed=2, up=0.35, tier_tip=1, under={2}, utone=0)),
        Shoot([(290, Y), (278, 544), (250, 476), (206, 424), (158, 404), (116, 412)], 6.8, 3.6, 0,
              grow(7, 92, 40, 0, first=1, f0=0.28, seed=3, up=0.35, tier_tip=1)),
        # --- middle tier
        Shoot([(313, Y), (340, 562), (392, 522), (446, 506), (496, 516), (530, 546)], 6.2, 3.4, 1,
              grow(6, 90, 44, 1, first=1, f0=0.28, seed=4, up=0.55, ang0=64)),
        Shoot([(286, Y), (262, 566), (214, 534), (160, 520), (112, 534), (76, 562)], 6.2, 3.4, 1,
              grow(6, 88, 42, 1, first=-1, f0=0.3, seed=5, up=0.55, ang0=64, under={4}, utone=1)),
        Shoot([(300, Y), (300, 550), (282, 486), (254, 424), (232, 364), (222, 318)], 6.2, 3.4, 1,
              grow(6, 98, 44, 1, first=-1, f0=0.34, seed=6, up=0.15, tier_tip=2, bracts=True),
              tip_flower=(21, 15, -12)),
        Shoot([(305, Y), (314, 550), (340, 494), (374, 452), (404, 430)], 6.0, 3.4, 1,
              grow(4, 96, 52, 1, first=1, f0=0.4, seed=7, up=0.2, tier_tip=2, bracts=True),
              tip_flower=(19, 13, 14)),
        # --- front tier (bright): low leaves covering the stem bases
        Shoot([(293, Y), (272, 590), (240, 578), (212, 576)], 5.8, 3.6, 2,
              grow(3, 100, 72, 2, first=1, f0=0.42, seed=8, ang0=50, ang1=34, up=0.4, shapes="cab")),
        Shoot([(309, Y), (334, 588), (366, 578), (396, 576)], 5.8, 3.6, 2,
              grow(3, 98, 70, 2, first=-1, f0=0.42, seed=9, ang0=50, ang1=34, up=0.4, shapes="acb")),
        Shoot([(301, Y), (304, 570), (314, 530), (330, 498)], 5.6, 3.6, 2,
              grow(3, 104, 66, 2, first=-1, f0=0.45, seed=10, ang0=56, ang1=30, up=0.1, shapes="bca")),
    ]
    for sh in crown:
        out += [sh.stem(), sh.leaves()]
    out += [sh.flower() for sh in crown]

    out.append(front)

    # trailing strands, drawn over the pot. Leaves turn outward/up off the
    # hanging stems; some twist to show the plum underside.
    trails = [
        # long left strand, all the way down past the pot foot
        Shoot([(232, 600), (198, 594), (170, 610), (152, 648), (142, 696), (138, 734), (142, 760)], 5.4, 2.8, 2,
              grow(8, 74, 34, 2, first=-1, f0=0.08, seed=11, ang0=78, ang1=44, up=0.9, under={2, 5},
                   utone=1, shapes="abcab", tier_tip=1, bracts=True),
              tip_flower=(15, 10, 10)),
        # medium right strand
        Shoot([(370, 600), (406, 594), (436, 612), (454, 652), (462, 700), (462, 730)], 5.2, 2.8, 2,
              grow(7, 72, 34, 2, first=1, f0=0.08, seed=12, ang0=78, ang1=44, up=0.9, under={3},
                   utone=0, shapes="cabca", tier_tip=1)),
        # short front drape
        Shoot([(326, 602), (344, 614), (352, 638), (352, 662)], 4.4, 2.8, 2,
              grow(3, 58, 36, 2, first=1, f0=0.35, seed=13, ang0=74, ang1=50, up=0.8, under={1},
                   utone=0, shapes="bac")),
    ]
    out += [sh.stem() for sh in trails]
    out += [sh.leaves() for sh in trails]
    out += [sh.flower() for sh in trails]
    return "".join(out)


if __name__ == "__main__":
    reset_ids()
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "..", "out", "tradescantia_zebrina.svg")
    open(dst, "w").write(svg_doc(build(), "Tradescantia zebrina (inch plant)"))
    print("wrote", os.path.normpath(dst), os.path.getsize(dst), "bytes")
