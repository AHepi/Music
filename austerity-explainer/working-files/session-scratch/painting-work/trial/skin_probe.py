import numpy as np, cv2, json
from PIL import Image
exec(open('fig_probe.py').read().split("def skin")[0])
def kovac(a):
    R,G,B=a[...,0],a[...,1],a[...,2]
    mx=np.maximum(np.maximum(R,G),B); mn=np.minimum(np.minimum(R,G),B)
    return (R>95)&(G>40)&(B>20)&(mx-mn>15)&(np.abs(R-G)>15)&(R>G)&(R>B)
def ycrcb(a):
    y=cv2.cvtColor(np.clip(a,0,255).astype(np.uint8),cv2.COLOR_RGB2YCrCb).astype(int)
    return (y[...,1]>=135)&(y[...,1]<=180)&(y[...,2]>=85)&(y[...,2]<=135)&(y[...,0]>80)
rules={'kovac':kovac,'ycrcb':ycrcb}
for rn,rule in rules.items():
    sp,sq=rule(plate),rule(paint)
    for frac in (0.12,0.2,0.3):
        line=[]
        for n in figs:
            m=vis(n)
            if m.sum()<30: continue
            ys,xs=np.nonzero(m); top=ys.min(); h=ys.max()-top+1
            head=m&(np.arange(H)[:,None]<top+frac*h)
            headw=cv2.dilate(head.astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
            line.append(f'{n.replace("man ","").replace("walker ","w")}:{int((sp&headw).sum())}->{int((sq&headw).sum())}')
        print(rn,frac,' '.join(line))
