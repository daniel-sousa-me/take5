"""Crassula ovata (jade plant) - v4 botanical card art.

A miniature tree: thick grey-brown gnarled trunk splitting into fleshy branches
(faint leaf-scar rings), each ending in a rosette of plump obovate leaves in
opposite (decussate) pairs. Leaves read as thick pads: darker side band + lighter
face, a tiny gloss sliver, and a thin blush-red rim on some.

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
RIM = P["rose"]
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


def shapes(k):
    """Return path strings (band/full, face, rim crescent, gloss) at L=100."""
    s = VARIANTS[k]
    nodes = [(t, w * s) for t, w in BASE]
    full = Leaf(100, nodes, tip_sharp=False)
    # face: inset on the right (band) side, a hair inside on the left and tip
    fr = [(t, w * 0.66) for t, w in nodes]
    fl = [(t, max(w - 0.028, 0) if t > 0 else 0) for t, w in nodes]
    face_leaf = Leaf(100, fr, fl, tip_sharp=False, tip_t=0.925)
    face_pts, sharp = face_leaf.outline()
    face_pts[0] = (0, -5)
    face = cr_path(face_pts, closed=True, sharp=sharp)
    # rim: crescent hugging the outer margin across the tip (t 0.5 -> tip -> 0.5)
    ts = [0.5, 0.64, 0.78, 0.88, 0.95]
    outer = [full.pt(t, full.width(t, "r")) for t in ts] + [(0, -100)] + \
            [full.pt(t, -full.width(t, "l")) for t in reversed(ts)]
    th = [0.0, 1.4, 2.6, 3.1, 3.3]
    inner = [full.pt(t, full.width(t, "r") - th[i] / 100) for i, t in enumerate(ts)] + [(0, -96.6)] + \
            [full.pt(t, -(full.width(t, "l") - th[i] / 100)) for i, t in reversed(list(enumerate(ts)))]
    ring = outer + inner[::-1]
    rim = cr_path(ring, closed=True, sharp={0, len(outer) - 1, len(outer), len(ring) - 1})
    # gloss: small sliver on the lit (left) half of the face
    g = [face_leaf.pt(0.42, -0.08 * s), face_leaf.pt(0.6, -0.16 * s), face_leaf.pt(0.78, -0.15 * s),
         face_leaf.pt(0.66, -0.12 * s)]
    gloss = cr_path(g, closed=True, sharp={0, 2})
    return full.path(), face, rim, gloss


def leaf_defs():
    out = ["<defs>"]
    for k in VARIANTS:
        full, face, rim, gloss = shapes(k)
        out.append(f'<path id="jb{k}" d="{full}"/><path id="jf{k}" d="{face}"/>'
                   f'<path id="jr{k}" d="{rim}"/><path id="jg{k}" d="{gloss}"/>')
    out.append("</defs>")
    return "".join(out)


def leaf(x, y, rot, L, tone, k="o", blush=None, sy=1.0, mirror=None, gloss=True):
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
    if gloss:
        g.append(f'<use href="#jg{k}" fill="{GLOSS[face]}"/>')
    if blush:
        g.append(f'<use href="#jr{k}" fill="{blush}"/>')
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


def scars(s, ws, every, start=1, col=SCAR, op=0.55, skip_end=2):
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
    return (f'<path d="{"".join(d)}" fill="none" stroke="{col}" stroke-width="1.3" '
            f'stroke-linecap="round" opacity="{op}"/>')


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
                 f'stroke-width="2.2" stroke-linecap="round" opacity=".8"/>')
    g.append(scars(s, ws, every, start))
    return "".join(g)


# ------------------------------------------------------------------ rosettes
def rosette(tip, a, size, tone, blush=(), nodes=5, spread=1.0, lean=0):
    """Leaf rosette at a branch tip, seen from the side. a = branch direction
    (deg, cw from up). Decussate pairs alternate between the picture plane
    (spread L/R pair) and the depth axis (a back leaf seen behind + a front leaf
    foreshortened toward the viewer). Returns (back_svg, mid_svg, front_svg)."""
    tx, ty = tip
    ar = math.radians(a)
    ux, uy = math.sin(ar), -math.cos(ar)

    sc = size / 55.0

    def at(back):
        return (tx - ux * back * sc, ty - uy * back * sc)

    bi = [0]

    def bl():
        i = bi[0]; bi[0] += 1
        return RIM if i in blush else None

    def T_(t):
        return max(0, min(5, t))

    rng = random.Random(int(tx * 7 + ty))

    def lf(x, y, rot, L, tone_, *args, **kw):  # gentle irregularity
        return leaf(x, y, rot + rng.uniform(-9, 9), L * rng.uniform(0.93, 1.06), tone_, *args, **kw)

    B, M, F = [], [], []
    # node 6: old pair, drooping outward
    if nodes >= 6:
        x, y = at(46)
        M.append(lf(x, y, a - 112 * spread + lean, size * 0.94, T_(tone), "w", bl()))
        M.append(lf(x, y, a + 108 * spread + lean, size * 0.92, T_(tone), "w", bl()))
    # node 4: oldest spread pair, lowest, widest angle, largest
    if nodes >= 5:
        x, y = at(30)
        M.append(lf(x, y, a - 92 * spread + lean, size * 1.0, T_(tone - 1), "o", bl()))
        M.append(lf(x, y, a + 88 * spread + lean, size * 0.97, T_(tone - 1), "o", bl()))
    # node 3: depth pair (back leaf up behind, front leaf toward viewer)
    if nodes >= 4:
        x, y = at(21)
        B.append(lf(x, y, a - 10 + lean, size * 0.92, T_(tone - 2), "w", bl(), sy=0.8, mirror=False))
        F.append(lf(x, y, a + 158 + lean, size * 0.8, T_(tone + 1), "w", bl(), sy=0.6))
    # node 2: spread pair
    x, y = at(12)
    M.append(lf(x, y, a - 52 * spread + lean, size * 0.9, T_(tone), "o", bl()))
    M.append(lf(x, y, a + 48 * spread + lean, size * 0.88, T_(tone), "o", bl()))
    # node 1: small depth pair
    x, y = at(5)
    B.append(lf(x, y, a + 12 + lean, size * 0.66, T_(tone - 1), "o", bl(), sy=0.85, mirror=True))
    # node 0: young pair at the tip
    x, y = at(0)
    M.append(lf(x, y, a - 20 + lean, size * 0.46, T_(tone + 1), "n", bl(), gloss=False))
    M.append(lf(x, y, a + 22 + lean, size * 0.42, T_(tone + 1), "n", bl(), gloss=False))
    return "".join(B), "".join(M), "".join(F)


# ------------------------------------------------------------------ build
def build():
    reset_ids()
    back, front = pot("bowl", rx=126, rim_y=600, rim_h=26, base_w=92)
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
        ([(288, 420), (268, 364), (250, 308), (238, 258), (233, 226)], [20, 15, 12.5, 10, 9],
         (), 7, 3),
    ]
    W = [wood(*l) for l in side + top]
    W.append(wood(TRUNK, TRUNK_W, ((1.6, 5), (3.4, 4), (5.0, 3), (7.6, 1.5)), every=8, start=4))

    # (tip, dir, size, tone, blush leaf indices, nodes, spread, lean)
    # leaf index order: n6 L,R | n4 L,R | n3 back,front | n2 L,R | n1 back | n0 L,R
    ros = [
        ((112, 368), -60, 68, 2, {0, 7}, 6, 0.9, 0),       # A1 far left
        ((192, 312), -6, 66, 4, {2, 9}, 6, 0.95, 0),      # A2
        ((232, 222), -16, 66, 2, {6, 10}, 6, 0.95, 0),     # B1
        ((328, 160), 5, 72, 4, {3, 6, 10}, 6, 1.0, 0),     # B2 top
        ((402, 292), 4, 66, 2, {1, 9}, 6, 0.95, 0),       # C2
        ((484, 368), 60, 68, 4, {1, 7, 10}, 6, 0.9, 0),    # C1 far right
        ((424, 512), 72, 54, 3, {5, 8}, 5, 0.85, -6),      # D low right
    ]
    rs = [rosette(*r) for r in ros]
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
