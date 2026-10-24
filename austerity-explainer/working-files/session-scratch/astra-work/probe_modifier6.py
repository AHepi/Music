# What this does: finds how to read and write a node-group input on a modifier in Blender 5.2.2.
import bpy, sys
bpy.ops.wm.read_factory_settings(use_empty=True)
path = sys.argv[sys.argv.index('--') + 1]
with bpy.data.libraries.load(path, link=False) as (s, d):
    d.objects = ['CT / Complete ceramic roof']
o = d.objects[0]
bpy.context.scene.collection.objects.link(o)
mod = o.modifiers['CT / Shared roof controls']
ins = mod.properties.inputs
print('ATTRS', [a for a in dir(ins) if not a.startswith('_')])
print('RNA', [p.identifier for p in ins.bl_rna.properties])
print('FUNCS', [f.identifier for f in ins.bl_rna.functions])
for ident in ('Socket_2', 'Width'):
    for how in ('getitem', 'getattr', 'get'):
        try:
            v = ins[ident] if how == 'getitem' else (getattr(ins, ident) if how == 'getattr' else ins.get(ident))
            print('READ OK', how, ident, repr(v), type(v))
        except Exception as e:
            print('READ FAIL', how, ident, type(e).__name__, e)
