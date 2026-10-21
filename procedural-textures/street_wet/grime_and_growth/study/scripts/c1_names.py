# What this does: opens a Blender file and only prints object names with type, collection, face count and material names. Saves nothing.
# Run: blender -b --disable-autoexec FILE --python c1_names.py -- OUT.txt
import bpy, sys
out = sys.argv[sys.argv.index('--') + 1]
rows = []
for ob in sorted(bpy.data.objects, key=lambda o: o.name):
    cols = ','.join(c.name for c in ob.users_collection)
    mats = [s.material.name if s.material else None for s in ob.material_slots]
    nf = len(ob.data.polygons) if ob.type == 'MESH' else ''
    mods = [f'{m.type}:{m.name}' for m in ob.modifiers]
    rows.append(f'{ob.type:6s} | {ob.name} | col={cols} | faces={nf} | mats={mats} | mods={mods} | parent={ob.parent.name if ob.parent else None} | hide_render={ob.hide_render}')
open(out, 'w').write('\n'.join(rows))
print(len(rows), 'objects')
