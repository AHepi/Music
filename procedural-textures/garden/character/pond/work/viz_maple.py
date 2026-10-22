import sys
P0='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/pond'
sys.path.insert(0,P0); sys.path.insert(0,P0+'/work')
import numpy as np
import sil, g6p_trees as T
from PIL import Image, ImageDraw
d=np.load(P0+'/work/old_maple.npz')
new=T.maple_crown(seed=31, hue_target=(d['hue'].mean(), d['hue'].std()))
cols=[(230,80,60),(240,160,40),(80,200,90),(60,170,230),(170,90,220),(230,230,80),(120,120,120)]
trunk,roots,B=T.maple_skeleton()
for cam in ('photo','veranda'):
    W=900
    u0,v0,z0,W_,H,f=sil.project(np.zeros((1,3)),cam,W)
    img=np.zeros((H,W,3),np.uint8)
    # old silhouette outline in dark blue
    mo=sil.disc_mask(d['P'], d['scale'][:,0]*1.5*0.5*0.85, cam, W)
    img[mo]=(40,40,90)
    for pi in range(len(T.MAPLE_PADS)):
        sel=new['PAD']==pi
        m=sil.disc_mask(new['P'][sel], new['SIZE'][sel]*0.5*0.85, cam, W)
        img[m]=np.array(cols[pi])*0.8
    im=Image.fromarray(img); dr=ImageDraw.Draw(im)
    for i,path in enumerate([trunk]+B):
        p=np.array(path)[:,:3]; u,v,z,_,_,_=sil.project(p,cam,W)
        dr.line([(float(a),float(b)) for a,b in zip(u,v)], fill=(255,255,255) if i==0 else (255,255,0), width=2)
        dr.text((float(u[-1]),float(v[-1])), str(i-1) if i>0 else 'T', fill=(255,255,255))
    im.save(P0+'/work/maple_viz_%s.png'%cam)
