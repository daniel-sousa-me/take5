"""Senecio (Curio) rowleyanus (string of pearls) -- v7.

Habit: a small pot with a LOW, lumpy cushion of strands sitting in it (the
front arc of the rim stays visible), and most of the plant's weight in the
strings that spill over the rim and hang down the pot sides and front at
varied lengths. A few slender flower stalks carry the white "shaving-brush"
heads above the cushion (as the set's echeveria carries its flowers).

The pot is the set's classic banded pot drawn SMALLER than usual in the
master (rx 64): deck.py scales this plant up more than the others
(PLANT_CLAMP_MAX), so its pot prints at the set's rim width while the whole
plant still prints at the set's height and area.

Pearl hierarchy (depth by tone, detail only in front):
  back   - the cushion's far side is one flat tonal shape (forest) whose
           scalloped top edge is made of pearl-sized bumps; strings hanging
           behind the pot sides are plain mid-tone beads
  middle - short strings combed over the cushion: mid-tone beads with a
           darker lower-right crescent, no highlight
  front  - the strings that run over the near face and spill over the rim:
           light beads, crescent, and an upper-left highlight dot (only where
           the dot is wholly visible)

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
RIM_Y = 645
BOTTOM = 752
RX = 64
RIM_H = 21
BASE_W = 45
R0 = 10.0       # bead symbol radius (scaled per bead)

# tone sets: body, crescent, highlight, stem
TONES = {
    "b": ("#4B6349", "#34503A", None, P["night"]),          # back strings (behind the pot), plain
    "m": (P["sage"], "#6A7E60", None, P["forest"]),        # middle strings on the cushion, plain
    "f": (P["light"], "#8E9E80", P["pale"], P["forest"]),  # front strings: pale highlight (L* ~83, white stock)
}
CUSHION = P["mid"]   # the cushion's far side: one flat mid-green shape (not the darkest green: keeps the mound light)
HL_R = 2.2      # highlight radius: a 4.4-unit dot (~0.36 mm printed), constant so every pearl reads the same way


def hl_geom(x, y, r):
    """Highlight disc (cx, cy, radius) of a bead at (x, y) of radius r."""
    return x - 0.36 * r, y - 0.34 * r, HL_R


# ------------------------------------------------------------------ bead defs
def _crescent_path(dx=-3.4, dy=-4.8, r=R0, n=10):
    """Circle(0,0,r) minus circle(dx,dy,r): a lower-right crescent, written with
    cubic segments (no arcs, so the print checker measures it correctly)."""
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    base = math.atan2(-uy, -ux)
    half = math.acos((d / 2) / r)
    outer = [(r * math.cos(base - half + 2 * half * i / n), r * math.sin(base - half + 2 * half * i / n))
             for i in range(n + 1)]
    b2 = math.atan2(outer[-1][1] - dy, outer[-1][0] - dx)
    e2 = math.atan2(outer[0][1] - dy, outer[0][0] - dx)
    if e2 > b2:
        e2 -= 2 * math.pi
    inner = [(dx + r * math.cos(b2 + (e2 - b2) * i / n), dy + r * math.sin(b2 + (e2 - b2) * i / n))
             for i in range(1, n)]
    return cr_path(outer + inner, closed=True, sharp={0, n})


RB = (5.6, 6.2, 6.8, 7.4, 8.0)   # bead radius buckets (one symbol each per tone)


def defs():
    out = ["<defs>", f'<path id="bc" d="{_crescent_path()}"/>']
    for k, (b, c, h, _) in TONES.items():
        out.append(f'<g id="{k}"><circle r="{R0:g}" fill="{b}"/><use href="#bc" fill="{c}"/></g>')
        for i, r in enumerate(RB):
            out.append(f'<use id="{k}{i}" href="#{k}" transform="scale({r / R0:.2f})"/>')
            if h:
                hx, hy, hr = hl_geom(0, 0, r)
                out.append(f'<g id="{k}{i}h"><use href="#{k}{i}"/>'
                           f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{hr:.1f}" fill="{h}"/></g>')
    out.append(FLOWER_DEF)
    out.append("</defs>")
    return "".join(out)


def bucket(r):
    return min(range(len(RB)), key=lambda j: abs(RB[j] - r))


def bead(x, y, r, tone, hl):
    return f'<use href="#{tone}{bucket(r)}{"h" if hl else ""}" x="{x:.0f}" y="{y:.0f}"/>'


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


def strand(ctrl, tone, seed, r0=7.6, r1=5.6, taper_from=0.5, gmin=2.0, gvar=3.0, stem=True, skip=0.0):
    """Stem through ctrl with beads alternating a little to either side, shrinking
    toward the tip (after `taper_from` of the length). Beads before arc length
    `skip` are left off (hidden in the cushion). Returns paint ops:
    ("stem", svg, polyline, width) and ("bead", x, y, r, tone)."""
    rnd = random.Random(seed)
    pts = cr_sample(ctrl, 12)
    acc = _arclen(pts)
    L = acc[-1]

    def rad(s):
        u = max(0.0, (min(1.0, s / L) - taper_from) / (1 - taper_from))
        return r0 + (r1 - r0) * (u ** 1.2)

    beads = []
    s, side = 0.0, rnd.choice((-1, 1))
    s_first = 0.0
    while True:
        r = rad(s) * rnd.uniform(0.93, 1.06)
        (px, py), (tx, ty) = _at(pts, acc, s)
        nx, ny = -ty * side, tx * side
        off = r * rnd.uniform(0.25, 0.45)
        if s >= skip:
            beads.append((px + nx * off, py + ny * off, r))
            s_first = s if len(beads) == 1 else s_first
        rn = rad(s + 2 * r)
        gap = gmin + rnd.uniform(0, gvar) + (rnd.uniform(3, 7) if rnd.random() < 0.18 else 0)
        lat = (r + rn) * 0.36
        step = math.sqrt(max((r + rn + gap) ** 2 - lat ** 2, (r + rn) ** 2 * 0.3))
        if s + step > L:
            break
        s += step
        side = -side
    out = []
    if stem and beads:
        lx, ly = beads[-1][0], beads[-1][1]
        sp = [p for p, a in zip(pts, acc) if s_first <= a < s] + [(lx, ly)]
        k = max(1, int(len(sp) * 20 / max(s - s_first, 1)))
        sp = sp[::k] + [sp[-1]]
        out.append(("stem", f'<path d="{open_path(sp)}" fill="none" stroke="{TONES[tone][3]}" '
                    f'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>', sp, 3.0))
    for x, y, r in beads:
        out.append(("bead", round(x), round(y), RB[bucket(r)], tone))
    return out


# ------------------------------------------------------------------ cushion
# uneven top edge of the cushion, left -> right (a lumpy, lopsided low mound: the
# crown sits right of centre, a dip left of it, a lower shoulder on the left)
TOP = [(212, 654), (210, 636), (218, 619), (233, 604), (250, 594), (268, 589), (283, 592),
       (297, 586), (311, 575), (325, 569), (339, 575), (351, 584), (364, 588), (376, 598),
       (386, 614), (392, 634), (389, 654)]


def cushion():
    """Far side of the cushion: one flat forest shape whose top edge is a row of
    pearl-sized bumps (the back strings, merged into one tone)."""
    pts = cr_sample(TOP, 10)
    acc = _arclen(pts)
    rnd = random.Random(5)
    bumps = []
    s = 4.0
    while s < acc[-1] - 4:
        (x, y), (tx, ty) = _at(pts, acc, s)
        r = rnd.uniform(6.6, 8.2)
        # centre just inside the edge (along the inward normal), so each bump shows as a pearl-round lump
        k = 0.4 * r
        bumps.append((x - ty * k, y + tx * k, r))
        s += r * rnd.uniform(1.35, 1.7)
    ring = TOP + [(366, 664), (CX, 672), (234, 664)]
    body = f'<path d="{cr_path(ring, closed=True, sharp={0, len(TOP) - 1})}" fill="{CUSHION}"/>'
    circ = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{CUSHION}"/>' for x, y, r in bumps)
    return body + circ


# ------------------------------------------------------------------ flowers
def _flower_def():
    cup = cr_path([(-5.5, 0), (-7.2, -9), (-6.4, -15), (6.4, -15), (7.2, -9), (5.5, 0)],
                  closed=True, sharp={0, 2, 3, 5})
    # the white florets are the paper itself; a brush of pale filaments, each ending in a dark anther
    tops = [(-12.5, -30), (-6.5, -36.5), (0.5, -39), (7, -36), (12.8, -29.5)]
    roots = [(-4.2, -15), (-2.2, -15), (0, -15), (2.2, -15), (4.2, -15)]
    fil = "".join(f"M{x0} {y0} L{x1 * 0.9:.1f} {y1 * 0.95 + 0.5:.1f}" for (x0, y0), (x1, y1) in zip(roots, tops))
    styles = f'<path d="{fil}" fill="none" stroke="{P["pale"]}" stroke-width="3.2" stroke-linecap="round"/>'
    d = "".join(f'<circle cx="{x}" cy="{y}" r="2.4" fill="{P["wine"]}"/>' for x, y in tops)
    return (f'<g id="fl">{styles}{d}'
            f'<path d="{cup}" fill="{P["sage"]}"/>'
            f'<path d="M1.5 -14 L5.8 -14 L6.4 -9 L4.6 0 L1.5 0Z" fill="#6A7E60"/></g>')


FLOWER_DEF = _flower_def()


def flower_stalk(pts, tilt, s=1.0):
    st = (f'<path d="{open_path(pts)}" fill="none" stroke="{P["sage"]}" stroke-width="3.2" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    x, y = pts[-1]
    return ("stem", st + f'<use href="#fl" transform="translate({f(x)} {f(y + 2)}) rotate({tilt}) scale({s})"/>',
            cr_sample(pts, 12), 3.2)


# ------------------------------------------------------------------ layout
def spill(side, out, tip, seed, curl=0.0):
    """Control points of a string that leaves the cushion's shoulder, arcs out over the
    side of the rim (the further out it lands, the higher it starts, like a fountain),
    and hangs down `out` units past the rim edge to y=tip; with `curl`, its tip then
    turns outward and up (the growing tips seek the light)."""
    rnd = random.Random(seed * 7 + out)
    x_out = CX + side * (RX + out)
    lift = out * 0.35
    pts = [(CX + side * (RX - 34), 624 - lift * 0.6 + rnd.uniform(-3, 3)),
           (CX + side * (RX - 8 + out * 0.2), 628 - lift),
           (CX + side * (RX + out * 0.7), 640 - lift * 0.5),
           (x_out, 664 + rnd.uniform(-3, 3))]
    y = pts[-1][1]
    sway = rnd.uniform(-5, 5)
    while y < tip - 1:
        y = min(tip, y + 26)
        pts.append((x_out + sway * math.sin((y - 664) / 30) - side * (y - 664) * 0.05, y))
    if curl:
        x, y = pts[-1]
        pts[-1] = (x + side * curl * 0.15, y)
        pts += [(x + side * curl * 0.55, y + 2), (x + side * curl, y - curl * 0.45)]
    return pts


def layout():
    """Paint ops: (hanging behind the cushion, on the cushion, in front of the pot)."""
    sd = [300]

    def S(pts, tone, **kw):
        sd[0] += 1
        return strand(pts, tone, sd[0], **kw)

    back, mid, ahead = [], [], []
    # 1. strings spilling over the side rims and hanging beside the pot, fanning out at varied lengths;
    #    neighbours alternate tone (mid / sage) so no two merge. Their roots are hidden under the cushion.
    # (side, out: how far past the rim edge the string swings, lowest y, tone, tip curl); drawn outermost
    # first so each nearer string lies over the one beyond it; only the outermost ones curl (outward)
    # The cascade is fuller on the left: the right side of the card has the number block beside the pot.
    for side, out, tip, tone, curl in ((-1, 112, 696, "b", 26), (-1, 94, 722, "m", 34), (-1, 74, 704, "b", 0),
                                       (-1, 56, 736, "m", 0), (-1, 38, 712, "b", 0), (-1, 20, 741, "m", 0),
                                       (-1, 3, 724, "b", 0),
                                       (1, 50, 708, "m", 0), (1, 34, 738, "b", 0), (1, 18, 716, "m", 0),
                                       (1, 4, 742, "b", 0)):
        back += S(spill(side, out, tip, sd[0], curl), tone, skip=20 + out * 0.3, gmin=1.2, gvar=2.4,
                  taper_from=0.7)
    # 2. flower stalks rise out of the cushion; their bases are covered by the strings on it
    mid += [
        flower_stalk([(298, 604), (292, 574), (280, 540), (262, 514), (244, 500)], -26, 1.2),
        flower_stalk([(320, 600), (324, 556), (330, 510), (338, 480), (346, 466)], 10, 1.3),
        flower_stalk([(344, 608), (362, 596), (388, 588), (414, 586)], 58, 1.0),
        flower_stalk([(330, 604), (344, 576), (366, 548), (392, 530)], 30, 1.05),
    ]
    # 3. short strings combed over the cushion from the crown (plain sage beads, some gaps)
    for pts in ([(318, 580), (300, 592), (284, 606), (268, 624), (262, 642)],
                [(328, 582), (344, 596), (354, 614), (358, 634)],
                [(292, 596), (272, 602), (254, 614), (244, 630)],
                [(336, 584), (320, 600), (314, 620), (316, 640)],
                [(302, 588), (298, 606), (290, 626), (286, 642)],
                [(350, 596), (366, 610), (372, 628)],
                [(262, 600), (244, 610), (230, 626), (226, 644)]):
        mid += S(pts, "m", r0=7.2, r1=6.4, taper_from=0.8, gmin=1.2, gvar=3.5, stem=False)
    # 4. front strings on the near face of the cushion (light, highlighted), ending at the rim
    mid += S([(310, 598), (294, 614), (280, 630), (272, 648)], "f", r0=7.6, r1=7.0, taper_from=0.9)
    mid += S([(348, 606), (336, 622), (332, 642)], "f", r0=7.6, r1=7.0, taper_from=0.9)
    # 5. front drapes: over the rim and down the pot face or just past its sides, varied lengths
    ahead += S([(262, 612), (240, 626), (224, 646), (218, 670), (220, 696), (216, 716)], "f", skip=6)
    ahead += S([(298, 608), (284, 628), (276, 652), (272, 678), (275, 704), (270, 728)], "f", skip=8)
    ahead += S([(330, 606), (340, 630), (342, 656), (338, 682), (340, 698)], "f", skip=8)
    ahead += S([(350, 610), (372, 624), (384, 644), (388, 668), (385, 692), (380, 708)], "f", skip=6)
    return back, mid, ahead


def build():
    reset_ids()
    back, front = pot(kind="classic", cx=CX, rim_y=RIM_Y, bottom=BOTTOM, rx=RX, rim_h=RIM_H,
                      base_w=BASE_W, band=True)
    hang, mid, ahead = layout()
    ops = hang + [("cushion", cushion())] + mid + [("pot", front)] + ahead
    hl = visible_highlights(ops)
    body = [back]
    for i, op in enumerate(ops):
        if op[0] == "bead":
            body.append(bead(*op[1:], hl=i in hl))
        else:
            body.append(op[1])
    return defs() + "\n" + "\n".join(body)


def _in_pot_front(x, y):
    """Inside the pot's front (rim band + body) silhouette, approximately (generous)."""
    dx = abs(x - CX)
    if dx > RX + 1.5:
        return False
    ry = RX * 0.15
    return y >= RIM_Y + ry * math.sqrt(max(0.0, 1 - (dx / RX) ** 2)) - 1.5


def _seg_dist(px, py, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / ((vx * vx + vy * vy) or 1)))
    return math.hypot(px - ax - vx * t, py - ay - vy * t)


def visible_highlights(ops):
    """Indices of front-tone beads whose highlight disc is not overlapped by anything
    painted after the bead, so there are no thin pale crescents."""
    ring = [(math.cos(2 * math.pi * k / 16), math.sin(2 * math.pi * k / 16)) for k in range(16)]
    keep = set()
    for i, op in enumerate(ops):
        if op[0] != "bead" or TONES[op[4]][2] is None:
            continue
        hx, hy, hr = hl_geom(op[1], op[2], op[3])
        hr += 0.8
        pts = [(hx, hy)] + [(hx + hr * c, hy + hr * s) for c, s in ring]
        ok = True
        for o in ops[i + 1:]:
            if o[0] == "bead":
                if math.hypot(o[1] - hx, o[2] - hy) < o[3] + hr:
                    ok = False
            elif o[0] == "stem":
                poly, w = o[2], o[3] / 2
                if any(_seg_dist(hx, hy, a, b) < hr + w for a, b in zip(poly, poly[1:])):
                    ok = False
            elif o[0] == "pot":
                if any(_in_pot_front(px, py) for px, py in pts):
                    ok = False
            if not ok:
                break
        if ok:
            keep.add(i)
    return keep


def main():
    svg = svg_doc(build(), "Senecio rowleyanus (string of pearls)")
    out = os.path.join(os.path.dirname(HERE), "out", "senecio_rowleyanus.svg")
    with open(out, "w") as fh:
        fh.write(svg)
    print(out, len(svg))


if __name__ == "__main__":
    main()
