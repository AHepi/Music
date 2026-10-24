# crop.py IMAGE NAME x0 y0 x1 y1 [scale]  -- fractions of the frame; writes crops/NAME.png
import sys, os
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__))
img = Image.open(sys.argv[1]).convert('RGB')
name = sys.argv[2]
x0, y0, x1, y1 = map(float, sys.argv[3:7])
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 3
W, H = img.size
box = (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))
c = img.crop(box)
c = c.resize((int(c.width * scale), int(c.height * scale)), Image.LANCZOS)
out = os.path.join(here, 'crops', name + '.png')
c.save(out)
print(out, box, c.size)
