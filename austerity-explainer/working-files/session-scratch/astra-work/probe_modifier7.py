# What this does: reads and writes one modifier input value on the Astra roof in Blender 5.2.2.
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
path = sys.argv[sys.argv.index('--') + 1]
with bpy.data.libraries.load(path, link=False) as (s, d):
    d.objects = ['CT / Complete ceramic roof', 'CT / Seated chiseled stone']
for o in d.objects:
    bpy.context.scene.collection.objects.link(o)
    mod = [m for m in o.modifiers if m.type == 'NODES'][0]
    ins = mod.properties.inputs
    for s in mod.node_group.interface.items_tree:
        if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name != 'Geometry':
            it = getattr(ins, s.identifier)
            print('INPUT', o.name, s.name, s.identifier, [a for a in dir(it) if not a.startswith('_') and a not in ('bl_rna','rna_type')], 'value=', getattr(it, 'value', 'NOVALUE'))
            if hasattr(it, 'value'):
                old = it.value; it.value = old
                print('   write-back OK')
