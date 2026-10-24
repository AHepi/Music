import bpy
g = bpy.context.evaluated_depsgraph_get(); out = {}
for o in bpy.context.scene.objects:
    if o.type != 'MESH': continue
    m = o.evaluated_get(g).to_mesh(); m.calc_loop_triangles(); n = len(m.loop_triangles); o.evaluated_get(g).to_mesh_clear()
    key = o.data.name
    out[key] = out.get(key, 0) + n
result = dict(sorted(out.items(), key=lambda kv: -kv[1]))
