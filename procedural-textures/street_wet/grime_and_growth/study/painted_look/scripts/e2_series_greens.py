import sys; sys.path.insert(0,'scripts')
from common import *
import glob, os, json
files=sorted(glob.glob(FILM+"/paintings/austerity-chapter-1/*.jpg")+glob.glob(FILM+"/paintings/inflation-chapter-2/*.png"))
rows=[]
for f in files:
    b=os.path.basename(f)
    if not any(k in b for k in ['bg-','pithead','glasgow-square','farmland','council','mine-small','402','410','101','106']): continue
    im=load_rgb(f,(768,1368))
    x=(im*255).astype(np.uint8); hsv=cv2.cvtColor(x,cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    h=hsv[...,0]*360/255; s=hsv[...,1]/255; v=hsv[...,2]/255
    g=(h>=70)&(h<170)&(s>0.18)&(v>0.12)
    share=g.mean()
    if share<0.004: rows.append((b,share,None)); continue
    rows.append((b,share,(float(np.median(h[g])),float(np.median(s[g])),float(np.median(v[g])),float(np.percentile(v[g],10)),float(np.percentile(v[g],90)))))
for b,sh,st in rows:
    if st is None: print("%-34s green share %.2f%%  (none worth measuring)"%(b,100*sh))
    else: print("%-34s green share %5.2f%%  median hue %3.0f  sat %.2f  value %.2f  (value p10 %.2f, p90 %.2f)"%(b,100*sh,*st))
