"""Take 5 botanical — card face + A4 print sheets (63.5x88 mm poker size, 1.5 mm bleed, 6 per A4: 2 cols x 3 rows, cards rotated 90 deg, inside Canon recommended print area)."""
import re, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

PLANTS = str(paths.PLANTS_PRINT)   # print-prepped plants (see print_prep.py)
PAPER_BG = None   # None = leave paper unprinted (use ivory/natural stock for the cream look); or e.g. "#F5EDDD"
FONT = str(paths.DM_SERIF)
paths.ensure_static_fonts()

TW, TH, B = 63.5, 88.0, 1.5          # trim size (poker), bleed
CW, CH = TW + 2 * B, TH + 2 * B       # printed card envelope 66.5 x 91 (card-local, portrait)
COLS, ROWS = 2, 3                     # cards turned 90 deg on a portrait A4: slot = CH wide x CW tall
PW, PH = 210.0, 297.0
# Canon GX5000-series A4: printable area 200 x 287 (5 mm all round); recommended area excludes
# 45.8 mm at the top and 36.8 mm at the bottom (feeding precision / quality "may be affected").
REC_TOP, REC_BOT = 45.8, PH - 36.8
MX = (PW - COLS * CH) / 2                              # 14.0
MY = (REC_TOP + REC_BOT) / 2 - ROWS * CW / 2           # 53.25 -> block 53.25..252.75, inside 45.8..260.2

C = dict(cream="#F5EDDD", deep="#314B37", forest="#405D43", burgundy="#74464D",
         terra_dark="#92543D", terra="#B96E4A", ink="#2B3F2F")

# ------------------------------------------------------------------ rules
def penalty(n):
    if n == 55: return 7
    if n % 11 == 0: return 5
    if n % 10 == 0: return 3
    if n % 5 == 0: return 2
    return 1

TIER = {  # (field tint, field accent, number colour, glyph colour)
    1: ("#E7E2C9", "#DFDBBF", C["deep"], "#8C6A4E"),
    2: ("#EEDFB6", "#E8D6A4", C["deep"], "#9A6A3A"),
    3: ("#EFD3BC", "#EAC7AC", C["deep"], C["terra_dark"]),
    5: ("#ECCBC6", "#E5BDB8", "#5E3A40", "#8A4A4E"),
    7: ("#E2BDBE", "#DAAEB0", "#5E3A40", "#74464D"),
}

SPECIES = sorted(f[:-4] for f in os.listdir(PLANTS) if f.endswith(".svg"))
SHOWY_55 = "strelitzia_reginae"
SHOWY_11 = ["anthurium_andraeanum", "spathiphyllum", "hoya_carnosa", "echeveria_elegans",
            "begonia_maculata", "oxalis_triangularis", "alocasia_amazonica", "opuntia_microdasys"]
ORDER = ["monstera_deliciosa", "chlorophytum_comosum", "ficus_lyrata", "aloe_vera", "calathea_ornata",
         "senecio_rowleyanus", "zamioculcas_zamiifolia", "crassula_ovata", "epipremnum_aureum",
         "dracaena_trifasciata", "pilea_peperomioides", "nephrolepis_exaltata", "ficus_elastica",
         "tradescantia_zebrina", "chamaedorea_elegans", "anthurium_andraeanum", "echeveria_elegans",
         "begonia_maculata", "alocasia_amazonica", "spathiphyllum", "opuntia_microdasys",
         "oxalis_triangularis", "hoya_carnosa", "strelitzia_reginae"]
assert sorted(ORDER) == SPECIES, set(SPECIES) ^ set(ORDER)


def assign():
    fixed = {55: SHOWY_55}
    for n in range(11, 105, 11):
        if n != 55:
            fixed[n] = SHOWY_11[n // 11 - 1 if n < 55 else n // 11 - 2]
    out, queue, k = {}, [], 0
    for n in range(1, 105):
        if n in fixed:
            out[n] = fixed[n]; continue
        bad = {out.get(n - 1), fixed.get(n + 1)}
        pick = next((q for q in queue if q not in bad), None)
        if pick:
            queue.remove(pick)
        else:
            while ORDER[k % len(ORDER)] in bad:
                queue.append(ORDER[k % len(ORDER)]); k += 1
            pick = ORDER[k % len(ORDER)]; k += 1
        out[n] = pick
    assert all(out[n] != out[n + 1] for n in range(1, 104))
    return out


# ------------------------------------------------------------------ number glyphs as paths
_font = TTFont(FONT)
_gs = _font.getGlyphSet()
_cmap = _font.getBestCmap()
UPM = _font["head"].unitsPerEm


def glyph(ch):
    g = _gs[_cmap[ord(ch)]]
    p = SVGPathPen(_gs); g.draw(p)
    return p.getCommands(), g.width


def number_path(n, size, cx, baseline, track=-0.02):
    """Centred number as a single path, `size` = font size in mm."""
    s = size / UPM
    items = [glyph(ch) for ch in str(n)]
    total = sum(w for _, w in items) + track * UPM * (len(items) - 1)
    x = cx / s - total / 2
    parts = []
    for d, w in items:
        parts.append(f'<path transform="translate({x:.2f} 0)" d="{d}"/>')
        x += w + track * UPM
    return (f'<g transform="translate(0 {baseline:.3f}) scale({s:.6f} {-s:.6f})">' + "".join(parts) + "</g>")


class PathFont:
    """Tiny text-to-path helper (advance widths + pair kerning from the 'kern'/GPOS-less tables ignored)."""
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm

    def width(self, text, size, track=0.0):
        w = sum(self.gs[self.cmap[ord(c)]].width for c in text)
        return (w + track * self.upm * (len(text) - 1)) * size / self.upm

    def path(self, text, size, x, baseline, track=0.0, anchor="middle"):
        s = size / self.upm
        w = self.width(text, size, track)
        x0 = x - (w / 2 if anchor == "middle" else 0)
        cur = x0 / s
        parts = []
        for c in text:
            g = self.gs[self.cmap[ord(c)]]
            if c != " ":
                p = SVGPathPen(self.gs); g.draw(p)
                parts.append(f'<path transform="translate({cur:.1f} 0)" d="{p.getCommands()}"/>')
            cur += g.width + track * self.upm
        return f'<g transform="translate(0 {baseline:.3f}) scale({s:.6f} {-s:.6f})">' + "".join(parts) + "</g>"


LABEL_FONT = PathFont(str(paths.FRAUNCES_MEDIUM))
LATIN_FONT = PathFont(str(paths.FRAUNCES_ITALIC))

NAMES = {  # common name, currently accepted botanical name
    "aloe_vera": ("Aloe", "Aloe vera"),
    "anthurium_andraeanum": ("Flamingo flower", "Anthurium andraeanum"),
    "begonia_maculata": ("Polka-dot begonia", "Begonia maculata"),
    "calathea_ornata": ("Pinstripe calathea", "Goeppertia ornata"),
    "dracaena_trifasciata": ("Snake plant", "Dracaena trifasciata"),
    "epipremnum_aureum": ("Golden pothos", "Epipremnum aureum"),
    "ficus_elastica": ("Rubber plant", "Ficus elastica"),
    "ficus_lyrata": ("Fiddle-leaf fig", "Ficus lyrata"),
    "monstera_deliciosa": ("Swiss cheese plant", "Monstera deliciosa"),
    "oxalis_triangularis": ("Purple shamrock", "Oxalis triangularis"),
    "pilea_peperomioides": ("Chinese money plant", "Pilea peperomioides"),
    "spathiphyllum": ("Peace lily", "Spathiphyllum wallisii"),
    "strelitzia_reginae": ("Bird of paradise", "Strelitzia reginae"),
    "zamioculcas_zamiifolia": ("ZZ plant", "Zamioculcas zamiifolia"),
    "alocasia_amazonica": ("African mask", "Alocasia × amazonica"),
    "chamaedorea_elegans": ("Parlour palm", "Chamaedorea elegans"),
    "chlorophytum_comosum": ("Spider plant", "Chlorophytum comosum"),
    "crassula_ovata": ("Jade plant", "Crassula ovata"),
    "echeveria_elegans": ("Mexican snowball", "Echeveria elegans"),
    "hoya_carnosa": ("Wax plant", "Hoya carnosa"),
    "nephrolepis_exaltata": ("Boston fern", "Nephrolepis exaltata"),
    "opuntia_microdasys": ("Bunny ears cactus", "Opuntia microdasys"),
    "senecio_rowleyanus": ("String of pearls", "Curio rowleyanus"),
    "tradescantia_zebrina": ("Inch plant", "Tradescantia zebrina"),
}


def name_label(species, cy, x_base, col_common, col_latin, rot=-90):
    """Vertical label centred on cy, first baseline at x_base (card-local).
    rot=-90 reads bottom-to-top (caps toward the left edge); rot=90 reads top-to-bottom (caps toward the right edge)."""
    common, latin = NAMES[species]
    g = (f'<g fill="{col_common}">' + LABEL_FONT.path(common, 3.0, 0, 0, track=0.02) + "</g>"
         f'<g fill="{col_latin}">' + LATIN_FONT.path(latin, 2.5, 0, 2.95) + "</g>")
    return f'<g transform="translate({x_base:.2f} {cy:.2f}) rotate({rot})">{g}</g>'


def numeral_height(size):
    bp = BoundsPen(_gs); _gs[_cmap[ord("8")]].draw(bp)
    return (bp.bounds[3]) * size / UPM


def needs_mark(n):
    rot = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    s = str(n)
    if any(c not in rot for c in s):
        return False
    r = "".join(rot[c] for c in reversed(s))
    return r != s and not r.startswith("0") and 1 <= int(r) <= 104

# ------------------------------------------------------------------ penalty glyph: wilted leaf
# drawn in a 10x10 box, origin top-left; stem arches over and the leaf hangs
WILT = ('<path d="M1.6 9.6 C1.2 6.6 1.9 3.6 3.9 2.2 C5.3 1.2 6.9 1.3 7.7 2.4" fill="none" stroke="{c}" '
        'stroke-width="1.0" stroke-linecap="round"/>'
        '<path d="M7.7 2.3 C9.6 3.4 10.2 5.9 9.5 7.9 C9.0 9.2 7.9 10.0 6.4 10.2 C5.4 9.0 5.0 7.0 5.5 5.3 '
        'C6.0 3.8 6.8 2.8 7.7 2.3Z" fill="{c}"/>'
        '<path d="M7.6 3.3 C7.6 5.3 7.3 7.4 6.7 9.3" fill="none" stroke="{hi}" stroke-width="0.55" '
        'stroke-linecap="round"/>')


def wilt_row(count, cx, y, size, col):
    gap = size * 0.22
    w = count * size + (count - 1) * gap
    x0 = cx - w / 2
    s = size / 10
    g = []
    for i in range(count):
        g.append(f'<g transform="translate({x0 + i * (size + gap):.3f} {y:.3f}) scale({s:.4f})">'
                 + WILT.format(c=col, hi="#FFFFFF" if PAPER_BG is None else PAPER_BG) + "</g>")
    return "".join(g)

# ------------------------------------------------------------------ plant embedding
_plant_cache = {}


def plant_inner(name):
    if name not in _plant_cache:
        s = open(f"{PLANTS}/{name}.svg").read()
        s = re.sub(r"<\?xml[^>]*>", "", s)
        body = s[s.index(">", s.index("<svg")) + 1: s.rindex("</svg>")]
        body = re.sub(r"<title>.*?</title>", "", body, flags=re.S)
        _plant_cache[name] = body
    return _plant_cache[name]


def uniq(body, tag):
    return re.sub(r'(id="|url\(#|href="#)([^"\)]+)', lambda m: f"{m.group(1)}{tag}{m.group(2)}", body)

# ------------------------------------------------------------------ card face
def field_blob(col, acc):
    """Organic colour field crossing the top-left corner (card-local coords incl. bleed)."""
    return (f'<path d="M-1 -1 H36 C33 6 27 9 20 11.5 C12 14.5 7 19 5 27 C4 31 2 34 -1 35 Z" fill="{col}"/>'
            f'<path d="M-1 22 C3 21 6 17.5 7.5 13 C9.5 7.5 14 4 21 2.5 C24 1.8 27 0.8 29 -1 H-1Z" fill="{acc}"/>')


def sprig(col):
    """Small open botanical ornament living inside the colour field (not following the trim)."""
    return (f'<g fill="none" stroke="{col}" stroke-width="0.45" stroke-linecap="round">'
            f'<path d="M4.2 24 C6.5 17 10.5 11 18 7.2"/></g>'
            f'<g fill="{col}">'
            f'<path d="M7.1 17.4 C5.2 16.6 4.6 14.6 5.2 13.4 C6.9 14.0 7.6 15.8 7.1 17.4Z"/>'
            f'<path d="M9.6 13.1 C10.0 11.2 11.9 10.2 13.2 10.5 C12.9 12.3 11.2 13.4 9.6 13.1Z"/>'
            f'<path d="M12.2 10.7 C11.0 9.0 11.6 7.1 12.6 6.4 C13.6 7.9 13.4 9.8 12.2 10.7Z"/>'
            f'<path d="M15.2 8.6 C15.9 6.9 17.8 6.3 19.0 6.8 C18.3 8.4 16.7 9.1 15.2 8.6Z"/>'
            f'</g>')


EDGE = 5.0          # clear space from the trim to any text / number ink (mm)
NUM_SIZE = 21.0     # numeral cap height ~13.6 mm
GLYPH = 4.0
PLANT_H = 36.0      # plant art height (mm)
FIELD_SCALE = 0.6   # corner colour field size


def number_ink(n, size):
    """(xmin, xmax) of the number's ink relative to its centring point (see number_path)."""
    s = size / UPM
    items = [(ch, glyph(ch)[1]) for ch in str(n)]
    track = -0.02 * UPM
    total = sum(w for _, w in items) + track * (len(items) - 1)
    x = -total / 2
    xmin, xmax = 1e9, -1e9
    for ch, w in items:
        bp = BoundsPen(_gs); _gs[_cmap[ord(ch)]].draw(bp)
        x0, _, x1, _ = bp.bounds
        xmin, xmax = min(xmin, x + x0), max(xmax, x + x1)
        x += w + track
    return xmin * s, xmax * s


PEN_STYLE = "quarter"   # "quarter" | "under" | "beside" | "rosette" | "corner"
CLUSTER = {1: [(0, 0)], 2: [(0, -0.5), (0, 0.5)], 3: [(0, -0.55), (0, 0.55), (0.95, 0)],
           5: [(0, -1), (1, -1), (0.5, 0), (0, 1), (1, 1)],
           7: [(0.5, -1), (1.5, -1), (0, 0), (1, 0), (2, 0), (0.5, 1), (1.5, 1)]}


def wilt_at(x, y, size, rot, col):
    """One penalty glyph centred on (x, y)."""
    hi = "#FFFFFF" if PAPER_BG is None else PAPER_BG
    return (f'<g transform="translate({x:.3f} {y:.3f}) rotate({rot:.1f}) scale({size / 10:.4f}) translate(-5.7 -6.1)">'
            + WILT.format(c=col, hi=hi) + "</g>")


def penalty_marks(style, p, gcol, left, top, nh, num_right, base_extra):
    out = []
    if style == "under":
        gy = top + nh + 1.9 + base_extra
        row_w = p * GLYPH + (p - 1) * GLYPH * 0.22
        out.append(wilt_row(p, left + row_w / 2 - GLYPH * 0.12, gy, GLYPH, gcol))
        return "".join(out), gy + GLYPH
    cy = top + nh / 2
    if style == "beside":
        gs = 4.6
        pitch = gs * 1.25
        x0 = num_right + 2.8 + gs / 2
        for u, v in CLUSTER[p]:
            out.append(wilt_at(x0 + u * pitch, cy + v * pitch, gs, 0, gcol))
    elif style == "rosette":
        gs = 4.6
        R = 0 if p == 1 else {2: 2.5, 3: 2.9, 5: 3.9, 7: 4.9}[p]
        cx = num_right + 2.8 + R + gs / 2
        for i in range(p):
            a = -90 + 360 * i / p
            x, y = cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))
            out.append(wilt_at(x, y, gs, a + 90 if p > 1 else 0, gcol))
    elif style == "corner":
        ox, oy = CW - B, B                      # trim corner, top-right
        R = 13.5
        span = {1: 0, 2: 22, 3: 36, 5: 56, 7: 66}[p]
        for i in range(p):
            t = 45 + (-span / 2 + span * i / max(p - 1, 1) if p > 1 else 0)
            x, y = ox - R * math.cos(math.radians(t)), oy + R * math.sin(math.radians(t))
            out.append(wilt_at(x, y, GLYPH, 45 - t, gcol))
    return "".join(out), top + nh + base_extra


ROWS_Q = {1: [1], 2: [2], 3: [3], 5: [3, 2], 7: [4, 3]}


def info_block(n, p, ncol, gcol):
    """Number + penalty marks in the top-left quadrant (card-local coords)."""
    top = B + EDGE
    nh = numeral_height(NUM_SIZE)
    base = top + nh
    xmin, xmax = number_ink(n, NUM_SIZE)
    if PEN_STYLE == "quarter":
        axis = B + TW / 4                                   # the 1/4 line of the trim
        cx = axis - (xmin + xmax) / 2                       # centre the ink (not the advance) on the axis
        if cx + xmin < B + EDGE:                            # 3-digit numbers: keep them off the edge
            cx = B + EDGE - xmin
    else:
        cx = B + EDGE - xmin
    mid = cx + (xmin + xmax) / 2
    out = [f'<g fill="{ncol}">' + number_path(n, NUM_SIZE, cx, base) + "</g>"]
    extra = 0.0
    if needs_mark(n):
        out.append(f'<rect x="{mid - 4:.2f}" y="{base + 1.0:.2f}" width="8" height="0.7" rx="0.35" fill="{ncol}"/>')
        extra = 1.2
    if PEN_STYLE != "quarter":
        marks, bottom = penalty_marks(PEN_STYLE, p, gcol, B + EDGE, top, nh, cx + xmax, extra)
        out.append(marks)
        return "".join(out), bottom
    gs, gap, lead = 4.2, 0.9, 1.0
    y = base + 2.0 + extra
    for k in ROWS_Q[p]:
        w = k * gs + (k - 1) * gap
        for i in range(k):
            out.append(wilt_at(mid - w / 2 + gs / 2 + i * (gs + gap), y + gs / 2, gs, 0, gcol))
        y += gs + lead
    return "".join(out), y - lead


def card(n, species):
    p = penalty(n)
    tint, acc, ncol, gcol = TIER[p]
    block, block_bottom = info_block(n, p, ncol, gcol)
    # colour field lives in the corner opposite the number (top-right; its 180-degree twin is bottom-left)
    field = (f'<g transform="translate({CW} 0) scale(-1 1) scale({FIELD_SCALE})">'
             + field_blob(tint, acc) + sprig(acc if p < 5 else "#C99A9A") + "</g>")
    half = field + block
    ph = PLANT_H
    pw = ph * 540 / 740
    # The info block sits in the top-left quadrant and its twin beside the pot at bottom-right, so the
    # plant drops below the tallest (two-row) block and nudges left, away from the bottom-right marks.
    cx, cy = CW / 2 - 1.5, B + EDGE + 26.4 + ph / 2
    plant = (f'<svg x="{cx - pw / 2:.3f}" y="{cy - ph / 2:.3f}" width="{pw:.3f}" height="{ph:.3f}" '
             f'viewBox="30 40 540 740">{uniq(plant_inner(species), f"k{n}-")}</svg>')
    # vertical name label on the right edge (the side without a number), caps on the EDGE line
    label = name_label(species, CH / 2 - 4.0, CW - B - EDGE - 2.15, "#405D43", "#7A6A58", rot=90)
    bg = f'<rect x="0" y="0" width="{CW}" height="{CH}" fill="{PAPER_BG}"/>' if PAPER_BG else ""
    return (bg + half
            + f'<g transform="rotate(180 {CW / 2} {CH / 2})">{half}</g>'
            + plant + label)

# ------------------------------------------------------------------ player aid (fills the 4 spare slots on the last sheet)
AID = "aid"          # stands in for a card number in page()
AID_KEY = [          # (penalty, which cards)
    (7, "55"),
    (5, "11, 22, 33 … 99"),
    (3, "10, 20, 30 … 100"),
    (2, "5, 15, 25 … 95"),
    (1, "every other card"),
]
AID_STEPS = [
    "Everyone picks a card; all reveal at once.",
    "Lowest card first: add it to the row whose last card is the highest number below it.",
    "Your card would be 6th? Take the five; yours starts the row.",
    "Lower than every row? Take any row; your card starts it.",
]
AID_SETUP = "Deal 10 each · 4 cards start 4 rows"
AID_END = ["Play out all 10, then deal again.", "At 66 points the game ends: fewest wins."]


def wrap(font, text, size, width):
    lines, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if cur and font.width(t, size) > width:
            lines.append(cur); cur = w
        else:
            cur = t
    return lines + [cur]


def aid_card():
    """Player aid: penalty key + one-glance rules. No corner number or tier field, so it can't pass for a game card."""
    x0, x1 = B + EDGE, CW - B - EDGE                    # text column, 5 mm clear of the cut
    num = PathFont(FONT)
    ink, soft = C["ink"], "#7A6A58"
    o = [f'<g fill="{C["deep"]}">' + num.path("Take 5", 7.2, CW / 2, B + EDGE + 5.4) + "</g>",
         f'<g fill="{soft}">' + LATIN_FONT.path("Botanical · player aid", 2.5, CW / 2, B + EDGE + 9.1) + "</g>"]
    y = B + EDGE + 11.6
    # penalty key: one tinted band per tier, leaves on the left, cards in the middle, points on the right
    bh, gs, gap = 4.7, 3.1, 0.55
    for p, which in AID_KEY:
        tint, _, ncol, gcol = TIER[p]
        o.append(f'<rect x="{x0:.2f}" y="{y:.2f}" width="{x1 - x0:.2f}" height="{bh}" rx="1.2" fill="{tint}"/>')
        cy = y + bh / 2
        for i in range(p):
            o.append(wilt_at(x0 + 1.2 + gs / 2 + i * (gs + gap), cy, gs, 0, gcol))
        o.append(f'<g fill="{ncol}">' + LABEL_FONT.path(which, 2.4, x0 + 7 * gs + 6 * gap + 2.6, cy + 0.85, anchor="start") + "</g>")
        o.append(f'<g fill="{ncol}">' + num.path(str(p), 3.6, x1 - 2.6, cy + 1.3) + "</g>")
        y += bh + 0.7
    # rules summary
    size, lead, w = 2.35, 2.95, x1 - x0
    y += 3.6
    o.append(f'<g fill="{soft}">' + LATIN_FONT.path(AID_SETUP, 2.25, CW / 2, y) + "</g>")
    y += 1.0
    for k, step in enumerate(AID_STEPS, 1):
        top = y + 1.3
        o.append(f'<g fill="{C["terra_dark"]}">' + num.path(str(k), 3.2, x0 + 1.4, top + 2.95) + "</g>")
        for line in wrap(LABEL_FONT, step, size, w - 4.6):
            y += lead
            o.append(f'<g fill="{ink}">' + LABEL_FONT.path(line, size, x0 + 4.6, y + 1.3, anchor="start") + "</g>")
        y += 1.3
    y += 1.6
    for line in AID_END:
        y += 2.9
        o.append(f'<g fill="{soft}">' + LATIN_FONT.path(line, 2.25, CW / 2, y) + "</g>")
    assert y <= CH - B - EDGE, f"player aid overflows: {y:.1f} mm"
    return "".join(o)

# ------------------------------------------------------------------ sheets
def slot(i):
    """Top-left of slot i on the page (slot is CH wide x CW tall)."""
    return MX + (i % COLS) * CH, MY + (i // COLS) * CW


def crop_marks(gap=2.0, length=4.0):
    xs = sorted({MX + c * CH + d for c in range(COLS) for d in (B, CH - B)})
    ys = sorted({MY + r * CW + d for r in range(ROWS) for d in (B, CW - B)})
    L = []
    for x in xs:
        L.append(f"M{x:.2f} {MY - gap - length:.2f}v{length}M{x:.2f} {PH - MY + gap:.2f}v{length}")
    for y in ys:
        L.append(f"M{MX - gap - length:.2f} {y:.2f}h{length}M{PW - MX + gap:.2f} {y:.2f}h{length}")
    return f'<path d="{"".join(L)}" stroke="#3A3A3A" stroke-width="0.2" fill="none"/>'


def page(cards, idx, total):
    g = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}mm" height="{PH}mm" viewBox="0 0 {PW} {PH}">',
         f'<defs><clipPath id="cc"><rect x="0" y="0" width="{CW}" height="{CH}"/></clipPath></defs>',
         f'<rect width="{PW}" height="{PH}" fill="#fff"/>']
    for i, (n, sp) in enumerate(cards):
        x, y = slot(i)
        # rotate 90 deg: card-local (u, v) -> page (x + CH - v, y + u)
        face = aid_card() if n == AID else card(n, sp)
        g.append(f'<g transform="translate({x + CH:.3f} {y:.3f}) rotate(90)"><g clip-path="url(#cc)">{face}</g></g>')
    g.append(crop_marks(gap=1.5, length=3.0))
    nums = [n for n, _ in cards if n != AID]
    what = f"cards {nums[0]}–{nums[-1]}" + (f" + {len(cards) - len(nums)} player aids" if len(nums) < len(cards) else "")
    g.append(f'<text x="{MX}" y="{MY - 5.2:.2f}" font-family="DejaVu Sans" font-size="2.0" fill="#777">'
             f'Take 5 · Botanical · sheet {idx}/{total} · {what} · 63.5 × 88 mm · print at 100%, borderless off</text>')
    g.append("</svg>")
    return "".join(g)


if __name__ == "__main__":
    import cairosvg
    from pypdf import PdfWriter, PdfReader
    outdir = sys.argv[1] if len(sys.argv) > 1 else str(paths.BUILD / "deck_sheets")
    os.makedirs(outdir, exist_ok=True)
    A = assign()
    allc = [(n, A[n]) for n in range(1, 105)]
    allc += [(AID, None)] * (-len(allc) % (COLS * ROWS))     # 104 cards leave 4 spare slots on the last sheet
    pages = [allc[i:i + 6] for i in range(0, len(allc), 6)]
    w = PdfWriter()
    for k, pc in enumerate(pages, 1):
        svg = page(pc, k, len(pages))
        open(f"{outdir}/sheet_{k:02d}.svg", "w").write(svg)
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=f"{outdir}/sheet_{k:02d}.pdf")
        w.append(PdfReader(f"{outdir}/sheet_{k:02d}.pdf"))
    w.add_metadata({"/Title": "Take 5 Botanical — 104-card print-and-play deck + 4 player aids (63.5x88 mm poker)"})
    w.write(str(paths.BUILD / "take5_botanical_deck_63x88_A4.pdf"))
    from collections import Counter
    print(Counter(A.values()))
