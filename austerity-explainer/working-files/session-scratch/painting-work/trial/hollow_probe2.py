import numpy as np, cv2, json
from PIL import Image
exec(open('hollow_probe.py').read().split('for k,(pp')[0])
for k,(pp,F,g) in cases.items():
    a=cv2.imread(pp)[...,::-1].astype(np.float32)
    H,W=a.shape[:2]
    facts=json.load(open(F+'facts.json'))
    ids=np.asarray(Image.open(F+'ids.png').convert('RGB')).astype(int)
    vis=(np.abs(ids-np.array(facts['groups'][g]['colour'])).sum(-1)<24).astype(np.uint8)
    vis=cv2.resize(vis,(W,H),interpolation=cv2.INTER_NEAREST).astype(bool)
    ys,xs=np.nonzero(vis); top=ys.min(); h=ys.max()-top+1
    topm=vis&(np.arange(H)[:,None]<top+0.3*h)
    L=0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
    body=vis&~topm
    bodyL=np.median(L[body])
    for thr in (1.5,2.0,2.5):
        glow=topm&(L>thr*bodyL)
        print(k,'body median L %.1f'%bodyL,'thr x%.1f'%thr,'glow share of top30 %.3f'%glow.mean() if False else 'glow px %d share %.3f of top30, %.4f of frame'%(glow.sum(),glow.sum()/topm.sum(),glow.sum()/(H*W)), 'glow L mean %.1f'%(L[glow].mean() if glow.any() else 0))
    hsv=cv2.cvtColor(np.clip(a,0,255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(float)
    print('   top30 V p99 %.2f S at those %.2f'%(np.percentile(hsv[...,2][topm],99)/255, np.median(hsv[...,1][topm&(hsv[...,2]>=np.percentile(hsv[...,2][topm],95))])/255))
