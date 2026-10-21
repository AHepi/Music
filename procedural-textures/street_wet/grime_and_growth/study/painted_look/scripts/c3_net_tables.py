import sys; sys.path.insert(0,'scripts')
from common import *
import json
d=json.load(open(NUM+'/c1_feature_survival.json'))
ks=[3,5,7,9,13,17,25,33,49]
names={3:'1-2',5:'3-4',7:'5-6',9:'7-8',13:'9-12',17:'13-16',25:'17-24',33:'25-32',49:'33-48'}
bins=[(0.015,0.03),(0.03,0.06),(0.06,0.12),(0.12,0.24),(0.24,1.0)]
def pooled(pairs,regionkey_by_pair,dark):
    tab={}
    for k in ks:
        for b in bins:
            S=C=N=0
            for p in pairs:
                reg=regionkey_by_pair[p]
                rows=d[p].get(reg,[])
                for x in rows:
                    if x['dark']==dark and x['k']==k and abs(x['depth_lo']-b[0])<1e-6:
                        S+=x['survive']*x['n']; C+=x['chance']*x['n']; N+=x['n']
            tab[(k,b)]=(S/N,C/N,N) if N>=100 else None
    return tab
def show(title,tab):
    print(title)
    print("width px  "+"".join(f"   depth {lo:.3f}-{hi:.2f}  " for lo,hi in bins))
    for k in ks:
        line=f"{names[k]:>8}  "
        for b in bins:
            v=tab[(k,b)]
            if v is None: line+="        -         "
            else:
                s,c,n=v; net=(s-c)/(1-c)
                line+=f"  net {net*100:4.0f}% ({s*100:2.0f}/{c*100:2.0f})  "
        print(line)
full_all={'lockout_dry':'all','corner_dry':'all','people_dry':'all'}
full_ground={'lockout_dry':'ground (road, pavement, kerb, gutter)','corner_dry':'lower half (ground)','people_dry':'lower half (ground)'}
small_all={'lockout_wet':'all','lockout_wet_r2':'all'}
small_ground={'lockout_wet':'ground (road, pavement, kerb, gutter)','lockout_wet_r2':'ground (road, pavement, kerb, gutter)'}
for dark in (True,False):
    tag='DARK' if dark else 'BRIGHT'
    show(f"=== FULL-SIZE plate sent to painter (3 dry pairs pooled) | whole picture | {tag} features: net survival (raw survive / chance)",pooled(['lockout_dry','corner_dry','people_dry'],full_all,dark))
    show(f"=== FULL-SIZE | ground only | {tag}",pooled(['lockout_dry','corner_dry','people_dry'],full_ground,dark))
    show(f"=== SMALL plate (0.53 size) sent (wet pair) | whole picture | {tag}",pooled(['lockout_wet','lockout_wet_r2'],small_all,dark))
    show(f"=== SMALL | ground only | {tag}",pooled(['lockout_wet','lockout_wet_r2'],small_ground,dark))
