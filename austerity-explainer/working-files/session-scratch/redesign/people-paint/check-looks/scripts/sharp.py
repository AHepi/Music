import numpy as np, cv2
from PIL import Image
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
D='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-looks/'
def load(p): return np.asarray(Image.open(p).convert('L')).astype(np.float32)
z=1.08; s=1080/1536*z
M=np.array([[s,0,540-1536/2*s],[0,s,960-2730/2*s]],np.float32)
st=cv2.warpAffine(load(P+'people-test-painting-state.png'),M,(1080,1920),flags=cv2.INTER_AREA)
pt=cv2.warpAffine(load(P+'people-test-painting.png'),M,(1080,1920),flags=cv2.INTER_AREA)
f3=load(D+'pf/f091.png'); f1=load(D+'pf/f031.png'); s1=load(D+'sf/f031.png')
regions={'far colliery and gate':(420,620,720,900),'left terraces (middle distance)':(0,500,300,900),'sky':(0,0,400,300),'drum':(470,960,620,1160),'near pavement (bottom)':(250,1500,1000,1900),'near steps (bottom right)':(780,1450,1080,1900)}
def sharp(a,b):
    x0,y0,x1,y1=b; r=a[y0:y1,x0:x1]
    return cv2.Laplacian(r,cv2.CV_32F,ksize=3).var()
print('%-34s %10s %10s %8s'%('region','painting','film 3s','film/painting'))
for n,b in regions.items():
    a=sharp(st,b); c=sharp(f3,b)
    print('%-34s %10.0f %10.0f %8.2f'%(n,a,c,c/a))
# grain/flicker: per-pixel temporal std over frames 61..120 in a flat region (sky, near pavement)
fr=np.stack([load(D+'pf/f%03d.png'%i) for i in range(62,121)])
sd=fr.std(0)
for n,b in regions.items():
    x0,y0,x1,y1=b; print('frame-to-frame wobble (std over 2-4 s) in %-30s %.2f levels'%(n,sd[y0:y1,x0:x1].mean()))
mn=fr.mean((1,2)); print('whole-frame mean over 2-4 s: min %.2f max %.2f'%(mn.min(),mn.max()))
