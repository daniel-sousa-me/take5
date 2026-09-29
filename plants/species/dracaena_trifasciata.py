"""Dracaena trifasciata 'Laurentii' (snake plant) — v4.

Stiff upright sword leaves in a tight basal fan. Each leaf = yellow margin
shape (outer outline) + inset green body; the zigzag cross-banding and a
faint concave-half shade are clipped to the green body so the yellow margin
stays clean on both edges.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import PAL, SHADE, cr_path, f, uid, pot, svg_doc, reset_ids  # noqa: E402

P = PAL
CX = 300
RIM_Y = 574
BASE_Y = RIM_Y + 16          # where leaves meet the soil (hidden by the rim front)

# width profile (t along leaf 0=base 1=tip, fraction of max half-width)
PROFILE = [(0.0, 0.34), (0.10, 0.58), (0.26, 0.86), (0.44, 1.0), (0.60, 0.96),
           (0.74, 0.80), (0.86, 0.52), (0.94, 0.24), (1.0, 0.0)]

# the yellow margin steps down in value with depth so overlapping margins
# never merge into one yellow blob (same hue family as PAL yellow_edge)
MARGIN_BACK = "#9F924A"
MARGIN_MID = "#B0A050"

TONES = {
    # body, dark band, light band, margin
    "back":  (P["deep"], P["night"], P["forest"], MARGIN_BACK),
    "midd":  (P["forest"], P["deep"], P["mid"], MARGIN_MID),
    "front": (P["mid"], P["forest"], P["sage"], P["yellow_edge"]),
    "fore":  (P["sage"], P["mid"], P["light"], P["yellow_edge"]),
}


def prof(t):
    for (t0, w0), (t1, w1) in zip(PROFILE, PROFILE[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u)  # smooth
            return w0 + (w1 - w0) * u
    return 0.0


class Sword:
    def __init__(self, x, lean, H, W, tone, bend=0.0, twist=0.0, seed=1, asym=0.0):
        self.x, self.lean, self.H, self.W = x, lean, H, W
        self.tone, self.bend, self.twist, self.seed, self.asym = tone, bend, twist, seed, asym

    # local coords: base (0,0), tip (bend*H, -H); later rotated by lean about base
    def axis(self, t):
        return (self.bend * self.H * t * t, -self.H * t)

    def normal(self, t):
        tx, ty = 2 * self.bend * self.H * t, -self.H
        m = math.hypot(tx, ty)
        return (-ty / m, tx / m)

    def hw(self, t, side):
        w = self.W * prof(t)
        # slight asymmetry: one side a touch fuller
        return w * (1 + side * self.asym * math.sin(math.pi * t))

    def pt(self, t, off):
        a, n = self.axis(t), self.normal(t)
        return (a[0] + n[0] * off, a[1] + n[1] * off)

    def outline(self, inset=0.0, extend=26):
        ts = [0.0, 0.05, 0.12, 0.22, 0.34, 0.46, 0.58, 0.70, 0.80, 0.88, 0.94]
        R, L = [], []
        for t in ts:
            wr = self.hw(t, 1) - inset
            wl = self.hw(t, -1) - inset
            if wr <= 0.6 or wl <= 0.6:
                continue
            R.append(self.pt(t, wr))
            L.append(self.pt(t, -wl))
        # tip: where inset width runs out
        tip_t = 1.0
        if inset:
            tt = 1.0
            while tt > 0.5 and min(self.hw(tt, 1), self.hw(tt, -1)) < inset * 1.15:
                tt -= 0.004
            tip_t = tt + 0.012
        tip = self.axis(tip_t)
        # extend the base straight down into the soil so the rim hides the end
        b0r = (R[0][0], R[0][1] + extend)
        b0l = (L[0][0], L[0][1] + extend)
        pts = [b0l, b0r] + R + [tip] + L[::-1]
        sharp = {0, 1, len(R) + 2}
        return cr_path(pts, closed=True, sharp=sharp)

    def bands(self, inset):
        """Non-overlapping cross-band strips between successive wavy lines.
        Strips cycle body / light / body / dark with irregular widths.
        Lines are clamped so they never cross (no self-intersecting strips)."""
        rnd = random.Random(self.seed)
        wmax = self.W * 1.35 + 8
        n = 5
        lines = []
        t = -4 / self.H
        prev = None
        while t < 0.975:
            amp = rnd.uniform(2.0, 4.6)
            chev = rnd.uniform(-4.5, 3.5)
            ph = rnd.randint(0, 1)
            row = []
            for i in range(n + 1):
                u = i / n
                z = amp * (1 if (i + ph) % 2 else -1) * rnd.uniform(0.5, 1.15)
                c = chev * (1 - (2 * u - 1) ** 2)
                tt = t + (z + c) / self.H
                if prev is not None:
                    tt = max(tt, prev[i] + 2.2 / self.H)
                row.append(tt)
            lines.append(row)
            prev = row
            t += rnd.uniform(7, 15) / self.H
        offs = [-wmax + 2 * wmax * i / n for i in range(n + 1)]

        def smooth(pts, first):
            # quadratic spline through midpoints (ends pinned)
            d = [f"{'M' if first else 'L'}{f(pts[0][0])} {f(pts[0][1])}"]
            for i in range(1, len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                e = b if i == len(pts) - 2 else ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                d.append(f"Q{f(a[0])} {f(a[1])} {f(e[0])} {f(e[1])}")
            return "".join(d)

        light, dark = [], []
        cyc = ["b", "l", "b", "d", "b", "d", "b", "l", "d"]
        k = rnd.randint(0, 4)
        for a, b in zip(lines, lines[1:]):
            kind = cyc[k % len(cyc)]
            k += 1
            if kind == "b":
                continue
            pa = [self.pt(tt, o) for tt, o in zip(a, offs)]
            pb = [self.pt(tt, o) for tt, o in zip(b, offs)][::-1]
            d = smooth(pa, True) + smooth(pb, False) + "Z"
            (light if kind == "l" else dark).append(d)
        return "".join(dark), "".join(light)

    def svg(self):
        body, dark, light, margin = TONES[self.tone]
        m = 4.4
        outer = self.outline(0)
        inner = self.outline(m)
        cid = uid("dt")
        bd, bl = self.bands(m)
        # concave shade: one half of the body a step darker (leaf is slightly channelled)
        side = 1 if self.lean > 0 else -1
        half = []
        for i in range(0, 21):
            t = -0.2 + i * 0.06
            half.append(self.pt(t, 0))
        far = [self.pt(-0.2 + i * 0.06, side * 80) for i in range(20, -1, -1)]
        hp = "M" + "L".join(f"{f(p[0])} {f(p[1])}" for p in half + far) + "Z"
        tr = f"translate({f(self.x)} {f(BASE_Y)}) rotate({f(self.lean)})"
        shade = SHADE.get(body, body)
        s = [f'<g transform="{tr}">',
             f'<path d="{outer}" fill="{margin}"/>',
             f'<clipPath id="{cid}"><path d="{inner}"/></clipPath>',
             f'<g clip-path="url(#{cid})">',
             f'<rect x="-70" y="{f(-self.H - 10)}" width="140" height="{f(self.H + 50)}" fill="{body}"/>',
             f'<path d="{bl}" fill="{light}"/>',
             f'<path d="{bd}" fill="{dark}"/>',
             f'<path d="{hp}" fill="{P["night"]}" opacity=".16"/>',
             '</g>']
        # (the tiny dry tip point was removed: at ~0.1 mm printed it is below the dark-sliver minimum)
        s.append("</g>")
        return "".join(s)


# draw order = list order (back -> front)
LEAVES = [
    # bases staggered so neighbouring yellow margins at the rim are either well
    # apart (>= ~10 units of green between them) or tucked decisively under the
    # leaf in front -- no parallel double lines with dark slivers
    Sword(322, 16, 360, 25, "back", bend=0.04, seed=11, asym=0.05),
    Sword(282, -9, 395, 27, "back", bend=-0.03, seed=12, asym=-0.05),
    Sword(269, -18, 300, 24, "midd", bend=-0.07, seed=13),
    Sword(333, 25, 238, 23, "midd", bend=0.05, seed=14),
    Sword(304, -1, 470, 30, "midd", bend=-0.015, seed=15, asym=0.06),
    Sword(315, 10, 412, 15, "front", bend=-0.02, seed=16),
    Sword(256, -42, 168, 22, "front", bend=-0.06, seed=17),
    Sword(286, -5, 222, 25, "fore", bend=-0.03, seed=18),
    Sword(319, 13.5, 196, 23, "front", bend=0.05, seed=19),
]


def build():
    reset_ids()
    back, front = pot(kind="cylinder", cx=CX, rim_y=RIM_Y, bottom=752, rx=94, rim_h=30,
                      base_w=80, band=True)
    plant = "".join(l.svg() for l in LEAVES)
    return back + plant + front


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "dracaena_trifasciata.svg")
    with open(out, "w") as fh:
        fh.write(svg_doc(build(), "Snake plant (Dracaena trifasciata 'Laurentii')"))
    print(out, os.path.getsize(out))
