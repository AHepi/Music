import numpy as np
from PIL import Image
F='../../final/'
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)/255
lum=lambda a: 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def reg(im,name,x0,y0,x1,y1):
    H,W,_=im.shape; r=im[int(y0*H):int(y1*H), int(x0*W):int(x1*W)].reshape(-1,3); L=lum(r)
    print(f'{name}: lum {L.mean():.3f} p90 {np.percentile(L,90):.3f} max {L.max():.3f} rgb {tuple(int(v) for v in r.mean(0)*255)} R-B {(r[:,0]-r[:,2]).mean():+.2f}')
S=load(F+'composed-end-5.png'); P=load(F+'notice-corner-plate-2.png'); R=load('/home/user/Music/austerity-explainer/experiments/30 Test - composed by Nano Banana - own camera.jpg')
# left terrace window glass vs reveal (still)
for x in np.arange(0.20,0.44,0.01):
    col=S[int(0.31*1920):int(0.40*1920), int(x*1080):int((x+0.01)*1080)]
    L=lum(col.reshape(-1,3))
    print(f'  x {x:.2f}: lum mean {L.mean():.3f} max {L.max():.3f} R-B {(col[...,0]-col[...,2]).mean():+.2f}')
reg(S,'still near-left upper window',0.01,0.27,0.045,0.34)
reg(P,'plate near-left upper window lower sash',0.036,0.318,0.062,0.345)
reg(P,'plate near-left upper window top sash',0.036,0.27,0.062,0.31)
# sky gradient: still vs reference
for name,im in (('still',S),('reference',R),('plate',P)):
    for y in (0.02,0.08,0.14,0.20):
        reg(im,f'{name} sky row {y:.2f}',0.15,y,0.40,y+0.03)
