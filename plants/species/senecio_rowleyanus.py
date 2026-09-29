"""Senecio rowleyanus (string of pearls) -- v4.

Classic pot (set scale, bottom 752). The crown is a dome built from strands
that climb out of the soil and curl over along nested shells (back / tall /
dark -> front / low / light), so the mound reads as tangled strings of beads,
not a pile of grapes. The outer dome strands keep going over the rim and
trail down the sides; short shoots arch up just above the dome and flop
over; a few front strands spill over the front rim.

Every bead is one shared <use>: a pre-rotated symbol (round body + small
pointed tip + translucent window stripe, tip turned away from its stem and
leaning toward the growing end) with an un-rotated darker lower crescent, so
light always reads from above. Five tone sets give depth.

Run:  python3 species/senecio_rowleyanus.py  -> out/senecio_rowleyanus.svg
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, cr_sample, open_path, pot, svg_doc, f, reset_ids  # noqa: E402

P = PAL
CX = 300
RIM_Y = 588
BOTTOM = 752
RX = 100
R0 = 10.0      # bead symbol radius (scaled per bead)
NANG = 16      # pre-rotated symbol angles
SHOULDER = 0.85
RXF = 1.08
HT = 1.5       # crown height factor (dome shells' ry)
SHOOT_UP = 55  # young shoots lifted by this much with the taller dome

# tone sets: body, crescent, window, stem
TONES = {
    "d": (P["forest"], "#34503A", P["mid"], P["night"]),
    "b": (P["mid"], "#4B6349", P["sage"], P["deep"]),
    "m": (P["sage"], "#6A7E60", P["light"], P["forest"]),
    "f": (P["light"], "#8E9E80", P["pale"], P["forest"]),
    "p": (P["pale"], P["light"], P["spot"], P["mid"]),
}


# ------------------------------------------------------------------ bead defs
def _crescent_path(dx=-2.2, dy=-3.6, r=R0):
    """Circle(0,0,r) minus circle(dx,dy,r): a lower-right crescent."""
    d = math.hypot(dx, dy)
    mx, my = dx / 2, dy / 2
    h = math.sqrt(r * r - (d / 2) ** 2)
    ux, uy = -dy / d, dx / d
    p1 = (mx + ux * h, my + uy * h)
    p2 = (mx - ux * h, my - uy * h)
    return (f"M{p1[0]:.1f} {p1[1]:.1f}A{r:g} {r:g} 0 1 1 {p2[0]:.1f} {p2[1]:.1f}"
            f"A{r:g} {r:g} 0 0 0 {p1[0]:.1f} {p1[1]:.1f}Z")


def defs(used):
    """Shape defs + one symbol per (tone, angle) actually used."""
    a = math.radians(16)
    sx, sy = R0 * math.sin(a), -R0 * math.cos(a)
    body = (f"M{sx:.2f} {sy:.2f}A{R0:g} {R0:g} 0 1 1 {-sx:.2f} {sy:.2f}"
            f"Q-1 -11 0 -13.6Q1 -11 {sx:.2f} {sy:.2f}Z")
    window = "M1.2 5.6Q5.4 -0.8 1.4 -8.4Q3.2 -1 1.2 5.6Z"
    out = ["<defs>", f'<path id="bd" d="{body}"/>', f'<path id="bw" d="{window}"/>',
           f'<path id="bc" d="{_crescent_path()}"/>']
    for k in sorted({t for t, _ in used}):
        b, c, w, _ = TONES[k]
        out.append(f'<use id="C{k}" href="#bc" fill="{c}"/>')
        out.append(f'<g id="W{k}"><use href="#bd" fill="{b}"/><use href="#bw" fill="{w}" opacity=".7"/></g>')
    for k, i in sorted(used):
        out.append(f'<g id="{k}{i}"><use href="#W{k}" transform="rotate({i * 360 // NANG})"/>'
                   f'<use href="#C{k}"/></g>')
    out.append("</defs>")
    return "".join(out)


class Beads:
    """Collects bead placements; renders each as a single <use>."""

    def __init__(self):
        self.used = set()

    def one(self, x, y, r, ang, tone):
        i = int(round((ang % 360) / (360 / NANG))) % NANG
        self.used.add((tone, i))
        return f'<use href="#{tone}{i}" transform="translate({f(x)} {f(y)}) scale({r / R0:.2f})"/>'

    def many(self, beads):
        return "".join(self.one(*b) for b in beads)


# ------------------------------------------------------------------ strands
def _arclen(pts):
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    return acc


def _at(pts, acc, s):
    for i in range(1, len(acc)):
        if acc[i] >= s:
            u = (s - acc[i - 1]) / ((acc[i] - acc[i - 1]) or 1)
            a, b = pts[i - 1], pts[i]
            tx, ty = b[0] - a[0], b[1] - a[1]
            m = math.hypot(tx, ty) or 1
            return (a[0] + tx * u, a[1] + ty * u), (tx / m, ty / m)
    a, b = pts[-2], pts[-1]
    m = math.hypot(b[0] - a[0], b[1] - a[1]) or 1
    return b, ((b[0] - a[0]) / m, (b[1] - a[1]) / m)


def strand(ctrl, tone, seed, r0=9.4, r1=3.8, start=0.0, side0=1, lean=30, taper_from=0.0, gmin=1.8):
    """Thin stem through ctrl with beads alternating sides, shrinking toward
    the end (after `taper_from` of the length). Returns (stem_svg, beads)."""
    rnd = random.Random(seed)
    pts = cr_sample(ctrl, 12)
    acc = _arclen(pts)
    L = acc[-1]

    def rad(s):
        u = max(0.0, (min(1.0, s / L) - taper_from) / (1 - taper_from))
        return r0 + (r1 - r0) * (u ** 1.15)

    beads = []
    s, side = start, side0
    while True:
        u = min(1.0, s / L)
        r = rad(s) * rnd.uniform(0.94, 1.06)
        (px, py), (tx, ty) = _at(pts, acc, s)
        nx, ny = -ty * side, tx * side
        off = r * rnd.uniform(0.42, 0.6)
        bx, by = px + nx * off, py + ny * off
        la = math.radians(lean + rnd.uniform(-14, 14))
        dx = nx * math.cos(la) + tx * math.sin(la)
        dy = ny * math.cos(la) + ty * math.sin(la)
        beads.append((bx, by, r, math.degrees(math.atan2(dx, -dy)), tone))
        rn = rad(s + 2 * r)
        gap = gmin + rnd.uniform(0, 2.0) + 1.6 * u
        lat = (r + rn) * 0.5
        step = math.sqrt(max((r + rn + gap) ** 2 - lat ** 2, (r + rn) ** 2 * 0.3))
        if s + step > L:
            break
        s += step
        side = -side
    lx, ly = beads[-1][0], beads[-1][1]
    sp = [p for p, a in zip(pts, acc) if a < s] + [(lx, ly)]
    sp = sp[::4] + [sp[-1]]
    stem_svg = (f'<path d="{open_path(sp)}" fill="none" stroke="{TONES[tone][3]}" '
                f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>')
    return stem_svg, beads


# ------------------------------------------------------------------ layout
def shell_strand(x0, rx, ry, a0, a1, tail=None, jit=3.0, seed=0):
    """Crown strand: rises from (x0, soil) to the shell top near angle a0 and
    curls over along the ellipse (CX, RIM_Y) to angle a1 (deg from vertical,
    + = right). Optional tail points continue it (e.g. over the rim)."""
    rnd = random.Random(seed)
    pts = [(x0, RIM_Y + 2)]
    n = 5
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        sa, ca = math.sin(a), math.cos(a)
        # superellipse (exponent < 1): full, rounded shoulders instead of a pointed dome
        sx = math.copysign(abs(sa) ** SHOULDER, sa)
        cy = math.copysign(abs(ca) ** SHOULDER, ca)
        pts.append((CX + rx * sx + rnd.uniform(-jit, jit),
                    RIM_Y - ry * cy + rnd.uniform(-jit, jit)))
    if tail:
        pts += tail
    return pts


def build():
    reset_ids()
    B = Beads()
    back, front = pot(kind="classic", cx=CX, rim_y=RIM_Y, bottom=BOTTOM, rx=RX, rim_h=30,
                      base_w=70, band=True)

    # ---- crown shells: (x0, rx, ry, a0, a1, tone, tail)
    crown = [
        # back shell (tall, dark): defines the dome silhouette
        (CX - 6, 112, 150, -6, -84, "d",
         [(CX - 136, 612), (CX - 140, 646)]),
        (CX + 8, 118, 146, 4, 92, "d",
         [(CX + 128, 610), (CX + 136, 656), (CX + 128, 700), (CX + 134, 730)]),
        (CX - 2, 100, 162, 14, -30, "d", None),
        (CX + 4, 90, 158, -20, 34, "d", None),
        # back-mid shell, the outer ones spill over the rim sides and trail
        (CX - 14, 118, 104, -20, -96, "b",
         [(CX - 120, 606), (CX - 128, 652), (CX - 120, 696), (CX - 126, 728)]),
        (CX + 16, 120, 100, 18, 98, "b",
         [(CX + 118, 606), (CX + 114, 648), (CX + 120, 680)]),
        (CX + 2, 96, 126, -4, 44, "b", None),
        (CX - 4, 92, 122, 8, -52, "b", None),
        # mid shell
        (CX - 10, 104, 84, 4, -84, "m", None),
        (CX + 10, 100, 86, -6, 80, "m", None),
        (CX + 4, 80, 104, -28, 26, "m", None),
        # front shell (low, light) - front row sits on the rim
        (CX - 16, 96, 58, -6, -80, "f", None),
        (CX + 14, 94, 54, 10, 82, "f", None),
        (CX, 64, 64, 30, -24, "f", None),
    ]
    # ---- front strands spilling over the front rim and down the pot face
    drapes = [
        ([(CX - 62, 592), (CX - 84, 610), (CX - 96, 652), (CX - 88, 698), (CX - 96, 734)],
         "p", 41, 9.2, 3.8, 1),
        ([(CX - 18, 598), (CX - 26, 632), (CX - 18, 672), (CX - 30, 712)], "p", 42, 9.0, 4.8, -1),
        ([(CX + 24, 600), (CX + 32, 640), (CX + 22, 690), (CX + 30, 716), (CX + 24, 738)],
         "p", 43, 9.2, 3.8, 1),
        ([(CX + 70, 594), (CX + 88, 620), (CX + 90, 666)], "p", 44, 8.8, 5.4, -1),
    ]

    # ---- low carpet of strands lying on the soil (hides it; nothing floats)
    carpet_back = [
        ([(CX + 10, 579), (CX - 30, 574), (CX - 70, 576), (CX - 94, 584)], "b", 71, -1),
        ([(CX - 14, 578), (CX + 30, 573), (CX + 70, 575), (CX + 94, 584)], "b", 72, 1),
        ([(CX - 60, 586), (CX - 20, 584), (CX + 24, 586), (CX + 64, 585)], "b", 75, 1),
    ]
    carpet_front = [
        ([(CX + 6, 591), (CX - 34, 595), (CX - 70, 594), (CX - 100, 598)], "m", 73, 1),
        ([(CX - 8, 593), (CX + 36, 597), (CX + 72, 595), (CX + 100, 598)], "m", 74, -1),
    ]

    def lay(lst):
        res = []
        for c, t, sd, s0 in lst:
            st, bs = strand(c, t, sd, 9.6, 8.8, start=2, side0=s0, lean=40, gmin=-1.0)
            res += [st, B.many(bs)]
        return res

    body = [back]
    # ---- young shoots rising above the dome and flopping over (tips in air)
    shoots = [  # rise at most ~80 px above the dome, then flop over
        ([(CX - 30, 540), (CX - 52, 470), (CX - 74, 420), (CX - 104, 404), (CX - 126, 420),
          (CX - 134, 450)], "b", 81, 9.8, 7.0, 1),
        ([(CX - 4, 540), (CX - 10, 450), (CX - 4, 390), (CX + 18, 360), (CX + 48, 362),
          (CX + 64, 388)], "m", 82, 9.6, 7.2, -1),
        ([(CX + 36, 546), (CX + 60, 470), (CX + 92, 420), (CX + 126, 414), (CX + 146, 440)],
         "b", 83, 9.4, 7.0, 1),
        ([(CX - 16, 540), (CX - 26, 460), (CX - 30, 404), (CX - 46, 374), (CX - 70, 376),
          (CX - 82, 398)], "m", 84, 9.4, 7.2, -1),
    ]
    body += lay(carpet_back)
    for i, (x0, rx, ry, a0, a1, t, tail) in enumerate(crown):
        if i == 3:
            for c, t, sd, r0, r1, s0 in shoots:
                c = [c[0]] + [(x, y - SHOOT_UP * min(1, (c[0][1] - y) / 60)) for x, y in c[1:]]
                st, bs = strand(c, t, sd, r0, r1, start=40, side0=s0, lean=24, taper_from=0.5)
                body += [st, B.many(bs)]
        if i == len(crown) - 3:
            body += lay(carpet_front)
        pts = shell_strand(x0, rx * RXF, ry * HT, a0, a1, tail, seed=60 + i)
        st, bs = strand(pts, t, 100 + i, r0=9.8, r1=(4.0 if tail else 7.2),
                        start=14, side0=1 if i % 2 else -1, lean=26,
                        taper_from=(0.45 if tail else 0.0))
        body += [st, B.many(bs)]
    body.append(front)
    for c, t, sd, r0, r1, s0 in drapes:
        st, bs = strand(c, t, sd, r0, r1, start=6, side0=s0, lean=38)
        body += [st, B.many(bs)]
    return defs(B.used) + "\n" + "\n".join(body)


def main():
    svg = svg_doc(build(), "Senecio rowleyanus (string of pearls)")
    out = os.path.join(os.path.dirname(HERE), "out", "senecio_rowleyanus.svg")
    with open(out, "w") as fh:
        fh.write(svg)
    print(out, len(svg))


if __name__ == "__main__":
    main()
