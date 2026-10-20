# What this does (plain words): writes the in-between descriptions for the rate-distortion table (accuracy against size): layout pieces (bar faces only; faces + edge
# shading) and layout + traced regions at total sizes of 16, 32, 64 (that is M), 128, 256 and 512 (that is L) kilobytes. Analysis only (traced regions are measured from the reference).
import json, os, sys
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..')); D=PROC+'/recipes/metal/description/'
sys.path.insert(0,HERE); sys.path.insert(0,HERE+'/../generator')
import trace_select as ts, metal_shapes as ms, preview_tools as pt
layout=json.load(open(D+'S0.json'))
A=json.loads(json.dumps(layout)); A['rivets']=[]; A.pop('rivet',None)
for b in A['bands']: b['a']=None; b['b']=None
A['bands']=[b for b in A['bands'] if b['name'] not in ('S1','S2','S3')]
json.dump(A,open(D+'layerA.json','w'),separators=(',',':'))
B=json.loads(json.dumps(layout)); B['rivets']=[]; B.pop('rivet',None)
json.dump(B,open(D+'layerB.json','w'),separators=(',',':'))
ref=cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1].copy()
pal=json.load(open(HERE+'/palette_k8.json'))['rgb']
canvas=pt.paint_stack(ms.build_stack(layout))
cands=ts.candidates_wrapped(ts.heal_seam(ref),canvas,pal,min_area=8)
base=os.path.getsize(D+'S0.json')+200
for kb in (16,32,128,256):
    regions,used=ts.select(cands,kb*1024-base-200)
    d=dict(layout); d['regions']=[regions[i:i+60] for i in range(0,len(regions),60)]; d['patch_colours']=[[int(round(v)) for v in c] for c in pal]
    json.dump(d,open(D+f'R{kb}k.json','w'),separators=(',',':')); print(kb,'kb',len(regions),'regions',os.path.getsize(D+f'R{kb}k.json'),'bytes')
