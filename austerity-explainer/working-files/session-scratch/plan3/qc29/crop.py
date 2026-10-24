import sys
from PIL import Image, ImageDraw
d,out,box=sys.argv[1],sys.argv[2],[int(v) for v in sys.argv[3].split(',')]; fr=[int(x) for x in sys.argv[4].split(',')]; sc=float(sys.argv[5]) if len(sys.argv)>5 else 1
ims=[Image.open(f"{d}/g{i:03d}.png").crop(box) for i in fr]
w,h=int(ims[0].width*sc),int(ims[0].height*sc); cols=min(len(fr),3); rows=(len(fr)+cols-1)//cols
S=Image.new('RGB',(cols*w,rows*(h+16)),'white'); D=ImageDraw.Draw(S)
for k,(i,im) in enumerate(zip(fr,ims)):
    x=(k%cols)*w; y=(k//cols)*(h+16); S.paste(im.resize((w,h)),(x,y+16)); D.text((x+4,y+2),f"f{i} {i/30:.2f}s",fill='black')
S.save(out)
