import bpy
sc=bpy.context.scene; sc.render.engine='CYCLES'
c=sc.cycles
print('dicing_rate',c.dicing_rate,'preview',c.preview_dicing_rate,'max_subdiv',c.max_subdivisions,'offscreen',c.offscreen_dicing_scale)
m=bpy.data.meshes.new('m'); o=bpy.data.objects.new('o',m); sc.collection.objects.link(o)
s=o.modifiers.new('s','SUBSURF')
print('subsurf default: levels',s.levels,'render_levels',s.render_levels,'adaptive',s.use_adaptive_subdivision,'space',s.adaptive_space,'pixel',s.adaptive_pixel_size,'edge',s.adaptive_object_edge_length)
mat=bpy.data.materials.new('x'); print('displacement_method default',mat.displacement_method, 'max_vertex_displacement', mat.max_vertex_displacement)
print('bake defaults margin',sc.render.bake.margin,'margin_type',sc.render.bake.margin_type,'samples',c.samples,'cage_extrusion',sc.render.bake.cage_extrusion,'max_ray',sc.render.bake.max_ray_distance,'normal swizzle',sc.render.bake.normal_r,sc.render.bake.normal_g,sc.render.bake.normal_b,'use_clear',sc.render.bake.use_clear)
nm=mat.node_tree if mat.node_tree else None
mat.use_nodes=True
n=mat.node_tree.nodes.new('ShaderNodeNormalMap'); print('normal map defaults: convention',n.convention,'space',n.space,'base',n.base)
b=mat.node_tree.nodes.new('ShaderNodeBump'); print('bump defaults', [(i.name,i.default_value) for i in b.inputs if i.name in ('Strength','Distance','Filter Width')])
d=mat.node_tree.nodes.new('ShaderNodeDisplacement'); print('disp defaults', [(i.name,i.default_value) for i in d.inputs if i.name in ('Height','Midlevel','Scale')], d.space)
