import json, numpy as np, cv2
from PIL import Image
P='/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/'
F='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/plate-facts/'
NC='/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/'
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
plate=load(P+'people-test-plate.jpg'); paint=load(P+'people-test-painting.png'); behind=load(P+'people-test-painting-behind.jpg'); state=load(P+'people-test-painting-state.png')
helper=load(P+'people-test-helper-plate.jpg')
ncp=load(NC+'notice-corner-painted.jpg')
H,W=plate.shape[:2]
facts=json.load(open(F+'facts.json'))
ids=np.asarray(Image.open(F+'ids.png').convert('RGB').resize((W,H),Image.NEAREST)).astype(int)
def gmask(name):
    c=np.array(facts['groups'][name]['colour'])
    return (np.abs(ids-c).sum(-1)<=6)
names=[n for n in facts['groups']]
print('groups:',names)
men=['man facing','man arms folded','man stooped','man hand on bar','man leaning']
walkers=[n for n in names if n.startswith('walker')]
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
def stats(name,a):
    L=lum(a); 
    print(f'{name:28s} mean L {L.mean():6.1f}  p5 {np.percentile(L,5):5.1f}  p50 {np.percentile(L,50):5.1f}  p95 {np.percentile(L,95):5.1f}  std {L.std():5.1f}  mean RGB {a.reshape(-1,3).mean(0).round(1)}')
for n,a in [('plate',plate),('painting',paint),('painting-behind',behind),('state',state),('helper plate',helper),('notice corner painting',ncp)]:
    stats(n,a)
# saturation
def sat(a):
    hsv=cv2.cvtColor(np.clip(a,0,255).astype(np.uint8),cv2.COLOR_RGB2HSV); return hsv[...,1].mean()
print('mean saturation (0-255): plate %.1f painting %.1f notice painting %.1f'%(sat(plate),sat(paint),sat(ncp)))
# sky
sky=(np.arange(H)[:,None]<H*0.12)&(np.arange(W)[None,:]<W*0.30)
print('sky top-left patch mean RGB plate',plate[sky].mean(0).round(1),'painting',paint[sky].mean(0).round(1),'notice painting',ncp[sky].mean(0).round(1))
# figures
print()
print('figure values (mean luminance inside the figure, and of a ring 6-30 px round it; ratio = figure/ring)')
for n in men+walkers:
    m=gmask(n)
    if m.sum()<50: print(n,'tiny',m.sum()); continue
    m8=m.astype(np.uint8)
    inner=cv2.erode(m8,np.ones((7,7),np.uint8)).astype(bool)
    ring=(cv2.dilate(m8,np.ones((61,61),np.uint8)).astype(bool))&~cv2.dilate(m8,np.ones((13,13),np.uint8)).astype(bool)
    allmen=np.zeros_like(m)
    for k in men+walkers: allmen|=gmask(k)
    ring&=~allmen
    out=[]
    for lab,a in [('plate',plate),('painting',paint)]:
        L=lum(a); fi=L[inner].mean(); ri=L[ring].mean()
        out.append(f'{lab}: fig {fi:5.1f} ring {ri:5.1f} ratio {fi/ri:4.2f}')
    print(f'{n:16s} px {m.sum():6d} | '+' | '.join(out), '| coat RGB plate',plate[inner].mean(0).round(0),'painting',paint[inner].mean(0).round(0))
np.save('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-looks/allmen.npy',np.any([gmask(k) for k in men+walkers],axis=0))
