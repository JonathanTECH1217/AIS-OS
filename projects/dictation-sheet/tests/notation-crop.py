"""Crop the staff region out of a 2600x700 screenshot and upscale it so the ties and dots can be seen.
Usage: python notation-crop.py in.png out.png x0 y0 x1 y1 scale"""
import sys
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = [int(v) for v in sys.argv[3:7]]
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 3
im = Image.open(src).crop((x0, y0, x1, y1))
im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
im.save(dst)
print('saved', dst, im.size)
