"""sheet.py OUT id id id ... : contact sheet of sprite images with id labels (scaled 2x)."""
import sys
from PIL import Image, ImageDraw
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import img
out, ids = sys.argv[1], [int(x) for x in sys.argv[2:]]
import os as _o; cell, cols = int(_o.environ.get("CELL", 72)), int(_o.environ.get("COLS", 12))
sheet = Image.new('RGB', (cell * cols, cell * ((len(ids) + cols - 1) // cols)), (40, 40, 48))
dr = ImageDraw.Draw(sheet)
for k, i in enumerate(ids):
    d = open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/pak/%05d.bin' % i, 'rb').read()
    im = img.to_image(d)
    im.thumbnail((cell - 4, cell - 14))
    x, y = (k % cols) * cell, (k // cols) * cell
    sheet.paste(im, (x + 2, y + 2), im)
    dr.text((x + 2, y + cell - 12), str(i), fill=(255, 255, 0))
sheet.save(out)
