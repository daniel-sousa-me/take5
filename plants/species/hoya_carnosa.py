"""Hoya carnosa (wax plant) -- v4.

A woven natural-fibre hoop rises from the pot. Stem A twines clockwise up the
left leg and over the top of the hoop; stem B twines up the right leg, then leaves
the hoop and trails down on the right; stem C drapes over the front of the rim.
Thick waxy opposite leaves in pairs at the nodes (some with fine pale speckles);
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
TONES = {  # fill, turned-away half, sheen opacity
    "deep": ("#314B37", "#27392C", 0.10),
    "forest": ("#405D43", "#34503A", 0.11),
    "mid": ("#5B7458", "#4B6349", 0.12),
    "sage": ("#7F9273", "#6A7E60", 0.14),
    "light": ("#A5B296", "#8E9E80", 0.16),
}
STEM = "#8E9E80"
HOOP = P["terra_dark"]
HOOP_WRAP = P["soil"]
MIDRIB = P["pale"]
PETAL = "#F3E2DA"
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
HOOP_PTS = [(268, 612), (268, 560), (262, 505), (236, 462), (198, 420), (176, 360), (172, 292),
            (186, 224), (220, 170), (262, 140), (304, 132), (346, 142), (384, 172), (414, 222),
            (428, 292), (424, 360), (402, 420), (364, 462), (338, 505), (332, 560), (332, 612)]
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
            f'<path d="{d}" fill="none" stroke="{HOOP_WRAP}" stroke-width="7.5" stroke-dasharray="1.8 4.4" opacity=".5"/>'
            f'<path d="{d}" fill="none" stroke="{P["terra"]}" stroke-width="1.4" transform="translate(-1.2 -.8)" opacity=".6"/>')


# ------------------------------------------------------------------ stems
class Stem:
    """Twines around the hoop from arclength d0 towards d1 (winding sine offset),
    then optionally continues free along `tail` points."""

    def __init__(self, d0, d1, tail=None, amp=6.0, period=80, phase=0.0, w0=5.0, w1=2.2):
        self.amp, self.period, self.phase = amp, period, phase
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
            tp = cr_sample([pts[-1]] + tail, 16)
            pts += tp[1:]
        self.path = Path(pts, raw=True)
        self.L = self.path.L
        self.hoop_len = min(self.hoop_len, self.L)
        self.w0, self.w1 = w0, w1

    def wave(self, s):
        ramp = min(1.0, s / 40.0)
        return ramp * math.sin(2 * math.pi * s / self.period + self.phase)

    def front(self, s):
        if s > self.hoop_len or s < 12:
            return True
        return math.cos(2 * math.pi * s / self.period + self.phase) > 0

    def at(self, s):
        return self.path.at(s)

    def width(self, s):
        return self.w0 + (self.w1 - self.w0) * min(1, s / self.L)

    def part(self, a, b):
        k = max(2, int((b - a) / 16))
        pts = [self.at(a + (b - a) * i / k)[0] for i in range(k + 1)]
        return f'<path d="{ribbon(pts, self.width(a), self.width(b), per=4)}" fill="{STEM}"/>'

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
            k = max(2, int((b - a) / 16))
            pts = [self.at(a + (b - a) * i / k)[0] for i in range(k + 1)]
            svg.append(ribbon(pts, self.width(a), self.width(b), per=4))
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


def leaf_def(var, tone, shade_side, speck):
    key = (var, tone, shade_side, speck)
    if key in DEFS:
        return DEFS[key][0]
    lid = f"hl{len(DEFS)}"
    lf = hoya_leaf(var)
    fill, sh, sheen = TONES[tone]
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
    o.append(f'<path d="{cr_path(a + b, closed=True, sharp={0, 3})}" fill="{P["cream"]}" opacity="{sheen}"/>')
    if speck:
        rnd = random.Random(speck * 31 + var)
        dd = []
        for _ in range(11):
            t = rnd.uniform(0.12, 0.84)
            side = rnd.choice(("r", "l"))
            g = 1 if side == "r" else -1
            p = lf.pt(t, g * lf.width(t, side) * rnd.uniform(0.18, 0.82))
            r = rnd.uniform(0.6, 1.05)
            dd.append(f"M{f(p[0] - r)} {f(p[1])}a{f(r)} {f(r)} 0 1 0 {f(2 * r)} 0a{f(r)} {f(r)} 0 1 0 {f(-2 * r)} 0")
        o.append(f'<path d="{"".join(dd)}" fill="{P["spot"]}" opacity=".7"/>')
    mid = [lf.axis(t) for t in (0.0, 0.3, 0.6, 0.88)]
    o.append(f'<path d="M{f(mid[0][0])} {f(mid[0][1])}' + "".join(f"L{f(x)} {f(y)}" for x, y in mid[1:])
             + f'" fill="none" stroke="{MIDRIB}" stroke-width="1.1" stroke-linecap="round" opacity=".4"/>')
    o.append("</g></g>")
    DEFS[key] = (lid, "".join(o))
    return lid


def place_leaf(node, ang, L, tone, var=0, speck=0, pl=6):
    """petiole from `node` along angle `ang` (0 = up, clockwise); returns (petiole, leaf)."""
    dv = dir_of(ang)
    q = (node[0] + dv[0] * pl, node[1] + dv[1] * pl)
    tuck = (q[0] + dv[0] * L * 0.1, q[1] + dv[1] * L * 0.1)
    back = (node[0] - dv[0] * 1.5, node[1] - dv[1] * 1.5)
    w = max(2.2, L * 0.048)
    pet = (f'<path d="M{f(back[0])} {f(back[1])}L{f(tuck[0])} {f(tuck[1])}" stroke-width="{f(w)}"/>')
    shade_side = "r" if math.cos(rad(ang)) > 0 else "l"
    lid = leaf_def(var, tone, shade_side, speck)
    s = L / UL
    use = f'<use href="#{lid}" transform="translate({f(q[0])} {f(q[1])}) rotate({f(ang)}) scale({s:.3f})"/>'
    return pet, use


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


def flower_defs(R=11.0):
    petals = star_d(R, R * 0.5)
    corona = star_d(R * 0.42, R * 0.2, rot=-54, soft=0.1)
    return (f'<clipPath id="hfc"><path d="{petals}"/></clipPath>'
            f'<g id="hf"><path d="{petals}" fill="{PETAL}"/>'
            f'<path d="M0 -14L14 -14L14 14L0 14Z" transform="rotate(-20)" fill="{PETAL_SH}" clip-path="url(#hfc)"/>'
            f'<path d="{corona}" fill="{CORONA}"/><circle r="{f(R * 0.11)}" fill="{CORONA_C}"/></g>'
            f'<g id="hfb"><path d="{petals}" fill="{PETAL_BK}"/>'
            f'<path d="{corona}" fill="{P["burgundy"]}"/></g>')


def umbel(anchor, R=32, n=64, seed=1, tilt=0.0):
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
    ped, fl = [], []
    for v in items:
        p = (c[0] + v[0] * R, c[1] + v[1] * R * 0.9)
        if v[1] < -0.2 and v[2] < 0.6:
            ped.append(f"M{f(anchor[0])} {f(anchor[1])}L{f(p[0])} {f(p[1])}")
        fore = max(0.35, math.sqrt(max(0.0, v[2])) if v[2] > 0 else 0.35)
        a = math.degrees(math.atan2(v[1], v[0]))
        spin = rnd.uniform(0, 72)
        use = "hf" if v[2] > 0.2 else "hfb"
        s = 0.94 + 0.12 * rnd.random()
        fl.append(f'<use href="#{use}" transform="translate({f(p[0])} {f(p[1])}) rotate({f(a)}) '
                  f'scale({fore * s:.2f} {s:.2f}) rotate({f(spin - a)})"/>')
    core_ = (f'<ellipse cx="{f(c[0])}" cy="{f(c[1] + R * 0.12)}" rx="{f(R * 0.78)}" ry="{f(R * 0.6)}" '
             f'fill="{P["rose"]}"/>')
    return (f'<path d="{"".join(ped)}" stroke="{PEDICEL}" stroke-width="1.3" fill="none" stroke-linecap="round"/>'
            + core_ + "".join(fl))


def peduncle(node, end, w=2.4):
    mid = ((node[0] + end[0]) / 2 + 3, (node[1] + end[1]) / 2)
    return f'<path d="{ribbon([node, mid, end], w, 1.6)}" fill="{PEDICEL}"/>'


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
    (700, [(-62, 58, "forest", 1, 3, 0), (46, 46, "mid", 0, 2, 0)]),
    (782, [(-50, 44, "light", 1, 1, 0), (40, 36, "deep", 0, 2, 0)]),
    (846, [(-64, 40, "mid", 1, 2, 0), (54, 32, "forest", 0, 1, 0)]),
    (888, [(-48, 22, "sage", 1, 0, 0), (58, 19, "mid", 0, 0, 0)]),
]
B_NODES = [
    (70, [(62, 48, "forest", 1, 2, 0), (-58, 40, "deep", 0, 1, 0)]),
    (165, [(58, 60, "sage", 1, 1, 5), (-66, 46, "forest", 0, 2, 0)]),
    (262, [(-70, 54, "mid", 1, 3, 0), (76, 50, "deep", 1, 0, 0)]),
    (352, [(-60, 48, "light", 1, 2, 6), (68, 44, "forest", 1, 1, 0)]),
    (420, [(-40, 30, "sage", 1, 0, 0), (40, 26, "mid", 1, 0, 0)]),
]
C_NODES = [
    (70, [(-70, 40, "sage", 1, 1, 0), (64, 36, "forest", 1, 2, 7)]),
    (132, [(-62, 34, "mid", 1, 2, 0), (70, 32, "light", 1, 1, 0)]),
    (176, [(-34, 22, "sage", 1, 0, 0), (36, 20, "forest", 1, 0, 0)]),
]


def nodes_svg(st, nodes, rnd):
    back, front = [], []
    for s, leaves in nodes:
        if s > st.L - 2:
            continue
        node, t = st.at(s)
        tang = ang_of(t)
        for a, L, tone, layer, var, speck in leaves:
            L *= SCALE
            ang = tang + a + rnd.uniform(-5, 5)
            pet, use = place_leaf(node, ang, L, tone, var, speck)
            (front if layer else back).append((pet, use))
    return back, front


def emit(pairs):
    if not pairs:
        return ""
    pets = "".join(p for p, _ in pairs)
    return (f'<g stroke="{STEM}" stroke-linecap="round" fill="none">{pets}</g>'
            + "".join(u for _, u in pairs))


def build():
    DEFS.clear()
    back, front = pot("classic", rx=98, rim_y=588, base_w=70, band=True)
    rnd = random.Random(7)
    HL = HP.L
    A = Stem(0, 900, phase=0.4, w0=6, w1=1.8)
    B = Stem(HL, HL - 190, tail=[(424, 446), (462, 468), (488, 506), (498, 552), (494, 596), (484, 628)],
             phase=2.3, w0=5.6, w1=2.2)
    C = Stem(0, 0, w0=4.2, w1=1.8)
    C.path = Path([(270, 586), (246, 589), (224, 589), (206, 594), (194, 616), (188, 650), (190, 686),
                   (198, 712)], per=20)
    C.L = C.path.L
    C.hoop_len = 0

    ab, af = nodes_svg(A, A_NODES, rnd)
    bb, bf = nodes_svg(B, B_NODES, rnd)
    cb, cf = nodes_svg(C, C_NODES, rnd)

    # umbel 1: from a node near the top-left, hangs inside the hoop
    n1, _ = A.at(478)
    u1_top = (n1[0] + 20, n1[1] + 34)
    # umbel 2: from a node on the trailing tail of B
    n2, _ = B.at(262)
    u2_top = (n2[0] - 30, n2[1] + 22)

    body = []
    body.append(back)
    body.append(emit(ab + bb))
    body.append(A.pieces(False) + B.pieces(False))
    body.append(C.part(0, 30))
    body.append(hoop_svg())
    body.append(A.pieces(True) + B.pieces(True))
    body.append(emit(af + bf))
    body.append(peduncle(n1, u1_top))
    body.append(umbel(u1_top, R=36, seed=2, tilt=0.12))
    body.append(peduncle(n2, u2_top))
    body.append(umbel(u2_top, R=33, seed=5, tilt=-0.1))
    body.append(front)
    body.append(C.part(22, C.L))
    body.append(emit(cb + cf))
    defs = "<defs>" + flower_defs() + "".join(v[1] for v in DEFS.values()) + "</defs>"
    return defs + "".join(body)


if __name__ == "__main__":
    reset_ids()
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "..", "out", "hoya_carnosa.svg")
    open(dst, "w").write(svg_doc(build(), "Hoya carnosa (wax plant)"))
    print("wrote", os.path.normpath(dst), os.path.getsize(dst), "bytes")
