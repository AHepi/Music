import json, numpy as np, cv2
from PIL import Image
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
F='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/plate-facts/'
D='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-looks/'
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
W,H=1536,2730
z=1.08; s=1080/1536*z
M=np.array([[s,0,540-W/2*s],[0,s,960-H/2*s]],np.float32)
def tofilm(a,interp=cv2.INTER_LINEAR): return cv2.warpAffine(a,M,(1080,1920),flags=interp)
paint=tofilm(load(P+'people-test-painting.png')); state=tofilm(load(P+'people-test-painting-state.png'))
plate=tofilm(load(P+'people-test-plate.jpg'))
facts=json.load(open(F+'facts.json'))
ids=np.asarray(Image.open(F+'ids.png').convert('RGB').resize((W,H),Image.NEAREST)).astype(np.uint8)
idsf=tofilm(ids,cv2.INTER_NEAREST).astype(int)
def gmask(name):
    c=np.array(facts['groups'][name]['colour']); return (np.abs(idsf-c).sum(-1)<=6)
men=['man facing','man arms folded','man stooped','man hand on bar','man leaning']
walkers=['walker %d'%i for i in range(1,7)]
allm=np.zeros((1920,1080),bool)
for k in men+walkers: allm|=gmask(k)
p1=load(D+'pf/f031.png'); p2=load(D+'pf/f061.png'); s1=load(D+'sf/f031.png')
print('whole frame mean L: painting(film framing) %.1f  painted film 1.0s %.1f  2.0s %.1f  silhouettes %.1f  state(film framing) %.1f'%(lum(paint).mean(),lum(p1).mean(),lum(p2).mean(),lum(s1).mean(),lum(state).mean()))
sky=np.zeros((1920,1080),bool); sky[20:200,20:300]=True
print('sky RGB painting',paint[sky].mean(0).round(1),'film',p1[sky].mean(0).round(1))
print('\nfigure / surroundings (mean luminance)')
for n in men+walkers:
    m=gmask(n)
    if m.sum()<30: continue
    m8=m.astype(np.uint8)
    inner=cv2.erode(m8,np.ones((5,5),np.uint8)).astype(bool)
    ring=cv2.dilate(m8,np.ones((41,41),np.uint8)).astype(bool)&~cv2.dilate(m8,np.ones((9,9),np.uint8)).astype(bool)&~allm
    row=[]
    for lab,a in [('plate',plate),('painting',paint),('painted film',p1),('silhouette film',s1)]:
        L=lum(a); row.append('%s %.0f/%.0f=%.2f'%(lab,L[inner].mean(),L[ring].mean(),L[inner].mean()/L[ring].mean()))
    print('%-16s'%n,' | '.join(row))
# silhouettes: value spread inside and bright seams
print('\nsilhouette insides:')
for n in men:
    m=gmask(n).astype(np.uint8); inner=cv2.erode(m,np.ones((5,5),np.uint8)).astype(bool)
    L=lum(s1)[inner]
    print('%-16s mean %.1f p50 %.1f p99 %.1f  pixels brighter than 40: %d (%.2f%%)'%(n,L.mean(),np.median(L),np.percentile(L,99),(L>40).sum(),100*(L>40).mean()))
    Lp=lum(p1)[inner]; print('   painted film same figure: mean %.1f p5 %.1f p95 %.1f'%(Lp.mean(),np.percentile(Lp,5),np.percentile(Lp,95)))
np.save(D+'allmen_film.npy',allm)
