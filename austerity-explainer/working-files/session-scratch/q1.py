import bpy
s=bpy.context.scene.render.image_settings
print([p.identifier for p in s.bl_rna.properties])
s.file_format='OPEN_EXR'
print([p.identifier for p in s.bl_rna.properties if 'exr' in p.identifier or 'layer' in p.identifier])
print(bpy.context.scene.view_layers[0].bl_rna.properties.keys()[:0])
print([p for p in dir(bpy.context.scene.view_layers[0]) if 'pass' in p])
