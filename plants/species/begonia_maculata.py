"""Begonia maculata (polka-dot begonia) -- v4.

Jointed bamboo-like canes, long asymmetric 'angel-wing' leaves with wavy
margins, irregular silver dots, burgundy undersides on turned leaves and a
small pendant cluster of blush flowers.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import PAL, SHADE, cr_path, cr_sample, ribbon, f, uid, T, pot, svg_doc, reset_ids  # noqa: E402

P = PAL


# ------------------------------------------------------------------ helpers
def refrac(pts, targets, per=14):
    """Arc-length fractions on `pts` of the points closest to each target (point, angle)."""
    s = cr_sample(pts, per)
    acc = [0.0]
    for a, b in zip(s, s[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return [acc[min(range(len(s)), key=lambda k: math.dist(s[k], p))] / acc[-1] for p, _ in targets]


def along(pts, fracs, per=14):
    """Point + tangent angle (deg, 0 = up, clockwise) at arc-length fractions."""
    s = cr_sample(pts, per)
    acc = [0.0]
    for a, b in zip(s, s[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    out = []
    for fr in fracs:
        tg = fr * acc[-1]
        i = next((k for k in range(1, len(acc)) if acc[k] >= tg), len(acc) - 1)
        a, b = s[i - 1], s[i]
        u = (tg - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
        p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        out.append((p, math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1])))))
    return out


def inside(pt, poly):
    x, y = pt
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                c = not c
    return c


def dist_to_poly(pt, poly):
    best = 1e9
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        m = dx * dx + dy * dy or 1
        u = max(0, min(1, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / m))
        best = min(best, math.hypot(pt[0] - ax - u * dx, pt[1] - ay - u * dy))
    return best


def mix(a, b, t):
    """Opaque pre-blend of hex colour b over a at strength t (print policy: no translucent detail)."""
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02X}" for i in (1, 3, 5))


DOT = "#FFFFFF"  # silvery-white polka dots = bare white paper (a beige tint read as cream on white stock)
DOT_MIN = 4.6    # light dot diameter floor (print policy: >= 4.5 units)
LINE_W = 3.0     # midrib / node-ring width (print policy: dark line >= 3.0 units)
EDGE_DEPTH = 0.068  # turned-over margin band, fraction of L at its widest (~14.5 units on the front leaf)


def to_world(p, x, y, rot, sx=1):
    a = math.radians(rot)
    px, py = p[0] * sx, p[1]
    return (x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a))


# ------------------------------------------------------------------ leaf
# (t, w) as fractions of L; t along the midrib (0 = petiole junction, 1 = tip),
# the big basal lobe swings back behind the junction (negative t).
BIG = [(0.0, 0.0), (-0.1, 0.07), (-0.105, 0.16), (-0.055, 0.225), (0.04, 0.26), (0.17, 0.258),
       (0.33, 0.225), (0.5, 0.168), (0.67, 0.108), (0.82, 0.056), (0.93, 0.02)]
SMALL = [(0.0, 0.0), (0.0, 0.05), (0.05, 0.108), (0.16, 0.142), (0.32, 0.142), (0.5, 0.118),
         (0.67, 0.082), (0.82, 0.044), (0.93, 0.014)]


class AngelLeaf:
    def __init__(self, L, seed=0, bend=0.06, width=1.0, wave=0.011, lobe=1.0):
        self.L, self.bend = L, bend
        rnd = random.Random(seed)
        self.rnd = rnd
        big = [(t * (lobe if t < 0 else 1), w * width * (lobe if t < 0.05 else 1)) for t, w in BIG]
        small = [(t, w * width) for t, w in SMALL]
        tip = (0.0, -L)
        R = [(w * L, -t * L) for t, w in big]
        Lf = [(-w * L, -t * L) for t, w in small]
        # dense smooth sides, sinus -> tip
        sr = cr_sample(R + [tip], 10)
        sl = cr_sample(Lf + [tip], 10)
        # ripple (wavy margin), tapered at sinus and tip
        def ripple(side, sgn):
            acc = [0.0]
            for a, b in zip(side, side[1:]):
                acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
            tot = acc[-1]
            lam = L * rnd.uniform(0.15, 0.2)
            ph = rnd.uniform(0, 6.3)
            out = []
            for i, p in enumerate(side):
                a = side[max(i - 1, 0)]
                b = side[min(i + 1, len(side) - 1)]
                dx, dy = b[0] - a[0], b[1] - a[1]
                m = math.hypot(dx, dy) or 1
                nx, ny = dy / m * sgn, -dx / m * sgn  # outward normal
                u = acc[i] / tot
                env = min(1, u / 0.12) * min(1, (1 - u) / 0.2)
                d = wave * L * env * math.sin(2 * math.pi * acc[i] / lam + ph)
                out.append((p[0] + nx * d, p[1] + ny * d))
            return out
        sr = ripple(sr, 1)
        sl = ripple(sl, -1)
        self.poly_local = sr + sl[::-1][1:-1]
        self.sl = sl
        # decimated control points for the path
        kr = sr[::6] + ([sr[-1]] if (len(sr) - 1) % 6 else [])
        kl = sl[::6] + ([sl[-1]] if (len(sl) - 1) % 6 else [])
        ring = [self.B(p) for p in kr] + [self.B(p) for p in kl[::-1][1:-1]]
        self.ring = ring
        self.tip_i = len(kr) - 1
        self.d = cr_path(ring, closed=True, sharp={0, self.tip_i}, k=1.0)
        self.poly = [self.B(p) for p in self.poly_local]

    def B(self, p):
        """apply midrib bend (tip swings to +x for positive bend)."""
        t = -p[1] / self.L
        return (p[0] + self.bend * self.L * t * t, p[1])

    def axis(self, t):
        return self.B((0, -t * self.L))

    def midrib_d(self, t0=0.0, t1=0.9):
        pts = [self.axis(t0 + (t1 - t0) * i / 5) for i in range(6)]
        return cr_path(pts, closed=False)

    def half(self, side):
        """region on one side of the midrib (for flat shading)."""
        sg = 1 if side == "r" else -1
        ts = [-0.3 + i * 0.2 for i in range(8)]
        mid = [self.axis(t) for t in ts]
        far = [(m[0] + sg * self.L, m[1]) for m in mid]
        pts = mid + far[::-1]
        pts = [(round(x), round(y)) for x, y in pts]
        return cr_path(pts, closed=True, sharp={0, len(mid) - 1, len(mid), len(pts) - 1})

    def turned_edge_d(self, depth=EDGE_DEPTH, t0=0.08, t1=0.97):
        """Narrow crescent along the small-side margin: the edge curling over to show a
        sliver of the burgundy underside (widest mid-leaf, tapering to nothing)."""
        L = self.L
        edge = [p for p in self.sl if t0 * L <= -p[1] <= t1 * L]
        inner = []
        for x, y in edge:
            u = (-y / L - t0) / (t1 - t0)
            d = depth * L * math.sin(math.pi * u) ** 0.9
            inner.append((x + d, y))
        ring = [self.B(p) for p in edge[::3]] + [self.B(p) for p in inner[::-1][::3]]
        return cr_path(ring, closed=True, sharp={0, len(edge[::3]) - 1, len(edge[::3]), len(ring) - 1})

    def veins_d(self):
        """faint palmate basal veins + a few pinnate laterals."""
        L = self.L
        v = []
        # into the big lobe
        for (a, b, c) in [((0, 0), (0.08, 0.02), (0.17, 0.07)), ((0, 0), (0.08, -0.03), (0.15, -0.07))]:
            pa, pb, pc = [self.B((w * L, -t * L)) for w, t in (a, b, c)]
            # (w,t) ordering used above
            v.append(f"M{round(pa[0])} {round(pa[1])}Q{round(pb[0])} {round(pb[1])} {round(pc[0])} {round(pc[1])}")
        for t, sg, reach in [(0.2, 1, 0.16), (0.36, 1, 0.13), (0.55, 1, 0.09),
                             (0.16, -1, 0.1), (0.33, -1, 0.1), (0.52, -1, 0.07)]:
            p0 = self.axis(t)
            p1 = self.B((sg * reach * 0.5 * L, -(t + 0.07) * L))
            p2 = self.B((sg * reach * L, -(t + 0.17) * L))
            v.append(f"M{round(p0[0])} {round(p0[1])}Q{round(p1[0])} {round(p1[1])} {round(p2[0])} {round(p2[1])}")
        return "".join(v)

    def dots(self, density=1.0, rmax=5.2, seed=1, small_margin=0.0):
        rnd = random.Random(seed)
        L = self.L
        pts = []
        tries = 0
        # fewer, print-safe dots: every dot >= DOT_MIN across (widen, don't multiply)
        target = int(24 * density * (L / 180) ** 2)
        rmin = DOT_MIN / 2
        xs = [p[0] for p in self.poly_local]
        ys = [p[1] for p in self.poly_local]
        while len(pts) < target and tries < 4000:
            tries += 1
            x = rnd.uniform(min(xs), max(xs))
            y = rnd.uniform(min(ys), max(ys))
            if not inside((x, y), self.poly_local):
                continue
            t = -y / L
            if t > 0.86 or t < -0.05:
                continue
            # size: skewed to small, fewer big; smaller towards tip
            u = rnd.random() ** 1.35
            top = max(rmin * 1.25, rmax * (1 - 0.45 * max(0, t - 0.4)) * (L / 180) ** 0.5)
            r = rmin + (top - rmin) * u
            e = dist_to_poly((x, y), self.poly_local)
            if e < r + 2.2 or (x < 0 and e < r + 2.2 + small_margin):
                continue
            if abs(x) < r + 1.8 and t > 0.02:  # keep midrib clear
                continue
            ok = True
            for (qx, qy, qr) in pts:
                if math.hypot(qx - x, qy - y) < r + qr + rnd.uniform(4.5, 10):
                    ok = False
                    break
            if ok:
                pts.append((x, y, r))
        # bucket by size -> one round-capped zero-length stroke path per bucket
        buckets = {}
        for x, y, r in pts:
            bx, by = self.B((x, y))
            q = max(DOT_MIN, round(r * 2 * 2) / 2)  # diameter to 0.5 px, never under the floor
            buckets.setdefault(q, []).append(f"M{round(bx)} {round(by)}h0")
        return buckets


def leaf_svg(lf, x, y, rot, mirror=False, fill=None, face="top", dot_seed=1,
             density=1.0, shade_side="l"):
    """face: 'top' (dotted upper surface), 'under' (burgundy underside),
    'fold' (upper surface on the big side, burgundy underside on the small side)."""
    sx = -1 if mirror else 1
    tr = T(x, y, rot, 1, sx=sx) if mirror else T(x, y, rot)
    cid = uid("bl")
    pid = cid + "p"
    o = [f'<g transform="{tr}">', f'<clipPath id="{cid}"><path id="{pid}" d="{lf.d}"/></clipPath>']
    if face == "under":
        o.append(f'<use href="#{pid}" fill="{P["burgundy"]}"/>')
        o.append(f'<g clip-path="url(#{cid})">')
        o.append(f'<path d="{lf.half("r")}" fill="{P["wine"]}"/>')
        o.append(f'<path d="{lf.midrib_d(0, 0.9)}" fill="none" stroke="{mix(P["burgundy"], P["rose"], 0.7)}" '
                 f'stroke-width="{LINE_W}" stroke-linecap="round"/>')
        o.append("</g></g>")
        return "".join(o)
    fill = P.get(fill, fill)
    shade = SHADE.get(fill, "#1F3025")
    o.append(f'<use href="#{pid}" fill="{fill}"/>')
    o.append(f'<g clip-path="url(#{cid})">')
    if face == "fold":
        o.append(f'<path d="{lf.half("l")}" fill="{P["burgundy"]}"/>')
    else:
        o.append(f'<path d="{lf.half(shade_side)}" fill="{shade}"/>')
    # lateral veins dropped (they cannot be print-safe without crowding the dots); midrib opaque
    o.append(f'<path d="{lf.midrib_d(0, 0.88)}" fill="none" stroke="{mix(fill, P["sage"], 0.42)}" '
             f'stroke-width="{LINE_W}" stroke-linecap="round"/>')
    sm = EDGE_DEPTH * lf.L + 1.5 if face == "edge" else 0.0     # keep dots off the turned-over band
    for dia, ds in sorted(lf.dots(density=density, seed=dot_seed, small_margin=sm).items()):
        o.append(f'<path d="{"".join(ds)}" stroke="{DOT}" stroke-width="{f(dia)}" stroke-linecap="round"/>')
    if face == "fold":
        # underside half gets a faint rose midrib edge only; hide the dots there
        o.append(f'<path d="{lf.half("l")}" fill="{P["burgundy"]}"/>')
        o.append(f'<path d="{lf.midrib_d(0, 0.9)}" fill="none" stroke="{mix(P["burgundy"], P["rose"], 0.6)}" '
                 f'stroke-width="{LINE_W}" stroke-linecap="round"/>')
    if face == "edge":
        # small-side margin turned over: a narrow burgundy band of underside
        o.append(f'<path d="{lf.turned_edge_d()}" fill="{P["burgundy"]}"/>')
    o.append("</g></g>")
    return "".join(o)


# ------------------------------------------------------------------ canes
def cane_svg(pts, w0, w1, color, node_fr, node_col):
    d = ribbon(pts, w0, w1, per=8)
    cid = uid("cn")
    o = [f'<clipPath id="{cid}"><path id="{cid}p" d="{d}"/></clipPath>', f'<use href="#{cid}p" fill="{color}"/>']
    rings = []
    for (p, a), fr in zip(along(pts, node_fr), node_fr):
        w = w0 + (w1 - w0) * fr
        rings.append(f'<path d="M{f(-w)} -0.4Q0 2.2 {f(w)} -0.4" transform="{T(p[0], p[1], a)}"/>')
    o.append(f'<g clip-path="url(#{cid})" fill="none" stroke="{node_col}" stroke-width="{LINE_W}">{"".join(rings)}</g>')
    return "".join(o)


def petiole(node, attach, rot, w0, w1, color, tuck=10, rot0=None):
    """Petiole leaving the cane at rot0 (steeper than the blade) and arcing over into
    the leaf's own direction (rot), so the blade hangs off it like a wing."""
    a = math.radians(rot)
    inner = (attach[0] + math.sin(a) * tuck, attach[1] - math.cos(a) * tuck)
    ln = math.hypot(attach[0] - node[0], attach[1] - node[1])
    a0 = math.radians(rot if rot0 is None else rot0)
    c1 = (node[0] + math.sin(a0) * ln * 0.5, node[1] - math.cos(a0) * ln * 0.5)
    c2 = (attach[0] - math.sin(a) * ln * 0.35, attach[1] + math.cos(a) * ln * 0.35)
    pts = []
    for i in range(4):
        t = i / 3
        u = 1 - t
        pts.append(tuple(u ** 3 * node[j] + 3 * u * u * t * c1[j] + 3 * u * t * t * c2[j] + t ** 3 * attach[j] for j in (0, 1)))
    return f'<path d="{ribbon(pts + [inner], w0, w1, per=6)}" fill="{color}"/>'


# ------------------------------------------------------------------ flowers
def flower_cluster(anchor, rot=0, hub=None):
    """Pendant cyme: arching peduncle, then 3 open male flowers + 2 buds."""
    ax, ay = anchor
    o = []
    if hub is None:
        ped = [(ax, ay), (ax + 16, ay - 10), (ax + 34, ay - 2), (ax + 42, ay + 22)]
    else:  # rises from the node ring, one arch out and down to the hub
        hx, hy = hub
        ped = [(ax, ay), (ax + (hx - ax) * 0.3, hy - 2), (ax + (hx - ax) * 0.68, hy - 10), (hx, hy)]
    o.append(f'<path d="{ribbon(ped, 3.4, 2.4, per=6)}" fill="{P["plum"]}"/>')
    hub = ped[-1]
    # (dx, dy, size, tilt, kind)
    blooms = [(-22, 30, 15, -14, "open"), (20, 38, 16, 12, "open"), (-2, 68, 14, 4, "open"),
              (38, 14, 6.5, 38, "bud"), (-36, 58, 6, -30, "bud")]
    for dx, dy, sz, tilt, kind in blooms:
        cx, cy = hub[0] + dx, hub[1] + dy
        top = (cx, cy - sz * (0.95 if kind == "open" else 0.9))
        mid = ((hub[0] + top[0]) / 2 + dx * 0.12, (hub[1] + top[1]) / 2 - 5)
        o.append(f'<path d="{ribbon([hub, mid, top], 2.5, 1.8, per=5)}" fill="{P["plum"]}"/>')
    for dx, dy, sz, tilt, kind in blooms:
        cx, cy = hub[0] + dx, hub[1] + dy
        g = [f'<g transform="{T(cx, cy, tilt)}">']
        if kind == "bud":
            g.append(f'<path d="M0 {f(-sz)}C{f(sz * 0.9)} {f(-sz * 0.7)} {f(sz * 0.8)} {f(sz * 0.7)} 0 {f(sz)}'
                     f'C{f(-sz * 0.8)} {f(sz * 0.7)} {f(-sz * 0.9)} {f(-sz * 0.7)} 0 {f(-sz)}Z" fill="{P["rose"]}"/>')
        else:
            s_ = sz
            # two narrow inner tepals (behind), one merged pair of broad outer tepals
            g.append(f'<ellipse cx="0" cy="{f(-s_ * 0.62)}" rx="{f(s_ * 0.28)}" ry="{f(s_ * 0.46)}" fill="{P["rose"]}"/>')
            g.append(f'<ellipse cx="0" cy="{f(s_ * 0.62)}" rx="{f(s_ * 0.28)}" ry="{f(s_ * 0.46)}" fill="{P["rose"]}"/>')
            k = s_
            g.append(f'<path d="M0 {f(-k * 0.42)}C{f(k * 0.25)} {f(-k * 0.78)} {f(k * 1.08)} {f(-k * 0.72)} {f(k * 1.08)} 0'
                     f'C{f(k * 1.08)} {f(k * 0.72)} {f(k * 0.25)} {f(k * 0.78)} 0 {f(k * 0.42)}'
                     f'C{f(-k * 0.25)} {f(k * 0.78)} {f(-k * 1.08)} {f(k * 0.72)} {f(-k * 1.08)} 0'
                     f'C{f(-k * 1.08)} {f(-k * 0.72)} {f(-k * 0.25)} {f(-k * 0.78)} 0 {f(-k * 0.42)}Z" fill="{P["blush"]}"/>')
            g.append(f'<circle cx="0" cy="0" r="{f(s_ * 0.27)}" fill="{P["mustard"]}"/>')
        g.append("</g>")
        o.append("".join(g))
    return "".join(o)


# ------------------------------------------------------------------ plant
def build():
    back, front = pot(kind="classic", rim_y=584, rx=100, base_w=70, band=True)
    CANE = P["sage"]
    NODE = P["plum"]

    # three canes leave the soil apart and lean three ways: left cane out to the left,
    # centre cane a soft S leaning a little right, right cane out to the right
    RX_TIP = (458, 318)
    canes = {
        "L": dict(pts=[(262, 606), (255, 524), (236, 446), (210, 376), (186, 318), (172, 276)],
                  w=(11.5, 6), nodes=[0.3, 0.52, 0.72, 0.88]),
        "R": dict(pts=[(332, 606), (344, 530), (368, 466), (400, 412), (432, 370)],
                  w=(11, 5.8), nodes=[0.3, 0.55, 0.78, 0.92],
                  # drawn on past the big leaf so the small top leaf's join shows
                  ext=[(RX_TIP[0] - 12, RX_TIP[1] + 24), RX_TIP]),
        "C": dict(pts=[(297, 606), (301, 520), (296, 430), (298, 340), (310, 250), (326, 178), (338, 142)],
                  w=(13, 6.5), nodes=[0.22, 0.4, 0.56, 0.7, 0.83, 0.93]),
    }
    nodes = {k: along(v["pts"], v["nodes"]) for k, v in canes.items()}

    # (cane, node index or 'tip', rot, L, mirror, fill, face, bend, seed, layer)
    # rot: direction of the leaf tip, degrees clockwise from straight up.
    # layer: 0 behind all canes, 1 after L/R canes, 2 after C cane, 3 in front of pot
    specs = [
        # angel wings: the older blades hang well below level and arch under their weight;
        # a few small young leaves near the tips stay up and straighter
        ("C", 4, -74, 138, True, "night", "top", 0.22, 11, 0),
        ("C", 5, 64, 108, False, "deep", "top", 0.2, 12, 2),
        ("L", "tip", -30, 74, True, "deep", "under", 0.1, 13, 1),
        ("L", 3, -112, 116, True, "deep", "top", 0.22, 22, 0),
        ("L", 2, -138, 166, True, "deep", "top", 0.26, 21, 1),
        ("L", 1, -158, 150, True, "forest", "top", 0.18, 23, 1),
        ("R", "tip", 30, 80, False, "forest", "top", 0.1, 31, 1),
        ("R", 3, 126, 128, False, "deep", "top", 0.24, 32, 1),
        ("R", 1, 150, 158, False, "forest", "top", 0.22, 33, 1),
        ("C", "tip", 8, 78, False, "mid", "top", 0.08, 41, 2),
        ("C", 3, 122, 158, False, "mid", "top", 0.26, 42, 2),
        ("C", 2, -126, 184, True, "mid", "top", 0.26, 43, 2),
        ("C", 1, 162, 204, False, "mid", "edge", 0.1, 44, 3),  # drapes in front: tip crosses the rim band, ends on the body
    ]

    def node_of(c, i):
        if i == "tip":
            p = canes[c]["pts"] + canes[c].get("ext", [])
            a = math.degrees(math.atan2(p[-1][0] - p[-2][0], -(p[-1][1] - p[-2][1])))
            return p[-1], a
        return nodes[c][i]

    def draw_leaf(sp):
        c, i, rot, L, mir, fill, face, bend, seed, _ = sp
        (nx, ny), ca = node_of(c, i)
        cw = canes[c]["w"][1]
        if i == "tip":
            at = (nx, ny)
            pet = ""
        else:
            plen = 16 + L * 0.06
            # the petiole springs up out of the node (between cane and blade direction)
            rot0 = ca + (rot - ca) * 0.45
            a = math.radians((rot0 + rot) / 2)
            at = (nx + math.sin(a) * plen, ny - math.cos(a) * plen)
            pet = petiole((nx, ny), at, rot, cw * 0.95, cw * 0.7, CANE, tuck=12, rot0=rot0)
        lf = AngelLeaf(L, seed=seed, bend=bend, lobe=1.0 if L > 130 else 0.85, wave=0.0065)
        return pet + leaf_svg(lf, at[0], at[1], rot, mirror=mir, fill=fill, face=face,
                              dot_seed=seed * 7, shade_side="l")

    o = [back]
    layer = lambda n: [draw_leaf(s) for s in specs if s[-1] == n]
    o += layer(0)
    for k in ("L", "R"):
        v = canes[k]
        if "ext" in v:  # longer cane, same node rings (re-found on the extended curve)
            pts = v["pts"] + v["ext"]
            o.append(cane_svg(pts, v["w"][0], v["w"][1], CANE, refrac(pts, nodes[k]), NODE))
        else:
            o.append(cane_svg(v["pts"], v["w"][0], v["w"][1], CANE, v["nodes"], NODE))
    o += layer(1)
    v = canes["C"]
    o.append(cane_svg(v["pts"], v["w"][0], v["w"][1], CANE, v["nodes"], NODE))
    o += layer(2)
    # peduncle from the lower node ring (R[2]), below the mid-green leaf; hub kept where
    # it was (x+42, y+22 from node R[3]) so the flowers do not move
    (n3x, n3y), _ = nodes["R"][3]
    o.append(flower_cluster(nodes["R"][2][0], hub=(n3x + 42, n3y + 22)))
    o.append(front)
    o += layer(3)
    return "".join(o)


if __name__ == "__main__":
    reset_ids()
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "out", "begonia_maculata.svg")
    open(out, "w").write(svg_doc(build(), "Begonia maculata"))
    print("wrote", out, os.path.getsize(out))
