# Probes the dressed Works: where the handcart's bed is, and what the crates on it rest on.
import bpy
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
for name in ('handcart', 'handcart-crate-1', 'handcart-crate-2', 'no-2-crate-3', 'w4-upturned-crate', 'tin-mug-and-wages', 'jacket-and-cap', 'brazier-drum', 'hurricane-lantern', 'lunch-tin'):
    o = bpy.data.objects.get(name)
    print('PROBE', name, tuple(round(v, 3) for v in o.matrix_world.translation) if o else None)
cart = bpy.data.objects['handcart']
for dy in (-0.9, -0.5, 0.0, 0.5, 0.9):
    for dx in (0.0,):
        hit = bpy.context.scene.ray_cast(dg, Vector((cart.location.x + dx, cart.location.y + dy, 3.0)), Vector((0, 0, -1)))
        print('PROBE cart ray', dy, round(hit[1].z, 3) if hit[0] else None, hit[4].name if hit[0] else None)
