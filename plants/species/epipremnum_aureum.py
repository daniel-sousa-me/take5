"""Epipremnum aureum (golden pothos) -- v4.

Few, large, glossy heart-shaped leaves with a curved acuminate tip and subtle
golden streaks that follow the lateral veins. Full crown above the rim and three
trailing vines of different lengths (long left drape, short right curl, a short
strand over the front of the rim).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import PAL, SHADE, cr_path, cr_sample, ribbon, f, uid, pot, svg_doc, reset_ids  # noqa: E402

P = PAL
CS = 1.08  # crown scale
HID = 0.13  # the petiole ends this far (x L) inside the blade, hidden under it


# ------------------------------------------------------------------ leaf
class PLeaf:
    """Pothos leaf in local coords, unit length. Origin = hidden petiole end;
    sinus just below it at +y, tip towards -y."""

    # right half from sinus to (just before) the tip, (x, y) in units of L,
    # y measured from the petiole attachment (0 = sinus) going up = negative
    RIGHT = [(0.085, 0.035), (0.215, 0.015), (0.345, -0.07), (0.425, -0.2),
             (0.44, -0.35), (0.4, -0.5), (0.315, -0.645), (0.2, -0.77),
             (0.082, -0.878), (0.022, -0.952)]

    def __init__(self, L, seed, asym=0.9, curl=0.1, wide=1.0, sinus=0.06):
        rnd = random.Random(seed)
        self.L, self.curl, self.rnd = L, curl, rnd
        self.sinus = sinus

        def side(sc):
            out = []
            for i, (x, y) in enumerate(self.RIGHT):
                j = rnd.uniform(-0.012, 0.012) if 1 < i < 8 else 0
                out.append((x * sc * wide + j, y))
            return out
        self.r = side(1.0)
        self.l = side(asym)

    def warp(self, x, y):
        """unit coords -> local px (tip curl + origin shift)."""
        t = -y
        s = max(0.0, (t - 0.5) / 0.5)
        x = x + self.curl * s * s
        return (x * self.L, (y + HID) * self.L)

    def outline(self):
        pts = [(0.0, -self.sinus)]  # sinus notch, a little up into the blade
        pts += self.r
        pts.append((0.0, -1.0))
        pts += [(-x, y) for x, y in self.l[::-1]]
        w = [self.warp(x, y) for x, y in pts]
        return cr_path(w, closed=True, sharp={0, len(self.r) + 1})

    def mid(self, t):
        return self.warp(0.0, -t)

    def width(self, t, side):
        pts = self.r if side > 0 else self.l
        best = pts[0][0]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if -y1 >= t >= -y0:
                u = (t + y0) / ((y0 - y1) or 1)
                return x0 + (x1 - x0) * u
        if t > -pts[-1][1]:
            return pts[-1][0] * max(0.0, (1 - t) / (1 + pts[-1][1]))
        return best

    def vpt(self, t, side, frac):
        return self.warp(side * self.width(t, side) * frac, -t)

    def half(self, side):
        ts = [-0.4, 0.3, 0.55, 0.7, 0.8, 0.9, 1.0, 1.1]
        a = [self.warp(0, -t) for t in ts]
        b = [self.warp(side * 3, -t) for t in (ts[-1], ts[0])][::-1]
        pts = a + b[::-1]
        return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"


def vein_curve(lf, t, side, reach=0.9, rise=0.26):
    p0 = lf.mid(t)
    p1 = lf.vpt(t + rise * 0.42, side, reach * 0.42)
    p2 = lf.vpt(min(t + rise, 0.96), side, reach)
    return p0, p1, p2


def spindle(p0, p1, p2, w):
    """Lens-shaped streak along the quadratic p0-p1-p2 (pointed both ends), two cubics."""
    dx, dy = p2[0] - p0[0], p2[1] - p0[1]
    m = math.hypot(dx, dy) or 1
    nx, ny = -dy / m * w * 0.66, dx / m * w * 0.66
    a = (p0[0] + (p1[0] - p0[0]) * 0.75, p0[1] + (p1[1] - p0[1]) * 0.75)
    b = (p2[0] + (p1[0] - p2[0]) * 0.75, p2[1] + (p1[1] - p2[1]) * 0.75)
    return (f"M{f(p0[0])} {f(p0[1])}C{f(a[0] + nx)} {f(a[1] + ny)} {f(b[0] + nx)} {f(b[1] + ny)} {f(p2[0])} {f(p2[1])}"
            f"C{f(b[0] - nx)} {f(b[1] - ny)} {f(a[0] - nx)} {f(a[1] - ny)} {f(p0[0])} {f(p0[1])}Z")


def leaf_svg(x, y, rot, L, fill, seed, flip=False, curl=None, asym=None, streak=None,
             wide=1.0, vein_col=None):
    rnd = random.Random(seed * 7 + 3)
    curl = rnd.uniform(0.03, 0.07) * rnd.choice((1, -1)) if curl is None else curl
    asym = rnd.uniform(0.84, 0.93) if asym is None else asym
    lf = PLeaf(L, seed, asym=asym, curl=curl, wide=wide)
    d = lf.outline()
    sx = -1 if flip else 1
    # shade the half that faces world-right (light from upper left)
    a = math.radians(rot)
    wx = sx * math.cos(a)
    side = 1 if wx > 0 else -1
    shade = SHADE.get(fill, fill)
    cid = uid("pl")
    inner = [f'<path d="{lf.half(side)}" fill="{shade}"/>']
    # golden variegation: a few thin spindle streaks lying along lateral veins
    n_st = rnd.choice([2, 2, 3]) if streak is None else streak
    slots = [0.1, 0.2, 0.3, 0.4, 0.5]
    rnd.shuffle(slots)
    pale_leaf = fill in (P["light"], P["pale"], P["sage"])
    col = P["mustard"] if pale_leaf else P["yellow_edge"]
    sd = rnd.choice((1, -1))
    for t in slots[:n_st]:
        sd = -sd if rnd.random() < 0.6 else sd
        p0, p1, p2 = vein_curve(lf, t + rnd.uniform(0.01, 0.04), sd, reach=rnd.uniform(0.7, 0.88))
        p0 = (p0[0] * 0.55 + p1[0] * 0.45, p0[1] * 0.55 + p1[1] * 0.45)
        inner.append(f'<path d="{spindle(p0, p1, p2, L * rnd.uniform(0.022, 0.032))}" fill="{col}" opacity=".72"/>')
        if rnd.random() < 0.45:  # hair-thin cream companion streak
            q0, q1, q2 = vein_curve(lf, t + 0.06, sd, reach=0.7)
            q0 = (q0[0] * 0.4 + q1[0] * 0.6, q0[1] * 0.4 + q1[1] * 0.6)
            inner.append(f'<path d="{spindle(q0, q1, q2, L * 0.011)}" fill="{P["cream"]}" opacity=".5"/>')
    # veins
    vc = vein_col or P["pale"]
    vv = []
    vts = (0.1, 0.23, 0.36, 0.48, 0.59) if L >= 60 else (0.13, 0.32, 0.5)
    for t in vts:
        for s in (1, -1):
            p0, p1, p2 = vein_curve(lf, t, s, rise=min(0.26, 0.8 - t))
            vv.append(f"M{f(p0[0])} {f(p0[1])}Q{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])}")
    inner.append(f'<path d="{"".join(vv)}" fill="none" stroke="{vc}" stroke-width="{f(max(0.7, L * 0.011))}" '
                 f'stroke-linecap="round" opacity=".32"/>')
    mp = [lf.mid(-0.02 + i * 0.16) for i in range(7)]
    inner.append(f'<path d="M{f(mp[0][0])} {f(mp[0][1])}' + "".join(
        f"L{f(px)} {f(py)}" for px, py in mp[1:]) + f'" fill="none" stroke="{vc}" '
        f'stroke-width="{f(max(1.0, L * 0.019))}" stroke-linecap="round" stroke-linejoin="round" opacity=".5"/>')
    tr = f"translate({f(x)} {f(y)}) rotate({f(rot)})" + (" scale(-1 1)" if flip else "")
    pid = cid + "p"
    return (f'<g transform="{tr}"><path id="{pid}" d="{d}" fill="{fill}"/>'
            f'<clipPath id="{cid}"><use href="#{pid}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{"".join(inner)}</g></g>')


def rot_of(u):
    return math.degrees(math.atan2(u[0], -u[1]))


def unit(v):
    m = math.hypot(*v) or 1
    return (v[0] / m, v[1] / m)


def petiole(a, b, u_end, w0, w1, col, bow=0.0):
    """a -> b, arriving along direction u_end (the leaf axis)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    m = (a[0] + dx * 0.5 - dy / L * bow * L, a[1] + dy * 0.5 + dx / L * bow * L)
    c = (b[0] - u_end[0] * L * 0.22, b[1] - u_end[1] * L * 0.22)
    return f'<path d="{ribbon([a, m, c, b], w0, w1)}" fill="{col}"/>'


# ------------------------------------------------------------------ vines
def along(s, frac):
    """point + unit tangent at fraction of arclength of sampled polyline s."""
    d = [0.0]
    for p, q in zip(s, s[1:]):
        d.append(d[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    tgt = frac * d[-1]
    for i in range(1, len(s)):
        if d[i] >= tgt:
            u = (tgt - d[i - 1]) / ((d[i] - d[i - 1]) or 1)
            p = (s[i - 1][0] + (s[i][0] - s[i - 1][0]) * u, s[i - 1][1] + (s[i][1] - s[i - 1][1]) * u)
            return p, unit((s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1]))
    return s[-1], unit((s[-1][0] - s[-2][0], s[-1][1] - s[-2][1]))


def vine(pts, leaves, w0, w1, col, pcol=None):
    """leaves: list of (frac, side, L, fill, seed, out_angle, droop, flip)."""
    s = cr_sample(pts, 10)
    stems, blades = [f'<path d="{ribbon(pts, w0, w1)}" fill="{col}"/>'], []
    pcol = pcol or col
    for fr, side, L, fill, seed, out, droop, flip in leaves:
        n, t = along(s, fr)
        # petiole direction: tangent rotated outward by `out` degrees
        a = math.radians(out * side)
        d = (t[0] * math.cos(a) - t[1] * math.sin(a), t[0] * math.sin(a) + t[1] * math.cos(a))
        pl = L * 0.26
        base = (n[0] + d[0] * pl, n[1] + d[1] * pl)
        u = unit((d[0] * (1 - droop), d[1] * (1 - droop) + droop))  # gravity pulls the blade down
        tip_w = max(1.6, L * 0.045)
        stems.append(petiole(n, base, u, tip_w * 1.15, tip_w * 0.9, pcol))
        blades.append(leaf_svg(base[0], base[1], rot_of(u), L, fill, seed, flip=flip))
    return "".join(stems), "".join(blades)


# ------------------------------------------------------------------ plant
def build():
    back, front = pot("classic", rx=98, rim_y=588, base_w=72, band=False)
    out = [back]

    # --- crown: (leaf base point, rotation, L, fill, seed, flip, stem start x, bow)
    crown_back = [
        # back tier, darkest; C (centre top) sits over A and B
        ((252, 410), -36, 120, P["deep"], 1, True, 276, -0.05),
        ((352, 400), 28, 124, P["deep"], 2, False, 318, 0.05),
        ((302, 376), -7, 128, P["mid"], 3, False, 298, 0.01),
        ((402, 478), 64, 108, P["forest"], 4, False, 330, 0.07),
        ((196, 510), -110, 100, P["forest"], 5, False, 266, -0.12),
    ]
    crown_front = [
        ((266, 506), -17, 112, P["light"], 6, True, 286, -0.03),
        ((340, 518), 22, 106, P["sage"], 7, False, 312, 0.04),
    ]
    # low leaves leaning forward over the rim (blade drawn after the pot front)
    crown_low = [
        ((290, 582), -72, 96, P["mid"], 8, True, 326, 0.04),
        ((372, 572), 80, 86, P["light"], 9, False, 322, 0.05),
    ]
    stems, leaves, low = [], [], []
    for grp in (crown_back, crown_front, crown_low):
        for (bx, by), rot, L, fill, seed, flip, sx0, bow in grp:
            if grp is not crown_low:  # grow the crown a little about the soil centre
                bx, by, L = 300 + (bx - 300) * CS, 612 + (by - 612) * CS, L * CS
            u = (math.sin(math.radians(rot)), -math.cos(math.radians(rot)))
            w = max(3.0, L * 0.036)
            stems.append(petiole((sx0, 612), (bx, by), u, w * 1.3, w, P["sage"], bow))
            (low if grp is crown_low else leaves).append(leaf_svg(bx, by, rot, L, fill, seed, flip=flip))
    out += stems + leaves

    # --- vines (drawn after the pot front: they spill over the rim)
    # long vine, left side; leaves alternate irregularly and shrink to the tip
    Lv = [(236, 604), (212, 588), (184, 592), (160, 618), (144, 660), (134, 704), (122, 740), (104, 762)]
    s1, b1 = vine(Lv, [
        (0.14, -1, 68, P["light"], 21, 50, 0.5, True),
        (0.33, 1, 60, P["forest"], 22, 60, 0.55, False),
        (0.50, -1, 54, P["mid"], 23, 55, 0.6, True),
        (0.65, 1, 46, P["sage"], 24, 58, 0.55, False),
        (0.83, -1, 38, P["forest"], 25, 50, 0.5, True),
        (0.98, 1, 28, P["mid"], 26, 40, 0.45, False),
    ], 5.2, 2.2, P["mid"], P["sage"])
    # short curl, right side; bare tip curls back up
    Rv = [(372, 604), (394, 590), (424, 596), (452, 620), (468, 650), (468, 678), (458, 693),
          (444, 695), (436, 686)]
    s2, b2 = vine(Rv, [
        (0.15, 1, 68, P["mid"], 31, 58, 0.4, False),
        (0.41, -1, 54, P["forest"], 32, 62, 0.55, True),
        (0.62, 1, 36, P["sage"], 33, 60, 0.35, False),
    ], 4.6, 1.5, P["mid"], P["sage"])
    # short strand over the front of the rim
    Fv = [(322, 600), (330, 612), (336, 638), (334, 668), (326, 690)]
    s3, b3 = vine(Fv, [
        (0.30, 1, 54, P["deep"], 41, 60, 0.5, False),
        (0.66, -1, 44, P["forest"], 42, 58, 0.55, True),
        (0.98, 1, 32, P["deep"], 43, 30, 0.4, False),
    ], 4.4, 2.0, P["forest"], P["mid"])
    out.append(front)
    out += low
    out += [s1, s2, s3, b3, b2, b1]
    return "".join(out)


if __name__ == "__main__":
    reset_ids()
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "..", "out", "epipremnum_aureum.svg")
    open(dst, "w").write(svg_doc(build(), "Epipremnum aureum (golden pothos)"))
    print("wrote", os.path.normpath(dst), os.path.getsize(dst), "bytes")
