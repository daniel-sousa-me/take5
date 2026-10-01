"""Epipremnum aureum (golden pothos) -- v4.

Few, large, glossy heart-shaped leaves with a curved acuminate tip and subtle
golden streaks that follow the lateral veins. Full crown above the rim and three
trailing vines of different lengths (long left drape, short right curl, a short
strand over the front of the rim).
"""
import math
import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import PAL, SHADE, cr_path, cr_sample, ribbon, f, uid, pot, svg_doc, reset_ids  # noqa: E402

P = PAL
CS = 1.08  # crown scale
HID = 0.13  # the petiole ends this far (x L) inside the blade, hidden under it


def _mix(a, b, t):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


_TONES = (P["deep"], P["forest"], P["mid"], P["sage"], P["light"], P["pale"])
# opaque golden streak per leaf tone (yellow_edge on dark leaves, mustard on pale ones)
STREAK = {c: _mix(c, P["mustard"] if c in (P["sage"], P["light"], P["pale"]) else P["yellow_edge"], 0.78)
          for c in _TONES}
# opaque midrib tone per leaf tone (pale @45 %)
RIB = {c: _mix(c, P["pale"], 0.45) for c in _TONES}


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

    def half(self, side, off=0.0):
        ts = [-0.4, 0.3, 0.55, 0.7, 0.8, 0.9, 1.0, 1.1]
        a = [self.warp(-side * off * min(1.0, max(0.0, 1.0 - t) * 1.6), -t) for t in ts]
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
             wide=1.0, vein_col=None, fore=1.0):
    rnd = random.Random(seed * 7 + 3)
    curl = rnd.uniform(0.03, 0.07) * rnd.choice((1, -1)) if curl is None else curl
    asym = rnd.uniform(0.84, 0.93) if asym is None else asym
    lf = PLeaf(L, seed, asym=asym, curl=curl, wide=wide)
    d = lf.outline()
    if L < 60:  # small vine leaves: whole units are plenty (file size)
        d = re.sub(r"-?\d+\.\d+", lambda m: str(round(float(m.group()))), d)
    sx = -1 if flip else 1
    # shade the half that faces world-right (light from upper left)
    a = math.radians(rot)
    wx = sx * math.cos(a)
    side = 1 if wx > 0 else -1
    shade = SHADE.get(fill, fill)
    cid = uid("pl")
    inner = [f'<path d="{lf.half(side)}" fill="{shade}"/>']
    # golden variegation: few, bold spindle streaks lying along lateral veins.
    # Opaque, pre-blended into each leaf tone, >= 5 units at the widest so
    # they survive print. Lateral veins are not drawn (the streaks carry the
    # vein rhythm); every leaf gets a print-safe tapered midrib instead.
    if streak is None:
        n_st = 3 if L >= 100 else (2 if L >= 58 else (1 if L >= 40 else 0))
    else:
        n_st = streak
    slots = {3: [0.1, 0.29, 0.48], 2: [0.16, 0.4], 1: [0.28], 0: []}[n_st]
    col = STREAK.get(fill, P["yellow_edge"])
    sd = rnd.choice((1, -1))
    for t in slots:
        sd = -sd if rnd.random() < 0.75 else sd
        p0, p1, p2 = vein_curve(lf, t + rnd.uniform(0.0, 0.03), sd, reach=rnd.uniform(0.8, 0.92),
                                rise=min(0.26, 0.86 - t))
        p0 = (p0[0] * 0.9 + p1[0] * 0.1, p0[1] * 0.9 + p1[1] * 0.1)
        inner.append(f'<path d="{spindle(p0, p1, p2, max(5.0, L * 0.042))}" fill="{col}"/>')
    # midrib: filled taper, widest (>= 4 units) at the sinus, low-contrast solid
    vc = vein_col or RIB.get(fill, P["pale"])
    hw = max(2.1, L * 0.02)
    ts = [0.0, 0.3, 0.62, 0.93]
    rr = [lf.warp(hw / L * (1 - 0.8 * t), -t) for t in ts]
    ll = [lf.warp(-hw / L * (1 - 0.8 * t), -t) for t in ts]
    ring = rr + ll[::-1]
    inner.append(f'<path d="{cr_path(ring, closed=True, sharp={0, len(rr) - 1, len(rr), len(ring) - 1})}" fill="{vc}"/>')
    sxx = round((-1 if flip else 1) * fore, 2)
    tr = f"translate({f(x)} {f(y)}) rotate({f(rot)})" + (f" scale({sxx:g} 1)" if sxx != 1 else "")
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
    return f'<path d="{ribbon([a, m, c, b], w0, w1, per=4)}" fill="{col}"/>'


def petiole_arc(a, b, u_end, w0, w1, col, k=0.45):
    """a -> b as ONE bend (quadratic bezier): the control point sits back down the
    leaf axis from b, so the petiole leaves the soil and arrives along the blade
    axis with no S-wiggle."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    X = (b[0] - u_end[0] * L * k, b[1] - u_end[1] * L * k)
    pts = [tuple((1 - t) ** 2 * a[j] + 2 * (1 - t) * t * X[j] + t * t * b[j] for j in (0, 1))
           for t in (i / 6 for i in range(7))]
    return f'<path d="{ribbon(pts, w0, w1)}" fill="{col}"/>'


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


def vine(pts, leaves, w0, w1, col, pcol=None, anchor=None, clip=None):
    """leaves: list of (frac, side, L, fill, seed, out_angle, droop, flip).
    anchor: the path the leaf fractions were laid out on (so re-routing the start
    of a vine does not move its leaves); each leaf node snaps to the nearest point
    of the drawn path. clip: optional clip-path id for the main stem."""
    s = cr_sample(pts, 10)
    sa = cr_sample(anchor, 10) if anchor else s
    cp = f' clip-path="url(#{clip})"' if clip else ""
    stems, blades = [f'<path d="{ribbon(pts, w0, w1, per=4)}" fill="{col}"{cp}/>'], []
    pcol = pcol or col
    for lv in leaves:
        fr, side, L, fill, seed, out, droop, flip = lv[:8]
        fore = lv[8] if len(lv) > 8 else 1.0
        n, t = along(sa, fr)
        if anchor:
            i = min(range(1, len(s)), key=lambda k: math.hypot(s[k][0] - n[0], s[k][1] - n[1]))
            n, t = s[i], unit((s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1]))
        # petiole direction: tangent rotated outward by `out` degrees
        a = math.radians(out * side)
        d = (t[0] * math.cos(a) - t[1] * math.sin(a), t[0] * math.sin(a) + t[1] * math.cos(a))
        pl = L * 0.26
        base = (n[0] + d[0] * pl, n[1] + d[1] * pl)
        u = unit((d[0] * (1 - droop), d[1] * (1 - droop) + droop))  # gravity pulls the blade down
        tip_w = max(2.8, L * 0.045)
        stems.append(petiole(n, base, u, tip_w * 1.15, tip_w * 0.9, pcol))
        blades.append(leaf_svg(base[0], base[1], rot_of(u), L, fill, seed, flip=flip, fore=fore))
    return "".join(stems), "".join(blades)

def bez(p0, p1, p2, p3, n=9):
    return [tuple((1 - t) ** 3 * p0[j] + 3 * (1 - t) ** 2 * t * p1[j] + 3 * (1 - t) * t * t * p2[j] + t ** 3 * p3[j]
                  for j in (0, 1)) for t in (i / (n - 1) for i in range(n))]


def crown_petiole(a, b, u_end, w0, w1, col, rise=0.42, arrive=0.34, bow=0.0):
    """Soil -> leaf as one graceful C: it leaves the soil close to vertical (stems spring
    from a tight cluster), then bends over to arrive along the blade axis, so outer
    petioles arc outward more than inner ones."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    lean = (b[0] - a[0]) / L
    d0 = unit((lean * 0.45 + bow, -1.0))
    p1 = (a[0] + d0[0] * L * rise, a[1] + d0[1] * L * rise)
    p2 = (b[0] - u_end[0] * L * arrive, b[1] - u_end[1] * L * arrive)
    return f'<path d="{ribbon(bez(a, p1, p2, b, 6), w0, w1, per=4)}" fill="{col}"/>'


def build():
    back, front = pot("classic", rx=90, rim_y=588, base_w=66, band=False)
    out = [back]

    # --- crown. The plant has a gentle sweep up and to the right (balanced by the long
    # left drape): leaves higher up are pushed a little right (LEAN), young small leaves
    # at the top, big old ones low and nodding outward under their weight.
    # (leaf base point, rotation, L, fill, seed, flip, stem start x, droop-curl, fore)
    crown_back = [
        ((236, 432), -50, 106, P["deep"], 1, True, 262, 0.06, 1.0),
        ((356, 400), 25, 126, P["deep"], 2, False, 322, 0.07, 0.9),
        ((330, 330), 22, 60, P["sage"], 10, False, 314, -0.03, 0.86),  # young top leaf (peeks out behind the centre leaf)
        ((298, 384), -4, 132, P["mid"], 3, False, 300, -0.04, 1.0),
        ((408, 488), 72, 96, P["forest"], 4, False, 344, 0.11, 1.0),
        ((194, 514), -100, 106, P["forest"], 5, False, 250, 0.12, 1.0),
    ]
    # the two front leaves close ranks over the open middle, so the long stems to the
    # top leaves pass behind them instead of running up through a gap
    crown_front = [
        ((272, 508), -16, 120, P["light"], 6, True, 278, 0.05, 1.0),
        ((321, 496), 24, 98, P["sage"], 7, False, 326, 0.08, 0.84),
    ]
    # low leaves leaning forward over the rim (blade drawn after the pot front)
    crown_low = [
        ((290, 584), -76, 100, P["mid"], 8, True, 314, 0.07, 1.0),
        ((372, 574), 84, 78, P["light"], 9, False, 336, 0.08, 0.9),
    ]
    ARC = {2, 3, 10}
    BOW = {3: -0.14, 10: 0.3, 2: 0.18, 1: -0.2, 5: -0.25, 4: 0.25}
    stems, leaves, low = [], [], []
    for grp in (crown_back, crown_front, crown_low):
        for (bx, by), rot, L, fill, seed, flip, sx0, droop, fore in grp:
            if grp is not crown_low:  # grow the crown a little about the soil centre
                bx, by, L = 300 + (bx - 300) * CS, 612 + (by - 612) * CS, L * CS
                lift = (612 - by) / 260.0
                bx += 26 * lift * lift  # gesture: the upper crown leans right
                rot += 7 * lift
            u = (math.sin(math.radians(rot)), -math.cos(math.radians(rot)))
            w = max(3.0, L * 0.036)
            stems.append(crown_petiole((sx0, 612), (bx, by), u, w * 1.35, w * 0.95, P["sage"],
                                       rise=0.5 if seed in ARC else 0.4, bow=BOW.get(seed, 0.0)))
            # tip droops toward the ground: sign follows which way "down" is in leaf coords
            sgn = (1 if rot > 0 else -1) * (-1 if flip else 1)
            curl = sgn * droop * min(1.0, abs(math.sin(math.radians(rot))) + 0.25)
            (low if grp is crown_low else leaves).append(
                leaf_svg(bx, by, rot, L, fill, seed, flip=flip, curl=curl, fore=fore))
    out += stems + leaves

    # --- vines (drawn after the pot front: they spill over the rim and hang under
    # their own weight: a smooth catenary-like drop, tips curling up slightly)
    # long left vine: rises from under the big low front leaf, crosses the lip and
    # drops in one long sweep down the left side of the pot
    Lv = [(250, 594), (226, 588), (198, 591), (170, 606), (146, 632), (127, 664), (114, 694),
          (102, 712), (86, 719), (70, 713), (59, 698)]
    s1, b1 = vine(Lv, [
        (0.11, -1, 66, P["light"], 21, 52, 0.45, True),
        (0.26, 1, 60, P["forest"], 22, 64, 0.38, False, 0.86),
        (0.40, -1, 54, P["mid"], 23, 58, 0.62, True),
        (0.54, 1, 48, P["sage"], 24, 66, 0.35, False, 0.82),
        (0.67, -1, 42, P["forest"], 25, 56, 0.55, True),
        (0.79, 1, 35, P["light"], 27, 60, 0.3, False, 0.88),
        (0.90, -1, 28, P["mid"], 26, 50, 0.4, True),
        (0.995, 1, 21, P["sage"], 28, 30, 0.2, False),
    ], 5.2, 1.9, P["forest"], P["sage"], anchor=[(236, 604), (212, 588)] + Lv[3:])
    # right vine: arches over the rim and hangs to mid-pot height
    Rv = [(346, 608), (360, 594), (380, 589), (402, 590), (430, 600), (456, 622), (474, 652),
          (483, 680), (487, 698), (491, 712), (499, 721)]
    rx, ry, rim_y = 90, 90 * 0.15, 588
    arc = [(x, rim_y + ry * math.sqrt(max(0.0, 1 - ((x - 300) / rx) ** 2))) for x in range(334, 367, 4)]
    hole = uid("vh")
    # canvas clockwise + hole anticlockwise (nonzero winding leaves the hole out)
    out.append(f'<clipPath id="{hole}"><path d="M0 0H600V800H0Z'
               f'M{f(arc[0][0])} 640L{f(arc[-1][0])} 640'
               + "".join(f"L{f(x)} {f(y)}" for x, y in arc[::-1]) + 'Z"/></clipPath>')
    s2, b2 = vine(Rv, [
        (0.16, 1, 66, P["mid"], 31, 58, 0.4, False),
        (0.36, -1, 56, P["forest"], 32, 64, 0.58, True, 0.85),
        (0.55, 1, 46, P["sage"], 33, 64, 0.35, False),
        (0.73, -1, 37, P["deep"], 35, 58, 0.5, True),
        (0.87, 1, 29, P["light"], 36, 54, 0.45, False, 0.86),
        (0.995, -1, 22, P["mid"], 34, 30, 0.25, True),
    ], 4.6, 1.9, P["mid"], P["sage"], anchor=[(372, 604), (394, 590)] + Rv[4:], clip=hole)
    # short strand over the front of the rim, with a soft S
    Fv = [(322, 600), (331, 614), (337, 640), (333, 668), (325, 690), (322, 708)]
    s3, b3 = vine(Fv, [
        (0.26, 1, 52, P["deep"], 41, 62, 0.5, False),
        (0.58, -1, 42, P["forest"], 42, 58, 0.55, True, 0.86),
        (0.98, 1, 30, P["deep"], 43, 34, 0.35, False),
    ], 4.4, 1.9, P["forest"], P["mid"])
    out.append(front)
    out.append(s1)  # under the low leaves: the left vine's start is tucked under the big front leaf
    out += low
    out += [s2, s3, b3, b2, b1]
    return "".join(out)




if __name__ == "__main__":
    reset_ids()
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "..", "out", "epipremnum_aureum.svg")
    open(dst, "w").write(svg_doc(build(), "Epipremnum aureum (golden pothos)"))
    print("wrote", os.path.normpath(dst), os.path.getsize(dst), "bytes")
