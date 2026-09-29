"""Regenerate the 24 master plant SVGs from their generators, namespace their ids, and draw a contact sheet.

    python plants/build_plants.py            # all species
    python plants/build_plants.py aloe_vera  # just one
"""
import os, re, sys, subprocess, glob
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def namespace_ids(path):
    """Prefix every id with a short species tag so several plants can share one SVG/HTML page."""
    name = os.path.basename(path)[:-4]
    tag = "".join(w[:2] for w in name.split("_")) + "-"
    s = open(path).read()
    ids = set(re.findall(r'\bid="([^"]+)"', s))
    for i in sorted(ids, key=len, reverse=True):
        if i.startswith(tag):
            continue
        s = re.sub(r'(id="|url\(#|href="#)' + re.escape(i) + r'(?=["\)])', lambda m: m.group(1) + tag + i, s)
    open(path, "w").write(s)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    for gen in sorted(glob.glob(os.path.join(HERE, "species", "*.py"))):
        name = os.path.basename(gen)[:-3]
        if only and name not in only:
            continue
        subprocess.run([sys.executable, gen], check=True, cwd=HERE, stdout=subprocess.DEVNULL)
        namespace_ids(os.path.join(OUT, name + ".svg"))
        print("built", name)
    sys.path.insert(0, HERE)
    from render import sheet
    files = sorted(glob.glob(os.path.join(OUT, "*.svg")))
    os.makedirs(os.path.join(HERE, "..", "build"), exist_ok=True)
    sheet(files, os.path.join(HERE, "..", "build", "plants_contact_sheet.png"), cols=6, cell=(300, 400))
    print("contact sheet -> build/plants_contact_sheet.png")
