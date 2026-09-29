import sys, io, cairosvg, numpy as np
from PIL import Image
def tac(svgfile, dpi=100):
    png = cairosvg.svg2png(url=svgfile, dpi=dpi, background_color="white")
    a = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(float)/255
    k = 1-a.max(axis=2)
    cmy = (1-a-k[...,None])/np.maximum(1-k[...,None],1e-6)
    t = cmy.sum(axis=2)+k
    inked = t > 0.02
    return t.mean()*100, inked.mean()*100, (t>1.5).mean()*100
for f in sys.argv[1:]:
    m,i,h = tac(f)
    print(f"{f}: mean ink {m:.1f}% of page (naive CMYK TAC), inked area {i:.0f}%, heavy (>150%) {h:.1f}%")
