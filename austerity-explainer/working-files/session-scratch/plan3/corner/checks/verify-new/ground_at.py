# What this does: prints the first upward surface straight below some spots (set objects only), for placing moved props on the ground.
import bpy
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
skip = ('wooden-barrel', 'brazier', 'kitchen-chair', 'wooden-pail', 'gas-lamp', 'notice', 'hurricane', 'lantern', 'handcart', 'coal-sacks', 'dustbins', 'tacks')
def top(o):
    while o.parent:
        o = o.parent
    return o
for x, y in [(1.95, 21.35), (1.8, 21.2), (2.76, 22.0), (2.76, 23.5), (3.72, 30.6), (3.0, 23.25), (3.45, 23.55), (2.96, 17.85)]:
    origin = Vector((x, y, 10.0))
    for _ in range(10):
        hit, loc, nrm, i, ob, m = bpy.context.scene.ray_cast(dg, origin, Vector((0, 0, -1)))
        if not hit:
            print('GROUND', (x, y), 'nothing'); break
        if top(ob).name.startswith(skip) or ob.name.startswith(skip) or ob.hide_render:
            origin = loc - Vector((0, 0, 0.001)); continue
        print('GROUND', (x, y), round(loc.z, 4), ob.name, 'normal z', round(nrm.z, 3)); break
