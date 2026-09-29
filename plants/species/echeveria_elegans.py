"""Echeveria elegans (Mexican snowball) -- v5.
python3 species/echeveria_elegans.py  -> out/echeveria_elegans.svg

One rosette of thick spoon-shaped leaves in concentric rings around a single
centre, seen from slightly above (each ring projects to an ellipse). Rings are
painted outer -> inner and back -> front; each ring is one clear tone step
lighter than the ring under it (outer deep blue-green -> pale powdery heart).
Every leaf is: face (ring tone) + the half turned away from the light (one
step darker) + its own opaque blush cap at the tip, all clipped to the leaf so
nothing leaks. The rosette sits in a shallow bowl: its front leaves lie well
over the rim band, whose lower part stays visible below and on both sides.
Two offsets on the rim and two nodding coral flower stalks (the taller one
gives the plant its height).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, cr_path, cr_sample, ribbon, f, uid, reset_ids, pot, svg_doc  # noqa: E402

P = PAL
CX = 300
RIM_Y = 616
RIM_H = 28
POT_RX = 94
EL = math.radians(46)                 # camera elevation above the horizon
SE, CE = math.sin(EL), math.cos(EL)

# powdery blue-green ramp (bluer extension of PAL sage / light / pale), dark -> light
RAMP = ["#4A6155", "#5A7165", "#6B8377", "#7F968A", "#94AB9F", "#AABFB4", "#C0D1C7", "#D5E1D8",
        "#E4ECE4"]
BLUSH = "#DCA29E"      # tip cap (between PAL blush and its lighter tint)
CAP_K = 0.15           # blush cap = leaf outline scaled by this about its tip
BAND_K = 1.6           # mid-pink band under the cap: the outline scaled by CAP_K * BAND_K


def mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(pa, pb))


# ------------------------------------------------------------------ leaf geometry
WP = [(0, .30), (.14, .44), (.32, .66), (.50, .86), (.66, .98), (.78, .92), (.88, .66),
      (.95, .30), (1.0, 0.0)]         # spoon-shaped half-width profile (fraction of W)
ST = [0, .16, .38, .58, .76, .88, .95]


def interp(tab, u):
    for (a, wa), (b, wb) in zip(tab, tab[1:]):
        if a <= u <= b:
            return wa + (wb - wa) * (u - a) / (b - a)
    return tab[-1][1]


class Leaf:
    """A leaf growing from the rosette centre in ground direction `th` (0 = right,
    90 deg = towards the viewer), rising at `al` degrees and curling up by `curl`."""

    def __init__(self, cx, cy, th, al, curl, L, W, r0=0.0, z0=0.0, cup=0.18):
        self.cx, self.cy = cx, cy
        self.th, self.L, self.W, self.cup = math.radians(th), L, W, cup
        d = (math.cos(self.th), math.sin(self.th))
        self.lat = (-d[1], d[0], 0.0)
        n = 30
        x, y, z = d[0] * r0, d[1] * r0, z0
        self.mid3, self.nrm = [], []
        for i in range(n + 1):
            u = i / n
            a = math.radians(al + curl * u ** 1.8)
            self.mid3.append((x, y, z))
            self.nrm.append((-math.sin(a) * d[0], -math.sin(a) * d[1], math.cos(a)))
            st = L / n
            x += math.cos(a) * d[0] * st
            y += math.cos(a) * d[1] * st
            z += math.sin(a) * st
        # upper face visible?  view vector towards the camera: (0, CE, SE)
        nm = self.nrm[18]
        self.top = nm[1] * CE + nm[2] * SE > 0.05
        self.depth = self.mid3[15][1] * CE + self.mid3[15][2] * SE   # nearer camera = larger

    def p3(self, u, w):
        i = min(int(u * 30), 29)
        s = u * 30 - i
        a, b = self.mid3[i], self.mid3[i + 1]
        m = [a[k] + (b[k] - a[k]) * s for k in range(3)]
        n = self.nrm[i]
        hw = self.W * interp(WP, u)
        return tuple(m[k] + w * hw * self.lat[k] + self.cup * abs(w) * hw * n[k] for k in range(3))

    def pr(self, p):
        return (self.cx + p[0], self.cy + p[1] * SE - p[2] * CE)

    def pt(self, u, w):
        return self.pr(self.p3(u, w))

    def outline(self):
        R = [self.pt(u, 1) for u in ST]
        Lf = [self.pt(u, -1) for u in ST]
        tip = self.pt(1.0, 0)
        pts = R + [tip] + Lf[1:][::-1]
        return pts, {0, len(R), len(pts) - 1 + 1 if False else 0}

    def poly(self):
        R = [self.pt(u, 1) for u in ST]
        Lf = [self.pt(u, -1) for u in ST]
        return [self.pt(0, 0)] + R[1:] + [self.pt(1.0, 0)] + Lf[1:][::-1]

    def path(self):
        R = [self.pt(u, 1) for u in ST]
        Lf = [self.pt(u, -1) for u in ST]
        tip = self.pt(1.0, 0)
        pts = [self.pt(0, 0)] + R[1:] + [tip] + Lf[1:][::-1]
        return rel_path(pts, sharp={0, len(R)})

    def half(self, side):
        """Polygon covering one side of the midline (to be clipped by the leaf)."""
        us = [-.2, .25, .55, .8, 1.0, 1.15]
        mids = [self.pt(max(0, min(1, u)), 0) if 0 <= u <= 1 else self._ext(u) for u in us]
        far = [self._off(u, side * 4) for u in us]
        return mids + far[::-1]

    def _ext(self, u):
        a, b = self.pt(0, 0), self.pt(0.1, 0)
        c, d = self.pt(0.95, 0), self.pt(1.0, 0)
        if u < 0:
            return (a[0] + (a[0] - b[0]) * 3, a[1] + (a[1] - b[1]) * 3)
        return (d[0] + (d[0] - c[0]) * 4, d[1] + (d[1] - c[1]) * 4)

    def _off(self, u, w):
        uu = max(0.02, min(0.98, u))
        m = self.p3(uu, 0)
        q = tuple(m[k] + w * self.W * self.lat[k] for k in range(3))
        return self.pr(q)

    def cap(self, u0=0.80):
        """Blush cap: a pointed patch running back from the tip along the midline
        (full width only over the last few percent), clipped by the leaf."""
        t = self._ext(1.2)
        c = self.pt(1.0, 0)
        ex = (t[0] - c[0], t[1] - c[1])
        r1, l1 = self._off(.94, .6), self._off(.94, -.6)
        return [self._off(u0, 0), self._off(.88, .3), r1, (r1[0] + ex[0], r1[1] + ex[1]),
                (l1[0] + ex[0], l1[1] + ex[1]), l1, self._off(.88, -.3)]

    def lit_side(self):
        """+1 if the right half (lat +) faces the upper-left light better."""
        lx, ly = self.lat[0], self.lat[1] * SE
        return 1 if (lx * -0.8 + ly * -0.6) > 0 else -1


def _num(v):
    t = f"{v:.1f}"
    if t.endswith(".0"):
        t = t[:-2]
    if t in ("-0", "-0.0"):
        t = "0"
    return t.replace("0.", ".", 1) if t.startswith("0.") else t.replace("-0.", "-.", 1)


def _join(nums):
    out = ""
    for v in nums:
        t = _num(v)
        if out and not t.startswith("-") and not (t.startswith(".") and "." in out.split(" ")[-1].split("-")[-1]):
            out += " "
        out += t
    return out


def rel_path(pts, sharp=()):
    """cr_path, written with relative cubic segments (smaller file, same curve)."""
    n = len(pts)
    sharp = set(sharp)
    q = lambda p: (round(p[0], 1), round(p[1], 1))  # noqa: E731
    cur = q(pts[0])
    d = [f"M{_num(cur[0])} {_num(cur[1])}c"]
    segs = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = p1 if i in sharp else (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = p2 if (i + 1) % n in sharp else (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        a, b, e = q(c1), q(c2), q(p2)
        segs += [a[0] - cur[0], a[1] - cur[1], b[0] - cur[0], b[1] - cur[1], e[0] - cur[0], e[1] - cur[1]]
        cur = e
    return d[0] + _join(segs) + "z"


def poly_d(pts):
    """Clip-only helper polygons: whole units are plenty."""
    return "M" + "L".join(f"{round(x)} {round(y)}" for x, y in pts) + "Z"


def width_metric(pts):
    """4*area/perimeter of a polygon (the print report's 'widest point' measure)."""
    A = abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2
    Pm = sum(math.dist(pts[i], pts[i - 1]) for i in range(len(pts)))
    return 4 * A / Pm if Pm else 0


MMU = 0.055          # planning print scale, mm per canvas unit (print policy)
MIN_MM = 0.25        # light shapes narrower than this on the card are left out


def leaf_svg(lf, face, shade, blush=True, k=None, ps=MMU):
    """ps: mm per unit of this rosette's own coordinates (pups are drawn scaled down)."""
    wm = width_metric(lf.poly()) * ps
    if wm < MIN_MM:
        return ""
    lid, cid = uid("L"), uid("C")
    if not lf.top:                     # seen from below: whole leaf a step darker
        face, shade = shade, mix(shade, RAMP[0], 0.5)
    sh = lf.half(-lf.lit_side())
    out = [f'<defs><path id="{lid}" d="{lf.path()}"/></defs><use href="#{lid}" fill="{face}"/>',
           f'<clipPath id="{cid}"><use href="#{lid}"/></clipPath>',
           f'<g clip-path="url(#{cid})"><path d="{poly_d(sh)}" fill="{shade}"/>']
    k = k or CAP_K
    if blush and lf.top and wm * k >= MIN_MM:
        # the blush is the leaf's own outline shrunk towards its tip, in two graded
        # steps: a wider mid-pink band (halfway between leaf and blush) and the
        # tip cap inside it, so the colour builds up to the tip instead of sitting
        # on the leaf as a separate pink shape
        tx, ty = lf.pt(1.0, 0)
        for kk, t in ((k * BAND_K, 0.40), (k, 0.12)):
            out.append(f'<use href="#{lid}" fill="{mix(BLUSH, face, t)}" transform="matrix({kk:.3g} 0 0 {kk:.3g} '
                       f'{f(tx * (1 - kk))} {f(ty * (1 - kk))})"/>')
    out.append("</g>")
    return "".join(out)


# ------------------------------------------------------------------ rosette
# rings, outer -> inner: (n, alpha, curl, L, W/L, ramp index of the face, phase deg)
RINGS = [
    (10, 2, 20, 150, .26, 2, 8),
    (9, 10, 20, 114, .28, 4, 30),
    (8, 20, 16, 84, .30, 5, 4),
    (6, 30, 12, 64, .38, 6, 26),     # fewer, larger inner leaves: a calm pale heart, not a mosaic
    (4, 42, 8, 42, .50, 7, 62),
]
BLUSH_RINGS = 2        # only the outer rings carry tip blush (inner tips read as pink speckle mid-leaf)


def rosette(cx, cy, s=1.0, rings=RINGS, hook=None, hook_after=0, blush=True, jitter=True, k=None,
            ps=MMU, bud=(5, 3.6), blush_rings=99):
    out = []
    for ri, (n, al, curl, L, wf, ci, ph) in enumerate(rings):
        leaves = []
        for i in range(n):
            j = ((i * 7 + ri * 3) % 5 - 2) / 2 if jitter else 0
            th = ph + i * 360 / n + j * 4
            Ls = L * s * (1 + j * 0.03)
            leaves.append(Leaf(cx, cy, th, al + j * 2, curl, Ls, Ls * wf, r0=2 * s, z0=ri * 3 * s))
        leaves.sort(key=lambda lf: lf.depth)
        face = RAMP[ci]
        shade = mix(RAMP[ci], RAMP[ci - 1], 0.75)
        for lf in leaves:
            out.append(leaf_svg(lf, face, shade, blush and ri < blush_rings, k, ps))
        if hook and ri == hook_after:
            out.append(hook())
    # tiny closed bud at the very heart hides where the innermost leaves meet
    z = (len(rings) - 1) * 3 * s + 2 * s
    out.append(f'<ellipse cx="{f(cx)}" cy="{f(cy - z * CE)}" rx="{f(bud[0] * s)}" ry="{f(bud[1] * s)}" '
               f'fill="{RAMP[8]}"/>')
    return "".join(out)


# ------------------------------------------------------------------ flower stalks
STALK = P["rose"]
STALK_SH = mix(P["rose"], P["plum"], 0.5)
BELL = "#DE9A86"          # coral between PAL blush and terra_hi
BELL_SH = "#C77F72"
BRACT = RAMP[5]
BRACT_SH = RAMP[3]


def along(pts, t):
    s = cr_sample(pts, 12)
    acc = [0.0]
    for a, b in zip(s, s[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = acc[-1] * t
    for i in range(1, len(s)):
        if acc[i] >= tot:
            u = (tot - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
            a, b = s[i - 1], s[i]
            p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
            m = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
            return p, ((b[0] - a[0]) / m, (b[1] - a[1]) / m)
    return s[-1], (0, 1)


def bract(p, d, side, L=15, W=4.6):
    nx, ny = -d[1] * side, d[0] * side
    ax, ay = d[0] * 0.86 + nx * 0.5, d[1] * 0.86 + ny * 0.5
    m = math.hypot(ax, ay)
    ax, ay = ax / m, ay / m
    px, py = -ay, ax
    b = (p[0] - ax * 3, p[1] - ay * 3)

    def at(t, w):
        return (b[0] + ax * L * t + px * W * w, b[1] + ay * L * t + py * W * w)
    pts = [b, at(.18, .8), at(.5, 1.0), at(.8, .72), at(1, 0), at(.8, -.72), at(.5, -1.0), at(.18, -.8)]
    half = [b, at(.18, .8), at(.5, 1.0), at(.8, .72), at(1, 0), at(.55, 0)]
    return (f'<path d="{cr_path(pts, sharp={0, 4})}" fill="{BRACT_SH}"/>'
            f'<path d="{cr_path(half, sharp={0, 4, 5})}" fill="{BRACT}"/>')


def bell_def():
    """Pendent urn-shaped flower at the origin hanging along +y (pedicel + bell + sepals)."""
    ped = 9
    L, W = 23, 8.6

    def at(t, w):
        return (W * w, ped + L * t)
    body = [at(0, 0), at(.12, .62), at(.45, .98), at(.8, .92), at(1, .78),
            at(1.0, -.78), at(.8, -.92), at(.45, -.98), at(.12, -.62)]
    sh = [at(0, 0), at(.45, 0.05), at(.8, 0.02), at(1, 0.0), at(1.0, -.78), at(.8, -.92),
          at(.45, -.98), at(.12, -.62)]
    sep = [at(-.05, 0), at(.1, .72), at(.34, .56), at(.16, 0), at(.34, -.56), at(.1, -.72)]
    mouth = [at(1.0, .8), at(1.1, .44), at(1.16, 0), at(1.1, -.44), at(1.0, -.8), at(.92, 0)]
    return "".join([
        f'<path d="{ribbon([(0, 0), (1.2, ped / 2), (0, ped + 1)], 2.8, 2.2)}" fill="{STALK}"/>',
        f'<path d="{cr_path(body, sharp={0, 4, 5})}" fill="{BELL}"/>',
        f'<path d="{cr_path(sh, sharp={0, 3, 4})}" fill="{BELL_SH}"/>',
        f'<path d="{cr_path(mouth, sharp={0, 4})}" fill="{P["mustard"]}"/>',
        f'<path d="{cr_path(sep, sharp={0, 1, 2, 3, 4, 5})}" fill="{RAMP[4]}"/>',
    ])


def tip_bud(p, d, turn=0.0, s=1.0):
    """Small unopened bud closing the raceme tip: its base sits over the end of the
    stalk (hiding the stalk's round end), pointing on along the stalk, turned
    `turn` degrees away from the last open bell. Coral like the bells, with a
    shaded half and a little green sepal collar, all above the print minimums."""
    a = math.degrees(math.atan2(d[1], d[0])) - 90 + turn
    L, W = 12.5, 3.5

    def at(t, w):
        return (W * w, L * t - 2.5)
    body = [at(0, 0), at(.2, .84), at(.48, 1.0), at(.76, .6), at(1, 0),
            at(.76, -.6), at(.48, -1.0), at(.2, -.84)]
    sh = [at(0, 0), at(.5, .06), at(1, 0), at(.76, -.6), at(.48, -1.0), at(.2, -.84)]
    col = [at(-.02, 0), at(.14, 1.05), at(.34, .72), at(.22, 0), at(.34, -.72), at(.14, -1.05)]
    return (f'<g transform="translate({f(p[0])} {f(p[1])}) rotate({a:.0f}) scale({s:g})">'
            f'<path d="{cr_path(body, sharp={0, 4})}" fill="{BELL}"/>'
            f'<path d="{cr_path(sh, sharp={0, 2})}" fill="{BELL_SH}"/>'
            f'<path d="{cr_path(col, sharp={0, 1, 2, 3, 4, 5})}" fill="{RAMP[4]}"/></g>')


def stalk_svg(pts, w0, w1, bracts, flowers, rise_side=1, bud_turn=0.0):
    cid = uid("q")
    sd = ribbon(pts, w0, w1, per=5)
    out = [f'<path id="{cid}p" d="{sd}" fill="{STALK}"/>']
    sh_pts = [(a[0] + 0.42 * w0, a[1] + 0.1 * w0) for a in pts]
    out.append(f'<clipPath id="{cid}"><use href="#{cid}p"/></clipPath>'
               f'<path clip-path="url(#{cid})" d="{ribbon(sh_pts, w0 * 0.7, w1 * 0.7, per=5)}" '
               f'fill="{STALK_SH}"/>')
    for i, t in enumerate(bracts):
        p, d = along(pts, t)
        out.append(bract(p, d, (-1) ** i * rise_side, L=22 - 6 * t, W=6.0 - 1.6 * t))
    for t, hang, s in flowers:
        p, d = along(pts, t)
        ang = math.degrees(math.atan2(-hang[0], hang[1]))
        out.append(f'<use href="#bell" transform="translate({f(p[0])} {f(p[1])}) '
                   f'rotate({ang:.0f}) scale({s:g})"/>')
    p, d = along(pts, 1.0)
    out.append(tip_bud(p, d, bud_turn))
    return "".join(out)


# ------------------------------------------------------------------ build
RC = (300, 548)          # rosette centre (soil level of the rosette, projected)
# x, y, scale (drawn PLANT_DY lower, like the rosette): a larger pup on the left and a clearly smaller
# one lower down on the right, so the two do not pair up either side of the rim like ears
PUPS = [(210, 612, .34), (404, 634, .21)]
PLANT_DY = 12            # rosette + pups + stalks sit this much lower (the shallow bowl's rim is at RIM_Y)


def build():
    reset_ids()
    back, front = pot(kind="bowl", cx=CX, rim_y=RIM_Y, bottom=752, rx=POT_RX, rim_h=RIM_H,
                      base_w=67)
    # tall stalk: rises from the leaf axils behind the heart, arches right and nods
    stalk1 = [(314, 516), (318, 420), (320, 322), (330, 240), (354, 176), (392, 144), (432, 148),
              (460, 174), (468, 204)]
    stalk2 = [(270, 520), (258, 466), (238, 416), (208, 384), (178, 376), (156, 388), (148, 408)]
    fl1 = [(0.58, (0.18, 1), 1.08), (0.66, (0.12, 1), 1.06), (0.74, (0.04, 1), 1.02),
           (0.81, (-0.08, 1), 0.98), (0.875, (-0.25, 1), 0.92), (0.935, (-0.45, 1), 0.84),
           (0.99, (-0.7, 1), 0.76)]
    fl2 = [(0.64, (-0.08, 1), 1.0), (0.77, (-0.06, 1), 0.94), (0.89, (0.12, 1), 0.86),
           (1.0, (0.45, 1), 0.76)]

    def stalks():
        return (stalk_svg(stalk2, 8.0, 4.4, [0.40], fl2, rise_side=-1, bud_turn=16)
                + stalk_svg(stalk1, 9.0, 4.6, [0.30, 0.44], fl1, bud_turn=-34))

    main = rosette(*RC, hook=stalks, hook_after=1, bud=(7, 5), blush_rings=BLUSH_RINGS)
    # the pups' outer ring is a step lighter (RAMP[4]) than the rosette's outer leaves behind them
    pup_rings = [(7, 10, 24, 150, .40, 4, 0), (6, 34, 20, 112, .42, 5, 30),
                 (5, 56, 14, 72, .46, 7, 10), (3, 76, 8, 40, .52, 8, 40)]
    pup = rosette(0, 0, 1.0, pup_rings, k=0.22, ps=MMU * min(p[2] for p in PUPS), bud=(15, 11))
    defs = f'<defs><g id="bell">{bell_def()}</g><g id="pup">{pup}</g></defs>'
    pups = "".join(f'<use href="#pup" transform="translate({x} {y}) scale({s:g})"/>'
                   for x, y, s in PUPS)
    return defs + back + front + f'<g transform="translate(0 {PLANT_DY})">' + main + pups + "</g>"


if __name__ == "__main__":
    doc = svg_doc(build(), "Echeveria elegans")
    out = os.path.join(os.path.dirname(HERE), "out", "echeveria_elegans.svg")
    with open(out, "w") as fh:
        fh.write(doc)
    print(out, len(doc))
