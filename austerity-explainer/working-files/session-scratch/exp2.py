import bpy, math, time, os
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
s=bpy.context.scene; s.render.engine='CYCLES'; s.cycles.device='CPU'; s.cycles.samples=16
bpy.ops.mesh.primitive_cube_add(size=1); o=bpy.context.active_object
o.scale=(0.3,0.3,0.6); bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02); bpy.ops.object.mode_set(mode='OBJECT')
m=bpy.data.materials.new('m'); m.use_nodes=True; o.data.materials.append(m)
N=m.node_tree.nodes; L=m.node_tree.links; bsdf=N['Principled BSDF']
bev=N.new('ShaderNodeBevel'); bev.samples=8; bev.inputs['Radius'].default_value=0.02
L.new(bev.outputs['Normal'], bsdf.inputs['Normal'])
img=bpy.data.images.new('bevel_normal',512,512); img.colorspace_settings.name='Non-Color'
t=N.new('ShaderNodeTexImage'); t.image=img; N.active=t
s.render.bake.margin=8
o.select_set(True); bpy.context.view_layer.objects.active=o
t0=time.time(); bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', margin=8, use_clear=True); dt=time.time()-t0
# AO bake timing too
img2=bpy.data.images.new('ao',512,512); t2=N.new('ShaderNodeTexImage'); t2.image=img2; N.active=t2
s.world=bpy.data.worlds.new('w'); s.world.light_settings.distance=0.3
t0=time.time(); bpy.ops.object.bake(type='AO', margin=8, use_clear=True); dt2=time.time()-t0
px=list(img.pixels[:]); 
# count non-flat normals (blue < 0.98)
nonflat=sum(1 for i in range(0,len(px),4) if px[i+2]<0.97 and px[i+3]>0)
p=os.path.join(bpy.app.tempdir,'bevel_normal.png'); img.filepath_raw=p; img.file_format='PNG'; img.save()
result={'normal_bake_s':round(dt,2),'ao_bake_s':round(dt2,2),'nonflat_px':nonflat,'path':p}
