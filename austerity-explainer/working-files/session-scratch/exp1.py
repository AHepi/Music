import bpy, bmesh, math, os, time
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
s=bpy.context.scene; out={}
# 1. bevel + harden normals + weighted normal on a box
bpy.ops.mesh.primitive_cube_add(size=1); o=bpy.context.active_object; o.name='wallbox'
o.scale=(1.6,0.12,0.65); bpy.ops.object.transform_apply(scale=True)
b=o.modifiers.new('bevel','BEVEL'); b.width=0.008; b.segments=2; b.limit_method='ANGLE'; b.angle_limit=math.radians(30)
b.harden_normals=True; b.use_clamp_overlap=True; b.miter_outer='MITER_ARC'; b.face_strength_mode='FSTR_AFFECTED'
wn=o.modifiers.new('wn','WEIGHTED_NORMAL'); wn.mode='FACE_AREA'; wn.keep_sharp=True; wn.use_face_influence=True
bpy.ops.object.shade_smooth()
# 2. geometry nodes: instance small boxes (bricks) on a grid and realize
bpy.ops.mesh.primitive_plane_add(size=1); g=bpy.context.active_object; g.name='gn_bricks'; g.location=(0,-1,0)
tree=bpy.data.node_groups.new('bricks','GeometryNodeTree')
tree.interface.new_socket('Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
tree.interface.new_socket('Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
N=tree.nodes; L=tree.links
gi=N.new('NodeGroupInput'); go=N.new('NodeGroupOutput')
grid=N.new('GeometryNodeMeshGrid'); grid.inputs['Size X'].default_value=1.0; grid.inputs['Size Y'].default_value=0.5
grid.inputs['Vertices X'].default_value=8; grid.inputs['Vertices Y'].default_value=8
cube=N.new('GeometryNodeMeshCube'); cube.inputs['Size'].default_value=(0.11,0.05,0.02)
iop=N.new('GeometryNodeInstanceOnPoints')
rnd=N.new('FunctionNodeRandomValue'); rnd.data_type='FLOAT_VECTOR'; rnd.inputs['Min'].default_value=(-0.03,-0.03,-0.1); rnd.inputs['Max'].default_value=(0.03,0.03,0.1)
real=N.new('GeometryNodeRealizeInstances')
L.new(grid.outputs['Mesh'],iop.inputs['Points']); L.new(cube.outputs['Mesh'],iop.inputs['Instance'])
L.new(rnd.outputs['Value'],iop.inputs['Rotation'])
L.new(iop.outputs['Instances'],real.inputs['Geometry']); L.new(real.outputs['Geometry'],go.inputs['Geometry'])
m=g.modifiers.new('bricks','NODES'); m.node_group=tree
# export and reimport
p=os.path.join(bpy.app.tempdir,'exp1.glb')
bpy.ops.export_scene.gltf(filepath=p,export_format='GLB',export_apply=True,export_normals=True,export_tangents=True)
dg=bpy.context.evaluated_depsgraph_get()
for ob in (o,g):
    e=ob.evaluated_get(dg).to_mesh(); e.calc_loop_triangles(); out[ob.name+'_tris']=len(e.loop_triangles); ob.evaluated_get(dg).to_mesh_clear()
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
bpy.ops.import_scene.gltf(filepath=p)
for ob in bpy.context.scene.objects:
    if ob.type=='MESH':
        ob.data.calc_loop_triangles(); out['reimport_'+ob.name]=(len(ob.data.loop_triangles), ob.data.has_custom_normals)
out['glb_kb']=os.path.getsize(p)//1024
result=out
