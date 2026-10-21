import sys; sys.path.insert(0,'scripts')
from common import *
ST=SW+"/painter_test/stage/stills/"
Pfull=load_rgb(PV+"/lockout-painted.jpg"); S=load_rgb(ST+"dry_projector/still-6.00.jpg",(1080,1920))
Pl=lum(Pfull); Ls=lum(S)
def edges(x,s=2.0):
    g=gauss(x,s); return np.sqrt(cv2.Sobel(g,cv2.CV_32F,1,0)**2+cv2.Sobel(g,cv2.CV_32F,0,1)**2)
best=None
for sc in np.arange(1.20,1.36,0.01):
    # stage px -> painting px:  xp = sc*(xs-540)+768 ; yp = sc*(ys-960)+1365
    M=np.array([[sc,0,768-sc*540],[0,sc,1365-sc*960]],np.float32)
    Pw=cv2.warpAffine(Pl,M,(1080,1920),flags=cv2.INTER_AREA|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT)
    ea=edges(Pw); eb=edges(Ls)
    sel=(slice(300,1700),slice(100,980))
    c=np.corrcoef(ea[sel].ravel(),eb[sel].ravel())[0,1]
    # also small shifts
    for dx in range(-8,9,2):
        for dy in range(-8,9,2):
            c2=np.corrcoef(np.roll(np.roll(ea,dy,0),dx,1)[sel].ravel(),eb[sel].ravel())[0,1]
            if best is None or c2>best[0]: best=(c2,sc,dx,dy)
    print(round(sc,2),round(c,3),flush=True)
print("best",best)
