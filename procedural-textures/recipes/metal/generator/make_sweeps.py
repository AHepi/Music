# What this does (plain words): makes the "what does this setting do" pictures for the guide. Each sweep takes the fitted description, changes ONE setting through
# five values, bakes a small (384 dots) colour picture for each with the real generator, and saves them as tile_00.png ... plus sweep.json (labels). Then
# lib/make_strip.py joins them into one labelled strip. Run inside Blender:
#   blender -b --disable-autoexec -t 2 --python make_sweeps.py -- [sweep names...]
# Sweeps: wear_size, rust_amount, streak_length, edge_attraction, grain, layers (add _zoom to a name, e.g. grain_zoom, for a full-size 300 x 300 window) (what each layer of the description adds)
import copy, json, os, sys
import bpy
HERE=os.path.dirname(os.path.abspath(__file__)); PROC=os.path.abspath(os.path.join(HERE,'..','..','..')); R=PROC+'/recipes/metal'
sys.path.insert(0,HERE)
import metal_generator as mg
S=json.load(open(R+'/description/S.json'))
L=json.load(open(R+'/description/L.json'))
OUT=R+'/guide_pictures'
SIZE=384
def run(name,variants,base=None,size=None,crop=None):
    folder=f'{OUT}/sweep_{name}'; os.makedirs(folder,exist_ok=True); files=[]; labels=[]
    for i,(label,change) in enumerate(variants):
        d=copy.deepcopy(base or S); change(d)
        tmp=f'{folder}/_t{i}'
        mg.bake_description(d,tmp,size=size or SIZE,samples=4,quiet=True,channels=('colour',))
        if crop:                                   # keep only a window (x0, y0, width, height in dots) of a full-size bake, to show fine detail
            picture=mg.bh.load_png_as_array(tmp+'/colour.png'); x0,y0,w,h=crop
            mg.bh.save_array_png(picture[y0:y0+h,x0:x0+w],f'{folder}/tile_{i:02d}.png')
        else:
            os.replace(tmp+'/colour.png',f'{folder}/tile_{i:02d}.png')
        files.append(f'tile_{i:02d}.png'); labels.append(label)
        for f in os.listdir(tmp): os.remove(tmp+'/'+f)
        os.rmdir(tmp)
    json.dump({'files':files,'labels':labels},open(folder+'/sweep.json','w'))
    print('sweep',name,'done',flush=True)
def layer(d,i): return d['procedural']['layers'][i]
def set_rust_scale(u):
    def f(d): layer(d,1)['fine']['scale_u']=u; layer(d,1)['fine']['scale_v']=round(u*0.68,1)
    return f
def set_offset(o):
    def f(d): layer(d,1)['offset']=o
    return f
def set_scale_v(v):
    def f(d): layer(d,1)['fine']['scale_v']=v
    return f
def set_edge(g):
    def f(d): layer(d,1)['edge_gain']=g
    return f
def set_grain(a):
    def f(d): d['procedural']['grain']['amount']=a
    return f
def layers_variants():
    def plate_only(d): d['bands']=[dict(b,a=None,b_=None) for b in d['bands']]; d['rivets']=[]; d.pop('procedural',None)
    def faces(d):
        for b in d['bands']: b['a']=None; b['b']=None
        d['rivets']=[]; d.pop('procedural',None)
    def profiles(d): d['rivets']=[]; d.pop('procedural',None)
    def full_layout(d): d.pop('procedural',None)
    return [('1 plate + bar faces',faces),('2 + edge shading',profiles),('3 + rivets, seams',full_layout),('4 + procedural wear',lambda d:None)]
which=(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []) or ['wear_size','rust_amount','streak_length','edge_attraction','grain','layers']
sweeps={
 'wear_size':[(f'rust size {u}',set_rust_scale(u)) for u in (15,25,44,80,140)],
 'rust_amount':[(f'rust offset {o:+.2f}',set_offset(o)) for o in (-0.10,-0.05,0.0,0.05,0.10)],
 'streak_length':[(f'rust up-scale {v}',set_scale_v(v)) for v in (8,16,30,60,110)],
 'edge_attraction':[(f'edge gain {g}',set_edge(g)) for g in (0.0,0.15,0.3,0.6,1.0)],
 'grain':[(f'grain {a}',set_grain(a)) for a in (0.0,0.04,0.08,0.16,0.3)],
}
ZOOM=dict(size=1254,crop=(40,470,300,300))      # a 300 x 300 window at full size around the crossing of the left vertical and the middle horizontal strap
for n in which:
    if n=='layers': run('layers',layers_variants())
    elif n.endswith('_zoom'): run(n,sweeps[n[:-5]],**ZOOM)
    else: run(n,sweeps[n])
