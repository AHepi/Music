import bpy
bpy.ops.object.light_add(type='SPOT')
l = bpy.context.active_object.data
print('PROBE custom distance', hasattr(l, 'use_custom_distance'), hasattr(l, 'cutoff_distance'))
print('PROBE light props', [p for p in type(l).bl_rna.properties.keys() if 'dist' in p or 'link' in p or 'shadow' in p])
print('PROBE object light linking', hasattr(bpy.context.active_object, 'light_linking'))
