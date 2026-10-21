# What this does (plain words): STUDY ONLY, saves nothing. Looks for the add-on's own bookkeeping on the saved courtyard scene: does any object carry an open "surface transaction"
# (the add-on's undo handle for pigment / detail / textile), and which custom properties do the add-on's objects and materials carry? Tells the kit what it must not disturb.
# Run: blender -b --disable-autoexec FILE --python c12_addon_marks.py -- OUT.json
import json, sys
from collections import Counter
import bpy
out = sys.argv[sys.argv.index('--') + 1]
objs = Counter(); mats = Counter(); trans = []
for o in bpy.data.objects:
    for k in o.keys():
        objs[k] += 1
        if k == 'astra_surface_transaction': trans.append(o.name)
for m in bpy.data.materials:
    for k in m.keys(): mats[k] += 1
res = {'object_custom_properties': dict(objs), 'material_custom_properties': dict(mats), 'objects_with_open_surface_transaction': trans,
       'restore_handles': [o.name for o in bpy.data.objects if o.get('astra_kind') == 'surface'], 'meshes_with_CT_rest': sum(1 for me in bpy.data.meshes if 'CT_rest' in me.attributes)}
json.dump(res, open(out, 'w'), indent=1); print(json.dumps(res, indent=1)[:1500])
