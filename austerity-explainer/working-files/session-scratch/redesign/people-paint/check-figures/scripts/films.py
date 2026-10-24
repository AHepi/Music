import numpy as np, cv2, json
from PIL import Image
F='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-figures/frames/'
O='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-figures/'
def L(k,i):
    return np.array(Image.open(f'{F}{k}/f{i:03d}.png').convert('RGB')).astype(np.float32)
def lum(a):  # relative luminance, sRGB linearised
    c=a/255.0; c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4)
    return 0.2126*c[...,0]+0.7152*c[...,1]+0.0722*c[...,2]
p59=L('painted',59); p60=L('painted',60); s60=L('sil',60); s59=L('sil',59)
d=np.abs(s60-p60).mean(2)
M=(cv2.GaussianBlur(d,(0,0),1.0)>18).astype(np.uint8)
M=cv2.morphologyEx(M,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
n,lab,st,cen=cv2.connectedComponentsWithStats(M)
keep=np.zeros_like(M)
comps=[]
for i in range(1,n):
    x,y,w,h,a=st[i]
    if a>150 and y>700 and y<1500:
        keep[lab==i]=1; comps.append((int(x),int(y),int(w),int(h),int(a)))
Image.fromarray(keep*255).save(O+'masks/film-figures-f60.png')
print('figure blobs (x,y,w,h,area) at frame 60:',sorted(comps))
ring=cv2.dilate(keep,np.ones((25,25),np.uint8))-cv2.dilate(keep,np.ones((5,5),np.uint8))
inner=cv2.erode(keep,np.ones((5,5),np.uint8))
def measure(img,name):
    Y=lum(img)
    fi=Y[inner>0]; bg=Y[ring>0]
    g=cv2.cvtColor(img.astype(np.uint8),cv2.COLOR_RGB2GRAY).astype(np.float32)
    lap=np.abs(cv2.Laplacian(g,cv2.CV_32F,ksize=3))
    r=dict(fig_lum=float(fi.mean()),bg_lum=float(bg.mean()),weber=float((bg.mean()-fi.mean())/bg.mean()),ratio=float((bg.mean()+0.05)/(fi.mean()+0.05)),
           fig_gray_mean=float(g[inner>0].mean()),fig_gray_std=float(g[inner>0].std()),fig_detail=float(lap[inner>0].mean()),bg_detail=float(lap[ring>0].mean()))
    print(f"{name:28s} figure lum {r['fig_lum']:.4f}  surround {r['bg_lum']:.4f}  weber {r['weber']:.2f}  ratio {r['ratio']:.2f}  inside grey {r['fig_gray_mean']:.1f}±{r['fig_gray_std']:.1f}  inner detail {r['fig_detail']:.2f} (surround {r['bg_detail']:.2f})")
    return r
res={}
res['painted_full']=measure(p59,'painted f59 full size')
res['sil_full']=measure(s59,'silhouettes f59 full size')
# phone size 360 wide
def small(img): return cv2.resize(img,(360,640),interpolation=cv2.INTER_AREA)
ks=cv2.resize(keep,(360,640),interpolation=cv2.INTER_AREA)
keep_s=(cv2.resize(keep.astype(np.float32),(360,640),interpolation=cv2.INTER_AREA)>0.5).astype(np.uint8)
ring_s=cv2.dilate(keep_s,np.ones((9,9),np.uint8))-cv2.dilate(keep_s,np.ones((3,3),np.uint8))
inner_s=cv2.erode(keep_s,np.ones((3,3),np.uint8))
def measure_s(img,name):
    a=small(img); Y=lum(a); g=cv2.cvtColor(a.astype(np.uint8),cv2.COLOR_RGB2GRAY).astype(np.float32)
    fi=Y[inner_s>0]; bg=Y[ring_s>0]
    # edge strength along figure boundary
    gx=cv2.Sobel(g,cv2.CV_32F,1,0); gy=cv2.Sobel(g,cv2.CV_32F,0,1); gm=np.hypot(gx,gy)
    edge=cv2.dilate(keep_s,np.ones((3,3),np.uint8))-cv2.erode(keep_s,np.ones((3,3),np.uint8))
    r=dict(fig_lum=float(fi.mean()),bg_lum=float(bg.mean()),ratio=float((bg.mean()+0.05)/(fi.mean()+0.05)),edge_strength=float(gm[edge>0].mean()),inside_std=float(g[inner_s>0].std()))
    print(f"{name:28s} figure lum {r['fig_lum']:.4f}  surround {r['bg_lum']:.4f}  ratio {r['ratio']:.2f}  boundary edge {r['edge_strength']:.1f}  inside grey spread {r['inside_std']:.1f}")
    return r
res['painted_phone']=measure_s(p59,'painted f59 at 360 wide')
res['sil_phone']=measure_s(s59,'silhouettes f59 at 360 wide')
json.dump(res,open(O+'film-figure-contrast.json','w'),indent=1)
