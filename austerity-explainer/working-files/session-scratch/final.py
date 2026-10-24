import bpy
out = {}
for f in ['factory-candidate-a', 'factory-candidate-b']:
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    bpy.ops.import_scene.gltf(filepath=f'/home/user/work/paper-pop-up-film-kit/assets/models/inflation-chapter-2/{f}.glb')
    s = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get(); tris = 0
    for o in s.objects:
        if o.type == 'MESH':
            m = o.evaluated_get(dg).to_mesh(); m.calc_loop_triangles(); tris += len(m.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
    out[f] = {'tris': tris, 'empties': {o.name: [round(c, 4) for c in o.matrix_world.translation] for o in s.objects if o.type == 'EMPTY'},
              'materials': sorted(m.name for m in bpy.data.materials), 'max_tex': max(max(i.size) for i in bpy.data.images if i.size[0]),
              'meshes': sorted(o.name for o in s.objects if o.type == 'MESH')}
result = out
