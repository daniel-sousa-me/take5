"""Chamaedorea elegans (parlour palm) -- v4 botanical card art.

A clump of three slender, ringed green canes rising from the soil, each
crowned with a few pinnate fronds: an arching rachis carrying long, narrow,
slightly curved lanceolate leaflets on both sides (longest mid-frond).
The far row of leaflets on every frond sits one tone darker than the near
row; back fronds are deep green, front fronds sage / light.

Leaflets are drawn from three shared <defs> shapes placed with <use>, the
fill (lit half) and `color` (turned-away half) set per instance, which keeps
the file small.

Run:  python3 species/chamaedorea_elegans.py   -> out/chamaedorea_elegans.svg
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, SHADE, f, cr_path, cr_sample, ribbon, pot, svg_doc, reset_ids  # noqa

P = PAL
CX, RIM_Y = 300, 586
DARKER = {P["pale"]: P["light"], P["light"]: P["sage"], P["sage"]: P["mid"],
          P["mid"]: P["forest"], P["forest"]: P["deep"], P["deep"]: P["night"]}
SH = dict(SHADE)
SH[P["night"]] = "#213127"


# ------------------------------------------------------------------ leaflet defs
def leaflet_d(bend, U=100.0):
    """Unit leaflet: base (0,0), tip (U, droop). Upper/lower halves + midrib."""
    ts = [0.0, 0.04, 0.12, 0.26, 0.42, 0.58, 0.73, 0.86, 0.95, 1.0]
    hw = [0.0, 0.024, 0.050, 0.070, 0.076, 0.070, 0.054, 0.034, 0.014, 0.0]

    def ax(t):
        return (U * t, bend * U * t * t)

    def nrm(t):
        tx, ty = U, 2 * bend * U * t
        m = math.hypot(tx, ty)
        return (-ty / m, tx / m)  # points "down" (+y) for an unbent leaflet

    up = [(ax(t)[0] - nrm(t)[0] * w * U, ax(t)[1] - nrm(t)[1] * w * U) for t, w in zip(ts, hw)]
    lo = [(ax(t)[0] + nrm(t)[0] * w * U * 0.92, ax(t)[1] + nrm(t)[1] * w * U * 0.92) for t, w in zip(ts, hw)]
    n = len(ts)
    outline = cr_path(up + lo[-2:0:-1], closed=True, sharp={0, n - 1})
    axis = [ax(t) for t in (1.0, 0.75, 0.5, 0.25, 0.0)]
    lower = cr_path(lo + axis[1:], closed=True, sharp={0, n - 1, len(lo) + len(axis) - 2})
    mid = ribbon([ax(t) for t in (0.0, 0.3, 0.6, 0.9)], 1.5, 0.35, per=4)
    return outline, lower, mid


LEAFLET_KINDS = {"a": 0.05, "b": 0.11, "c": 0.18}


def defs():
    out = ["<defs>"]
    for k, bend in LEAFLET_KINDS.items():
        o, lo, mid = leaflet_d(bend)
        # (leaflet midribs dropped: too fine to survive print)
        out.append(f'<g id="ce{k}"><path d="{o}"/><path d="{lo}" fill="currentColor"/></g>')
        # flat variant for the smallest tip leaflets, whose shaded half alone would be
        # narrower than the print minimum (it reads as a speck): one tone, no split
        out.append(f'<path id="ce{k}f" d="{o}"/>')
    out.append("</defs>")
    return "".join(out)


# ------------------------------------------------------------------ geometry helpers
def resample(pts, per=12):
    s = cr_sample(pts, per)
    acc = [0.0]
    for a, b in zip(s, s[1:]):
        acc.append(acc[-1] + math.dist(a, b))
    return s, acc


def at(s, acc, fr):
    """point + unit tangent at arc fraction fr."""
    tgt = fr * acc[-1]
    i = next((k for k in range(1, len(acc)) if acc[k] >= tgt), len(acc) - 1)
    a, b = s[i - 1], s[i]
    u = (tgt - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
    p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
    d = (b[0] - a[0], b[1] - a[1])
    m = math.hypot(*d) or 1
    return p, (d[0] / m, d[1] / m)


# print check for the shaded lower half of a leaflet: its measured width (4A/P) in
# template units, and the plan scale (mm/unit, a little under this plant's deck scale)
HALF_W, MM_PLAN = 9.68, 0.052


def lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def half_ok(L, wscale, shade):
    need = 0.225 if lum(shade) > 0.55 else 0.175
    return HALF_W * L / 100 * math.sqrt(wscale) * MM_PLAN >= need


def use(kind, x, y, ang, L, wscale, flip):
    sy = -wscale if flip else wscale
    return (f'<use href="#ce{kind}" transform="translate({f(x)} {f(y)}) rotate({f(ang)}) '
            f'scale({L / 100:.3f} {sy * L / 100:.3f})"/>')


# ------------------------------------------------------------------ frond
def frond_parts(pts, tone, n_pairs, lmax, seed, bare=0.2, near="upper", spread=(52, 30),
                droop=(0.42, 0.16), rach_col=None, rach_w=(4.2, 1.1), lead=None):
    """Returns (leaflets_svg, rachis_svg). pts: rachis control points, first =
    the crown. near: which row is the near/lighter one ('upper', 'lower',
    'right', 'left')."""
    rnd = random.Random(seed)
    s, acc = resample(pts)
    _, tm = at(s, acc, 0.5)
    # side +1 = tangent rotated clockwise (screen) -> for a leftward frond that's the upper row
    if near in ("upper", "lower"):
        up_side = 1 if tm[0] < 0 else -1
        near_side = up_side if near == "upper" else -up_side
    else:
        near_side = 1 if (near == "right") == (tm[1] < 0) else -1
    far_tone = DARKER[tone]
    rows = {1: [], -1: []}
    last = 0.0
    for side in (1, -1):
        off = 0.0 if side == 1 else 0.45
        for i in range(n_pairs):
            u = min((i + off) / (n_pairs - 0.4), 1.0)
            fr = bare + (1 - bare) * (u ** 0.95) * 0.975
            p, t = at(s, acc, fr)
            # length profile: shortish at base, longest ~40 %, short at the tip
            prof = 0.55 + 0.45 * math.sin(math.pi * min(1.0, 0.15 + u * 0.92))
            if u > 0.7:
                prof *= 1 - (u - 0.7) * 1.55
            L = lmax * prof * rnd.uniform(0.94, 1.05)
            if L < 24:          # tip leaflets this small print as noise: leave them out
                continue
            last = max(last, fr)
            a = math.radians(spread[0] + (spread[1] - spread[0]) * u + rnd.uniform(-3, 3)) * side
            dx = t[0] * math.cos(a) - t[1] * math.sin(a)
            dy = t[0] * math.sin(a) + t[1] * math.cos(a)
            g = droop[0] if dy > -0.3 else droop[1]
            dy += g
            m = math.hypot(dx, dy)
            dx, dy = dx / m, dy / m
            ang = math.degrees(math.atan2(dy, dx))
            flip = dx < 0  # tip always curves downward
            kind = "a" if dy < -0.55 else ("c" if dy > 0.35 else "b")
            if rnd.random() < 0.25:
                kind = {"a": "b", "b": "c", "c": "b"}[kind]
            x0, y0 = p[0] - dx * 2.0, p[1] - dy * 2.0   # base tucked under the rachis
            ws = rnd.uniform(0.92, 1.08)
            row_tone = tone if side == near_side else far_tone
            if not half_ok(L, ws, SH[row_tone]):
                kind += "f"
            rows[side].append(use(kind, x0, y0, ang, L, ws, flip))
    nr, fr_ = rows[near_side], rows[-near_side]
    rc = rach_col or P["light"]
    if lead:
        # the leaf sheath: the rachis starts a little way down the cane, wrapping it
        # (flat collar, cane width), and bends smoothly out into the frond -- no
        # notch or wedge where the frond leaves the cane
        pts_l, w_l = lead
        # one smooth cubic from the collar (down the cane, along its axis) to a
        # point 14 % out along the rachis (along the rachis) -> a monotone bend
        (l0, l1), fb = pts_l, 0.14
        tc = (l1[0] - l0[0], l1[1] - l0[1])
        m = math.hypot(*tc) or 1
        tc = (tc[0] / m, tc[1] / m)
        q, tq = at(s, acc, fb)
        # control = where the cane axis meets the rachis tangent at q (quadratic
        # bezier -> a single, monotone bend of the petiole out of the cane)
        den = tc[0] * tq[1] - tc[1] * tq[0]
        X = l1
        if abs(den) > 1e-3:
            t_ = ((q[0] - l0[0]) * tq[1] - (q[1] - l0[1]) * tq[0]) / den
            if 0 < t_ < 3 * m:
                X = (l0[0] + tc[0] * t_, l0[1] + tc[1] * t_)
        bz = [tuple((1 - u) ** 2 * l0[j] + 2 * (1 - u) * u * X[j] + u * u * q[j] for j in (0, 1))
              for u in (i / 10 for i in range(11))]
        k = next(i for i in range(len(acc)) if acc[i] > fb * acc[-1])
        raw = bz + s[k:]
        # uniform ~7 px spacing so the spline through it has no overshoot kinks
        cum = [0.0]
        for a_, b_ in zip(raw, raw[1:]):
            cum.append(cum[-1] + math.dist(a_, b_))
        n = max(4, int(cum[-1] / 7))
        sr, j = [], 0
        for i in range(n + 1):
            tgt = cum[-1] * i / n
            while j < len(cum) - 2 and cum[j + 1] < tgt:
                j += 1
            u = (tgt - cum[j]) / ((cum[j + 1] - cum[j]) or 1)
            sr.append((raw[j][0] + (raw[j + 1][0] - raw[j][0]) * u, raw[j][1] + (raw[j + 1][1] - raw[j][1]) * u))
        rach = ribbon(sr, w_l, rach_w[1], per=2)
    else:
        # the rachis ends at the base of the last leaflet, its tip hidden in the
        # leaflet junction (no bare whip tip poking past the last pair)
        cut = min(1.0, last - 0.004)
        k = next((i for i in range(len(acc)) if acc[i] >= cut * acc[-1]), len(s) - 1)
        sc = s[:k + 1]
        rach = ribbon(sc[::3] + ([sc[-1]] if (len(sc) - 1) % 3 else []), rach_w[0], rach_w[1], per=4)
    leaf = (f'<g fill="{far_tone}" color="{SH[far_tone]}">{"".join(fr_)}</g>'
            f'<g fill="{tone}" color="{SH[tone]}">{"".join(nr)}</g>')
    return leaf, f'<path d="{rach}" fill="{rc}"/>'


def frond(*a, **k):
    l, r = frond_parts(*a, **k)
    return l + r


# ------------------------------------------------------------------ cane
def cane(pts, w0, w1, col, ring_col, rings):
    s, acc = resample(pts)
    out = [f'<path d="{ribbon(pts, w0, w1)}" fill="{col}"/>']
    dd = []
    for fr in rings:
        p, t = at(s, acc, fr)
        w = (w0 + (w1 - w0) * fr) / 2 - 0.2
        nx, ny = -t[1], t[0]
        a = (p[0] + nx * w, p[1] + ny * w)
        b = (p[0] - nx * w, p[1] - ny * w)
        c = (p[0] + t[0] * 2.4, p[1] + t[1] * 2.4)
        dd.append(f"M{f(a[0])} {f(a[1])}Q{f(c[0])} {f(c[1])} {f(b[0])} {f(b[1])}")
    # node rings: opaque, one tone darker than the cane, print-safe weight, few
    out.append(f'<path d="{"".join(dd)}" fill="none" stroke="{ring_col}" stroke-width="3" '
               f'stroke-linecap="round"/>')
    return "".join(out)


def lead_from(cane_pts, w_top, back=(28, 0.5)):
    """Two points down the cane below its top, for a frond whose sheath wraps it."""
    s, acc = resample(cane_pts)
    L = acc[-1]
    return ([at(s, acc, (L - b) / L)[0] for b in back], w_top + 1.0)


def trunc(cane_pts, back):
    """Cane control points ending `back` px below the crown (the rest is hidden
    inside the sheath of the frond that wraps it)."""
    s, acc = resample(cane_pts)
    L = acc[-1]
    return list(cane_pts[:-1]) + [at(s, acc, (L - back) / L)[0]]


def sheath(pts, w, col, lift=7.0):
    """Tubular leaf sheath wrapping the cane top: flush with the cane edges at the
    bottom (oblique collar line), slightly swollen, closing to a point above the crown."""
    s, acc = resample(pts, 10)
    n = len(s)
    L, R = [], []
    for i, p in enumerate(s):
        _, t = at(s, acc, min(i / (n - 1), 1.0))
        nx, ny = -t[1], t[0]
        u = i / (n - 1)
        hw = w / 2 * (1.08 if u < 0.7 else 1.08 * max(0.0, 1 - (u - 0.7) / 0.3) ** 0.7)
        L.append((p[0] + nx * hw, p[1] + ny * hw))
        R.append((p[0] - nx * hw, p[1] - ny * hw))
    # oblique collar: one side starts `lift` px further up
    _, t0 = at(s, acc, 0.0)
    L[0] = (L[0][0] + t0[0] * lift, L[0][1] + t0[1] * lift)
    ring = L[::2] + [s[-1]] + R[::-2][1:]
    ring = [pt for pt in ring]
    d = cr_path(ring, closed=True, sharp={0, len(L[::2]), len(ring) - 1})
    return f'<path d="{d}" fill="{col}"/>'


# ------------------------------------------------------------------ build
def arc_frac(pts, q):
    """Arc fraction of the point on the spline through pts nearest to q."""
    s, acc = resample(pts)
    k = min(range(len(s)), key=lambda i: math.dist(s[i], q))
    return acc[k] / acc[-1]


def rings(pts, w0, w1, col, fracs):
    """Node rings across a tapered cane (opaque, print-safe, one tone darker)."""
    s, acc = resample(pts)
    dd = []
    for fr in fracs:
        p, t = at(s, acc, fr)
        w = (w0 + (w1 - w0) * fr) / 2 - 0.2
        nx, ny = -t[1], t[0]
        a = (p[0] + nx * w, p[1] + ny * w)
        b = (p[0] - nx * w, p[1] - ny * w)
        c = (p[0] + t[0] * 2.4, p[1] + t[1] * 2.4)
        dd.append(f"M{f(a[0])} {f(a[1])}Q{f(c[0])} {f(c[1])} {f(b[0])} {f(b[1])}")
    return (f'<path d="{"".join(dd)}" fill="none" stroke="{col}" stroke-width="3" '
            f'stroke-linecap="round"/>')


RING = {P["pale"]: P["sage"], P["light"]: SHADE[P["sage"]], P["sage"]: SHADE[P["sage"]],
        P["mid"]: SHADE[P["mid"]]}


def palm_frond(pts, start, tone, n_pairs, lmax, seed, stem_col, w0, ring_at, **kw):
    """One frond on its own slender cane-like petiole, straight out of the soil:
    a single tapered ribbon (one colour, soil to tip, so no joints), node
    rings on the bare lower part, leaflets from the point nearest `start`."""
    bare = arc_frac(pts, start)
    leaf, rach = frond_parts(pts, tone, n_pairs, lmax, seed, bare=bare, rach_col=stem_col,
                             rach_w=(w0, kw.pop("w1", 1.0)), **kw)
    return leaf + rach + rings(pts, w0, 1.0, RING[stem_col], ring_at)


def build():
    reset_ids()
    back, front = pot("classic", cx=CX, rim_y=RIM_Y, rx=100, base_w=70, band=True)
    G = []
    # A clump of seedling canes, each carrying one frond, fanning out of the
    # soil: outermost canes lean furthest and carry the lowest fronds.
    # ---- back: up-left (deep) and up-right (deep)
    G.append(palm_frond([(285, 602), (280, 520), (268, 432), (248, 354), (218, 288), (176, 240),
                         (134, 214), (92, 218)], (212, 282), P["deep"], 9, 80, 1,
                        P["mid"], 7.0, [0.2, 0.42], near="lower", spread=(46, 30)))
    G.append(palm_frond([(322, 602), (330, 530), (347, 466), (378, 408), (424, 366), (474, 340),
                         (516, 330), (548, 336)], (372, 416), P["deep"], 10, 74, 2,
                        P["sage"], 6.8, [0.16, 0.34], near="lower"))
    # ---- mid-left (forest)
    G.append(palm_frond([(272, 602), (263, 538), (246, 476), (218, 422), (180, 385), (140, 362),
                         (106, 361)], (230, 440), P["forest"], 9, 66, 5,
                        P["sage"], 6.6, [0.14, 0.33], near="upper"))
    # ---- leader: upright (mid)
    G.append(palm_frond([(297, 602), (297, 500), (298, 404), (300, 318), (306, 226), (320, 152),
                         (338, 106), (356, 76)], (300, 318), P["mid"], 12, 76, 3,
                        P["sage"], 8.2, [0.12, 0.27, 0.41], w1=1.1, near="left",
                        spread=(50, 28), droop=(0.5, 0.2)))
    # ---- front: arching up-right (light)
    G.append(palm_frond([(309, 602), (314, 520), (325, 440), (344, 364), (374, 304), (414, 262),
                         (456, 240), (496, 240)], (356, 334), P["light"], 9, 70, 7,
                        P["pale"], 6.4, [0.1, 0.3], near="lower", spread=(42, 28), droop=(0.45, 0.16)))
    # ---- front: arching down-right (mid) and down-left (sage)
    G.append(palm_frond([(336, 602), (346, 542), (364, 496), (398, 464), (450, 466), (500, 494),
                         (542, 536)], (386, 472), P["mid"], 9, 74, 4,
                        P["light"], 6.8, [0.12, 0.3], near="upper", spread=(52, 38), droop=(0.4, 0.16)))
    G.append(palm_frond([(260, 602), (248, 548), (230, 506), (198, 484), (150, 490), (104, 514),
                         (66, 552)], (214, 490), P["sage"], 9, 70, 16,
                        P["light"], 6.6, [0.18], near="upper", spread=(52, 36), droop=(0.45, 0.18)))
    return defs() + back + "".join(G) + front


def main():
    svg = svg_doc(build(), "Chamaedorea elegans (parlour palm)")
    out = os.path.join(os.path.dirname(HERE), "out", "chamaedorea_elegans.svg")
    with open(out, "w") as fh:
        fh.write(svg)
    print(out, len(svg))


if __name__ == "__main__":
    main()
