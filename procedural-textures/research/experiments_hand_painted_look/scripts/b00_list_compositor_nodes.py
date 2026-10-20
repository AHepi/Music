# What this does: lists every compositor node type in this Blender, and the settings and sockets of the stylising ones
# (Kuwahara, Pixelate, Posterize, Filter, Dilate/Erode, Blur, Bilateral Blur, Despeckle...). Prints plain text.
import bpy
print('VERSION', bpy.app.version_string)
names = sorted(n for n in dir(bpy.types) if n.startswith('CompositorNode'))
print('COUNT', len(names))
print(' '.join(names))
scene = bpy.context.scene
print('scene attrs with node:', [a for a in dir(scene) if 'node' in a.lower() or 'compos' in a.lower()])
