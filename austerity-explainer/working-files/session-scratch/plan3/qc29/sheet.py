import sys
from PIL import Image, ImageDraw
d,out=sys.argv[1],sys.argv[2]; fr=[int(x) for x in sys.argv[3].split(',')]; w=int(sys.argv[4]) if len(sys.argv)>4 else 270
ims=[Image.open(f"{d}/f{i+1:03d}.png") for i in fr]
h=int(w*16/9); cols=min(len(fr),6); rows=(len(fr)+cols-1)//cols
S=Image.new('RGB',(cols*w,rows*(h+16)),'white'); D=ImageDraw.Draw(S)
for k,(i,im) in enumerate(zip(fr,ims)):
    x=(k%cols)*w; y=(k//cols)*(h+16); S.paste(im.resize((w,h)),(x,y+16)); D.text((x+4,y+2),f"f{i} {i/30:.2f}s",fill='black')
S.save(out)
