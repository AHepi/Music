import sys, numpy as np
from PIL import Image
p = sys.argv[1]
im = Image.open(p).convert('RGB'); W,H = im.size
a = np.asarray(im).astype(np.float32)/255
R,G,B = a[...,0],a[...,1],a[...,2]
L = 0.2126*R+0.7152*G+0.0722*B
hsv = np.asarray(im.convert('HSV')).astype(np.float32)
h = hsv[...,0]/255*360; s = hsv[...,1]/255; v = hsv[...,2]/255
print('size',W,H,'mean L',L.mean().round(3))
# cool vs warm
cool = (B > R+0.03)
warm = (R > B+0.08) & (s>0.25)
print('cool (blue > red) share %', round(cool.mean()*100,1), ' warm-ish (red>blue, saturated) share %', round(warm.mean()*100,1))
for name,(x0,x1) in {'left third':(0,1/3),'mid third':(1/3,2/3),'right third':(2/3,1)}.items():
    sl = (slice(None), slice(int(x0*W),int(x1*W)))
    print(f'{name}: mean L {L[sl].mean():.3f}  cool% {cool[sl].mean()*100:.0f}  warm% {warm[sl].mean()*100:.1f}  L>0.6 % {(L[sl]>0.6).mean()*100:.2f}')
for name,(y0,y1) in {'top third':(0,1/3),'mid third':(1/3,2/3),'bottom third':(2/3,1)}.items():
    sl = (slice(int(y0*H),int(y1*H)), slice(None))
    print(f'{name}: mean L {L[sl].mean():.3f}  cool% {cool[sl].mean()*100:.0f}  warm% {warm[sl].mean()*100:.1f}  L>0.6 % {(L[sl]>0.6).mean()*100:.2f}')
# quadrants of 3x3
print('3x3 mean brightness (rows top->bottom, cols left->right):')
for r in range(3):
    print('  ', [round(float(L[int(r*H/3):int((r+1)*H/3), int(c*W/3):int((c+1)*W/3)].mean()),3) for c in range(3)])
# elements: boxes in display coords (1116 wide) -> scale
sc = W/1116
boxes = {
 'notice paper':(830,905,1020,1290),
 'notice key lines (PITS..NEW TERMS)':(840,1080,1010,1170),
 'notice headline NOTICE':(840,930,1010,990),
 'fire (drum top)':(590,1260,740,1335),
 'drum body':(565,1340,760,1645),
 'lantern':(862,1300,940,1470),
 'chair seat':(785,1425,1035,1480),
 'chair back':(955,1205,1080,1430),
 'street lamp glass':(815,290,935,440),
 'pithead wheels':(585,380,810,500),
 'sky beside wheels (lamp halo)':(560,520,790,640),
 'sky top-left':(80,40,460,300),
 'colliery gate':(575,850,770,940),
 'cart+sacks':(15,955,370,1145),
 'lit cobbles left':(300,1390,520,1570),
 'left near lamp':(232,712,290,800),
 'lit window left':(98,560,128,690),
 'bottom pavement strip':(0,1800,1116,2000),
}
print('\nelement: mean L | surround-ring L | contrast ratio | mean sat | warm%')
for k,(x0,y0,x1,y1) in boxes.items():
    X0,Y0,X1,Y1 = [int(t*sc) for t in (x0,y0,x1,y1)]
    inner = L[Y0:Y1,X0:X1]
    pad = int(0.5*max(X1-X0,Y1-Y0))
    oy0,oy1,ox0,ox1 = max(0,Y0-pad),min(H,Y1+pad),max(0,X0-pad),min(W,X1+pad)
    ring = L[oy0:oy1,ox0:ox1].copy(); m = np.ones_like(ring,bool); m[Y0-oy0:Y1-oy0, X0-ox0:X1-ox0]=False
    rl = ring[m].mean()
    print(f'{k:38s} {inner.mean():.3f} | {rl:.3f} | {(inner.mean()+0.05)/(rl+0.05):.2f} | {s[Y0:Y1,X0:X1].mean():.2f} | {warm[Y0:Y1,X0:X1].mean()*100:.0f}')
# brightest 0.5% pixels: where
thr = np.quantile(L,0.995)
ys,xs = np.nonzero(L>=thr)
print('\nbrightest 0.5% pixels threshold',round(float(thr),3))
hist = {}
for nm,(x0,y0,x1,y1) in boxes.items():
    X0,Y0,X1,Y1 = [int(t*sc) for t in (x0,y0,x1,y1)]
    n = ((xs>=X0)&(xs<X1)&(ys>=Y0)&(ys<Y1)).sum()
    if n: hist[nm]=n
tot=len(xs)
for k,v_ in sorted(hist.items(), key=lambda t:-t[1]): print(f'  {k}: {v_/tot*100:.0f}%')
