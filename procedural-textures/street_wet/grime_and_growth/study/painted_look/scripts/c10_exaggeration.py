import sys; sys.path.insert(0,'scripts')
import c7_specific_match as C
from common import *
import json
a=json.load(__import__('gzip').open(NUM+'/c7_marks.json.gz')); b={}
def rows_of(keys): 
    out=[]
    for k in keys: out+= (a if k in a else b)[k]
    return out
FULL=[k for k in a if 'full-size' in k]; SMALL=[k for k in a if 'small input' in k]
for label,keys in (('FULL',FULL),('SMALL',SMALL)):
    R=rows_of(keys); ok,ch=C.judge(R)
    S=np.array([r['plate'] for r in R]); P=np.array([r['paint'] for r in R]); Wd=np.array([r['width'] for r in R]); E=np.array([r['elong'] for r in R])
    print(label)
    for (wlo,whi) in [(0,2.5),(2.5,4.5),(4.5,8),(8,14)]:
        for slo,shi in [(0.03,0.06),(0.06,0.12),(0.12,1)]:
            s=ok&(Wd>=wlo)&(Wd<whi)&(S>=slo)&(S<shi)
            if s.sum()>=10:
                r=P[s]/S[s]
                print("  width %4.1f-%4.1f, plate contrast %.2f-%.2f: n=%4d  painted contrast / plate contrast: median %.2f  (p25 %.2f, p75 %.2f)"%(wlo,whi,slo,shi,s.sum(),np.median(r),np.percentile(r,25),np.percentile(r,75)))
