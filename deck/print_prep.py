"""Print-prep pass for pigment inkjet (Canon GX5050) on 250 gsm uncoated card.

Scales every stroke by its *effective* size on the printed card and enforces:
  - positive (dark-on-light) lines  >= MIN_POS mm
  - knockout (light-on-dark) lines  >= MIN_KO  mm   (dot gain fills thin light lines in)
  - faint hairlines (opacity < DROP_OP) are removed: on uncoated stock they dither into speckle
Writes print variants to OUT; the master SVGs are untouched.
"""
import re, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
from lxml import etree

SRC = str(paths.PLANTS_SRC)
OUT = str(paths.PLANTS_PRINT)
MM_PER_UNIT = 0.0486          # plant viewBox unit on the printed card (see deck.py plant zone)
MIN_POS, MIN_KO, DROP_OP = 0.15, 0.20, 0.34
NS = "{http://www.w3.org/2000/svg}"


def lum(hexc):
    hexc = hexc.strip()
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", hexc):
        return None
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def tscale(tr):
    """Approximate uniform scale of a transform attribute."""
    s = 1.0
    if not tr:
        return s
    for fn, args in re.findall(r"(\w+)\(([^)]*)\)", tr):
        a = [float(x) for x in re.split(r"[ ,]+", args.strip()) if x]
        if fn == "scale":
            sx = a[0]; sy = a[1] if len(a) > 1 else a[0]
            s *= math.sqrt(abs(sx * sy))
        elif fn == "matrix":
            s *= math.sqrt(abs(a[0] * a[3] - a[1] * a[2]))
    return s


def get(el, key):
    v = el.get(key)
    if v is None and el.get("style"):
        m = re.search(rf"(?:^|;)\s*{key}\s*:\s*([^;]+)", el.get("style"))
        v = m.group(1).strip() if m else None
    return v


def process(fn):
    tree = etree.parse(fn)
    root = tree.getroot()
    ids = {e.get("id"): e for e in root.iter() if e.get("id")}
    # effective scale at which each element is drawn; for <defs> content use the smallest <use> scale
    use_scale = {}

    def walk_scale(el, s):
        s = s * tscale(el.get("transform"))
        if el.tag == NS + "use":
            ref = (el.get("href") or el.get("{http://www.w3.org/1999/xlink}href") or "")[1:]
            use_scale[ref] = min(use_scale.get(ref, 9e9), s)
        for c in el:
            if c.tag in (NS + "defs",):
                continue
            walk_scale(c, s)
    walk_scale(root, 1.0)

    def base_scale(el):
        # walk up to find a referenced ancestor inside defs
        s, e = 1.0, el
        while e is not None:
            s *= tscale(e.get("transform")) if e is not el else 1.0
            if e.get("id") in use_scale and (e.getparent() is not None and e.getparent().tag in (NS + "defs", NS + "symbol") or e.tag == NS + "symbol"):
                return s * use_scale[e.get("id")]
            e = e.getparent()
        return None

    changes = dict(widened=0, dropped=0)
    for el in list(root.iter()):
        if not isinstance(el.tag, str):
            continue
        w = get(el, "stroke-width")
        stroke = get(el, "stroke")
        if w is None or stroke in (None, "none") or el.tag == NS + "g" and False:
            continue
        # cumulative scale
        s = 1.0; e = el; in_defs = False
        chain = []
        while e is not None:
            chain.append(e)
            if e.tag in (NS + "defs", NS + "clipPath", NS + "mask"):
                in_defs = True
            e = e.getparent()
        if any(c.tag == NS + "clipPath" for c in chain):
            continue
        if in_defs:
            s = None
            for c in chain:
                if c.get("id") in use_scale:
                    s = use_scale[c.get("id")]
                    for c2 in chain[:chain.index(c) + 1]:
                        if c2 is not c:
                            s *= tscale(c2.get("transform"))
                    s *= tscale(el.get("transform")) if el is not c else 1
                    break
            if s is None:
                continue
        else:
            for c in chain:
                s *= tscale(c.get("transform"))
        try:
            wv = float(re.sub(r"[a-z]+$", "", w))
        except ValueError:
            continue
        eff_mm = wv * s * MM_PER_UNIT
        L = lum(stroke) if stroke else None
        ko = L is not None and L > 0.55
        need = MIN_KO if ko else MIN_POS
        if eff_mm < need:
            el.set("stroke-width", f"{need / (s * MM_PER_UNIT):.2f}")
            if el.get("style"):
                el.set("style", re.sub(r"stroke-width\s*:[^;]+;?", "", el.get("style")))
            changes["widened"] += 1
        # faint hairline texture can't survive pigment dot gain on uncoated stock: drop it
        op = el.get("opacity") or get(el, "stroke-opacity")
        anc_op = 1.0
        for c in chain[1:]:
            if c.get("opacity"):
                anc_op *= float(c.get("opacity"))
        eff_op = (float(op) if op else 1.0) * anc_op
        if eff_mm < 0.3 and eff_op < DROP_OP:
            el.getparent().remove(el)
            changes["dropped"] += 1
            continue
    os.makedirs(OUT, exist_ok=True)
    tree.write(os.path.join(OUT, os.path.basename(fn)), xml_declaration=False, encoding="utf-8")
    return changes


if __name__ == "__main__":
    for f in sorted(os.listdir(SRC)):
        if f.endswith(".svg"):
            print(f"{f[:-4]:24}", process(os.path.join(SRC, f)))
