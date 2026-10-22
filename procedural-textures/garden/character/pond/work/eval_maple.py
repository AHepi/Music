import sys
P0='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond'
sys.path.insert(0,P0); sys.path.insert(0,P0+'/work')
import numpy as np, importlib
import sil, g6p_trees as T
from PIL import Image
importlib.reload(T)
d=np.load(P0+'/work/old_maple.npz')
old_u=d['hue']; 
def masks(P, size, cam, skel=True, extra_r=0.85):
    r=size*0.5*extra_r
    ml=sil.disc_mask(P,r,cam,600)
    mb=np.zeros_like(ml)
    if skel:
        trunk,roots,B=T.maple_skeleton()
        for path in [trunk]+B:
            p=np.array(path); mb|=sil.tube_mask(p[:,:3],p[:,3],cam,600)
    return ml, mb
res={}
for cam in ('photo','veranda'):
    ml0,_=masks(d['P'], d['scale'][:,0]*1.5, cam, skel=False)
    tr=[(-6.7,1.3,-0.05),(-6.65,1.2,0.95),(-6.15,1.05,1.85),(-5.55,1.2,2.6),(-5.0,1.45,3.25)]
    mt=sil.tube_mask(tr,[0.2,0.165,0.13,0.095,0.06],cam,600)
    # old branches
    old=ml0|mt
    res[cam]=old
new=T.maple_crown(seed=31, hue_target=(old_u.mean(), old_u.std()))
print("new leaves", len(new['P']), "U mean %.3f std %.3f (old %.3f %.3f)"%(new['U'].mean(),new['U'].std(),old_u.mean(),old_u.std()))
out=[]
for cam in ('photo','veranda'):
    ml,mb=masks(new['P'], new['SIZE'], cam)
    sn=ml|mb
    so=res[cam]
    print(cam, "old area %.4f new area %.4f ratio %.3f IoU %.3f  inter/old %.3f; leaf-only new %.4f; branch px visible (not under leaves) %d"%(so.mean(), sn.mean(), sn.sum()/so.sum(), sil.iou(so,sn), (so&sn).sum()/so.sum(), ml.mean(), (mb&~ml).sum()))
    img=np.zeros(so.shape+(3,),np.uint8); img[so]=(90,90,255); img[sn&~so]=(255,90,90); img[so&sn]=(200,200,200); img[mb&~ml&sn]=(60,255,60)
    out.append(Image.fromarray(img))
W=Image.new('RGB',(1200,400)); W.paste(out[0],(0,0)); W.paste(out[1],(600,0)); W.save(P0+'/work/maple_compare.png')

# per-branch visible pixels (not covered by leaves)
trunk,roots,B=T.maple_skeleton()
for cam in ('photo','veranda'):
    ml,_=masks(new['P'], new['SIZE'], cam, skel=False)
    vis=[]
    for i,path in enumerate(B):
        p=np.array(path); mb=sil.tube_mask(p[:,:3],p[:,3],cam,600)
        vis.append(int((mb&~ml).sum()))
    p=np.array(trunk); mt=sil.tube_mask(p[:,:3],p[:,3],cam,600)
    print(cam,"visible branch px:", vis, "trunk px", int((mt&~ml).sum()), "branches with >=150 px:", sum(v>=150 for v in vis))
