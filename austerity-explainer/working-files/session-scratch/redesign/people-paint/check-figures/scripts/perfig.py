import numpy as np, cv2, json
from PIL import Image
F='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-figures/frames/'
O='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-figures/'
def L(k,i): return np.array(Image.open(f'{F}{k}/f{i:03d}.png').convert('RGB')).astype(np.float32)
def lum(a):
    c=a/255.0; c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
    return 0.2126*c[...,0]+0.7152*c[...,1]+0.0722*c[...,2]
p59=L('painted',59); p60=L('painted',60); s59=L('sil',59); s60=L('sil',60)
gs=cv2.cvtColor(s59.astype(np.uint8),cv2.COLOR_RGB2GRAY)
d=np.abs(s60-p60).mean(2)
fig=((d>12)|(gs<10)).astype(np.uint8)
fig&=(np.abs(s59-p60).mean(2)>10).astype(np.uint8)
fig=cv2.morphologyEx(fig,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
fig=cv2.morphologyEx(fig,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
# restrict to people band
fig[:780]=0; fig[1400:]=0
n,lab,st,cen=cv2.connectedComponentsWithStats(fig)
blobs=[(i,*st[i]) for i in range(1,n) if st[i][4]>300]
blobs.sort(key=lambda b:b[1])
names={}
for b in blobs: print('blob',b)
Image.fromarray(fig*255).save(O+'masks/film-figs-f59.png')
small=lambda a:cv2.resize(a,(360,640),interpolation=cv2.INTER_AREA)
ps,ss=small(p59),small(s59)
Yp,Ys=lum(ps),lum(ss)
out={}
for b in blobs:
    i,x,y,w,h,a=b
    m=(lab==i).astype(np.float32)
    ms=(cv2.resize(m,(360,640),interpolation=cv2.INTER_AREA)>0.5).astype(np.uint8)
    if ms.sum()<4: continue
    inner=cv2.erode(ms,np.ones((2,2),np.uint8)) if ms.sum()>40 else ms
    ring=cv2.dilate(ms,np.ones((7,7),np.uint8))-cv2.dilate(ms,np.ones((3,3),np.uint8))
    ring&=(1-cv2.dilate((fig>0).astype(np.uint8)[::3,::3][:640,:360],np.ones((3,3),np.uint8)))  # avoid other figures
    r={}
    for k,Y in (('painted',Yp),('silhouette',Ys)):
        f=Y[inner>0].mean(); g=Y[ring>0].mean()
        r[k]=dict(fig=round(float(f),4),around=round(float(g),4),ratio=round(float((max(f,g)+0.05)/(min(f,g)+0.05)),2))
    out[f'x{x}y{y}w{w}h{h}']=r
    print(f'blob x={x:4d} y={y:4d} h={h:3d} phone h={h/3:.0f}px | painted fig {r["painted"]["fig"]:.4f} vs around {r["painted"]["around"]:.4f} ratio {r["painted"]["ratio"]} | silhouette fig {r["silhouette"]["fig"]:.4f} vs around {r["silhouette"]["around"]:.4f} ratio {r["silhouette"]["ratio"]}')
json.dump(out,open(O+'film-per-figure-contrast.json','w'),indent=1)
