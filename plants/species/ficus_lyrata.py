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

# half-width profile of the violin-shaped blade (t along midrib, w as fraction of L)
PROFILE = [(0.00, 0.075), (0.06, 0.150), (0.16, 0.205), (0.28, 0.228), (0.40, 0.212),
           (0.52, 0.255), (0.64, 0.325), (0.76, 0.365), (0.86, 0.345), (0.935, 0.255),
           (0.985, 0.095)]
SINUS_T = 0.035
TIP_T = 0.972


class Fig:
    def __init__(self, base, rot, L, sx=1.0, sy=1.0, bend=0.0, seed=0, fat=1.0):
        self.bx, self.by = base
        self.rot = math.radians(rot)
        self.L, self.sx, self.sy, self.bend = L, sx, sy, bend
        rnd = random.Random(seed)
        waist = rnd.uniform(0.86, 1.04)   # how pinched the "fiddle" waist is
        crown = rnd.uniform(0.94, 1.08)   # breadth of the rounded upper blade
        self.prof = {}
        for side in ("r", "l"):
            asym = rnd.uniform(-0.025, 0.025)
            pr = []
            for i, (t, w) in enumerate(PROFILE):
                wig = rnd.uniform(-0.016, 0.016) if 2 <= i <= 9 else 0
                k = waist if 0.3 <= t <= 0.5 else (crown if t >= 0.6 else 1.0)
                pr.append((t, (w * k + wig + (asym if t > 0.45 else 0)) * fat))
            self.prof[side] = pr

    # local unit coords -> page
    def M(self, x, y):
        x, y = x * self.L * self.sx, y * self.L * self.sy
        c, s = math.cos(self.rot), math.sin(self.rot)
        return (self.bx + x * c - y * s, self.by + x * s + y * c)

    def ax(self, t):  # midrib, local unit coords (tip toward -y)
        return (self.bend * t * t, -t)

    def nrm(self, t):
        tx, ty = 2 * self.bend * t, -1
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

    def veins(self, ts, reach=0.82, dt=0.13):
        d = []
        for t in ts:
            for side, sg in (("r", 1), ("l", -1)):
                t2 = min(t + dt, 0.95)
                p0 = self.M(*self.ax(t))
                p1 = self.M(*self.lp(t + dt * 0.35, sg * self.wid(t + dt * 0.35, side) * reach * 0.62))
                p2 = self.M(*self.lp(t2, sg * self.wid(t2, side) * reach))
                d.append(f"M{f(p0[0])} {f(p0[1])}Q{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])}")
        return "".join(d)

    def rib_shape(self, w):
        ts = [-0.03, 0.3, 0.6, 0.9]
        ws = [w / 2, w * 0.36, w * 0.24, 0.35]
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

    def svg(self, fill, vein_col=None, vein_op=0.42, rib_op=0.8, rib_w=3.2, under=False):
        d = self.path()
        cid = uid("fl")
        shade = SHADE.get(fill, fill)
        sg = 1 if self.right_is_away() else -1
        vc = vein_col or P["pale"]
        o = [f'<clipPath id="{cid}"><path d="{d}"/></clipPath>',
             f'<path d="{d}" fill="{fill}"/>',
             f'<g clip-path="url(#{cid})">',
             f'<path d="{self.half(sg)}" fill="{shade}"/>',
             f'<path d="{self.veins([0.15, 0.30, 0.45, 0.59, 0.72])}" fill="none" stroke="{vc}" '
             f'stroke-width="1.4" stroke-linecap="round" opacity="{vein_op}"/>',
             f'<path d="{self.rib_shape(rib_w)}" fill="{vc}" opacity="{rib_op}"/>',
             "</g>"]
        return "".join(o)


def petiole(stem_pt, fig, length_in=0.06, w0=5.0, w1=3.6, col=BARK):
    """From a point inside the stem to just inside the leaf base (hidden by blade)."""
    end = fig.M(*fig.ax(length_in))
    base = (fig.bx, fig.by)
    mid = ((stem_pt[0] * 0.45 + base[0] * 0.55), (stem_pt[1] * 0.45 + base[1] * 0.55))
    return f'<path d="{ribbon([stem_pt, mid, base, end], w0, w1, per=2)}" fill="{col}"/>'


def offset(p, rot, dist):
    r = math.radians(rot)
    return (p[0] + math.sin(r) * dist, p[1] - math.cos(r) * dist)


# ------------------------------------------------------------------ scene
TRUNK = [(297, 600), (295, 540), (298, 475), (304, 410), (306, 340), (301, 270), (296, 205),
         (297, 160)]
BRANCH = [(304, 425), (292, 400), (276, 374), (259, 352), (246, 338)]


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
# layer 0 = behind the trunk, 1 = in front of trunk
LEAVES = [
    # ---- back crown (darkest), behind the trunk
    (0, "T", 0.80, -58, 7, 155, 0.95, 1.0, -0.05, "deep", 3),
    (0, "T", 0.78, 66, 7, 160, 0.92, 1.0, 0.06, "deep", 4),
    (0, "T", 0.95, -18, 6, 135, 0.92, 0.95, -0.03, "forest", 5),
    (0, "T", 0.93, 36, 6, 130, 0.88, 1.0, 0.03, "forest", 6),
    (0, "B", 1.00, -80, 6, 140, 0.95, 1.0, -0.08, "forest", 7),
    (0, "T", 0.62, 112, 7, 135, 0.9, 1.0, 0.10, "deep", 15),
    (0, "B", 0.70, -122, 6, 125, 0.9, 1.0, 0.08, "deep", 17),
    # ---- middle
    (1, "T", 0.99, 10, 5, 115, 0.95, 0.95, 0.03, "light", 8),    # newest top leaf
    (1, "T", 0.78, 38, 7, 150, 0.8, 1.0, -0.05, "mid", 12),
    (1, "T", 0.82, -30, 7, 150, 1.0, 0.9, 0.03, "sage", 11),
    (1, "T", 0.68, 78, 8, 140, 0.56, 1.0, 0.16, "mid", 9),       # right, turned
    (1, "B", 0.85, -106, 7, 132, 0.7, 1.0, 0.12, "sage", 10),    # left, from branch
    # ---- front
    (1, "T", 0.57, -4, 7, 158, 1.0, 0.74, 0.02, "light", 13),   # facing viewer, foreshortened
    (1, "T", 0.60, 138, 7, 112, 0.8, 0.9, -0.06, "sage", 14),   # drooping toward viewer
]


def build():
    reset_ids()
    back, front = pot(kind="classic", rx=96, rim_y=588, base_w=66, band=True)
    out = [back]
    stems = {"T": TRUNK, "B": BRANCH}
    layers = {0: [], 1: []}
    for (lay, st, fr, rot, pl, L, sx, sy, bend, tone, seed) in LEAVES:
        sp = on(stems[st], fr)
        base = offset(sp, rot, pl)
        fig = Fig(base, rot, L, sx, sy, bend, seed)
        dark = tone in ("deep", "forest")
        vein = P["light"] if dark else P["ivory"]
        pw = 5.5 if L > 150 else 4.6
        s = petiole(sp, fig, w0=pw, w1=pw * 0.7)
        s += fig.svg(P[tone], vein_col=vein, vein_op=0.3 if dark else 0.38,
                     rib_op=0.6 if dark else 0.72)
        if os.environ.get("DBG"):
            c = fig.M(0, -0.5)
            s += f'<text x="{f(c[0])}" y="{f(c[1])}" font-size="22" fill="red">{len(layers[0]) + len(layers[1])}</text>'
        layers[lay].append(s)

    out += layers[0]
    # trunk + branch
    out.append(f'<path d="{ribbon(BRANCH, 8, 4.5)}" fill="{BARK}"/>')
    out.append(f'<path d="{ribbon(TRUNK, 15, 6)}" fill="{BARK}"/>')
    # bark shading: darker right edge, faint highlight left, small leaf scars
    tid = uid("tk")
    out.append(f'<clipPath id="{tid}"><path d="{ribbon(TRUNK, 15, 6)}"/></clipPath>'
               f'<g clip-path="url(#{tid})">'
               f'<path d="{ribbon([(p[0] + 5, p[1]) for p in TRUNK], 9, 3)}" fill="{BARK_DK}" opacity=".55"/>'
               f'<path d="{cr_path([(p[0] - 3.2, p[1]) for p in TRUNK[:5]], closed=False)}" fill="none" '
               f'stroke="{BARK_HI}" stroke-width="2" stroke-linecap="round" opacity=".7"/>'
               + "".join(f'<path d="M{f(x - 4)} {f(y)} q4 -2.5 8 0" fill="none" stroke="{BARK_DK}" '
                         f'stroke-width="1.6" stroke-linecap="round" opacity=".8"/>'
                         for x, y in [(on(TRUNK, 0.12)[0], on(TRUNK, 0.12)[1]),
                                      (on(TRUNK, 0.25)[0], on(TRUNK, 0.25)[1]),
                                      (on(TRUNK, 0.37)[0], on(TRUNK, 0.37)[1])])
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
