import numpy as np, cv2, sys
from PIL import Image
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
NC='/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/'
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def skel(b):
    dt=cv2.distanceTransform(b.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    mx=cv2.dilate(dt,np.ones((3,3),np.uint8)); return (dt>0)&(dt>=mx), dt
def lines(Lm):
    k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(21,21))
    bh=cv2.morphologyEx(Lm,cv2.MORPH_BLACKHAT,k)
    ink=(bh>18)&(Lm<45)
    ink=cv2.morphologyEx(ink.astype(np.uint8),cv2.MORPH_OPEN,np.ones((2,2),np.uint8)).astype(bool)
    sk,dt=skel(ink)
    return ink.mean()*100, (2*dt[sk]).mean()
for name,p in [('people painting',P+'people-test-painting.png'),('notice painting',NC+'notice-corner-painted.jpg'),('people plate',P+'people-test-plate.jpg')]:
    a=load(p); L=lum(a)
    hsv=cv2.cvtColor(np.clip(a,0,255).astype(np.uint8),cv2.COLOR_RGB2HSV)
    cover,w=lines(L)
    R,G,B=a[...,0],a[...,1],a[...,2]
    warm=(R-B>18)&(L>45)
    H=a.shape[0]
    ground=np.zeros(L.shape,bool); ground[int(0.55*H):,:]=True
    # film crop version
    z=1.08; s=1080/1536*z
    M=np.array([[s,0,540-1536/2*s],[0,s,960-2730/2*s]],np.float32)
    f=cv2.warpAffine(a,M,(1080,1920)); Lf=lum(f); wf=((f[...,0]-f[...,2]>18)&(Lf>45)); gf=np.zeros(Lf.shape,bool); gf[int(0.55*1920):,:]=True
    r=cv2.resize(a,(1080,1920),interpolation=cv2.INTER_LANCZOS4); Lr=lum(r); wr=((r[...,0]-r[...,2]>18)&(Lr>45))
    print(f'{name}: size {a.shape[1]}x{a.shape[0]} brightness {L.mean():.1f} spread {L.std():.1f} colour {hsv[...,1].mean():.1f} ink {cover:.2f}% width {w:.2f} warm ground full {100*warm[ground].mean():.1f}% filmcrop {100*wf[gf].mean():.1f}% resized {100*wr[gf].mean():.1f}%')
