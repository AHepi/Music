import bpy
for i in bpy.data.images:
    if i.name.startswith('pk_'):
        print('IMG', i.name, tuple(i.size), i.colorspace_settings.name)
