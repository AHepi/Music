# What this does: lists the settings of the Sky Texture node in Blender 5.2.2 (read only).
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
w = bpy.data.worlds.new('w'); w.use_nodes = True
n = w.node_tree.nodes.new('ShaderNodeTexSky')
print('SKYPROPS', [p.identifier for p in n.bl_rna.properties if p.identifier not in ('rna_type','name','label','location','width','height','dimensions','inputs','outputs','internal_links','parent','select','show_options','show_preview','hide','mute','show_texture','bl_idname','bl_label','bl_description','bl_icon','bl_static_type','bl_width_default','bl_width_min','bl_width_max','bl_height_default','bl_height_min','bl_height_max','type','color','use_custom_color','width_hidden','warning_propagation')])
print('SKYTYPES', [i.identifier for i in n.bl_rna.properties['sky_type'].enum_items])
print('INPUTS', [i.name for i in n.inputs])
print('LOOKS', [i.identifier for i in bpy.types.ViewSettings.bl_rna.properties['look'].enum_items][:30])
