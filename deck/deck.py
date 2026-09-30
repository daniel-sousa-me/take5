"""Take 5 botanical — card face + A4 print sheets (63.5x88 mm poker size, 1.5 mm bleed, 6 per A4: 2 cols x 3 rows, cards rotated 90 deg, inside Canon recommended print area)."""
import re, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

PLANTS = str(paths.PLANTS_PRINT)   # print-prepped plants (see print_prep.py)
PAPER_BG = None   # None = leave the white stock unprinted (recommended); a tint must be L* <= 88 (face_colour_check)
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

TIER = {  # (field tint, field accent, sprig ornament, number colour, glyph colour) -- pre-blended solids
    # five hue families so a tier reads at a glance: sage, ochre, terracotta, dusty rose, and 55's own
    # bird-of-paradise orange (the one card with 7 marks gets a strong field *and* an orange number)
    1: ("#D8DDBF", "#CDD4AF", "#A3AF83", C["deep"], "#6B7C52"),
    2: ("#EFD8A0", "#E8CC87", "#C9A45A", C["deep"], "#A0722C"),
    3: ("#F0C4A4", "#E9B592", "#CF906B", C["deep"], "#7E4630"),   # marks a dark brown-terracotta: the old #A9583A
    # was nearly the pot's #B96E4A (dE00 7.8; the bottom-right marks on 10/20/100 read as part of the pot) and tier 7's
    # #A8452A (dE00 5.3); #7E4630 is dE00 17.5 from the pot and 9.4 from tier 7, same hue (h 47) as before
    5: ("#D8A3B0", "#CD94A3", "#B07282", "#6A3A45", "#86465A"),   # cooler + ~10 L darker than tier 3 so they never merge
    7: ("#E38E62", "#D97D51", "#F4C2A2", "#A8452A", "#A8452A"),
}

SPECIES = sorted(f[:-4] for f in os.listdir(paths.PLANTS_SRC) if f.endswith(".svg"))
SHOWY_55 = "strelitzia_reginae"
SHOWY_11 = ["anthurium_andraeanum", "spathiphyllum", "hoya_carnosa", "echeveria_elegans",
            "begonia_maculata", "monstera_deliciosa", "alocasia_amazonica", "opuntia_microdasys"]
# Predominantly burgundy/pink plants never go on a tier-5 (dusty rose, burgundy marks) or tier-7 (orange) card:
# leaf, marks and corner field would be one hue family and the marks would sink into the leaves (oxalis used
# to be on 77). assign() asserts it; every multiple of 11 is a SHOWY card, so these only ever cycle.
NOT_ON_ROSE = {"oxalis_triangularis", "tradescantia_zebrina"}
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
    assert not [n for n in out if penalty(n) >= 5 and out[n] in NOT_ON_ROSE], "burgundy plant on a rose/orange card"
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


_profiles = {}


def glyph_profile(ch):
    """(ys, left, right): for every font-unit row y of the digit's ink, its leftmost and rightmost ink x
    (NaN where the row has no ink). Rasterised from the outline at 1 font unit per pixel."""
    if ch not in _profiles:
        import numpy as np
        from PIL import Image, ImageDraw
        from fontTools.pens.basePen import BasePen

        class Flat(BasePen):                        # outline -> polygons (curves sampled 16x)
            def __init__(self):
                super().__init__(_gs); self.rings, self.cur = [], []
            def _moveTo(self, p): self.cur = [p]
            def _lineTo(self, p): self.cur.append(p)
            def _curveToOne(self, a, b, c):
                p0 = self.cur[-1]
                for i in range(1, 17):
                    t = i / 16; u = 1 - t
                    self.cur.append(tuple(u ** 3 * p0[k] + 3 * u * u * t * a[k] + 3 * u * t * t * b[k] + t ** 3 * c[k] for k in (0, 1)))
            def _qCurveToOne(self, a, b):
                p0 = self.cur[-1]
                for i in range(1, 17):
                    t = i / 16; u = 1 - t
                    self.cur.append(tuple(u * u * p0[k] + 2 * u * t * a[k] + t * t * b[k] for k in (0, 1)))
            def _closePath(self): self.rings.append(self.cur); self.cur = []
            _endPath = _closePath

        f = Flat(); _gs[_cmap[ord(ch)]].draw(f)
        pad = 200                                                  # font units of room round the glyph
        im = Image.new("1", (UPM + 2 * pad, UPM + 2 * pad), 0)
        d = ImageDraw.Draw(im)
        for r in f.rings:                                          # fill every contour: extents ignore holes
            if len(r) > 2:
                d.polygon([(x + pad, UPM + pad - y) for x, y in r], fill=1)
        m = np.array(im)
        rows = np.nonzero(m.any(axis=1))[0]
        m = m[rows]
        left = np.array([np.argmax(r) for r in m], float) - pad
        right = np.array([len(r) - 1 - np.argmax(r[::-1]) for r in m], float) - pad + 1
        _profiles[ch] = (UPM + pad - rows.astype(float), left, right)
    return _profiles[ch]


def pair_distance(a, b, dx):
    """Shortest distance (font units) between the ink of digit a and that of digit b drawn dx units to its
    right (origin to origin). Exact to the 1-unit raster: the nearest ink to the other glyph is always on its
    facing frontier, so each glyph is reduced to its row-by-row right (a) / left (b) edge. 0 if they touch."""
    import numpy as np
    ya, _, ra = glyph_profile(a)
    yb, lb, _ = glyph_profile(b)
    hx = lb[None, :] + dx - ra[:, None]
    if (hx[ya[:, None] == yb[None, :]] <= 0).any():
        return 0.0
    hx = np.maximum(hx, 0)
    return float(np.sqrt((hx ** 2 + (ya[:, None] - yb[None, :]) ** 2).min()))


DIGIT_GAP = 0.6      # min paper between neighbouring digits' ink (mm): 0.5 mm spec + 0.1 for ink spread on uncoated card
DIGIT_GAP_MAX_3 = 1.0   # 100-104: the loose 1->0 pair is closed to this, so "1 00" doesn't read as two groups
_pair_cache = {}


def pair_advance(a, b, size, track, n_digits=2):
    """Distance (font units) from digit a's origin to digit b's: advance + tracking, opened just enough to leave
    DIGIT_GAP mm of paper between their ink (and, on 3-digit numbers, closed to at most DIGIT_GAP_MAX_3)."""
    key = (a, b, size, track, n_digits == 3)
    if key not in _pair_cache:
        s = size / UPM
        adv = glyph(a)[1] + track * UPM
        lo, hi = DIGIT_GAP / s, (DIGIT_GAP_MAX_3 / s if n_digits == 3 else None)
        dist = pair_distance(a, b, adv)
        target = lo if dist < lo else hi if hi is not None and dist > hi else None
        if target is not None:                                    # bisect the advance to hit the target gap
            x0, x1 = (adv, adv + 2 * target) if dist < lo else (adv - 2 * target, adv)
            for _ in range(30):
                xm = (x0 + x1) / 2
                if pair_distance(a, b, xm) < target: x0 = xm
                else: x1 = xm
            adv = x1
        _pair_cache[key] = adv
    return _pair_cache[key]


def digit_origins(n, size, track):
    """Glyph origins (font units) of each digit of n, centred on the advance box (as number_path draws them)."""
    t = str(n)
    xs = [0.0]
    for a, b in zip(t, t[1:]):
        xs.append(xs[-1] + pair_advance(a, b, size, track, len(t)))
    total = xs[-1] + glyph(t[-1])[1]
    return [x - total / 2 for x in xs]


def number_path(n, size, cx, baseline, track=-0.02):
    """Centred number as a single path, `size` = font size in mm; digit spacing from pair_advance."""
    s = size / UPM
    parts = [f'<path transform="translate({cx / s + x:.2f} 0)" d="{glyph(ch)[0]}"/>'
             for ch, x in zip(str(n), digit_origins(n, size, track))]
    return (f'<g transform="translate(0 {baseline:.3f}) scale({s:.6f} {-s:.6f})">' + "".join(parts) + "</g>")


def digit_gaps(n):
    """Paper (mm) between each pair of neighbouring digits on card n, as drawn."""
    size, track = num_style(n)
    xs = digit_origins(n, size, track)
    t = str(n)
    return [pair_distance(t[i], t[i + 1], xs[i + 1] - xs[i]) * size / UPM for i in range(len(t) - 1)]


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
FRAUNCES_TEXT = paths.STATIC_FONTS / "Fraunces-Regular-opsz9-static.ttf"


@__import__("functools").lru_cache(None)
def text_font():
    """Fraunces Regular at the 9 pt optical size (made once into build/fonts): the proof's body text and the
    sheet headers, drawn as paths like every other label."""
    if not FRAUNCES_TEXT.exists():
        from fontTools.varLib import instancer
        paths.STATIC_FONTS.mkdir(parents=True, exist_ok=True)
        inst = instancer.instantiateVariableFont(TTFont(str(paths.FRAUNCES_VAR)),
                                                 {"wght": 400, "opsz": 9, "SOFT": 0, "WONK": 0})
        inst.save(str(FRAUNCES_TEXT))
    return PathFont(str(FRAUNCES_TEXT))


def sheet_header(s, size=2.0, col="#777"):
    """One line of sheet header, in Fraunces as paths, left-aligned 5.2 mm above the card block (inside the
    recommended area: top of the caps ~46.6 mm > REC_TOP 45.8 mm) and ending inside the block's right edge."""
    f = text_font()
    assert MX + f.width(s, size) <= PW - MX, f"sheet header overruns: {s!r}"
    assert MY - 5.2 - size * 0.75 >= REC_TOP
    return f'<g fill="{col}">' + f.path(s, size, MX, MY - 5.2, anchor="start") + "</g>"
LATIN_COL = "#625444"    # botanical name: warm grey-brown, a step darker than the old #7A6A58 (too faint on uncoated card)
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


LATIN_OFFSET = 3.35   # botanical baseline, mm below the common name's (was 2.95: the common name's descenders came within
                      # 0.44-0.55 mm of the botanical caps/ascenders on begonia, jade, string of pearls, Swiss cheese,
                      # bird of paradise and Chinese money plant; now >= 0.83 mm on every label, name_label_gap())
LABEL_ASC = 2.25      # common-name ascender height (ink reaches 2.23 mm above its baseline)
LABEL_MIN_GAP = 0.8   # min paper between the two lines' ink (mm), asserted on every build


def name_label(species, cy, x_base, col_common, col_latin, rot=-90):
    """Vertical label centred on cy, first baseline at x_base (card-local).
    rot=-90 reads bottom-to-top (caps toward the left edge); rot=90 reads top-to-bottom (caps toward the right edge)."""
    common, latin = NAMES[species]
    g = (f'<g fill="{col_common}">' + LABEL_FONT.path(common, 3.0, 0, 0, track=0.02) + "</g>"
         f'<g fill="{col_latin}">' + LATIN_FONT.path(latin, 2.5, 0, LATIN_OFFSET) + "</g>")
    return f'<g transform="translate({x_base:.2f} {cy:.2f}) rotate({rot})">{g}</g>'


def name_label_gap(species, k=40):
    """Shortest paper gap (mm) between the common name's ink and the botanical name's ink, rendered upright at
    k px/mm. Exact to the raster: the nearest ink of each line to the other lies on its facing frontier, so each
    line is reduced to its column-by-column bottom (common) / top (botanical) edge."""
    import io, cairosvg, numpy as np
    from PIL import Image
    common, latin = NAMES[species]
    w = max(LABEL_FONT.width(common, 3.0, 0.02), LATIN_FONT.width(latin, 2.5)) + 2

    def ink(g):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * k:.0f}" height="{8 * k}" '
               f'viewBox="{-w / 2} -3 {w} 8">{g}</svg>')
        return np.array(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGBA"))[..., 3] > 127
    a = ink(LABEL_FONT.path(common, 3.0, 0, 0, track=0.02))
    b = ink(LATIN_FONT.path(latin, 2.5, 0, LATIN_OFFSET))
    ca, cb = np.nonzero(a.any(0))[0], np.nonzero(b.any(0))[0]
    bot = a.shape[0] - 1 - np.argmax(a[::-1, ca], axis=0)          # lowest ink row of each common-name column
    top = np.argmax(b[:, cb], axis=0)                              # highest ink row of each botanical column
    dy = np.maximum(top[None, :] - bot[:, None] - 1, 0)
    dx = np.maximum(np.abs(cb[None, :] - ca[:, None]) - 1, 0)
    return float(np.sqrt(dx ** 2 + dy ** 2).min()) / k


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
# 10x10 box, origin top-left. A stem rises and bends over at the top; from the bend a broad, ovate leaf hangs
# limp, widest near its stalk and tapering to a pointed tip straight down (a hanging pothos-style leaf), and a
# second small leaf droops off the stem. Designed to read at ~4 mm: no inner detail (a paper-coloured midrib
# turned an earlier version into a coffee bean), solid silhouette, stroke 0.85 (= 0.34 mm). Ink box x 0..9.2.
WILT = ('<path d="M2.8 10 C2.7 7.4 2.9 4.9 3.6 3.4 C4.2 2.1 5.4 1.4 6.6 1.9" fill="none" stroke="{c}" '
        'stroke-width="0.85" stroke-linecap="round"/>'
        '<path d="M6.5 1.85 C5.4 2.6 5.2 4.2 5.8 5.8 C6.4 7.3 7.3 8.6 7.7 10.0 C8.4 8.6 9.2 6.9 9.2 5.0 '
        'C9.2 3.2 8.0 2.0 6.5 1.85Z" fill="{c}"/>'
        '<path d="M2.78 6.2 C1.4 6.1 0.2 7.3 0.0 8.8 C1.4 8.7 2.5 7.6 2.78 6.2Z" fill="{c}"/>')
WILT_C = (4.6, 5.8)   # visual centre of the ink in the 10x10 box


def wilt_row(count, cx, y, size, col):
    gap = size * 0.22
    w = count * size + (count - 1) * gap
    x0 = cx - w / 2
    s = size / 10
    g = []
    for i in range(count):
        g.append(f'<g transform="translate({x0 + i * (size + gap):.3f} {y:.3f}) scale({s:.4f})">'
                 + WILT.format(c=col) + "</g>")
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
NUM_SIZE_3 = 18.5   # 100-104: a size step smaller (cap ~12 mm) with tighter tracking, so the wide twin number
NUM_TRACK, NUM_TRACK_3 = -0.02, -0.045   # in the bottom-right corner sits well clear under the pot
POT_GAP = 4.0       # min gap (mm) between the pot and a bottom-right number that sits under it (3-digit cards);
                    # the plant is lifted on those cards to keep it
SHOWPIECE = {55: 1.15}   # cards whose plant may be drawn up to this much larger than its species size, as large
SHOWPIECE_SHIFTS = (0.0, 0.5, 1.0, 1.5, -0.5, -1.0)   # as fits (collision-checked), pot sliding up to these mm
SHOWPIECE_MARK_CLEAR = 2.0   # air round the showpiece card's top-left marks (mm; the top half is open anyway) ...
SHOWPIECE_BR_CLEAR = 3.5     # ... and round its bottom-right block (number + 7 marks, right beside the pot), so the
                             # busiest corner of the busiest card doesn't feel crowded (box clearance; ink gap ~4.6 mm)
GLYPH = 4.0
# Plant size. Each plant is measured (ink box of its master SVG) and scaled so the deck reads as one
# consistent size: a blend of height-fit and area-fit, damped and clamped so pots never jump wildly.
# The pot bottom (canvas y 752, x 300 in every plant SVG) always lands on the same point of the card.
PLANT_S = 0.054           # mm per plant-canvas unit for a reference plant (= 40 mm for the full 740-unit canvas)
PLANT_REF = (657, 113.5e3)  # reference ink height above the pot base (units) and ink area (units^2)
PLANT_FIT = (0.6, 0.4, 0.8)  # weights of height-fit and area-fit, then damping exponent
PLANT_CLAMP = (0.92, 1.2)  # limits on the per-plant factor
PLANT_CLAMP_MAX = {"senecio_rowleyanus": 1.53}  # per-species upper limit overriding PLANT_CLAMP[1]: a plant drawn
                          # with a smaller pot in its master may be scaled up further (its pot still prints at the set's rim width)
POT_MAX = 13.5            # widest pot rim on the card (mm): squat plants in wide bowls don't balloon
PLANT_X, PLANT_Y = CW / 2 - 1.5, 68.6   # card position of the pot's bottom centre
PLANT_SHIFTS = (0.0, -1.0, -2.0, -3.0)  # allowed leftward pot shifts (mm) when a plant is blocked
PLANT_CLEAR = 1.2         # min gap between plant ink and numbers / label (mm); plants also stay inside EDGE
MARK_CLEAR = 2.0          # ... and the (smaller, busier) penalty marks get more air
MARK_CLEAR_2ROW = 2.75    # ... more still round a two-row block (tier 5: 3 over 2), which reads crowded at 2.0
NUM_AXIS = B + TW / 4 - 0.5   # number axis: 0.5 mm outside the 1/4 line (the most that keeps 88/99 off the EDGE),
                              # so the bottom-right block sits a little nearer its corner
FIELD_SCALE = 0.6   # corner colour field size


def num_style(n):
    """(font size, tracking) of the number on card n."""
    return (NUM_SIZE_3, NUM_TRACK_3) if n >= 100 else (NUM_SIZE, NUM_TRACK)


def number_ink(n, size, track=NUM_TRACK):
    """(xmin, xmax) of the number's ink relative to its centring point (see number_path)."""
    s = size / UPM
    xmin, xmax = 1e9, -1e9
    for ch, x in zip(str(n), digit_origins(n, size, track)):
        bp = BoundsPen(_gs); _gs[_cmap[ord(ch)]].draw(bp)
        x0, _, x1, _ = bp.bounds
        xmin, xmax = min(xmin, x + x0), max(xmax, x + x1)
    return xmin * s, xmax * s


PEN_STYLE = "quarter"   # "quarter" | "under" | "beside" | "rosette" | "corner"
CLUSTER = {1: [(0, 0)], 2: [(0, -0.5), (0, 0.5)], 3: [(0, -0.55), (0, 0.55), (0.95, 0)],
           5: [(0, -1), (1, -1), (0.5, 0), (0, 1), (1, 1)],
           7: [(0.5, -1), (1.5, -1), (0, 0), (1, 0), (2, 0), (0.5, 1), (1.5, 1)]}


def wilt_at(x, y, size, rot, col):
    """One penalty glyph centred on (x, y)."""
    return (f'<g transform="translate({x:.3f} {y:.3f}) rotate({rot:.1f}) scale({size / 10:.4f}) '
            f'translate({-WILT_C[0]} {-WILT_C[1]})">' + WILT.format(c=col) + "</g>")


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
GLYPH_Q = 4.0      # penalty mark size in the "quarter" layout (mm)
UL_INSET = 0.3     # underline = numeral ink width minus this at each end


def info_block(n, p, ncol, gcol):
    """Number + penalty marks in the top-left quadrant (card-local coords).
    Returns (svg, bottom of the block, ink boxes [(x0, y0, x1, y1)])."""
    top = B + EDGE
    size, track = num_style(n)
    nh = numeral_height(size)
    base = top + nh
    xmin, xmax = number_ink(n, size, track)
    if PEN_STYLE == "quarter":
        axis = NUM_AXIS                                     # just outside the 1/4 line of the trim
        cx = axis - (xmin + xmax) / 2                       # centre the ink (not the advance) on the axis
        if cx + xmin < B + EDGE:                            # 3-digit numbers: keep them off the edge
            cx = B + EDGE - xmin
    else:
        cx = B + EDGE - xmin
    mid = cx + (xmin + xmax) / 2
    out = [f'<g fill="{ncol}">' + number_path(n, size, cx, base, track) + "</g>"]
    boxes = [(cx + xmin, top, cx + xmax, base)]
    extra = 0.0
    if needs_mark(n):   # 6/9 underline: the full width of the numeral ink less a small inset, centred
        u0, u1 = cx + xmin + UL_INSET, cx + xmax - UL_INSET
        out.append(f'<rect x="{u0:.2f}" y="{base + 1.0:.2f}" width="{u1 - u0:.2f}" height="0.7" rx="0.35" fill="{ncol}"/>')
        extra = 1.2
        boxes.append((u0, base + 1.0, u1, base + 1.7))
    if PEN_STYLE != "quarter":
        marks, bottom = penalty_marks(PEN_STYLE, p, gcol, B + EDGE, top, nh, cx + xmax, extra)
        out.append(marks)
        boxes.append((B + EDGE, top, cx + xmax + 20, bottom))       # rough: alternative styles only
        return "".join(out), bottom, boxes
    gs, gap, lead = GLYPH_Q, 0.8, 0.7
    y = base + 1.8 + extra
    for k in ROWS_Q[p]:
        w = k * gs + (k - 1) * gap
        x0 = max(mid - w / 2, B + EDGE)                     # a wide row never crosses the EDGE line
        for i in range(k):
            out.append(wilt_at(x0 + gs / 2 + i * (gs + gap), y + gs / 2, gs, 0, gcol))
        boxes.append((x0, y, x0 + w, y + gs, MARK_CLEAR_2ROW if len(ROWS_Q[p]) > 1 else MARK_CLEAR))
        y += gs + lead
    return "".join(out), y - lead, boxes


# ------------------------------------------------------------------ plant size + collision-safe fit
_mask_cache = {}
MASK_UNITS = 2            # plant canvas units per mask pixel


def plant_measure(name):
    """(ink mask, pot width in canvas units) of the master plant SVG. Mask = alpha > 40, 1 px = MASK_UNITS
    canvas units; the pot is found by its terracotta colour in the lower part of the canvas."""
    if name not in _mask_cache:
        import io, cairosvg, numpy as np
        from PIL import Image
        png = cairosvg.svg2png(url=str(paths.PLANTS_SRC / f"{name}.svg"),
                               output_width=600 // MASK_UNITS, output_height=800 // MASK_UNITS)
        im = np.array(Image.open(io.BytesIO(png)).convert("RGBA")).astype(float)
        r, g, b, a = (im[..., i] for i in range(4))
        gr, br = g / np.maximum(r, 1), b / np.maximum(r, 1)
        pot = (a > 200) & (r > 120) & (gr > 0.5) & (gr < 0.72) & (br > 0.3) & (br < 0.52)
        pot[:540 // MASK_UNITS] = False
        widths = [np.ptp(np.nonzero(row)[0]) for row in pot if row.sum() > 10]
        _mask_cache[name] = (a > 40, max(widths, default=0) * MASK_UNITS)
    return _mask_cache[name]


def plant_mask(name):
    return plant_measure(name)[0]


def plant_design_scale(name):
    """mm per canvas unit this plant is drawn at when nothing is in the way."""
    import numpy as np
    m, pot_w = plant_measure(name)
    ys = np.nonzero(m.any(axis=1))[0]
    h = 752 - ys.min() * MASK_UNITS
    area = m.sum() * MASK_UNITS ** 2
    wh, wa, damp = PLANT_FIT
    rel = ((PLANT_REF[0] / h) ** wh * (PLANT_REF[1] / area) ** (wa / 2)) ** damp
    s = PLANT_S * min(PLANT_CLAMP_MAX.get(name, PLANT_CLAMP[1]), max(PLANT_CLAMP[0], rel))
    return min(s, POT_MAX / pot_w) if pot_w else s


def label_box(species, cy, x_base):
    common, latin = NAMES[species]
    half = max(LABEL_FONT.width(common, 3.0, 0.02), LATIN_FONT.width(latin, 2.5)) / 2
    return (x_base - LATIN_OFFSET - 0.65, cy - half, x_base + LABEL_ASC, cy + half)   # latin descenders ~0.63 mm


def plant_y(n):
    """Card y of the pot base on card n. Normally PLANT_Y. On 100-104 (whose wide bottom-right number reaches
    under the pot), and on any card whose twin number would, the plant is lifted just enough to leave POT_GAP
    between the pot and the numeral, so the pot never looks as if it stands on it."""
    _, _, boxes = info_block(n, penalty(n), "#000", "#000")
    x0, y0, x1, y1 = boxes[0][:4]                              # the number's ink box (top-left block)
    tx0, ty0 = CW - x1, CH - y1                                # its 180-degree twin: left edge, top
    if n < 100 and tx0 > PLANT_X + POT_HALF_LOW:              # twin number clear of the pot sideways
        return PLANT_Y
    pot_bottom = PLANT_Y + POT_INK
    return PLANT_Y - max(0.0, pot_bottom + POT_GAP - ty0)


POT_INK = 0.4             # pot ink below its base point (the rounded bottom), mm
POT_HALF_LOW = 6.0        # half-width of the lower pot body (widest pot, plus a margin), mm


def plant_collides(name, s, boxes, dx=0.0, py=PLANT_Y):
    m = plant_mask(name)
    px = PLANT_X + dx
    H, W = m.shape
    for x0, y0, x1, y1 in boxes:
        u0 = int(math.floor((300 + (x0 - px) / s) / MASK_UNITS)); u1 = int(math.ceil((300 + (x1 - px) / s) / MASK_UNITS))
        v0 = int(math.floor((752 + (y0 - py) / s) / MASK_UNITS)); v1 = int(math.ceil((752 + (y1 - py) / s) / MASK_UNITS))
        u0, v0, u1, v1 = max(u0, 0), max(v0, 0), min(u1, W), min(v1, H)
        if u0 < u1 and v0 < v1 and m[v0:v1, u0:u1].any():
            return True
    return False


def obstacles(n, species, showpiece=False):
    """Boxes (card-local mm) the plant ink must stay out of."""
    p = penalty(n)
    _, _, boxes = info_block(n, p, "#000", "#000")
    obs = []
    for x0, y0, x1, y1, *k in boxes:
        c = (SHOWPIECE_MARK_CLEAR if showpiece else k[0]) if k else PLANT_CLEAR
        obs.append((x0 - c, y0 - c, x1 + c, y1 + c))
        if showpiece:                    # the bottom-right block sits beside the pot: number and marks get more air
            c = max(c, SHOWPIECE_BR_CLEAR)
        obs.append((CW - x1 - c, CH - y1 - c, CW - x0 + c, CH - y0 + c))      # 180-degree twin
    c = PLANT_CLEAR
    x0, y0, x1, y1 = label_box(species, *LABEL_POS)
    obs.append((x0 - c, y0 - c, x1 + c, y1 + c))
    fw, fh = 36 * FIELD_SCALE, 35 * FIELD_SCALE                                 # corner colour fields
    obs += [(CW - fw, 0, CW, fh), (0, CH - fh, fw, CH)]
    e, big = B + EDGE, 1e3
    obs += [(-big, -big, e, big), (CW - e, -big, big, big), (-big, -big, big, e), (-big, CH - e, big, big)]
    return obs


def plant_scale(n, species, dx=0.0, s0=None, showpiece=False):
    """Design scale (or s0), reduced until the plant clears everything on card n."""
    s0 = s = s0 or plant_design_scale(species)
    obs = obstacles(n, species, showpiece)
    py = plant_y(n)
    while plant_collides(species, s, obs, dx, py):
        s *= 0.99
        assert s > 0.6 * s0, f"card {n}: {species} does not fit"
    return s


_species_fit = {}


def species_fit(species):
    """(scale, x shift) per species: the scale is the smallest that fits on every card the species appears
    on, so a plant always looks the same size (print_prep sizes its lines for exactly this scale). A plant
    whose design size is blocked on some card may slide up to PLANT_SHIFT mm left if that lets it stay bigger."""
    if not _species_fit:
        cards = {}
        for n, sp in assign().items():
            cards.setdefault(sp, []).append(n)
        for sp, ns in cards.items():
            best = None
            for dx in PLANT_SHIFTS:
                k = min(plant_scale(n, sp, dx) for n in ns)
                if best is None or k > best[0] * 1.02:      # only move the pot for a real gain
                    best = (k, dx)
            _species_fit[sp] = best
    return _species_fit.get(species) or (plant_scale(1, species), 0.0)


def showpiece_fit(n, species, s):
    """(scale, x shift) on a SHOWPIECE card: as large as fits, up to SHOWPIECE[n] x the species scale s, with
    SHOWPIECE_MARK_CLEAR around the marks; shifts where the pot itself cannot clear them are skipped."""
    fits = []
    for d in SHOWPIECE_SHIFTS:
        try:
            fits.append((plant_scale(n, species, d, s * SHOWPIECE[n], showpiece=True), d))
        except AssertionError:
            pass
    return max(fits, key=lambda t: (round(t[0], 5), -abs(t[1])))


def plant_scales():
    """mm per plant-canvas unit for every species (used by print_prep.py)."""
    return {sp: species_fit(sp)[0] for sp in SPECIES}


LABEL_POS = (CH / 2 - 4.0, CW - B - EDGE - LABEL_ASC)   # (centre y, first baseline x) of the vertical name label:
                                                        # the common name's ascenders end on the EDGE line


def card(n, species):
    p = penalty(n)
    tint, acc, sprig_col, ncol, gcol = TIER[p]
    block, block_bottom, _ = info_block(n, p, ncol, gcol)
    # colour field lives in the corner opposite the number (top-right; its 180-degree twin is bottom-left)
    field = (f'<g transform="translate({CW} 0) scale(-1 1) scale({FIELD_SCALE})">'
             + field_blob(tint, acc) + sprig(sprig_col) + "</g>")
    half = field + block
    # pot bottom-centre pinned to (PLANT_X, PLANT_Y): just left of centre so the bottom-right block sits
    # beside the narrow pot rather than under the leaves
    s, dx = species_fit(species)
    py = plant_y(n)
    if n in SHOWPIECE:                                           # showpiece card: as large as it fits, up to the cap
        s, dx = showpiece_fit(n, species, s)
    elif plant_collides(species, s, obstacles(n, species), dx, py):   # species forced onto another card (preview)
        s = min(s, plant_scale(n, species, dx))
    plant = (f'<g transform="translate({PLANT_X + dx:.3f} {py:.3f}) scale({s:.5f}) translate(-300 -752)">'
             f'{uniq(plant_inner(species), f"k{n}-")}</g>')
    # vertical name label on the right edge (the side without a number), caps on the EDGE line
    label = name_label(species, *LABEL_POS, "#405D43", LATIN_COL, rot=90)
    bg = f'<rect x="0" y="0" width="{CW}" height="{CH}" fill="{PAPER_BG}"/>' if PAPER_BG else ""
    return (bg + half
            + f'<g transform="rotate(180 {CW / 2} {CH / 2})">{half}</g>'
            + plant + label)

def face_colour_check():
    """White stock: no card-face colour (tier fields / accents / sprigs / numbers / marks, name labels, PAPER_BG)
    may be a near-white or sit in the speckle band (L* 88-95, C* <= 25: prints as a sparse dither, not an even
    tint). Returns the lightest face colour and its L*."""
    from print_prep import lab, paper_white, speckle_band
    cols = {c for t in TIER.values() for c in t} | {"#405D43", LATIN_COL} | ({PAPER_BG} if PAPER_BG else set())
    bad = sorted(c for c in cols if paper_white(c) or speckle_band(c))
    assert not bad, f"card-face colours too light for white stock (L* > 88, C* <= 25): {bad}"
    top = max(cols, key=lambda c: lab(c)[0])
    return top, lab(top)[0]


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
        g.append(f'<g transform="translate({x + CH:.3f} {y:.3f}) rotate(90)"><g clip-path="url(#cc)">{card(n, sp)}</g></g>')
    g.append(crop_marks(gap=1.5, length=3.0))
    g.append(sheet_header(f'Take 5 · Botanical · sheet {idx}/{total} · cards {cards[0][0]}–{cards[-1][0]} · '
                          '63.5 × 88 mm · print at 100%, borderless off'))
    g.append("</svg>")
    return "".join(g)


if __name__ == "__main__":
    import cairosvg
    from pypdf import PdfWriter, PdfReader
    gaps = sorted((min(digit_gaps(n)), n) for n in range(10, 105))
    assert gaps[0][0] >= DIGIT_GAP - 0.01, gaps[:5]
    c0, L0 = face_colour_check()
    print(f"card-face colours ok on white stock (lightest {c0}, L* {L0:.1f}; none in the L* 88-95 speckle band)")
    print("digit gaps (mm), tightest:", ", ".join(f"{n} {g:.2f}" for g, n in gaps[:5]))
    lg = sorted((name_label_gap(sp), sp) for sp in SPECIES)
    assert lg[0][0] >= LABEL_MIN_GAP, f"name label lines too close: {lg[:3]}"
    print("name label line gaps (mm), tightest:", ", ".join(f"{sp} {g:.2f}" for g, sp in lg[:4]))
    outdir = sys.argv[1] if len(sys.argv) > 1 else str(paths.BUILD / "deck_sheets")
    os.makedirs(outdir, exist_ok=True)
    A = assign()
    allc = [(n, A[n]) for n in range(1, 105)]
    pages = [allc[i:i + 6] for i in range(0, len(allc), 6)]
    w = PdfWriter()
    for k, pc in enumerate(pages, 1):
        svg = page(pc, k, len(pages))
        open(f"{outdir}/sheet_{k:02d}.svg", "w").write(svg)
        cairosvg.svg2pdf(bytestring=svg.encode(), write_to=f"{outdir}/sheet_{k:02d}.pdf")
        w.append(PdfReader(f"{outdir}/sheet_{k:02d}.pdf"))
    w.add_metadata({"/Title": "Take 5 Botanical — 104-card print-and-play deck (63.5x88 mm poker)"})
    w.write(str(paths.BUILD / "take5_botanical_deck_63x88_A4.pdf"))
    from collections import Counter
    print(Counter(A.values()))
