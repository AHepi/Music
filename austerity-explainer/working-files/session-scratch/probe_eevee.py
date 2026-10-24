import bpy
e = bpy.context.scene.eevee
print('PROBE pool options', [i.identifier for i in e.bl_rna.properties['shadow_pool_size'].enum_items])
print('PROBE has shadow_resolution_scale', hasattr(e, 'shadow_resolution_scale'), getattr(e, 'shadow_resolution_scale', None))
print('PROBE light props', [p for p in bpy.types.Light.bl_rna.properties.keys() if 'shadow' in p])
