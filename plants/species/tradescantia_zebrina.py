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
SILVER_EDGE = {-1: 1.03, 1: 0.96}   # silver stripes run almost to the edge: margin is a seam

# ---------------------------------------------------------------- tones
# upper-surface tiers: margin lit/shade, centre band lit/shade, silver lit/shade
TIERS = {
    0: ("#5B6B5C", "#4F5E50", "#4A3441", "#3E2C37", "#8E9A8B", "#7D897A"),
    1: ("#788A72", "#6B7C65", P["wine"], "#4E3036", "#BAC3AE", "#A3AD98"),
    2: ("#94A48B", "#86957D", "#6C4150", "#5A3743", "#E0E3D3", "#C8CFBB"),
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
        n = 6
        outer, inner = [], []
        for i in range(1, n):
            t = t0 + (t1 - t0) * i / n
            env = min(1.0, (t - t0) / taper0, (t1 - t) / taper1) ** 0.6
            c, h = (lo + hi) / 2, (hi - lo) / 2 * env
            j = jit[i] if jit else 0
            outer.append(self.p(t, side * min(1.03, c + h + j)))
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


# pattern proportions as fractions of the local half-width. Two size classes so the
# green margin and plum band stay print-safe on the small tip leaves too
# (large: L >= 60 world units, small: below that).
PATTERN = {  # size: (band, silver_lo, silver_hi lit side, silver_hi shade side)
    "": (0.37, 0.28, 0.84, 0.81),
    "s": (0.34, 0.26, 0.72, 0.70),
    "t": (0.44, 0.30, 1.03, 1.03),   # tiny tip leaves / bracts: no margin sliver
}
SMALL_L, TINY_L = 60, 40


def tmpl_upper(tid, shape, tier, seed, size=""):
    """All opaque fills, no strokes: green margin -> two broad silver stripes ->
    plum centre band. Widths are chosen so every band is >= ~3 world units on
    the leaves that use this template (print minimum at ~0.055 mm/unit)."""
    wide, curl = SHAPES[shape]
    lf = Tmpl(wide, curl)
    mg, mgs, bd, bds, sv, svs = TIERS[tier]
    band, lo, hi_l, hi_s = PATTERN[size]
    rnd = random.Random(seed)
    g = [f'<g id="{tid}"><path d="{lf.outline()}" fill="{mg}"/>',
         f'<path d="{lf.half(1)}" fill="{mgs}"/>']
    for side, col, hi in ((-1, sv, hi_l), (1, svs, hi_s)):
        jit = [rnd.uniform(-0.05, 0.04) for _ in range(9)]
        g.append(f'<path d="{lf.region(side, 0.0, 0.93, lo, hi, taper0=0.2, taper1=0.4, jit=jit)}" fill="{col}"/>')
    g.append(f'<path d="{lf.band(-1, band)}" fill="{bd}"/><path d="{lf.band(1, band)}" fill="{bds}"/></g>')
    return "".join(g)


def tmpl_under(tid, shape, tone):
    """Plum underside: flat lit / shaded halves only (the tonal split reads as
    the midrib; no hairline strokes)."""
    wide, curl = SHAPES[shape]
    lf = Tmpl(wide, curl)
    lit, shd, _ = UNDER[tone]
    return (f'<g id="{tid}"><path d="{lf.outline()}" fill="{lit}"/>'
            f'<path d="{lf.half(1)}" fill="{shd}"/></g>')


def _ints(svg):
    """template coords are in 1/100 leaf units: integers are plenty."""
    return re.sub(r'd="[^"]*"', lambda d: re.sub(r"-?\d+\.\d+", lambda m: str(round(float(m.group()))),
                                                 d.group()), svg)


def defs():
    out = ["<defs>"]
    k = 0
    for tier in TIERS:
        for s in SHAPES:
            for size in PATTERN:
                k += 1
                out.append(tmpl_upper(f"z{tier}{s}{size}", s, tier, k, size))
    for tone in UNDER:
        for s in ("a", "b"):
            out.append(tmpl_under(f"u{tone}{s}", s, tone))
    out.append("</defs>")
    return _ints("".join(out))


def place(tid, x, y, rot, L):
    """shaded half (+x local) must face world right; flip when it would not."""
    flip = math.cos(math.radians(rot)) < 0
    if tid.startswith("z") and L < SMALL_L:
        if L < TINY_L:  # tiny leaves: two outline variants are plenty
            tid = tid.replace("c", "a") + "t"
        else:
            tid += "s"
    sx = (-1 if flip else 1) * L / 100
    return (f'<use href="#{tid}" transform="translate({f(x)} {f(y)}) rotate({f(rot)}) '
            f'scale({sx:.3f} {L / 100:.3f})"/>')


# ---------------------------------------------------------------- flower
def flower(x, y, r, rot=0):
    """Three broad blush petals, rose eye, paper-white centre."""
    out = [f'<g transform="translate({f(x)} {f(y)}) rotate({f(rot)})">']
    tones = ("#EBC3BE", P["blush"], "#E2B1AD")
    pd = cr_path([(0, 0), (r * 0.52, -r * 0.3), (r * 0.6, -r * 0.72), (r * 0.3, -r * 1.02), (0, -r * 1.1),
                  (-r * 0.3, -r * 1.02), (-r * 0.6, -r * 0.72), (-r * 0.52, -r * 0.3)], closed=True, sharp={0})
    for i in range(3):
        out.append(f'<path d="{pd}" fill="{tones[i]}" transform="rotate({i * 120})"/>')
    # rose eye with a single paper-white centre (>= 4.8 units across: print-safe knockout dot)
    out.append(f'<circle r="{f(max(4.2, r * 0.32))}" fill="{P["rose"]}"/>')
    out.append(f'<circle r="{f(max(2.4, r * 0.15))}" fill="#FFFFFF"/>')
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

    def __init__(self, pts, w0, w1, st, nodes, tip_flower=None, lead=None):
        self.pts, self.w0, self.w1, self.st = pts, w0, w1, st
        self.lead = lead  # extra stem points before pts[0] (stem only; nodes stay put)
        self.nodes, self.tip_flower = nodes, tip_flower
        self.s = cr_sample(pts, 10)
        self.total = along(self.s, 1.0)[2]

    def ribbon(self):
        return ribbon((self.lead or []) + self.pts, self.w0, self.w1, per=4)

    def stem(self, clip=None):
        cp = f' clip-path="url(#{clip})"' if clip else ""
        out = [f'<path d="{self.ribbon()}" fill="{STEM[self.st]}"{cp}/>']
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
         shapes="acbab", seed=0, tier_tip=None, bracts=False, drop=()):
    """Alternating nodes, leaves shrinking toward the tip, internodes shortening.
    drop: node indices left bare (leaf shed) -- thins the dense centre without
    disturbing the rest of the shoot's sequence."""
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
        if i not in drop:
            out.append((min(fr, 1.0), side, L, tid, a, uu))
        side = -side
    if bracts:  # terminal pair of small folded leaves cupping the flower
        tr = tier if tier_tip is None else tier_tip
        out.append((1.0, side, L1 * 0.86, f"z{tr}b", 34, up))
        out.append((1.0, -side, L1 * 0.76, f"z{tr}a", 30, up))
    return out


# ---------------------------------------------------------------- plant
def build():
    back, front = pot("classic", cx=300, rim_y=590, rx=92, base_w=65, band=True)
    out = [defs(), back]
    Y = SOIL_Y

    # crown, back to front. Stems arch outward and flop; the tallest stand in the
    # back, low bushy ones in front hide the stem bases.
    crown = [
        # --- back tier (dusky)
        Shoot([(297, Y), (292, 530), (282, 450), (278, 370), (286, 296), (304, 236)], 7.0, 3.8, 0,
              grow(7, 96, 44, 0, first=1, f0=0.26, seed=1, ang0=56, up=0.1, tier_tip=1, drop={0, 1})),
        Shoot([(308, Y), (320, 540), (346, 468), (388, 408), (436, 374), (484, 368)], 6.8, 3.6, 0,
              # all upper sides: this shoot's leaves stand upright, so none is turned to show its underside
              # (plum undersides are kept for the trailing / turned leaves)
              grow(7, 94, 42, 0, first=-1, f0=0.26, seed=2, up=0.35, tier_tip=1, drop={0, 1})),
        Shoot([(290, Y), (278, 544), (250, 476), (206, 424), (158, 404), (116, 412)], 6.8, 3.6, 0,
              grow(7, 92, 40, 0, first=1, f0=0.28, seed=3, up=0.35, tier_tip=1, drop={0})),
        # --- middle tier
        Shoot([(313, Y), (340, 562), (392, 522), (446, 506), (494, 516), (524, 546)], 6.2, 3.4, 1,
              grow(6, 90, 44, 1, first=1, f0=0.28, seed=4, up=0.55, ang0=64)),
        Shoot([(286, Y), (262, 566), (214, 534), (160, 520), (112, 534), (76, 562)], 6.2, 3.4, 1,
              grow(6, 88, 42, 1, first=-1, f0=0.3, seed=5, up=0.55, ang0=64, under={4}, utone=1)),
        Shoot([(300, Y), (300, 550), (282, 486), (254, 424), (232, 364), (222, 318)], 6.2, 3.4, 1,
              grow(6, 98, 44, 1, first=-1, f0=0.34, seed=6, up=0.15, tier_tip=2, bracts=True),
              tip_flower=(21, 15, -12)),
        Shoot([(305, Y), (314, 550), (340, 494), (374, 452), (404, 430)], 6.0, 3.4, 1,
              grow(4, 96, 52, 1, first=1, f0=0.4, seed=7, up=0.2, tier_tip=2, bracts=True),
              tip_flower=(19, 13, 14)),
        # --- front tier (bright): low leaves covering the stem bases. The lowest leaf of
        # the centre shoot and the two back-tier leaves behind it are shed (drop=): opens
        # the densest part of the crown onto the stems, with no same-tier leaves meeting.
        Shoot([(293, Y), (272, 590), (240, 578), (212, 576)], 5.8, 3.6, 2,
              grow(3, 100, 72, 2, first=1, f0=0.42, seed=8, ang0=50, ang1=34, up=0.4, shapes="cab")),
        Shoot([(309, Y), (334, 588), (366, 578), (396, 576)], 5.8, 3.6, 2,
              grow(3, 98, 70, 2, first=-1, f0=0.42, seed=9, ang0=50, ang1=34, up=0.4, shapes="acb")),
        Shoot([(301, Y), (304, 570), (314, 530), (330, 498)], 5.6, 3.6, 2,
              grow(3, 104, 66, 2, first=-1, f0=0.45, seed=10, ang0=56, ang1=30, up=0.1, shapes="bca",
                   drop={0}, under={1}, utone=1)),   # its leaning leaf is turned: solid plum rests the eye
    ]
    # trailing strands leave the soil behind the crown: their first stretch (inside the
    # pot opening) is drawn here, under the crown; the part crossing the rim is drawn
    # again over the pot front, clipped to outside the opening -- seamless at the lip.
    trails = trail_shoots()
    out += [f'<path d="{sh.ribbon()}" fill="{STEM[sh.st]}"/>' for sh in trails if sh.lead]
    for sh in crown:
        out += [sh.stem(), sh.leaves()]
    out += [sh.flower() for sh in crown]

    out.append(front)

    # front copy: only beyond the lip crossing (x side of the strand) and outside the opening
    ell = f"M{f(300 - 92)} 590A92 13.8 0 1 0 {f(300 + 92)} 590A92 13.8 0 1 0 {f(300 - 92)} 590Z"
    for i, (x0, x1) in enumerate(((0, 245), (357, 600))):
        out.append(f'<clipPath id="rimout{i}"><path clip-rule="evenodd" '
                   f'd="M{x0} 0H{x1}V800H{x0}Z{ell}"/></clipPath>')
    out += [sh.stem(f"rimout{i}" if sh.lead else None) for i, sh in enumerate(trails)]
    out += [sh.leaves() for sh in trails]
    out += [sh.flower() for sh in trails]
    body = "".join(out)
    # drop templates no <use> references (keeps the file small)
    used = set(re.findall(r'href="#(\w+)"', body))
    return re.sub(r'<g id="(\w+)">.*?</g>', lambda m: m.group(0) if m.group(1) in used else "", body)


def trail_shoots():
    """trailing strands, drawn over the pot. Leaves turn outward/up off the
    hanging stems; some twist to show the plum underside."""
    return [
        # long left strand: hangs down the pot side, tip turning out well above the ground line
        Shoot([(239, 600), (208, 594), (172, 610), (150, 644), (134, 674), (116, 694), (98, 700)], 5.4, 2.8, 2,
              grow(8, 74, 34, 2, first=-1, f0=0.08, seed=11, ang0=78, ang1=44, up=0.9, under={2, 5},
                   utone=1, shapes="abcab", tier_tip=1, bracts=True),
              tip_flower=(15, 10, 10), lead=[(272, 614), (268, 597), (254, 592)]),
        # medium right strand: tip lifted ~26 units so its last leaves clear the card's bottom-right marks
        Shoot([(363, 600), (396, 594), (432, 610), (453, 644), (461, 680), (463, 704)], 5.2, 2.8, 2,
              grow(7, 72, 34, 2, first=1, f0=0.08, seed=12, ang0=78, ang1=44, up=0.9, under={3},
                   utone=0, shapes="cabca", tier_tip=1), lead=[(318, 614), (325, 596), (345, 592)]),
        # short front drape
        Shoot([(326, 602), (344, 614), (352, 638), (352, 662)], 4.4, 2.8, 2,
              grow(3, 58, 36, 2, first=1, f0=0.35, seed=13, ang0=74, ang1=50, up=0.8, under={1},
                   utone=0, shapes="bac")),
    ]


if __name__ == "__main__":
    reset_ids()
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "..", "out", "tradescantia_zebrina.svg")
    open(dst, "w").write(svg_doc(build(), "Tradescantia zebrina (inch plant)"))
    print("wrote", os.path.normpath(dst), os.path.getsize(dst), "bytes")
