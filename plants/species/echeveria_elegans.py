"""Echeveria elegans (Mexican snowball) - v4 generator.
python3 species/echeveria_elegans.py  -> out/echeveria_elegans.svg

Each rosette is built as explicit concentric tiers of thick spoon-shaped leaves
(flat, slightly creased upper face + keeled underside) in 3-D, projected from a
3/4 camera and painted outer tier -> inner tier, back -> front, so the spiral
tiers stay geometrically exact.  Per leaf: silhouette (side / thickness tone),
upper face in its shaded tone, the lit half of the face, and a blush tip.
Paths are written relative on a half-pixel grid (scale .5) to keep the file small.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, cr_sample, uid, reset_ids, pot, svg_doc  # noqa: E402

try:
    from shapely.geometry import Polygon, Point
    from shapely.ops import unary_union
except Exception:  # culling is an optimisation only
    Polygon = None

P = PAL
CX = 300
RIM_Y = 598
RIM_H = 28
EL = math.radians(30)                      # camera elevation
CE, SE = math.cos(EL), math.sin(EL)
V = (0.0, -CE, SE)                          # towards the camera
LIGHT = (-0.62, -0.25, 0.74)                # upper-left-front
_m = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _m for c in LIGHT)

# powdery blue-green ramp: a slightly bluer extension of PAL sage / light / pale
RAMP = ["#4A6155", "#5A7165", "#6B8377", "#7F968A", "#94AB9F", "#AABFB4", "#C0D1C7", "#D5E1D8",
        "#E4ECE4"]
TIP_SIDE = P["rose"]
TIP_TOP = "#DDA6A2"                          # between PAL blush and its lighter tint
TIP_TOP_HI = "#E8BDB6"


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm(v):
    m = math.sqrt(dot(v, v)) or 1
    return tuple(c / m for c in v)


# ------------------------------------------------------------------ path encoding
class Enc:
    """Catmull-Rom -> relative cubic bezier on a 0.5 px grid (drawn in a scale(.5) group)."""

    @staticmethod
    def q(p):
        return (round(p[0] * 2), round(p[1] * 2))

    @staticmethod
    def poly(pts):
        cur = Enc.q(pts[0])
        out = [f"M{cur[0]} {cur[1]}l"]
        nums = []
        for p in pts[1:]:
            e = Enc.q(p)
            nums += [e[0] - cur[0], e[1] - cur[1]]
            cur = e
        s = ""
        for j, v in enumerate(nums):
            t = str(v)
            s += t if (j == 0 or t.startswith("-")) else " " + t
        return out[0] + s + "z"

    @staticmethod
    def path(pts, sharp=(), closed=True, k=1.0):
        n = len(pts)
        sharp = set(sharp)
        segs = n if closed else n - 1
        cur = Enc.q(pts[0])
        out = [f"M{cur[0]} {cur[1]}"]
        for i in range(segs):
            p1, p2 = pts[i], pts[(i + 1) % n]
            p0 = pts[(i - 1) % n] if (closed or i > 0) else p1
            p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
            c1 = p1 if i in sharp else (p1[0] + (p2[0] - p0[0]) / 6 * k, p1[1] + (p2[1] - p0[1]) / 6 * k)
            c2 = p2 if ((i + 1) % n) in sharp else (p2[0] - (p3[0] - p1[0]) / 6 * k,
                                                     p2[1] - (p3[1] - p1[1]) / 6 * k)
            a, b, e = Enc.q(c1), Enc.q(c2), Enc.q(p2)
            nums = [a[0] - cur[0], a[1] - cur[1], b[0] - cur[0], b[1] - cur[1], e[0] - cur[0], e[1] - cur[1]]
            s = "c"
            for j, v in enumerate(nums):
                t = str(v)
                s += t if (j == 0 or t.startswith("-")) else " " + t
            out.append(s)
            cur = e
        if closed:
            out.append("z")
        return "".join(out)


def ribbon_d(pts, w0, w1, per=5):
    """core.ribbon, but encoded on the half-pixel grid."""
    s = cr_sample(pts, per)
    n = len(s)
    L, R = [], []
    for i, p in enumerate(s):
        a, b = s[max(i - 1, 0)], s[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy / m, dx / m
        w = (w0 + (w1 - w0) * (i / (n - 1))) / 2
        L.append((p[0] + nx * w, p[1] + ny * w))
        R.append((p[0] - nx * w, p[1] - ny * w))
    step = max(1, per // 2)
    Ls = L[::step] + ([L[-1]] if (n - 1) % step else [])
    Rs = R[::step] + ([R[-1]] if (n - 1) % step else [])
    ring = Ls + Rs[::-1]
    return Enc.path(ring, sharp={0, len(ring) - 1})


# ------------------------------------------------------------------ 3-D leaf
WP = [(0, .34), (.12, .46), (.28, .64), (.44, .82), (.58, .95), (.70, 1.0), (.80, .93),
      (.89, .70), (.95, .40), (1.0, 0.0)]          # spatulate / spoon half-width profile
TP = [(0, .35), (.2, .9), (.4, 1.0), (.65, .8), (.88, .45), (1.0, 0.0)]   # keel thickness profile
US = [.16, .44, .70, .88]                # edge stations (base + tip added)


def interp(tab, u):
    for (a, wa), (b, wb) in zip(tab, tab[1:]):
        if a <= u <= b:
            return wa + (wb - wa) * (u - a) / (b - a)
    return tab[-1][1]


class Leaf3:
    def __init__(self, phi, alpha, L, W, T, curl, r0, z0, cup, tone):
        self.phi, self.alpha, self.L, self.W, self.T = phi, alpha, L, W, T
        self.cup, self.tone = cup, tone
        d = (math.cos(phi), math.sin(phi), 0.0)
        self.d, self.lat = d, (-math.sin(phi), math.cos(phi), 0.0)
        n = 40
        pts, nrm = [], []
        x, y, z = d[0] * r0, d[1] * r0, z0
        for i in range(n + 1):
            u = i / n
            th = alpha + curl * u ** 1.7          # the spoon tip curls upwards
            pts.append((x, y, z))
            nrm.append((-math.sin(th) * d[0], -math.sin(th) * d[1], math.cos(th)))
            st = L / n
            x += math.cos(th) * d[0] * st
            y += math.cos(th) * d[1] * st
            z += math.sin(th) * st
        self._p, self._n = pts, nrm

    def mid(self, u):
        i = min(int(u * 40), 39)
        s = u * 40 - i
        a, b, na, nb = self._p[i], self._p[i + 1], self._n[i], self._n[i + 1]
        return (tuple(a[k] + (b[k] - a[k]) * s for k in range(3)),
                tuple(na[k] + (nb[k] - na[k]) * s for k in range(3)))

    def edge(self, u, side):
        p, n = self.mid(u)
        w = self.W * interp(WP, u)
        return tuple(p[k] + side * w * self.lat[k] + self.cup * w * n[k] for k in range(3))

    def keel(self, u):
        p, n = self.mid(u)
        t = self.T * interp(TP, u)
        return tuple(p[k] - t * n[k] for k in range(3))

    def belly(self, u, side):
        """Rounded underside between the margin and the keel."""
        p, n = self.mid(u)
        w = self.W * interp(WP, u)
        t = self.T * interp(TP, u)
        return tuple(p[k] + side * 0.72 * w * self.lat[k] - 0.78 * t * n[k] for k in range(3))

    def normal(self, u=0.62):
        return self.mid(u)[1]

    def depth(self):
        return dot(self.mid(0.6)[0], V)


DROOP = [6, 8, 0, 0, 0, 0, 0]   # front leaves of the outer tiers flop forward a little
LIFT = 18            # rosette raised so only its lowest leaves go behind the rim band
MSCALE = 1.56
PUPS = [(420, 614, .96), (182, 618, .72)]   # offsets sitting on the rim: x, y, scale
UNDER_BLUSH = False  # rose tip on leaves seen from below (they only peek out as slivers)
TIP_R = 0.5          # drop a side blush whose leaf tip is hidden ...
SLIVER = 1.2         # ... or whose visible part is thinner than this (mean half-width)
FRONT_CAP = 0.35     # leaves pointing at the viewer get their side blush in the face blush


def rosette(tiers, phase=0.0, twist=0.0, scale=1.0, tone_shift=0, jit=0.0, seed=1):
    """tiers: (n, alpha_deg, L, Wfrac, r0, z0, tone). Leaves in a tier are evenly
    spaced; each tier is rotated half a step + `twist` so leaves sit in the gaps."""
    out = []
    rot = phase
    j = seed
    for ti, (n, a, L, wf, r0, z0, tone) in enumerate(tiers):
        step = 2 * math.pi / n
        tier = []
        for i in range(n):
            j = (j * 9301 + 49297) % 233280
            r = j / 233280 - 0.5
            phi = rot + i * step + r * jit
            Ls = L * scale * (1 + r * 0.06)
            fr = max(0.0, -math.sin(phi)) ** 1.5
            dr = DROOP[ti] if ti < len(DROOP) else 0
            lf = Leaf3(phi, math.radians(a + r * 4 - dr * fr), Ls, Ls * wf, Ls * 0.17,
                       curl=math.radians(26 - ti * 3), r0=r0 * scale, z0=z0 * scale,
                       cup=0.12, tone=tone + tone_shift)
            tier.append(lf)
        tier.sort(key=lambda lf: lf.depth())
        out.append(tier)
        rot += step / 2 + twist
    return out


# ------------------------------------------------------------------ 2-D faces
def proj(p, ox, oy):
    return (ox + p[0], oy - p[2] * CE - p[1] * SE)


def faces(lf, ox, oy, u_start=0.0):
    """Projected faces.  Stations S start at u_start: 0 for leaves seen from above;
    for leaves seen from below the part hidden in the axil (u < US[0]) is dropped so
    no narrow wedge of leaf base pokes out beneath the next tier."""
    pr = lambda p: proj(p, ox, oy)  # noqa: E731
    S = [u_start] + [u for u in US if u > u_start + 1e-6]
    tip = pr(lf.mid(1.0)[0])
    R = [pr(lf.edge(u, 1)) for u in S]
    Lf = [pr(lf.edge(u, -1)) for u in S]
    K = [pr(lf.keel(u)) for u in S]
    M = [pr(lf.mid(u)[0]) for u in S]
    B = [[pr(lf.belly(u, sd)) for u in S] for sd in (1, -1)]
    # silhouette: per station the extreme projected point on each side
    sr, sl = [], []
    for i, u in enumerate(S):
        a = pr(lf.mid(max(u - .03, 0))[0])
        b = pr(lf.mid(u + .03)[0])
        t = (b[0] - a[0], b[1] - a[1])
        m = math.hypot(*t) or 1
        nx, ny = -t[1] / m, t[0] / m
        if (R[i][0] - M[i][0]) * nx + (R[i][1] - M[i][1]) * ny < 0:
            nx, ny = -nx, -ny
        cand = [R[i], Lf[i], K[i], B[0][i], B[1][i]]
        key = lambda p: (p[0] - M[i][0]) * nx + (p[1] - M[i][1]) * ny  # noqa: E731
        sr.append(max(cand, key=key))
        sl.append(min(cand, key=key))
    # blunt, clasping leaf base
    sil = [sl[0]] + sr + [tip] + sl[1:][::-1]
    top = [Lf[0]] + R + [tip] + Lf[1:][::-1]
    return dict(tip=tip, R=R, L=Lf, K=K, M=M, sil=sil, top=top, n=len(S) - 1)


def half_pts(F, side, under=False):
    """Lit/shaded half of the visible surface: edge -> tip -> midline (or keel)."""
    E = F["R"] if side > 0 else F["L"]
    inner = F["K"] if under else F["M"]
    return [inner[0]] + E + [F["tip"]] + inner[1:][::-1]


def tip_pts(lf, ox, oy, u0, top=True):
    """Blush at the leaf tip.  Upper face: a crescent hugging the margin that
    tapers back along both edges.  Side/keel: the whole cross-section near the tip."""
    pr = lambda p: proj(p, ox, oy)  # noqa: E731

    def e(u, side, ext):
        m = lf.mid(u)[0]
        q = lf.edge(u, side) if side else lf.keel(u)
        return pr(tuple(m[k] + ext * (q[k] - m[k]) for k in range(3)))
    m1, m0 = lf.mid(1.0)[0], lf.mid(0.97)[0]
    tipo = pr(tuple(m1[k] + (m1[k] - m0[k]) * 3 for k in range(3)))
    um = u0 + (1 - u0) * 0.55
    if top:
        pts = [e(u0, 1, 1.0), e(u0, 1, 1.5), e(um, 1, 1.6), tipo, e(um, -1, 1.6), e(u0, -1, 1.5),
               e(u0, -1, 1.0), e(um, -1, 0.8), pr(lf.mid(1 - (1 - u0) * 0.16)[0]), e(um, 1, 0.8)]
        return pts, {0, 1, 5, 6}
    # keel / side: convex hull of the (over-sized) cross-sections from u0 to the tip
    from shapely.geometry import MultiPoint
    cloud = [tipo]
    for u in (u0, um, 1 - (1 - u0) * 0.15):
        m = lf.mid(u)[0]
        for q in (lf.edge(u, 1), lf.edge(u, -1), lf.keel(u), lf.belly(u, 1), lf.belly(u, -1)):
            cloud.append(pr(tuple(m[k] + 1.5 * (q[k] - m[k]) for k in range(3))))
    hull = list(MultiPoint(cloud).convex_hull.exterior.coords)[:-1]
    return hull, set(range(len(hull)))


def poly(pts, sharp=()):
    if Polygon is None:
        return None
    # sample the same Catmull-Rom the path uses (sharp corners approximated)
    return Polygon(cr_sample(list(pts) + [pts[0]], 4)).buffer(0)


class Painter:
    """Collects shapes in paint order; emit() culls shapes that end up (almost)
    fully covered by later ones, at the level of individual faces."""

    def __init__(self):
        self.shapes = []     # dict(poly, svg, id, needs)

    def add(self, svg, pts=None, pid=None, needs=(), clip_poly=None, tip=None):
        pg = None
        if pts is not None and Polygon is not None:
            pg = poly(pts)
            if clip_poly is not None:
                pg = pg.intersection(clip_poly)
        self.shapes.append(dict(poly=pg, svg=svg, id=pid, needs=needs, cover=clip_poly is None, tip=tip))

    def extra(self, svg):
        self.shapes.append(dict(poly=None, svg=svg, id=None, needs=(), cover=False))

    def leaf(self, lf, ox, oy, tipu=0.76, blush=True):
        n_top = lf.normal()
        top_vis = dot(n_top, V) > 0.04
        F = faces(lf, ox, oy, 0.0 if top_vis else US[0])
        n = F["n"]
        b = 0.45
        halves = {}
        for s in (1, -1):
            if top_vis:
                nh = norm(tuple(n_top[k] * math.cos(b) + s * lf.lat[k] * math.sin(b) for k in range(3)))
            else:
                nh = norm(tuple(-n_top[k] * 0.5 + s * lf.lat[k] for k in range(3)))
            halves[s] = dot(nh, LIGHT)
        lit = 1 if halves[1] > halves[-1] else -1
        lam = dot(n_top if top_vis else tuple(-c for c in n_top), LIGHT)
        tone = lf.tone
        if top_vis:
            face_c = tone + (1 if lam > 0.55 else 0)
            lit_c, sil_c = face_c + 1, face_c - 2
        else:
            face_c, lit_c, sil_c = tone - 2, tone - 1, tone - 3
        c_sil, c_face, c_lit = [RAMP[max(0, min(len(RAMP) - 1, c))] for c in (sil_c, face_c, lit_c)]
        sid, fid = uid("s"), uid("t")
        sil_d = Enc.path(F["sil"], sharp={0, 1, n + 2})
        self.add(f'<path id="{sid}" d="{sil_d}" fill="{c_sil}"/>', F["sil"], pid=(sid, sil_d))
        silp = self.shapes[-1]["poly"]
        topp = None
        hs = {0, 1, n + 2}
        def side_tip(u0):
            # rose tip on the thickness band / underside (clipped to the silhouette)
            if not blush:
                return
            c1 = uid("k")
            tp, _ = tip_pts(lf, ox, oy, u0, top=False)
            # leaves pointing at the viewer show their tip's thickness as a band *below*
            # the face: paint it in the face's blush so the tip reads as one pink cap
            # instead of a loose rose crescent under the leaf
            col = TIP_TOP if -math.sin(lf.phi) > FRONT_CAP else TIP_SIDE
            self.add(f'<clipPath id="{c1}"><use href="#{sid}"/></clipPath>'
                     f'<path clip-path="url(#{c1})" d="{Enc.path(tp)}" fill="{col}"/>',
                     tp, needs=(sid,), clip_poly=silp, tip=proj(lf.mid(1.0)[0], ox, oy))
        if top_vis:
            side_tip(0.93)
            top_d = Enc.path(F["top"], sharp={0, 1, n + 2})
            self.add(f'<path id="{fid}" d="{top_d}" fill="{c_face}"/>', F["top"], pid=(fid, top_d))
            topp = self.shapes[-1]["poly"]
            hp = half_pts(F, lit)
            self.add(f'<path d="{Enc.path(hp, sharp=hs)}" fill="{c_lit}"/>', hp)
        else:
            for sd, c in ((lit, c_face), (-lit, c_lit)):
                hp = half_pts(F, sd, under=True)
                self.add(f'<path d="{Enc.path(hp, sharp=hs)}" fill="{c}"/>', hp)
            if UNDER_BLUSH:
                side_tip(0.93)
        if blush and top_vis:
            c2 = uid("k")
            tp, sh = tip_pts(lf, ox, oy, tipu, top=True)
            self.add(f'<clipPath id="{c2}"><use href="#{fid}"/></clipPath>'
                     f'<path clip-path="url(#{c2})" d="{Enc.path(tp, sharp=sh)}" fill="{TIP_TOP}"/>',
                     tp, needs=(fid,), clip_poly=topp)

    def emit(self, thr=2.5):
        keep = [True] * len(self.shapes)
        cover = None
        for i in range(len(self.shapes) - 1, -1, -1):
            sh = self.shapes[i]
            pg = sh["poly"]
            if pg is None:
                continue
            vis = pg if cover is None else pg.difference(cover)
            if vis.area < thr or (sh.get("tip") and cover is not None
                                  and cover.contains(Point(sh["tip"]).buffer(TIP_R))):
                # a rose tip whose leaf tip is hidden would only show as a loose crescent
                keep[i] = False
                continue
            if sh.get("tip") and vis.length and 2 * vis.area / vis.length < SLIVER:
                keep[i] = False      # ... and so would a thin visible band of one
                continue
            if sh["cover"]:
                cover = pg if cover is None else unary_union([cover, pg])
        needed = set()
        for sh, k in zip(self.shapes, keep):
            if k:
                needed.update(sh["needs"])
        out, defs = [], []
        for sh, k in zip(self.shapes, keep):
            if k:
                out.append(sh["svg"])
            elif sh["id"] and sh["id"][0] in needed:
                defs.append(f'<path id="{sh["id"][0]}" d="{sh["id"][1]}"/>')
        return (f"<defs>{''.join(defs)}</defs>" if defs else "") + "".join(out)


# ------------------------------------------------------------------ rosettes
MAIN = [  # n, alpha, L, Wfrac, r0, z0, tone
    (8, 5, 118, .36, 7, 0, 3),
    (8, 18, 105, .36, 5, 7, 4),
    (7, 42, 85, .38, 4, 14, 4),
    (6, 54, 64, .39, 3, 20, 4),
    (5, 66, 46, .40, 2, 25, 5),
    (4, 78, 30, .44, 1, 29, 6),
    (3, 86, 18, .48, 0, 32, 6),
]
PUP = [
    (6, 12, 104, .40, 6, 0, 2),
    (5, 34, 76, .42, 4, 10, 4),
    (4, 58, 50, .45, 4, 18, 5),
    (3, 80, 28, .50, 1, 24, 6),
]


def paint_rosette(pt, tiers, ox, oy, after_tier=None, hook=None, core=0, **kw):
    sc = kw.get("scale", 1.0)
    for ti, tier in enumerate(rosette(tiers, **kw)):
        for lf in tier:
            pt.leaf(lf, ox, oy)
        if hook is not None and ti == after_tier:
            hook(pt)
        if ti == core:
            # shadowed heart of the rosette: fills gaps between the inner tiers' bases
            r = tiers[0][2] * sc * 0.26
            cy = oy - tiers[1][5] * sc * CE
            pts = [(ox + r * math.cos(t * math.pi / 4), cy + r * 0.62 * math.sin(t * math.pi / 4))
                   for t in range(8)]
            pt.add(f'<path d="{Enc.path(pts)}" fill="{RAMP[1]}"/>', pts)


# ------------------------------------------------------------------ flower stalks
STALK = P["rose"]
STALK_SH = P["plum"]
BELL = "#DE9A86"          # coral between PAL blush and terra_hi
BELL_SH = "#C77F72"
BELL_TIP = P["mustard"]
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
    """Small fleshy sessile bract clasping the stalk (blue-green, like the leaves):
    its base sits across the stalk, the blade angles up and out to one side."""
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
    return (f'<path d="{Enc.path(pts, sharp={0, 4})}" fill="{BRACT_SH}"/>'
            f'<path d="{Enc.path(half, sharp={0, 4, 5})}" fill="{BRACT}"/>')


def bell(p, hang, s=1.0):
    """Pendent urn-shaped flower: pedicel from p, bell hanging along `hang`."""
    hx, hy = hang
    px, py = -hy, hx
    ped = 8 * s
    b0 = (p[0] + hx * ped, p[1] + hy * ped)
    L, W = 21 * s, 7.8 * s

    def at(t, w):
        return (b0[0] + hx * L * t + px * W * w, b0[1] + hy * L * t + py * W * w)
    body = [at(0, 0), at(.12, .62), at(.45, .98), at(.8, .92), at(1, .78),
            at(1.0, -.78), at(.8, -.92), at(.45, -.98), at(.12, -.62)]
    sh = [at(0, 0), at(.45, 0.05), at(.8, 0.02), at(1, 0.0), at(1.0, -.78), at(.8, -.92),
          at(.45, -.98), at(.12, -.62)]
    sep = [at(-.05, 0), at(.1, .7), at(.3, .55), at(.16, 0), at(.3, -.55), at(.1, -.7)]
    return "".join([
        f'<path d="{ribbon_d([p, ((p[0] + b0[0]) / 2 + px * 1.2, (p[1] + b0[1]) / 2 + py * 1.2), b0], 2.2 * s, 1.6 * s)}" fill="{STALK}"/>',
        f'<path d="{Enc.path(body, sharp={0, 4, 5})}" fill="{BELL}"/>',
        f'<path d="{Enc.path(sh, sharp={0, 3, 4})}" fill="{BELL_SH}"/>',
        f'<path d="{Enc.path(sep, sharp={0, 1, 2, 3, 4, 5})}" fill="{RAMP[4]}"/>',
    ])


def stalk_svg(pts, w0, w1, bracts, flowers, rise_side=1):
    """pts: base (hidden inside the rosette) -> nodding tip."""
    cid = uid("q")
    sd = ribbon_d(pts, w0, w1, per=5)
    out = [f'<path id="{cid}p" d="{sd}" fill="{STALK}"/>']
    # thin shaded edge on the side away from the light (right-hand side), clipped to the stalk
    sh_pts = [((a[0] + 0.4 * w0), a[1] + 0.1 * w0) for a in pts]
    out.append(f'<clipPath id="{cid}"><use href="#{cid}p"/></clipPath>'
               f'<path clip-path="url(#{cid})" d="{ribbon_d(sh_pts, w0 * 0.7, w1 * 0.7, per=5)}" '
               f'fill="{STALK_SH}" opacity=".45"/>')
    for i, t in enumerate(bracts):
        p, d = along(pts, t)
        out.append(bract(p, (d[0], d[1]), (-1) ** i * rise_side, L=20 - 5 * t, W=5.6 - 1.4 * t))
    for t, hang, s in flowers:
        p, d = along(pts, t)
        ang = math.degrees(math.atan2(-hang[0], hang[1]))
        out.append(f'<use href="#bell" transform="translate({round(p[0] * 2)} {round(p[1] * 2)}) '
                   f'rotate({ang:.0f}) scale({s:g})"/>')
    return "".join(out)


# ------------------------------------------------------------------ build
def build():
    reset_ids()
    back, front = pot(kind="bowl", cx=CX, rim_y=RIM_Y, bottom=752, rx=138, rim_h=RIM_H, base_w=96)
    pt = Painter()

    # short, tight arching stalks: they add the charm of the nodding coral
    # bells without setting the plant's height, so the rosette stays dominant
    stalk1 = [(x, y - LIFT) for x, y in [(296, 548), (296, 470), (300, 400), (318, 336), (350, 292), (390, 274),
              (424, 282), (446, 306), (452, 326)]]
    stalk2 = [(x, y - LIFT) for x, y in [(262, 552), (250, 492), (232, 446), (206, 414), (178, 404), (156, 414), (148, 428)]]
    # one-sided nodding raceme: flowers hang from the underside of the arch,
    # crowding towards the tip where they are still buds
    fl1 = [(0.60, (0.18, 1), 1.08), (0.68, (0.12, 1), 1.06), (0.76, (0.04, 1), 1.02),
           (0.83, (-0.08, 1), 0.96), (0.89, (-0.25, 1), 0.88), (0.945, (-0.45, 1), 0.78),
           (0.99, (-0.7, 1), 0.66)]
    fl2 = [(0.66, (-0.08, 1), 0.98), (0.79, (-0.06, 1), 0.92), (0.905, (0.12, 1), 0.82),
           (1.0, (0.45, 1), 0.68)]

    def hook(p):
        p.extra(stalk_svg(stalk2, 8.0, 4.0, [0.42], fl2, rise_side=-1))
        p.extra(stalk_svg(stalk1, 9.0, 4.2, [0.34, 0.46], fl1))

    paint_rosette(pt, MAIN, 290, RIM_Y - 20 - LIFT, after_tier=1, hook=hook, phase=0.2, twist=0.09,
                  scale=MSCALE)

    # the offsets: one pup drawn once (at the origin) and placed twice
    pup = Painter()
    paint_rosette(pup, PUP, 0, 0, phase=1.1, twist=-0.1, scale=0.64)
    defs = (f'<defs><g id="bell">{bell((0, 0), (0, 1), 1.0)}</g>'
            f'<g id="pup">{pup.emit()}</g></defs>')
    offsets = ''.join(f'<use href="#pup" transform="translate({round(x * 2)} {round(y * 2)}) scale({s:g})"/>'
                      for x, y, s in PUPS)
    # the rim band is drawn over the rosette's lowest leaves, so the rosette sits down
    # in the bowl like every other plant; the offsets sit on the rim, spilling over it
    main = f'<g transform="scale(.5)">{defs}{pt.emit()}</g>'
    return back + main + front + f'<g transform="scale(.5)">{offsets}</g>'


if __name__ == "__main__":
    doc = svg_doc(build(), "Echeveria elegans")
    out = os.path.join(os.path.dirname(HERE), "out", "echeveria_elegans.svg")
    with open(out, "w") as fh:
        fh.write(doc)
    print(out, len(doc))
