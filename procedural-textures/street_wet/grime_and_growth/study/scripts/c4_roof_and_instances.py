# What this does (plain words): STUDY ONLY, saves nothing. Counts the little copies (instances) that the geometry-nodes roof makes, says what each copy is made of
# and how big the roof's evaluated mesh is, and lists the timber material the roof hands out. Answers: can a layer see the roof tiles?
# Run: blender -b --disable-autoexec FILE --python c4_roof_and_instances.py -- OUT.json
import json, sys
from collections import Counter
import bpy, numpy as np
out = sys.argv[sys.argv.index('--') + 1]
deps = bpy.context.evaluated_depsgraph_get()
inst = Counter(); mats = {}
for oi in deps.object_instances:
    if oi.is_instance:
        parent = oi.parent.name if oi.parent else None
        key = (parent, oi.object.name, oi.object.type)
        inst[key] += 1
        if key not in mats:
            ms = [s.material.name if s.material else None for s in oi.object.material_slots]
            mats[key] = {'materials': ms, 'faces': len(oi.object.data.polygons) if oi.object.type == 'MESH' else None,
                         'dims': [round(v, 3) for v in oi.object.dimensions], 'scale': [round(v, 3) for v in oi.matrix_world.to_scale()]}
res = {'instances': [{'parent': k[0], 'object': k[1], 'type': k[2], 'count': n, **mats[k]} for k, n in inst.most_common()]}
roof = bpy.data.objects['Hall roof']
ev = roof.evaluated_get(deps)
me = ev.to_mesh()
res['roof_evaluated_mesh'] = {'faces': len(me.polygons), 'verts': len(me.vertices), 'materials': [m.name if m else None for m in me.materials],
                              'attributes': [(a.name, a.domain, a.data_type) for a in me.attributes]}
ev.to_mesh_clear()
res['roof_modifier_inputs'] = {}
for md in roof.modifiers:
    try:
        res['roof_modifier_inputs'][md.name] = {k: str(md[k])[:80] for k in md.keys() if not k.endswith('_use_attribute') and not k.endswith('_attribute_name')}
    except Exception as e:
        res['roof_modifier_inputs'][md.name] = str(e)
# stones: attributes of an evaluated stone
st = bpy.data.objects['Rock 0']; ev = st.evaluated_get(deps); me = ev.to_mesh()
res['rock0_evaluated'] = {'faces': len(me.polygons), 'verts': len(me.vertices), 'attributes': [(a.name, a.domain, a.data_type) for a in me.attributes], 'materials': [m.name if m else None for m in me.materials]}
ev.to_mesh_clear()
# timber material the roof hands out
tm = bpy.data.materials.get('CT / Timber painterly surface')
if tm:
    res['timber_material'] = {'groups': [n.node_tree.name for n in tm.node_tree.nodes if n.bl_idname == 'ShaderNodeGroup' and n.node_tree],
                              'props': {k: str(tm[k])[:100] for k in tm.keys()}, 'nodes': [n.bl_idname.replace('ShaderNode', '') + ':' + n.name for n in tm.node_tree.nodes]}
# all materials: how many carry the add-on's custom properties, and the ones with 'ct_material_role'
roles = Counter()
for m in bpy.data.materials:
    if m.get('ct_material_role'): roles[m['ct_material_role']] += 1
res['ct_material_roles'] = dict(roles)
res['n_materials'] = len(bpy.data.materials)
json.dump(res, open(out, 'w'), indent=1, default=str)
print('DONE')
