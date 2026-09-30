import sys, io, glob, os
import cairosvg
from PIL import Image, ImageDraw, ImageFont

def sheet(files, out, cols=4, cell=(300, 400), bg=(255, 255, 255), label=True):
    rows = (len(files) + cols - 1) // cols
    lab = 26 if label else 0
    W, H = cols * cell[0], rows * (cell[1] + lab)
    im = Image.new("RGB", (W, H), bg)
    dr = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except Exception:
        font = None
    for i, fn in enumerate(files):
        png = cairosvg.svg2png(url=fn, output_width=cell[0], output_height=cell[1])
        tile = Image.open(io.BytesIO(png)).convert("RGBA")
        x, y = (i % cols) * cell[0], (i // cols) * (cell[1] + lab)
        im.paste(tile, (x, y), tile)
        if label:
            name = os.path.basename(fn)[:-4].replace("_", " ")
            dr.text((x + 10, y + cell[1] + 5), name, fill=(80, 70, 60), font=font)
    im.save(out)

if __name__ == "__main__":
    files = sys.argv[2:]
    big = len(files) <= 2
    sheet(files, sys.argv[1], cols=min(4, len(files)), cell=(600, 800) if big else (300, 400))
