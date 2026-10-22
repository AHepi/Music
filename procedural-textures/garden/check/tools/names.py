import bpy
for o in sorted(bpy.data.objects,key=lambda o:o.name):
    print(f"{o.type:8} {o.name}")
