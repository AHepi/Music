"""Plain note: this script (our own, not part of Ucupaint) turns Ucupaint on inside headless Blender 5.2.2 and lists
what it added: its commands (operators) with the kinds of layer you can add. It changes nothing on disk."""
import bpy, addon_utils, sys, json, time
t0 = time.time()
mod = 'bl_ext.user_default.ucupaint'
try:
    m = addon_utils.enable(mod, default_set=True, persistent=False)
    print('ENABLE returned', m, 'in %.2fs' % (time.time()-t0))
except Exception as e:
    print('ENABLE FAILED', repr(e)); sys.exit(1)
print('enabled addons:', [a for a in bpy.context.preferences.addons.keys()])
ops = [n for n in dir(bpy.ops.wm) if n.startswith('y_')]
print('NUM wm.y_ operators', len(ops))
print(ops)
# layer types for new layer
op = bpy.ops.wm.y_new_layer
props = op.get_rna_type().properties
for p in props:
    if p.identifier in ('type','blend_type','texcoord_type','mask_type','interpolation','add_mask','mask_color'):
        if hasattr(p, 'enum_items'):
            print(p.identifier, [(i.identifier) for i in p.enum_items])
print('all y_new_layer props:', [p.identifier for p in props])
