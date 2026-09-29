"""Chlorophytum comosum 'Vittatum' type (variegated spider plant) -- v4.

A fountain of long, narrow, channelled strap leaves from one central crown.
Each leaf = green margin band + pale central stripe; the concave (channel)
half of both the margin and the stripe takes the flat shade tone, which gives
the V-channel look in the set's half-leaf shading language.  Leaves are
layered back -> front with the margin green stepping lighter toward the
viewer, so every overlap reads as a green edge over a different green.
Two wiry runners arch out and down, each ending in a small plantlet rosette
with a few aerial root nubs.  The two front "drape" leaves are drawn over the
pot and clipped at the rim's front edge so their bases still sink into the
soil.

Run:  python3 species/chlorophytum_comosum.py   -> out/chlorophytum_comosum.svg
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, cr_path, ribbon, f, uid, pot, svg_doc, reset_ids  # noqa: E402

P = PAL
CX = 300
RIM_Y = 586
RX = 100
CROWN = (300, 614)      # leaf bases converge here (hidden by the rim front)

# tiers: margin, margin shade, stripe, stripe shade
TIER = {
    "back":  (P["deep"], P["night"], P["pale"], P["light"]),
    "midd":  (P["forest"], "#34503A", P["spot"], P["pale"]),
    "front": (P["mid"], "#4B6349", P["spot"], P["pale"]),
    "fore":  (P["sage"], "#6A7E60", P["ivory"], P["spot"]),
    "top":   (P["light"], "#8E9E80", P["ivory"], P["spot"]),
    "baby":  (P["mid"], "#4B6349", P["ivory"], P["spot"]),
    "babyb": (P["forest"], "#34503A", P["spot"], P["pale"]),
    "babyf": (P["sage"], "#6A7E60", P["ivory"], P["spot"]),
}


def smooth(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def half_w(s, W, w0):
    """Half-width along the strap (s 0..1): narrow sheath, long parallel
    blade, long gradual taper to a fine point."""
    if s < 0.14:
        return w0 + (W - w0) * smooth(s / 0.14)
    if s < 0.55:
        return W
    u = min(1.0, (s - 0.55) / 0.45)
    return W * max(0.0, 1 - u) ** 0.8


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u * u * u * p0[j] + 3 * u * u * t * p1[j] + 3 * u * t * t * p2[j] + t * t * t * p3[j]
                 for j in (0, 1))


class Strap:
    """Strap leaf along a cubic Bezier centreline base -> c1 -> c2 -> tip,
    resampled at n+1 equal arc-length stations (heading from vertical)."""

    def __init__(self, base, c1, c2, tip, W=11, w0=None, n=8):
        dense = [bez(base, c1, c2, tip, i / 200) for i in range(201)]
        acc = [0.0]
        for a, b in zip(dense, dense[1:]):
            acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        Ltot = acc[-1]
        self.pts, self.heads = [], []
        j = 0
        for i in range(n + 1):
            target = Ltot * i / n
            while j < 199 and acc[j + 1] < target:
                j += 1
            seg = acc[j + 1] - acc[j] or 1
            u = min(1.0, max(0.0, (target - acc[j]) / seg))
            a, b = dense[j], dense[j + 1]
            self.pts.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
            self.heads.append(math.atan2(b[0] - a[0], -(b[1] - a[1])))
        self.top = min(p[1] for p in dense)
        self.L = Ltot
        self.W = W
        self.w0 = W * 0.5 if w0 is None else w0
        # concave side: sign of the turning (cross product of start/end heading)
        d0 = (c1[0] - base[0], c1[1] - base[1])
        d1 = (tip[0] - c2[0], tip[1] - c2[1])
        cr = d0[0] * d1[1] - d0[1] * d1[0]
        self.sg = 1 if cr > 0 else -1

    @property
    def tip(self):
        return self.pts[-1]

    def off(self, k0, k1, stop=1.0):
        """Closed band between offsets k0*w and k1*w (fractions of half-width,
        +: right-hand normal).  Ends pointed at the tip."""
        m = len(self.pts)
        A, B = [], []
        for i, ((x, y), th) in enumerate(zip(self.pts, self.heads)):
            s = i / (m - 1)
            if s > stop + 1e-6:
                break
            w = half_w(s, self.W, self.w0)
            if s >= stop - 1e-6:
                w = 0.0
            nx, ny = math.cos(th), math.sin(th)
            A.append((x + nx * w * k0, y + ny * w * k0))
            B.append((x + nx * w * k1, y + ny * w * k1))
        tip = A.pop()
        B.pop()
        ring = A + [tip] + B[::-1]
        return cr_path(ring, closed=True, sharp={0, len(A), len(ring) - 1})

    def svg(self, tier, stripe=0.42, stop=0.9, stripe_shade=True):
        mc, ms, sc, ss = TIER[tier]
        g = self.sg
        out = (f'<path d="{self.off(-1, 1)}" fill="{mc}"/>'
               f'<path d="{self.off(0, g)}" fill="{ms}"/>'
               f'<path d="{self.off(-stripe, stripe, stop)}" fill="{sc}"/>')
        if stripe_shade:
            out += f'<path d="{self.off(0, g * stripe, stop)}" fill="{ss}"/>'
        return out


# (base dx, c1, c2, tip, half-width, tier) -- canvas coordinates.
# Draw order = list order inside each layer.
LEAVES = {
    "back": [
        (-4, (290, 360), (255, 105), (140, 262), 11, "back"),    # tall left
        (5, (314, 340), (372, 60), (482, 202), 11, "back"),      # tallest, right
        (-7, (268, 450), (160, 290), (52, 480), 11, "back"),     # wide left
        (7, (336, 460), (455, 330), (556, 500), 11, "back"),     # wide right
    ],
    "midd": [
        (0, (300, 430), (304, 300), (322, 262), 12, "midd"),      # young upright centre leaf
        (-3, (282, 440), (196, 250), (78, 380), 12, "midd"),
        (3, (324, 430), (425, 270), (520, 420), 12, "midd"),
        (-6, (262, 520), (130, 430), (62, 575), 12, "midd"),     # low left
        (6, (342, 515), (470, 440), (548, 588), 12, "midd"),     # low right
    ],
    "front": [
        (-3, (286, 480), (222, 360), (128, 500), 13, "front"),
        (-5, (270, 560), (158, 468), (148, 700), 12.5, "front"),   # sweeps down past rim
        (-2, (292, 500), (252, 400), (186, 452), 13, "fore"),
        (2, (312, 530), (372, 460), (420, 540), 12.5, "fore"),
    ],
    "drape": [   # drawn over the pot front; bases clipped by the rim
        (-3, (284, 540), (214, 484), (208, 730), 12.5, "top"),
        (4, (320, 575), (385, 540), (418, 690), 12, "front"),
    ],
}


WSCALE = 1.15   # global leaf-width scale (tuned against the rest of the set)


def make(spec):
    dx, c1, c2, tip, W, tier = spec
    return Strap((CROWN[0] + dx, CROWN[1]), c1, c2, tip, W * WSCALE), tier


def arc_leaf(base, a0, a1, L, W, n=5):
    """Small leaf by heading a0 -> a1 (deg from vertical) and length."""
    def d(a, k):
        r = math.radians(a)
        return (math.sin(r) * L * k, -math.cos(r) * L * k)
    am = (a0 + a1) / 2
    c1 = (base[0] + d(a0, 0.4)[0], base[1] + d(a0, 0.4)[1])
    c2 = (c1[0] + d(am, 0.35)[0], c1[1] + d(am, 0.35)[1])
    tip = (c2[0] + d(a1, 0.3)[0], c2[1] + d(a1, 0.3)[1])
    return Strap(base, c1, c2, tip, W, w0=W * 0.55, n=n)


def rim_hide_clip():
    """Clip for leaves drawn in front of the pot: hides the part of the leaf
    below the rim's front edge near the crown (so the bases still look like
    they come out of the soil) while letting the drape over the rim show."""
    cid = uid("rh")
    ry = RX * 0.15
    x0, x1 = CX - 62, CX + 62
    arc = []
    for i in range(9):
        x = x0 + (x1 - x0) * i / 8
        u = (x - CX) / RX
        arc.append(f"{f(x)} {f(RIM_Y + ry * math.sqrt(1 - u * u) + 1)}")
    # one simple contour: the canvas with a notch cut up to the rim's front edge
    d = f"M0 0H600V800H{f(x1)}L" + "L".join(arc[::-1]) + f"L{f(x0)} 800H0Z"
    return cid, f'<clipPath id="{cid}"><path d="{d}"/></clipPath>'


# ------------------------------------------------------------------ runners
RUN_COL = "#B3AF74"     # pale straw-green stolon, apart from every leaf green
RUN_SH = "#8F8C57"      # its shaded underside


def runner(pts, w0=6.2, w1=4.4):
    """Wiry stolon: a solid filled ribbon (not a hairline stroke) so it keeps
    ~0.2-0.3 mm on the printed card, with a darker underside strip so it still
    separates from the pale cream ground and from the leaves it crosses."""
    return (f'<path d="{ribbon(pts, w0, w1, per=8)}" fill="{RUN_SH}"/>'
            f'<path d="{ribbon([(x - 0.9, y - 0.9) for x, y in pts], w0 * 0.62, w1 * 0.55, per=8)}" fill="{RUN_COL}"/>')


def plantlet(x, y, spec, roots):
    """Small rosette: leaves radiating from (x,y); root nubs hanging below."""
    out = []
    for dx, rl in roots:
        out.append(f'<path d="{ribbon([(x, y - 2), (x + dx * 0.4, y + rl * 0.55), (x + dx, y + rl)], 3.0, 1.0, per=4)}" '
                   f'fill="{P["light"]}"/>')
    for a0, a1, L, W, tier in spec:
        out.append(arc_leaf((x, y + 3), a0, a1, L * 1.3, W * 1.35).svg(tier, 0.4, 0.86, stripe_shade=False))
    return "".join(out)


# ------------------------------------------------------------------ build
def build(report=False):
    back, front = pot("classic", cx=CX, rim_y=RIM_Y, rx=RX, base_w=70, band=False)
    layers = {}
    for k, specs in LEAVES.items():
        svgs = []
        for spec in specs:
            s, tier = make(spec)
            if report:
                print(k, spec[0], "top", round(s.top), "L", round(s.L))
            svgs.append(s.svg(tier))
        layers[k] = "".join(svgs)

    # runners: leave the crown at the rim, arch up and out, then hang
    LB = (104, 668)
    RB = (506, 640)
    runL = [(262, 614), (250, 586), (236, 556), (214, 526), (186, 504), (156, 496), (132, 506),
            (116, 530), (107, 564), (104, 604), (104, 640), LB]
    runR = [(338, 614), (350, 588), (368, 562), (396, 540), (430, 530), (462, 536), (484, 556),
            (498, 584), (504, 612), RB]
    babyL = plantlet(*LB, [
        (-52, -124, 46, 6.0, "babyb"), (50, 140, 42, 5.6, "babyb"),
        (-24, -100, 64, 6.6, "baby"), (18, 92, 58, 6.4, "baby"),
        (-14, -58, 60, 6.6, "babyf"), (-90, -164, 30, 5.0, "baby"),
        (86, 166, 32, 5.0, "baby")], [(-6, 22), (6, 18), (0, 30)])
    babyR = plantlet(*RB, [
        (-58, -136, 60, 5.6, "babyb"), (54, 142, 58, 5.6, "babyb"),
        (-18, -92, 70, 6.0, "baby"), (22, 88, 66, 6.0, "babyf"),
        (-88, -166, 42, 5.0, "baby"), (84, 166, 40, 5.0, "baby")],
        [(-5, 20), (6, 24)])

    cid, clip = rim_hide_clip()
    # the right runner leaves the crown behind all foliage and only shows
    # where it drops clear of the leaves; the left one arches over the back
    # leaves and under the middle ones.
    # both runners sit on the top layer, in front of every leaf; the same rim
    # clip hides their bases so they visibly rise out of the soil at the rim.
    body = [back, layers["back"], layers["midd"], layers["front"], front,
            clip, f'<g clip-path="url(#{cid})">{layers["drape"]}',
            runner(runL, 5.6, 4.0), runner(runR, 5.6, 4.0), "</g>",
            babyL, babyR]
    return "".join(body)


if __name__ == "__main__":
    reset_ids()
    rep = "-r" in sys.argv
    out = os.path.join(os.path.dirname(HERE), "out", "chlorophytum_comosum.svg")
    open(out, "w").write(svg_doc(build(rep), "Chlorophytum comosum (variegated spider plant)"))
    print("wrote", out, os.path.getsize(out))
