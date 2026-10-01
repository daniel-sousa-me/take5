"""Aloe vera — v4 generator.  python3 species/aloe_vera.py  -> out/aloe_vera.svg"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, SHADE, ribbon, cr_path, cr_sample, f, uid, reset_ids, pot, svg_doc  # noqa: E402

P = PAL
CX = 300
RIM_Y = 598
BASE_Y = 628  # leaf bases: below the rim's front arc, hidden by the rim band


def resample(pts, n, per=14):
    """Points + unit tangents at n+1 equal arc-length stations along a CR spline."""
    s = cr_sample(pts, per)
    acc = [0.0]
    for a, b in zip(s, s[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = acc[-1]
    out = []
    j = 1
    for i in range(n + 1):
        tgt = tot * i / n
        while j < len(acc) - 1 and acc[j] < tgt:
            j += 1
        a, b = s[j - 1], s[j]
        u = (tgt - acc[j - 1]) / ((acc[j] - acc[j - 1]) or 1)
        p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        out.append((p, (dx / m, dy / m)))
    return out, tot


# width profile (fraction of wmax) along the leaf: broad fleshy base, long taper
PROF = [(0.0, 0.86), (0.10, 1.0), (0.28, 0.93), (0.50, 0.72), (0.70, 0.47), (0.86, 0.24), (1.0, 0.0)]


def prof(t):
    for (t0, w0), (t1, w1) in zip(PROF, PROF[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / (t1 - t0)
            u = u * u * (3 - 2 * u) * 0.35 + u * 0.65  # soften the knots
            return w0 + (w1 - w0) * u
    return 0.0


def mix(a, b, t):
    """Opaque pre-blend of hex colour b over a at strength t (print policy: no translucent detail)."""
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02X}" for i in (1, 3, 5))


def lum(c):
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def fat(poly):
    """4 * area / perimeter (= incircle diameter of a triangle): print_prep's sliver measure."""
    A = abs(sum(poly[i][0] * poly[i - 1][1] - poly[i - 1][0] * poly[i][1] for i in range(len(poly)))) / 2
    return 4 * A / sum(math.dist(poly[i], poly[i - 1]) for i in range(len(poly)))


def tooth_pts(E, tg, nn, sg, s):
    """Hooked marginal tooth on edge point E (tangent tg, normal nn, side sg), size s."""
    a = (E[0] - tg[0] * s * 0.9 - nn[0] * sg * 1.2, E[1] - tg[1] * s * 0.9 - nn[1] * sg * 1.2)
    b = (E[0] + tg[0] * s * 0.9 - nn[0] * sg * 1.2, E[1] + tg[1] * s * 0.9 - nn[1] * sg * 1.2)
    c = (E[0] + nn[0] * sg * s * 0.9 + tg[0] * s * 0.9, E[1] + nn[1] * sg * s * 0.9 + tg[1] * s * 0.9)
    return a, c, b


def tooth_min(col, stroke=0.8):
    """Smallest tooth size s whose printed width passes (light >= 4.5 units, dark >= 3.5; policy dots)."""
    need = (4.5 if lum(col) > 0.55 else 3.5) * 1.03 - stroke
    s = 1.0
    while fat(tooth_pts((0, 0), (0, -1), (1, 0), 1, s)) < need:
        s += 0.05
    return s


def aloe_leaf(spine, wmax, face, side=1, k=0.35, teeth=True, speck=0, seed=0, n=14, band=None):
    """spine: control points base->tip. side: which margin (+1 = right of travel
    direction) shows the darker thick underside band. k: where the upper face
    ends on that side, as a fraction of the half width."""
    band = band or SHADE[face]
    rnd = random.Random(seed)
    st, length = resample(spine, n)

    def at(t):
        i = min(int(t * n), n - 1)
        u = t * n - i
        (p0, u0), (p1, u1) = st[i], st[i + 1]
        p = (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)
        tx, ty = u0[0] + (u1[0] - u0[0]) * u, u0[1] + (u1[1] - u0[1]) * u
        m = math.hypot(tx, ty) or 1
        return p, (tx / m, ty / m), (-ty / m, tx / m)  # point, tangent, right normal

    def edge(t, r):  # r in half-widths, +1 = right margin
        p, _, nn = at(t)
        w = wmax * prof(t) * r
        return (p[0] + nn[0] * w, p[1] + nn[1] * w)

    ts = [i / n for i in range(n)]  # tip handled separately
    tip = st[-1][0]
    Rm = [edge(t, 1) for t in ts]
    Lm = [edge(t, -1) for t in ts]
    body_pts = Rm + [tip] + Lm[::-1]
    body = cr_path(body_pts, closed=True, sharp={0, len(Rm), len(body_pts) - 1})
    # upper face: from the far margin to an inner line near the band margin
    far = [edge(t, -side) for t in ts]
    inner = [edge(t, side * k * (1 - 0.25 * t)) for t in ts]
    face_pts = far + [tip] + inner[::-1]
    face_d = cr_path(face_pts, closed=True, sharp={0, len(far), len(face_pts) - 1})

    out = []
    cid = uid("al")
    out.append(f'<path d="{body}" fill="{band}"/>')
    out.append(f'<clipPath id="{cid}"><path d="{face_d}"/></clipPath>')
    out.append(f'<path d="{face_d}" fill="{face}"/>')
    inner_g = []
    # shallow channel: a soft darker line down the face, offset toward the band
    ch = [edge(t, side * (k - 0.55) * (1 - 0.3 * t)) for t in [0.02 + i * 0.14 for i in range(7)]]
    inner_g.append(f'<path d="{ribbon(ch, wmax * 0.13, 1.4)}" fill="{mix(face, band, 0.45)}"/>')
    if speck:
        dots = []
        t = 0.12 + rnd.uniform(0, 0.05)
        while t < 0.78:
            for _ in range(rnd.choice([1, 1, 2])):
                if rnd.random() > speck:
                    continue
                r = side * rnd.uniform(-0.78, k - 0.15)
                tt = t + rnd.uniform(-0.02, 0.02)
                p, tg, nn = at(tt)
                w = wmax * prof(tt)
                x, y = p[0] + nn[0] * w * r, p[1] + nn[1] * w * r
                a = math.degrees(math.atan2(nn[1], nn[0]))
                # fewer, bolder flecks: every one >= 4.8 units across its short axis (light-dot minimum)
                rx = max(3.8, w * rnd.uniform(0.15, 0.21))
                dots.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx)}" ry="2.4" '
                            f'transform="rotate({f(a)} {f(x)} {f(y)})"/>')
            t += rnd.uniform(0.085, 0.12)
        inner_g.append(f'<g fill="{mix(face, P["spot"], 0.6)}">' + "".join(dots) + "</g>")
    out.append(f'<g clip-path="url(#{cid})">' + "".join(inner_g) + "</g>")
    if teeth:
        tf, tb = [], []
        # fewer, larger teeth: the smallest (near the tip) is still print-safe for its colour
        gap = 24.0 / length
        for sg in (1, -1):
            s_min = tooth_min(band if sg == side else face)
            t = 0.2 + rnd.uniform(0, gap) + (gap * 0.5 if sg < 0 else 0)
            while t < 0.84:
                p, tg, nn = at(t)
                w = wmax * prof(t)
                s = s_min * (1 + 0.3 * prof(t))  # tooth size shrinks toward the tip
                E = (p[0] + nn[0] * sg * w, p[1] + nn[1] * sg * w)
                a, c, b = tooth_pts(E, tg, nn, sg, s)
                d = f"M{f(a[0])} {f(a[1])}L{f(c[0])} {f(c[1])}L{f(b[0])} {f(b[1])}Z"
                (tb if sg == side else tf).append(d)
                t += gap * rnd.uniform(0.9, 1.1)
        if tb:
            out.append(f'<path d="{"".join(tb)}" fill="{band}" stroke="{band}" stroke-width=".8" stroke-linejoin="round"/>')
        if tf:
            out.append(f'<path d="{"".join(tf)}" fill="{face}" stroke="{face}" stroke-width=".8" stroke-linejoin="round"/>')
    return "<g>" + "".join(out) + "</g>"


def build():
    reset_ids()
    back, front = pot(kind="bowl", cx=CX, rim_y=RIM_Y, bottom=752, rx=100, rim_h=30, base_w=68)
    by = BASE_Y
    L = []
    # --- back tier: upright, darkest
    # gently bowed (convex to the right, tip turning back in) so its margin is not a ruled line
    L.append(aloe_leaf([(318, by), (336, 480), (357, 352), (364, 262), (354, 194)], 30, P["deep"], side=1, k=0.5, seed=9))
    L.append(aloe_leaf([(312, by), (354, 506), (418, 410), (474, 360), (518, 356), (544, 380), (552, 414)], 28, P["forest"], side=1, k=0.4, seed=10))
    L.append(aloe_leaf([(296, by), (303, 486), (302, 362), (290, 254), (266, 166)], 34, P["forest"], side=-1, k=0.5, seed=1))
    L.append(aloe_leaf([(284, by), (256, 492), (214, 388), (172, 318), (136, 286), (110, 290)], 32, P["mid"], side=-1, k=0.4, speck=0.55, seed=2))
    L.append(aloe_leaf([(314, by), (342, 488), (386, 364), (424, 270), (438, 216)], 32, P["mid"], side=-1, k=0.4, speck=0.55, seed=3))
    # --- middle tier: arching outward, sage
    L.append(aloe_leaf([(292, by), (244, 540), (172, 450), (104, 414), (66, 422), (48, 444)], 32, P["sage"], side=-1, k=0.3, speck=0.6, seed=4))
    L.append(aloe_leaf([(308, by), (356, 540), (420, 480), (476, 462), (506, 490)], 28, P["sage"], side=1, k=0.3, speck=0.6, seed=5))
    # --- front tier: low splaying leaves over the rim, lightest
    L.append(aloe_leaf([(300, by), (258, 580), (202, 566), (150, 578), (122, 612)], 26, P["light"], side=-1, k=0.3, seed=6))
    L.append(aloe_leaf([(304, by), (362, 576), (440, 558), (500, 578), (534, 634)], 29, P["pale"], side=1, k=0.3, seed=7, band=P["sage"]))
    # --- focal centre leaf, pale, leaning a little right
    L.append(aloe_leaf([(304, by), (322, 522), (343, 432), (354, 362), (352, 318), (346, 292)], 33, P["pale"], side=1, k=0.45, seed=8))
    body = back + "".join(L) + front
    return body


if __name__ == "__main__":
    doc = svg_doc(build(), "Aloe vera")
    out = os.path.join(os.path.dirname(HERE), "out", "aloe_vera.svg")
    with open(out, "w") as fh:
        fh.write(doc)
    print(out, len(doc))
