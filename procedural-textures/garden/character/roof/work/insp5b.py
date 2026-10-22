import bpy
o=bpy.data.objects["Hall roof"]
m=o.modifiers[0]
print([a for a in dir(m) if not a.startswith('_')])
