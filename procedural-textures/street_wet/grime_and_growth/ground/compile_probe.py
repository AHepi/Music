import sys, os, json, time
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
import bpy
from harness import runner as R, cameras
from ground import ground_common as gc
out=sys.argv[sys.argv.index('--')+1]
r=R.Runner(dict(set='pit_village_street', scene='street', pack=True, feature_dirs=[], jobs=[]), out)
r.set_look('base'); r.kit.set_state(0.85,0.5)
bpy.context.scene.camera=r.cams['main']
def draw(tag):
    r.eevee(540,960,16)
    bpy.context.scene.render.filepath=f'{out}/p.png'
    t=time.time(); bpy.ops.render.render(write_still=True); return time.time()-t
print('PROBE base first', round(draw('base'),2), 'second', round(draw('base'),2), flush=True)
orig=gc.elements_for_material
tests=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'compile_tests.json')))
for layer, sets in tests.items():
    for els in sets:
        gc.elements_for_material=lambda kit,key,mat,els=els: tuple(els)
        for k in list(r.kit.active): r.kit.remove(k)
        r.kit.apply(layers=[layer]); r.kit.set_state(0.85,0.5)
        t1=draw('a'); t2=draw('b')
        print('PROBE', layer, els, 'first', round(t1,2), 'second', round(t2,2), flush=True)
