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
        r = rad(s) * rnd.uniform(0.9, 1.1)
        (px, py), (tx, ty) = _at(pts, acc, s)
        nx, ny = -ty * side, tx * side
        off = r * rnd.uniform(0.38, 0.55)
        bx, by = px + nx * off, py + ny * off
        la = math.radians(lean + rnd.uniform(-12, 12))
        dx = nx * math.cos(la) + tx * math.sin(la)
        dy = ny * math.cos(la) + ty * math.sin(la)
        beads.append((bx, by, r, math.degrees(math.atan2(dx, -dy)), tone))
        rn = rad(s + 2 * r)
        gap = gmin + rnd.uniform(0, 3.6) + 2.4 * u + (rnd.uniform(3, 7) if rnd.random() < 0.18 else 0)
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
# BACK: silhouette of the cushion; outer strands flop over the back rim (rising
# at most ~50 units above it) and hang behind / beside the pot sides (drawn
# before the pot front)
BACK = [
    # cushion back mounds (stay inside the cushion)
    ([(292, 588), (288, 558), (306, 538), (336, 534), (362, 546)], "d", 13, 9.8, 1),
    ([(310, 588), (304, 558), (282, 540), (252, 540), (230, 554)], "d", 14, 9.8, -1),
    ([(300, 588), (306, 554), (298, 534), (276, 528)], "d", 19, 9.6, 1),
    # flopping strands: a low arch, then a soft fall into a hanging curtain
    ([(282, 582), (246, 554), (204, 546), (170, 556), (152, 584), (146, 626), (150, 672),
      (146, 712), (150, 736)], "d", 11, 9.6, 1),
    ([(262, 580), (218, 552), (170, 548), (128, 562), (106, 590), (100, 634), (104, 674),
      (100, 700)], "d", 15, 9.4, -1),
    ([(318, 582), (356, 552), (396, 548), (428, 562), (446, 596), (450, 640), (446, 690),
      (450, 734)], "d", 12, 9.6, -1),
    ([(340, 580), (386, 554), (436, 556), (476, 574), (498, 602), (502, 634), (498, 660)],
     "d", 16, 9.4, 1),
]

# MID: the middle of the cushion; the outer ones spill over the side rims
MID_IN = [  # drawn before the pot front (stay inside the cushion)
    ([(300, 594), (292, 566), (266, 552), (236, 556), (216, 574)], "m", 21, 9.8, 1),
    ([(302, 594), (316, 564), (346, 552), (378, 558), (394, 576)], "m", 22, 9.8, -1),
    ([(286, 594), (300, 566), (326, 552), (346, 552)], "m", 23, 9.6, 1),
    ([(304, 584), (270, 576), (238, 578), (212, 588)], "m", 29, 9.6, 1),
    ([(298, 586), (332, 574), (366, 576), (392, 588)], "m", 30, 9.6, -1),
    # low fill so no soil shows between the cushion and the front row
    ([(236, 592), (262, 586), (290, 588), (318, 584), (346, 588), (372, 592)], "m", 33, 9.2, 1),
    ([(320, 578), (296, 566), (268, 566), (244, 574)], "m", 34, 9.2, -1),
    ([(280, 578), (306, 568), (334, 566), (360, 572)], "m", 35, 9.2, 1),
]
MID_OUT = [  # over the side rims: drawn after the pot front
    ([(262, 576), (226, 560), (200, 572), (186, 604), (180, 646), (184, 684), (180, 710)],
     "m", 25, 9.6, -1),
    ([(282, 568), (240, 550), (192, 552), (150, 568), (130, 596), (124, 640), (128, 684),
      (124, 726)], "m", 27, 9.4, -1),
    ([(340, 576), (376, 560), (402, 574), (414, 610), (418, 652), (414, 690), (418, 716)],
     "m", 26, 9.6, 1),
    ([(322, 566), (372, 550), (424, 556), (460, 578), (474, 610), (476, 652), (472, 684)],
     "m", 28, 9.4, 1),
]

# FRONT: the cushion's front row (resting on the rim) and strands draping
# over the front of the rim and down the pot face
FRONT_ROW = [
    ([(308, 600), (276, 594), (244, 592), (214, 596)], "f", 31, 9.8, 1),
    ([(294, 598), (326, 590), (358, 590), (388, 596)], "f", 32, 9.8, -1),
]
DRAPES = [
    ([(234, 590), (222, 616), (218, 650), (224, 686), (218, 718)], "f", 41, 9.6, 1),
    ([(266, 594), (258, 622), (262, 662), (256, 700), (260, 734)], "f", 42, 9.6, -1),
    ([(318, 596), (324, 622), (318, 650), (324, 676)], "f", 43, 9.6, 1),
    ([(352, 592), (362, 616), (358, 652), (364, 696), (358, 726)], "f", 44, 9.6, -1),
    ([(386, 590), (398, 612), (400, 642)], "f", 45, 9.4, 1),
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
