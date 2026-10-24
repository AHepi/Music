import bpy, os
D='/home/user/work/paper-pop-up-film-kit/assets/models/inflation-chapter-2'
result={}
for f in ['factory-a.glb','town.glb','desk.glb','props.glb','factory-b.glb']:
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(D,f))
    g=bpy.context.evaluated_depsgraph_get()
    tris=0; meshes=0; flat=0; smooth=0; custom=0
    for o in bpy.context.scene.objects:
        if o.type!='MESH': continue
        meshes+=1
        m=o.data; m.calc_loop_triangles(); tris+=len(m.loop_triangles)
        for p in m.polygons:
            if p.use_smooth: smooth+=1
            else: flat+=1
        if m.has_custom_normals: custom+=1
    imgs=sorted({(i.name,i.size[0],i.size[1]) for i in bpy.data.images})
    result[f]=str(dict(objects=meshes,tris=tris,flat_faces=flat,smooth_faces=smooth,custom_normal_meshes=custom,materials=len(bpy.data.materials),images=len(imgs),big=len([x for x in imgs if x[1]>=1024])))
