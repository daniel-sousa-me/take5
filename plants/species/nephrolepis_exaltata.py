"""Boston fern (Nephrolepis exaltata) -- v4 botanical card art.

A fountain of long, arching once-pinnate fronds from a central crown.  Each
frond = thin tapered rachis + many small, closely set, narrow-oblong pinnae
(alternate, slightly falcate toward the frond tip) that diminish at both
ends.  Fronds are generated from a simple "bend" model (heading angle grows
with arc length) so neighbouring fronds fan out in order and do not cross.
Tones step from dark (upright, back) to light (outer draping / young, front).
One pinna shape per tone is defined once and reused via <use>.

Run:  python3 species/nephrolepis_exaltata.py  -> out/nephrolepis_exaltata.svg
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, SHADE, Leaf, cr_path, f, uid, reset_ids, pot, svg_doc  # noqa: E402

P = PAL
CX = 300
RIM = 588
RX = 94
CROWN_Y = 600          # rachis bases start here (inside soil, hidden by rim front)
LIGHT = (-0.55, -0.83)  # light from the upper left
U = 10.0               # unit pinna length in defs

_DEFS = {}
_DEFS_SVG = []


def g(v):
    """compact number for matrix coefficients"""
    s = f"{v:.3f}".rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s or "0"


def g2(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s if s not in ("", "-") else "0"


# ------------------------------------------------------------------ pinna
def pinna_leaf(L=U):
    # narrow oblong, slightly broader and auricled on the upper (acroscopic)
    # side at the base, bluntly acute tip; gentle falcate curve (bend)
    # widest near the base, then a long, gentle taper to a fine acute tip that
    # curves forward (falcate) -- a fern pinna, not a blunt capsule
    right = [(0.0, 0.09), (0.10, 0.165), (0.30, 0.158), (0.52, 0.132), (0.72, 0.092), (0.88, 0.045)]
    left = [(0.0, 0.07), (0.10, 0.13), (0.30, 0.14), (0.52, 0.118), (0.72, 0.082), (0.88, 0.04)]
    wf = 1.14  # breadth factor (fuller foliage mass)
    right = [(t, w * wf) for t, w in right]
    left = [(t, w * wf) for t, w in left]
    return Leaf(L, right, left, bend=0.16, base_sharp=False)


def _shapes():
    """Pinna outline + its two half-blades, defined once (no fill) and
    coloured per tone by <use fill=...>."""
    lf = pinna_leaf(U * 10)  # authored 10x for precision, scaled back below
    sc = f' transform="scale({1 / 10:g})"'
    out = [f'<path id="po"{sc} d="{lf.path()}"/>']
    for side, sg in (("r", 1), ("l", -1)):
        nodes = lf.right if side == "r" else lf.left
        pts = [lf.axis(0)] + [lf.pt(t, sg * w) for t, w in nodes] + [lf.axis(1)] + \
              [lf.axis(t) for t in (0.66, 0.33)]
        n = len(nodes) + 1
        out.append(f'<path id="h{side}"{sc} d="{cr_path(pts, closed=True, sharp={0, n, n + 1, n + 2, n + 3})}"/>')
    return "".join(out)


# Print floor (policy: 0.055 mm/unit planning scale; filled slivers count by their widest
# point, 4*area/perimeter as deck/print_prep.py measures it).  A pinna whose shaded half-blade
# would print thinner than the minimum is drawn flat (one tone), and no pinna is drawn so
# small that its whole blade falls under the minimum.
MM_U = 0.055
W_PINNA, W_HALF = 0.428, 0.22     # measured widths per unit pinna length (U = 10): blade, half-blade


def _lumi(h):
    r, g_, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g_ + 0.0722 * b


def _need(col):
    """printed minimum (mm) for a filled shape of this colour (light knockout vs dark)."""
    return 0.225 if _lumi(col) > 0.55 else 0.175


def pinna_def(tone, shade_right):
    """shade_right None = flat pinna (no shaded half)."""
    key = (tone, shade_right)
    if key in _DEFS:
        return _DEFS[key]
    if not _DEFS_SVG:
        _DEFS_SVG.append(_shapes())
    fill, shade = tone
    gid = uid("p")
    half = "" if shade_right is None else f'<use href="#h{"r" if shade_right else "l"}" fill="{shade}"/>'
    _DEFS_SVG.append(f'<g id="{gid}"><use href="#po" fill="{fill}"/>{half}</g>')
    _DEFS[key] = gid
    return gid


def pinna_use(x, y, rot, L, tone, mirror, wf=1.0):
    """base at (x,y), pointing along rot (deg, 0 = up, clockwise +).
    mirror=-1 flips the falcate curve (so it always bends toward the frond tip)."""
    fill, shade = tone
    wk = min(1.0, wf)                                   # breadth factor (conservative)
    L = max(L, _need(fill) / (W_PINNA * wk * MM_U) * 1.02)   # never below a printable blade
    a = math.radians(rot)
    c, s = math.cos(a), math.sin(a)
    k = L / U
    # world direction of local +x after mirroring
    rx, ry = mirror * c, mirror * s
    # shade the half that faces away from the light -- if that half is printable
    shade_right = (rx * LIGHT[0] + ry * LIGHT[1]) < 0
    if L * W_HALF * wk * MM_U < _need(shade):
        shade_right = None
    gid = pinna_def(tone, shade_right)
    m = (c * k * mirror * wf, s * k * mirror * wf, -s * k, c * k, x, y)
    return (f'<use href="#{gid}" transform="matrix({g2(m[0])} {g2(m[1])} {g2(m[2])} {g2(m[3])} '
            f'{f(m[4])} {f(m[5])})"/>')


# ------------------------------------------------------------------ frond
def frond_curve(x0, y0, a0, length, bend, power=1.7, ds=3.0):
    """heading theta(s) = a0 + bend * (s/L)^power; returns [(x, y, theta)]."""
    pts = [(x0, y0, a0)]
    n = int(length / ds)
    x, y = x0, y0
    for i in range(1, n + 1):
        s = i * ds
        th = a0 + bend * (s / length) ** power
        a = math.radians(th)
        x += math.sin(a) * ds
        y -= math.cos(a) * ds
        pts.append((x, y, th))
    return pts


def spine(ctrl, ds=3.0):
    """Catmull-Rom through hand-placed control points, resampled to uniform
    arc length; returns ([(x, y, theta)], length)."""
    from core import cr_sample
    raw = cr_sample(ctrl, 16)
    acc = [0.0]
    for a, b in zip(raw, raw[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    L = acc[-1]
    out, j = [], 0
    n = int(L / ds)
    for i in range(n + 1):
        s = L * i / n
        while j < len(acc) - 2 and acc[j + 1] < s:
            j += 1
        r = (s - acc[j]) / ((acc[j + 1] - acc[j]) or 1)
        a, b = raw[j], raw[j + 1]
        th = math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1])))
        out.append((a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r, th))
    # unwrap headings so interpolation never jumps across +-180
    for i in range(1, len(out)):
        x, y, th = out[i]
        while th - out[i - 1][2] > 180:
            th -= 360
        while th - out[i - 1][2] < -180:
            th += 360
        out[i] = (x, y, th)
    return out, L


def at(pts, u):
    i = min(int(u * (len(pts) - 1)), len(pts) - 2)
    r = u * (len(pts) - 1) - i
    a, b = pts[i], pts[i + 1]
    return (a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r, a[2] + (b[2] - a[2]) * r)


def rachis_path(pts, w0, w1, end):
    L, R = [], []
    n = 12
    for i in range(n + 1):
        u = end * i / n
        x, y, th = at(pts, u)
        a = math.radians(th)
        nx, ny = math.cos(a), math.sin(a)
        w = (w0 + (w1 - w0) * (u / end) ** 0.8) / 2
        L.append((x - nx * w, y - ny * w))
        R.append((x + nx * w, y + ny * w))
    tip = at(pts, end)[:2]
    ring = L + [tip] + R[::-1]
    return cr_path(ring, closed=True, sharp={0, len(ring) - 1})


BBOX = [1e9, 1e9, -1e9, -1e9]


def _grow(x, y):
    BBOX[0], BBOX[1] = min(BBOX[0], x), min(BBOX[1], y)
    BBOX[2], BBOX[3] = max(BBOX[2], x), max(BBOX[3], y)


def hidden_by_pot(x, y):
    """True if (x, y) lies under the rim front / pot body (drawn later)."""
    dx = (x - CX) / (RX - 3)
    if abs(dx) >= 1:
        return False
    return y > RIM + RX * 0.15 * math.sqrt(1 - dx * dx) + 3


def frond(ctrl, tone, rachis_col, pmax, bare=0.05, seed=0, w0=4.2,
          dev0=64, dev1=46, gap=1.5, cull=True, prof0=0.30, scale=1.22,
          peak=0.42, tipf=0.16, wf=1.0, grav=0.14):
    """One pinnate frond.  pmax = longest pinna length (px).  cull: drop pinnae
    completely hidden behind the pot front (only for fronds drawn before it)."""
    r = random.Random(seed)
    pmax *= scale
    pts, length = spine(ctrl)
    uses = []
    s0 = max(bare * length, 26)
    pos = s0
    side = 1 if seed % 2 else -1
    last = None
    while True:
        u = (pos - s0) / (length - s0)
        if u >= 0.965:
            break
        # lanceolate outline: short at the base, longest around `peak`
        # (varies per frond), long taper to a short tip
        if u < peak:
            prof = prof0 + (1 - prof0) * math.sin(u / peak * math.pi / 2)
        else:
            prof = 1 - (1 - tipf) * ((u - peak) / (1 - peak)) ** 1.25
        pl = pmax * prof * r.uniform(0.86, 1.1)
        dev = dev0 + (dev1 - dev0) * u
        x, y, th = at(pts, pos / length)
        jit = r.uniform(-6, 6)
        rot = th + side * (dev + jit)
        if math.cos(math.radians(rot)) > 0.2 and math.cos(math.radians(th)) < 0.6:
            # convex side of an arch: the pinna lies back toward the tip rather than
            # standing straight up off the rachis
            rot = th + side * (dev * 0.68 + jit)
        # gravity: pinnae further out along the frond sag a little toward the ground
        dd = ((180 - rot + 540) % 360) - 180
        if abs(dd) < 140:
            rot += dd * grav * u
        a = math.radians(rot)
        tx, ty = x + math.sin(a) * pl, y - math.cos(a) * pl
        if not (cull and hidden_by_pot(x, y) and hidden_by_pot(tx, ty + 4)):
            # right-side pinna must curve back toward the tip (counter-clockwise)
            uses.append(pinna_use(x, y, rot, pl, tone, -side, wf))
            if not hidden_by_pot(tx, ty):
                _grow(tx, ty)
        last = pos
        # alternate sides; step ~ pinna width so pinnae sit close but separate
        pos += gap * 0.16 * pl / math.sin(math.radians(dev))
        side = -side
    # terminal pinna along the rachis
    end = (last + 1.5) / length
    x, y, th = at(pts, end)
    uses.append(pinna_use(x, y, th + r.uniform(-4, 4), pmax * 0.22, tone, 1, wf))
    _grow(x, y)
    rp = rachis_path(pts, w0, 1.0, end + 0.004)
    return f'<path d="{rp}" fill="{rachis_col}"/>' + "".join(uses), pts


# ------------------------------------------------------------------ fiddlehead
def fiddlehead(x0, pts_ctrl, coil_r, turns, fill, dark, w0=4.2, left=True):
    """A stipe rising from the crown that ends in a tight crozier."""
    # stipe
    from core import cr_sample
    s = cr_sample([(x0, CROWN_Y)] + pts_ctrl, 10)
    # end direction
    (ax, ay), (bx, by) = s[-2], s[-1]
    th = math.atan2(by - ay, bx - ax)
    # spiral: centre off to the inner side of the end tangent
    sg = -1 if left else 1
    nxn, nyn = -math.sin(th) * sg, math.cos(th) * sg  # normal toward coil centre
    cxp, cyp = bx + nxn * coil_r, by + nyn * coil_r
    phi0 = math.atan2(by - cyp, bx - cxp)
    sp = []
    N = 40
    for i in range(1, N + 1):
        t = i / N
        phi = phi0 - sg * t * turns * 2 * math.pi
        rr = coil_r * (1 - 0.78 * t)
        sp.append((cxp + math.cos(phi) * rr, cyp + math.sin(phi) * rr))
    path = s + sp
    n = len(path)
    L, R = [], []
    for i, p in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy / m, dx / m
        u = i / (n - 1)
        # the coil is fatter (rolled-up pinnae) than the stipe
        if i < len(s):
            w = w0 * (1 - 0.15 * u)
        else:
            k = (i - len(s)) / (n - len(s))
            w = w0 * 0.85 + coil_r * 0.55 * math.sin(min(k * 3, 1) * math.pi / 2) * (1 - 0.75 * k)
        L.append((p[0] + nx * w / 2, p[1] + ny * w / 2))
        R.append((p[0] - nx * w / 2, p[1] - ny * w / 2))
    L, R = L[::3] + [L[-1]], R[::3] + [R[-1]]
    ring = L + R[::-1]
    d = cr_path(ring, closed=True, sharp={0, len(L) - 1, len(L), len(ring) - 1})
    # (the old hairline groove on the coil is dropped: below print minimum)
    return f'<path d="{d}" fill="{fill}"/>'


def base_stub(x0, y0, th, w, col):
    """Hidden-crown extension of a stipe: from a common crown point below the
    rim's front edge up to the stipe's start (x0, y0), arriving along its heading
    th, same width and colour, so the stipes fan out of the soil as one tapered
    bundle instead of showing cut ends on the soil."""
    a = math.radians(th)
    d = (math.sin(a), -math.cos(a))
    c = (CX + (x0 - CX) * 0.35, CROWN_Y + 16)
    k = math.hypot(x0 - c[0], y0 - c[1]) * 0.5
    m = (x0 - d[0] * k, y0 - d[1] * k)
    e = (x0 + d[0] * 1.5, y0 + d[1] * 1.5)
    pts = [tuple((1 - t) ** 2 * c[j] + 2 * (1 - t) * t * m[j] + t * t * e[j] for j in (0, 1))
           for t in (i / 16 for i in range(17))]
    # plain polygon (no spline smoothing: a smoothed ribbon bulges at its square end)
    L, R = [], []
    for i, q in enumerate(pts):
        a_, b_ = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]
        mm = math.hypot(dx, dy) or 1
        L.append((q[0] - dy / mm * w / 2, q[1] + dx / mm * w / 2))
        R.append((q[0] + dy / mm * w / 2, q[1] - dx / mm * w / 2))
    ring = L + R[::-1]
    return '<path d="M' + "L".join(f"{f(x)} {f(y)}" for x, y in ring) + f'Z" fill="{col}"/>'


def frond_stub(fr, col):
    pts, _ = spine(fr["ctrl"])
    x, y, th = pts[0]
    return base_stub(x, y, th, fr.get("w0", 4.2), col)


# ------------------------------------------------------------------ build
DEEP = (P["deep"], SHADE[P["deep"]])
FOREST = (P["forest"], SHADE[P["forest"]])
MID = (P["mid"], SHADE[P["mid"]])
SAGE = (P["sage"], SHADE[P["sage"]])
LIGHTT = (P["light"], SHADE[P["light"]])

# Each frond: x0, a0 (start heading, deg, 0 = up, + = right), length, bend
# (total change of heading along the frond), pmax, seed.  Listed back -> front.
BACK = [  # tallest, darkest: rise from the crown, then roll over outward, tips nodding down
    dict(ctrl=[(292, 600), (284, 510), (265, 420), (236, 334), (198, 264), (158, 216), (120, 194), (88, 198), (66, 218)], pmax=31, seed=3, bare=0.2, peak=0.44, wf=1.1, dev0=62, dev1=40),
    dict(ctrl=[(308, 600), (318, 514), (340, 428), (372, 350), (410, 288), (452, 246), (492, 226), (524, 228), (546, 248)], pmax=29, seed=8, bare=0.2, peak=0.38, wf=0.95, dev0=66, dev1=44, gap=1.6),
]
CENTRE = [  # young frond standing in the gap of the V: sage, narrow, tip just starting to bow
    dict(ctrl=[(300, 600), (302, 502), (307, 404), (318, 318), (336, 248), (360, 204), (384, 188)], pmax=20, seed=15, bare=0.24, wf=0.88, prof0=0.4, peak=0.5, dev0=58, dev1=40, gap=1.7),
]
RING2 = [  # leaning out and arching down, forest
    dict(ctrl=[(288, 600), (262, 546), (222, 482), (176, 430), (130, 404), (92, 406), (64, 430), (50, 466)], pmax=29, seed=5, bare=0.2, peak=0.36, wf=1.05, dev0=68, grav=0.2),
    dict(ctrl=[(312, 600), (342, 546), (386, 488), (436, 448), (484, 434), (520, 448), (542, 478), (550, 514)], pmax=27, seed=12, bare=0.24, peak=0.48, wf=0.92, dev1=38, gap=1.45, grav=0.2),
]
RING3 = [  # spilling over the rim, mid
    dict(ctrl=[(286, 600), (252, 560), (204, 536), (156, 536), (116, 560), (88, 604), (74, 656)], pmax=28, seed=7, bare=0.22, peak=0.40, wf=0.95, gap=1.55, grav=0.24),
    dict(ctrl=[(316, 600), (354, 570), (404, 556), (452, 566), (488, 600), (506, 648), (510, 690)], pmax=25, seed=10, bare=0.16, peak=0.34, wf=1.08, dev0=60, grav=0.24),
]
DRAPE = [  # right side, behind the pot, draping past the rim: sage
    dict(ctrl=[(318, 603), (342, 580), (386, 569), (426, 588), (451, 624), (461, 664), (460, 700)], pmax=24, seed=2, bare=0.18, peak=0.45, grav=0.24),
]
TUFT = [  # short young fronds screening the crown: sage, in front of the rings
    dict(ctrl=[(296, 602), (283, 562), (262, 530), (237, 510), (214, 504), (196, 510)], pmax=20, seed=31, bare=0.22, prof0=0.5, peak=0.5),
]
FRONT = [  # left side, over the rim in front of the pot: lightest, freshest
    dict(ctrl=[(282, 598), (248, 580), (200, 572), (152, 590), (118, 632), (102, 682), (100, 734)], pmax=26, seed=9, bare=0.16, peak=0.4, gap=1.5, grav=0.24),
]


def build():
    reset_ids()
    _DEFS.clear()
    _DEFS_SVG.clear()
    BBOX[:] = [1e9, 1e9, -1e9, -1e9]
    back, front = pot(kind="classic", cx=CX, rim_y=RIM, rx=RX, base_w=68, band=True)
    body = [back]
    for group, tone, rc in ((BACK, DEEP, P["mid"]), (CENTRE, SAGE, P["light"]),
                            (RING2, FOREST, P["sage"]),
                            (RING3, MID, P["forest"]), (DRAPE, LIGHTT, P["sage"]),
                            (TUFT, LIGHTT, P["sage"])):
        for fr in group:
            body.append(frond_stub(fr, rc) + frond(tone=tone, rachis_col=rc, **fr)[0])
    fh0 = math.degrees(math.atan2(304 - 302, -(560 - CROWN_Y)))
    body.append(base_stub(302, CROWN_Y, fh0, 4.0, P["pale"]))
    # the front frond's stub goes under the pot front (its visible bit on the soil
    # joins the rachis drawn over the rim)
    body += [frond_stub(fr, P["sage"]) for fr in FRONT]
    body.append(fiddlehead(302, [(304, 560), (311, 530), (324, 512)], 13, 1.15,
                           P["pale"], P["sage"], w0=4.0, left=False))
    body.append(front)
    for fr in FRONT:
        body.append(frond(tone=LIGHTT, rachis_col=P["sage"], cull=False, **fr)[0])
    return "<defs>" + "".join(_DEFS_SVG) + "</defs>" + "".join(body)


if __name__ == "__main__":
    out = os.path.join(HERE, "..", "out", "nephrolepis_exaltata.svg")
    with open(out, "w") as fh:
        fh.write(svg_doc(build(), "Nephrolepis exaltata (Boston fern)"))
    print(os.path.normpath(out), os.path.getsize(out), "bbox", [round(v) for v in BBOX])
