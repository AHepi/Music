# What this does (plain words): tracing experiment: ranks every candidate patch by gain per byte, keeps the best until a byte budget is used and prints the scores of the result (preview painted with OpenCV).
import sys, json, os, time
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0,HERE); sys.path.insert(0,HERE+'/../generator')
import trace_select as ts, metal_shapes as ms, preview_tools as pt
ref=cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1]
desc=json.load(open(PROC+'/recipes/metal/description/layout_v0.json')); desc['maps']=json.load(open(PROC+'/recipes/metal/description/maps_rule.json'))
pal=json.load(open(HERE+'/palette_k24.json'))['rgb']
canvas=pt.paint_stack(ms.build_stack(desc))
t0=time.time(); cands=ts.candidates(ref,canvas,pal,min_area=8); print('candidates',len(cands),round(time.time()-t0,1),'s')
for budget in (300000,):
    regions,used=ts.select(cands,budget)
    d=dict(desc); d['regions']=regions; d['patch_colours']=[[int(round(v)) for v in c] for c in pal]
    img=pt.paint_stack(ms.build_stack(d)); out=PROC+f'/recipes/metal/scores/sel_{budget}'
    pt.write_map_set(img,out,desc['maps']); pixel,tex=pt.compare(out,sheet=False)
    print(budget,'regions',len(regions),'bytes',used,'|',pt.summary_line(pixel,tex))
