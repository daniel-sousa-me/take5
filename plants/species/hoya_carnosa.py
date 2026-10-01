"""Hoya carnosa (wax plant) -- v4.

A woven natural-fibre hoop rises from the pot. Stem A twines clockwise up the
left leg and over the top of the hoop; stem B twines up the right leg, then leaves
the hoop and trails down on the right; stem C drapes over the front of the rim.
Thick waxy opposite leaves in pairs at the nodes (some with fine pale speckles,
spread over both sides of the hoop);
two hemispherical umbels of blush star flowers with red coronas hang on short
peduncles.

Leaves are drawn once per (shape, tone, lit side, speckle) in <defs> at a unit
length of 60 px and placed with <use> (keeps the file small).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import PAL, Leaf, cr_path, cr_sample, ribbon, f, pot, svg_doc, reset_ids  # noqa: E402

P = PAL
# fill, turned-away half, sheen, midrib, speckle -- the last three are pre-blended
# solids (cream @17 %, pale @42 %, spot @36 % over the fill): the card face allows no
# transparency and faint overlays vanish in pigment print.
TONES = {
    "deep": ("#314B37", "#27392C", "#526753", "#71846F", "#73816E"),
    "forest": ("#405D43", "#34503A", "#5F755D", "#7A8E76", "#7C8D76"),
    "mid": ("#5B7458", "#4B6349", "#75896F", "#899B82", "#8E9C84"),
    "sage": ("#7F9273", "#6A7E60", "#93A185", "#9EAD92", "#A5AF95"),
    "light": ("#A5B296", "#8E9E80", "#B3BCA2", "#B4BFA6", "#BDC3AB"),
}
STEM = "#8E9E80"
HOOP = P["terra_dark"]
HOOP_WRAP = "#774C37"  # soil over terra_dark @50 %, pre-blended
PETAL = "#ECD6CD"      # pale blush tint, L* 87.2 (white stock: visible tints stay <= L* 88)
PETAL_SH = "#E4C3BB"
PETAL_BK = "#DDB0AA"
CORONA = P["red"]
CORONA_C = P["wine"]
PEDICEL = P["rose"]
UL = 60.0  # unit leaf length in defs
SCALE = 1.26  # global leaf size factor


def rad(a):
    return math.radians(a)


def dir_of(a):
    return (math.sin(rad(a)), -math.cos(rad(a)))


def ang_of(v):
    return math.degrees(math.atan2(v[0], -v[1]))


# ------------------------------------------------------------------ polyline
class Path:
    """arclength-parametrised dense polyline"""

    def __init__(self, pts, per=30, raw=False):
        self.s = list(pts) if raw else cr_sample(pts, per)
        self.acc = [0.0]
        for a, b in zip(self.s, self.s[1:]):
            self.acc.append(self.acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        self.L = self.acc[-1]

    def at(self, d):
        d = max(0.0, min(self.L, d))
        lo, hi = 0, len(self.acc) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if self.acc[m] < d:
                lo = m
            else:
                hi = m
        a, b = self.s[lo], self.s[hi]
        u = (d - self.acc[lo]) / ((self.acc[hi] - self.acc[lo]) or 1)
        p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        return p, (dx / m, dy / m)


# ------------------------------------------------------------------ hoop
_HOOP0 = [(268, 612), (268, 560), (262, 505), (236, 462), (198, 420), (176, 360), (172, 292),
          (186, 224), (220, 170), (262, 140), (304, 132), (346, 142), (384, 172), (414, 222),
          (428, 292), (424, 360), (402, 420), (364, 462), (338, 505), (332, 560), (332, 612)]


def _hand_bent(p):
    """a hand-bent cane, not a drawn ellipse: the loop leans a little left, its left
    shoulder sits higher and fuller than the right, the right flank is flatter"""
    x, y = p
    h = max(0.0, (612 - y) / 480.0)
    x -= 22 * h * h
    if x < 300:
        x -= 6 * math.sin(math.pi * min(1.0, h * 1.25))
        y -= 8 * h * h
    else:
        x -= 7 * math.sin(math.pi * min(1.0, h * 1.6)) * (1 - h)
        y += 4 * h * h
    return (x, y)


HOOP_PTS = [_hand_bent(p) for p in _HOOP0]
CX, CY = 300, 300
HP = Path(HOOP_PTS)


def outward(p, t):
    n = (-t[1], t[0])
    if (p[0] - CX) * n[0] + (p[1] - CY) * n[1] < 0:
        n = (-n[0], -n[1])
    return n


def hoop_svg():
    d = cr_path(HOOP_PTS, closed=False)
    return (f'<path d="{d}" fill="none" stroke="{HOOP}" stroke-width="7.5" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{HOOP_WRAP}" stroke-width="7.5" stroke-dasharray="3 4.5"/>')


# ------------------------------------------------------------------ stems
class Stem:
    """Twines around the hoop from arclength d0 towards d1 (winding sine offset),
    then optionally continues free along `tail` points."""

    def __init__(self, d0, d1, tail=None, amp=7.5, period=125, phase=0.0, w0=5.0, w1=2.2, base=12):
        self.amp, self.period, self.phase = amp, period, phase
        self.base = base  # below this the stem is in front (rises from the soil before the cane)
        sg = 1 if d1 > d0 else -1
        n = max(1, int(abs(d1 - d0) / 3))
        pts = []
        for i in range(n + 1):
            s = abs(d1 - d0) * i / n
            p, t = HP.at(d0 + sg * s)
            nn = outward(p, t)
            w = self.wave(s)
            pts.append((p[0] + nn[0] * amp * w, p[1] + nn[1] * amp * w))
        self.hoop_len = abs(d1 - d0)
        if tail:
            # blend from the last hoop point into the free tail
            # (leading out along the vine's last direction of travel: no kink where it leaves)
            a, b = pts[-6], pts[-1]
            m = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
            lead = (b[0] + (b[0] - a[0]) / m * 14, b[1] + (b[1] - a[1]) / m * 14)
            tp = cr_sample([pts[-1], lead] + tail, 16)
            pts += tp[1:]
        self.path = Path(pts, raw=True)
        self.L = self.path.L
        self.hoop_len = min(self.hoop_len, self.L)
        self.w0, self.w1 = w0, w1

    def theta(self, s):
        # irregular twining: the pitch drifts (tight turns, then a lazy stretch)
        return 2 * math.pi * s / self.period + self.phase + 0.7 * math.sin(s / 160.0 + self.phase * 1.7)

    def wave(self, s):
        ramp = min(1.0, s / 110.0) ** 1.5  # leaves the soil straight, the winding builds up slowly
        # loose: the vine drifts off the cane by varying amounts, now hugging it, now
        # swinging out in a slack loop
        a = 0.75 + 0.45 * (0.5 + 0.5 * math.sin(s / 140.0 + self.phase * 2.3)) ** 2
        return ramp * a * math.sin(self.theta(s))

    def _base_switch(self):
        """the stem stays in front from the soil until the first place past `base`
        where it is swung fully off the cane, so it first slips behind there (a
        clean cross, not a cut while it still lies on the cane)"""
        if not hasattr(self, "_b2"):
            x = self.base
            while x < self.base + 400 and not (abs(self.wave(x)) > 0.9 and math.cos(self.theta(x)) <= 0):
                x += 0.5
            self._b2 = x
        return self._b2

    def front(self, s):
        if s > self.hoop_len or s < self.base:
            return True
        if s < self._base_switch():
            return True
        return math.cos(self.theta(s)) > 0

    def at(self, s):
        return self.path.at(s)

    def width(self, s):
        # linear taper, but never under 3 units (print minimum) until the last
        # 30 units, where it runs out to a fine growing tip
        lin = self.w0 + (self.w1 - self.w0) * min(1, s / self.L)
        tip = self.w1 + (3.0 - self.w1) * min(1.0, max(0.0, (self.L - s) / 30.0))
        return max(lin, min(3.0, tip)) if self.w0 >= 3.0 else lin

    def ribbon_ab(self, a, b):
        """filled ribbon between arclengths a..b with the stem's own width profile"""
        k = max(3, int((b - a) / 16))
        ss = [a + (b - a) * i / k for i in range(k + 1)]
        L, R = [], []
        for s_ in ss:
            p, t = self.at(s_)
            w = self.width(s_) / 2
            L.append((p[0] - t[1] * w, p[1] + t[0] * w))
            R.append((p[0] + t[1] * w, p[1] - t[0] * w))
        ring = L + R[::-1]
        return cr_path(ring, closed=True, sharp={0, len(L) - 1, len(L), len(ring) - 1})

    def part(self, a, b):
        return f'<path d="{self.ribbon_ab(a, b)}" fill="{STEM}"/>'

    def runs(self, front, step=0.5):
        """[(a, b)] arclength runs where the stem is in front (or behind) of the hoop"""
        n = int(self.L / step)
        out, a = [], None
        for i in range(n + 1):
            s = i * self.L / n
            if self.front(s) == front:
                if a is None:
                    a = s
            elif a is not None:
                out.append((a, s))
                a = None
        if a is not None:
            out.append((a, self.L))
        if front and self.hoop_len > 0:
            # where the stem leaves the hoop it is still centred on the cane: it comes
            # out from behind the cane, so its front copy starts only once clear of it
            hw = 3.75
            for i, (a, b) in enumerate(out):
                if abs(a - self.hoop_len) < 1:
                    s = a
                    while s < b:
                        p, _ = self.at(s)
                        dq = min(math.hypot(h[0] - p[0], h[1] - p[1]) for h in HP.s)
                        if dq > hw + self.width(s) / 2 + 0.5:
                            break
                        s += 0.5
                    out[i] = (s, b)
        return out

    def run_mask(self, a, b, pad=4.0, bevel=5.0):
        """polygon over the stem between a..b, padded sideways. At a switch the end
        is bevelled: the side facing the cane stops `bevel` early, the outer side runs
        `bevel` on, so the stem's inner edge slips behind the cane edge in a taper
        instead of a square step."""
        def inner_is_L(s_):
            p, t = self.at(s_)
            q = min(HP.s, key=lambda h: (h[0] - p[0]) ** 2 + (h[1] - p[1]) ** 2)
            return (q[0] - p[0]) * -t[1] + (q[1] - p[1]) * t[0] > 0

        ends = {}
        for e, sg in ((a, 1), (b, -1)):
            if 0 < e < self.L and abs(e - self.hoop_len) > 0.6:
                il = inner_is_L(e)
                ends[sg] = (e + sg * bevel, e - sg * bevel) if il else (e - sg * bevel, e + sg * bevel)
            else:
                ends[sg] = (e, e)
        (la, ra), (lb, rb) = ends[1], ends[-1]

        def side(s0, s1, sgn):
            s0, s1 = max(0.0, s0), min(self.L, s1)
            n = max(2, int((s1 - s0) / 5.0))
            out = []
            for i in range(n + 1):
                s_ = s0 + (s1 - s0) * i / n
                p, t = self.at(s_)
                w = (self.width(s_) / 2 + pad) * sgn
                out.append((p[0] - t[1] * w, p[1] + t[0] * w))
            return out
        ring = side(la, lb, 1) + side(ra, rb, -1)[::-1]
        return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in ring) + "Z"

    def pieces(self, front):
        step = 3.0
        n = int(self.L / step)
        ss = [i * self.L / n for i in range(n + 1)]
        runs, run = [], []
        for s in ss:
            if self.front(s) == front:
                run.append(s)
            else:
                if run:
                    runs.append(run)
                run = []
        if run:
            runs.append(run)
        svg = []
        for r in runs:
            a = max(0.0, r[0] - (3 if r[0] > 0 else 0))
            b = min(self.L, r[-1] + 3)
            if b - a < 3:
                continue
            svg.append(self.ribbon_ab(a, b))
        if not svg:
            return ""
        return f'<path d="{"".join(svg)}" fill="{STEM}"/>'


# ------------------------------------------------------------------ leaves
def hoya_leaf(var):
    wide, bend = {0: (1.0, 0.0), 1: (0.9, 0.05), 2: (0.9, -0.05), 3: (1.08, 0.02)}[var]
    r = [(0.03, 0.10), (0.12, 0.22), (0.28, 0.29), (0.46, 0.30), (0.64, 0.26),
         (0.80, 0.18), (0.915, 0.088), (0.972, 0.026)]
    r = [(t, w * wide) for t, w in r]
    return Leaf(UL, r, bend=bend, tip_sharp=True, base_sharp=False)


DEFS = {}


def half(lf, side):
    sg = 1 if side == "r" else -1
    ts = (-0.2, 0.2, 0.45, 0.7, 0.9, 1.2)
    pts = [lf.axis(t) for t in ts] + [lf.pt(t, sg * 0.6) for t in ts[::-1]]
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts) + "Z"


def leaf_def(var, tone, shade_side, speck, ribw=0.0):
    key = (var, tone, shade_side, speck, ribw)
    if key in DEFS:
        return DEFS[key][0]
    lid = f"hl{len(DEFS)}"
    lf = hoya_leaf(var)
    fill, sh, sheen, rib, spk = TONES[tone]
    d = lf.path()
    cid = f"hk{var}"
    o = []
    if not any(k[0] == var for k in DEFS):
        o.append(f'<path id="hp{var}" d="{d}"/><clipPath id="{cid}"><use href="#hp{var}"/></clipPath>')
    o += [f'<g id="{lid}">',
          f'<use href="#hp{var}" fill="{fill}"/><g clip-path="url(#{cid})">',
          f'<path d="{half(lf, shade_side)}" fill="{sh}"/>']
    lit = "l" if shade_side == "r" else "r"
    sg = 1 if lit == "r" else -1
    a = [lf.pt(t, sg * lf.width(t, lit) * 0.68) for t in (0.2, 0.36, 0.54, 0.70)]
    b = [lf.pt(t, sg * lf.width(t, lit) * 0.42) for t in (0.62, 0.46, 0.30)]
    if ribw:  # (small tip leaves: no sheen -- it would print as a sub-minimum sliver)
        o.append(f'<path d="{cr_path(a + b, closed=True, sharp={0, 3})}" fill="{sheen}"/>')
    if speck and ribw:
        rnd = random.Random(speck * 31 + var)
        dd = []
        # a few bold silver flecks, loosely scattered (>= 4.6 units across on the
        # card whatever the leaf scale); low-contrast so they read as texture
        pts = []
        tries = 0
        while len(pts) < 4 and tries < 200:
            tries += 1
            t = rnd.uniform(0.16, 0.8)
            side = rnd.choice(("r", "l"))
            g = 1 if side == "r" else -1
            p = lf.pt(t, g * lf.width(t, side) * rnd.uniform(0.3, 0.7))
            if all(math.hypot(p[0] - q[0], p[1] - q[1]) > 11 for q in pts):
                pts.append(p)
        for p in pts:
            r = ribw * rnd.uniform(1.1, 1.35)
            k = r * 0.5523  # circle as four cubics (arcs measure as zero-area chords in print_prep)
            x, y = p
            dd.append(f"M{f(x - r)} {f(y)}C{f(x - r)} {f(y - k)} {f(x - k)} {f(y - r)} {f(x)} {f(y - r)}"
                      f"C{f(x + k)} {f(y - r)} {f(x + r)} {f(y - k)} {f(x + r)} {f(y)}"
                      f"C{f(x + r)} {f(y + k)} {f(x + k)} {f(y + r)} {f(x)} {f(y + r)}"
                      f"C{f(x - k)} {f(y + r)} {f(x - r)} {f(y + k)} {f(x - r)} {f(y)}Z")
        o.append(f'<path d="{"".join(dd)}" fill="{spk}"/>')
    # midrib as a filled taper (not a hairline stroke) so the print pass keeps it
    # exactly as drawn instead of fattening it into a heavy pale bar
    # ribw = half-width at the base in def units, chosen per leaf so the rib is
    # >= 4 units wide on the card (0 = small tip leaf, no rib)
    if ribw:
        a0, a1, a2 = lf.axis(0.0), lf.axis(0.45), lf.axis(0.86)
        h = ribw
        o.append(f'<path d="M{f(a0[0] - h)} {f(a0[1])}Q{f(a1[0] - h * .75)} {f(a1[1])} {f(a2[0])} {f(a2[1])}'
                 f'Q{f(a1[0] + h * .75)} {f(a1[1])} {f(a0[0] + h)} {f(a0[1])}Z" fill="{rib}"/>')
    o.append("</g></g>")
    DEFS[key] = (lid, "".join(o))
    return lid


def place_leaf(node, ang, L, tone, var=0, speck=0, pl=None):
    """petiole from `node` along angle `ang` (0 = up, clockwise); returns
    (petiole, leaf, petiole_stub).  The petiole is ~0.17 L long (hoya petioles
    are short but distinct) so it always shows between vine and blade; the
    stub is the same petiole stopped at the blade base, drawn in front of the
    hoop for leaves that sit behind it (so their join is never hidden)."""
    if pl is None:
        pl = 5 + L * 0.12
    dv = dir_of(ang)
    q = (node[0] + dv[0] * pl, node[1] + dv[1] * pl)
    tuck = (q[0] + dv[0] * L * 0.1, q[1] + dv[1] * L * 0.1)
    edge = (q[0] + dv[0] * 1.2, q[1] + dv[1] * 1.2)
    back = (node[0] - dv[0] * 1.5, node[1] - dv[1] * 1.5)
    w = max(3.9, L * 0.05)  # pale stem on paper = knockout line: >= 0.20 mm printed
    pet = (f'<path d="M{f(back[0])} {f(back[1])}L{f(tuck[0])} {f(tuck[1])}" stroke-width="{f(w)}"/>')
    stub = (f'<path d="M{f(back[0])} {f(back[1])}L{f(edge[0])} {f(edge[1])}" stroke-width="{f(w)}"/>')
    shade_side = "r" if math.cos(rad(ang)) > 0 else "l"
    s = L / UL
    ribw = round(2.1 / s * 4) / 4 if L >= 44 else 0.0
    lid = leaf_def(var, tone, shade_side, speck, ribw)
    use = f'<use href="#{lid}" transform="translate({f(q[0])} {f(q[1])}) rotate({f(ang)}) scale({s:.3f})"/>'
    return pet, use, stub


# ------------------------------------------------------------------ flowers
def star_d(r_out, r_in, rot=-90, soft=0.35):
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        a = rad(rot + i * 36)
        pts.append((r * math.cos(a), r * math.sin(a)))
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for i in range(10):
        a, b = pts[i], pts[(i + 1) % 10]
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        c = (m[0] * (1 + soft * 0.35), m[1] * (1 + soft * 0.35))
        d += f"Q{f(c[0])} {f(c[1])} {f(b[0])} {f(b[1])}"
    return d + "Z"


def flower_defs(R=13.0):
    petals = star_d(R, R * 0.5)
    corona = star_d(R * 0.5, R * 0.24, rot=-54, soft=0.1)
    return (f'<clipPath id="hfc"><path d="{petals}"/></clipPath>'
            f'<g id="hf"><path d="{petals}" fill="{PETAL}"/>'
            f'<path d="M0 -14L14 -14L14 14L0 14Z" transform="rotate(-20)" fill="{PETAL_SH}" clip-path="url(#hfc)"/>'
            f'<path d="{corona}" fill="{CORONA}"/><circle r="2.6" fill="{CORONA_C}"/></g>'
            f'<g id="hfb"><path d="{petals}" fill="{PETAL_BK}"/>'
            f'<path d="{corona}" fill="{P["burgundy"]}"/></g>')


def umbel(anchor, R=32, n=40, seed=1, tilt=0.0):
    """hanging hemispherical umbel; anchor = top of the ball (peduncle end)."""
    rnd = random.Random(seed)
    c = (anchor[0], anchor[1] + R * 0.62)
    golden = math.pi * (3 - math.sqrt(5))
    items = []
    for i in range(n):
        y = 1 - (i + 0.5) / n * 2
        r = math.sqrt(max(0, 1 - y * y))
        th = i * golden + seed
        v = (math.cos(th) * r, -y, math.sin(th) * r)  # x, y (down +), z (toward viewer)
        if v[1] < -0.5 or v[2] < -0.15:
            continue
        ca, sa = math.cos(tilt), math.sin(tilt)
        v = (v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca, v[2])
        items.append(v)
    items.sort(key=lambda v: v[2])
    fl = []
    for v in items:
        p = (c[0] + v[0] * R, c[1] + v[1] * R * 0.9)
        fore = max(0.5, math.sqrt(max(0.0, v[2])) if v[2] > 0 else 0.5)
        a = math.degrees(math.atan2(v[1], v[0]))
        spin = rnd.uniform(0, 72)
        use = "hf" if v[2] > 0.2 else "hfb"
        s = 0.94 + 0.12 * rnd.random()
        fl.append(f'<use href="#{use}" transform="translate({f(p[0])} {f(p[1])}) rotate({f(a)}) '
                  f'scale({fore * s:.2f} {s:.2f}) rotate({f(spin - a)})"/>')
    core_ = (f'<ellipse cx="{f(c[0])}" cy="{f(c[1] + R * 0.12)}" rx="{f(R * 0.78)}" ry="{f(R * 0.6)}" '
             f'fill="{P["rose"]}"/>')
    return core_ + "".join(fl)


def peduncle(node, top, R, w=3.6):
    """From the node down into the umbel's centre (its end is hidden under the ball)."""
    end = (top[0], top[1] + R * 0.62)
    # one smooth arc: out from the node, then hanging straight down into the ball
    mid = (node[0] * 0.3 + end[0] * 0.7, node[1] * 0.55 + top[1] * 0.45)
    return f'<path d="{ribbon([node, mid, end], w, 3.0, per=8)}" fill="{PEDICEL}"/>'


# ------------------------------------------------------------------ layout
# per stem: list of nodes (s, [leaf...]); leaf = (a, L, tone, layer, var, speck)
# a = angle relative to the stem's direction of travel (+ = right of travel)
# layer: 0 = behind the hoop, 1 = in front
A_NODES = [
    (92, [(-58, 50, "mid", 1, 1, 0), (62, 42, "deep", 0, 2, 0)]),
    (182, [(-66, 64, "sage", 1, 3, 1), (48, 50, "forest", 0, 1, 0)]),
    (292, [(-78, 68, "forest", 1, 0, 0), (70, 46, "deep", 0, 2, 0)]),
    (372, [(-52, 58, "light", 1, 2, 2), (100, 40, "forest", 0, 1, 0)]),
    (478, [(-38, 60, "mid", 1, 1, 3), (58, 44, "deep", 0, 0, 0)]),
    (590, [(-40, 66, "sage", 1, 2, 0), (58, 50, "forest", 0, 1, 4)]),
    (700, [(-62, 58, "forest", 1, 3, 9), (46, 46, "mid", 0, 2, 0)]),
    (782, [(-50, 44, "light", 1, 1, 0), (40, 36, "deep", 0, 2, 0)]),
    (846, [(-64, 40, "mid", 1, 2, 0), (54, 32, "forest", 0, 1, 0)]),
    (-5, [(-46, 19, "sage", 1, 0, 0), (50, 16, "mid", 1, 0, 0)]),  # growing tip: ends in a young pair
]
B_NODES = [
    (70, [(62, 48, "forest", 1, 2, 0), (-58, 40, "deep", 0, 1, 0)]),
    (165, [(58, 60, "sage", 1, 1, 5), (-66, 46, "forest", 0, 2, 0)]),
    (262, [(-70, 54, "mid", 1, 3, 10), (76, 44, "forest", 1, 0, 0)]),  # dark leaf behind umbel 2 (pale stem reads on it)
    (352, [(-60, 48, "light", 1, 2, 6), (68, 44, "forest", 1, 1, 0)]),
    (420, [(-56, 34, "sage", 1, 2, 0), (60, 30, "mid", 1, 1, 0)]),
    (-5, [(-40, 20, "light", 1, 0, 0), (44, 17, "sage", 1, 0, 0)]),
]
D_NODES = [  # short side shoot branching off A across the hoop interior
    (46, [(-64, 50, "mid", 1, 1, 0), (70, 42, "deep", 1, 2, 0)]),
    (104, [(-58, 44, "light", 1, 3, 8), (62, 38, "forest", 1, 1, 0)]),
    (-4, [(-44, 22, "sage", 1, 0, 0), (48, 19, "mid", 1, 0, 0)]),
]
E_NODES = [  # escaping runner: one young pair, then bare (hoya runners leaf out late)
    (66, [(-62, 28, "sage", 1, 2, 0), (66, 24, "mid", 1, 1, 0)]),
    (132, [(-92, 13, "light", 1, 0, 0), (66, 12, "sage", 1, 0, 0)]),
]
C_NODES = [
    (70, [(-70, 40, "sage", 1, 1, 0), (64, 36, "forest", 1, 2, 7)]),
    (132, [(-62, 34, "mid", 1, 2, 0), (70, 32, "light", 1, 1, 0)]),
    (-4, [(-34, 22, "sage", 1, 0, 0), (36, 20, "forest", 1, 0, 0)]),
]


def snap_front(st, s):
    """Move a node to the nearest place where the vine passes in front of the
    hoop, so the leaf's join is visible (not tucked behind the hoop)."""
    if st.hoop_len <= 0 or st.front(s):
        return s
    for k in range(1, 60):
        for c in (s + k, s - k):
            if 0 < c < st.L - 2 and st.front(c) and st.front(c + 4 if c > s else c - 4):
                return c + (4 if c > s else -4)
    return s


def nodes_svg(st, nodes, rnd):
    back, front, stubs = [], [], []
    for s, leaves in nodes:
        if s < 0:  # measured back from the tip: a shoot ends in its young leaf pair
            s = st.L + s
        if s > st.L - 2:
            continue
        s = snap_front(st, s)
        node, t = st.at(s)
        tang = ang_of(t)
        for a, L, tone, layer, var, speck in leaves:
            L *= SCALE
            ang = tang + a + rnd.uniform(-5, 5)
            pet, use, stub = place_leaf(node, ang, L, tone, var, speck)
            if layer:
                front.append((pet, use))
            else:
                back.append((pet, use))
                stubs.append(stub)
    return back, front, stubs


def emit(pairs):
    if not pairs:
        return ""
    pets = "".join(p for p, _ in pairs)
    return (f'<g stroke="{STEM}" stroke-linecap="round" fill="none">{pets}</g>'
            + "".join(u for _, u in pairs))


def emit_stubs(stubs):
    if not stubs:
        return ""
    return f'<g stroke="{STEM}" stroke-linecap="round" fill="none">{"".join(stubs)}</g>'


def build():
    DEFS.clear()
    back, front = pot("classic", rx=100, rim_y=588, base_w=71, band=True)  # rx 98 -> 100: printed rim back to ~10.3 mm after the deck scale change
    rnd = random.Random(7)
    HL = HP.L
    # A leaves the hoop on the right and ends in a free, tapering growing tip
    # A leaves the hoop on the right as a free shoot that reaches out and curls upward,
    # still searching for support
    A = Stem(0, 806, tail=[(438, 310), (462, 316), (484, 308), (498, 292)],
             phase=0.4, w0=6, w1=0.9, base=56)
    B = Stem(HL, HL - 190, tail=[(424, 446), (462, 468), (488, 504), (499, 546), (500, 588), (492, 620), (476, 640)],
             phase=2.3, w0=5.6, w1=2.2, base=32)
    C = Stem(0, 0, w0=4.2, w1=1.8)
    C.path = Path([(268, 594), (246, 603), (222, 617), (204, 638), (192, 666), (192, 694),
                   (204, 716), (220, 728)], per=20)
    C.L = C.path.L
    C.hoop_len = 0

    d0, _ = A.at(240)
    D = Stem(0, 0, w0=3.6, w1=1.6)
    D.path = Path([d0, (224, 396), (262, 378), (296, 350), (318, 318), (326, 292)], per=20)
    D.L = D.path.L
    D.hoop_len = 0

    ab, af, ast = nodes_svg(A, A_NODES, rnd)
    db, df, dst = nodes_svg(D, D_NODES, rnd)
    bb, bf, bst = nodes_svg(B, B_NODES, rnd)
    cb, cf, cst = nodes_svg(C, C_NODES, rnd)

    # umbel 1: from a node near the top-left, hangs inside the hoop
    n1, _ = A.at(478)
    u1_top = (n1[0] + 20, n1[1] + 34)
    # umbel 2: from a node on the trailing tail of B
    n2, _ = B.at(262)
    u2_top = (n2[0] - 30, n2[1] + 22)

    body = []
    body.append(back)
    body.append(emit(ab + bb))
    # A and B: each stem is ONE continuous ribbon drawn behind the hoop, plus an
    # identical copy in front of it clipped to the runs where the stem passes in
    # front. Outside the cane both copies coincide, so the wraps have no seams,
    # nubs or square cuts: a stem simply disappears behind the cane.
    fm = "hfm"
    masks = "".join(st.run_mask(a, b) for st in (A, B) for a, b in st.runs(True))
    body.append(f'<path id="hstm" d="{A.ribbon_ab(0, A.L)}{B.ribbon_ab(0, B.L)}" fill="{STEM}"/>')
    full = '<use href="#hstm"/>'
    body.append(C.part(0, 14))
    body.append(hoop_svg())
    body.append(f'<clipPath id="{fm}"><path d="{masks}"/></clipPath><g clip-path="url(#{fm})">{full}</g>')
    body.append(emit_stubs(ast + bst))
    body.append(D.part(0, D.L))
    body.append(emit(af + bf + df))
    body.append(peduncle(n1, u1_top, 36))
    body.append(umbel(u1_top, R=36, seed=2, tilt=0.12))
    body.append(peduncle(n2, u2_top, 33))
    body.append(umbel(u2_top, R=33, seed=5, tilt=-0.1))
    body.append(front)
    body.append(C.part(10, C.L))
    body.append(emit(cb + cf) + emit_stubs(cst))
    defs = "<defs>" + flower_defs() + "".join(v[1] for v in DEFS.values()) + "</defs>"
    return defs + "".join(body)


if __name__ == "__main__":
    reset_ids()
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "..", "out", "hoya_carnosa.svg")
    open(dst, "w").write(svg_doc(build(), "Hoya carnosa (wax plant)"))
    print("wrote", os.path.normpath(dst), os.path.getsize(dst), "bytes")
