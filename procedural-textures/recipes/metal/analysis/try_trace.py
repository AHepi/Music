# What this does (plain words): first tracing experiment: keeps every patch above an area limit (4 settings) and prints the scores. Superseded by try_select.py (gain per byte), kept as a record.
import sys, json, os, time
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0,HERE); sys.path.insert(0,HERE+'/../generator')
import trace_regions as tr, metal_shapes as ms, preview_tools as pt
ref=cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1]
desc=json.load(open(PROC+'/recipes/metal/description/layout_v0.json'))
pal=json.load(open(HERE+'/palette_k16.json'))['rgb']
canvas=pt.paint_stack(ms.build_stack(desc))
maps=desc['maps']
for min_area,eps in ((400,2.5),(150,1.8),(60,1.2),(25,1.0)):
    t0=time.time()
    patches=tr.trace(ref,canvas,pal,min_area,eps)
    enc=tr.encode(patches)
    size=len(json.dumps(enc,separators=(',',':')))
    d=dict(desc); d['patches']=enc; d['patch_colours']=[[int(round(v)) for v in c] for c in pal]
    img=pt.paint_stack(ms.build_stack(d))
    out=PROC+f'/recipes/metal/scores/trace_a{min_area}_e{eps}'
    pt.write_map_set(img,out,maps)
    pixel,tex=pt.compare(out,sheet=False,texture=True)
    print(min_area,eps,'patches',len(enc),'bytes',size,'|',pt.summary_line(pixel,tex),'|',round(time.time()-t0,1),'s')
