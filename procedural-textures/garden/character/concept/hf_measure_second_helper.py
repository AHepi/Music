import sys
from PIL import Image, ImageFilter
import numpy as np
B="/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/concept/"
R={"roof":(700,300,1500,500),"bridge":(0,1250,900,1500),"grass fg":(1500,1350,2400,1600),"maple":(100,300,800,700),"sand":(1700,900,2300,1300),"wall":(1500,580,2300,800),"rock":(200,840,420,1050)}
files=sys.argv[1:]
print("%-16s"%"file"+"".join("%9s"%k for k in R)+"   mean-lum  sat")
for f in files:
    im=Image.open(f).convert("RGB").resize((2400,1600),Image.LANCZOS)
    a=np.asarray(im).astype(np.float32)/255
    lum=0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
    g=Image.fromarray((lum*255).astype(np.uint8))
    blur=np.asarray(g.filter(ImageFilter.GaussianBlur(2))).astype(np.float32)
    hf=np.abs(np.asarray(g).astype(np.float32)-blur)
    mx=a.max(-1); mn=a.min(-1); sat=((mx-mn)/np.maximum(mx,1e-4)).mean()
    print("%-16s"%f.split("/")[-1][:16]+"".join("%9.2f"%hf[y0:y1,x0:x1].mean() for (x0,y0,x1,y1) in R.values())+"   %.3f  %.3f"%(lum.mean(),sat))
