"""Crassula ovata (jade plant) - v4 botanical card art.

A miniature tree: thick grey-brown gnarled trunk splitting into fleshy branches
(faint leaf-scar rings), each ending in a rosette of plump obovate leaves in
opposite (decussate) pairs. Leaves read as thick pads: darker side band + lighter
face, a tiny gloss sliver, and a thin blush-red rim round the sun-exposed tip.

Run:  python3 species/crassula_ovata.py   -> out/crassula_ovata.svg
"""
import math
import random
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, SHADE, Leaf, cr_path, cr_sample, pot, svg_doc, T, f, reset_ids  # noqa: E402

P = PAL
WOOD = "#857766"      # grey-brown bark (greyer than the ficus bark)
WOOD_DK = "#6A5E51"
WOOD_HI = "#A39584"
SCAR = "#534940"
SCAR_S = "#5E5347"   # scar rings, pre-blended onto the bark (opaque)
RIM = "#B96665"      # red x rose: a thin blush-red margin (opaque)
RIM2 = P["red"]

# face tone ladder, dark -> light, and the side-band tone for each
LAD = [P["deep"], P["forest"], P["mid"], P["sage"], P["light"], P["pale"]]
BAND = dict(SHADE)
BAND[P["pale"]] = P["light"]
GLOSS = {P["deep"]: P["forest"], P["forest"]: P["mid"], P["mid"]: P["sage"],
         P["sage"]: P["light"], P["light"]: P["pale"], P["pale"]: P["ivory"]}


# ------------------------------------------------------------------ leaf shapes (defs)
BASE = [(0.0, 0.0), (0.1, 0.07), (0.3, 0.15), (0.55, 0.235), (0.75, 0.27),
        (0.88, 0.235), (0.96, 0.14)]
VARIANTS = {"o": 1.0, "w": 1.18, "n": 0.84}


RIM_W = 3.2                 # visible red margin, world units (print-safe dark line)
BUCKETS = [0.2, 0.25, 0.31, 0.39, 0.49, 0.62]   # leaf scales (L/100) we pre-build rims for


def shapes(k):
    """Return path strings (band/full, face, gloss) at L=100 plus a rim band per
    scale bucket: an even band all round the distal margin, equal on both sides."""
    s = VARIANTS[k]
    nodes = [(t, w * s) for t, w in BASE]
    full = Leaf(100, nodes, tip_sharp=False)
    # face: inset on the right (band) side, a hair inside on the left and tip
    # (the face stops short of the leaf tip; drop nodes beyond its tip so the
    # outline never doubles back into a notch)
    fr = [(t, w * 0.66) for t, w in nodes if t < 0.92]
    fl = [(t, max(w - 0.028, 0) if t > 0 else 0) for t, w in nodes if t < 0.92]
    face_leaf = Leaf(100, fr, fl, tip_sharp=False, tip_t=0.955)
    face_pts, sharp = face_leaf.outline()
    face_pts[0] = (0, -5)
    face = cr_path(face_pts, closed=True, sharp=sharp)
    rims = []
    # rim only round the rounded distal end (the sun-exposed tip), fading in by t~0.7
    ts = [0.6, 0.66, 0.72, 0.78, 0.84, 0.9, 0.95]
    for sc in BUCKETS:
        th = RIM_W / sc          # local units
        ramp = [0.0, 0.5, 0.9, 1, 1, 1, 1]
        outer = [full.pt(t, full.width(t, "r")) for t in ts] + [(0, -100)] + \
                [full.pt(t, -full.width(t, "l")) for t in reversed(ts)]
        inner = [full.pt(t, full.width(t, "r") - th * ramp[i] / 100) for i, t in enumerate(ts)] + \
                [(0, -100 + th)] + \
                [full.pt(t, -(full.width(t, "l") - th * ramp[i] / 100)) for i, t in reversed(list(enumerate(ts)))]
        ring = outer + inner[::-1]
        rims.append(cr_path(ring, closed=True, sharp={0, len(outer) - 1, len(outer), len(ring) - 1}))
    # gloss: small sliver on the lit (left) half of the face
    g = [face_leaf.pt(0.40, -0.07 * s), face_leaf.pt(0.58, -0.19 * s), face_leaf.pt(0.8, -0.16 * s),
         face_leaf.pt(0.64, -0.07 * s)]
    gloss = cr_path(g, closed=True, sharp={0, 2})
    return full.path(), face, rims, gloss


def leaf_defs():
    out = ["<defs>"]
    for k in VARIANTS:
        full, face, rims, gloss = shapes(k)
        out.append(f'<path id="jb{k}" d="{full}"/><path id="jf{k}" d="{face}"/><path id="jg{k}" d="{gloss}"/>')
        for i, r in enumerate(rims):
            out.append(f'<path id="jr{k}{i}" d="{r}"/>')
    out.append("</defs>")
    return "".join(out)


def leaf(x, y, rot, L, tone, k="o", sy=1.0, mirror=None, gloss=True):
    """rot: degrees clockwise from straight up. Band sits on the down-facing side."""
    face = LAD[tone]
    band = BAND[face]
    if mirror is None:
        mirror = ((rot % 360) > 180)
    s = L / 100
    sx = -s if mirror else s
    tr = f"translate({f(x)} {f(y)}) rotate({f(rot)}) scale({sx:.3g} {s * sy:.3g})"
    g = [f'<g transform="{tr}">',
         f'<use href="#jb{k}" fill="{band}"/>',
         f'<use href="#jf{k}" fill="{face}"/>']
    if gloss and s >= 0.45:     # gloss lens only where it prints as a clear mark
        g.append(f'<use href="#jg{k}" fill="{GLOSS[face]}"/>')
    # largest pre-built bucket not bigger than this leaf's (foreshortened) scale,
    # so the printed rim is never thinner than RIM_W
    se = s * min(1.0, sy)
    bk = max([i for i, b in enumerate(BUCKETS) if b <= se] or [0])
    rim_ok = se >= BUCKETS[0]
    if rim_ok:
        g.append(f'<use href="#jr{k}{bk}" fill="{RIM}"/>')
    g.append("</g>")
    return "".join(g)


# ------------------------------------------------------------------ wood
def limb(pts, widths, bumps=(), seed=0.0):
    """Tapered limb with node swellings. widths: one per control point.
    Returns (outline path, shade path, centre samples, per-sample width)."""
    per = 8
    s = cr_sample(pts, per)
    n = len(s)
    ws = []
    for i in range(n):
        u = i / per
        j = min(int(u), len(widths) - 2)
        fr = u - j
        w = widths[j] + (widths[j + 1] - widths[j]) * fr
        for (bu, bh) in bumps:          # gentle swelling at old nodes
            w += bh * math.exp(-((u - bu) * 2.6) ** 2)
        ws.append(w)
    L, R, Sh = [], [], []
    for i, p in enumerate(s):
        a, b = s[max(i - 1, 0)], s[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy / m, dx / m
        h = ws[i] / 2
        L.append((p[0] - nx * h, p[1] - ny * h))
        R.append((p[0] + nx * h, p[1] + ny * h))
        Sh.append((p[0] + nx * h * 0.22, p[1] + ny * h * 0.22))
    # rounded end cap
    a, b = s[-2], s[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    m = math.hypot(dx, dy) or 1
    cap = (b[0] + dx / m * ws[-1] * 0.45, b[1] + dy / m * ws[-1] * 0.45)
    st = 2
    Ls, Rs, Ss = L[::st], R[::st], Sh[::st]
    if (n - 1) % st:
        Ls.append(L[-1]); Rs.append(R[-1]); Ss.append(Sh[-1])
    ring = Ls + [cap] + Rs[::-1]
    outline = cr_path(ring, closed=True, sharp={0, len(ring) - 1})
    # shade: right-hand portion (from just right of centre to the right edge)
    sring = Ss + [cap] + Rs[::-1]
    shade = cr_path(sring, closed=True, sharp={0, len(sring) - 1})
    return outline, shade, s, ws


def scars(s, ws, every, start=1, col=SCAR_S, skip_end=2):
    """Faint leaf-scar rings: shallow arcs across the limb."""
    d = []
    n = len(s)
    for i in range(start, n - skip_end, every):
        p = s[i]
        a, b = s[max(i - 1, 0)], s[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        tx, ty = dx / m, dy / m
        nx, ny = -ty, tx
        h = ws[i] / 2 * 0.82
        p0 = (p[0] - nx * h, p[1] - ny * h)
        p1 = (p[0] + nx * h, p[1] + ny * h)
        c = (p[0] - tx * ws[i] * 0.22, p[1] - ty * ws[i] * 0.22)  # bows back toward base
        d.append(f"M{f(p0[0])} {f(p0[1])}Q{f(c[0])} {f(c[1])} {f(p1[0])} {f(p1[1])}")
    return (f'<path d="{"".join(d)}" fill="none" stroke="{col}" stroke-width="3" '
            f'stroke-linecap="round"/>')


def wood(pts, widths, bumps=(), every=7, start=3, hi=True):
    o, sh, s, ws = limb(pts, widths, bumps)
    g = [f'<path d="{o}" fill="{WOOD}"/>', f'<path d="{sh}" fill="{WOOD_DK}"/>']
    if hi:  # thin highlight along the lit edge
        hp = []
        n = len(s)
        for i in range(2, n - 3, 2):
            p = s[i]
            a, b = s[i - 1], s[i + 1]
            dx, dy = b[0] - a[0], b[1] - a[1]
            m = math.hypot(dx, dy) or 1
            nx, ny = -dy / m, dx / m
            h = ws[i] / 2 * 0.62
            hp.append((p[0] - nx * h, p[1] - ny * h))
        g.append(f'<path d="{cr_path(hp, closed=False)}" fill="none" stroke="{WOOD_HI}" '
                 f'stroke-width="4" stroke-linecap="round"/>')
    g.append(scars(s, ws, int(every * 1.6), start))
    return "".join(g)


# ------------------------------------------------------------------ rosettes
def back_along(samples, dist):
    """Point and direction (deg cw from up, pointing toward the tip) at arc length
    `dist` back from the end of a sampled branch."""
    d = 0.0
    for i in range(len(samples) - 1, 0, -1):
        b, a = samples[i], samples[i - 1]
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        if d + seg >= dist or i == 1:
            u = min(1.0, (dist - d) / (seg or 1))
            p = (b[0] + (a[0] - b[0]) * u, b[1] + (a[1] - b[1]) * u)
            return p, math.degrees(math.atan2(b[0] - a[0], -(b[1] - a[1])))
        d += seg


def rosette(samples, size, tone, pairs=3, seed=0, gap=1.0, spread=0, tilt=0, first="spread"):
    """Decussate leaf pairs spaced along the last stretch of a branch (samples =
    the branch centre line, base -> tip). A small closed bud pair sits at the tip;
    below it, opposite pairs at lengthening internodes (bare stem shows between
    them), alternating between a spread pair in the picture plane (both leaves
    ascending left/right) and a depth pair (one leaf tipped toward us and
    foreshortened, its partner leaning back behind the stem).
    Returns (back_svg, mid_svg, front_svg)."""
    rng = random.Random(seed)
    B, M, F = [], [], []

    def lf(x, y, rot, L, tone_, *args, jit=6, **kw):
        r = (rot + 180) % 360 - 180
        rot = max(-112, min(112, r))                # leaves ascend or spread, never hang
        return leaf(x, y, rot + rng.uniform(-jit, jit), L * rng.uniform(0.94, 1.05), tone_, *args, **kw)

    T_ = lambda t: max(0, min(5, t))
    pos, d = [0.0], size * 0.13
    for i in range(1, pairs + 1):
        pos.append(d)
        d += size * (0.36 + 0.1 * i) * gap * rng.uniform(0.92, 1.1)
    kinds = ["spread", "depth"] if first == "spread" else ["depth", "spread"]
    items = []
    for i in reversed(range(pairs + 1)):
        (x, y), a = back_along(samples, pos[i])
        a += tilt
        age = i / pairs
        L = size * (0.52 + 0.36 * age)
        tn = T_(tone - (1 if age > 0.9 else 0))
        if i == 0:                                  # closed bud pair at the tip
            # one plump pair, big enough to print as leaves (not red-tipped specks)
            M.append(lf(x, y, a - 9, size * 0.44, T_(tone + 1), "o", gloss=False, jit=2))
            M.append(lf(x, y, a + 8, size * 0.40, T_(tone + 1), "o", gloss=False, jit=2))
        elif kinds[(i - 1) % 2] == "spread":        # pair in the picture plane
            op = 44 + 22 * age + spread
            sk = rng.uniform(-6, 6)
            M.append(lf(x, y, a - op + sk, L, tn, "o", sy=1.0 if i % 2 else 0.86))
            M.append(lf(x, y, a + op + sk, L * rng.uniform(0.88, 0.98), tn, "o", sy=0.86 if i % 2 else 1.0))
        else:                                       # depth pair
            side = 1 if rng.random() < 0.5 else -1
            B.append(lf(x, y, a + side * rng.uniform(16, 24), L * 0.9, T_(tn - 1), "o", sy=0.84))
            ft = tn + 1 if tn < 4 else tn - 1
            F.append(lf(x, y, a - side * rng.uniform(34, 44), L * 0.9, ft, "w", sy=0.66))
    return "".join(B), "".join(M), "".join(F)


# ------------------------------------------------------------------ build
def build():
    reset_ids()
    back, front = pot("bowl", rx=100, rim_y=600, rim_h=26, base_w=73)
    out = [back, leaf_defs()]

    # ---- wood: (points, widths, bumps, scar every, scar start)
    TRUNK = [(302, 648), (300, 612), (292, 572), (298, 536), (294, 500), (287, 454),
             (286, 414), (298, 360), (312, 300), (322, 240), (328, 166)]
    TRUNK_W = [68, 58, 50, 46, 40, 32, 26, 19, 15, 12, 10]
    side = [
        ([(216, 460), (206, 412), (198, 358), (192, 316)], [14, 12, 10, 8.5], (), 7, 2),
        # A: left main, forks into A1 (far left) and A2 (up)
        ([(294, 522), (258, 488), (218, 458), (178, 430), (140, 396), (112, 370)],
         [30, 24, 19, 15, 12, 10], ((1.8, 2.5),), 7, 3),
        ([(382, 442), (392, 398), (398, 346), (402, 296)], [14, 12, 10, 8.5], (), 7, 2),
        # C: right main, forks into C1 (far right) and C2 (up)
        ([(298, 512), (338, 476), (376, 444), (414, 414), (452, 390), (484, 370)],
         [30, 24, 19, 15, 12, 10], ((2.2, 2.5),), 7, 3),
        # D: low right, short
        ([(302, 558), (344, 543), (388, 527), (422, 514)], [22, 17, 13, 10.5], (), 7, 2),
    ]
    top = [
        # B1: side fork off the leader (the trunk continues as the top branch)
        # (scars start at sample 14: the ring at 3 sat in the fork, hidden by the trunk
        # except for its round end, which peeked out as a dark half-disc)
        ([(288, 420), (268, 364), (250, 308), (238, 258), (233, 226)], [20, 15, 12.5, 10, 9],
         (), 7, 14),
    ]
    W = [wood(*l) for l in side + top]
    W.append(wood(TRUNK, TRUNK_W, ((1.6, 5), (3.4, 4), (5.0, 3), (7.6, 1.5)), every=8, start=4))
    br = {"A2": side[0][0], "A1": side[1][0], "C2": side[2][0], "C1": side[3][0], "D": side[4][0],
          "B1": top[0][0], "B2": TRUNK}
    smp = {k: cr_sample(v, 8) for k, v in br.items()}

    # (branch, size, tone, pairs, seed, gap, spread, tilt, first) -- each cluster differs
    ros = [
        ("A1", 82, 2, 3, 11, 1.0, 0, 0, "spread"),     # far left
        ("A2", 72, 3, 3, 23, 0.9, -4, 0, "depth"),
        ("B1", 80, 2, 3, 37, 1.0, 2, 0, "spread"),
        ("B2", 86, 4, 4, 41, 0.95, 0, 0, "depth"),    # top
        ("C2", 74, 2, 3, 53, 1.0, 0, 0, "spread"),
        ("C1", 82, 4, 3, 67, 1.15, -2, 0, "depth"),     # far right
        ("D", 66, 3, 2, 79, 1.3, 0, 0, "spread"),      # low right
    ]
    rs = [rosette(smp[r[0]], *r[1:]) for r in ros]
    out += [r[0] for r in rs]      # away-pointing leaves behind all wood
    out += W
    order = [2, 4, 0, 3, 1, 5, 6]  # darker/far clusters first
    for i in order:
        out.append(rs[i][1])
        out.append(rs[i][2])
    out.append(front)
    return "".join(out)


if __name__ == "__main__":
    dst = os.path.join(os.path.dirname(HERE), "out", "crassula_ovata.svg")
    with open(dst, "w") as fh:
        fh.write(svg_doc(build(), "Crassula ovata (jade plant)"))
    print(dst, os.path.getsize(dst))
