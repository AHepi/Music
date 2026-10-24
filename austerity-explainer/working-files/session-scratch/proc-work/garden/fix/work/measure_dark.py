import sys
from PIL import Image
import numpy as np
S='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/'
def load(p):
    return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
def L(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
items=[('orig',S+'astra-work/out/courtyard_final.png'),('real',S+'proc-work/garden/final/renders/real_hero.png'),('painted',S+'proc-work/garden/final/renders/painted_hero.png')]
if len(sys.argv)>1:
    items=[(a.split('=')[0],a.split('=')[1]) for a in sys.argv[1:]]
for nm,p in items:
    a=load(p); l=L(a)
    print(nm,a.shape,'mean',l.mean().round(1),'dark%',[ (t, round(float((l<t).mean()*100),2)) for t in (6,10,15,20,30)], 'p5',np.percentile(l,5).round(1))
    H,W=l.shape
    box=l[int(H*0.75):, :int(W*0.233)]
    print('   lowerleft box mean',box.mean().round(1),'<10:',round(float((box<10).mean()*100),1),'p50',np.percentile(box,50).round(1), 'p10', np.percentile(box,10).round(1))
