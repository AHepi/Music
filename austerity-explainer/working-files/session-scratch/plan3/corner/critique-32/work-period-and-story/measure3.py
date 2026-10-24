import numpy as np
from PIL import Image
F='../../final/'
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)/255
lum=lambda a: 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
S=load(F+'composed-end-5.png'); P=load(F+'notice-corner-plate-2.png')
def colscan(im,name,y0,y1,x0,x1,step=0.005):
    H,W,_=im.shape
    out=[]
    for x in np.arange(x0,x1,step):
        c=im[int(y0*H):int(y1*H), int(x*W):int((x+step)*W)].reshape(-1,3)
        out.append((x,lum(c).mean(),(c[:,0]-c[:,2]).mean()))
    print(name, ' '.join(f'{x:.3f}:{l:.2f}/{rb:+.2f}' for x,l,rb in out))
colscan(S,'still downpipe band y0.05-0.40',0.05,0.40,0.80,0.92)
colscan(P,'plate right pipe band y0.35-0.70',0.35,0.70,0.88,1.0)
# drum mouth inside flatness (still): rows
H,W,_=S.shape
for y in np.arange(0.630,0.650,0.002):
    r=S[int(y*H):int((y+0.002)*H), int(0.49*W):int(0.64*W)].reshape(-1,3)
    print(f'drum row {y:.3f}: lum {lum(r).mean():.3f} sd {lum(r).std():.3f} rgb {tuple(int(v) for v in r.mean(0)*255)}')
# gutter stripes: luminance profile down a line through the channel at x where channel is (still)
for x in (0.30,0.38,0.44):
    col=S[int(0.78*H):H, int(x*W):int((x+0.01)*W)].mean(1)
    L=lum(col)
    d=np.abs(np.diff(L))
    print(f'gutter x {x}: lum range {L.min():.2f}-{L.max():.2f}, strong steps (>0.04 between rows): {(d>0.04).sum()}')
