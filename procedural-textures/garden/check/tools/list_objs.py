import bpy, sys, time
t=time.time()
print("FILE", bpy.data.filepath, "objects", len(bpy.data.objects), "open s", round(time.time()-t,2))
import re
pat=re.compile(r"Bridge|Veranda|cap|Cap|Lantern|Wall|wall|stringer|Stringer|Roof|plinth|Plinth|Hall|Open room",re.I)
for o in sorted(bpy.data.objects,key=lambda o:o.name):
    if pat.search(o.name):
        print(f"{o.name!r:48} {o.type:8} verts={len(o.data.vertices) if o.type=='MESH' else '-':>6} owner={o.get('garden_owner','')!s:8} role={o.get('garden_role','')} hide={o.hide_render}")
