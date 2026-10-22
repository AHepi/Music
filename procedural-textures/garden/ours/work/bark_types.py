import bpy
for o in bpy.context.scene.objects:
    if o.name.startswith(('Maple','Pine')): print('OBJ', o.name, o.type, [s.material.name for s in o.material_slots if s.material])
