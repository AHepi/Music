# What this does: lists the view transforms and looks available in Blender 5.2.2 (read only).
import bpy
v = bpy.context.scene.view_settings
print('TRANSFORMS', [i.identifier for i in v.bl_rna.properties['view_transform'].enum_items])
v.view_transform = 'AgX'
print('LOOKS', [i.identifier for i in v.bl_rna.properties['look'].enum_items])
