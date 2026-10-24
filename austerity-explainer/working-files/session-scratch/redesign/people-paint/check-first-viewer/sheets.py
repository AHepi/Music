import sys, os
from PIL import Image, ImageDraw
src, out, start, end = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
# frames every 0.1 s = every 3rd frame; frame n (1-based) is at time (n-1)/30
idx = [i for i in range(start, end+1, 3)]
W=360; H=640
cols=5
rows=(len(idx)+cols-1)//cols
sheet=Image.new('RGB',(cols*W, rows*(H+24)),(255,255,255))
d=ImageDraw.Draw(sheet)
for k,i in enumerate(idx):
    im=Image.open(f'{src}/f{i:03d}.png').convert('RGB').resize((W,H),Image.LANCZOS)
    x=(k%cols)*W; y=(k//cols)*(H+24)
    sheet.paste(im,(x,y+24))
    d.text((x+5,y+5),f't={(i-1)/30:.2f}s (frame {i-1})',fill=(0,0,0))
sheet.save(out,quality=90)
