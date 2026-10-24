# What this does: inspects mod.properties.inputs of a geometry-nodes modifier in Blender 5.2.2 (read, then a test write).
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
path = sys.argv[sys.argv.index('--') + 1]
with bpy.data.libraries.load(path, link=False) as (s, d):
    d.objects = ['CT / Complete ceramic roof', 'CT / Seated chiseled stone']
for o in d.objects:
    bpy.context.scene.collection.objects.link(o)
    mod = [m for m in o.modifiers if m.type == 'NODES'][0]
    ins = mod.properties.inputs
    print('INPUTS', o.name, type(ins), len(ins), [a for a in dir(ins) if not a.startswith('_')][:30])
    for i, item in enumerate(ins):
        print('  ITEM', i, type(item).__name__, [a for a in dir(item) if not a.startswith('_')][:14])
        break
    for key in range(len(ins)):
        it = ins[key]
        print('  ', key, getattr(it, 'name', None), getattr(it, 'identifier', None), getattr(it, 'value', 'novalue'))
