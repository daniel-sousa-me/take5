"""Pilea peperomioides (Chinese money plant) — v4.

Round peltate 'coin' leaves on long pale petioles that spiral out of a short,
upright central stem. Seen from the side, each petiole slips under the disc
and the attachment shows as a pale dot inside the leaf with faint veins
radiating from it. Lower leaves: big, dark, arching out; crown leaves: small,
light, tilted up (strong foreshortening). A small pup sits in the soil.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import PAL, SHADE, cr_path, stem, pot, svg_doc, uid, reset_ids, f  # noqa: E402

P = PAL
# tone ladder, dark -> light: (fill, cup-shade, vein, dot). Veins are opaque and
# only ~one step lighter than the blade (subtle), drawn as tapered wedges >= 4.4
# units wide at the dot so they print on every leaf.
TONES = {
    "deep":   (P["deep"],   SHADE[P["deep"]],   "#4A634D", P["light"]),
    "forest": (P["forest"], SHADE[P["forest"]], "#587558", P["pale"]),
    "mid":    (P["mid"],    SHADE[P["mid"]],    "#728A6C", P["pale"]),
    "sage":   (P["sage"],   SHADE[P["sage"]],   "#95A688", "#D7DDCC"),  # pale green tint, L* 87.3 (<= 88 on white stock)
    "light":  (P["light"],  SHADE[P["light"]],  "#B9C4AB", "#FFFFFF"),  # paper-white dot (white stock)
    "pale":   (P["pale"],   SHADE[P["pale"]],   "#D7DDCC", "#FFFFFF"),  # vein tint L* 87.3
}
VEIN_W0, VEIN_W1 = 4.4, 1.0   # world units at the dot / at the vein end
DOT_MIN_R = 2.5               # world minor radius of the attachment dot (>= 4.5 across)


class Coin:
    """A round peltate leaf. c = centre, R = radius, sq = foreshortening
    (minor/major), rot = degrees of the major axis, node = petiole origin."""

    def __init__(self, c, R, sq, rot, tone, node, via, pet_w=(5.5, 3.2), cup=1.0,
                 attach=0.2, nveins=6, vrot=0.0):
        self.c, self.R, self.sq, self.rot = c, R, sq, math.radians(rot)
        self.tone, self.node, self.via = tone, node, via
        self.pet_w, self.cup, self.nveins, self.vrot = pet_w, cup, nveins, vrot
        # petiole direction in local (unsquashed) leaf coordinates
        src = via[-1] if via else node
        dx, dy = src[0] - c[0], src[1] - c[1]
        lx, ly = self.to_local(dx, dy)
        m = math.hypot(lx, ly) or 1
        self.pdir = (lx / m, ly / m)
        self.A = (self.pdir[0] * attach * R, self.pdir[1] * attach * R)

    def to_local(self, dx, dy):
        cs, sn = math.cos(-self.rot), math.sin(-self.rot)
        x, y = dx * cs - dy * sn, dx * sn + dy * cs
        return x, y / self.sq

    def w(self, u, v):
        """local circle coords -> world."""
        y = v * self.sq
        cs, sn = math.cos(self.rot), math.sin(self.rot)
        return (self.c[0] + u * cs - y * sn, self.c[1] + u * sn + y * cs)

    def radius(self, phi):
        # coin with a barely-there tip opposite the petiole and a slight
        # flattening on the petiole side
        pd = math.atan2(self.pdir[1], self.pdir[0])
        dt = math.cos(phi - (pd + math.pi))
        tip = 0.04 * max(0.0, dt) ** 4
        flat = -0.025 * max(0.0, -dt) ** 2
        return self.R * (1 + tip + flat)

    def outline(self, n=16, shift=(0, 0), scale=1.0):
        pts = []
        for i in range(n):
            phi = 2 * math.pi * i / n
            r = self.radius(phi) * scale
            pts.append(self.w(shift[0] + r * math.cos(phi), shift[1] + r * math.sin(phi)))
        return cr_path(pts, closed=True)

    def attach_world(self):
        return self.w(*self.A)

    # ------------------------------------------------------------ render
    def petiole(self):
        fill = getattr(self, "pet_col", None) or P["light"]
        A = self.attach_world()
        prev = self.via[-1] if self.via else self.node
        # the visible petiole must enter the rim aimed straight at the centre
        # dot, then run on (hidden under the blade) to end beneath it
        rim = self.w(*self.rim_local())
        ux, uy = prev[0] - A[0], prev[1] - A[1]
        m = math.hypot(ux, uy) or 1
        dq = math.hypot(rim[0] - A[0], rim[1] - A[1]) + 14
        pts = [self.node] + list(self.via)
        if m > dq + 10:
            pts.append((A[0] + ux / m * dq, A[1] + uy / m * dq))
        pts.append(A)
        return stem(pts, self.pet_w[0], self.pet_w[1], fill)

    def rim_local(self, phi=None):
        """point on the rim from the attachment point A along phi (default:
        toward the petiole), local coords."""
        ax, ay = self.A
        if phi is None:
            phi = math.atan2(self.pdir[1], self.pdir[0])
        ux, uy = math.cos(phi), math.sin(phi)
        b = ax * ux + ay * uy
        cc = ax * ax + ay * ay - (self.R * 0.97) ** 2
        L = -b + math.sqrt(b * b - cc)
        return ax + ux * L, ay + uy * L

    def svg(self):
        fill, shade, vcol, dot = TONES[self.tone]
        d = self.outline()
        cid = uid("pl")
        out = [f'<clipPath id="{cid}"><path id="{cid}p" d="{d}"/></clipPath>', f'<use href="#{cid}p" fill="{fill}"/>']
        inner = []
        # veins: opaque tapered wedges radiating from the attachment point; the
        # first one runs toward the petiole, so stalk -> rim -> vein -> dot reads
        # as one line. Built in world space so the width survives foreshortening.
        ax, ay = self.A
        Aw = self.w(ax, ay)
        n = self.nveins
        base = math.atan2(self.pdir[1], self.pdir[0]) + self.vrot
        vv = []
        for k in range(n):
            phi = base + 2 * math.pi * k / n
            e = self.rim_local(phi)
            frac = 0.86 if k == 0 else (0.80 if k % 2 else 0.64)
            el = (ax + (e[0] - ax) * frac, ay + (e[1] - ay) * frac)
            mid = ((ax + el[0]) / 2, (ay + el[1]) / 2)
            ux, uy = el[0] - ax, el[1] - ay
            bend = 0.08 if k % 2 else -0.06
            mid = (mid[0] - uy * bend, mid[1] + ux * bend)
            E, M = self.w(*el), self.w(*mid)
            tx, ty = E[0] - Aw[0], E[1] - Aw[1]
            tm = math.hypot(tx, ty) or 1
            nx, ny = -ty / tm, tx / tm
            h0, h1 = VEIN_W0 / 2, VEIN_W1 / 2
            hm = (h0 + h1) / 2 * 1.3
            vv.append(f"M{f(Aw[0] + nx * h0)} {f(Aw[1] + ny * h0)}"
                      f"Q{f(M[0] + nx * hm)} {f(M[1] + ny * hm)} {f(E[0] + nx * h1)} {f(E[1] + ny * h1)}"
                      f"L{f(E[0] - nx * h1)} {f(E[1] - ny * h1)}"
                      f"Q{f(M[0] - nx * hm)} {f(M[1] - ny * hm)} {f(Aw[0] - nx * h0)} {f(Aw[1] - ny * h0)}Z")
        inner.append(f'<path d="{"".join(vv)}" fill="{vcol}"/>')
        # cupping: flat darker crescent on the lower-right rim (over the vein ends)
        if self.cup:
            lx, ly = self.to_local(0.55, 0.85)
            m = math.hypot(lx, ly)
            s = 0.16 * self.R * self.cup
            sh = (-lx / m * s, -ly / m * s)
            cres = d + self.outline(shift=sh, scale=1.0)
            inner.append(f'<path d="{cres}" fill="{shade}" fill-rule="evenodd"/>')
        # pale attachment dot: foreshortened, but never thinner than the dot minimum
        ru = max(2.8, self.R * 0.08)
        rv = max(ru, DOT_MIN_R / self.sq)
        dp = [self.w(ax + ru * math.cos(t), ay + rv * math.sin(t))
              for t in (2 * math.pi * i / 10 for i in range(10))]
        inner.append(f'<path d="{cr_path(dp)}" fill="{dot}"/>')
        out.append(f'<g clip-path="url(#{cid})">' + "".join(inner) + "</g>")
        return "".join(out)


STEM_X = 298
STEM = [(STEM_X + 2, 606), (STEM_X + 1, 530), (STEM_X - 2, 440), (STEM_X + 1, 350), (STEM_X + 2, 300)]


def leaves():
    """Returns the draw list (back -> front). The string "STEM" marks where
    the central stem is drawn, so back petioles tuck into it and front ones
    cross over it."""
    L = []

    def add(*a, pet=None, **k):
        c = Coin(*a, **k)
        c.pet_col = P[pet] if pet else None
        L.append(c)

    # ---- crown: young, pale leaves at the stem apex, peeking over the top leaf
    # (lifted a little up-left off the centre leaf so a short stretch of its stalk
    # shows between the two, entering the rim aimed at the centre dot)
    add((247, 121), 31, .50, -16, "light", (298, 318), [(290, 252), (256, 186)], pet_w=(3.8, 2.6), pet="sage", nveins=5)
    add((340, 114), 25, .44, 14, "pale", (299, 318), [(312, 250), (334, 148)], pet_w=(3.4, 2.2), pet="sage", nveins=5)
    # ---- back layer: big, dark leaves
    add((164, 322), 72, .88, -12, "deep", (298, 434), [], pet_w=(6, 3.4), pet="sage")
    add((430, 300), 76, .84, 10, "forest", (299, 456), [(346, 400), (404, 336)], pet_w=(6, 3.4), pet="sage")
    add((122, 486), 54, .54, -26, "forest", (298, 548), [(236, 516), (176, 503)], pet_w=(6, 3.4), pet="sage")
    add((474, 432), 58, .76, 14, "deep", (300, 534), [(370, 478), (436, 446)], pet_w=(6, 3.4), pet="sage")
    add((302, 186), 72, .80, -4, "mid", (300, 318), [(301, 260)], pet_w=(6, 3.6), pet="light")
    L.append("STEM")
    # ---- middle layer (petioles start behind the centre leaf)
    add((212, 250), 50, .66, -26, "sage", (298, 330), [(258, 296)], pet_w=(5, 3), pet="light")
    add((382, 208), 46, .54, 22, "sage", (300, 326), [(344, 272)], pet_w=(4.6, 2.8), pet="light")
    add((314, 286), 60, .93, 6, "light", (299, 336), [], pet_w=(5.5, 3.2), pet="light")
    # ---- front layer: nearer the viewer
    add((212, 446), 58, .96, 4, "mid", (297, 512), [(256, 480)], pet_w=(6, 3.4), pet="light")
    add((390, 412), 52, .62, 26, "sage", (300, 494), [(350, 448)], pet_w=(5.5, 3.2), pet="light")
    return L


def pup():
    """A small offset pup in the soil, left of the main stem."""
    out = []
    a = Coin((230, 546), 21, .70, -18, "light", (250, 602), [(244, 574)], pet_w=(3.8, 2.4), cup=.6, nveins=5)
    b = Coin((266, 556), 15, .55, 22, "sage", (254, 602), [(262, 580)], pet_w=(3.2, 2.2), cup=.6, nveins=5)
    a.pet_col = b.pet_col = P["sage"]
    for c in (b, a):
        out.append(c.petiole())
        out.append(c.svg())
    return "".join(out)


def central_stem():
    # (leaf scars on the bare lower stem were hairlines: dropped for print)
    return stem(STEM, 14, 7, P["forest"])


def build():
    reset_ids()
    back, front = pot(kind="classic", rx=100, rim_y=586, base_w=72, band=False)
    parts = [back]
    seq = leaves()
    k = seq.index("STEM")
    for lf in seq[:k]:  # back layer: petiole then disc
        parts += [lf.petiole(), lf.svg()]
    # remaining petioles all go behind the stem, so their bases tuck into it
    parts += [lf.petiole() for lf in seq[k + 1:]]
    parts.append(central_stem())
    parts += [lf.svg() for lf in seq[k + 1:]]
    parts.append(pup())
    parts.append(front)
    return "".join(parts)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "out", "pilea_peperomioides.svg")
    with open(out, "w") as fh:
        fh.write(svg_doc(build(), "Pilea peperomioides (Chinese money plant)"))
    print(out, os.path.getsize(out))
