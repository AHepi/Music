import numpy as np, cv2, json
from PIL import Image
exec(open('hollow_probe.py').read().split('for k,(pp')[0])
tiles=[]
for k,(pp,F,g) in cases.items():
    a=cv2.imread(pp)
    facts=json.load(open(F+'facts.json'))
    ids=np.asarray(Image.open(F+'ids.png').convert('RGB')).astype(int)
    vis=(np.abs(ids-np.array(facts['groups'][g]['colour'])).sum(-1)<24)
    ys,xs=np.nonzero(vis); s=1536/1080
    l,t,r,b=int(xs.min()*s)-20,int(ys.min()*s)-20,int(xs.max()*s)+20,int(ys.max()*s)+20
    c=a[t:b,l:r]; c=cv2.resize(c,(400,int(400*c.shape[0]/c.shape[1])))
    tiles.append(c)
    # painting
pt=cv2.imread('/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/people-test-painting.png')
h=max(t.shape[0] for t in tiles)
out=np.hstack([np.pad(t,((0,h-t.shape[0]),(0,10),(0,0))) for t in tiles])
cv2.imwrite('hollow-crops.png',out)
