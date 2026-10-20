# What this does (plain words): finds the colour palette of the reference: k-means in the Lab colour space (so colours that look alike are grouped) for 8, 12, 16,
# 24 and 32 colours, and prints how far (Delta E 76) the average dot is from its nearest palette colour. Writes palette_k8.json ... palette_k32.json (colours sorted
# dark to light) and, for 16 colours, the "label picture" labels_k16.npy (which palette colour each dot is closest to; used only by the analysis scripts).
# Note: the palette files used by the final descriptions (palette_k8.json etc.) came from earlier runs of this same method with different random starting points; running this again gives
# slightly different colours, not different accuracy. Analysis only (it reads the reference). Run: python3 -I palette_fit.py
import json, os
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
c=cv2.imread(PROC+'/reference/metal/colour.png')
flat=cv2.cvtColor(c.astype(np.float32)/255.0,cv2.COLOR_BGR2LAB).reshape(-1,3)        # true Lab (L 0..100)
rng=np.random.default_rng(1); sample=flat[rng.choice(len(flat),200000,replace=False)]
def nearest(cent):
    out=np.zeros(len(flat),np.int32); err=np.zeros(len(flat),np.float32)
    for i in range(0,len(flat),200000):
        d=((flat[i:i+200000,None,:]-cent[None,:,:])**2).sum(-1); out[i:i+200000]=d.argmin(1); err[i:i+200000]=np.sqrt(d.min(1))
    return out,err
for K in (8,12,16,24,32):
    crit=(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,80,0.1)
    _,_,cent=cv2.kmeans(sample,K,None,crit,3,cv2.KMEANS_PP_CENTERS)
    idx,err=nearest(cent)
    rgb=cv2.cvtColor(cent.reshape(1,-1,3).astype(np.float32),cv2.COLOR_LAB2RGB).reshape(-1,3)*255
    order=np.argsort(rgb.sum(1))
    print('K',K,'mean Delta E to the nearest palette colour',round(float(err.mean()),2))
    json.dump({'rgb':rgb[order].round(1).tolist()},open(HERE+f'/palette_k{K}.json','w'))
    if K==16:
        share=np.bincount(idx,minlength=K)/len(flat)
        json.dump({'rgb':rgb.round(1).tolist(),'share':share.round(4).tolist()},open(HERE+'/palette_k16.json','w'))   # unsorted: indices match labels_k16.npy
        np.save(HERE+'/labels_k16.npy',idx.reshape(1254,1254).astype(np.uint8))
