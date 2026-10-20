# NOTE (plain words): my own re-measure of some of the helper's numbers, done a different way from the helper:
#  (1) is the brightest road brighter than the notice paper? (helper: 1.21 times, using the notice's 80th-percentile brightness)
#  (2) how much of the sky is bright cloud? (helper: 19 % of sky clearly brighter than the plate's sky)
#  (3) do the bright reflection patches on the road sit in the same places as in the plate? (helper: overlap 0.63 vs 0.04 dry)
#  (4) how much darker is the wet painting's road than the dry painting's road? (helper: 0.72 times)
# It reads pictures only (nothing in the film project is changed) and prints numbers. Run: python3 -I remeasure_numbers.py
import numpy as np, cv2, json, sys
B='proc-work/street_wet/painter_test'
SW='proc-work/street_wet/work/r35/main_wet_plate.png'
W,H=1080,1920
def load(p): return cv2.resize(cv2.imread(p),(W,H),interpolation=cv2.INTER_AREA)
def lum(im):  # Rec.709 on plain (not linear) pixel values, same convention as the helper so numbers are comparable
    b,g,r=[im[:,:,i].astype(np.float32)/255 for i in range(3)]; return 0.2126*r+0.7152*g+0.0722*b
pics={'plate_wet':load(SW),'paint_wet':load(B+'/pictures/wet_painting_lined_up.png'),'paint_dry':load('/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout-painted.jpg')}
L={k:lum(v) for k,v in pics.items()}
def solo(path):
    a=cv2.imread(path); return a.max(axis=2)>100
road=solo(B+'/alignment/facts_surfaces/solo/road.png'); notice=solo(B+'/alignment/facts/solo/notice.png')
er=lambda m,n=5: cv2.erode(m.astype(np.uint8),np.ones((n,n),np.uint8))>0
road_e=er(road); notice_e=er(notice,5)
print('road px',int(road_e.sum()),'notice px',int(notice_e.sum()))
res={}
print('\n(1) brightness of notice paper vs brightest road (1080x1920)')
for k in L:
    n=L[k][notice_e]; r=L[k][road_e]
    d={'notice_p50':np.percentile(n,50),'notice_p80':np.percentile(n,80),'notice_p95':np.percentile(n,95),'notice_max':n.max(),
       'road_p99':np.percentile(r,99),'road_p99.9':np.percentile(r,99.9),'road_max':r.max(),
       'road_share_over_notice_p80':(r>np.percentile(n,80)).mean(),'road_share_over_notice_p95':(r>np.percentile(n,95)).mean(),'road_share_over_notice_max':(r>n.max()).mean()}
    res[k]=d; print(k,{a:round(float(b),4) for a,b in d.items()})
print('ratio road_p99.9 / notice_p80 :',{k:round(float(res[k]['road_p99.9']/res[k]['notice_p80']),3) for k in res})
print('ratio road_p99.9 / notice_p95 :',{k:round(float(res[k]['road_p99.9']/res[k]['notice_p95']),3) for k in res})
print('ratio road_p99.9 / notice_max :',{k:round(float(res[k]['road_p99.9']/res[k]['notice_max']),3) for k in res})
# (2) sky: use the top 17 % of the picture (rows 0..326), leave out the left 18 % (chimney and rope) and right 12 %, so no roofs or props are in it
import glob
cov=np.zeros((H,W),bool)
for f in glob.glob(B+'/alignment/facts/solo/*.png')+glob.glob(B+'/alignment/facts_surfaces/solo/*.png'):
    cov|=cv2.imread(f).max(axis=2)>20
cov=cv2.dilate(cov.astype(np.uint8),np.ones((9,9),np.uint8))>0
skym=(~cov); skym[int(0.45*H):]=False
print('\n(2) sky = pixels no Blender mask covers (grown by 9 px), above 45 percent of the height: ',int(skym.sum()),'px =',round(float(skym[:int(0.45*H)].mean()),3),'of that band')
y1=int(0.17*H); xs=slice(int(0.18*W),int(0.88*W))
base=cv2.GaussianBlur(L['plate_wet'],(0,0),40)
for k in L:
    s=L[k][skym]
    print(k,'mean',round(float(s.mean()),3),'share>0.45',round(float((s>0.45).mean()),3),'share>0.6',round(float((s>0.6).mean()),3),'share brighter than plate sky by 0.12',round(float(((L[k]-base)[skym]>0.12).mean()),3),'share brighter than 0.12 over own blurred sky',round(float(((L[k]-cv2.GaussianBlur(L[k],(0,0),40))[skym]>0.12).mean()),3))
# (3) bright reflection patches: use 24x24 block averages inside the road, top-decile blocks, overlap; independent of the helper's blur-and-percentile
bs=24
def blocks(Lk):
    h=H//bs; w=W//bs; return Lk[:h*bs,:w*bs].reshape(h,bs,w,bs).mean(axis=(1,3))
rb=(cv2.resize(road_e.astype(np.uint8),(W//bs,H//bs),interpolation=cv2.INTER_AREA)>0.9)
print('\n(3) 24 px blocks fully in the road:',int(rb.sum()))
bl={k:blocks(L[k]) for k in L}
def top(k,q=90):
    v=bl[k]; t=np.percentile(v[rb],q); return (v>=t)&rb
def iou(a,b): return float((a&b).sum()/max(1,(a|b).sum()))
def spearmanr(a,b):
    ra=np.argsort(np.argsort(a)).astype(float); rb_=np.argsort(np.argsort(b)).astype(float)
    return (np.corrcoef(ra,rb_)[0,1],)
for q in (90,80):
    print('top',100-q,'% blocks: plate vs wet painting IoU',round(iou(top('plate_wet',q),top('paint_wet',q)),3),' plate vs dry painting IoU',round(iou(top('plate_wet',q),top('paint_dry',q)),3),' (chance about',round((100-q)/100/(2-(100-q)/100),3),')')
print('Spearman rank correlation of block brightness inside road: plate~wet',round(float(spearmanr(bl['plate_wet'][rb],bl['paint_wet'][rb])[0]),3),' plate~dry',round(float(spearmanr(bl['plate_wet'][rb],bl['paint_dry'][rb])[0]),3))
# also remove the top-to-bottom trend (every road row has its own mean) so near-vs-far brightness does not do the work
def detr(v):
    o=np.zeros_like(v)
    for i in range(v.shape[0]):
        m=rb[i]
        if m.sum()>2: o[i,m]=v[i,m]-v[i,m].mean()
    return o
d={k:detr(bl[k]) for k in bl}
print('same, after taking out each row average: plate~wet',round(float(spearmanr(d['plate_wet'][rb],d['paint_wet'][rb])[0]),3),' plate~dry',round(float(spearmanr(d['plate_wet'][rb],d['paint_dry'][rb])[0]),3))
# (4) road darkness
print('\n(4) road mean brightness (not eroded mask):',{k:round(float(L[k][road].mean()),3) for k in L}, 'wet painting / dry painting =',round(float(L['paint_wet'][road].mean()/L['paint_dry'][road].mean()),3))
print('   with simple average of R,G,B instead of Rec.709:',{k:round(float(pics[k][road].mean()/255),3) for k in pics})
