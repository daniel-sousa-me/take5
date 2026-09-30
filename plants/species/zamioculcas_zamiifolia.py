"""ZZ plant (Zamioculcas zamiifolia) -- v4.

Six pinnate stalks fanned from swollen bases at the soil.  Each stalk is
bare for its lower third, then carries near-opposite, slightly offset,
sessile glossy leaflets that shrink toward the tip.  Stalks alternate
between two leaf tones and are layered back (centre) -> front (outer).
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import PAL, SHADE, Leaf, cr_path, cr_sample, f, uid, reset_ids, pot, svg_doc  # noqa: E402

P = PAL

# ------------------------------------------------------------------ helpers
def resample(pts, per=14):
    s = cr_sample(pts, per)
    acc = [0.0]
    for a, b in zip(s, s[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return s, acc


def at(s, acc, fr):
    """point + tangent angle (deg, 0 = up, clockwise +) at arc fraction."""
    tot = acc[-1]
    tgt = fr * tot
    i = next((k for k in range(1, len(acc)) if acc[k] >= tgt), len(acc) - 1)
    a, b = s[i - 1], s[i]
    u = (tgt - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
    p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
    return p, math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1])))


def stalk_path(pts, wfun, n=40, end=1.0):
    """Tapered stalk with an arbitrary width profile wfun(u), u in 0..1."""
    s, acc = resample(pts, 16)
    L, R = [], []
    for i in range(n + 1):
        u = i / n
        p, ang = at(s, acc, u * end)
        a = math.radians(ang)
        nx, ny = math.cos(a), math.sin(a)  # right-hand normal of the tangent
        w = wfun(u) / 2
        L.append((p[0] - nx * w, p[1] - ny * w))
        R.append((p[0] + nx * w, p[1] + ny * w))
    L, R = L[::2], R[::2]
    # the tip point sits a little AHEAD of the last width pair (a short convex
    # taper); at the same arc position it pinched the end into a V (two points)
    # (the last side points get zero handles too: the coarse spacing made the
    # spline overshoot there into two little horns either side of the tip)
    tip, _ = at(s, acc, min(1.0, end + 2.0 / acc[-1]))
    ring = L + [tip] + R[::-1]
    return cr_path(ring, closed=True, sharp={0, len(L) - 1, len(L) + 1, len(ring) - 1})


def leaflet_shape(L, k, curl):
    r = random.Random(k * 7 + 1)
    j = lambda v: v * r.uniform(0.95, 1.05)
    # elliptic, slightly broader below the middle, rounded wedge base, acute tip
    right = [(0.05, 0.08), (0.18, j(0.18)), (0.40, j(0.25)), (0.62, j(0.225)), (0.82, j(0.135)), (0.95, 0.045)]
    left = [(0.05, 0.08), (0.18, j(0.175)), (0.40, j(0.245)), (0.62, j(0.22)), (0.82, j(0.13)), (0.95, 0.04)]
    return Leaf(L, right, left, bend=curl * (0.07 + 0.03 * k))


LIGHT = (-0.55, -0.83)  # light from upper left
_DEFS = {}      # key -> gid
_MIN_L = {}     # key -> smallest leaflet length drawn with that def
_DEFS_SVG = []
U = 100.0  # unit leaflet length for the shared defs
SMALL = 42  # leaflets shorter than this get their own defs (with a relatively wider sheen)


def lum(c):
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def fat(poly):
    """4 * area / perimeter: the measure print_prep uses for a filled sliver's width."""
    A = abs(sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly)))) / 2
    P_ = sum(math.dist(poly[i], poly[i - 1]) for i in range(len(poly)))
    return 4 * A / P_


def sheen_pts(lf, sg, m):
    """Glossy lens on the lit half: outer / inner edge around a centre line, half-width scaled by m."""
    ts = (0.40, 0.60)
    outer = [(0.40, 0.125), (0.60, 0.12)]
    inner = [(0.60, 0.075), (0.40, 0.08)]
    o = [lf.pt(0.20, sg * 0.06)]
    for (t, wo), (_, wi) in zip(outer, inner[::-1]):
        c, h = (wo + wi) / 2, (wo - wi) / 2 * m
        o.append(lf.pt(t, sg * (c + h)))
    o.append(lf.pt(0.76, sg * 0.07))
    for (t, wi), (_, wo) in zip(inner, outer[::-1]):
        c, h = (wo + wi) / 2, (wo - wi) / 2 * m
        o.append(lf.pt(t, sg * (c - h)))
    return o


def leaflet_def(tone, k, curl, lit_right, small, L):
    key = (tone, k, curl, lit_right, small)
    _MIN_L[key] = min(L, _MIN_L.get(key, 1e9))
    if key not in _DEFS:
        _DEFS[key] = uid("zd")
    return _DEFS[key]


def emit_defs():
    for key, gid in _DEFS.items():
        _DEFS_SVG.append(leaflet_svg(gid, *key[:4], _MIN_L[key]))


def leaflet_svg(gid, tone, k, curl, lit_right, min_len):
    lf = leaflet_shape(U, k, curl)
    d = lf.path()
    cid = uid("zc")
    fill, shade, sheen, rib = tone
    sg = 1 if lit_right else -1
    # flat turned-away half: a simple polygon hugging the (slightly curved) midrib
    ax = [lf.axis(t) for t in (-0.1, 0.3, 0.6, 1.1)]
    far = [lf.pt(t, -sg * 0.6) for t in (1.1, 0.6, 0.3, -0.1)]
    half = "M" + "L".join(f"{f(p[0])} {f(p[1])}" for p in ax + far) + "Z"
    # glossy sheen: slim lens on the lit half, following the leaf curve
    # Print policy: the sheen must print on the smallest leaflet using this def (light >= 4.5 units,
    # dark >= 3.5 units wide), so small leaflets get a relatively fuller lens; the hairline midrib is gone
    # (the shade/lit split already draws the midrib line).
    need = (4.5 if lum(sheen) > 0.55 else 3.5) * 1.04
    m = 1.0
    while fat(cr_sample(sheen_pts(lf, sg, m) + [sheen_pts(lf, sg, m)[0]], 8)) * min_len / U < need and m < 3.2:
        m += 0.05
    sp = sheen_pts(lf, sg, m)
    sheen_d = cr_path(sp, closed=True, sharp={0, 3})
    return (f'<clipPath id="{cid}"><path d="{d}"/></clipPath>'
            f'<g id="{gid}"><path d="{d}" fill="{fill}"/><g clip-path="url(#{cid})">'
            f'<path d="{half}" fill="{shade}"/><path d="{sheen_d}" fill="{sheen}"/>'
            f'</g></g>')


def leaflet(x, y, rot, L, tone, seed, curl):
    """Glossy sessile leaflet; base at (x,y), pointing along rot (deg)."""
    a = math.radians(rot)
    rn = (math.cos(a), math.sin(a))  # world direction of local +x (right side)
    lit_right = rn[0] * LIGHT[0] + rn[1] * LIGHT[1] > 0
    gid = leaflet_def(tone, seed % 2, curl, lit_right, L < SMALL, L)
    return (f'<use href="#{gid}" transform="translate({f(x)} {f(y)}) rotate({f(rot)}) '
            f'scale({L / U:.3f})"/>')


# tone = (fill, shade, sheen, midrib)
DARK = (P["deep"], SHADE[P["deep"]], P["mid"], P["night"])
MIDT = (P["mid"], SHADE[P["mid"]], P["light"], P["deep"])
FOR = (P["forest"], SHADE[P["forest"]], P["sage"], P["night"])


def zz_stalk(pts, tone, rachis, lmax, bare=0.36, base_w=19, spread=(56, 38), seed=0,
             gap=1.0, top=0.93, tip_scale=0.5, skip=()):
    r = random.Random(seed)
    s, acc = resample(pts, 16)
    tot = acc[-1]
    out = []
    leaves = []
    # walk up the rachis; spacing follows leaflet size so same-side
    # neighbours never overlap (leaflet width ~0.43 L)
    pos, k = bare * tot, 0
    z0, z1 = bare * tot, top * tot
    while pos < z1:
        u = (pos - z0) / (z1 - z0)
        # small near the base, fullest just below the middle, small again at the tip
        size = lmax * (0.66 + 1.25 * u - 1.3 * u * u) * r.uniform(0.93, 1.07)
        dev = spread[0] + (spread[1] - spread[0]) * u
        step = gap * 0.56 * size / math.sin(math.radians(dev))
        off = step * r.uniform(0.2, 0.28) * (1 if seed % 2 else -1)
        for side, dp in ((-1, -off / 2), (1, off / 2)):
            if (k, side) in skip:
                continue
            tt = (pos + dp) / tot
            p, ang = at(s, acc, tt)
            rot = ang + side * (dev + r.uniform(-4, 4))
            leaves.append((tt, p, rot, size, r.randint(0, 999), -side))
        pos += step
        k += 1
    # terminal leaflet sits just beyond the last pair; the rachis ends under it
    end = min((pos - step * 0.35) / tot, 1.0)
    p, ang = at(s, acc, end)
    leaves.append((end, p, ang + r.uniform(-3, 3), lmax * tip_scale, r.randint(0, 999), 0))
    for tt, p, rot, size, sd, cu in sorted(leaves, key=lambda v: v[0]):
        out.append(leaflet(p[0], p[1], rot, size, tone, sd, cu))

    tipw = 2.6
    nodes = [(0.0, 0.95), (0.045, 1.22), (0.11, 0.92), (0.2, 0.52), (1.0, None)]

    def wfun(u):
        # bulbous base sitting on the soil, a waist, then a long gentle taper
        if u >= 0.2:
            k = (u - 0.2) / 0.8
            return base_w * 0.52 + (tipw - base_w * 0.52) * k ** 0.9
        for (u0, w0), (u1, w1) in zip(nodes, nodes[1:]):
            if u0 <= u <= u1:
                k = (u - u0) / (u1 - u0)
                k = k * k * (3 - 2 * k)
                return base_w * (w0 + (w1 - w0) * k)

    col, mot = rachis
    sp = stalk_path(pts, wfun, end=end + 0.01)
    sid = uid("zs")
    out.append(f'<clipPath id="{sid}"><path d="{sp}"/></clipPath><path d="{sp}" fill="{col}"/>')
    # ZZ petiole bases carry darker transverse mottling: a few irregular flecks
    fl = []
    u = 0.05
    while u < 0.24:
        p, ang = at(s, acc, u)
        a = math.radians(ang)
        w = wfun(u) / 2
        c = r.uniform(-0.45, 0.45) * w
        ln = w * r.uniform(0.35, 0.6)
        n = (math.cos(a), math.sin(a))
        q0 = (p[0] + n[0] * (c - ln), p[1] + n[1] * (c - ln))
        q1 = (p[0] + n[0] * (c + ln), p[1] + n[1] * (c + ln))
        fl.append(f"M{f(q0[0])} {f(q0[1])}L{f(q1[0])} {f(q1[1])}")
        u += r.uniform(0.05, 0.085)   # fewer, print-weight flecks (3 units)
    out.append(f'<g clip-path="url(#{sid})"><path d="{"".join(fl)}" stroke="{mot}" stroke-width="3" '
               f'stroke-linecap="round"/></g>')
    return "".join(out)


RIM = 578


def build():
    reset_ids()
    _DEFS.clear()
    _DEFS_SVG.clear()
    back, front = pot(kind="classic", rx=96, rim_y=RIM, base_w=66, band=True)
    B = RIM + 12
    # mottle colours are pre-blended solids (deep/night over the rachis @32 %)
    S_DK = (P["sage"], "#6B7E63")
    S_FO = (P["forest"], "#384F3B")
    stalks = [
        # back: centre tallest (dark)
        dict(pts=[(300, B), (296, 470), (286, 330), (290, 190), (308, 56)], tone=DARK,
             rachis=S_DK, lmax=68, base_w=20, seed=3, bare=0.40, skip={(0, -1)},
             spread=(58, 36)),
        # left upright (mid): the longest, bowing out and arching over at the top
        dict(pts=[(290, B), (262, 486), (220, 360), (160, 250), (96, 192), (62, 190)], tone=MIDT,
             rachis=S_FO, lmax=62, base_w=18, seed=11, bare=0.36, spread=(62, 40)),
        # right upright (mid): shorter, steeper and almost straight
        dict(pts=[(310, B), (330, 486), (360, 380), (392, 290), (418, 222)], tone=MIDT,
             rachis=S_FO, lmax=54, base_w=18, seed=7, bare=0.38, spread=(52, 42)),
        # left arching (dark, front): long, low and drooping at the tip
        dict(pts=[(284, B), (238, 530), (168, 482), (104, 462), (58, 478)], tone=DARK,
             rachis=S_DK, lmax=56, base_w=17, seed=21, bare=0.40, spread=(58, 40)),
        # right arching (dark, front): short, lifting rather than drooping
        dict(pts=[(318, B), (372, 530), (432, 474), (478, 420), (506, 380)], tone=DARK,
             rachis=S_DK, lmax=46, base_w=16, seed=5, bare=0.46, spread=(54, 34)),
    ]
    body = [back]
    for st in stalks:
        body.append(zz_stalk(**st))
    body.append(front)
    emit_defs()
    return "<defs>" + "".join(_DEFS_SVG) + "</defs>" + "".join(body)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "out", "zamioculcas_zamiifolia.svg")
    with open(out, "w") as fh:
        fh.write(svg_doc(build(), "Zamioculcas zamiifolia (ZZ plant)"))
    print(out, os.path.getsize(out))
