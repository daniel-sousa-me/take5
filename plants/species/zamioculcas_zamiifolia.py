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
    tip, _ = at(s, acc, end)
    ring = L + [tip] + R[::-1]
    return cr_path(ring, closed=True, sharp={0, len(ring) - 1})


def leaflet_shape(L, k, curl):
    r = random.Random(k * 7 + 1)
    j = lambda v: v * r.uniform(0.95, 1.05)
    # elliptic, slightly broader below the middle, rounded wedge base, acute tip
    right = [(0.05, 0.08), (0.18, j(0.18)), (0.40, j(0.25)), (0.62, j(0.225)), (0.82, j(0.135)), (0.95, 0.045)]
    left = [(0.05, 0.08), (0.18, j(0.175)), (0.40, j(0.245)), (0.62, j(0.22)), (0.82, j(0.13)), (0.95, 0.04)]
    return Leaf(L, right, left, bend=curl * (0.07 + 0.03 * k))


LIGHT = (-0.55, -0.83)  # light from upper left
_DEFS = {}
_DEFS_SVG = []
U = 100.0  # unit leaflet length for the shared defs


def leaflet_def(tone, k, curl, lit_right):
    key = (tone, k, curl, lit_right)
    if key in _DEFS:
        return _DEFS[key]
    lf = leaflet_shape(U, k, curl)
    d = lf.path()
    gid, cid = uid("zd"), uid("zc")
    fill, shade, sheen, rib = tone
    sg = 1 if lit_right else -1
    # flat turned-away half: a simple polygon hugging the (slightly curved) midrib
    ax = [lf.axis(t) for t in (-0.1, 0.3, 0.6, 1.1)]
    far = [lf.pt(t, -sg * 0.6) for t in (1.1, 0.6, 0.3, -0.1)]
    half = "M" + "L".join(f"{f(p[0])} {f(p[1])}" for p in ax + far) + "Z"
    # glossy sheen: slim lens on the lit half, following the leaf curve
    sp = [lf.pt(0.20, sg * 0.06), lf.pt(0.40, sg * 0.125), lf.pt(0.60, sg * 0.12),
          lf.pt(0.76, sg * 0.07), lf.pt(0.58, sg * 0.075), lf.pt(0.40, sg * 0.08)]
    sheen_d = cr_path(sp, closed=True, sharp={0, 3})
    mid_d = cr_path([lf.axis(t) for t in (0.03, 0.3, 0.6, 0.88)], closed=False)
    _DEFS_SVG.append(
        f'<clipPath id="{cid}"><path d="{d}"/></clipPath>'
        f'<g id="{gid}"><path d="{d}" fill="{fill}"/><g clip-path="url(#{cid})">'
        f'<path d="{half}" fill="{shade}"/><path d="{sheen_d}" fill="{sheen}"/>'
        f'<path d="{mid_d}" fill="none" stroke="{rib}" stroke-width="2.2" stroke-linecap="round" opacity=".5"/>'
        f'</g></g>')
    _DEFS[key] = gid
    return gid


def leaflet(x, y, rot, L, tone, seed, curl):
    """Glossy sessile leaflet; base at (x,y), pointing along rot (deg)."""
    a = math.radians(rot)
    rn = (math.cos(a), math.sin(a))  # world direction of local +x (right side)
    lit_right = rn[0] * LIGHT[0] + rn[1] * LIGHT[1] > 0
    gid = leaflet_def(tone, seed % 2, curl, lit_right)
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
        size = lmax * (0.9 + 0.35 * u - 0.72 * u * u) * r.uniform(0.95, 1.05)
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
        u += r.uniform(0.035, 0.07)
    out.append(f'<g clip-path="url(#{sid})"><path d="{"".join(fl)}" stroke="{mot}" stroke-width="2.2" '
               f'stroke-linecap="round" opacity=".32"/></g>')
    return "".join(out)


RIM = 578


def build():
    reset_ids()
    _DEFS.clear()
    _DEFS_SVG.clear()
    back, front = pot(kind="classic", rx=96, rim_y=RIM, base_w=66, band=True)
    B = RIM + 12
    stalks = [
        # back: centre tallest (dark)
        dict(pts=[(300, B), (297, 470), (293, 320), (300, 170), (312, 48)], tone=DARK,
             rachis=(P["sage"], P["deep"]), lmax=68, base_w=20, seed=3, bare=0.40, skip={(0, -1)}),
        # left upright (mid), taller of the two side stalks
        dict(pts=[(290, B), (264, 482), (212, 352), (150, 244), (104, 176)], tone=MIDT,
             rachis=(P["forest"], P["night"]), lmax=64, base_w=18, seed=11, bare=0.37),
        # right upright (mid), a little shorter
        dict(pts=[(310, B), (336, 492), (386, 382), (440, 290), (482, 240)], tone=MIDT,
             rachis=(P["forest"], P["night"]), lmax=60, base_w=18, seed=7, bare=0.38),
        # left arching (dark, front)
        dict(pts=[(284, B), (242, 526), (170, 470), (104, 436), (60, 430)], tone=DARK,
             rachis=(P["sage"], P["deep"]), lmax=58, base_w=17, seed=21, bare=0.42),
        # right arching (dark, front), shorter and a touch higher
        dict(pts=[(318, B), (366, 528), (438, 474), (496, 450), (538, 452)], tone=DARK,
             rachis=(P["sage"], P["deep"]), lmax=54, base_w=17, seed=5, bare=0.44),
    ]
    body = [back]
    for st in stalks:
        body.append(zz_stalk(**st))
    body.append(front)
    return "<defs>" + "".join(_DEFS_SVG) + "</defs>" + "".join(body)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "out", "zamioculcas_zamiifolia.svg")
    with open(out, "w") as fh:
        fh.write(svg_doc(build(), "Zamioculcas zamiifolia (ZZ plant)"))
    print(out, os.path.getsize(out))
