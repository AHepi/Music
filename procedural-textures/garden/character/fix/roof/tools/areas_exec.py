import bpy, json, os
res = {}
for o in bpy.data.objects:
    if o.type == 'MESH' and (o.name.startswith('G6 roof / lantern moss') or o.name.startswith('G6 roof / roof moss') or o.name.startswith('G6 roof / moss cap')):
        me = o.data
        res[o.name] = round(sum(p.area for p in me.polygons), 5)
    if o.type == 'MESH' and o.name.startswith('G6 roof / lantern moss'):
        pass
# materials colours for the lantern moss
for m in bpy.data.materials:
    if m.name in ('G6 roof / moss cap', 'G6 roof / lantern moss', 'G6 roof / roof moss'):
        res['MAT ' + m.name] = [round(c, 3) for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeMix' and n.data_type == 'RGBA' for c in [0]][:0]
os.makedirs(os.path.dirname(p['out']), exist_ok=True)
json.dump(res, open(p['out'], 'w'), indent=1)
print('AREAS', json.dumps(res)[:800], flush=True)
