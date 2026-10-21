"""Marks in a plate (dark or bright, found by a top-hat) and whether the painting has the SAME mark.
For every mark the plate's own contrast is measured as (ring around the mark) - (the mark itself); the painting's contrast is measured on the same shape,
looking in a +-2 pixel neighbourhood and taking the best.  The same is done for the shape moved to 12 other places 30 to 90 pixels away: that is how big a
contrast the painter's own brush marks give by chance.  A mark 'comes back' when the painting's best contrast at the true place is at least half the plate's,
at least 0.02, and bigger than 90% of the chance values.  The chance rate is the share of the moved copies that would pass the first two tests."""
import sys; sys.path.insert(0,'scripts')
from common import *
import json
rng=np.random.default_rng(7)
def disc(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(k,k))
OFFS=[]
for r in (35,55,75,90):
    for a in range(0,360,90):
        OFFS.append((int(r*np.cos(np.radians(a+r))),int(r*np.sin(np.radians(a+r)))))
OFFS=OFFS[:12]
def marks(A,region,dark,kmax,thr,maxarea=4000):
    f=(cv2.morphologyEx(A,cv2.MORPH_CLOSE,disc(kmax))-A) if dark else (A-cv2.morphologyEx(A,cv2.MORPH_OPEN,disc(kmax)))
    mask=((f>thr)&region).astype(np.uint8)
    n,lab,stats,cent=cv2.connectedComponentsWithStats(mask,connectivity=8)
    out=[]
    for i in range(1,n):
        x,y,w,h,area=stats[i]
        if area<5 or area>maxarea or w>150 or h>150: continue
        out.append((i,x,y,w,h,area))
    return lab,out
def signal(img,compfull,ringfull,dark):
    c=img[compfull].mean(); r=img[ringfull].mean()
    return (r-c) if dark else (c-r)
def run(name,region,dark,kmax=17,thr=0.03):
    p,q=PAIRS[name]
    A=lum(load_rgb(p)); B=lum(load_rgb(WORK+f"/{name}_painting_registered.png"))
    lab,items=marks(A,region,dark,kmax,thr)
    rows=[]
    m=12
    for (i,x,y,w,h,area) in items:
        if x<100 or y<100 or x+w>W-100 or y+h>H-100: continue
        x0,y0=x-m,y-m; x1,y1=x+w+m,y+h+m
        comp=(lab[y0:y1,x0:x1]==i)
        core=comp
        dt=cv2.distanceTransform(comp.astype(np.uint8),cv2.DIST_L2,3); width=2*dt.max()
        ring=cv2.dilate(comp.astype(np.uint8),disc(11))>0; ring&=~(cv2.dilate(comp.astype(np.uint8),disc(3))>0)
        if ring.sum()<8: continue
        cpts=cv2.findNonZero(comp.astype(np.uint8)); (cx,cy),(rw,rh),ang=cv2.minAreaRect(cpts); length=max(rw,rh); thick=max(1.0,min(rw,rh))
        Ap=A[y0:y1,x0:x1]; sp=signal(Ap,comp,ring,dark)
        def best_at(dx,dy):
            xa,ya,xb,yb=x0+dx,y0+dy,x1+dx,y1+dy
            if xa<4 or ya<4 or xb>W-4 or yb>H-4: return None
            big=B[ya-3:yb+3,xa-3:xb+3]
            bst=-9
            for ddx in (-2,-1,0,1,2):
                for ddy in (-2,-1,0,1,2):
                    sub=big[3+ddy:3+ddy+(y1-y0),3+ddx:3+ddx+(x1-x0)]
                    s=signal(sub,comp,ring,dark)
                    if s>bst: bst=s
            return bst
        sb=best_at(0,0)
        ch=[v for v in (best_at(dx,dy) for dx,dy in OFFS) if v is not None]
        if sb is None or len(ch)<6: continue
        rows.append(dict(x=int(x),y=int(y),width=float(width),length=float(length),elong=float(length/thick),plate=float(sp),paint=float(sb),chance=[float(c) for c in ch]))
    return rows
def judge(rows,minfrac=0.5,minabs=0.02):
    ok=[];chance=[]
    for r in rows:
        need=max(minfrac*r['plate'],minabs)
        ch=np.array(r['chance'])
        ok.append(bool(r['paint']>=need and r['paint']>np.percentile(ch,90)))
        chance.append(float((ch>=need).mean()))
    return np.array(ok),np.array(chance)
def report(rows,label):
    print("-----",label,"marks:",len(rows))
    if not rows: return {}
    ok,chance=judge(rows)
    W_=np.array([r['width'] for r in rows]); E_=np.array([r['elong'] for r in rows]); S_=np.array([r['plate'] for r in rows])
    res={}
    for kind,sel in (("specks (length < 2.5 x width)",E_<2.5),("lines (length >= 4 x width)",E_>=4)):
        print(" ",kind)
        for wlo,whi in [(0,2.5),(2.5,4.5),(4.5,8),(8,14),(14,60)]:
            for slo,shi in [(0.02,0.04),(0.04,0.08),(0.08,0.2),(0.2,1)]:
                s=sel&(W_>=wlo)&(W_<whi)&(S_>=slo)&(S_<shi)
                if s.sum()<8: continue
                res[f"{kind}|w{wlo}-{whi}|c{slo}-{shi}"]=dict(n=int(s.sum()),back=float(ok[s].mean()),chance=float(chance[s].mean()))
                print("    width %4.1f-%4.1f px, plate contrast %.2f-%.2f: n=%4d  come back %3.0f%%   chance pass rate %3.0f%%"%(wlo,whi,slo,shi,s.sum(),100*ok[s].mean(),100*chance[s].mean()))
    return res
if __name__=='__main__':
    out={}
    yy,xx=np.mgrid[0:H,0:W]
    jobs=[]
    flags=(xx>=880)&(xx<=1500)&(yy>=2120)&(yy<=2700)&~((xx<1220)&(yy<2250))
    jobs.append(('corner_dry',flags,'corner pavement flags (full-size input)'))
    jobs.append(('corner_dry',(xx<=640)&(yy>=1900)&(yy<=2700),'corner setts, near (full-size input)'))
    M=lockout_masks()
    jobs.append(('lockout_dry',erode(M['road']|M['pavement']|M['kerb']|M['gutter'],7),'lockout ground (full-size input)'))
    jobs.append(('lockout_wet',erode(M['road']|M['pavement']|M['kerb']|M['gutter'],7),'lockout ground (small input, wet)'))
    jobs.append(('lockout_dry',erode(M['walls'],9),'lockout walls (full-size input)'))
    jobs.append(('lockout_wet',erode(M['walls'],9),'lockout walls (small input, wet)'))
    jobs.append(('people_dry',(yy>=H*0.6),'people-test ground (full-size input)'))
    jobs.append(('lockout_wet_r2',erode(M['road']|M['pavement']|M['kerb']|M['gutter'],7),'lockout round 2 ground (small input, wet)'))
    jobs.append(('lockout_wet_r2',erode(M['walls'],9),'lockout round 2 walls (small input, wet)'))
    allrows={}
    for name,reg,lab in jobs:
        for dark in (True,False):
            rows=run(name,reg,dark)
            key=f"{lab} | {'dark' if dark else 'bright'}"
            allrows[key]=rows
            out[key]=report(rows,key)
    json.dump(allrows,open(NUM+'/c7_marks.json','w'))
    json.dump(out,open(NUM+'/c7_report.json','w'),indent=1)
