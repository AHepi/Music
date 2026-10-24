import numpy as np
def dark_lines(prof, depth, half=5):
    """local minima at least `depth` below the max of both sides within `half` px; returns positions and widths at half depth"""
    p=np.asarray(prof,float); n=len(p); pos=[]; wid=[]
    for i in range(2,n-2):
        if p[i]<=p[i-1] and p[i]<=p[i+1] and p[i]<p[i-2] and p[i]<p[i+2]:
            l=p[max(0,i-half):i].max(); r=p[i+1:i+1+half].max()
            d=min(l,r)-p[i]
            if d>=depth:
                if pos and i-pos[-1]<3: 
                    if p[i]<p[pos[-1]]: pos[-1]=i
                    continue
                pos.append(i)
                lvl=p[i]+d/2; a=i; b=i
                while a>0 and p[a]<lvl: a-=1
                while b<n-1 and p[b]<lvl: b+=1
                wid.append(b-a-1)
    return pos,wid
