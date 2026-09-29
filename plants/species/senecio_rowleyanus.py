"""Senecio rowleyanus (string of pearls) -- v5.

Habit: a low cushion of pearls just above the rim, a few strands arching a
little up and over, and a long curtain of strands spilling over the rim and
hanging down both sides and the front of the pot at varied lengths. The
vertical rhythm comes from the hanging strands, not from an upright column.

Depth is carried by three clearly separated tone sets:
  back  (forest)  - cushion silhouette + strands hanging behind the pot sides
  mid   (sage)    - cushion middle + strands spilling over the side rims
  front (pale)    - cushion front row + strands draping over the front rim
Every bead is one shared <use>: a body (round, small pointed tip turned
along the strand), an un-rotated darker lower-right crescent and an opaque
upper-left highlight, so light always reads from above-left.

Run:  python3 species/senecio_rowleyanus.py  -> out/senecio_rowleyanus.svg
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, cr_path, cr_sample, open_path, pot, svg_doc, f, reset_ids  # noqa: E402

P = PAL
CX = 300
RIM_Y = 588
BOTTOM = 752
RX = 98
R0 = 10.0      # bead symbol radius (scaled per bead)
TIP_MIN = 6.8  # smallest bead radius: keeps the highlight dot print-safe

# tone sets: body, crescent, highlight, stem
TONES = {
    "d": (P["deep"], P["night"], P["mid"], P["night"]),
    "m": (P["mid"], "#4B6349", P["light"], P["night"]),
    "f": (P["light"], "#8E9E80", P["ivory"], P["forest"]),
}


# ------------------------------------------------------------------ bead defs
def _crescent_path(dx=-3.4, dy=-4.8, r=R0, n=10):
    """Circle(0,0,r) minus circle(dx,dy,r): a lower-right crescent, written with
    cubic segments (no arcs, so the print checker measures it correctly)."""
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    h = math.sqrt(r * r - (d / 2) ** 2)
    base = math.atan2(-uy, -ux)                    # direction of the crescent's middle
    half = math.acos((d / 2) / r)                  # half-angle to the cusps on the outer circle
    outer = [(r * math.cos(base - half + 2 * half * i / n), r * math.sin(base - half + 2 * half * i / n))
             for i in range(n + 1)]
    cx2, cy2 = dx, dy
    b2 = math.atan2(outer[-1][1] - cy2, outer[-1][0] - cx2)
    e2 = math.atan2(outer[0][1] - cy2, outer[0][0] - cx2)
    if e2 > b2:
        e2 -= 2 * math.pi
    inner = [(cx2 + r * math.cos(b2 + (e2 - b2) * i / n), cy2 + r * math.sin(b2 + (e2 - b2) * i / n))
             for i in range(1, n)]
    return cr_path(outer + inner, closed=True, sharp={0, n})


def defs(used):
    """One bead symbol per tone: round body, lower-right crescent, upper-left highlight."""
    out = ["<defs>", f'<path id="bc" d="{_crescent_path()}"/>']
    for k in sorted({t for t, _ in used}):
        b, c, h, _ = TONES[k]
        out.append(f'<g id="{k}"><circle r="{R0:g}" fill="{b}"/><use href="#bc" fill="{c}"/>'
                   f'<circle cx="-3.6" cy="-3.4" r="3.4" fill="{h}"/></g>')
    out.append("</defs>")
    return "".join(out)


class Beads:
    def __init__(self):
        self.used = set()

    def one(self, x, y, r, ang, tone):
        self.used.add((tone, 0))
        return f'<use href="#{tone}" transform="translate({f(x)} {f(y)}) scale({r / R0:.2f})"/>'

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


def strand(ctrl, tone, seed, r0=9.4, r1=TIP_MIN, start=0.0, side0=1, lean=30, taper_from=0.5,
           gmin=2.2):
    """Stem through ctrl with beads alternating sides, shrinking toward the end
    (after `taper_from` of the length). Returns (stem_svg, beads)."""
    r1 = max(r1, TIP_MIN)
    rnd = random.Random(seed)
    pts = cr_sample(ctrl, 12)
    acc = _arclen(pts)
    L = acc[-1]

    def rad(s):
        u = max(0.0, (min(1.0, s / L) - taper_from) / (1 - taper_from))
        return r0 + (r1 - r0) * (u ** 1.2)

    beads = []
    s, side = start, side0
    while True:
        u = min(1.0, s / L)
        r = rad(s) * rnd.uniform(0.95, 1.05)
        (px, py), (tx, ty) = _at(pts, acc, s)
        nx, ny = -ty * side, tx * side
        off = r * rnd.uniform(0.38, 0.55)
        bx, by = px + nx * off, py + ny * off
        la = math.radians(lean + rnd.uniform(-12, 12))
        dx = nx * math.cos(la) + tx * math.sin(la)
        dy = ny * math.cos(la) + ty * math.sin(la)
        beads.append((bx, by, r, math.degrees(math.atan2(dx, -dy)), tone))
        rn = rad(s + 2 * r)
        gap = gmin + rnd.uniform(0, 2.4) + 2.0 * u
        lat = (r + rn) * 0.48
        step = math.sqrt(max((r + rn + gap) ** 2 - lat ** 2, (r + rn) ** 2 * 0.3))
        if s + step > L:
            break
        s += step
        side = -side
    lx, ly = beads[-1][0], beads[-1][1]
    sp = [p for p, a in zip(pts, acc) if a < s] + [(lx, ly)]
    sp = sp[::4] + [sp[-1]]
    stem_svg = (f'<path d="{open_path(sp)}" fill="none" stroke="{TONES[tone][3]}" '
                f'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    return stem_svg, beads


def draw(B, items, **kw):
    out = []
    for c, t, sd, r0, s0 in items:
        st, bs = strand(c, t, sd, r0=r0, side0=s0, **kw)
        out += [st, B.many(bs)]
    return out


# ------------------------------------------------------------------ layout
# (control points, tone, seed, first bead radius, first side)
# BACK: silhouette of the cushion; outer strands arch over the back rim and
# hang behind / beside the pot sides (drawn before the pot front)
BACK = [
    ([(300, 590), (272, 522), (232, 494), (194, 500), (168, 530), (154, 580), (148, 630),
      (144, 680), (148, 722)], "d", 11, 9.6, 1),
    ([(304, 590), (330, 518), (370, 490), (408, 498), (432, 532), (446, 580), (452, 632),
      (448, 682), (452, 726)], "d", 12, 9.6, -1),
    ([(292, 588), (294, 512), (314, 476), (346, 468), (372, 482)], "d", 13, 9.8, 1),
    ([(310, 588), (302, 510), (280, 472), (250, 464), (226, 478)], "d", 14, 9.8, -1),
    # arching shoots: up a little, over, and down beside the pot
    ([(266, 580), (238, 488), (192, 442), (142, 446), (110, 484), (98, 538), (96, 598),
      (100, 648), (96, 690)], "d", 15, 9.4, 1),
    ([(336, 580), (366, 504), (408, 474), (450, 484), (478, 516), (494, 560), (498, 600),
      (494, 626)], "d", 16, 9.4, -1),
    ([(300, 588), (300, 500), (318, 452), (350, 440), (380, 452), (394, 480)], "d", 19, 9.4, 1),
]

# MID: the middle of the cushion; the outer ones spill over the side rims
MID_IN = [  # drawn before the pot front (stay inside the cushion)
    ([(300, 594), (294, 540), (266, 512), (230, 514), (208, 540)], "m", 21, 9.8, 1),
    ([(302, 594), (314, 538), (344, 512), (380, 518), (398, 546)], "m", 22, 9.8, -1),
    ([(284, 594), (298, 532), (326, 500), (354, 498)], "m", 23, 9.8, 1),
    ([(304, 582), (270, 572), (236, 574), (208, 584)], "m", 29, 9.6, 1),
    ([(298, 584), (332, 570), (366, 572), (394, 584)], "m", 30, 9.6, -1),
]
MID_OUT = [  # over the side rims: drawn after the pot front
    ([(262, 574), (230, 540), (200, 552), (186, 590), (182, 640), (188, 690), (182, 728)],
     "m", 25, 9.6, -1),
    ([(342, 574), (376, 540), (404, 556), (414, 596), (416, 640), (410, 680)], "m", 26, 9.6, 1),
    ([(282, 566), (236, 516), (184, 504), (144, 526), (126, 570), (122, 620), (126, 664),
      (122, 700)], "m", 27, 9.4, -1),
    ([(322, 562), (372, 512), (424, 506), (462, 534), (476, 580), (478, 634), (472, 690),
      (476, 724)], "m", 28, 9.4, 1),
]

# FRONT: the cushion's front row (resting on the rim) and strands draping
# over the front of the rim and down the pot face
FRONT_ROW = [
    ([(308, 600), (276, 594), (244, 592), (214, 596)], "f", 31, 9.8, 1),
    ([(294, 598), (326, 590), (358, 590), (388, 596)], "f", 32, 9.8, -1),
]
DRAPES = [
    ([(234, 590), (220, 616), (216, 648), (222, 684), (216, 714)], "f", 41, 9.6, 1),
    ([(266, 594), (258, 620), (262, 662), (256, 704), (260, 732)], "f", 42, 9.6, -1),
    ([(318, 596), (324, 620), (318, 648), (324, 672)], "f", 43, 9.6, 1),
    ([(352, 592), (362, 614), (358, 650), (364, 696), (358, 728)], "f", 44, 9.6, -1),
    ([(386, 590), (398, 610), (400, 640)], "f", 45, 9.4, 1),
]


def build():
    reset_ids()
    B = Beads()
    back, front = pot(kind="classic", cx=CX, rim_y=RIM_Y, bottom=BOTTOM, rx=RX, rim_h=30,
                      base_w=68, band=True)
    body = [back]
    body += draw(B, BACK, start=12, lean=28)
    body += draw(B, MID_IN, start=10, lean=28, taper_from=0.9)
    body.append(front)
    body += draw(B, MID_OUT, start=16, lean=30)
    body += draw(B, DRAPES, start=8, lean=34, taper_from=0.35)
    body += draw(B, FRONT_ROW, start=6, lean=30, taper_from=0.9)
    return defs(B.used) + "\n" + "\n".join(body)


def main():
    svg = svg_doc(build(), "Senecio rowleyanus (string of pearls)")
    out = os.path.join(os.path.dirname(HERE), "out", "senecio_rowleyanus.svg")
    with open(out, "w") as fh:
        fh.write(svg)
    print(out, len(svg))


if __name__ == "__main__":
    main()
