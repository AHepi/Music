# What this does: tests reading and writing a geometry-nodes modifier's inputs through mod.properties in Blender 5.2.2.
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
path = sys.argv[sys.argv.index('--') + 1]
with bpy.data.libraries.load(path, link=False) as (s, d):
    d.objects = ['CT / Complete ceramic roof', 'CT / Seated chiseled stone']
for o in d.objects:
    bpy.context.scene.collection.objects.link(o)
    for mod in o.modifiers:
        if mod.type != 'NODES': continue
        p = mod.properties
        print('MODIFIER', o.name, '|', mod.name, type(p), 'keys', list(p.keys()))
        for s in mod.node_group.interface.items_tree:
            if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name != 'Geometry':
                ident = s.identifier
                try:
                    cur = p[ident]; p[ident] = cur
                    print('  OK', s.name, ident, repr(cur))
                except Exception as e:
                    print('  FAIL', s.name, ident, e)
