import bpy
print('VERSION', bpy.app.version_string)
s = bpy.context.scene
s.render.engine = 'CYCLES'
b = bpy.data.objects.new('t', bpy.data.meshes.new('t'))
bpy.context.scene.collection.objects.link(b)
m = b.modifiers.new('x','SUBSURF')
print([p for p in dir(m) if 'adapt' in p])
print([p for p in dir(b.cycles) if 'adapt' in p or 'dicing' in p])
