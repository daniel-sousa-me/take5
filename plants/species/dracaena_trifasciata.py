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
    def __init__(self, x, lean, H, W, tone, bend=0.0, twist=0.0, seed=1, asym=0.0, fade=None,
                 sway=0.0, twist_t=0.62):
        self.x, self.lean, self.H, self.W, self.fade = x, lean, H, W, fade
        self.tone, self.bend, self.twist, self.seed, self.asym = tone, bend, twist, seed, asym
        self.sway, self.twist_t = sway, twist_t

    # local coords: base (0,0), tip (bend*H, -H); later rotated by lean about base.
    # sway adds a faint S to the blade (base and tip leaning opposite ways)
    def axis(self, t):
        x = self.bend * self.H * t * t + self.sway * self.H * t * (1 - t) * (1 - 2 * t)
        return (x, -self.H * t)

    def normal(self, t):
        tx = 2 * self.bend * self.H * t + self.sway * self.H * (1 - 6 * t + 6 * t * t)
        ty = -self.H
        m = math.hypot(tx, ty)
        return (-ty / m, tx / m)

    def hw(self, t, side):
        w = self.W * prof(t)
        if self.twist:
            # a gentle quarter-turn of the blade: it narrows where it turns edge-on
            w *= 1 - self.twist * math.exp(-((t - self.twist_t) / 0.13) ** 2)
        # slight asymmetry: one side a touch fuller
        return w * (1 + side * self.asym * math.sin(math.pi * t))

    def pt(self, t, off):
        a, n = self.axis(t), self.normal(t)
        return (a[0] + n[0] * off, a[1] + n[1] * off)

    def outline(self, inset=0.0, extend=26, fade=None):
        """fade=(s0, s1): the inset (yellow margin) is 0 up to s0 units above the base and grows
        smoothly to full width by s1, so the margin tapers out just above the rim."""
        ts = [0.0, 0.05, 0.12, 0.22, 0.34, 0.46, 0.58, 0.70, 0.80, 0.88, 0.94]
        if fade:
            ts = sorted(set(ts + [fade[0] / self.H, (fade[0] + fade[1]) / 2 / self.H, fade[1] / self.H]))

        def ins(t):
            if not fade:
                return inset
            u = min(1.0, max(0.0, (t * self.H - fade[0]) / (fade[1] - fade[0])))
            return inset * u * u * (3 - 2 * u)
        R, L = [], []
        for t in ts:
            if fade and ins(t) < 0.3:
                wr, wl = self.hw(t, 1) + 0.6, self.hw(t, -1) + 0.6   # a hair proud: no margin fringe
            else:
                wr = self.hw(t, 1) - ins(t)
                wl = self.hw(t, -1) - ins(t)
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
        inner = self.outline(m, fade=self.fade)
        cid, hid, lid, did = uid("dt"), uid("dh"), uid("dl"), uid("dd")
        bd, bl = self.bands(m)
        # concave shade: one half of the body a step darker (leaf is slightly channelled)
        side = 1 if self.lean > 0 else -1
        def half_poly(t0, t1, sg):
            ts = [t0 + (t1 - t0) * i / 20 for i in range(21)]
            pts = [self.pt(t, 0) for t in ts] + [self.pt(t, sg * 80) for t in ts[::-1]]
            return "M" + "L".join(f"{f(p[0])} {f(p[1])}" for p in pts) + "Z"
        if self.twist >= 0.3:
            # a visibly twisting blade: the channelled (shaded) half swaps sides where
            # the blade turns edge-on
            hp = half_poly(-0.2, self.twist_t, side) + half_poly(self.twist_t, 1.2, -side)
        else:
            hp = half_poly(-0.2, 1.0, side)
        tr = f"translate({f(self.x)} {f(BASE_Y)}) rotate({f(self.lean)})"
        shade = SHADE.get(body, body)
        s = [f'<g transform="{tr}">',
             f'<path d="{outer}" fill="{margin}"/>',
             f'<clipPath id="{cid}"><path d="{inner}"/></clipPath>',
             f'<g clip-path="url(#{cid})">',
             f'<rect x="-70" y="{f(-self.H - 10)}" width="140" height="{f(self.H + 50)}" fill="{body}"/>',
             # band shapes defined once, drawn twice (plain and in the channelled half) via <use>
             f'<defs><path id="{lid}" d="{bl}"/><path id="{did}" d="{bd}"/></defs>',
             f'<use href="#{lid}" fill="{light}"/>',
             f'<use href="#{did}" fill="{dark}"/>',
             # the channelled half: the same body + bands again, clipped to the half, each tone an OPAQUE
             # pre-blend of night @ 16 % over it (identical look to the old translucent overlay, no transparency)
             f'<clipPath id="{hid}"><path d="{hp}"/></clipPath>',
             f'<g clip-path="url(#{hid})">',
             f'<rect x="-70" y="{f(-self.H - 10)}" width="140" height="{f(self.H + 50)}" fill="{mix(body, P["night"], .16)}"/>',
             f'<use href="#{lid}" fill="{mix(light, P["night"], .16)}"/>',
             f'<use href="#{did}" fill="{mix(dark, P["night"], .16)}"/>',
             '</g>',
             '</g>']
        # (the tiny dry tip point was removed: at ~0.1 mm printed it is below the dark-sliver minimum)
        s.append("</g>")
        return "".join(s)


# behind the two front-most leaves, the yellow margins taper out over the bottom of the fan (just above the
# rim) so the crossing bases read as one green clump instead of a tangle of yellow lines
FADE = (40, 64)

# draw order = list order (back -> front)
LEAVES = [
    # bases staggered so neighbouring yellow margins at the rim are either well
    # apart (>= ~10 units of green between them) or tucked decisively under the
    # leaf in front -- no parallel double lines with dark slivers.
    # Subtle life only: a faint S (sway) in the tall blades, two blades turning
    # a little edge-on (twist), and the outer ones arching out a touch more.
    Sword(324, 19, 330, 25, "back", bend=0.15, seed=11, asym=0.05, fade=FADE, sway=0.02),
    Sword(282, -6, 420, 27, "back", bend=-0.08, seed=12, asym=-0.05, fade=FADE, sway=-0.04,
          twist=0.5, twist_t=0.6),
    Sword(268, -21, 262, 24, "midd", bend=-0.13, seed=13, fade=FADE, twist=0.2, twist_t=0.55),
    Sword(334, 27, 278, 23, "midd", bend=0.17, seed=14, fade=FADE),
    Sword(305, 3, 478, 30, "midd", bend=-0.06, seed=15, asym=0.06, fade=FADE, sway=0.05),
    Sword(315, 12, 352, 15, "front", bend=0.05, seed=16, fade=FADE, sway=-0.04),
    Sword(256, -44, 150, 22, "front", bend=-0.2, seed=17, fade=FADE),
    Sword(286, -9, 250, 25, "fore", bend=-0.08, seed=18, twist=0.52, twist_t=0.6, sway=0.03),
    Sword(320, 17, 176, 23, "front", bend=0.11, seed=19),
]


def mix(a, b, t):
    """b laid over a at opacity t, as one opaque hex colour."""
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02X}" for i in (1, 3, 5))


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
