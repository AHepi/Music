import cv2, numpy as np, json
exec(open('measure.py').read().split("\nimport sys; sys.path")[0].split("print('frame mean")[0])
now=load(NOW); ref=load(REF); old=load(OLD)
G=json.load(open(B+'final/facts/facts.json'))['groups']
M={k:idm(v['colour']) for k,v in G.items()}
L=luma(now); H,W=L.shape
def rb(px): return (px[:,0]-px[:,2]).mean()
def warmidx(px):  # (R-B)/(R+B)
    return ((px[:,0]-px[:,2])/(px[:,0]+px[:,2]+1e-6)).mean()
print('== NOW notice in 6 bands, paper pixels only (luma >= band 40th pct)')
nm=M['notice']; ys,xs=np.nonzero(nm); y0,y1=ys.min(),ys.max()
edges=np.linspace(y0,y1+1,7).astype(int)
for a,b in zip(edges[:-1],edges[1:]):
    m=nm.copy(); m[:a]=False; m[b:]=False
    l=L[m]; t=np.percentile(l,40); pm=m&(L>=t); px=now[pm]
    print(f' rows {a/H:.3f}-{b/H:.3f} n={m.sum():5d} paper luma {L[pm].mean():.3f} RGB {px.mean(0)[0]*255:4.0f}{px.mean(0)[1]*255:4.0f}{px.mean(0)[2]*255:4.0f} R-B {rb(px):+.3f} (R-B)/(R+B) {warmidx(px):+.3f}  letters p2 {np.percentile(l,2):.3f}')
print('== REF notice bands, box x 0.760-0.905 (0.760-0.855 below 0.60), paper = luma>=40th pct')
Lr=luma(ref); h,w=Lr.shape
edges=np.linspace(0.462,0.645,7)
for a,b in zip(edges[:-1],edges[1:]):
    x1=0.905 if b<=0.60 else 0.855
    m=box(ref,0.760,a,x1,b); l=Lr[m]; t=np.percentile(l,40); pm=m&(Lr>=t); px=ref[pm]
    print(f' rows {a:.3f}-{b:.3f} paper luma {Lr[pm].mean():.3f} RGB {px.mean(0)[0]*255:4.0f}{px.mean(0)[1]*255:4.0f}{px.mean(0)[2]*255:4.0f} R-B {rb(px):+.3f} (R-B)/(R+B) {warmidx(px):+.3f}  letters p2 {np.percentile(l,2):.3f}')
print('== OLD notice bands, box x 0.765-0.920 (0.765-0.80 below 0.61)')
Lo=luma(old)
edges=np.linspace(0.512,0.640,7)
for a,b in zip(edges[:-1],edges[1:]):
    x1=0.92 if b<=0.61 else 0.80
    m=box(old,0.765,a,x1,b); l=Lo[m]; t=np.percentile(l,40); pm=m&(Lo>=t); px=old[pm]
    print(f' rows {a:.3f}-{b:.3f} paper luma {Lo[pm].mean():.3f} RGB {px.mean(0)[0]*255:4.0f}{px.mean(0)[1]*255:4.0f}{px.mean(0)[2]*255:4.0f} R-B {rb(px):+.3f} letters p2 {np.percentile(l,2):.3f}')

# brightest 3% after slight blur, who owns them
print('\n== brightest 3% (blur 5px) ownership')
for name,im in [('ref',ref),('old',old),('now',now)]:
    l=cv2.GaussianBlur(luma(im),(0,0),3); t=np.percentile(l,97); m=l>=t
    ys,xs=np.nonzero(m); hh,ww=l.shape
    print(f' {name}: threshold {t:.3f}, centre {xs.mean()/ww:.2f},{ys.mean()/hh:.2f}')
    if name=='now':
        tot=m.sum()
        for k in ['notice','board','drum','chair','lantern','lamp post','pail']:
            print(f'    {k:10s} {100*(m&M[k]).sum()/tot:5.1f}%')
        rest=m.copy()
        for k in M: rest&=~M[k]
        ys,xs=np.nonzero(rest); print(f'    not a prop {100*rest.sum()/tot:5.1f}% centred {xs.mean()/ww:.2f},{ys.mean()/hh:.2f}')
    # components
    n,lab,st,cen=cv2.connectedComponentsWithStats(m.astype(np.uint8))
    order=np.argsort(-st[1:,4])[:6]+1
    print('    biggest bright patches (x0,y0,x1,y1 fractions, % of frame):',
          [(round(st[i,0]/ww,2),round(st[i,1]/hh,2),round((st[i,0]+st[i,2])/ww,2),round((st[i,1]+st[i,3])/hh,2),round(100*st[i,4]/(ww*hh),2)) for i in order])
