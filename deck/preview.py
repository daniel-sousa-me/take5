"""Quick PNG preview of one A4 sheet with chosen card numbers:  python deck/preview.py out.png 1 55 104"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cairosvg, deck
A = deck.assign()
nums = [int(x) for x in sys.argv[2:]]
svg = deck.page([(n, A[n]) for n in nums], 1, 1)
cairosvg.svg2png(bytestring=svg.encode(), write_to=sys.argv[1], output_width=1400)
