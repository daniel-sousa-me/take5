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
MUST_SH = "#AE8436"  # shaded mustard (flower turned-away side)
BAND = {  # thickness band tone for each face tone (a clear step darker)
    P["pale"]: "#8E9E80", P["light"]: P["sage"], P["sage"]: "#5F7355",
    P["mid"]: P["forest"], P["forest"]: "#2E4633",
}
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

    def svg(self, tufts=True):
        d = self.path()
        cid = uid("pd")
        sh = SHADE.get(self.fill, "#27392C")
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
            out.append(self.tufts())
        out.append("</g></g>")
        return "".join(out)

    def tufts(self):
        """Areoles in a regular quincunx (diagonal) lattice, as on the real
        plant. Spacing is measured in world units so edge-on pads keep the
        same density; each areole is counter-scaled so it stays round.
        Areoles are single opaque discs >= 4.5 units across at print scale."""
        sx = self.sx
        gy = 19.0            # row spacing (world units, pre plant-scale)
        gx = 23.0            # spacing along a row
        rnd = random.Random(self.seed)
        ox = rnd.uniform(-gx / 2, gx / 2)
        v = "a" if self.fill in (P["pale"], P["light"]) else "b"
        uses = []
        inv = 1 / sx
        j = 0
        y = -self.L * 0.06
        while y > -self.L * 0.97:
            t = -y / self.L
            shift = (gx / 2 if j % 2 else 0) + ox
            for i in range(-8, 9):
                wx = i * gx + shift          # world-ish x before foreshortening
                px = wx / sx if sx < 0.99 else wx
                side = 1 if px >= 0 else -1
                if abs(px) * min(sx, 1) > (self.hw(t, side)) * min(sx, 1) - 5.5:
                    continue
                if abs(inv - 1) < 1e-3:
                    uses.append(f'<use href="#ar{v}" x="{f(px)}" y="{f(y)}"/>')
                else:
                    uses.append(f'<use href="#ar{v}" transform="translate({f(px)} {f(y)}) scale({inv:.2f} 1)"/>')
            y -= gy
            j += 1
        return "".join(uses)


def glochid_defs():
    """Areole discs: warm cream-gold on the darker pads (light knockout),
    mustard on the pale young pads (dark-on-light). r=2.6 -> 5.6 units wide
    after the plant scale, above the 4.5-unit knockout minimum."""
    return ('<defs>'
            f'<circle id="arb" r="2.6" fill="#E9D59A"/>'
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
    g.append(f'<path d="{per}" fill="{P["sage"]}" transform="translate(3 2)"/>')
    g.append(f'<clipPath id="{cid}"><path d="{per}"/></clipPath><path d="{per}" fill="{P["light"]}"/>')
    g.append(f'<g clip-path="url(#{cid})"><rect x="4" y="-30" width="12" height="36" fill="{SHADE[P["light"]]}"/>'
             '<use href="#ara" x="-4" y="-8"/><use href="#ara" x="4" y="-15"/><use href="#ara" x="-3" y="-20"/></g>')
    if bud:
        b = cr_path([(-8, -21), (-10, -31), (-6, -43), (0, -49), (6, -43), (10, -31), (8, -21)], closed=True,
                    sharp={3})
        bc = uid("fb")
        g.append(f'<clipPath id="{bc}"><path d="{b}"/></clipPath><path d="{b}" fill="{P["mustard"]}"/>')
        g.append(f'<g clip-path="url(#{bc})"><path d="M1 -60 Q4 -36 1 -18 L20 -18 L20 -60Z" fill="{MUST_SH}"/>'
                 f'<path d="M-12 -41 Q0 -45.5 12 -41 L12 -60 L-12 -60Z" fill="{P["blush"]}"/></g>')
    else:
        def petal(a, L, w, col):  # obovate petal fanning out from the cup base
            p = cr_path([(-w * 0.15, 0), (w * 0.15, 0), (w * 0.42, -L * 0.45), (w * 0.52, -L * 0.8),
                         (0, -L), (-w * 0.52, -L * 0.8), (-w * 0.42, -L * 0.45)], closed=True, sharp={0, 1})
            return f'<path d="{p}" fill="{col}" transform="translate(0 -20) rotate({a})"/>'
        # back petals (amber) -> stamen boss in the cup mouth -> front cup (mustard, scalloped rim)
        for a, L, c in ((-20, 42, P["terra_hi"]), (21, 41, P["terra_hi"]), (-47, 36, P["amber"]), (48, 35, P["amber"])):
            g.append(petal(a, L, 22, c))
        g.append(f'<ellipse cx="0" cy="-49" rx="15" ry="5.5" fill="{P["cream"]}"/>')
        g.append(f'<ellipse cx="0" cy="-50" rx="5" ry="2.2" fill="{P["yellow_edge"]}"/>')
        cup = cr_path([(-4.5, -19), (4.5, -19), (13, -29), (18.5, -41), (17, -50), (9, -45.5), (0, -49),
                       (-9, -45.5), (-17, -50), (-18.5, -41), (-13, -29)], closed=True, sharp={0, 1, 5, 7})
        cc = uid("fc")
        g.append(f'<clipPath id="{cc}"><path d="{cup}"/></clipPath><path d="{cup}" fill="{P["mustard"]}"/>')
        g.append(f'<g clip-path="url(#{cc})"><path d="M5 -60 Q9 -38 4 -18 L24 -18 L24 -60Z" fill="{MUST_SH}"/></g>')
    g.append("</g>")
    return "".join(g)


# ------------------------------------------------------------------ build
def build():
    reset_ids()
    back, front = pot(kind="bowl", cx=300, rim_y=600, bottom=752, rx=126, rim_h=28, base_w=88, band=True)
    D, F, M, S, Lt, Pa = P["deep"], P["forest"], P["mid"], P["sage"], P["light"], P["pale"]

    # base pad, rooted below the rim
    p0 = Pad(292, 672, -4, 228, 168, M, asym=0.04, seed=1)
    # tier 2: left pad leans out, right pad more upright (no mirror symmetry)
    a3 = p0.top(4, 14)
    p3 = Pad(a3[0], a3[1], 6, 196, 150, F, sx=0.3, seed=3)            # edge-on, centre-back
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
    body += [p.svg() for p in pads]
    fa = e2.top(8, 3)
    body.append(flower(fa[0], fa[1], -6, 1.3))
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
