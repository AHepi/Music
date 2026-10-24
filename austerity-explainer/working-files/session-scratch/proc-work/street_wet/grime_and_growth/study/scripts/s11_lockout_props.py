# What this does (plain words): STUDY ONLY, saves nothing. In the lockout shot file, lists the meshes that are not in the street copy (the props) and which collection each one sits in, so
# "what is a prop" can be told from the file's own collections instead of from a saved list of street object names.
import json, sys
from collections import Counter, defaultdict
import bpy
street = set(l.split()[0] for l in open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/relief_and_rubbish/rubbish/work/objects_street.txt') if l.strip())
by_col = defaultdict(list)
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and o.name not in street:
        by_col[o.users_collection[0].name if o.users_collection else None].append(o.name)
res = {k: dict(n=len(v), sample=v[:8]) for k, v in by_col.items()}
# materials on props in the 'signs' collection (these keep their own lettering)
signs = defaultdict(set)
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and o.users_collection and o.users_collection[0].name == 'signs':
        for s in o.material_slots:
            if s.material:
                signs[o.name].add(s.material.name)
res['signs_materials'] = {k: sorted(v) for k, v in signs.items()}
# which street objects are also in collections props/signs (should be none)
res['street_objects_in_props_or_signs'] = [o.name for o in bpy.context.scene.objects if o.name in street and o.users_collection and o.users_collection[0].name in ('props', 'signs')][:5]
# shared materials between props and street
street_mats = set()
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and o.name in street:
        street_mats |= {s.material.name for s in o.material_slots if s.material}
prop_mats = set()
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and o.name not in street:
        prop_mats |= {s.material.name for s in o.material_slots if s.material}
res['materials_used_by_props_only'] = len(prop_mats - street_mats)
res['materials_shared_street_and_props'] = sorted(prop_mats & street_mats)
json.dump(res, open(sys.argv[sys.argv.index('--') + 1], 'w'), indent=1)
