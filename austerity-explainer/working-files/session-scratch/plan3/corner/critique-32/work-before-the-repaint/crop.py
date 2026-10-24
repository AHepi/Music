import sys
from PIL import Image
src = sys.argv[1]; out = sys.argv[2]
x0,y0,x1,y1 = map(float, sys.argv[3:7]); scale = float(sys.argv[7]) if len(sys.argv)>7 else 3
im = Image.open(src).convert('RGB'); W,H = im.size
box = (int(x0*W), int(y0*H), int(x1*W), int(y1*H))
c = im.crop(box); c = c.resize((int(c.width*scale), int(c.height*scale)), Image.NEAREST if scale>=3 else Image.LANCZOS)
c.save(out); print(box, c.size)
