# What this does: probes how Blender 5.2.2 stores geometry-nodes modifier inputs for the Astra roof asset (read only).
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
path = sys.argv[sys.argv.index('--') + 1]
with bpy.data.libraries.load(path, link=False) as (s, d):
    d.objects = ['CT / Complete ceramic roof']
o = d.objects[0]
bpy.context.scene.collection.objects.link(o)
mod = o.modifiers.get('CT / Shared roof controls')
print('MOD', mod, mod.type, 'keys:', list(mod.keys())[:20])
for s in mod.node_group.interface.items_tree:
    if s.item_type == 'SOCKET' and s.in_out == 'INPUT':
        print('SOCKET', repr(s.name), s.identifier, s.socket_type, 'current:', mod.get(s.identifier, 'MISSING'), type(mod.get(s.identifier)))
for name, val in [('Socket_2', 4.2)]:
    pass
# try writing each kind
import traceback
for s in mod.node_group.interface.items_tree:
    if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name != 'Geometry':
        try:
            cur = mod[s.identifier]
            mod[s.identifier] = cur
            print('WRITE OK', s.name, s.identifier)
        except Exception as e:
            print('WRITE FAIL', s.name, s.identifier, type(cur) if 'cur' in dir() else None, e)
