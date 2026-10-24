import bpy
t=bpy.data.node_groups.new('x','ShaderNodeTree')
for k in ['ShaderNodeTexGabor','ShaderNodeTexBrick','ShaderNodeTexChecker','ShaderNodeTexWhiteNoise','ShaderNodeTexWave','ShaderNodeTexMagic','ShaderNodeTexGradient','ShaderNodeTexNoise','ShaderNodeTexVoronoi','ShaderNodeMath','ShaderNodeMapping','ShaderNodeDisplacement','ShaderNodeVectorDisplacement']:
    n=t.nodes.new(k)
    props=[p.identifier for p in n.bl_rna.properties if p.identifier not in ('rna_type','name','label','location','width','height','dimensions','select','show_options','show_preview','hide','mute','show_texture','inputs','outputs','internal_links','parent','type','color','use_custom_color','width_hidden','warning_propagation','is_active_output','bl_idname','bl_label','bl_description','bl_icon','bl_static_type','bl_width_default','bl_width_min','bl_width_max','bl_height_default','bl_height_min','bl_height_max','node_tree','location_absolute','color_mapping','texture_mapping','image_user','image','interface_items') and not p.identifier.startswith('bl_')]
    print(k, 'props', props)
    print('   in ', [(s.name, s.type, s.enabled) for s in n.inputs])
    print('   out', [s.name for s in n.outputs])
print([i.identifier for i in bpy.types.ShaderNodeMath.bl_rna.properties['operation'].enum_items])
print([i.identifier for i in bpy.types.ShaderNodeTexGradient.bl_rna.properties['gradient_type'].enum_items])
print([i.identifier for i in bpy.types.ShaderNodeTexWave.bl_rna.properties['wave_profile'].enum_items])
