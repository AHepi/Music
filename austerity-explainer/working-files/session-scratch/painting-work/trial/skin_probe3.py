import numpy as np, cv2, json
from PIL import Image
exec(open('skin_probe.py').read().split("rules={")[0])
sp,sq=kovac(plate),kovac(paint)
for frac,wid in ((0.13,9),(0.13,15),(0.15,11),(0.18,11)):
    line=[]
    for n in figs:
        m=vis(n)
        if m.sum()<30: continue
        ys,xs=np.nonzero(m); top=ys.min(); h=ys.max()-top+1
        head=m&(np.arange(H)[:,None]<top+frac*h)
        k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*wid+1,2*wid+1))
        hw=cv2.dilate(head.astype(np.uint8),k).astype(bool)
        line.append(f'{n.replace("man ","").replace("walker ","w")}:{int((sp&hw).sum())}->{int((sq&hw).sum())}')
    print(frac,wid,' '.join(line))
