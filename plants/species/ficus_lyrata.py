"""Ficus lyrata (fiddle-leaf fig) as a small standard tree -- v4.

Own leaf renderer: leaf geometry is built in unit-length local coords and
mapped (foreshorten -> rotate -> translate) into page coords, so vein stroke
widths stay constant even on foreshortened leaves.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core import PAL, SHADE, cr_path, cr_sample, ribbon, uid, reset_ids, f, pot, svg_doc  # noqa

P = PAL
BARK = "#6A5943"
BARK_DK = P["soil"]
BARK_HI = "#8A7659"


def mix(a, b, t):
    """Opaque pre-blend of hex colours a -> b (t = 0..1)."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


VEIN_W = 4.8     # light-on-dark lateral veins at their base (tapered ribbons, print-safe widest point)
VEIN_TS = [0.14, 0.31, 0.48, 0.65]   # four sub-opposite pairs of laterals

# half-width profile of the violin-shaped blade (t along midrib, w as fraction of L)
# Few, evenly spread nodes -> smooth margin: narrow base, one gentle waist (~0.42),
# broadest at ~0.8, broad rounded apex with only a tiny point.
PROFILE = [(0.00, 0.045), (0.11, 0.125), (0.26, 0.180), (0.41, 0.176), (0.58, 0.262),
           (0.77, 0.345), (0.905, 0.312), (0.972, 0.165)]
SINUS_T = 0.035
TIP_T = 0.995


class Fig:
    def __init__(self, base, rot, L, sx=1.0, sy=1.0, bend=0.0, seed=0, fat=1.0, sway=0.0):
        self.sway = sway
        self.bx, self.by = base
        self.rot = math.radians(rot)
        self.L, self.sx, self.sy, self.bend = L, sx, sy, bend
        rnd = random.Random(seed)
        waist = rnd.uniform(0.94, 1.0)    # how pinched the "fiddle" waist is
        crown = rnd.uniform(0.96, 1.04)   # breadth of the rounded upper blade
        self.prof = {}
        for side in ("r", "l"):
            asym = rnd.uniform(-0.014, 0.014)
            pr = []
            for i, (t, w) in enumerate(PROFILE):
                wig = 0  # (random margin wiggle removed: it made the blades lumpy)
                k = waist if 0.35 <= t <= 0.45 else (crown if t >= 0.6 else 1.0)
                pr.append((t, (w * k + wig + (asym if t > 0.45 else 0)) * fat))
            self.prof[side] = pr

    # local unit coords -> page
    def M(self, x, y):
        x, y = x * self.L * self.sx, y * self.L * self.sy
        c, s = math.cos(self.rot), math.sin(self.rot)
        return (self.bx + x * c - y * s, self.by + x * s + y * c)

    def ax(self, t):  # midrib, local unit coords (tip toward -y); bend = C, sway = S
        return (self.bend * t * t + self.sway * t * (1 - t) * (1 - 2 * t), -t)

    def nrm(self, t):
        tx, ty = 2 * self.bend * t + self.sway * (1 - 6 * t + 6 * t * t), -1
        m = math.hypot(tx, ty)
        return (-ty / m, tx / m)

    def lp(self, t, w):
        a, n = self.ax(t), self.nrm(t)
        return (a[0] + n[0] * w, a[1] + n[1] * w)

    def wid(self, t, side):
        pr = self.prof[side]
        if t <= pr[0][0]:
            return pr[0][1]
        for (t0, w0), (t1, w1) in zip(pr, pr[1:]):
            if t0 <= t <= t1:
                return w0 + (w1 - w0) * (t - t0) / (t1 - t0)
        return 0.0

    def outline(self):
        R = [self.lp(t, w) for t, w in self.prof["r"]]
        Lf = [self.lp(t, -w) for t, w in self.prof["l"]]
        pts = [self.ax(SINUS_T)] + R + [self.ax(TIP_T)] + Lf[::-1]
        sharp = {0, len(R) + 1}
        return [self.M(*p) for p in pts], sharp

    def path(self):
        pts, sharp = self.outline()
        return cr_path(pts, closed=True, sharp=sharp)

    def half(self, sg):
        ts = [-0.2, 0.1, 0.3, 0.5, 0.7, 0.9, 1.2]
        pts = [self.M(*self.ax(t)) for t in ts]
        pts += [self.M(*self.lp(1.2, sg * 1.0)), self.M(*self.lp(-0.2, sg * 1.0))]
        return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"

    def right_is_away(self):
        # light from upper left: the half whose outward normal points right/down is shaded
        a = self.M(0, -0.5)
        b = self.M(0.3, -0.5)
        return (b[0] - a[0]) + 0.35 * (b[1] - a[1]) > 0

    def veins(self, ts, reach=0.8, dt=0.17, w0=4.8, w1=1.8, stagger=0.035):
        """Lateral veins as tapered ribbons (page coords, so widths are print-true).
        Each one leaves the midrib at ~60 deg, then bends gently toward the apex
        and thins out before the margin. Left/right are sub-opposite (staggered)
        so a pair never joins into one arc across the midrib."""
        d = []
        for t in ts:
            for side, sg in (("r", 1), ("l", -1)):
                t0 = t + (stagger if side == "l" else 0.0)
                t2 = min(t0 + dt, 0.93)
                ex = sg * self.wid(t2, side) * reach
                p0 = self.ax(t0)
                # control: most of the lateral run happens early (steep take-off),
                # the last stretch turns up toward the tip
                c = self.lp(t0 + (t2 - t0) * 0.42, ex * 0.72)
                p2 = self.lp(t2, ex)
                d.append(taper(self.M(*p0), self.M(*c), self.M(*p2), w0, w1))
        return "".join(d)

    def rib_shape(self, w):
        ts = [-0.03, 0.3, 0.6, 0.9]
        ws = [w / 2, w * 0.45, w * 0.38, w * 0.3]
        R, Lf = [], []
        for t, hw in zip(ts, ws):
            a, n = self.M(*self.ax(t)), self.M(*self.lp(t, 1)),
            c = self.M(*self.ax(t))
            dx, dy = n[0] - c[0], n[1] - c[1]
            m = math.hypot(dx, dy) or 1
            R.append((c[0] + dx / m * hw, c[1] + dy / m * hw))
            Lf.append((c[0] - dx / m * hw, c[1] - dy / m * hw))
        ring = R + Lf[::-1]
        return cr_path(ring, closed=True, sharp={0, len(R) - 1, len(R), len(ring) - 1})

    def midrib(self, t0=-0.02, t1=0.88):
        pts = [self.M(*self.ax(t0 + (t1 - t0) * i / 6)) for i in range(7)]
        return pts

    def svg(self, fill, vein_col, rib_col, rib_w=6.0):
        """Every leaf carries the same bold, opaque vein system: a tapered
        midrib + three pairs of pale laterals (the fiddle-leaf pattern), all
        at print-safe weight."""
        d = self.path()
        cid = uid("fl")
        shade = SHADE.get(fill, fill)
        sg = 1 if self.right_is_away() else -1
        o = [f'<clipPath id="{cid}"><path d="{d}"/></clipPath>',
             f'<path d="{d}" fill="{fill}"/>',
             f'<g clip-path="url(#{cid})">',
             f'<path d="{self.half(sg)}" fill="{shade}"/>',
             f'<path d="{self.veins(VEIN_TS)}" fill="{vein_col}"/>',
             f'<path d="{self.rib_shape(rib_w)}" fill="{rib_col}"/>',
             "</g>"]
        return "".join(o)


def taper(p0, c, p2, w0, w1):
    """Compact tapered vein: a quadratic (p0, control c, p2) widened w0 -> w1,
    written as two offset quadratics (keeps the file small)."""
    def nrm(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        return (-dy / m, dx / m)
    n0, n2, nc = nrm(p0, c), nrm(c, p2), nrm(p0, p2)
    wc = (w0 + w1) / 4
    A = [(p0[0] + n0[0] * w0 / 2, p0[1] + n0[1] * w0 / 2), (c[0] + nc[0] * wc, c[1] + nc[1] * wc),
         (p2[0] + n2[0] * w1 / 2, p2[1] + n2[1] * w1 / 2)]
    B = [(p0[0] - n0[0] * w0 / 2, p0[1] - n0[1] * w0 / 2), (c[0] - nc[0] * wc, c[1] - nc[1] * wc),
         (p2[0] - n2[0] * w1 / 2, p2[1] - n2[1] * w1 / 2)]
    q = lambda P: f"{f(P[0])} {f(P[1])}"
    return f"M{q(A[0])}Q{q(A[1])} {q(A[2])}L{q(B[2])}Q{q(B[1])} {q(B[0])}Z"


def petiole(stem_pt, fig, rot0, length_in=0.06, w0=5.0, w1=3.6, col=BARK):
    """From a point inside the stem to just inside the leaf base (hidden by blade).
    Leaves the stem at rot0 (steeper, closer to the stem's own direction) and arcs
    round to meet the blade along its midrib."""
    end = fig.M(*fig.ax(length_in))
    base = (fig.bx, fig.by)
    ln = math.hypot(base[0] - stem_pt[0], base[1] - stem_pt[1])
    d0 = offset((0, 0), rot0, 1)
    d1 = (end[0] - base[0], end[1] - base[1])
    m = math.hypot(*d1) or 1
    d1 = (d1[0] / m, d1[1] / m)
    c1 = (stem_pt[0] + d0[0] * ln * 0.5, stem_pt[1] + d0[1] * ln * 0.5)
    c2 = (base[0] - d1[0] * ln * 0.35, base[1] - d1[1] * ln * 0.35)
    pts = []
    for i in range(5):
        t = i / 4
        u = 1 - t
        pts.append(tuple(u ** 3 * stem_pt[j] + 3 * u * u * t * c1[j] + 3 * u * t * t * c2[j] + t ** 3 * base[j] for j in (0, 1)))
    return f'<path d="{ribbon(pts + [end], w0, w1, per=3)}" fill="{col}"/>'


def offset(p, rot, dist):
    r = math.radians(rot)
    return (p[0] + math.sin(r) * dist, p[1] - math.cos(r) * dist)


# ------------------------------------------------------------------ scene
TRUNK = [(293, 600), (298, 540), (308, 478), (319, 412), (323, 342), (317, 272), (305, 208),
         (297, 164)]   # slight lean right, then the crown swings back over the pot: a gentle S
BRANCH = [(317, 448), (298, 427), (274, 412), (252, 404), (233, 396), (218, 382)]   # sweeps out, tip turns up


def on(pts, fr):
    """Point at arc-length fraction along a CR spline."""
    s = cr_sample(pts, 12)
    acc = [0.0]
    for a, b in zip(s, s[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tgt = fr * acc[-1]
    for i in range(1, len(acc)):
        if acc[i] >= tgt:
            u = (tgt - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
            a, b = s[i - 1], s[i]
            return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
    return s[-1]


# leaf spec: (layer, stem, frac, rot, petiole_len, L, sx, sy, bend, fill, seed)
# layer 0 = behind the trunk, 1 = in front of trunk.
# Depth logic: a dark back ring (deep) gives the silhouette; a few mid-tone
# leaves sit between; the three pale front leaves only ever overlap deep
# leaves (never each other or the mid tones), so every overlap is >= 2 tone
# steps and the crown reads as layers even at thumbnail size.
# (layer, stem, frac, rot, petiole_len, L, sx, sy, bend, fill, seed, sway)
# bend sign = droop: tips fall toward the ground (positive for right-hand leaves).
LEAVES = [
    # ---- back ring (darkest), behind the trunk
    (0, "T", 0.60, -106, 10, 150, 0.92, 1.0, -0.11, "deep", 3, 0.03),    # left, lower and drooping
    (0, "T", 0.79, 82, 10, 138, 0.90, 1.0, 0.09, "deep", 4, -0.03),      # right, higher and smaller
    (0, "T", 0.95, -26, 8, 132, 0.90, 1.0, -0.06, "deep", 5, 0.04),      # upper left
    (0, "T", 0.92, 36, 8, 136, 0.86, 1.0, 0.07, "deep", 6, 0.0),         # upper right
    (0, "T", 0.55, 126, 12, 126, 0.84, 1.0, 0.12, "deep", 15, 0.04),     # low right, hanging
    (0, "B", 0.70, -140, 14, 116, 0.86, 1.0, -0.07, "forest", 17, 0.0),    # branch, hanging (visible petiole)
    # ---- middle tones
    (1, "T", 1.00, 4, 5, 116, 0.90, 0.95, -0.04, "mid", 8, 0.05),        # newest top leaf
    (1, "B", 1.00, -48, 7, 128, 0.84, 1.0, -0.08, "mid", 10, -0.03),     # branch terminal leaf
    # ---- front (lightest)
    (1, "T", 0.82, -62, 8, 132, 0.95, 0.95, -0.06, "sage", 11, 0.04),    # upper left, facing
    (1, "T", 0.88, 64, 8, 134, 0.62, 1.0, 0.16, "sage", 9, 0.0),         # right, turned edge-on
    (1, "T", 0.52, 14, 7, 150, 1.0, 0.74, 0.05, "light", 13, -0.04),     # tip tipping toward the viewer
]


def build():
    reset_ids()
    back, front = pot(kind="classic", rx=99, rim_y=588, base_w=68, band=True)
    out = [back]
    stems = {"T": TRUNK, "B": BRANCH}
    layers = {0: [], 1: []}
    for (lay, st, fr, rot, pl, L, sx, sy, bend, tone, seed, sway) in LEAVES:
        sp = on(stems[st], fr)
        rot0 = rot * 0.6       # petiole leaves the stem steeper than the blade hangs
        base = offset(sp, (rot0 + rot) / 2, pl)
        fig = Fig(base, rot, L, sx, sy, bend, seed, sway=sway)
        dark = tone in ("deep", "forest")
        # opaque pre-blended vein tones: pale tint of the blade colour
        # (kept ~25 % below the silhouette contrast so vein detail reads as detail)
        vein = mix(P[tone], P["light"] if dark else P["ivory"], 0.17 if dark else 0.25)
        rib = mix(P[tone], P["light"] if dark else P["ivory"], 0.3 if dark else 0.45)
        pw = 5.5 if L > 150 else 4.6
        s = petiole(sp, fig, rot0, w0=pw, w1=pw * 0.7)
        s += fig.svg(P[tone], vein, rib)
        if os.environ.get("DBG"):
            c = fig.M(0, -0.5)
            s += f'<text x="{f(c[0])}" y="{f(c[1])}" font-size="22" fill="red">{len(layers[0]) + len(layers[1])}</text>'
        layers[lay].append(s)

    out += layers[0]
    # trunk + branch
    out.append(f'<path d="{ribbon(BRANCH, 8, 4.5)}" fill="{BARK}"/>')
    out.append(f'<path d="{ribbon(TRUNK, 15, 6)}" fill="{BARK}"/>')
    # bark shading: darker right edge (opaque pre-blend) + a print-safe
    # highlight rising from the soil and tapering out into the branch fork; hairline scars dropped
    tid = uid("tk")
    out.append(f'<clipPath id="{tid}"><path d="{ribbon(TRUNK, 15, 6)}"/></clipPath>'
               f'<g clip-path="url(#{tid})">'
               f'<path d="{ribbon([(p[0] + 5, p[1]) for p in TRUNK], 9, 3)}" fill="{mix(BARK, BARK_DK, 0.55)}"/>'
               f'<path d="{ribbon([(p[0] - 3.4, p[1]) for p in TRUNK[:3]] + [(lambda q: (q[0] - 2.4, q[1]))(on(TRUNK, fr)) for fr in (0.38, 0.42)], 4.6, 0.6, per=4)}" fill="{BARK_HI}"/>'
               + "</g>")
    out += layers[1]
    out.append(front)
    return "".join(out)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "..", "out", "ficus_lyrata.svg")
    with open(dst, "w") as fh:
        fh.write(svg_doc(build(), "Ficus lyrata (fiddle-leaf fig)"))
    print(dst, os.path.getsize(dst))
