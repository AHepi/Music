import numpy as np, cv2, json
from PIL import Image
exec(open('skin_probe.py').read().split("rules={")[0])
box=(slice(1210,1320),slice(950,1060))
for rn,rule in {'kovac':kovac,'ycrcb':ycrcb}.items():
    print(rn,'box plate',int(rule(plate)[box].sum()),'paint',int(rule(paint)[box].sum()))
# head region from mask: top 15% box widened
for rn,rule in {'kovac':kovac,'ycrcb':ycrcb}.items():
    sp,sq=rule(plate),rule(paint)
    for frac,wid in ((0.15,10),(0.2,10),(0.2,15),(0.25,12)):
        line=[]
        for n in figs:
            m=vis(n)
            if m.sum()<30: continue
            ys,xs=np.nonzero(m); top=ys.min(); h=ys.max()-top+1
            head=m&(np.arange(H)[:,None]<top+frac*h)
            hy,hx=np.nonzero(head)
            r=(slice(max(0,hy.min()-wid),hy.max()+wid+1),slice(max(0,hx.min()-wid),hx.max()+wid+1))
            line.append(f'{n.replace("man ","").replace("walker ","w")}:{int(sp[r].sum())}->{int(sq[r].sum())}')
        print(rn,frac,wid,' '.join(line))
