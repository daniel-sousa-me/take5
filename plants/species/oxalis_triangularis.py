"""Oxalis triangularis (purple shamrock) -- v4 generator.

Each leaf = three obdeltoid leaflets meeting at one point (the petiole tip).
Leaflets are built in a tiny orthographic 3D model (yaw / droop / fold / view
elevation) so trios read as open or half-folded 'butterflies' at varied angles,
and each leaflet half gets a flat tone from its facing to the light.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import PAL, f, cr_path, cr_sample, ribbon, pot, svg_doc, uid, reset_ids  # noqa: E402

P = PAL
# leaf ramp, dark -> light (burgundy family); blotch uses the same ramp + 2
RAMP = ["#43292F", "#4F3036", P["wine"], P["burgundy"], P["plum"], "#A0646C",
        P["rose"], "#C88B8C", P["blush"]]
# petioles: a light pinkish-green, clearly apart from every leaf tone so they
# read where they cross the foliage (the real stems are paler than the blades)
PET_BACK = "#A08679"
PET_FRONT = "#B39A8C"
PEDUNCLE = "#B08A88"
FL = ["#CD9A9B", "#DBAEAC", "#E6C0BC"]  # blush petal tones, deep enough to hold on ivory
FL_EDGE = "#C38D8F"  # petal rim, one step darker
LIGHT = (-0.45, -0.45, 0.77)


def norm(v):
    m = math.sqrt(sum(c * c for c in v)) or 1
    return tuple(c / m for c in v)


LIGHT = norm(LIGHT)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


class Frame:
    """Maps a leaflet's local (s along axis, w across) to screen coords."""

    def __init__(self, tip, phi, droop, fold, elev, lean):
        self.tip, self.phi, self.droop, self.fold = tip, phi, droop, fold
        self.elev, self.lean = elev, lean

    def basis(self, side):
        ph, d, b = self.phi, self.droop, self.fold
        a = (math.cos(d) * math.cos(ph), math.cos(d) * math.sin(ph), -math.sin(d))
        c = (-math.sin(ph) * math.cos(b), math.cos(ph) * math.cos(b), -math.sin(b))
        c = (c[0] * side, c[1] * side, c[2]) if side > 0 else (c[0] * side, c[1] * side, c[2])
        return a, c

    def to3(self, s, w):
        side = 1 if w >= 0 else -1
        a, c = self.basis(side)
        aw = abs(w)
        return tuple(a[i] * s + c[i] * aw for i in range(3))

    def scr(self, p3):
        X, Y, Z = p3
        e = self.elev
        up = Y * math.sin(e) + Z * math.cos(e)
        x, y = X, -up
        cl, sl = math.cos(self.lean), math.sin(self.lean)
        return (self.tip[0] + x * cl - y * sl, self.tip[1] + x * sl + y * cl)

    def pt(self, s, w):
        return self.scr(self.to3(s, w))

    def depth(self, s, w):
        X, Y, Z = self.to3(s, w)
        return -Y * math.cos(self.elev) + Z * math.sin(self.elev)

    def light(self, side):
        a, c = self.basis(side)
        n = norm(cross(a, c)) if side > 0 else norm(cross(c, a))
        if n[2] < 0:
            n = tuple(-x for x in n)
        view = (0, -math.cos(self.elev), math.sin(self.elev))
        under = dot(n, view) < 0
        return dot(n, LIGHT), under


def bez(frame, segs, start):
    d = f"M{f(start[0])} {f(start[1])}"
    for c1, c2, p in segs:
        a, b, q = frame.pt(*c1), frame.pt(*c2), frame.pt(*p)
        d += f"C{f(a[0])} {f(a[1])} {f(b[0])} {f(b[1])} {f(q[0])} {f(q[1])}"
    return d


def leaflet_segs(L, W, sg=1, notch=0.87):
    """Right (sg=1) / left (sg=-1) half outline, base -> notch, in (s, w)."""
    w = lambda v: sg * v * W  # noqa: E731
    return [
        ((0.22 * L, w(0.04)), (0.60 * L, w(0.58)), (0.85 * L, w(0.92))),
        ((0.95 * L, w(1.05)), (1.05 * L, w(0.86)), (1.0 * L, w(0.52))),
        ((0.97 * L, w(0.26)), (0.91 * L, w(0.06)), (notch * L, 0)),
    ]


def blotch_segs(L, W, sg=1):
    """Lighter central zone: a soft chevron hugging the leaflet base."""
    w = lambda v: sg * v * W  # noqa: E731
    return [
        ((0.16 * L, w(0.03)), (0.33 * L, w(0.25)), (0.46 * L, w(0.40))),
        ((0.50 * L, w(0.45)), (0.55 * L, w(0.42)), (0.56 * L, w(0.33))),
        ((0.57 * L, w(0.20)), (0.58 * L, w(0.08)), (0.60 * L, 0)),
    ]


def rev(segs, start):
    """Reverse a list of cubic segments that begins at `start`."""
    pts = [start] + [p for _, _, p in segs]
    out = []
    for i in range(len(segs) - 1, -1, -1):
        c1, c2, _ = segs[i]
        out.append((c2, c1, pts[i]))
    return out


def col(i):
    """Continuous blend along RAMP (keeps every tone inside the palette family)."""
    i = max(0.0, min(len(RAMP) - 1.0, i))
    k = min(int(i), len(RAMP) - 2)
    u = i - k
    a, b = RAMP[k], RAMP[k + 1]
    c = [round(int(a[j:j + 2], 16) * (1 - u) + int(b[j:j + 2], 16) * u) for j in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(c)


def tone(v, under, off):
    # v in [-1,1]: brightness of the half; off = the trio's depth layer on the
    # RAMP (explicit per trio, see LEAVES). The light swing inside one trio is
    # kept modest so neighbouring layers stay >= 2 ramp steps apart where
    # they overlap (verified pair by pair, not by eye).
    i = 1.3 + v * TONE_SWING + off - (0.6 if under else 0)
    return max(0.0, min(7.0, i))


TONE_SWING = 1.1


def leaflet(frame, L, W, off, asym=1.0, notch=0.87):
    """Returns svg for one leaflet (two halves, blotch, midrib)."""
    base = frame.pt(0, 0)
    R = leaflet_segs(L, W, 1, notch)
    Lh = leaflet_segs(L, W * asym, -1, notch)
    outline = bez(frame, R + rev(Lh, (0, 0)), base) + "Z"
    lr, ur = frame.light(1)
    ll, ul = frame.light(-1)
    tr, tl = tone(lr, ur, off), tone(ll, ul, off)
    # guarantee the two halves read as a fold only when folded
    if frame.fold > 0.35 and abs(tr - tl) < 0.6:
        tl = max(0, min(tr, tl) - 0.6)
    cid = uid("ox")
    pid = cid + "p"
    out = [f'<clipPath id="{cid}"><path id="{pid}" d="{outline}"/></clipPath>',
           f'<use href="#{pid}" fill="{col(tr)}"/>']
    inner = []
    if abs(tl - tr) > 0.05:
        half = bez(frame, Lh, base) + f"L{f(base[0])} {f(base[1])}Z"
        inner.append(f'<path d="{half}" fill="{col(tl)}"/>')
    for sg, t in ((1, tr), (-1, tl)):
        b = blotch_segs(L, W * (asym if sg < 0 else 1), sg)
        bd = bez(frame, b, base) + f"L{f(base[0])} {f(base[1])}Z"
        inner.append(f'<path d="{bd}" fill="{col(t + 1.1)}"/>')
    out.append(f'<g clip-path="url(#{cid})">' + "".join(inner) + "</g>")
    return "".join(out)


def trio(tip, L, yaw, droop=0.35, fold=0.1, elev=0.9, lean=0.0, off=0, var=(1, 1, 1),
         folds=None):
    """Three leaflets meeting at `tip`. yaw rotates the trio in its own plane."""
    parts = []
    for i, k in enumerate((90, 210, 330)):
        phi = math.radians(k + yaw)
        fo = folds[i] if folds else fold
        fr = Frame(tip, phi, droop * (0.6 if k == 90 else 1.0), fo, min(elev + 0.32, 1.35),
                   math.radians(lean))
        Li = L * var[i]
        W = Li * 0.56
        d = fr.depth(Li * 0.6, 0)
        parts.append((d, fr, Li, W, (1.0 - 0.08 * ((i + yaw) % 2))))
    parts.sort(key=lambda p: -p[0])  # far first
    return "".join(leaflet(fr, Li, W, off, asym) for _, fr, Li, W, asym in parts)


def tail_ribbon(pts, w0, w1, tail, per=6):
    """core.ribbon, but the last `tail` units narrow to a fine point, so the stalk
    runs into the leaflet junction without a round end showing above it."""
    s = cr_sample(pts, per)
    n = len(s)
    dist = [0.0] * n
    for i in range(n - 2, -1, -1):
        dist[i] = dist[i + 1] + math.dist(s[i], s[i + 1])
    L, R = [], []
    for i, p in enumerate(s):
        a, b = s[max(i - 1, 0)], s[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy / m, dx / m
        w = (w0 + (w1 - w0) * (i / (n - 1))) / 2
        if dist[i] < tail:
            w *= 0.15 + 0.85 * math.sin(dist[i] / tail * math.pi / 2)  # smooth onset, pointed end
        L.append((p[0] + nx * w, p[1] + ny * w))
        R.append((p[0] - nx * w, p[1] - ny * w))
    step = max(1, per // 2)
    keep = sorted(set(list(range(0, n, step)) + [k for k in range(n) if dist[k] < tail * 1.5] + [n - 1]))
    ring = [L[k] for k in keep] + [R[k] for k in keep][::-1]
    return cr_path(ring, closed=True, sharp={0, len(ring) - 1})


def base_stub(p0, p1, w, color):
    """Hidden-crown extension below a stalk's start p0 (heading towards p1): it
    curves down to a shared crown point under the rim's front edge, same width and
    colour, so the stalks fan out of the soil as one bundle and no cut end sits on
    the visible soil. Plain polygon (a smoothed ribbon bulges at its square end)."""
    d = (p1[0] - p0[0], p1[1] - p0[1])
    m = math.hypot(*d) or 1
    d = (d[0] / m, d[1] / m)
    c = (300 + (p0[0] - 300) * 0.35, 618)
    k = math.hypot(p0[0] - c[0], p0[1] - c[1]) * 0.5
    q = (p0[0] - d[0] * k, p0[1] - d[1] * k)
    e = (p0[0] + d[0] * 1.5, p0[1] + d[1] * 1.5)
    pts = [tuple((1 - t) ** 2 * c[j] + 2 * (1 - t) * t * q[j] + t * t * e[j] for j in (0, 1))
           for t in (i / 16 for i in range(17))]
    L, R = [], []
    for i, pt in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        mm = math.hypot(dx, dy) or 1
        L.append((pt[0] - dy / mm * w / 2, pt[1] + dx / mm * w / 2))
        R.append((pt[0] + dy / mm * w / 2, pt[1] - dx / mm * w / 2))
    ring = L + R[::-1]
    return '<path d="M' + "L".join(f"{f(x)} {f(y)}" for x, y in ring) + f'Z" fill="{color}"/>'


def petiole(base, tip, bow=0.0, w0=5.2, w1=3.0, color=PET_FRONT, tail=0.0):
    """Wiry petiole: rises steeply out of the soil, then arches out to the tip.
    tail: narrow the last stretch to a point that runs into the leaflet junction."""
    bx, by = base
    tx, ty = tip
    dx, dy = tx - bx, ty - by
    lift = max(0.0, abs(dx) - 0.45 * abs(dy)) * 0.22 * min(1.0, abs(dy) / 160)
    p1 = (bx + dx * 0.10 + bow * 0.4, by + dy * 0.34 - lift * 0.5)
    p2 = (bx + dx * 0.50 + bow, by + dy * 0.78 - lift)
    p3 = (tx - dx * 0.12 + bow * 0.2, ty - dy * 0.06 - lift * 0.12)
    # match the ribbon's own start heading (first spline sample)
    stub = base_stub(base, cr_sample([base, p1, p2, p3, tip], 6)[1], w0, color)
    if tail:
        return stub + f'<path d="{tail_ribbon([base, p1, p2, p3, tip], w0, w1, tail)}" fill="{color}"/>'
    return stub + f'<path d="{ribbon([base, p1, p2, p3, tip], w0, w1)}" fill="{color}"/>'


# ------------------------------------------------------------------ flowers
def petal_segs(L, W, sg):
    w = lambda v: sg * v * W  # noqa: E731
    return [
        ((0.30 * L, w(0.10)), (0.45 * L, w(0.70)), (0.78 * L, w(0.92))),
        ((0.98 * L, w(1.02)), (1.05 * L, w(0.45)), (1.0 * L, 0)),
    ]


def flower(c, L, elev, lean, yaw, cup=-0.55):
    parts = []
    for i in range(5):
        phi = math.radians(yaw + i * 72)
        fr = Frame(c, phi, cup, 0.0, elev, math.radians(lean))
        parts.append((fr.depth(L * 0.6, 0), fr))
    parts.sort(key=lambda p: -p[0])
    out = []
    for k, (dd, fr) in enumerate(parts):
        base = fr.pt(0, 0)
        R = petal_segs(L, L * 0.42, 1)
        Lh = petal_segs(L, L * 0.42, -1)
        d = bez(fr, R + rev(Lh, (0, 0)), base) + "Z"
        v, under = fr.light(1)
        t = 0 if under else (2 if v > 0.55 else 1)
        # darker rim = the full petal in FL_EDGE, the face inset inside it
        Ri = petal_segs(L * 0.9, L * 0.42 * 0.84, 1)
        Li = petal_segs(L * 0.9, L * 0.42 * 0.84, -1)
        di = bez(fr, Ri + rev(Li, (0, 0)), base) + "Z"
        out.append(f'<path d="{d}" fill="{FL_EDGE if t else "#BE8889"}"/><path d="{di}" fill="{FL[t]}"/>')
    out.append(f'<circle cx="{f(c[0])}" cy="{f(c[1])}" r="{f(L * 0.16)}" fill="{P["yellow_edge"]}"/>')
    return "".join(out)


def bud(tip, L, ang):
    a = math.radians(ang)
    ux, uy = math.sin(a), -math.cos(a)
    nx, ny = -uy, ux

    def P2(s, w):
        return (tip[0] + ux * s + nx * w, tip[1] + uy * s + ny * w)
    pts = [P2(0, 0), P2(L * 0.35, L * 0.2), P2(L * 0.8, L * 0.15), P2(L, 0),
           P2(L * 0.8, -L * 0.15), P2(L * 0.35, -L * 0.2)]
    d = cr_path(pts, closed=True, sharp={0, 3})
    s1, s2, s3 = P2(L * 0.1, L * 0.05), P2(L * 0.55, L * 0.12), P2(L * 0.95, 0)
    half = cr_path([P2(0, 0), s2, s3, P2(L * 0.8, -L * 0.15), P2(L * 0.35, -L * 0.2)], closed=True,
                   sharp={0, 2})
    return f'<path d="{d}" fill="{FL[1]}"/><path d="{half}" fill="{FL_EDGE}"/>'


def umbel(base, top, bow, heads):
    """Peduncle from soil to `top`, then short pedicels to flowers/buds."""
    out = [petiole(base, top, bow, 4.0, 3.0, PEDUNCLE)]
    for kind, (hx, hy), prm in heads:
        pts = [top, ((top[0] + hx) / 2 + prm.get("pb", 0), (top[1] + hy) / 2 - 3), (hx, hy)]
        out.append(f'<path d="{ribbon(pts, 3.0, 2.6)}" fill="{PEDUNCLE}"/>')
    for kind, (hx, hy), prm in heads:
        if kind == "bud":
            out.append(bud((hx, hy), prm["L"], prm["ang"]))
        else:
            out.append(flower((hx, hy), prm["L"], prm["elev"], prm["lean"], prm["yaw"]))
    return "".join(out)


# ------------------------------------------------------------------ layout
# (base_x, tip(x,y), L, yaw, droop, fold, elev, lean, tone_off, bow, var, folds)
LEAVES = [
    # listed in draw order (back -> front); tone_off places each trio on RAMP.
    # back: the top-centre crown and the two far outliers, darkest
    (296, (286, 196), 76, 8, 0.30, 0.15, 0.95, -3, -1.1, -6, (1, 1.05, .95), None),
    (268, (86, 300), 62, -30, 0.45, 0.20, 0.75, -20, -1.2, -18, (1.03, 1, .68), (0.2, 0.2, 0.6)),
    (334, (510, 350), 60, 32, 0.40, 0.45, 0.80, 18, -0.6, 18, (1, .9, 1), None),
    # second layer: the two upper side trios, mid burgundy -> breaks the top mass
    (284, (170, 222), 70, -14, 0.40, 0.30, 0.85, -12, 1.2, -10, (1, .95, 1.05), (0.1, 0.5, 0.2)),
    (316, (424, 240), 68, 20, 0.35, 0.10, 0.90, 10, 1.0, 12, (.95, 1.05, 1), None),
    (276, (128, 406), 64, -22, 0.42, 0.15, 0.80, -16, 1.1, -14, (1, 1.05, 1), None),
    (282, (226, 462), 62, -18, 0.40, 0.20, 0.72, -12, 2.9, -10, (1, 1, .95), None),
    # front layer (lighter / rosier)
    (302, (300, 382), 72, -2, 0.30, 0.10, 0.80, 2, 4.2, 4, (1, 1.05, 1), (0.15, 0.1, 0.45)),
    (320, (398, 478), 64, 18, 0.42, 0.15, 0.75, 10, 3.0, 10, (.95, 1, 1), (0.45, 0.1, 0.15)),
    (270, (104, 522), 50, -34, 0.50, 0.30, 0.62, -22, 3.2, -16, (1, .95, 1), None),
    (330, (506, 526), 52, 30, 0.50, 0.20, 0.62, 20, 3.0, 16, (1, 1, .95), None),
    # drapes over the rim: deep plum so it parts clearly from the terracotta
    (288, (228, 560), 56, -10, 0.45, 0.25, 0.60, -6, 1.0, -4, (1, 1, 1), (0.3, 0.2, 0.2)),
]


def build():
    reset_ids()
    back, front = pot(kind="classic", cx=300, rim_y=592, bottom=752, rx=100, rim_h=30, base_w=72,
                      band=True)
    body = [back]
    # flowers sit behind most foliage in depth but rise above it
    fl1 = umbel((294, 600), (238, 120), -8, [
        ("flower", (200, 96), dict(L=25, elev=0.95, lean=-22, yaw=12)),
        ("flower", (248, 78), dict(L=26, elev=1.15, lean=4, yaw=40)),
        ("bud", (272, 104), dict(L=20, ang=38)),
    ])
    fl2 = umbel((308, 600), (372, 138), 10, [
        ("flower", (404, 106), dict(L=24, elev=0.85, lean=24, yaw=-8)),
        ("bud", (352, 108), dict(L=19, ang=-28)),
    ])
    body += [fl1, fl2]
    late = []
    for i, (bx, tip, L, yaw, droop, fold, elev, lean, off, bow, var, folds) in enumerate(LEAVES):
        col = PET_BACK if off < 2.0 else PET_FRONT
        w0 = 5.6 if off >= 2.0 else 5.2
        bx = 300 + (tip[0] - 300) * 0.24 + (bx - 300) * 0.5
        body.append(petiole((bx, 602), tip, bow, w0, 4.0, col, tail=7.0))
        t = trio(tip, L, yaw, droop, fold, elev, lean, off, var, folds)
        (late if tip[1] > 540 else body).append(t)
    body.append(front)
    body += late
    return "".join(body)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "out", "oxalis_triangularis.svg")
    doc = svg_doc(build(), "Oxalis triangularis (purple shamrock)")
    with open(out, "w") as fh:
        fh.write(doc)
    print(len(doc), "bytes")
