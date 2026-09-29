"""Shared geometry + drawing helpers for the v4 botanical set.

Everything outputs plain SVG paths (flat fills, no gradients / filters) so the
art stays print-friendly and editable.
"""
import math

PAL = {
    "deep": "#314B37", "forest": "#405D43", "mid": "#5B7458", "sage": "#7F9273",
    "light": "#A5B296", "pale": "#C9D2BC", "terra": "#B96E4A", "terra2": "#CB825D",
    "terra_dark": "#92543D", "soil": "#5C4331", "mustard": "#C49A41",
    "cream": "#F5EDDD", "burgundy": "#74464D", "blush": "#D79C9A",
    "yellow_edge": "#BFAE54", "spot": "#E8E2D1", "red": "#B95850",
    # small extensions of the palette (same temperature / saturation family)
    "night": "#27392C", "terra_hi": "#D89A76", "wine": "#5E3A40",
    "plum": "#8A5560", "rose": "#B97479", "ivory": "#FBF6EA", "sky": "#6F8A96",
    "amber": "#D48A4C",
}
SHADE = {  # flat "turned-away half" tone for each leaf tone
    "#C9D2BC": "#A5B296", "#A5B296": "#8E9E80", "#7F9273": "#6A7E60",
    "#5B7458": "#4B6349", "#405D43": "#34503A", "#314B37": "#27392C",
}

_ids = [0]


def uid(p="c"):
    _ids[0] += 1
    return f"{p}{_ids[0]}"


def reset_ids():
    _ids[0] = 0


def f(v):
    s = f"{v:.1f}"
    if s.endswith(".0"):
        s = s[:-2]
    return "0" if s == "-0" else s


# ---------------------------------------------------------------- splines
def cr_path(pts, closed=True, sharp=(), k=1.0):
    """Catmull-Rom through pts -> cubic bezier path. `sharp` = indices that
    get zero-length handles (corners)."""
    n = len(pts)
    sharp = set(sharp)
    d = [f"M{f(pts[0][0])} {f(pts[0][1])}"]
    segs = n if closed else n - 1
    for i in range(segs):
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p0 = pts[(i - 1) % n] if (closed or i > 0) else p1
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        if i in sharp:
            c1 = p1
        else:
            c1 = (p1[0] + (p2[0] - p0[0]) / 6 * k, p1[1] + (p2[1] - p0[1]) / 6 * k)
        if ((i + 1) % n) in sharp:
            c2 = p2
        else:
            c2 = (p2[0] - (p3[0] - p1[0]) / 6 * k, p2[1] - (p3[1] - p1[1]) / 6 * k)
        d.append(f"C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}")
    if closed:
        d.append("Z")
    return "".join(d)


def cr_sample(pts, per=8):
    """Densely sample an open Catmull-Rom spline."""
    out = []
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else p2
        for s in range(per):
            t = s / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(
                0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                       + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def open_path(pts):
    return cr_path(pts, closed=False)


# ---------------------------------------------------------------- stems
def ribbon(pts, w0, w1, per=6):
    """Tapered filled stroke through pts (w0 at start, w1 at end)."""
    s = cr_sample(pts, per)
    n = len(s)
    L, R = [], []
    for i, p in enumerate(s):
        a = s[max(i - 1, 0)]
        b = s[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy / m, dx / m
        w = (w0 + (w1 - w0) * (i / (n - 1))) / 2
        L.append((p[0] + nx * w, p[1] + ny * w))
        R.append((p[0] - nx * w, p[1] - ny * w))
    step = max(1, per // 2)
    Ls = L[::step] + ([L[-1]] if (n - 1) % step else [])
    Rs = R[::step] + ([R[-1]] if (n - 1) % step else [])
    ring = Ls + Rs[::-1]
    return cr_path(ring, closed=True, sharp={0, len(ring) - 1})


def stem(pts, w0, w1, color, extra=""):
    return f'<path d="{ribbon(pts, w0, w1)}" fill="{color}"{extra}/>'


def line(pts, width, color, opacity=None, cap="round"):
    op = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<path d="{open_path(pts)}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="{cap}" stroke-linejoin="round"{op}/>')


# ---------------------------------------------------------------- leaves
class Leaf:
    """A leaf in local coords: petiole attachment at (0,0), tip at ~(0,-L).
    right/left: lists of (t, w) nodes from base to tip, w as fraction of L
    (positive numbers; the left side is mirrored automatically)."""

    def __init__(self, L, right, left=None, bend=0.0, tip_sharp=True, base_sharp=True,
                 cordate=False, tip_t=1.0):
        self.L, self.bend = L, bend
        self.right = right
        self.left = left if left is not None else right
        self.tip_sharp, self.base_sharp, self.cordate = tip_sharp, base_sharp, cordate
        self.tip_t = tip_t

    def axis(self, t):
        L = self.L
        return (self.bend * L * t * t, -L * t)

    def normal(self, t):
        L = self.L
        tx, ty = 2 * self.bend * L * t, -L
        m = math.hypot(tx, ty)
        return (-ty / m, tx / m)  # points to the right when unbent

    def pt(self, t, w):
        a = self.axis(t)
        n = self.normal(t)
        return (a[0] + n[0] * w * self.L, a[1] + n[1] * w * self.L)

    def width(self, t, side="r"):
        nodes = [nw for nw in (self.right if side == "r" else self.left) if nw[0] >= 0]
        nodes = sorted(nodes)
        if t <= nodes[0][0]:
            return nodes[0][1]
        for (t0, w0), (t1, w1) in zip(nodes, nodes[1:]):
            if t0 <= t <= t1:
                u = (t - t0) / (t1 - t0 or 1)
                return w0 + (w1 - w0) * u
        return 0.0

    def side_pts(self, side):
        sgn = 1 if side == "r" else -1
        nodes = self.right if side == "r" else self.left
        return [self.pt(t, sgn * w) for t, w in nodes]

    def outline(self):
        R = self.side_pts("r")
        Lf = self.side_pts("l")
        tip = self.axis(self.tip_t)
        pts = []
        sharp = set()
        if not self.cordate:
            pts.append(self.axis(0))
            if self.base_sharp:
                sharp.add(0)
        else:
            pts.append(self.axis(self.right[0][0]))  # sinus
            sharp.add(0)
            R, Lf = R[1:], Lf[1:]
        pts += R
        sharp_tip = len(pts)
        pts.append(tip)
        if self.tip_sharp:
            sharp.add(sharp_tip)
        pts += Lf[::-1]
        return pts, sharp

    def path(self):
        pts, sharp = self.outline()
        return cr_path(pts, closed=True, sharp=sharp)

    def half_region(self, side="r", reach=3.0):
        """Big polygon covering one side of the midrib (to be clipped)."""
        sgn = 1 if side == "r" else -1
        ts = [-0.3 + i * 0.1 for i in range(16)]
        mid = [self.axis(t) for t in ts]
        far = [self.pt(t, sgn * reach) for t in ts]
        pts = mid + far[::-1]
        return cr_path(pts, closed=True, sharp={0, len(mid) - 1, len(mid), len(pts) - 1})


def leaf_g(leaf, fill, shade=None, side="r", midrib=None, veins=None, extra=None,
           under=None, clip_extra=True, transform=None, d=None, evenodd=False):
    """Render a Leaf. midrib: (color, width, opacity, t0, t1). veins: (color, width,
    opacity, [t...], reach, dt). extra(leaf) -> svg inside the leaf clip."""
    d = d or leaf.path()
    cid = uid("lc")
    out = []
    tr = f' transform="{transform}"' if transform else ""
    out.append(f"<g{tr}>")
    if under:
        out.append(under)
    eo = ' clip-rule="evenodd"' if evenodd else ""
    fr = ' fill-rule="evenodd"' if evenodd else ""
    out.append(f'<clipPath id="{cid}"><path d="{d}"{eo}/></clipPath>')
    out.append(f'<path d="{d}" fill="{fill}"{fr}/>')
    inner = []
    if shade:
        inner.append(f'<path d="{leaf.half_region(side)}" fill="{shade}"/>')
    if extra:
        inner.append(extra(leaf))
    if veins:
        col, w, op, ts, reach, dt = veins
        vv = []
        for t in ts:
            for s in ("r", "l"):
                sg = 1 if s == "r" else -1
                t2 = min(t + dt, 0.98)
                p0 = leaf.axis(t)
                p1 = leaf.pt(t + dt * 0.45, sg * leaf.width(t + dt * 0.45, s) * reach * 0.55)
                p2 = leaf.pt(t2, sg * leaf.width(t2, s) * reach)
                vv.append(f"M{f(p0[0])} {f(p0[1])}Q{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])}")
        inner.append(f'<path d="{"".join(vv)}" fill="none" stroke="{col}" stroke-width="{w}" '
                     f'stroke-linecap="round" opacity="{op}"/>')
    if midrib:
        col, w, op, t0, t1 = midrib
        mp = [leaf.axis(t0 + (t1 - t0) * i / 6) for i in range(7)]
        inner.append(line(mp, w, col, op))
    if inner:
        out.append(f'<g clip-path="url(#{cid})">' + "".join(inner) + "</g>")
    out.append("</g>")
    return "".join(out)


def T(x, y, rot=0, s=1.0, sx=None):
    sx = s if sx is None else sx
    parts = [f"translate({f(x)} {f(y)})"]
    if rot:
        parts.append(f"rotate({f(rot)})")
    if sx != 1 or s != 1:
        parts.append(f"scale({f(sx)} {f(s)})" if sx != s else f"scale({s:g})")
    return " ".join(parts)


# ---------------------------------------------------------------- pots
def pot(kind="classic", cx=300, rim_y=584, bottom=752, rx=104, rim_h=32, base_w=74,
        band=False):
    """Returns (back, front) svg: back = rim lip + soil (draw before plant),
    front = rim band + body (draw after plant)."""
    P = PAL
    ry = rx * 0.15

    def mix(a, b, t):  # pre-blend: b laid over a at opacity t, as one opaque colour
        return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t):02X}" for i in (1, 3, 5))

    # every tone below is an opaque pre-blend of the old translucent overlays (same look, no transparency)
    body_sh = mix(P["terra"], P["terra_dark"], 0.30)          # body shade (terra_dark @ .30)
    top_band = mix(P["terra"], P["terra_dark"], 0.38)         # shadow under the rim (terra_dark @ .38)
    top_band_sh = mix(body_sh, P["terra_dark"], 0.38)         # ... where it crosses the body shade
    body_hi = mix(P["terra"], P["terra_hi"], 0.55)            # body highlight stroke (terra_hi @ .55)
    body_hi_band = mix(top_band, P["terra_hi"], 0.55)         # ... where it crosses the rim shadow
    rim_sh = mix(P["terra2"], P["terra"], 0.55)               # rim shade (terra @ .55)
    rim_arc = mix(P["terra2"], P["terra_hi"], 0.75)           # rim top highlight (terra_hi @ .75)
    rim_arc_sh = mix(rim_sh, P["terra_hi"], 0.75)             # ... over the rim shade
    rim_hi = mix(P["terra2"], P["terra_hi"], 0.60)            # rim vertical glint (terra_hi @ .60)
    soil_line = mix(P["soil"], "#4A3527", 0.70)               # soil edge (#4A3527 @ .70)
    # --- back: inner lip + soil
    back = (f'<ellipse cx="{f(cx)}" cy="{f(rim_y)}" rx="{f(rx)}" ry="{f(ry)}" fill="{P["terra_dark"]}"/>'
            f'<ellipse cx="{f(cx)}" cy="{f(rim_y + 2.5)}" rx="{f(rx - 8)}" ry="{f(ry - 3.2)}" fill="{P["soil"]}"/>'
            f'<path d="M{f(cx - rx + 14)} {f(rim_y + 1)} Q{f(cx)} {f(rim_y - ry * 0.55)} {f(cx + rx - 14)} {f(rim_y + 1)}" '
            f'fill="none" stroke="{soil_line}" stroke-width="3"/>')
    # --- rim band
    rb = rim_y + rim_h
    body_top_w = rx - 7
    if kind == "cylinder":
        bw = body_top_w - 4
    elif kind == "bowl":
        bw = base_w
    else:
        bw = base_w
    rim = (f"M{f(cx - rx)} {f(rim_y)} A{f(rx)} {f(ry)} 0 0 0 {f(cx + rx)} {f(rim_y)} "
           f"L{f(cx + rx - 1.5)} {f(rb - 5)} Q{f(cx + rx - 2)} {f(rb)} {f(cx + rx - 9)} {f(rb + 1)} "
           f"Q{f(cx)} {f(rb + ry + 3)} {f(cx - rx + 9)} {f(rb + 1)} Q{f(cx - rx + 2)} {f(rb)} {f(cx - rx + 1.5)} {f(rb - 5)}Z")
    # --- body
    by0 = rb - 2
    if kind == "bowl":
        body = (f"M{f(cx - body_top_w)} {f(by0)} C{f(cx - body_top_w + 2)} {f(bottom - 60)} {f(cx - bw - 20)} {f(bottom - 4)} "
                f"{f(cx - bw + 6)} {f(bottom - 1)} Q{f(cx)} {f(bottom + 7)} {f(cx + bw - 6)} {f(bottom - 1)} "
                f"C{f(cx + bw + 20)} {f(bottom - 4)} {f(cx + body_top_w - 2)} {f(bottom - 60)} {f(cx + body_top_w)} {f(by0)}Z")
    else:
        body = (f"M{f(cx - body_top_w)} {f(by0)} L{f(cx - bw - 4)} {f(bottom - 14)} "
                f"Q{f(cx - bw - 2)} {f(bottom - 1)} {f(cx - bw + 12)} {f(bottom)} Q{f(cx)} {f(bottom + 7)} {f(cx + bw - 12)} {f(bottom)} "
                f"Q{f(cx + bw + 2)} {f(bottom - 1)} {f(cx + bw + 4)} {f(bottom - 14)} L{f(cx + body_top_w)} {f(by0)}Z")
    bid = uid("pc")
    # right-hand shade and left highlight, clipped to the body
    shade = (f"M{f(cx + body_top_w * 0.52)} {f(by0)} Q{f(cx + bw * 0.62)} {f((by0 + bottom) / 2)} {f(cx + bw * 0.42)} {f(bottom + 10)} "
             f"L{f(cx + 200)} {f(bottom + 10)} L{f(cx + 200)} {f(by0)}Z")
    hi = (f"M{f(cx - body_top_w * 0.70)} {f(by0 + 14)} Q{f(cx - bw * 0.78)} {f((by0 + bottom) / 2)} {f(cx - bw * 0.62)} {f(bottom - 12)}")
    front = [
        # ground shadow: opaque pre-blend (deep over white paper @ ~18 %, L* 87.4) -- white card stock
        # prints an even tint only at L* <= ~90, so it sits with margin (<= 88) below the speckle band;
        # a touch smaller than the old 11 % translucent ellipse so the solid tone stays quiet
        f'<ellipse cx="{f(cx)}" cy="{f(bottom + 3)}" rx="{f(bw + 34)}" ry="8" fill="#D8DCD9"/>',
        f'<clipPath id="{bid}"><path d="{body}"/></clipPath>',
        f'<path d="{body}" fill="{P["terra"]}"/>',
        f'<g clip-path="url(#{bid})">',
        f'<path d="{shade}" fill="{body_sh}"/>',
    ]
    if band:
        # a subtle band round the body: an OPAQUE pre-blended line (terra_dark at ~40 % over the body colour,
        # and over the shaded side a step darker) 4 units wide, so it survives print_prep unchanged
        on_body = mix(P["terra"], P["terra_dark"], 0.40)
        on_shade = mix(mix(P["terra"], P["terra_dark"], 0.30), P["terra_dark"], 0.40)
        yb = by0 + (bottom - by0) * 0.55
        bd = f"M{f(cx - 200)} {f(yb)} Q{f(cx)} {f(yb + 16)} {f(cx + 200)} {f(yb)}"
        sid = uid("ps")
        front += [f'<path d="{bd}" fill="none" stroke="{on_body}" stroke-width="4"/>',
                  f'<clipPath id="{sid}"><path d="{shade}"/></clipPath>',
                  f'<path d="{bd}" fill="none" stroke="{on_shade}" stroke-width="4" clip-path="url(#{sid})"/>']
    tb = f"M{f(cx - 200)} {f(by0 - 6)} H{f(cx + 200)} V{f(by0 + 10)} Q{f(cx)} {f(by0 + 22)} {f(cx - 200)} {f(by0 + 10)}Z"
    tbid, shid = uid("pt"), uid("pt")
    front += [
        f'<clipPath id="{tbid}"><path d="{tb}"/></clipPath><clipPath id="{shid}"><path d="{shade}"/></clipPath>',
        f'<path d="{tb}" fill="{top_band}"/>',
        f'<path d="{tb}" fill="{top_band_sh}" clip-path="url(#{shid})"/>',
        f'<path d="{hi}" fill="none" stroke="{body_hi}" stroke-width="7" stroke-linecap="round"/>',
        f'<path d="{hi}" fill="none" stroke="{body_hi_band}" stroke-width="7" stroke-linecap="round" clip-path="url(#{tbid})"/>',
    ]
    front.append("</g>")
    rid, rsid = uid("rc"), uid("rs")
    rs = (f"M{f(cx + rx * 0.55)} {f(rim_y - 20)} Q{f(cx + rx * 0.62)} {f(rb)} {f(cx + rx * 0.5)} {f(rb + 30)} "
          f"L{f(cx + 200)} {f(rb + 30)} L{f(cx + 200)} {f(rim_y - 20)}Z")
    arc = f"M{f(cx - rx - 5)} {f(rim_y + 1)} A{f(rx + 5)} {f(ry + 1)} 0 0 0 {f(cx + rx + 5)} {f(rim_y + 1)}"
    front += [
        f'<clipPath id="{rsid}"><path d="{rs}"/></clipPath>',
        f'<clipPath id="{rid}"><path d="{rim}"/></clipPath>',
        f'<path d="{rim}" fill="{P["terra2"]}"/>',
        f'<g clip-path="url(#{rid})">',
        f'<path d="{rs}" fill="{rim_sh}"/>',
        # the vertical glint goes under the top highlight (their tiny overlap shows the arc tone)
        f'<path d="M{f(cx - rx * 0.78)} {f(rim_y + 12)} L{f(cx - rx * 0.80)} {f(rb - 4)}" stroke="{rim_hi}" stroke-width="6" stroke-linecap="round"/>',
        f'<path d="{arc}" fill="none" stroke="{rim_arc}" stroke-width="5"/>',
        f'<path d="{arc}" fill="none" stroke="{rim_arc_sh}" stroke-width="5" clip-path="url(#{rsid})"/>',
        "</g>",
    ]
    return back, "".join(front)


def svg_doc(body, title):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="600" height="800" viewBox="0 0 600 800">\n'
            f"<title>{title}</title>\n{body}\n</svg>\n")
