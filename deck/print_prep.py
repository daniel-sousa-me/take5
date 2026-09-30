"""Print-prep pass for pigment inkjet (Canon GX5050) on 250 gsm uncoated card.

Makes a print copy of every master plant SVG (plants/out -> build/plants_print). Each plant is drawn at its
own scale on the card (deck.plant_scales(): the smallest it appears anywhere in the deck), so every size
below is the *printed* size in mm at that scale, following all transforms, including <use> instances.

Rules (docs/DESIGN_AND_PRINT_NOTES.md and the plant print policy):
  - Minimum stroke widths: dark-on-light lines >= MIN_POS mm, light (knockout) lines >= MIN_KO mm.
  - A stroke that is under its minimum is
      * DROPPED if it is translucent (effective opacity < 1: element, stroke-opacity and every ancestor
        group / <use> opacity multiplied together). Widening a see-through line only turns it into a pale
        wash with ghost caps; it is not widened.
      * WIDENED if it is opaque, by at most MAX_WIDEN (MAX_WIDEN_CLIPPED if every instance of it is drawn
        inside a clip-path, which keeps a widened vein inside its leaf). A line that needs more than that
        is DROPPED (a fattened hairline reads as a bar, and an unclipped one spills past its leaf).
    If the element is also filled, only its stroke is removed; the fill stays. An outline in the shape's own
    fill colour is not a line (it only grows the shape) and is left alone.
  - Filled dots and small shapes are never changed, only reported when they are under the dot minimums
    (dark >= MIN_DOT_POS, light >= MIN_DOT_KO): the plant author decides whether to enlarge or drop them.
  - Paper-white: the stock is WHITE card (STOCK = #FFFFFF). A fill / stroke / stop colour that is meant to look
    white but is drawn as a near-white (L* >= PAPER_MIN_L and chroma C* <= PAPER_MAX_C) cannot print as an even
    tint: pigment inkjet dithers such a light colour into a sparse speckle. It is set to pure white (#FFFFFF =
    no ink, the bare paper shows). This is informational, not a rule break: the master keeps its colour (it is
    right on screen) and the plant still reports "ok (unchanged)" for the line rules; the count is shown
    separately as "[paper-white: N]".
  - Speckle band: a pale, low-chroma colour with SPECKLE_MIN_L < L* < PAPER_MIN_L (88-95) and C* <= SPECKLE_MAX_C
    (25: creams and pale yellows too, not only near-neutrals) is too light to print as an even tint and not a
    white to send as bare paper. It is printed as drawn and reported per plant as a warning, "[speckle-band: N]"
    (-v lists the colours): the plant author should move it to L* <= 88 (a visible pale tint) or to #FFFFFF. Like paper-white it is a separate note, not part of "ok (unchanged)".
A master that follows the policy passes through unchanged. Everything widened or dropped is printed per plant.

Usage:  python deck/print_prep.py            # summary line per plant
        python deck/print_prep.py -v         # plus the details (colour, width, count) of every change
"""
import re, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from lxml import etree

SRC = str(paths.PLANTS_SRC)
OUT = str(paths.PLANTS_PRINT)
# Printed minimums (mm). The plant policy's unit figures (3.0 / 4.0 u lines, 3.5 / 4.5 u dots) are these at
# 0.050 mm/unit, the smallest scale any plant is drawn at.
MIN_POS, MIN_KO = 0.15, 0.20          # lines: dark on light / light on dark
MIN_DOT_POS, MIN_DOT_KO = 0.175, 0.225  # filled dots and slivers (by their widest point), report only
KO_LUM = 0.55                         # a stroke/fill lighter than this counts as a knockout (light-on-dark) mark
MAX_WIDEN, MAX_WIDEN_CLIPPED = 1.6, 2.0
STOCK = "#FFFFFF"                     # 250 gsm uncoated WHITE card; the face leaves it unprinted
PAPER_MAX_C = 15.0                    # chroma limit for paper-white (near-neutral whites / creams)
PAPER_MIN_L = 95.0                    # L* >= this (and C* <= PAPER_MAX_C) -> printed as bare paper (#FFFFFF, no ink)
SPECKLE_MIN_L = 88.0                  # SPECKLE_MIN_L < L* < PAPER_MIN_L (and C* <= SPECKLE_MAX_C) -> "speckle band":
SPECKLE_MAX_C = 25.0                  # sparse dither, warned about. Wider than paper-white (a pale cream / pale yellow
                                      # such as the anthurium spadix #EFE3BC, L* 90.3 C* 21, dithers just the same) and
                                      # from L* 88, a margin under the ~L* 90 where the printer starts to lay an even tint
TOL = 0.995                           # rounding slack: 0.1495 mm counts as 0.15
NS = "{http://www.w3.org/2000/svg}"
XLINK = "{http://www.w3.org/1999/xlink}href"
SHAPES = {NS + t for t in ("path", "circle", "ellipse", "rect", "line", "polyline", "polygon")}
SKIP = {NS + t for t in ("defs", "clipPath", "mask", "symbol", "title", "desc", "metadata", "style")}
INHERIT = ("stroke", "stroke-width", "stroke-opacity", "fill", "fill-opacity", "color")


def lum(hexc):
    hexc = (hexc or "").strip()
    if re.fullmatch(r"#[0-9A-Fa-f]{3}", hexc):
        hexc = "#" + "".join(c * 2 for c in hexc[1:])
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", hexc):
        return None
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def norm_hex(c):
    """'#abc' / '#aabbcc' / 'white' -> '#AABBCC', else None."""
    c = (c or "").strip()
    if c.lower() == "white":
        return "#FFFFFF"
    if re.fullmatch(r"#[0-9A-Fa-f]{3}", c):
        c = "#" + "".join(ch * 2 for ch in c[1:])
    return c.upper() if re.fullmatch(r"#[0-9A-Fa-f]{6}", c) else None


def lab(hexc):
    """CIE L*, a*, b*, C* (D65) of a hex colour, or None."""
    h = norm_hex(hexc)
    if h is None:
        return None
    lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5))
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    fn = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    L, a, bb = 116 * fn(Y) - 16, 500 * (fn(X) - fn(Y)), 200 * (fn(Y) - fn(Z))
    return L, a, bb, math.hypot(a, bb)


def paper_white(c):
    """True if colour c is a near-white (L* >= PAPER_MIN_L, near-neutral): it is printed as bare paper (no ink)."""
    v = lab(c)
    return v is not None and v[0] >= PAPER_MIN_L and v[3] <= PAPER_MAX_C


def speckle_band(c):
    """True if colour c is a pale, low-chroma tint in the speckle band (SPECKLE_MIN_L < L* < PAPER_MIN_L, C* <=
    SPECKLE_MAX_C) and not already paper-white: too light for an even tint on white stock. Printed as drawn, but
    warned about."""
    v = lab(c)
    return v is not None and SPECKLE_MIN_L < v[0] < PAPER_MIN_L and v[3] <= SPECKLE_MAX_C


PAPER_KEYS = ("fill", "stroke", "stop-color", "flood-color", "lighting-color", "color")


def paper_pass(root):
    """Set every paper-white colour (attribute or style) to #FFFFFF (no ink); leave speckle-band colours as drawn
    but count them. Returns ({colour: count} paper-white, {colour: count} speckle band)."""
    hits, band = {}, {}
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        for k in PAPER_KEYS:
            v = el.get(k)
            if v is not None and speckle_band(v):
                band[norm_hex(v)] = band.get(norm_hex(v), 0) + 1
            if v is not None and paper_white(v) and norm_hex(v) != "#FFFFFF":
                hits[norm_hex(v)] = hits.get(norm_hex(v), 0) + 1
                el.set(k, "#FFFFFF")
        st = el.get("style")
        if st:
            def sub(m):
                if speckle_band(m.group(2)):
                    band[norm_hex(m.group(2))] = band.get(norm_hex(m.group(2)), 0) + 1
                if paper_white(m.group(2)) and norm_hex(m.group(2)) != "#FFFFFF":
                    hits[norm_hex(m.group(2))] = hits.get(norm_hex(m.group(2)), 0) + 1
                    return m.group(1) + "#FFFFFF"
                return m.group(0)
            el.set("style", re.sub(r"((?:^|;)\s*(?:%s)\s*:\s*)([^;]+?)(?=\s*(?:;|$))" % "|".join(PAPER_KEYS), sub, st))
    return hits, band


def num(v, default=1.0):
    try:
        return float(re.sub(r"[a-z%]+$", "", str(v).strip()))
    except (TypeError, ValueError):
        return default


def tscale(tr):
    """Uniform scale (sqrt |det|) of a transform attribute."""
    s = 1.0
    for fn, args in re.findall(r"(\w+)\s*\(([^)]*)\)", tr or ""):
        a = [float(x) for x in re.split(r"[ ,]+", args.strip()) if x]
        if fn == "scale":
            s *= math.sqrt(abs(a[0] * (a[1] if len(a) > 1 else a[0])))
        elif fn == "matrix":
            s *= math.sqrt(abs(a[0] * a[3] - a[1] * a[2]))
    return s


def get(el, key):
    v = el.get(key)
    if v is None and el.get("style"):
        m = re.search(rf"(?:^|;)\s*{key}\s*:\s*([^;]+)", el.get("style"))
        v = m.group(1).strip() if m else None
    return v


def set_attr(el, key, val):
    el.set(key, val)
    if el.get("style"):
        el.set("style", re.sub(rf"(?:^|;)\s*{key}\s*:[^;]+", "", el.get("style")).strip(";"))


# ------------------------------------------------------------------ geometry for the dot/sliver report
def path_polys(d, steps=8):
    """Flatten an SVG path into polygons (list of point lists). Arcs are taken as straight chords."""
    toks = re.findall(r"[A-Za-z]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", d)
    polys, cur, pts = [], (0.0, 0.0), []
    start, cmd, i = (0.0, 0.0), None, 0
    counts = dict(M=2, L=2, H=1, V=1, C=6, S=4, Q=4, T=2, A=7, Z=0)
    last_ctrl = None
    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]; i += 1
            if cmd in "Zz":
                if pts:
                    polys.append(pts)
                pts, cur = [], start
                continue
        n = counts[cmd.upper()]
        a = [float(x) for x in toks[i:i + n]]; i += n
        if len(a) < n:
            break
        rel = cmd.islower()
        ox, oy = cur if rel else (0.0, 0.0)
        C = cmd.upper()
        if C == "M":
            if pts:
                polys.append(pts)
            cur = start = (a[0] + ox, a[1] + oy); pts = [cur]
            cmd = "l" if rel else "L"
        elif C == "L" or C == "T":
            cur = (a[0] + ox, a[1] + oy); pts.append(cur)
        elif C == "H":
            cur = (a[0] + (cur[0] if rel else 0), cur[1]); pts.append(cur)
        elif C == "V":
            cur = (cur[0], a[0] + (cur[1] if rel else 0)); pts.append(cur)
        elif C == "A":
            cur = (a[5] + ox, a[6] + oy); pts.append(cur)
        else:
            if C == "C":
                p1, p2, p3 = (a[0] + ox, a[1] + oy), (a[2] + ox, a[3] + oy), (a[4] + ox, a[5] + oy)
            elif C == "S":
                p1 = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_ctrl else cur
                p2, p3 = (a[0] + ox, a[1] + oy), (a[2] + ox, a[3] + oy)
            else:  # Q
                q, p3 = (a[0] + ox, a[1] + oy), (a[2] + ox, a[3] + oy)
                p1 = (cur[0] + 2 / 3 * (q[0] - cur[0]), cur[1] + 2 / 3 * (q[1] - cur[1]))
                p2 = (p3[0] + 2 / 3 * (q[0] - p3[0]), p3[1] + 2 / 3 * (q[1] - p3[1]))
            p0 = cur
            for k in range(1, steps + 1):
                t = k / steps; u = 1 - t
                pts.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
            last_ctrl = p2; cur = p3
            continue
        last_ctrl = None
    if pts:
        polys.append(pts)
    return polys


def shape_width(el):
    """Rough 'widest point' of a filled shape, in its own units: 4*area/perimeter (= the diameter of a circle,
    ~1.3x the widest point of a tapered sliver). None if it is not a closed filled shape we can measure."""
    t = el.tag[len(NS):]
    if t == "circle":
        return 2 * num(el.get("r"), 0)
    if t == "ellipse":
        return 2 * min(num(el.get("rx"), 0), num(el.get("ry"), 0))
    if t == "rect":
        return min(num(el.get("width"), 0), num(el.get("height"), 0))
    if t != "path" or not el.get("d"):
        return None
    A = P = 0.0
    for poly in path_polys(el.get("d")):
        if len(poly) < 3:
            continue
        a = sum(poly[k][0] * poly[k - 1][1] - poly[k - 1][0] * poly[k][1] for k in range(len(poly)))
        A += abs(a) / 2
        P += sum(math.dist(poly[k], poly[k - 1]) for k in range(len(poly)))
    return 4 * A / P if P else None


# ------------------------------------------------------------------ render walk
def instances(root):
    """Every rendered instance of every shape: {element: [ctx, ...]}, ctx = dict(scale, opacity, clipped,
    stroke, stroke-width, ...) with presentation attributes resolved by inheritance, <use> expanded."""
    ids = {e.get("id"): e for e in root.iter() if isinstance(e.tag, str) and e.get("id")}
    found = {}

    def walk(el, ctx, depth=0):
        if not isinstance(el.tag, str) or el.tag in SKIP or depth > 40:
            return
        c = dict(ctx)
        c["scale"] *= tscale(el.get("transform"))
        c["opacity"] *= num(get(el, "opacity"), 1.0)
        if get(el, "clip-path") not in (None, "none"):
            c["clipped"] = True
        for k in INHERIT:
            v = get(el, k)
            if v is not None and v != "inherit":
                c[k] = v
        if el.tag == NS + "use":
            ref = ids.get((el.get("href") or el.get(XLINK) or "")[1:])
            if ref is not None:
                walk(ref, c, depth + 1)
        elif el.tag in SHAPES:
            found.setdefault(el, []).append(c)
        else:
            for ch in el:
                walk(ch, c, depth + 1)

    walk(root, {"scale": 1.0, "opacity": 1.0, "clipped": False, "fill": "#000", "stroke": "none",
                "stroke-width": "1", "stroke-opacity": "1", "fill-opacity": "1", "color": "#000"})
    for ctxs in found.values():
        for c in ctxs:
            for k in ("fill", "stroke"):
                if c[k] == "currentColor":
                    c[k] = c["color"]
    return found


def process(fn, mm_per_unit, out_dir=OUT):
    """Write the print copy of one plant; return the report (Counters keyed by a short description)."""
    tree = etree.parse(fn)
    root = tree.getroot()
    rep = dict(widened={}, dropped={}, small={})

    def note(kind, key, mm):
        n, lo, hi = rep[kind].get(key, (0, 9e9, 0))
        rep[kind][key] = (n + 1, min(lo, mm), max(hi, mm))
    for el, ctxs in instances(root).items():
        s = min(c["scale"] for c in ctxs)
        c0 = min(ctxs, key=lambda c: c["scale"])
        # ---- stroke
        stroke = c0["stroke"]
        same = str(stroke).lower() == str(c0["fill"]).lower()   # outline in its own fill colour: grows the shape, not a line
        if stroke not in (None, "none", "transparent") and not same:
            wv = num(c0["stroke-width"], 1.0)
            eff = wv * s * mm_per_unit
            L = lum(stroke)
            need = MIN_KO if L is not None and L > KO_LUM else MIN_POS
            op = min(c["opacity"] * num(c["stroke-opacity"], 1.0) for c in ctxs)
            if eff < need * TOL and wv > 0:
                filled = c0["fill"] not in ("none", "transparent")
                factor = need / eff
                cap = MAX_WIDEN_CLIPPED if all(c["clipped"] for c in ctxs) else MAX_WIDEN
                if op < 0.999 or factor > cap:
                    why = f"translucent (opacity {op:.2f})" if op < 0.999 else f"opaque, needs > x{cap:g}"
                    note("dropped", f"stroke {stroke} {why}", eff)
                    if filled:
                        set_attr(el, "stroke", "none")
                    else:
                        el.getparent().remove(el)
                        continue
                else:
                    set_attr(el, "stroke-width", f"{need / (s * mm_per_unit):.2f}")
                    note("widened", f"stroke {stroke} {'clipped' if cap == MAX_WIDEN_CLIPPED else 'unclipped'}", eff)
        # ---- filled dots / slivers (report only)
        fill = c0["fill"]
        if fill not in ("none", "transparent") and (c0["stroke"] in (None, "none") or same):
            w = shape_width(el)
            if w is not None and same:
                w += num(c0["stroke-width"], 1.0)
            if w is not None:
                L = lum(fill)
                need = MIN_DOT_KO if L is not None and L > KO_LUM else MIN_DOT_POS
                eff = w * s * mm_per_unit
                if eff < need * TOL:
                    note("small", f"{el.tag[len(NS):]} {fill} ({'light' if need == MIN_DOT_KO else 'dark'})", eff)
    # paper-white pass last, so the line / dot rules above see the master's own colours
    rep["paper"], rep["speckle"] = paper_pass(root)
    os.makedirs(out_dir, exist_ok=True)
    tree.write(os.path.join(out_dir, os.path.basename(fn)), xml_declaration=False, encoding="utf-8")
    return rep


def summary(rep):
    """Line/dot rule result ("ok (unchanged)" when the master meets the policy), plus two separate notes: the
    paper-white count (informational: near-whites sent as bare paper) and the speckle-band count (a warning: pale
    tints between L* 88 and 95, C* <= 25, that the plant author should move to L* <= 88 or to #FFFFFF)."""
    n = {k: sum(x[0] for x in rep[k].values()) for k in ("widened", "dropped", "small")}
    s = "ok (unchanged)" if not any(n.values()) else \
        f"widened {n['widened']:3d} · dropped {n['dropped']:3d} · small dots/slivers {n['small']:3d}"
    p = sum(rep.get("paper", {}).values())
    b = sum(rep.get("speckle", {}).values())
    return s + (f"   [paper-white: {p}]" if p else "") + (f"   [speckle-band: {b}]" if b else "")


if __name__ == "__main__":
    import deck
    verbose = "-v" in sys.argv
    scales = deck.plant_scales()          # mm per plant-canvas unit, smallest use in the deck
    for f in sorted(os.listdir(SRC)):
        if f.endswith(".svg"):
            k = scales[f[:-4]]
            rep = process(os.path.join(SRC, f), k)
            print(f"{f[:-4]:24} {k:.4f} mm/u  {summary(rep)}")
            if verbose:
                for kind in ("widened", "dropped", "small"):
                    for d, (c, lo, hi) in sorted(rep[kind].items(), key=lambda x: -x[1][0]):
                        print(f"    {kind:8} {c:3d} × {d:52} {lo:.3f}–{hi:.3f} mm")
                for col, c in sorted(rep["paper"].items()):
                    L = lab(col)
                    print(f"    paper    {c:3d} × {col} (L* {L[0]:.1f}, C* {L[3]:.1f}) -> #FFFFFF, no ink")
                for col, c in sorted(rep["speckle"].items()):
                    L = lab(col)
                    print(f"    SPECKLE  {c:3d} × {col} (L* {L[0]:.1f}, C* {L[3]:.1f}) printed as drawn: "
                          f"move to L* <= {SPECKLE_MIN_L:g} or #FFFFFF")
    print(f"paper-white = near-white (L* >= {PAPER_MIN_L:g}, C* <= {PAPER_MAX_C:g}) on the white {STOCK} stock: printed "
          "as bare paper (#FFFFFF); informational, masters keep their colour")
    print(f"speckle-band = pale low-chroma tint ({SPECKLE_MIN_L:g} < L* < {PAPER_MIN_L:g}, C* <= {SPECKLE_MAX_C:g}): "
          f"prints as sparse speckle, not an even tint; WARNING, fix in the master (L* <= {SPECKLE_MIN_L:g} or #FFFFFF)")
