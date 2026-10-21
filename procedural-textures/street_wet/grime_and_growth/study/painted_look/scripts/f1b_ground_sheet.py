"""'How much grime is too much?'  Synthetic grime is laid over a real painting (round 2 wet painting, the latest) at several coverages and strengths, the result is put through the
film stage's finishing step (scale, curve, grain), and we count what is lost: area pushed to black, and how much of the street's own structure (sett joints, brick courses,
window frames) is still told apart.  The grime here is only a stand-in made of soft noise: it tests the tone and area budget, not any real recipe."""
import sys; sys.path.insert(0,'scripts')
from common import *
from stage_curve import *
import json
rng=np.random.default_rng(3)
PAINT=WORK+"/lockout_wet_r2_painting_registered.png"
P=load_rgb(PAINT)
M=lockout_masks()
walls=erode(M['walls']|M['roofs'],5); ground=erode(M['road']|M['pavement']|M['kerb']|M['gutter'],5)
def fbm(h,w,scales,weights,aspect=1.0,seed=0):
    r=np.random.default_rng(seed); out=np.zeros((h,w),np.float32)
    for s,wt in zip(scales,weights):
        n=r.standard_normal((h//8+2,w//8+2)).astype(np.float32)
        n=cv2.resize(n,(w,h),interpolation=cv2.INTER_CUBIC)
        sx=s; sy=s*aspect
        n=cv2.GaussianBlur(n,(0,0),sigmaX=max(0.5,sx),sigmaY=max(0.5,sy))
        n/=n.std()+1e-6; out+=wt*n
    return out/np.sqrt(sum(w_*w_ for w_ in weights))
# one soft field for the ground, one streaky (vertical) field for the walls
Fg=fbm(H,W,[10,28,70],[0.4,0.6,0.8],1.0,seed=1)
Fw=fbm(H,W,[3,8,20],[0.5,0.7,0.6],6.0,seed=2)       # streaky: stretched along the picture's vertical
def mask_cov(F,cov):
    thr=np.quantile(F,1-cov); m=np.clip((F-thr)/0.6+0.5,0,1)   # soft edge about 0.6 sigma wide
    return m.astype(np.float32)
def film_view(img):
    sc=1.281; Mx=np.array([[sc,0,768-sc*540],[0,sc,1365-sc*960]],np.float32)
    v=np.stack([cv2.warpAffine(img[...,i],Mx,(1080,1920),flags=cv2.INTER_AREA|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT) for i in range(3)],-1)
    yy,xx=np.mgrid[0:1920,0:1080]; edge=smoothstep(0.85,0.2,np.sqrt(((xx/1080-0.5)*0.9)**2+(yy/1920-0.5)**2)*1.25)
    o=stage_rgb(v,LOOK_LOCKOUT,edge[...,None])
    o=np.clip(o+0.022,0,1)
    n=(np.random.default_rng(5).random((1920,1080,1))-0.5)*0.035*(1-0.6*o)
    return np.clip(o+n,0,1)
def warp_mask(m):
    sc=1.281; Mx=np.array([[sc,0,768-sc*540],[0,sc,1365-sc*960]],np.float32)
    return cv2.warpAffine(m.astype(np.uint8)*255,Mx,(1080,1920),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP)>127
wallsF=warp_mask(walls); groundF=warp_mask(ground)
base=film_view(P); Lb=lum(base)
def metrics(film):
    L=lum(film); out={}
    for nm,m in (('walls',wallsF),('ground',groundF)):
        out[nm]=dict(black_share=float((L[m]<0.03).mean()),dark_share=float((L[m]<0.06).mean()),mean=float(L[m].mean()))
        # structure kept: correlation of the 3-10 px band with the un-grimed film view
        a=dog(Lb,2.0); b=dog(L,2.0)
        out[nm]['structure_corr']=float(np.corrcoef(a[m],b[m])[0,1])
        out[nm]['structure_rms_ratio']=float(b[m].std()/a[m].std())
    return out
ladder=[]
levels=[('0 none',0,1.0),('1 light  (10% of area, to 80%)',0.10,0.80),('2 medium (25%, to 65%)',0.25,0.65),('3 heavy  (45%, to 50%)',0.45,0.50),('4 smothered (70%, to 40%)',0.70,0.40)]
res={}
tiles=[]
for nm,cov,fac in levels:
    G=P.copy()
    if cov>0:
        mw=mask_cov(Fw,cov)*walls; mg=mask_cov(Fg,cov)*ground
        k=(mw+mg)[...,None]
        G=P*(1-k*(1-fac))        # darkening grime (soot) on walls and ground
    film=film_view(G)
    res[nm]=metrics(film)
    tiles.append((nm,film))
    print(nm, json.dumps({k:{kk:round(vv,3) for kk,vv in v.items()} for k,v in res[nm].items()}))

# sheet: lower-middle crop of each level at film size, side by side
crops=[]
for nm,film in tiles:
    c=(film[1240:1880,60:1020]*255+.5).astype(np.uint8)
    crops.append((nm,c))
import PIL.Image as Image, PIL.ImageDraw as ImageDraw
ww=480; hh=320
sheet=Image.new('RGB',(ww*3+20,(hh+22)*2+10),(20,20,20)); d=ImageDraw.Draw(sheet)
for i,(nm,c) in enumerate(crops[:5]):
    im=Image.fromarray(c).resize((ww,hh),Image.LANCZOS)
    x=(i%3)*(ww+10); y=(i//3)*(hh+32)
    sheet.paste(im,(x,y+20)); d.text((x+3,y+4),nm,fill=(255,255,255))
sheet.save(WORK+"/f1_ladder_dark_sheet_ground.jpg",quality=88)
Image.fromarray((tiles[0][1]*255+.5).astype(np.uint8)).save(WORK+"/f1_film_level0.jpg",quality=90)
Image.fromarray((tiles[3][1]*255+.5).astype(np.uint8)).save(WORK+"/f1_film_level3.jpg",quality=90)
