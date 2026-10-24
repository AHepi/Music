# What this does: lists every picture a .blend file uses, whether it is packed inside, and whether its
# linked file exists on disk (run with blender -b FILE --python this).
import bpy, os
for image in bpy.data.images:
    path = bpy.path.abspath(image.filepath) if image.filepath else ''
    print('IMAGE', image.name, '| packed' if image.packed_file else '| linked', '|', image.filepath, '| exists' if path and os.path.exists(path) else '| MISSING' if path else '')
print('OBJECTS', len(bpy.data.objects))
