# What this does: lists the attributes of a geometry-nodes modifier in Blender 5.2.2 (read only).
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
path = sys.argv[sys.argv.index('--') + 1]
with bpy.data.libraries.load(path, link=False) as (s, d):
    d.objects = ['CT / Complete ceramic roof']
o = d.objects[0]
bpy.context.scene.collection.objects.link(o)
mod = o.modifiers.get('CT / Shared roof controls')
print('TYPE', type(mod))
print('ATTRS', [a for a in dir(mod) if not a.startswith('_')])
for a in ('inputs', 'input_values', 'node_group_inputs'):
    if hasattr(mod, a): print('HAS', a, getattr(mod, a))
print('VERSION', bpy.app.version_string)
