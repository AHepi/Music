import numpy as np, cv2
from PIL import Image
NC='/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/'
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
D='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-looks/'
def load(p): return np.asarray(Image.open(p).convert('L')).astype(np.float32)
def edges(a):
    e=cv2.Canny(a.astype(np.uint8),40,100).astype(np.float32); return cv2.GaussianBlur(e,(0,0),2)
def best_map(paint,fr):
    best=None
    for z in np.arange(1.04,1.20,0.005):
        for dx in range(-12,13,4):
          for dy in range(-12,13,4):
            s=1080/1536*z
            M=np.array([[s,0,540-1536/2*s+dx],[0,s,960-2730/2*s+dy]],np.float32)
            w=cv2.warpAffine(paint,M,(1080,1920),flags=cv2.INTER_AREA)
            e1=edges(w);e2=edges(fr)
            c=(e1*e2).sum()/np.sqrt((e1*e1).sum()*(e2*e2).sum())
            if best is None or c>best[0]: best=(c,z,dx,dy,w)
    return best
ncp=load(NC+'notice-corner-painted.jpg'); t0=load(D+'ncf/t1.png')
b=best_map(ncp,t0); print('notice corner film t=0 vs its painting: match %.3f zoom %.3f shift %d,%d'%b[:4])
w=b[4]
regions={'far colliery and gate':(420,560,720,900),'left terraces (middle distance)':(0,450,300,900),'near pavement (bottom)':(250,1500,1000,1900)}
def sharp(a,bx):
    x0,y0,x1,y1=bx; return cv2.Laplacian(a[y0:y1,x0:x1],cv2.CV_32F,ksize=3).var()
for n,bx in regions.items():
    print('  %-34s painting %6.0f film %6.0f ratio %.2f'%(n,sharp(w,bx),sharp(t0,bx),sharp(t0,bx)/sharp(w,bx)))
pt=load(P+'people-test-painting.png'); f0=load(D+'pf/f001.png')
b=best_map(pt,f0); print('people test film t=0 vs its painting: match %.3f zoom %.3f shift %d,%d'%b[:4])
w=b[4]
for n,bx in regions.items():
    print('  %-34s painting %6.0f film %6.0f ratio %.2f'%(n,sharp(w,bx),sharp(f0,bx),sharp(f0,bx)/sharp(w,bx)))
Image.fromarray(np.hstack([w[560:900,420:720],f0[560:900,420:720]]).astype(np.uint8)).save(D+'people-far-painting-vs-film.png')
