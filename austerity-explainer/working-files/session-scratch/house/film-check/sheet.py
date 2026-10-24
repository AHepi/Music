import sys,numpy as np
from PIL import Image,ImageDraw
a=np.load(sys.argv[1],mmap_mode='r'); s,e,step,out=int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
idx=list(range(s,min(e,len(a)),step)); cols=8; rows=(len(idx)+cols-1)//cols
W,H=270,480; im=Image.new('RGB',(cols*W,rows*(H+14)),'white'); d=ImageDraw.Draw(im)
for k,i in enumerate(idx):
    x,y=(k%cols)*W,(k//cols)*(H+14)
    im.paste(Image.fromarray(a[i].astype(np.uint8)),(x,y+14)); d.text((x+3,y+1),f"f{i} {i/30:.2f}s",fill='black')
im.save(out)
