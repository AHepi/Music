import bpy
s = bpy.context.scene
g = bpy.context.evaluated_depsgraph_get(); tris = 0
for o in s.objects:
    if o.type == 'MESH':
        m = o.evaluated_get(g).to_mesh(); m.calc_loop_triangles(); tris += len(m.loop_triangles); o.evaluated_get(g).to_mesh_clear()
result = {'tris': tris, 'meshes': sum(o.type == 'MESH' for o in s.objects),
 'empties': ' '.join(f"{o.name}@{tuple(round(c,3) for c in o.matrix_world.translation)}" for o in sorted(s.objects, key=lambda o: o.name) if o.type == 'EMPTY'),
 'materials': ' '.join(sorted(m.name for m in bpy.data.materials))}
