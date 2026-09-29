"""Alocasia x amazonica 'Polly' -- v4 botanical card art.

Run:  python3 species/alocasia_amazonica.py   -> out/alocasia_amazonica.svg

Sagittate, sinuate-edged, near-black leaves with bold silvery veins and a
pale rim, held on long pale petioles that meet the blade just above the
basal sinus. One leaf is turned to show its burgundy underside; one new
leaf is still furled.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from core import PAL, Leaf, ribbon, cr_path, pot, svg_doc, T, f, uid, reset_ids  # noqa: E402

P = PAL
SOIL_Y = 600
VEIN = P["pale"]
SHADE_OF = {P["night"]: "#1F3025", P["deep"]: P["night"], P["forest"]: "#34503A",
            P["burgundy"]: P["wine"]}


def world(x, y, rot, s, lx, ly):
    a = math.radians(rot)
    lx, ly = lx * s, ly * s
    return (x + lx * math.cos(a) - ly * math.sin(a), y + lx * math.sin(a) + ly * math.cos(a))


# ------------------------------------------------------------------ leaf geometry
class Arrow:
    """Sagittate blade in local units (multiplied by L). Origin = petiole
    attachment; tip at (0,-1); sinus notch just below the origin; two basal
    lobes flaring back and out like the barbs of an arrowhead."""

    VY = [-0.11, -0.33, -0.54, -0.75]   # lateral vein ends (y)

    def __init__(self, L, lobe=1.0, wide=1.0, asym=0.0, curl=0.0):
        self.L, self.lobe, self.wide, self.asym, self.curl = L, lobe, wide, asym, curl

    def xw(self, y, sg):
        """Half-width of the main blade at height y (y in -1..0)."""
        t = -y
        w = 0.325 * self.wide * (1 - t) ** 0.95 * (1 + 0.22 * t)
        return w * (1 + sg * self.asym)

    def cx(self, y):
        """Midrib bows slightly (curl) toward one side."""
        t = -y
        return self.curl * t * t

    def p(self, x, y):
        return ((x + self.cx(y)) * self.L, y * self.L)

    def side(self, sg):
        lb, wd = self.lobe, self.wide
        k = 1 + sg * self.asym
        pts = [
            (sg * 0.07 * wd, 0.13 * lb),            # inner lobe edge
            (sg * 0.165 * wd, 0.24 * lb),
            (sg * 0.25 * wd * k, 0.30 * lb),         # rounded lobe tip
            (sg * 0.315 * wd * k, 0.265 * lb),
            (sg * 0.34 * wd * k, 0.15 * lb),         # outer lobe edge
            (sg * 0.335 * wd * k, 0.03),             # shoulder
        ]
        for i, vy in enumerate(self.VY):
            pts.append((sg * self.xw(vy, sg), vy))
            if i + 1 < len(self.VY):
                my = (vy + self.VY[i + 1]) / 2
                dip = 0.024 * (1 + my) ** 1.5 + 0.003
                pts.append((sg * (self.xw(my, sg) - dip), my))
        pts.append((sg * self.xw(-0.935, sg) * 0.9, -0.935))
        return [self.p(x, y) for x, y in pts]

    def outline(self):
        R, Lf = self.side(1), self.side(-1)
        pts = [self.p(0, 0.075)] + R + [self.p(0, -1.0)] + Lf[::-1]
        return cr_path(pts, closed=True, sharp={0, len(R) + 1})

    def half(self, sg):
        ys = [0.6, 0.3, 0.0, -0.25, -0.5, -0.75, -1.0, -1.3]
        mid = [self.p(0, y) for y in ys]
        far = [self.p(sg * 1.2, y) for y in ys]
        pts = mid + far[::-1]
        return cr_path(pts, closed=True, sharp={0, len(mid) - 1, len(mid), len(pts) - 1})

    def veins(self):
        """(pts, w0, w1) tapered vein ribbons, local px."""
        L = self.L
        out = [([self.p(0, 0.02), self.p(0, -0.47), self.p(0, -0.97)], 6.4, 2.2)]
        for sg in (1, -1):
            k = 1 + sg * self.asym
            # posterior costa into each basal lobe
            out.append(([self.p(0, 0.0), self.p(sg * 0.14 * self.wide, 0.12 * self.lobe),
                         self.p(sg * 0.265 * self.wide * k, 0.28 * self.lobe)], 5.2, 2.0))
            # primary laterals to the margin points
            for i, vy in enumerate(self.VY):
                y0 = min(0.0, vy + 0.13 + 0.02 * i)
                xe = sg * self.xw(vy, sg) * 0.99
                if i == 0:
                    xe = sg * 0.33 * self.wide * k
                mid = (xe * 0.5, vy + (y0 - vy) * 0.3)
                w0 = 5.0 - 0.15 * i
                out.append(([self.p(0, y0), self.p(*mid), self.p(xe, vy)], w0, 2.0))
        return out


def taper(pts, w0, w1):
    """Compact tapered vein: quadratic through 3 points (start, via, end)."""
    if len(pts) > 3:
        pts = [pts[0], pts[len(pts) // 2], pts[-1]]
    p0, pm, p2 = pts
    c = (2 * pm[0] - (p0[0] + p2[0]) / 2, 2 * pm[1] - (p0[1] + p2[1]) / 2)

    def nrm(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        return (-dy / m, dx / m)
    n0, n2, nc = nrm(p0, c), nrm(c, p2), nrm(p0, p2)
    wc = (w0 + w1) / 4
    A = [(p0[0] + n0[0] * w0 / 2, p0[1] + n0[1] * w0 / 2), (c[0] + nc[0] * wc, c[1] + nc[1] * wc),
         (p2[0] + n2[0] * w1 / 2, p2[1] + n2[1] * w1 / 2)]
    B = [(p0[0] - n0[0] * w0 / 2, p0[1] - n0[1] * w0 / 2), (c[0] - nc[0] * wc, c[1] - nc[1] * wc),
         (p2[0] - n2[0] * w1 / 2, p2[1] - n2[1] * w1 / 2)]
    q = lambda P: f"{f(P[0])} {f(P[1])}"
    return f"M{q(A[0])}Q{q(A[1])} {q(A[2])}L{q(B[2])}Q{q(B[1])} {q(B[0])}Z"


def leaf_svg(a, x, y, rot, fill, side=1, s=1.0, flip=False, vein=VEIN, rim=VEIN):
    d = a.outline()
    cid = uid("ac")
    sc = f" scale({-1 if flip else 1} 1)" if flip else ""
    g = [f'<g transform="{T(x, y, rot, s)}{sc}">',
         f'<clipPath id="{cid}"><path d="{d}"/></clipPath>',
         f'<path d="{d}" fill="{fill}"/>',
         f'<g clip-path="url(#{cid})">',
         f'<path d="{a.half(side)}" fill="{SHADE_OF[fill]}"/>']
    vd = "".join(taper(p, w0, w1) for p, w0, w1 in a.veins())
    g.append(f'<path d="{vd}" fill="{vein}"/>')
    # pale margin: clipped stroke, ~4 units visible inside the blade
    g.append(f'<path d="{d}" fill="none" stroke="{rim}" stroke-width="7.6" stroke-linejoin="round"/>')
    g.append("</g></g>")
    return "".join(g)


def petiole(x, y, x0, via, w0, w1, col, rot=None, L=None, ap=0.5):
    """Petiole from the soil to the blade. With the leaf given (rot, L) it is
    one smooth cubic whose last tangent runs along the leaf's own axis, up
    *between* the basal lobes, ending under the midrib / basal-vein junction
    (local origin): it always meets the blade at the sinus, never a lobe."""
    if rot is None:
        pts = [(x0, SOIL_Y)] + via + [(x, y)]
    else:
        p0, c1 = (x0, SOIL_Y), via[0]
        c2, p3 = world(x, y, rot, 1, 0, ap * L), (x, y)
        pts = []
        for i in range(9):
            t = i / 8
            u = 1 - t
            pts.append(tuple(u ** 3 * p0[k] + 3 * u * u * t * c1[k] + 3 * u * t * t * c2[k] + t ** 3 * p3[k]
                             for k in (0, 1)))
    return f'<path d="{ribbon(pts, w0, w1, per=4)}" fill="{col}"/>'


# ------------------------------------------------------------------ young rolled leaf
def rolled(x, y, rot, H, col, shade):
    lf = Leaf(H, [(0.0, 0.035), (0.15, 0.08), (0.45, 0.088), (0.75, 0.06), (0.93, 0.022)],
              bend=0.06, base_sharp=False)
    d = lf.path()
    cid = uid("rl")
    seam = cr_path([lf.pt(0.05, -0.08), lf.pt(0.35, 0.0), lf.pt(0.65, 0.06), lf.pt(0.92, 0.02)],
                   closed=False)
    return (f'<g transform="{T(x, y, rot)}"><clipPath id="{cid}"><path d="{d}"/></clipPath>'
            f'<path d="{d}" fill="{col}"/><g clip-path="url(#{cid})">'
            f'<path d="{lf.half_region("r")}" fill="{shade}"/>'
            f'<path d="{seam}" fill="none" stroke="{P["light"]}" stroke-width="4.5" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{P["light"]}" stroke-width="8"/>'
            f'</g></g>')


# ------------------------------------------------------------------ build
def build():
    reset_ids()
    back, front = pot(kind="classic", cx=300, rim_y=588, rx=98, rim_h=30, base_w=70, band=False)
    N, D, F = P["night"], P["deep"], P["forest"]
    PET, PET2 = P["sage"], P["light"]

    # x, y = petiole attachment; rot 0 = tip straight up (clockwise positive)
    leaves = [
        # --- back tier: tall, night
        dict(x=254, y=240, rot=-38, L=150, col=N, side=1, x0=288,
             via=[(288, 420)], w=(8.5, 5.5), pc=PET2, asym=0.04, curl=-0.04),
        dict(x=384, y=224, rot=56, L=156, col=N, side=-1, x0=310,
             via=[(312, 420)], w=(8.5, 5.5), pc=PET2, asym=-0.04, curl=0.05),
        # --- middle tier: held out sideways; petiole arches up and the blade
        # hangs from the sinus
        dict(x=192, y=356, rot=-96, L=132, col=D, side=-1, x0=286,
             via=[(282, 400)], w=(8, 5), pc=PET, curl=-0.05, lobe=0.95, ap=0.6),
        dict(x=416, y=376, rot=106, L=128, col=D, side=1, x0=314,
             via=[(318, 410)], w=(8, 5), pc=PET, curl=0.05, lobe=0.95, ap=0.6),
    ]
    # --- front focal leaf: lighter, fairly upright, slightly foreshortened
    focal = dict(x=298, y=338, rot=-8, L=150, col=F, side=1, x0=300,
                 via=[(300, 450)], w=(9, 6), pc=PET, curl=0.03)
    # --- turned leaf showing its burgundy underside, low left
    under = dict(x=222, y=472, rot=-118, L=104, col=P["burgundy"], x0=292,
                 via=[(288, 470)], w=(7, 4.5), pc=PET, ap=0.6)

    out = [back, '<g transform="translate(300 600) scale(1.07) translate(-300 -600)">']

    def put(sp, flip=False, vein=VEIN, rim=VEIN):
        a = Arrow(sp["L"], lobe=sp.get("lobe", 1), asym=sp.get("asym", 0), curl=sp.get("curl", 0))
        out.append(petiole(sp["x"], sp["y"], sp["x0"], sp["via"], *sp["w"], sp["pc"],
                           rot=sp["rot"], L=sp["L"], ap=sp.get("ap", 0.4)))
        out.append(leaf_svg(a, sp["x"], sp["y"], sp["rot"], sp["col"], sp.get("side", 1),
                            flip=flip, vein=vein, rim=rim))

    for sp in leaves[:2]:
        put(sp)
    # furled new leaf (paler, as new Polly leaves are) in front of the right back leaf
    rl_base = (320, 236)
    out.append(petiole(*rl_base, 305, [(310, 440)], 8, 7, PET2))
    out.append(rolled(rl_base[0], rl_base[1] + 6, 7, 140, P["mid"], SHADE_OF.get(P["mid"], "#4B6349")))
    for sp in leaves[2:]:
        put(sp)
    put(under, flip=True, vein=P["rose"], rim=P["rose"])
    put(focal)
    out.append("</g>")
    out.append(front)
    return "".join(out)


def main():
    svg = svg_doc(build(), "Alocasia amazonica (Alocasia 'Polly')")
    p = os.path.join(ROOT, "out", "alocasia_amazonica.svg")
    with open(p, "w") as fh:
        fh.write(svg)
    print(p, len(svg))


if __name__ == "__main__":
    main()
