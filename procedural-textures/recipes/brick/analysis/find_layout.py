# What this does (plain words): finds where the brick courses (rows) and the bricks sit in the reference colour picture. It looks for the thin
# dark outline lines that run along both edges of every mortar joint (a pair of dark lines about 20 dots apart), first the horizontal pairs
# (between courses), then, inside each course, the vertical pairs (between bricks). Writes layout_found.json: for each course its top and
# bottom, and for each brick its left and right edge. Analysis only (it reads the reference).
import json, cv2, numpy as np
c=cv2.imread('../../../reference/brick/colour.png')[..., ::-1].astype(float)
g=(c@np.array([.299,.587,.114])).astype(np.float32)
H=1254
def pad(a,p=40): return np.pad(a,((p,p),(p,p)),mode='wrap')
gp=pad(g)
th_h=cv2.morphologyEx(gp,cv2.MORPH_BLACKHAT,cv2.getStructuringElement(cv2.MORPH_RECT,(1,9)))[40:-40,40:-40]
th_v=cv2.morphologyEx(gp,cv2.MORPH_BLACKHAT,cv2.getStructuringElement(cv2.MORPH_RECT,(9,1)))[40:-40,40:-40]

def smooth(p,k=3):
    return np.convolve(np.concatenate([p[-k:],p,p[:k]]),np.ones(k)/k,'same')[k:-k]

def peaks(sm,thr):
    n=len(sm)
    return [i for i in range(n) if sm[i]>=sm[i-1] and sm[i]>=sm[(i+1)%n] and sm[i]>thr]

def pairs(sm,thr,gap_lo,gap_hi):
    pk=peaks(sm,thr)
    out=[]
    for a in pk:
        for b in pk:
            d=(b-a)%len(sm)
            if gap_lo<=d<=gap_hi:
                out.append((a,b,float(sm[a]+sm[b])))
    # keep strongest non-overlapping
    out.sort(key=lambda t:-t[2])
    kept=[]
    for a,b,s in out:
        if all(min(abs(a-k[0])%len(sm),abs(k[0]-a)%len(sm))>40 for k in kept):
            kept.append((a,b,s))
    return sorted(kept)

# courses: horizontal pairs from the horizontal-line profile (whole width)
prof_h=smooth(th_h.mean(1),3)
course_pairs=pairs(prof_h,9,12,32)
print('course pairs',course_pairs)
# a course = from the lower line of one pair to the upper line of the next pair
rows=[]
for i,(a,b,s) in enumerate(course_pairs):
    a2,b2,_=course_pairs[(i+1)%len(course_pairs)]
    top=b; bottom=a2 if a2>b else a2+H
    rows.append((int(top),int(bottom)))
print('rows (top,bottom)',rows)
layout={'rows':[]}
for (top,bottom) in rows:
    ys=np.arange(top+9,bottom-8)%H
    prof=smooth(th_v[ys].mean(0),3)
    jp=pairs(prof,12,12,34)
    bricks=[]
    for i,(a,b,s) in enumerate(jp):
        a2,b2,_=jp[(i+1)%len(jp)]
        left=b; right=a2 if a2>b else a2+H
        bricks.append([int(left),int(right)])
    layout['rows'].append({'top':top,'bottom':bottom,'joints':[(int(a),int(b)) for a,b,s in jp],'bricks':bricks})
    print(top,bottom,len(jp),[(a,b) for a,b,s in jp])
json.dump(layout,open('layout_found.json','w'))
