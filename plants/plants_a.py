import math, random
from core import *

P = PAL


def rot_of(dx, dy):
    return math.degrees(math.atan2(dx, -dy))


def along(pts, fracs, per=12):
    """Points + tangent rotation at arc-length fractions along a CR spline."""
    s = cr_sample(pts, per)
    acc = [0.0]
    for a, b in zip(s, s[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = acc[-1]
    out = []
    for fr in fracs:
        target = fr * tot
        i = next((k for k in range(1, len(acc)) if acc[k] >= target), len(acc) - 1)
        a, b = s[i - 1], s[i]
        u = (target - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
        p = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        out.append((p, rot_of(b[0] - a[0], b[1] - a[1])))
    return out


# =================================================================== MONSTERA
def monstera_leaf(L, splits=6, seed=0, young=False):
    rnd = random.Random(seed)
    right = [(0.07, 0), (-0.05, 0.19), (0.0, 0.37), (0.14, 0.51), (0.37, 0.57), (0.62, 0.50),
             (0.83, 0.31), (0.95, 0.11)]
    left = [(0.07, 0), (-0.04, 0.18), (0.01, 0.35), (0.16, 0.49), (0.40, 0.55), (0.64, 0.47),
            (0.84, 0.29), (0.95, 0.10)]
    lf = Leaf(L, right, left, bend=rnd.uniform(-0.06, 0.06), cordate=True, tip_t=1.0)
    if young:
        return lf, lf.path()
    sinus, tip = lf.axis(0.07), lf.axis(1.0)
    R = [sinus] + lf.side_pts("r")[1:] + [tip]
    Lp = [tip] + lf.side_pts("l")[1:][::-1] + [sinus]

    def slit(pts, sg, lo, hi):
        S = cr_sample(pts, 12)
        n = len(S)
        k = splits + rnd.choice([-1, 0, 0])
        centers = []
        for i in range(k):
            u = lo + (hi - lo) * (i + rnd.uniform(0.3, 0.7)) / k
            centers.append(int(u * n))
        out = []  # (pt, sharp)
        i = 0
        g = 1
        while i < n:
            if i in centers and g <= i < n - g:
                ea, eb = S[i - g], S[i + g]
                E = S[i]
                t = -E[1] / L
                depth = rnd.uniform(0.06, 0.12)
                I = lf.pt(max(t - rnd.uniform(0.07, 0.11), 0.05), sg * depth)
                dx, dy = I[0] - E[0], I[1] - E[1]
                m = math.hypot(dx, dy) or 1
                nx, ny = -dy / m, dx / m
                hw = L * 0.0105
                A = (I[0] - dx / m * hw * 1.2 + nx * hw, I[1] - dy / m * hw * 1.2 + ny * hw)
                B = (I[0] - dx / m * hw * 1.2 - nx * hw, I[1] - dy / m * hw * 1.2 - ny * hw)
                if math.hypot(A[0] - ea[0], A[1] - ea[1]) > math.hypot(B[0] - ea[0], B[1] - ea[1]):
                    A, B = B, A
                lerp = lambda p, q, u: (p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u)
                if g > 1:
                    del out[-(g - 1):]
                out.append((ea, False)); out.append((lerp(ea, A, 0.18), True)); out.append((A, False))
                out.append((I, False)); out.append((B, False)); out.append((lerp(eb, B, 0.18), True))
                out.append((eb, False))
                i += g + 1
                continue
            out.append((S[i], False))
            i += 1
        return out

    rs = slit(R, 1, 0.20, 0.86)
    ls = slit(Lp, -1, 0.14, 0.80)
    seq = rs[:-1] + ls[:-1]  # tip shared, sinus shared (closed)
    pts, sharp = [], set()
    for j, (p, sh) in enumerate(seq):
        keep = sh or j % 2 == 0 or (j + 1 < len(seq) and seq[j + 1][1]) or (j > 0 and seq[j - 1][1])
        if p == tip or p == sinus:
            sh, keep = True, True
        if keep:
            if sh:
                sharp.add(len(pts))
            pts.append(p)
    d = cr_path(pts, closed=True, sharp=sharp)
    # a few elliptical holes near the midrib
    for sg in (1, -1):
        for t in [0.24, 0.42, 0.6][: rnd.randint(1, 3)]:
            x, y = lf.pt(t + rnd.uniform(-0.03, 0.03), sg * rnd.uniform(0.09, 0.12))
            rx, ry = L * 0.02, L * 0.048
            a = math.radians(sg * 50)
            # ellipse as two arcs, rotated
            p1 = (x - ry * math.sin(a), y + ry * math.cos(a))
            p2 = (x + ry * math.sin(a), y - ry * math.cos(a))
            d += (f"M{f(p1[0])} {f(p1[1])}A{f(rx)} {f(ry)} {f(sg*50)} 1 0 {f(p2[0])} {f(p2[1])}"
                  f"A{f(rx)} {f(ry)} {f(sg*50)} 1 0 {f(p1[0])} {f(p1[1])}Z")
    return lf, d


def monstera_place(x, y, rot, L, fill, seed, splits=6, sx=1.0, young=False, side="r"):
    lf, d = monstera_leaf(L, splits, seed, young=young)
    return leaf_g(lf, fill, shade=SHADE.get(fill), side=side, d=d, evenodd=True,
                  midrib=(P["pale"], L * 0.016, 0.55, 0.07, 0.93),
                  veins=(P["night"], L * 0.008, 0.2, [0.16, 0.30, 0.44, 0.58, 0.71], 0.9, 0.09),
                  transform=T(x, y, rot, 1, sx))


def monstera():
    back, front = pot("classic")
    g = []
    base = (300, 590)
    leaves = [
        # x, y, rot, L, fill, seed, sx, side, petiole ctrl
        (318, 318, 9, 196, P["deep"], 3, 1, "l", (316, 450)),
        (236, 362, -52, 180, P["forest"], 5, 1, "r", (264, 476)),
        (378, 352, 58, 184, P["deep"], 7, -1, "l", (350, 476)),
        (212, 474, -100, 146, P["mid"], 11, 1, "r", (244, 544)),
        (392, 474, 104, 140, P["forest"], 13, -1, "l", (356, 544)),
        (336, 452, 28, 128, P["mid"], 17, 1, "r", (322, 524)),
    ]
    # petioles first (behind everything)
    for x, y, r, L, col, sd, sx, sd2, c in leaves[:3]:
        g.append(stem([(base[0] + (x - 300) * 0.05, base[1]), c, (x, y + 4)], 11, 7, P["mid"]))
    for x, y, r, L, col, sd, sx, sd2, c in leaves[:3]:
        g.append(monstera_place(x, y, r, L, col, sd, sx=sx, side=sd2))
    # young furled leaf
    g.append(stem([(292, 590), (284, 520), (276, 455)], 8, 5, P["sage"]))
    yl = Leaf(96, [(0, 0), (0.2, 0.12), (0.5, 0.15), (0.8, 0.09)], bend=0.12)
    g.append(leaf_g(yl, P["light"], shade=P["sage"], side="r", transform=T(276, 458, -14),
                    midrib=(P["mid"], 2, 0.5, 0.05, 0.9)))
    for x, y, r, L, col, sd, sx, sd2, c in leaves[3:]:
        g.append(stem([(base[0] + (x - 300) * 0.06, base[1]), c, (x, y + 3)], 10, 6.5, P["sage"]))
        g.append(monstera_place(x, y, r, L, col, sd, splits=5, sx=sx, side=sd2))
    # aerial root
    g.append(line([(262, 588), (250, 560), (256, 520), (246, 500)], 4, P["soil"], 0.75))
    return back + "".join(g) + front


# =================================================================== POTHOS
def pothos_leaf(L, seed, fill=None):
    rnd = random.Random(seed)
    j = lambda v, a=0.03: v + rnd.uniform(-a, a)
    right = [(0.11, 0), (-0.03, j(0.2)), (0.08, j(0.37)), (0.3, j(0.41)), (0.55, j(0.33)),
             (0.78, j(0.17)), (0.93, 0.05)]
    left = [(0.11, 0), (-0.02, j(0.18)), (0.09, j(0.35)), (0.31, j(0.39)), (0.56, j(0.31)),
            (0.79, j(0.15)), (0.93, 0.045)]
    lf = Leaf(L, right, left, bend=rnd.uniform(0.02, 0.12), cordate=True)

    def streaks(l):
        s = []
        for k in range(rnd.randint(2, 4)):
            sg = rnd.choice([1, -1])
            t = rnd.uniform(0.12, 0.7)
            w = l.width(t + 0.1, "r" if sg > 0 else "l")
            pts = [l.pt(t, sg * 0.02), l.pt(t + 0.08, sg * w * 0.5), l.pt(t + 0.14, sg * w * rnd.uniform(0.8, 1.1))]
            col = rnd.choice([P["pale"], P["light"], P["yellow_edge"]])
            s.append(f'<path d="{ribbon(pts, L*0.05, L*0.012)}" fill="{col}" opacity=".85"/>')
        return "".join(s)
    return lf, streaks


def pothos_place(x, y, rot, L, fill, seed, sx=1.0, side="r"):
    lf, ex = pothos_leaf(L, seed)
    return leaf_g(lf, fill, shade=SHADE.get(fill), side=side, extra=ex,
                  midrib=(P["pale"], max(1.6, L * 0.022), 0.6, 0.1, 0.9),
                  transform=T(x, y, rot, 1, sx))


def vine(pts, n, L0, L1, fills, seed, width=5.5, flip_start=1, spacing_jitter=0.35):
    rnd = random.Random(seed)
    out = [stem(pts, width, width * 0.45, P["mid"])]
    fr = []
    acc = 0.05
    for i in range(n):
        fr.append(min(acc, 0.985))
        acc += (0.93 / n) * rnd.uniform(1 - spacing_jitter, 1 + spacing_jitter)
    placed = along(pts, fr)
    side = flip_start
    for i, (p, r) in enumerate(placed):
        u = i / max(n - 1, 1)
        L = L0 + (L1 - L0) * u + rnd.uniform(-6, 6)
        off = side * rnd.uniform(38, 70)
        sx = rnd.choice([1, 1, 0.78, 0.62]) * (1 if side > 0 else -1)
        fill = fills[(i + rnd.randint(0, 1)) % len(fills)]
        # short petiole
        pr = math.radians(r + off)
        px, py = p[0] + math.sin(pr) * L * 0.18, p[1] - math.cos(pr) * L * 0.18
        out.append(line([p, (px, py)], 3, P["mid"]))
        out.append(pothos_place(px, py, r + off, L, fill, seed * 31 + i, sx=sx, side="r" if side > 0 else "l"))
        side = -side if rnd.random() > 0.18 else side
    return "".join(out)


def pothos():
    back, front = pot("classic", rx=100, base_w=72)
    g = []
    # crown mound (behind the rim)
    crown = [
        (262, 560, -38, 84, P["forest"], 1, 1), (338, 556, 36, 88, P["mid"], 2, -1),
        (300, 552, 4, 98, P["forest"], 3, 1), (228, 574, -70, 72, P["mid"], 4, 1),
        (372, 574, 72, 74, P["forest"], 5, -1), (282, 566, -16, 70, P["sage"], 6, 0.7),
        (322, 566, 20, 66, P["mid"], 7, -0.75),
    ]
    for x, y, r, L, c, s, sx in crown:
        g.append(line([(300, 588), ((300 + x) / 2, 580), (x, y)], 4, P["mid"]))
    for x, y, r, L, c, s, sx in crown:
        g.append(pothos_place(x, y, r, L, c, 100 + s, sx=sx, side="r" if sx > 0 else "l"))
    frontg = []
    # long left trailing vine
    frontg.append(vine([(250, 586), (196, 604), (162, 650), (150, 706), (128, 752), (104, 778)],
                       8, 70, 46, [P["forest"], P["mid"], P["sage"]], 11))
    # right shorter vine with curl
    frontg.append(vine([(356, 588), (410, 606), (446, 646), (458, 690), (470, 716), (492, 724)],
                       6, 66, 44, [P["mid"], P["forest"], P["sage"]], 23, flip_start=-1))
    # a short strand spilling over the front of the rim
    frontg.append(vine([(318, 590), (334, 612), (340, 640), (352, 664)], 3, 58, 44,
                       [P["sage"], P["mid"]], 37))
    # a strand heading up/out on the left (sprawling, not symmetric)
    g.append(vine([(270, 580), (228, 548), (194, 540), (160, 548)], 4, 64, 46,
                  [P["forest"], P["mid"]], 41, flip_start=-1))
    return back + "".join(g) + front + "".join(frontg)
