# verifier: re-bake two of the guide's sweeps with the CURRENT S.json and generator into verify/sweep_check (never touches guide_pictures)
import copy, json, os, sys
import bpy
M='proc-work/recipes/metal'
sys.path.insert(0, M+'/generator')
import metal_generator as mg
S=json.load(open(M+'/description/S.json'))
OUT=M+'/verify/sweep_check'; os.makedirs(OUT, exist_ok=True)
def bake(name, d, i, size=384):
    tmp=f'{OUT}/_t'
    mg.bake_description(d, tmp, size=size, samples=4, quiet=True, channels=('colour',))
    os.replace(tmp+'/colour.png', f'{OUT}/{name}_{i}.png')
    for f in os.listdir(tmp): os.remove(tmp+'/'+f)
    os.rmdir(tmp)
for i,o in enumerate((-0.10,-0.05,0.0,0.05,0.10)):
    d=copy.deepcopy(S); d['procedural']['layers'][1]['offset']=o; bake('rust_amount', d, i)
for i,u in enumerate((15,25,44,80,140)):
    d=copy.deepcopy(S); l=d['procedural']['layers'][1]; l['fine']['scale_u']=u; l['fine']['scale_v']=round(u*0.68,1); bake('wear_size', d, i)
for i,v in enumerate((8,16,30,60,110)):
    d=copy.deepcopy(S); d['procedural']['layers'][1]['fine']['scale_v']=v; bake('streak_length', d, i)
print('SWEEPDONE')
