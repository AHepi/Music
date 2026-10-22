import bpy, sys, numpy as np, math
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=4; sc.cycles.use_denoising=False
sc.render.resolution_x=64; sc.render.resolution_y=64
# leaf source in an unlinked collection
src=bpy.data.collections.new('src')   # NOT linked to scene
me=bpy.data.meshes.new('leaf'); me.from_pydata([(-0.4,-0.4,0),(0.4,-0.4,0),(0.4,0.4,0),(-0.4,0.4,0)],[],[(0,1,2,3)])
mat=bpy.data.materials.new('M'); mat.use_nodes=True
t=mat.node_tree; b=t.nodes['Principled BSDF']; att=t.nodes.new('ShaderNodeAttribute'); att.attribute_type='INSTANCER'; att.attribute_name='leaf_hue'
em=t.nodes.new('ShaderNodeEmission'); t.links.new(att.outputs['Fac'],em.inputs['Color']); t.links.new(em.outputs[0],t.nodes['Material Output'].inputs['Surface'])
me.materials.append(mat)
lo=bpy.data.objects.new('leaf0',me); src.objects.link(lo)
pm=bpy.data.meshes.new('pts'); pm.from_pydata([(-0.6,0,0),(0.6,0,0)],[],[])
a=pm.attributes.new('leaf_hue','FLOAT','POINT'); a.data.foreach_set('value',[0.1,0.9])
host=bpy.data.objects.new('host',pm); sc.collection.objects.link(host)
g=bpy.data.node_groups.new('t','GeometryNodeTree')
g.interface.new_socket('Geometry',in_out='INPUT',socket_type='NodeSocketGeometry'); g.interface.new_socket('Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
i=g.nodes.new('NodeGroupInput'); o=g.nodes.new('NodeGroupOutput')
ci=g.nodes.new('GeometryNodeCollectionInfo'); ci.inputs['Collection'].default_value=src; ci.transform_space='RELATIVE'
ci.inputs['Separate Children'].default_value=True; ci.inputs['Reset Children'].default_value=True
iop=g.nodes.new('GeometryNodeInstanceOnPoints'); iop.inputs['Pick Instance'].default_value=True
g.links.new(i.outputs[0],iop.inputs['Points']); g.links.new(ci.outputs[0],iop.inputs['Instance']); g.links.new(iop.outputs[0],o.inputs[0])
m=host.modifiers.new('gn','NODES'); m.node_group=g
cam=bpy.data.cameras.new('c'); cam.type='ORTHO'; cam.ortho_scale=2.0
co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); co.location=(0,0,3); sc.camera=co
sc.render.filepath='proc-work/garden/life/work/t_attr.png'
sc.view_settings.view_transform='Standard'
sc.world=bpy.data.worlds.new('w'); sc.world.color=(0,0,0)
bpy.ops.render.render(write_still=True)
img=bpy.data.images.load(sc.render.filepath)
px=np.array(img.pixels[:]).reshape(64,64,4)
print('left pixel',px[32,12,:3],'right pixel',px[32,52,:3])
