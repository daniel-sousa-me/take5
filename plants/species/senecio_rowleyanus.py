"""Senecio (Curio) rowleyanus (string of pearls) -- v6.

Habit: a well-grown plant in a small pot. The strands pile into a soft,
rounded cushion that mounds up above the rim and bulges out past it, then
spill over the rim and hang down the pot sides and front at varied lengths.
A few slender flower stalks carry the plant's white "shaving-brush" heads
above the cushion. The pot is the same classic banded pot as the rest of
the set, just smaller, so the plant reads at the set's size on the card.

The cushion is built as a mound (a solid of revolution): every strand
follows the mound surface -- down a meridian from near the top, or round
part of it -- and, once past the widest point, falls straight down.
Depth is carried by tone, set by how far round the mound a strand lies:
  back  (deep)  - the far side: top silhouette, strands behind the pot
  mid   (mid)   - the sides of the mound and the side curtains
  front (light) - the near face and the strands draping over the front rim
Each bead is one shared <use>: a round body, an un-rotated darker
lower-right crescent and an opaque upper-left highlight (light from
above-left).

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
RIM_Y = 616
BOTTOM = 752
RX = 82
R0 = 10.0      # bead symbol radius (scaled per bead)
TIP_MIN = 6.8  # smallest bead radius: keeps the highlight dot print-safe

# mound: base centre, max half-width, height above the base, view tilt
MB = (300, 612)
MA = 144
MH = 172
TILT = 0.26
# profile of the mound, top -> widest point: (radius fraction, height fraction)
PROFILE = [(0.0, 1.0), (0.30, 0.975), (0.56, 0.90), (0.78, 0.76), (0.93, 0.58), (1.0, 0.40)]
LOW = [(0.95, 0.21), (0.76, 0.04)]   # underside of the bulge, into the rim
ULOW = 1 + len(LOW) / (len(PROFILE) - 1) - 0.02

# tone sets: body, crescent, highlight, stem
TONES = {
    "d": (P["deep"], P["night"], P["mid"], P["night"]),
    "m": (P["mid"], "#4B6349", P["light"], P["night"]),
    # front highlight: a pale green-cream a few L* below the ivory stock, so it prints as ink (a paper-white
    # dot would print as bare paper and make the mass read as foam)
    "f": (P["light"], "#8E9E80", "#E4E6D2", P["forest"]),
}
HL_MIN = 2.4    # highlight radius floor: 4.8-unit dot, above the 4.5-unit print minimum
HL_FRAC = 0.25  # highlight radius as a fraction of the bead radius (~1/4 of the diameter across)


def hl_geom(x, y, r):
    """Highlight disc (cx, cy, radius) of a bead at (x, y) of radius r."""
    return x - 0.33 * r, y - 0.31 * r, max(HL_MIN, HL_FRAC * r)


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
    cx2, cy2 = dx, dy
    b2 = math.atan2(outer[-1][1] - cy2, outer[-1][0] - cx2)
    e2 = math.atan2(outer[0][1] - cy2, outer[0][0] - cx2)
    if e2 > b2:
        e2 -= 2 * math.pi
    inner = [(cx2 + r * math.cos(b2 + (e2 - b2) * i / n), cy2 + r * math.sin(b2 + (e2 - b2) * i / n))
             for i in range(1, n)]
    return cr_path(outer + inner, closed=True, sharp={0, n})


RB = (6.8, 7.4, 8.0, 8.6, 9.2, 9.8, 10.4)   # bead radius buckets (one symbol each per tone)


def defs(used):
    """One bead symbol per tone: round body and lower-right crescent; a scaled
    copy per radius bucket, and a variant of each with the upper-left highlight
    (used only where the highlight is wholly visible)."""
    out = ["<defs>", f'<path id="bc" d="{_crescent_path()}"/>']
    for k in sorted(used):
        b, c, h, _ = TONES[k]
        out.append(f'<g id="{k}"><circle r="{R0:g}" fill="{b}"/><use href="#bc" fill="{c}"/></g>')
        for i, r in enumerate(RB):
            hx, hy, hr = hl_geom(0, 0, r)
            out.append(f'<use id="{k}{i}" href="#{k}" transform="scale({r / R0:.2f})"/>'
                       f'<g id="{k}{i}h"><use href="#{k}{i}"/>'
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


def strand(ctrl, tone, seed, r0=9.4, r1=TIP_MIN, taper_from=0.5, gmin=1.6, gvar=3.0, stem=True):
    """Stem through ctrl with beads alternating sides, shrinking toward the end
    (after `taper_from` of the length). Returns a list of paint ops:
    ("stem", svg, polyline, width) and ("bead", x, y, r, tone)."""
    r1 = max(r1, TIP_MIN)
    rnd = random.Random(seed)
    pts = cr_sample(ctrl, 12)
    acc = _arclen(pts)
    L = acc[-1]

    def rad(s):
        u = max(0.0, (min(1.0, s / L) - taper_from) / (1 - taper_from))
        return r0 + (r1 - r0) * (u ** 1.2)

    beads = []
    s, side = 0.0, rnd.choice((-1, 1))
    while True:
        u = min(1.0, s / L)
        r = rad(s) * rnd.uniform(0.9, 1.08)
        (px, py), (tx, ty) = _at(pts, acc, s)
        nx, ny = -ty * side, tx * side
        off = r * rnd.uniform(0.34, 0.52)
        beads.append((px + nx * off, py + ny * off, r))
        rn = rad(s + 2 * r)
        gap = gmin + rnd.uniform(0, gvar) + 2.0 * u + (rnd.uniform(3, 6) if rnd.random() < 0.15 else 0)
        lat = (r + rn) * 0.46
        step = math.sqrt(max((r + rn + gap) ** 2 - lat ** 2, (r + rn) ** 2 * 0.3))
        if s + step > L:
            break
        s += step
        side = -side
    out = []
    if stem:
        lx, ly = beads[-1][0], beads[-1][1]
        sp = [p for p, a in zip(pts, acc) if a < s] + [(lx, ly)]
        k = max(1, int(len(sp) * 22 / max(s, 1)))      # a node every ~22 units
        sp = sp[::k] + [sp[-1]]
        out.append(("stem", f'<path d="{open_path(sp)}" fill="none" stroke="{TONES[tone][3]}" '
                    f'stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>', sp, 3.0))
    for x, y, r in beads:
        # snap to what is drawn (integer position, bucket radius) so the visibility test is exact
        out.append(("bead", round(x), round(y), RB[bucket(r)], tone))
    return out


# ------------------------------------------------------------------ mound geometry
def prof(u):
    """(radius frac, height frac) at u in [0, 1] along the profile (top -> widest);
    u in (1, 1 + len(LOW)/5] continues round the underside of the bulge."""
    if u > 1:
        seg = [PROFILE[-1]] + LOW
        k = min((u - 1) * (len(PROFILE) - 1), len(LOW) - 1e-9)
        i = int(k)
        t = k - i
        (r0, h0), (r1, h1) = seg[i], seg[i + 1]
        return r0 + (r1 - r0) * t, h0 + (h1 - h0) * t
    k = u * (len(PROFILE) - 1)
    i = min(int(k), len(PROFILE) - 2)
    t = k - i
    (r0, h0), (r1, h1) = PROFILE[i], PROFILE[i + 1]
    return r0 + (r1 - r0) * t, h0 + (h1 - h0) * t


def proj(rf, hf, phi, lift=0.0):
    """Mound surface point -> canvas. phi: 90 = facing the viewer, 270 = far side."""
    a = math.radians(phi)
    # soft irregularity: a few broad lobes round the mound, and a crown that sits
    # a little higher on the left
    lobe = 1 + 0.045 * math.sin(3 * a + 0.7) + 0.03 * math.sin(5 * a + 2.1)
    rf *= 1 + (lobe - 1) * min(1.0, rf * 1.4)
    hf *= 1 - 0.05 * math.cos(a) * hf
    x = MA * rf * math.cos(a)
    z = MA * rf * math.sin(a)
    return (MB[0] + x, MB[1] - MH * hf + TILT * z - lift)


def meridian(phi, u0, drop_to=None, sway=5.0, seed=0, bend=0.0):
    """Down the mound from u0 to the widest point (drifting `bend` degrees round
    the mound on the way), then -- if drop_to -- hang straight down to y=drop_to."""
    pts = []
    n = 5
    for i in range(n + 1):
        u = u0 + (1 - u0) * i / n
        rf, hf = prof(u)
        pts.append(proj(rf, hf, phi + bend * i / n))
    if drop_to:
        rnd = random.Random(seed)
        x0, y0 = pts[-1]
        # tuck in a little under the bulge (the strand swings from the rim edge)
        a = math.radians(phi + bend)
        dx_in = -math.cos(a) * rnd.uniform(4, 12)
        y = y0
        k = 0
        ph = rnd.uniform(0, 6.28)
        while y < drop_to - 1:
            y = min(drop_to, y + 42)
            k += 1
            x = x0 + dx_in * min(1, k / 2) + sway * math.sin(ph + k * 1.1)
            pts.append((x, y))
    else:
        # no drop: carry on round the underside of the bulge into the rim
        for rf, hf in LOW:
            pts.append(proj(rf, hf, phi + bend))
    return pts


def contour(phi0, phi1, u, n=6, wobble=0.04, seed=0, drift=0.0):
    """Part-way round the mound at profile position u (drifting by `drift` along
    the profile, with a little wander)."""
    rnd = random.Random(seed)
    pts = []
    for i in range(n + 1):
        uu = min(ULOW, max(0.0, u + drift * (i / n - 0.5) + rnd.uniform(-wobble, wobble)))
        rf, hf = prof(uu)
        pts.append(proj(rf, hf, phi0 + (phi1 - phi0) * i / n))
    return pts


# ------------------------------------------------------------------ flowers
# white brush-like flower head: green involucre cup + a fan of white florets
# with dark anthers, drawn upright at the origin (cup base at 0,0)
def _flower_def():
    cup = cr_path([(-5.5, 0), (-7.2, -9), (-6.4, -15), (6.4, -15), (7.2, -9), (5.5, 0)],
                  closed=True, sharp={0, 2, 3, 5})
    # the white florets are the paper itself: no pale fan (it would print as a barely-there tint). A brush of
    # five pale filaments, each ending in a dark anther, reads as the flower on its own.
    tops = [(-12.5, -30), (-6.5, -36.5), (0.5, -39), (7, -36), (12.8, -29.5)]
    roots = [(-4.2, -15), (-2.2, -15), (0, -15), (2.2, -15), (4.2, -15)]
    fil = "".join(f"M{x0} {y0} L{x1 * 0.9:.1f} {y1 * 0.95 + 0.5:.1f}" for (x0, y0), (x1, y1) in zip(roots, tops))
    styles = (f'<path d="{fil}" fill="none" stroke="{P["pale"]}" stroke-width="3.2" stroke-linecap="round"/>')
    d = "".join(f'<circle cx="{x}" cy="{y}" r="2.4" fill="{P["wine"]}"/>' for x, y in tops)
    return (f'<g id="fl">{styles}{d}'
            f'<path d="{cup}" fill="{P["sage"]}"/>'
            f'<path d="M1.5 -14 L5.8 -14 L6.4 -9 L4.6 0 L1.5 0Z" fill="#6A7E60"/></g>')


FLOWER_DEF = _flower_def()


def flower_stalk(pts, tilt, s=1.0):
    st = (f'<path d="{open_path(pts)}" fill="none" stroke="{P["sage"]}" stroke-width="3.4" '
          f'stroke-linecap="round" stroke-linejoin="round"/>')
    x, y = pts[-1]
    return ("stem", st + f'<use href="#fl" transform="translate({f(x)} {f(y + 2)}) rotate({tilt}) scale({s})"/>',
            cr_sample(pts, 12), 3.4)


# ------------------------------------------------------------------ layout
def zof(pts_rf_phi):
    return sum(rf * math.sin(math.radians(ph)) for rf, ph in pts_rf_phi) / len(pts_rf_phi)


THIN_U, THIN_P = 0.72, 0.3
# (phi, start on the profile, drift round the mound in degrees, hang to y, seed)
ARCS = [(44, 0.16, 24, 690, 501), (80, 0.06, 18, 726, 502), (116, 0.10, -16, 700, 503),
        (150, 0.20, -26, 676, 504)]


def tone_z(z):
    return "d" if z < -0.2 else ("m" if z < 0.5 else "f")


def cushion_shadow():
    """Solid dark mass inside the cushion so gaps between strands read as the
    shaded interior, not as paper."""
    ring = ([(CX - RX + 4, RIM_Y + 4), proj(0.9, 0.2, 180)]
            + [proj(rf * 0.94, hf * 0.985, 180) for rf, hf in PROFILE[::-1]][:-1]
            + [proj(0, 0.975, 90)]
            + [proj(rf * 0.94, hf * 0.985, 0) for rf, hf in PROFILE][1:]
            + [proj(0.9, 0.2, 0), (CX + RX - 4, RIM_Y + 4), (CX, RIM_Y + 14)])
    return f'<path d="{cr_path(ring, closed=True)}" fill="{P["night"]}"/>'


def layout():
    """List of (z, svg) strand items (painter's order by z)."""
    rnd = random.Random(7)
    items = []
    seed = [100]

    def add(pts, z, tone=None, **kw):
        seed[0] += 1
        items.append((z, strand(pts, tone or tone_z(z), seed[0], **kw)))

    # 1. tangled cover: rows of short strands wandering round the mound level by
    #    level (each drifting a little up or down), overlapping at their ends
    u = 0.03
    k = 0
    thin = random.Random(31)     # separate stream: thinning leaves the rest of the layout as it was
    while u < ULOW - 0.05:
        rf = max(prof(u)[0], 0.12)
        near = u > 0.62                          # lower rows: only the near half shows
        c = rnd.uniform(-40, 0) if near else rnd.uniform(0, 360)
        end = c + (225 if near else 360)
        while c < end:
            span = min(rnd.uniform(34, 60) / rf, 150)
            a0, a1 = c, c + span
            dr = rnd.uniform(-0.14, 0.14)
            z = zof([(prof(u)[0], a0 + (a1 - a0) * t / 4) for t in range(5)])
            k += 1
            tone = tone_z(z)
            # upper, visible face of the dome: thinned out and held a step darker, so the few long strings
            # arcing over it (section 5) read as strings rather than one even field of pearls
            upper = u < THIN_U and z > -0.2
            if upper and thin.random() < THIN_P:
                c = a1 - rnd.uniform(-4, 16) / rf
                continue
            if tone == "f":
                tone = "m"
            add(contour(a0, a1, u, wobble=0.05, seed=k, drift=dr), z, tone, r0=rnd.uniform(9.0, 10.0),
                taper_from=0.95, stem=tone == "f", gmin=0.6, gvar=2.4)
            c = a1 - rnd.uniform(-4, 16) / rf
        u += rnd.uniform(0.07, 0.085)

    # 2. far side: meridians over the back, outer ones hanging behind the pot sides
    for phi in (194, 207, 221, 319, 333, 346):
        ph = phi + rnd.uniform(-5, 5)
        drop = rnd.uniform(676, 728)
        add(meridian(ph, rnd.uniform(0.3, 0.6), drop, seed=seed[0], bend=rnd.uniform(-10, 10)),
            -0.6, "d", r0=9.6, taper_from=0.7)

    # 3. side curtains (mid): spill over the side rims and hang at varied lengths
    for phi, drop in ((-8, 736), (6, 694), (20, 724), (32, 662), (148, 732), (160, 704), (174, 672), (188, 716)):
        ph = phi + rnd.uniform(-4, 4)
        add(meridian(ph, rnd.uniform(0.55, 0.8), drop, seed=seed[0], bend=rnd.uniform(-8, 8),
                     sway=rnd.uniform(3, 7)),
            0.05 if 0 < ph < 180 else -0.1, "m", r0=9.6, taper_from=0.6)

    # 4. front drapes (light): over the front rim and down the pot face
    for phi, u0, drop in ((62, 0.72, 706), (84, 0.8, 736), (104, 0.7, 668), (122, 0.78, 720)):
        ph = phi + rnd.uniform(-3, 3)
        add(meridian(ph, u0, drop, seed=seed[0], bend=rnd.uniform(-8, 8), sway=rnd.uniform(3, 6)),
            1.2, "f", r0=9.8, taper_from=0.4)

    # 5. a few long strings from the crown arcing down over the near face of the dome and on over the rim
    for phi, u0, bend, drop, sd in ARCS:
        add(meridian(phi, u0, drop, seed=sd, bend=bend, sway=4), 1.3, "f", r0=9.6, taper_from=0.55, gmin=1.2)
    return items


def build():
    reset_ids()
    back, front = pot(kind="classic", cx=CX, rim_y=RIM_Y, bottom=BOTTOM, rx=RX, rim_h=27,
                      base_w=57, band=True)
    items = layout()
    behind = sorted((it for it in items if it[0] < 0), key=lambda t: t[0])
    ahead = sorted((it for it in items if it[0] >= 0), key=lambda t: t[0])
    ops = [op for _, st in behind for op in st]
    # flower stalks rise from inside the mound; their bases are covered by the nearer strands
    mid_stalk = [(318, 500), (320, 460), (326, 410), (338, 350), (350, 318)]
    fork = min(cr_sample(mid_stalk, 12), key=lambda q: abs(q[1] - 394))
    ops += [
        flower_stalk([(290, 502), (286, 470), (282, 420), (270, 372), (252, 334)], -14, 1.4),
        flower_stalk([fork, (318, 368), (306, 352)], -28, 1.05),   # side head off the middle stalk
        flower_stalk(mid_stalk, 10, 1.45),
        flower_stalk([(350, 506), (356, 480), (374, 440), (396, 404), (414, 386)], 26, 1.3),
    ]
    ops.append(("pot", front))
    ops += [op for _, st in ahead for op in st]
    body = [back, cushion_shadow()]
    hl = visible_highlights(ops)
    for i, op in enumerate(ops):
        if op[0] == "bead":
            body.append(bead(*op[1:], hl=i in hl))
        else:
            body.append(op[1])
    return defs({"d", "m", "f"}) + "\n" + "\n".join(body)


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
    """Indices of beads whose highlight disc is not overlapped by anything painted
    after the bead (later beads, stems, flower stalks, the pot front). Highlights of
    partly hidden beads are left off, so there are no thin pale crescents."""
    ring = [(math.cos(2 * math.pi * k / 16), math.sin(2 * math.pi * k / 16)) for k in range(16)]
    keep = set()
    for i, op in enumerate(ops):
        if op[0] != "bead":
            continue
        hx, hy, hr = hl_geom(op[1], op[2], op[3])
        hr += 0.8                                      # a little clearance: no hairline slivers either
        pts = [(hx, hy)] + [(hx + hr * c, hy + hr * s) for c, s in ring]
        ok = True
        for o in ops[i + 1:]:
            if o[0] == "bead":
                x, y, r = o[1], o[2], o[3]
                if math.hypot(x - hx, y - hy) < r + hr:
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
