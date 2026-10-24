import bpy, sys, numpy as np
KIT='/home/user/Music/plugins/explainer-film/kit'
sys.path.insert(0, KIT+'/place-kit')
import place_kit as pk
from place_kit import parts as pkp
pkp.refresh_ground()
rng=np.random.default_rng(1)
# relief across 1.5 m footprints in forest region
rel=[];hs=[]
for _ in range(300):
    x=rng.uniform(-140,140); y=rng.uniform(-85,85)
    pts=[(x,y),(x+.7,y),(x-.7,y),(x,y+.7),(x,y-.7)]
    h=[pkp.ground_probe(*p) for p in pts]
    if any(v is None for v in h): continue
    z=[v[0] for v in h]; rel.append(max(z)-min(z)); hs.append((z[0],h[0][1]))
rel=np.array(rel); print('relief 1.4 m footprint: mean %.3f p50 %.3f p90 %.3f max %.3f'%(rel.mean(),np.median(rel),np.percentile(rel,90),rel.max()))
zs=np.array([h[0] for h in hs]); print('height range', zs.min(), zs.max())
from collections import Counter; print(Counter(h[1] for h in hs))
# overall: which ground objects cover points outside clearing? forest floor vs. roads at same xy
for p in [(-70,-10),(-100,-20),(0,-30),(0,60),(80,-30),(120,-20),(-120,50)]:
    print(p, pkp.ground_probe(*p))
