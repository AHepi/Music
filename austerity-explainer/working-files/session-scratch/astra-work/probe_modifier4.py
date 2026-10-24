# What this does: inspects mod.properties of a geometry-nodes modifier in Blender 5.2.2 (read only).
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
path = sys.argv[sys.argv.index('--') + 1]
with bpy.data.libraries.load(path, link=False) as (s, d):
    d.objects = ['CT / Complete ceramic roof']
o = d.objects[0]
bpy.context.scene.collection.objects.link(o)
mod = o.modifiers['CT / Shared roof controls']
p = mod.properties
print('PTYPE', type(p), [a for a in dir(p) if not a.startswith('_')])
for s in mod.node_group.interface.items_tree:
    if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name != 'Geometry':
        ident = s.identifier
        for access in ('getattr', 'getitem'):
            try:
                v = getattr(p, ident) if access == 'getattr' else p[ident]
                print('READ', access, s.name, ident, repr(v))
            except Exception as e:
                print('READFAIL', access, s.name, ident, type(e).__name__, e)
