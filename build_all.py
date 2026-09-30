"""Rebuild everything:  python build_all.py            (uses the master plant SVGs in plants/out)
                        python build_all.py --plants   (also regenerates the plant SVGs from their generators)

Outputs land in build/:
  take5_botanical_deck_63x88_A4.pdf   104 cards, 13 A4 sheets of 8: front, back, front, back ... (26 pages, duplex)
  take5_print_proof_A4.pdf             one-page printer/paper proof
  card_back.svg / card_back_preview.png
  plants_print/                        print-prepped plant SVGs used on the cards
"""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(*args):
    print(">", " ".join(os.path.relpath(a, ROOT) if os.path.isabs(a) else a for a in args))
    subprocess.run([PY, *args], check=True, cwd=ROOT)


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    if "--plants" in sys.argv:
        run(os.path.join(ROOT, "plants", "build_plants.py"))
    run(os.path.join(ROOT, "deck", "print_prep.py"))
    run(os.path.join(ROOT, "deck", "deck.py"))
    run(os.path.join(ROOT, "deck", "back.py"))
    run(os.path.join(ROOT, "deck", "backs_sheet.py"))
    run(os.path.join(ROOT, "deck", "proof.py"))
    print("done -> build/")
