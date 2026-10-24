import sys
from PIL import Image, ImageDraw
src,out=sys.argv[1],sys.argv[2]
frames=[int(x) for x in sys.argv[3].split(',')]
W,H=360,640
sheet=Image.new('RGB',(len(frames)*W,H+24),(255,255,255))
d=ImageDraw.Draw(sheet)
for k,i in enumerate(frames):
    im=Image.open(f'{src}/f{i+1:03d}.png').convert('RGB').resize((W,H),Image.LANCZOS)
    sheet.paste(im,(k*W,24)); d.text((k*W+5,5),f'frame {i}  t={i/30:.3f}s',fill=(0,0,0))
sheet.save(out,quality=92)
