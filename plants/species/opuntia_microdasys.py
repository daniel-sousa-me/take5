"""Opuntia microdasys (bunny-ear cactus) - v4 botanical card art.

Run:  python3 species/opuntia_microdasys.py   -> out/opuntia_microdasys.svg

Pads are drawn in local coords: joint (attachment) at (0,0), pad grows up -y.
Each pad = thickness band (world-offset copy, darker) + face + flat shaded
half + clipped glochid tufts. Children are attached to a point on the parent's
outline and drawn in front of it, one tone lighter (young pads are paler).
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, SHADE, cr_path, pot, svg_doc, T, f, uid, reset_ids  # noqa: E402

P = PAL
SC, DX = 1.08, 10  # plant scale about (300, 640) and x-shift before scaling
FL_MUST = "#DCB93A"  # flower mid tone: lemon-butter yellow (a step yellower than PAL mustard)
MUST_SH = "#C09E2C"  # its shaded side (flower turned-away side)
BUTTER = "#EFD463"   # mustard lifted toward cream: inner face of the petals
BUTTER2 = "#E3C348"  # a half step deeper, for alternating petals
THROAT = "#AA8B28"   # the inside of the cup: a mid ochre, one step under the back petals
BACK1 = "#CFAC34"    # back petals' inner face (alternates with mustard so the pair reads)
BACK2 = "#C2A02E"    # outermost back petals, turned furthest from the light
LIT = "#F4E186"      # the front petal square to the light
STAMEN = "#D5D08E"   # pale yellow-green anthers: low contrast on the ochre throat
STIGMA = "#C9CB84"   # stigma, a hair greener
BAND = {  # thickness band tone for each face tone (a clear step darker)
    P["pale"]: "#8E9E80", P["light"]: P["sage"], P["sage"]: "#5F7355",
    P["mid"]: P["forest"], P["forest"]: "#2E4633", "#4B6349": "#34503A",
}
BACKPAD = "#4B6349"  # edge-on centre-back pad: half a step lighter than forest (mid's own shade tone)
PAD_SHADE = dict(SHADE, **{BACKPAD: P["forest"]})
PROF = [(0.0, 0.16), (0.07, 0.5), (0.22, 0.82), (0.45, 0.99), (0.64, 1.0),
        (0.8, 0.9), (0.91, 0.66), (0.975, 0.34)]


def rot(x, y, deg):
    a = math.radians(deg)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


class Pad:
    def __init__(self, x, y, deg, L, W, fill, asym=0.0, sx=1.0, seed=0):
        self.x, self.y, self.deg, self.L, self.W = x, y, deg, L, W
        self.fill, self.asym, self.sx, self.seed = fill, asym, sx, seed

    def hw(self, t, side=1):
        k = 1 + self.asym * side
        for (t0, w0), (t1, w1) in zip(PROF, PROF[1:] + [(1.0, 0.0)]):
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0)
                # round-off the very top with a circular falloff
                w = w0 + (w1 - w0) * u
                if t1 == 1.0:
                    w = w0 * math.sqrt(max(0.0, 1 - u * u))
                return w * self.W / 2 * k
        return 0.0

    def outline_pts(self):
        L = self.L
        pts = [(0, L * 0.012)]
        for t, w in PROF:
            pts.append((w * self.W / 2 * (1 + self.asym), -L * t))
        pts.append((0, -L))
        for t, w in PROF[::-1]:
            pts.append((-w * self.W / 2 * (1 - self.asym), -L * t))
        return pts

    def path(self):
        return cr_path(self.outline_pts(), closed=True)

    def local_to_world(self, px, py):
        q = rot(px * self.sx, py, self.deg)
        return (self.x + q[0], self.y + q[1])

    def edge(self, t, side):
        """World point on the outline at height t (side +1 right / -1 left),
        pulled inward by `inset` so a child's joint overlaps the rim."""
        return self.local_to_world(side * self.hw(t, side), -self.L * t)

    def top(self, a, inset=10):
        """Point on the upper rim at polar-ish angle a (deg, 0 = tip, +right),
        moved `inset` px toward the pad centre."""
        cx, cy = 0, -self.L * 0.55
        ang = math.radians(a)
        # march outward from centre until we leave the outline
        dx, dy = math.sin(ang), -math.cos(ang)
        r = 0
        while True:
            px, py = cx + dx * r, cy + dy * r
            t = -py / self.L
            if t >= 1 or t <= 0:
                break
            side = 1 if px >= 0 else -1
            if abs(px) > self.hw(t, side):
                break
            r += 0.5
        r -= inset
        return self.local_to_world(cx + dx * r, cy + dy * r)

    def svg(self, tufts=True, blocked=None):
        d = self.path()
        cid = uid("pd")
        sh = PAD_SHADE.get(self.fill, "#27392C")
        band = BAND.get(self.fill, "#27392C")
        tr = T(self.x, self.y, self.deg, 1, self.sx)
        # thickness band: same outline, offset toward lower-right in world space
        thick = max(4.0, self.W * 0.045) if self.sx >= 0.6 else 6.5
        bx, by = self.x + thick * 0.8, self.y + thick * 0.55
        out = [f'<path d="{d}" fill="{band}" transform="{T(bx, by, self.deg, 1, self.sx)}"/>',
               f'<g transform="{tr}">',
               f'<clipPath id="{cid}"><path d="{d}"/></clipPath>',
               f'<path d="{d}" fill="{self.fill}"/>',
               f'<g clip-path="url(#{cid})">']
        # flat shaded half: right of a gently bowed line (pad is slightly domed)
        ts = [-0.1, 0.1, 0.3, 0.5, 0.7, 0.9, 1.1]
        sgn = 1 if self.sx > 0 else -1
        line_pts = [(sgn * self.W * (0.14 + 0.1 * math.sin(math.pi * min(max(t, 0), 1))), -self.L * t) for t in ts]
        far = [(sgn * self.W * 1.5, -self.L * t) for t in ts[::-1]]
        sp = line_pts + far
        out.append(f'<path d="{cr_path(sp, closed=True, sharp={0, len(ts) - 1, len(ts), len(sp) - 1})}" fill="{sh}"/>')
        if tufts:
            out.append(self.tufts(blocked))
        out.append("</g></g>")
        return "".join(out)

    def world_poly(self, n=48, dx=0.0, dy=0.0):
        """Outline as a world-space polygon (the thickness band is the same, offset by dx, dy)."""
        R = [self.local_to_world(self.hw(i / n, 1), -self.L * i / n) for i in range(n + 1)]
        Lf = [self.local_to_world(-self.hw(i / n, -1), -self.L * i / n) for i in range(n, -1, -1)]
        return [(x + dx, y + dy) for x, y in R + Lf]

    def occluders(self):
        """What this pad covers when drawn in front: its face and its thickness band."""
        thick = max(4.0, self.W * 0.045) if self.sx >= 0.6 else 6.5
        return [self.world_poly(), self.world_poly(dx=thick * 0.8, dy=thick * 0.55)]

    def tufts(self, blocked=None):
        """Areoles in a quincunx (diagonal) lattice, as on the real plant, each
        nudged a little off the grid so the lattice reads as grown, not printed.
        Spacing is measured in world units so edge-on pads keep the same
        density; each areole is counter-scaled so it stays round. Areoles are
        single opaque discs >= 4.5 units across at print scale. A disc that
        would be cut by this pad's own edge, a pad drawn in front of it or the
        pot rim (`blocked(world point)`) is left out: no half-dots."""
        sx = self.sx
        gy = 19.0            # row spacing (world units, pre plant-scale)
        gx = 23.0            # spacing along a row
        rnd = random.Random(self.seed)
        ox = rnd.uniform(-gx / 2, gx / 2)
        v = "a" if self.fill in (P["pale"], P["light"]) else "b"
        own = self.world_poly()
        uses = []
        inv = 1 / sx
        j = 0
        y0 = -self.L * 0.06
        while y0 > -self.L * 0.97:
            shift = (gx / 2 if j % 2 else 0) + ox
            for i in range(-8, 9):
                jx, jy = rnd.uniform(-2.5, 2.5), rnd.uniform(-2.0, 2.0)   # drawn for every slot: stable
                wx = i * gx + shift + jx     # world-ish x before foreshortening
                y = y0 + jy
                t = -y / self.L
                if not 0 < t < 1:
                    continue
                px = wx / sx if sx < 0.99 else wx
                side = 1 if px >= 0 else -1
                if abs(px) * min(sx, 1) > (self.hw(t, side)) * min(sx, 1) - 5.5:
                    continue
                w = self.local_to_world(px, y)
                if _edge_dist(own, w) < EDGE_CLEAR or (blocked and blocked(w)):
                    continue
                if abs(inv - 1) < 1e-3:
                    uses.append(f'<use href="#ar{v}" x="{f(px)}" y="{f(y)}"/>')
                else:
                    uses.append(f'<use href="#ar{v}" transform="translate({f(px)} {f(y)}) scale({inv:.2f} 1)"/>')
            y0 -= gy
            j += 1
        return "".join(uses)


EDGE_CLEAR = 6.4     # areole centre to any edge that cuts it (radius 2.6 + ~4 units clear), pre plant-scale


def _seg_dist(p, a, b):
    ax, ay = b[0] - a[0], b[1] - a[1]
    L2 = ax * ax + ay * ay or 1e-9
    u = max(0.0, min(1.0, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / L2))
    return math.hypot(p[0] - a[0] - u * ax, p[1] - a[1] - u * ay)


def _edge_dist(poly, p):
    return min(_seg_dist(p, poly[i - 1], poly[i]) for i in range(len(poly)))


def _inside(poly, p):
    x, y, c = p[0], p[1], False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i - 1], poly[i]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c


def glochid_defs():
    """Areole discs: light gold (mustard lifted toward cream, same family) on the darker pads (light knockout),
    mustard on the pale young pads (dark-on-light). r=2.6 -> 5.6 units wide
    after the plant scale, above the 4.5-unit knockout minimum."""
    return ('<defs>'
            f'<circle id="arb" r="2.6" fill="#E4C67A"/>'
            f'<circle id="ara" r="2.4" fill="{P["mustard"]}"/>'
            '</defs>')


# ------------------------------------------------------------------ flower
def flower(x, y, deg, s=1.0, bud=False):
    """Yellow cup flower (or bud) sitting on a pad rim: pericarpel (little
    green 'pad' with tufts) then petals. Base at (x,y)."""
    g = [f'<g transform="{T(x, y, deg, s)}">']
    # pericarpel
    per = cr_path([(0, 3), (9, -2), (11, -14), (8, -24), (-8, -24), (-11, -14), (-9, -2)], closed=True)
    cid = uid("fp")
    pc = []  # drawn last: the ovary rim overlaps the petal bases
    pc.append(f'<path d="{per}" fill="{P["sage"]}" transform="translate(3 2)"/>')
    pc.append(f'<clipPath id="{cid}"><path d="{per}"/></clipPath><path d="{per}" fill="{P["light"]}"/>')
    pc.append(f'<g clip-path="url(#{cid})"><rect x="4" y="-30" width="12" height="36" fill="{SHADE[P["light"]]}"/>'
             '<use href="#ara" x="-4" y="-7"/><use href="#ara" x="4" y="-14"/></g>')
    def petal(a, L, w, col, sh=None, oy=-20.0, claw=0.40, bw=0.14):
        """Obovate petal (rounded tip) from the cup base, rotated by a; the
        turned-away (right) half flat-shaded."""
        pts = [(-w * bw, 0), (w * bw, 0), (w * claw, -L * 0.40), (w * 0.50, -L * 0.72),
               (w * 0.36, -L * 0.93), (0, -L), (-w * 0.36, -L * 0.93), (-w * 0.50, -L * 0.72),
               (-w * claw, -L * 0.40)]
        d = cr_path(pts, closed=True, sharp={0, 1})
        tr = f"translate(0 {f(oy)}) rotate({f(a)})"
        if not sh:
            return f'<path d="{d}" fill="{col}" transform="{tr}"/>'
        c = uid("fq")
        return (f'<g transform="{tr}"><clipPath id="{c}"><path d="{d}"/></clipPath><path d="{d}" fill="{col}"/>'
                f'<path d="M{f(w * 0.08)} 2 Q{f(w * 0.16)} {f(-L * 0.5)} {f(w * 0.02)} {f(-L - 2)} L{f(w)} {f(-L - 2)} '
                f'L{f(w)} 2Z" fill="{sh}" clip-path="url(#{c})"/></g>')
    if bud:
        # closed bud: three furled petals (same mustard family as the open flower)
        for a, L, c, sh in ((-8, 31, BUTTER2, None), (8, 31, BUTTER2, None), (0, 34, FL_MUST, MUST_SH)):
            g.append(petal(a, L, 16, c, sh, oy=-19, claw=0.4, bw=0.3))
    else:
        # open cup seen from the side, a little from above. The back petals
        # show their inner face in the cup's shadow (two mid mustards that
        # alternate so each petal reads); the throat is a mid ochre only a
        # step deeper, holding a small low-contrast tuft of pale yellow-green
        # stamens + stigma; the three front petals face the light and are the
        # lightest part of the flower (lit / turned-away halves), so the cup
        # reads as a rounded form rather than a flat disc.
        for a, L, c in ((-62, 31, BACK2), (62, 31, BACK2), (-21, 38, FL_MUST), (21, 38, BACK1)):
            g.append(petal(a, L, 18, c, oy=-22, claw=0.3))
        g.append(f'<ellipse cx="0" cy="-41.5" rx="14" ry="7.5" fill="{THROAT}"/>')
        for sx_, sy_, r_ in ((-3.6, -42.6, 1.6), (3.4, -42.9, 1.6), (-1.4, -45.4, 1.6), (1.9, -45.6, 1.5),
                             (0.4, -40.6, 1.6)):
            g.append(f'<circle cx="{f(sx_)}" cy="{f(sy_)}" r="{f(r_)}" fill="{STAMEN}"/>')
        g.append(f'<circle cx="0" cy="-43.2" r="1.9" fill="{STIGMA}"/>')
        for a, L, c, sh in ((-38, 26, BUTTER, BUTTER2), (38, 26, BUTTER, BUTTER2), (0, 23, LIT, BUTTER)):
            g.append(petal(a, L, 16, c, sh, oy=-19, claw=0.38, bw=0.26))
    g += pc
    g.append("</g>")
    return "".join(g)


# ------------------------------------------------------------------ build
def build():
    reset_ids()
    back, front = pot(kind="bowl", cx=300, rim_y=600, bottom=752, rx=112, rim_h=28, base_w=78, band=True)
    D, F, M, S, Lt, Pa = P["deep"], P["forest"], P["mid"], P["sage"], P["light"], P["pale"]

    # base pad, rooted below the rim
    p0 = Pad(292, 672, -4, 228, 168, M, asym=0.04, seed=1)
    # tier 2: left pad leans out, right pad more upright (no mirror symmetry)
    a3 = p0.top(4, 14)
    p3 = Pad(a3[0], a3[1], 6, 196, 150, BACKPAD, sx=0.42, seed=3)            # edge-on, centre-back
    a1 = p0.top(-42, 16)
    p1 = Pad(a1[0], a1[1], -28, 182, 136, S, asym=-0.05, seed=4)
    a2 = p0.top(36, 16)
    p2 = Pad(a2[0], a2[1], 21, 158, 118, S, asym=0.05, seed=5)
    # ears
    e5a = p3.top(-2, 6)
    e5 = Pad(e5a[0], e5a[1], -13, 104, 80, Lt, seed=9)
    ea = p1.top(-40, 11)
    e1 = Pad(ea[0], ea[1], -32, 104, 78, Lt, seed=6)
    eb = p1.top(12, 11)
    e2 = Pad(eb[0], eb[1], -13, 124, 92, Pa, seed=7)
    ec = p2.top(-8, 11)
    e3 = Pad(ec[0], ec[1], 9, 114, 86, Pa, seed=8)
    ed = p2.top(48, 11)
    e4 = Pad(ed[0], ed[1], 54, 92, 68, Lt, seed=10)

    pads = [p0, p3, p1, p2, e5, e1, e4, e2, e3]
    body = [glochid_defs(), back]
    # whole plant scaled about the soil point (keeps joints exact)
    body.append(f'<g transform="translate({f(300 - SC * (300 - DX))} {f(640 - SC * 640)}) scale({SC})">')
    # plant-group -> canvas: the pot rim's front edge (drawn over the base pad) in plant-group coordinates
    tx, ty = 300 - SC * (300 - DX), 640 - SC * 640
    RIM_Y, RIM_RX = 600, 112
    RIM_RY = RIM_RX * 0.15

    def under_rim(w):
        X, Y = tx + SC * w[0], ty + SC * w[1]
        u = (X - 300) / RIM_RX
        top = RIM_Y + RIM_RY * math.sqrt(max(0.0, 1 - u * u)) if abs(u) < 1 else RIM_Y
        return Y > top - SC * EDGE_CLEAR

    for k, p in enumerate(pads):
        occ = [q for later in pads[k + 1:] for q in later.occluders()]

        def blocked(w, occ=occ):
            return under_rim(w) or any(_inside(q, w) or _edge_dist(q, w) < EDGE_CLEAR for q in occ)
        body.append(p.svg(blocked=blocked))
    fa = e2.top(8, 3)
    body.append(flower(fa[0], fa[1], -6, 1.5))
    fb = e3.top(-26, 3)
    body.append(flower(fb[0], fb[1], -14, 1.05, bud=True))
    body.append("</g>")
    body.append(front)
    return "".join(body)


if __name__ == "__main__":
    doc = svg_doc(build(), "Opuntia microdasys")
    out = os.path.join(os.path.dirname(HERE), "out", "opuntia_microdasys.svg")
    with open(out, "w") as fh:
        fh.write(doc)
    print(out, len(doc))
