# Lists what a light-linking collection entry offers in this Blender.
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_plane_add(); plane = bpy.context.active_object
receivers = bpy.data.collections.new('receivers'); receivers.objects.link(plane)
item = receivers.collection_objects[0]
print('ITEM', type(item).__name__, [a for a in dir(item) if not a.startswith('__')])
print('LINK', [a for a in dir(item.light_linking) if not a.startswith('__')])
print('KEYS', list(receivers.collection_objects.keys()))
