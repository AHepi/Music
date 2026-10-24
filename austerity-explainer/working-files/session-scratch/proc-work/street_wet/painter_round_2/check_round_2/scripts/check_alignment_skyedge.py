"""Checker's own alignment test that does not use the film's lining-up tool or phase correlation on paint texture:
the sky mask drawn by Blender gives the exact place of the roof lines, chimney and headframe edges against the sky.
For a picture, look at how strong the picture's own edge is ON those mask edges after moving the picture by (sx, sy) dots; the best (sx, sy) is where the picture's edges sit on Blender's edges.
Uses only pictures where the sky differs clearly from the buildings (the as-returned painting, before the free sky was put in)."""
import cv2, numpy as np
RR='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/'
cov=cv2.imread(RR+'paint/work/sky/sky_coverage_1536x2730.png',0).astype(np.float32)/255
cs=cv2.GaussianBlur(cov,(0,0),1.0)
gx=cv2.Sobel(cs,cv2.CV_32F,1,0); gy=cv2.Sobel(cs,cv2.CV_32F,0,1)
mag=np.sqrt(gx*gx+gy*gy)
ys,xs=np.where(mag>0.25*mag.max()); print('boundary points',len(ys))
# keep only long edges, avoid image border
sel=(ys>30)&(ys<2700)&(xs>30)&(xs<1500); ys,xs=ys[sel],xs[sel]
def edge_strength(path, resize=None):
    im=cv2.imread(path,0)
    if resize is not None: im=cv2.resize(im,(1536,2730),interpolation=cv2.INTER_AREA)
    a=cv2.GaussianBlur(im.astype(np.float32)/255,(0,0),1.2)
    ex=cv2.Sobel(a,cv2.CV_32F,1,0); ey=cv2.Sobel(a,cv2.CV_32F,0,1)
    return np.sqrt(ex*ex+ey*ey)
def best_shift(E, rng=5, step=0.5):
    res={}
    for sy in np.arange(-rng,rng+0.01,step):
        for sx in np.arange(-rng,rng+0.01,step):
            # picture content shifted by (sx,sy) -> sample the edge map at (x - sx, y - sy)
            M=np.float32([[1,0,sx],[0,1,sy]])
            Es=cv2.warpAffine(E,M,(1536,2730),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
            res[(sx,sy)]=float(Es[ys,xs].mean())
    k=max(res,key=res.get); return k,res[k],res[(0,0)]
for name,path,rs in (('as returned (resized only)','paint/pictures/front_painting_as_returned.png',True),
                     ('their lined-up version','paint/front_painting_lined_up.png',None),
                     ('behind as returned (resized only)','behind/pictures/behind_painting_as_returned.png',True),
                     ('behind lined up (their tool)','paint/behind_painting_lined_up.png',None)):
    E=edge_strength(RR+path,rs)
    k,v,v0=best_shift(E)
    print('%-36s best extra move of the picture to sit on Blender edges: dx %+.1f dy %+.1f dots (edge strength %.3f vs %.3f unmoved)'%(name,k[0],k[1],v,v0))
