import numpy as np, cv2, json
from PIL import Image
cases={'people':('/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/people-test/people-test-plate.jpg','/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/plate-facts/','brazier'),
'notice':('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/paint/notice-corner-plate-3.jpg','/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/final/plate-facts-3/','drum')}
for k,(pp,F,g) in cases.items():
    a=cv2.imread(pp)[...,::-1].astype(np.float32)
    a=cv2.resize(a,(1080,1920),interpolation=cv2.INTER_AREA)
    facts=json.load(open(F+'facts.json'))
    ids=np.asarray(Image.open(F+'ids.png').convert('RGB')).astype(int)
    vis=(np.abs(ids-np.array(facts['groups'][g]['colour'])).sum(-1)<24)
    solo=cv2.imread(F+'solo/'+g+'.png').max(2)>8
    for nm,m in (('visible',vis),('solo',solo)):
        ys,xs=np.nonzero(m); top=ys.min(); h=ys.max()-top+1
        topm=m&(np.arange(1920)[:,None]<top+0.3*h)
        L=0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
        hsv=cv2.cvtColor(np.clip(a,0,255).astype(np.uint8),cv2.COLOR_RGB2HSV).astype(float)
        V,S=hsv[...,2]/255,hsv[...,1]/255
        warm=(a[...,0]-a[...,2])
        whole_L=L[m].mean()
        print(k,nm,'top30 px',int(topm.sum()),'L mean %.1f p95 %.1f max %.1f'%(L[topm].mean(),np.percentile(L[topm],95),L[topm].max()),
              'whole mean %.1f'%whole_L, 'V>0.85&S>0.6: %d'%int(((V>0.85)&(S>0.6)&topm).sum()),
              'warm>40&L>60: %d'%int(((warm>40)&(L>60)&topm).sum()), 'L>1.5x whole mean: %.3f'%((L>1.5*whole_L)[topm].mean()),
              'lower70 L %.1f'%L[m&~topm].mean())
