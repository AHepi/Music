import sys; sys.path.insert(0,'scripts')
import c7_specific_match as C
from common import *
import json
a=json.load(__import__('gzip').open(NUM+'/c7_marks.json.gz')); b={}
FULL=[k for k in a if 'full-size' in k]
SMALL=[k for k in a if 'small input' in k]
print("full-size sets:",FULL); print("small sets:",SMALL)
def pool(keys,src):
    rows=[]
    for k in keys:
        for r in (a if k in a else b)[k]: rows.append(r)
    return rows
cb=[0.02,0.03,0.04,0.06,0.08,0.12,0.20,1.0]
wb=[(0,2.5),(2.5,4.5),(4.5,8),(8,14),(14,60)]
res={}
def table(rows,label,kind):
    ok,ch=C.judge(rows)
    W_=np.array([r['width'] for r in rows]); E_=np.array([r['elong'] for r in rows]); S_=np.array([r['plate'] for r in rows])
    sel0=(E_<2.5) if kind=='specks' else (E_>=4)
    print(f"\n=== {label} | {kind} | share that come back (n)")
    print("plate contrast: "+"".join(f"{cb[i]:.2f}-{cb[i+1]:.2f}".rjust(13) for i in range(len(cb)-1)))
    T={}
    for (wlo,whi) in wb:
        line=f"width {wlo:>4.1f}-{whi:>4.1f} px "
        for i in range(len(cb)-1):
            s=sel0&(W_>=wlo)&(W_<whi)&(S_>=cb[i])&(S_<cb[i+1])
            if s.sum()>=12:
                line+=f"{100*ok[s].mean():4.0f}% ({s.sum():>4})".rjust(13); T[f"{wlo}-{whi}|{cb[i]}-{cb[i+1]}"]=(float(ok[s].mean()),int(s.sum()))
            else: line+="          -  "
        print(line)
    res[f"{label}|{kind}"]=T
full=pool(FULL,a); small=pool(SMALL,a)
print(len(full),len(small))
for kind in ('specks','lines'):
    table(full,'FULL-SIZE plate sent (dry corner, lockout, people)',kind)
    table(small,'SMALL plate sent (0.53; wet lockout rounds 1 and 2)',kind)
json.dump(res,open(NUM+'/c9_pooled.json','w'),indent=1)
