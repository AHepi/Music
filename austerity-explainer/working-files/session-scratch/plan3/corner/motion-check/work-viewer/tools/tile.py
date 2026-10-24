# usage: tile.py out.png cols scale x0 y0 x1 y1 frame1 frame2 ... (x/y as pixel box)
import sys
from PIL import Image, ImageDraw
out, cols, sc = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
x0,y0,x1,y1 = map(int, sys.argv[4:8])
fr = sys.argv[8:]
W = sys.argv[0].rsplit('/tools/',1)[0]
ims=[]
for f in fr:
    im=Image.open(f"{W}/frames/f{int(f):03d}.png").convert("RGB").crop((x0,y0,x1,y1))
    im=im.resize((int((x1-x0)*sc),int((y1-y0)*sc)), Image.LANCZOS)
    d=ImageDraw.Draw(im); d.rectangle((0,0,70,18),fill=(0,0,0)); d.text((3,3),f"{int(f)/30:.2f}s",fill=(255,255,0))
    ims.append(im)
w,h=ims[0].size; rows=(len(ims)+cols-1)//cols
S=Image.new("RGB",(w*cols+4*(cols-1),h*rows+4*(rows-1)),(255,0,255))
for i,im in enumerate(ims): S.paste(im,((i%cols)*(w+4),(i//cols)*(h+4)))
S.save(out)
