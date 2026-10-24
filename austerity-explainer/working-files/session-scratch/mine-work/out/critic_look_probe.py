import bpy
s=bpy.context.scene
s.view_settings.view_transform='AgX'
print('LOOKS', [i.identifier for i in s.view_settings.bl_rna.properties['look'].enum_items])
try:
    s.view_settings.look='AgX - Punchy'; print('PUNCHY OK', s.view_settings.look)
except Exception as e: print('PUNCHY FAIL', e)
print('TRANSFORMS',[i.identifier for i in s.view_settings.bl_rna.properties['view_transform'].enum_items])
