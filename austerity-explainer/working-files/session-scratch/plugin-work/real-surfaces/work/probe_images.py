# What this does: lists the plan pictures in a saved scene (name, size, packed or not, users), to see which one did not survive the save.
import bpy
for image in bpy.data.images:
    if image.name.startswith('pk_plan'):
        print('IMAGE', image.name, tuple(image.size), bool(image.packed_file), image.users, image.get('pk_bounds') is not None, image.source)
