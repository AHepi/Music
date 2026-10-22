import bpy
for name in ('Shoji paper glow','Lantern flame','Open room, dim','Hills, far haze','Far hill','Shoji paper, softer','Pond water'):
    m=bpy.data.materials.get(name)
    if not m: print('NO',name); continue
    print('==',name,'users',m.users)
    for n in m.node_tree.nodes:
        ins=[]
        for i in n.inputs:
            if hasattr(i,'default_value') and not i.is_linked:
                try: v=tuple(round(x,3) for x in i.default_value)
                except TypeError: v=round(i.default_value,3) if isinstance(i.default_value,float) else i.default_value
                ins.append((i.name,v))
        print('  ',n.bl_idname.replace('ShaderNode',''),n.name,[x for x in ins if x[0] in ('Color','Strength','Base Color','Roughness','Emission Strength','Emission Color','Transmission Weight','IOR','Alpha','Weight','Fac')])
    links=[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]
    print('   links',links)
sc=bpy.context.scene
print('world lightgroup attr', hasattr(sc.world,'lightgroup'))
vl=bpy.context.view_layer
print('view layers',[v.name for v in sc.view_layers], 'lightgroups',[g.name for g in vl.lightgroups])
print('cycles',sc.cycles.device, sc.cycles.use_light_tree, sc.cycles.sample_clamp_indirect, sc.cycles.use_fast_gi if hasattr(sc.cycles,'use_fast_gi') else None, 'caustics',sc.cycles.caustics_reflective,sc.cycles.caustics_refractive)
print('compositor', sc.use_nodes if hasattr(sc,'use_nodes') else None, sc.compositing_node_group, sc.render.use_compositing, getattr(sc.render,'compositor_device',None))
print('sun lamp data', bpy.data.objects['Golden hour sun'].data.angle, 'vis cam', bpy.data.objects['Golden hour sun'].visible_camera)
for n in ('Cool sky fill','Hall glow 0','Lantern light'):
    o=bpy.data.objects[n]; print(n,'visible_camera',o.visible_camera,'lightgroup',o.lightgroup)
print('Lantern window glow parent/collections', [c.name for c in bpy.data.objects['Lantern window glow'].users_collection])
print('hills collections', [c.name for c in bpy.data.objects['Hills, far'].users_collection])
