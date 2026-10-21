import sys; sys.path.insert(0,'scripts')
from common import *
import json
d=json.load(open(NUM+'/c1b_feature_survival_regions.json'))
ks=[3,5,7,9,13,17,25,33,49]
names={3:'1-2',5:'3-4',7:'5-6',9:'7-8',13:'9-12',17:'13-16',25:'17-24',33:'25-32',49:'33-48'}
bins=[(0.015,0.03),(0.03,0.06),(0.06,0.12),(0.12,0.24),(0.24,1.0)]
def pooled(sel,dark):
    tab={}
    for k in ks:
        for b in bins:
            S=C=N=0
            for pair,reg in sel:
                for x in d.get(pair,{}).get(reg,[]):
                    if x['dark']==dark and x['k']==k and abs(x['depth_lo']-b[0])<1e-6:
                        S+=x['survive']*x['n']; C+=x['chance']*x['n']; N+=x['n']
            tab[(k,b)]=(S/N,C/N,N) if N>=60 else None
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
                s,c,n=v; net=(s-c)/(1-c); line+=f"  net {net*100:4.0f}% ({s*100:2.0f}/{c*100:2.0f},{n:>5})"
        print(line)
sets={'FLAGS full-size (corner + lockout dry pavement)':[('corner_dry','pavement flags'),('lockout_dry','pavement flags')],
      'FLAGS small-input (wet pavement)':[('lockout_wet','pavement flags'),('lockout_wet_r2','pavement flags')],
      'SETTS near, full-size':[('corner_dry','setts near'),('lockout_dry','setts near')],
      'SETTS near, small-input':[('lockout_wet','setts near'),('lockout_wet_r2','setts near')],
      'SETTS middle, full-size':[('lockout_dry','setts middle')],'SETTS middle, small-input':[('lockout_wet','setts middle'),('lockout_wet_r2','setts middle')],
      'SETTS far, full-size':[('lockout_dry','setts far')],'SETTS far, small-input':[('lockout_wet','setts far'),('lockout_wet_r2','setts far')],
      'WALLS full-size':[('corner_dry','right wall'),('lockout_dry','walls')],'WALLS small-input':[('lockout_wet','walls'),('lockout_wet_r2','walls')]}
for t,sel in sets.items():
    for dark in (True,False):
        show(f"=== {t} | {'DARK' if dark else 'BRIGHT'}",pooled(sel,dark))
