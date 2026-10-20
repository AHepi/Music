# What this does (plain words): experiment: traces the M-size patches on a copy of the reference whose seam was healed (trace_select.heal_seam) and prints the scores, to see what healing costs.
import sys, json, os, time
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0,HERE); sys.path.insert(0,HERE+'/../generator')
import trace_select as ts, metal_shapes as ms, preview_tools as pt
ref=cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1].copy()
healed=ts.heal_seam(ref)
cv2.imwrite(PROC+'/recipes/metal/analysis/ref_healed.png',healed[...,::-1])
desc=json.load(open(PROC+'/recipes/metal/description/layout_v0.json'))
pal=json.load(open(HERE+'/palette_k8.json'))['rgb']
canvas=pt.paint_stack(ms.build_stack(desc))
t0=time.time(); cands=ts.candidates_wrapped(healed,canvas,pal,min_area=8); print('candidates',len(cands),round(time.time()-t0,1))
for budget in (57000,):
    regions,used=ts.select(cands,budget)
    d=dict(desc); d['regions']=regions; d['patch_colours']=[[int(round(v)) for v in c] for c in pal]
    img=pt.paint_stack(ms.build_stack(d)); out=PROC+'/recipes/metal/scores/heal_M'
    pt.write_map_set(img,out,desc['maps']); pixel,tex=pt.compare(out,sheet=False)
    print(budget,len(regions),'|',pt.summary_line(pixel,tex),'| tiling',tex['groups']['tiling'])
