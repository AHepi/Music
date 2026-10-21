import sys, os, json
KIT = 'proc-work/kits/weathering'
sys.path.insert(0, KIT); sys.dont_write_bytecode = True
import bpy, numpy as np
from apply import kit as kit_module
from harness import cameras, render
from masks import bus as bus_module
from walls import apply_walls
args = sys.argv[sys.argv.index('--') + 1:]
out = args[2]; layer = args[3]; cam = args[4]; parts = args[5].split(',')
os.makedirs(out, exist_ok=True)
k = kit_module.Kit.load(args[0], scene_id=args[1], strict=False); bus_module.attach(k); apply_walls.register(k)
cams, _ = cameras.make_all(k.settings, args[1]); camera = cams[cam]
k.prepare(); k.apply(layers=[layer])
res = {}
for part in parts:
    render.plain_light(True)
    undo = apply_walls.show_part(k, layer, part)
    render.draw(out + '/p.png', 240, 180, 1, camera, raytracing=False)
    undo(); render.plain_light(False)
    a = render.read(out + '/p.png')
    res[part] = dict(finite=bool(np.isfinite(a).all()), min=float(np.nanmin(a)), max=float(np.nanmax(a)), mean=float(np.nanmean(a)))
    print('PART', part, res[part], flush=True)
