# What this does (plain words): assembles the size classes of the fitted description from the layers: S0 = layout only; S = layout + procedural wear
# (noise layers, thresholds fitted by calibrate_wear.py); M and L = layout + traced regions chosen by gain per byte (trace_select.py) with an 8-colour
# palette, with the byte budget of the class. Writes description/S0.json, S.json, M.json, L.json (compact) and runs the audit on each.
# Analysis only (the traced regions are measured from the reference). Run: python3 -I build_descriptions.py
import json, os, subprocess, sys
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0,HERE); sys.path.insert(0,HERE+'/../generator')
import trace_select as ts, metal_shapes as ms, preview_tools as pt
D=PROC+'/recipes/metal/description/'
layout=json.load(open(D+'layout_v0.json'))
def dump(d,name):
    json.dump(d,open(D+name,'w'),separators=(',',':'))
    r=subprocess.run(['python3','-I',PROC+'/lib/description_audit.py',D+name,'--limit-kilobytes','512'],capture_output=True,text=True)
    print(name,os.path.getsize(D+name),'bytes |',r.stdout.strip().replace('\n',' | ')[:200])
dump(layout,'S0.json')
# S: layout + calibrated procedural wear (copied from the tuned trial), without the calibration targets
trial=json.load(open(PROC+'/recipes/metal/outputs/trial_final/description.json'))
proc=trial['procedural']
for l in proc['layers']: l.pop('targets',None); l.pop('name',None); l.pop('cover_all',None) if False else None
S=dict(layout); S['procedural']=proc
dump(S,'S.json')
ref=cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1]
pal=json.load(open(HERE+'/palette_k8.json'))['rgb']
canvas=pt.paint_stack(ms.build_stack(layout))
healed=ts.heal_seam(ref.copy())
cands=ts.candidates_wrapped(healed,canvas,pal,min_area=8)
print('candidates',len(cands))
base_bytes=os.path.getsize(D+'S0.json')+len(json.dumps([[int(round(v)) for v in c] for c in pal],separators=(',',':')))+40
for cls,limit in (('M',64*1024),('L',512*1024)):
    budget=limit-base_bytes-200
    regions,used=ts.select(cands,budget)
    d=dict(layout); d['regions']=[regions[i:i+60] for i in range(0,len(regions),60)];       # stored in chunks of 60 outlines (same order); see the guide, section on the audit
    d['patch_colours']=[[int(round(v)) for v in c] for c in pal]
    dump(d,cls+'.json'); print(cls,'regions',len(regions))
