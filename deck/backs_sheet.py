"""A4 sheet of 6 card backs, positioned to match the front sheets for a LONG-EDGE flip
(sheet turned over left-to-right, same edge leading into the rear tray)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cairosvg, deck, back, paths

def page():
    g = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{deck.PW}mm" height="{deck.PH}mm" viewBox="0 0 {deck.PW} {deck.PH}">',
         f'<defs><clipPath id="bc"><rect width="{deck.CW}" height="{deck.CH}"/></clipPath></defs>',
         f'<rect width="{deck.PW}" height="{deck.PH}" fill="#fff"/>']
    art = back.back_group()
    g.append(f'<defs><g id="backart">{art}</g></defs>')
    for i in range(deck.COLS * deck.ROWS):
        x, y = deck.slot(i)
        # mirror the column for a long-edge flip (the layout is symmetric left/right, so this is exact)
        x = deck.PW - x - deck.CH
        g.append(f'<g transform="translate({x + deck.CH:.3f} {y:.3f}) rotate(90)"><g clip-path="url(#bc)"><use href="#backart"/></g></g>')
    g.append(deck.sheet_header('Take 5 · Botanical · card backs · print on the reverse of each deck sheet · '
                               'flip on the long edge · 100%, borderless off'))
    g.append("</svg>")
    return "".join(g)

if __name__ == "__main__":
    svg = page()
    paths.BUILD.mkdir(exist_ok=True)
    open(paths.BUILD / "backs_sheet.svg", "w").write(svg)
    deck.write_pdf(svg, paths.BUILD / "take5_card_backs_63x88_A4.pdf", "Take 5 Botanical — card backs (print on the reverse of every deck sheet)")
