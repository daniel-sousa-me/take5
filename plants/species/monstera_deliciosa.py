"""Monstera deliciosa — v4 card art.

Leaves are built as true polygons with shapely: a cordate blade minus
constant-width slits (round inner ends, following the lateral-vein angle)
minus a few midrib holes, then morphologically opened so the fingers get
softly rounded ends.  Everything is emitted in global coordinates.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import PAL, SHADE, cr_sample, ribbon, pot, svg_doc, uid, reset_ids, f  # noqa: E402

from shapely.geometry import Polygon, LineString, Point, MultiPolygon  # noqa: E402
from shapely.affinity import rotate, scale, translate  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

P = PAL


# ------------------------------------------------------------------ geometry
def poly_d(geom, tol=0.22):
    """Polygon / MultiPolygon -> compact path data (absolute M, relative l)."""
    geom = geom.simplify(tol, preserve_topology=True)
    polys = [geom] if isinstance(geom, Polygon) else list(geom.geoms)
    out = []
    for pg in polys:
        for ring in [pg.exterior] + list(pg.interiors):
            c = list(ring.coords)[:-1]
            s = [f"M{f(c[0][0])} {f(c[0][1])}l"]
            px, py = round(c[0][0], 1), round(c[0][1], 1)
            parts = []
            for x, y in c[1:]:
                x, y = round(x, 1), round(y, 1)
                parts.append(f"{f(x - px)} {f(y - py)}")
                px, py = x, y
            s.append(" ".join(parts).replace(" -", "-"))
            s.append("z")
            out.append("".join(s))
    return "".join(out)


def mix(a, b, t):
    """Opaque pre-blend of hex colour b over a at strength t."""
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02X}" for i in (1, 3, 5))


def lum(c):
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def line_d(pts):
    return "M" + "L".join(f"{f(x)} {f(y)}" for x, y in pts)


class MLeaf:
    """Monstera blade. Local frame: sinus/petiole at (0,0), tip at (0,-1) (unit L)."""

    def __init__(self, L, seed, slits=(6, 6), holes=True, bend=0.0, young=False, wscale=1.0, trim=None):
        # trim: {(side, i): (start, end[, dt])} per-slit override of where a slit starts and ends along its vein
        # (units of L; side 1 = right, -1 = left, i counted from the base; end None = runs out through the
        # margin, a number = stops short of it as a closed hole; (None, None) = no slit; dt shifts the slit
        # along the midrib; {("hole", side, k): None} leaves out the midrib hole after slit k). Used where a
        # leaf behind would otherwise show through only part of a slit (a hard leaf/paper break in one slit).
        trim = trim or {}
        self.L, self.bend = L, bend
        rnd = random.Random(seed)
        self.rnd = rnd
        j = lambda v, a=0.012: v + rnd.uniform(-a, a)
        # right-margin nodes from sinus to tip (x, y) in units of L
        base = [(0.0, 0.0), (0.06, j(0.085)), (0.19, j(0.13)), (0.34, j(0.095)), (0.45, j(-0.03)),
                (0.505, j(-0.22)), (0.49, j(-0.42)), (0.425, j(-0.61)), (0.31, j(-0.785)),
                (0.16, j(-0.925)), (0.0, -1.0)]
        if young:
            base = [(0.0, 0.0), (0.08, 0.08), (0.21, 0.1), (0.33, 0.04), (0.41, -0.1),
                    (0.43, -0.3), (0.39, -0.5), (0.3, -0.69), (0.18, -0.86), (0.07, -0.96), (0.0, -1.0)]
        right = [(x * wscale * j(1, 0.03), y) for x, y in base]
        left = [(-x * wscale * j(1, 0.03), y) for x, y in base]
        R = cr_sample(right, 10)
        Lm = cr_sample(left, 10)
        ring = R + Lm[::-1][1:-1]
        blade = Polygon([self.bent(p) for p in ring]).buffer(0)
        self.blade_full = blade
        cuts = []
        self.fingers = []  # vein centre lines (local), for vein drawing
        self.holes = []
        for side, n in ((1, slits[0]), (-1, slits[1])):
            if n <= 0:
                self.fingers += self._vein_lines(side, [0.2, 0.36, 0.52, 0.68, 0.82])
                continue
            # inner ends evenly spread along the midrib
            t0, t1 = (0.07, 0.80) if n >= 4 else (0.25, 0.72)
            ts = [t0 + (t1 - t0) * (i + 0.5 + rnd.uniform(-0.12, 0.12)) / n for i in range(n)]
            wid = 0.034 * j(1, 0.06)
            for i, t in enumerate(ts):
                u = (t - t0) / (t1 - t0)
                inner = 0.175 - 0.055 * math.sin(u * math.pi) + rnd.uniform(-0.018, 0.018)
                if young:
                    inner = 0.22
                start, end, dt = (tuple(trim.get((side, i), (inner, None))) + (0.0,))[:3]
                if start is None:  # slit left out (one hidden under a front leaf)
                    continue
                pts = self._vein(side, t + dt, start, 1.0 if end is None else end - start)
                cuts.append(LineString(pts).buffer(wid / 2 * (0.85 if young else 1), cap_style=1,
                                                   resolution=8))
            # vein centres between the slits
            sp = (t1 - t0) / n
            mids = [(a + b) / 2 for a, b in zip([ts[0] - sp] + ts, ts + [ts[-1] + sp])]
            self.fingers += [self._vein(side, t, 0.0, 0.9) for t in mids if 0.03 < t < 0.95]
            if holes and not young:
                # a few small holes in the band near the midrib, between slits
                for k, (a, b) in enumerate(zip(ts, ts[1:])):
                    if rnd.random() < 0.55 and trim.get(("hole", side, k), True):
                        tm = (a + b) / 2
                        c = self._vein(side, tm, 0.0, 0.2)
                        p0 = self._at(c, 0.05)
                        p1 = self._at(c, 0.088)
                        h = LineString([p0, p1]).buffer(0.019, cap_style=1, resolution=8)
                        cuts.append(h)
        leaf = blade.difference(unary_union(cuts)) if cuts else blade
        r = 0.011
        leaf = leaf.buffer(-r, resolution=6).buffer(r, resolution=6)
        if isinstance(leaf, MultiPolygon):  # keep the main body only
            leaf = max(leaf.geoms, key=lambda g: g.area)
        self.geom = leaf

    # --- local helpers
    def bent(self, p):
        x, y = p
        return (x + self.bend * y * y, y)

    def axis(self, t):
        return self.bent((0.0, -t))

    def _at(self, pts, dist):
        ls = LineString(pts)
        pt = ls.interpolate(dist)
        return (pt.x, pt.y)

    def _vein(self, side, t, start, length):
        """Lateral vein leaving the midrib at t: lower veins nearly horizontal
        (slightly drooping), upper ones swept toward the tip; slight curve."""
        ang0 = math.radians(98 - 62 * t)  # angle from the midrib direction
        pts = []
        x0, y0 = self.axis(t)
        steps = 14
        for k in range(steps + 1):
            s = k / steps * 0.75
            a = ang0 - math.radians(18) * (s / 0.75) ** 1.3
            # integrate
            if k == 0:
                x, y = x0, y0
            else:
                ds = 0.75 / steps
                x += side * math.sin(a) * ds
                y += -math.cos(a) * ds
            pts.append((x, y))
        ls = LineString(pts)
        d0, d1 = start, min(start + length, ls.length)
        out = [self._at(pts, d0 + (d1 - d0) * i / 10) for i in range(11)]
        return out

    def _vein_lines(self, side, ts):
        return [self._vein(side, t, 0.0, 0.8) for t in ts]

    # --- placement
    def place(self, g, x, y, rot, flip=1):
        g = scale(g, xfact=self.L * flip, yfact=self.L, origin=(0, 0))
        g = rotate(g, rot, origin=(0, 0))
        return translate(g, x, y)

    def place_pt(self, p, x, y, rot, flip=1):
        px, py = p[0] * self.L * flip, p[1] * self.L
        a = math.radians(rot)
        return (x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a))


def draw_leaf(spec, trim=None):
    (x, y, rot, L, fill, seed, slits, flip, bend, young, vein_col) = spec
    lf = MLeaf(L, seed, slits=slits, bend=bend, young=young, holes=not young, trim=trim)
    G = lf.place(lf.geom, x, y, rot, flip)
    d = poly_d(G)
    cid = uid("mc")
    out = [f'<clipPath id="{cid}"><path d="{d}" clip-rule="evenodd"/></clipPath>',
           f'<path d="{d}" fill="{fill}" fill-rule="evenodd"/>']
    inner = []
    # shaded half: the side of the midrib facing lower-right (away from light)
    mid = [lf.place_pt(lf.axis(t), x, y, rot, flip) for t in [-0.3] + [i / 10 for i in range(11)] + [1.3]]
    far = []
    halves = []
    for sg in (1, -1):
        ex = [lf.place_pt((sg * 2.0 + lf.axis(t)[0], -t), x, y, rot, flip) for t in (1.3, -0.3)]
        halves.append(Polygon(mid + ex).buffer(0).intersection(G))
    halves.sort(key=lambda h: h.centroid.x + 0.6 * h.centroid.y if not h.is_empty else -1e9)
    sh = halves[-1]
    if not sh.is_empty and SHADE.get(fill):
        inner.append(f'<path d="{poly_d(sh)}" fill="{SHADE[fill]}" fill-rule="evenodd"/>')
    # Print policy: the faint lateral veins could not be print-safe without striping the fingers (the slits
    # already carry the vein rhythm), so they are gone; the midrib stays, opaque (pre-blended), >= print min.
    col = mix(fill, vein_col, 0.5)
    mw = max(L * 0.012, 4.0 if lum(col) > 0.55 else 3.0)
    mr = [lf.place_pt(lf.axis(t), x, y, rot, flip) for t in [0.0, 0.2, 0.4, 0.6, 0.8, 0.95]]
    inner.append(f'<path d="{line_d(mr)}" fill="none" stroke="{col}" stroke-width="{f(mw)}" '
                 f'stroke-linecap="round"/>')
    out.append(f'<g clip-path="url(#{cid})">' + "".join(inner) + "</g>")
    sinus = lf.place_pt((0, 0), x, y, rot, flip)
    tuck = lf.place_pt(lf.axis(0.09), x, y, rot, flip)
    return "".join(out), sinus, tuck


def petiole(src, ctrl, sinus, tuck, w0, w1, col):
    return (f'<path d="{ribbon([src, ctrl, sinus, tuck], w0, w1, per=8)}" fill="{col}"/>')


# ------------------------------------------------------------------ plant
# (x, y, rot, L, fill, seed, slits(r,l), flip, bend, young, vein, petiole: src, ctrl, w0, w1, col)
LEAVES = [
    # A: big top leaf, back, leaning left
    dict(leaf=(284, 318, -13, 218, P["deep"], 3, (6, 6), 1, 0.05, False, P["light"]),
         src=(294, 596), ctrl=(292, 430), w=(12, 8), col=P["mid"],
         trim={(1, 0): (None, None)}),  # lowest right slit lies under B: it only showed through B's slits
    # C: left, mid height
    dict(leaf=(232, 420, -68, 168, P["mid"], 5, (5, 5), -1, 0.07, False, P["pale"]),
         src=(286, 598), ctrl=(262, 492), w=(10.5, 7), col=P["forest"],
         # (1, 0) lies under E; the two basal left slits stop short of A's edge, so they show paper only
         trim={(1, 0): (None, None), (-1, 0): (0.156, 0.30), (-1, 1): (0.126, 0.31)}),
    # B: big right leaf rising, overlapping A
    dict(leaf=(356, 372, 42, 206, P["sage"], 7, (6, 5), 1, -0.06, False, P["pale"]),
         src=(306, 598), ctrl=(334, 470), w=(11.5, 7.5), col=P["forest"],
         # the two lowest left slits start inside A's outline (all dark); the third is moved a little up the
         # midrib, off A's tip, so no dark sliver runs down one side of it
         trim={(-1, 0): (0.18, None), (-1, 1): (0.19, None), (-1, 2): (0.130, None, 0.035)}),
    # E: lower-left front, drooping
    dict(leaf=(248, 478, -106, 130, P["light"], 11, (4, 4), 1, -0.07, False, P["mid"]),
         src=(292, 600), ctrl=(266, 552), w=(9, 6), col=P["mid"],
         # (1, 2) starts and stops inside C's outline (all C), and the midrib hole C's margin cut in half
         # is left out
         trim={(1, 2): (0.16, 0.35), ("hole", 1, 1): None}),
    # D: lower-right front
    dict(leaf=(362, 474, 96, 150, P["deep"], 13, (4, 5), -1, 0.07, False, P["light"]),
         src=(308, 600), ctrl=(340, 546), w=(9.5, 6.5), col=P["mid"],
         trim={(1, 0): (0.33, None), (1, 1): (0.142, 0.32)}),  # all over B / all over paper
    # F: young leaf, few splits
    dict(leaf=(318, 470, 16, 98, P["pale"], 17, (1, 2), 1, 0.08, True, P["sage"]),
         src=(302, 600), ctrl=(312, 530), w=(7, 5), col=P["sage"],
         trim={(1, 0): (None, None)}),  # its one right split showed paper, D and B's edge in a few units
]


def build():
    reset_ids()
    back, front = pot("classic", rx=106, base_w=76)
    g = []
    for spec in LEAVES:
        svg, sinus, tuck = draw_leaf(spec["leaf"], spec.get("trim"))
        g.append(petiole(spec["src"], spec["ctrl"], sinus, tuck, *spec["w"], spec["col"]))
        g.append(svg)
    return back + "".join(g) + front


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out", "monstera_deliciosa.svg")
    doc = svg_doc(build(), "Monstera deliciosa")
    open(out, "w").write(doc)
    print(out, len(doc))
