# What this does (plain words): one quick trial of the procedural wear: takes a description with wear layers (that carry 'targets'), applies the changes
# you pass on the command line, sets the thresholds (calibrate_wear.py), bakes the colour picture in Blender and prints the wear statistics next to
# the reference's (wear_stats.py). Saves the trial under outputs/trial_NAME/ and a side-by-side crop in analysis/trial_NAME.png.
# Use:  python3 -I try_wear.py NAME 'layer index.path=value' ...      e.g.  1.fine.scale_u=44 1.mod.weight=0.45
import json, os, subprocess, sys
import cv2, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..'))
sys.path.insert(0,HERE)
import calibrate_wear as cw, wear_stats as ws
name=sys.argv[1]
base=sys.argv[2] if sys.argv[2].endswith('.json') else PROC+'/recipes/metal/description/S_v2_uncal.json'
args=[a for a in sys.argv[2:] if '=' in a]
desc=json.load(open(base))
for a in args:
    path,val=a.split('=',1); val=json.loads(val)
    parts=path.split('.'); layer=desc['procedural']['layers'][int(parts[0])]
    node=layer
    for p in parts[1:-1]: node=node.setdefault(p,{})
    node[parts[-1]]=val
desc,rep=cw.calibrate(desc,627)
out=PROC+'/recipes/metal/outputs/trial_'+name; os.makedirs(out,exist_ok=True)
json.dump(desc,open(out+'/description.json','w'))
subprocess.run([cw.BLENDER,'-b','--disable-autoexec','-t','2','--python',PROC+'/recipes/metal/generator/metal_generator.py','--',out+'/description.json',out,'--samples','4','--channels','colour'],check=True,capture_output=True)
rgb=cv2.imread(out+'/colour.png')[...,::-1]
ws.show('REFERENCE',ws.stats(cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1])); ws.show(name,ws.stats(rgb))
ref=cv2.imread(PROC+'/reference/metal/colour.png')
cv2.imwrite(HERE+f'/trial_{name}.png',np.hstack([ref[600:1100,100:600],rgb[600:1100,100:600][...,::-1]]))
