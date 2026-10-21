import sys; sys.path.insert(0,'scripts')
from common import *
import c1_feature_survival as C
import json
allres={}
for name in PAIRS:
    if name.startswith('lockout'):
        M=lockout_masks()
        ys=np.nonzero(M['road'].any(axis=1))[0]; y0,y1=ys.min(),ys.max(); th=[y0,y0+(y1-y0)//3,y0+2*(y1-y0)//3,y1+1]
        def rb(m,a,b): r=np.zeros_like(m); r[a:b]=m[a:b]; return r
        regions={'pavement flags':erode(M['pavement'],9),'setts near':erode(rb(M['road'],th[2],th[3]),9),'setts middle':erode(rb(M['road'],th[1],th[2]),9),'setts far':erode(rb(M['road'],th[0],th[1]),9),
                 'walls':erode(M['walls'],9),'kerb and gutter':erode(M['kerb']|M['gutter'],5)}
    elif name=='corner_dry':
        yy,xx=np.mgrid[0:H,0:W]
        regions={'pavement flags':(xx>=880)&(xx<=1500)&(yy>=2120)&(yy<=2700),'setts near':(xx>=0)&(xx<=640)&(yy>=1900)&(yy<=2700),
                 'right wall':(xx>=1200)&(yy<=1700)}
    else:
        continue
    allres[name]=C.run(name,regions)
    print(name,'done',flush=True)
json.dump(allres,open(NUM+'/c1b_feature_survival_regions.json','w'),indent=1)
