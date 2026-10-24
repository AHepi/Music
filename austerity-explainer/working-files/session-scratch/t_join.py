import bpy, bmesh, math
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
objs=[]
for i in range(2):
    me=bpy.data.meshes.new(f'b{i}'); bm=bmesh.new(); bmesh.ops.create_cube(bm,size=1); bm.to_mesh(me); bm.free()
    o=bpy.data.objects.new(f'b{i}',me); bpy.context.scene.collection.objects.link(o); o.location=(i*2,0,0)
    b=o.modifiers.new('bevel','BEVEL'); b.width=0.05; b.segments=2; b.limit_method='ANGLE'; b.harden_normals=True; b.miter_outer='MITER_ARC'; b.face_strength_mode='FSTR_AFFECTED'
    me.polygons.foreach_set('use_smooth',[True]*len(me.polygons))
    w=o.modifiers.new('wn','WEIGHTED_NORMAL'); w.keep_sharp=True; w.use_face_influence=True
    objs.append(o)
for o in objs:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active=o
    for m in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=m.name)
before=objs[1].data.has_custom_normals
bpy.ops.object.select_all(action='DESELECT')
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active=objs[0]; bpy.ops.object.join()
me=objs[0].data
# check a flat face's corner normals equal the face normal (hardened)
p=me.polygons[0]; ns=[tuple(round(c,3) for c in me.corner_normals[li].vector) for li in p.loop_indices]
result={'custom_before_join':before,'custom_after':me.has_custom_normals,'polys':len(me.polygons),'face_n':tuple(round(c,3) for c in p.normal),'corner_n':ns}
