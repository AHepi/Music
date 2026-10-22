import bpy, mathutils
sc=bpy.context.scene
print("OBJS", len(bpy.data.objects), "MATS", len(bpy.data.materials))
names=["Hall roof","CT / Ceramic pan prototype","Hall plaster","Back wall, left","Back wall, left cap","Back wall, right","Back wall, right cap","Right wall behind hall","Right wall behind hall cap","Lantern base","Lantern post","Lantern gallery","Lantern firebox","Lantern cap","Lantern finial","Lantern window glow","Lantern light","Water basin","Basin front stone","Basin candle stone","Basin bucket stone","Basin drain pebbles","Shore stones"]+["Rock %d"%i for i in range(5)]+["Pond edge stone %d"%i for i in range(15)]
for n in names:
    o=bpy.data.objects.get(n)
    if not o: print("MISSING",n); continue
    me=o.data
    dims=o.dimensions
    print("%-28s %-8s v=%6d f=%6d loc=(%.2f,%.2f,%.2f) dim=(%.2f,%.2f,%.2f) mats=%s mods=%s hide=%s cols=%s uv=%s"%(n,o.type,len(me.vertices) if hasattr(me,'vertices') else 0,len(me.polygons) if hasattr(me,'polygons') else 0,*o.location,*dims,[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else None,[m.name+':'+m.type for m in o.modifiers],o.hide_get() or o.hide_render,[c.name for c in o.users_collection],[u.name for u in me.uv_layers] if hasattr(me,'uv_layers') else None))
for c in bpy.data.collections:
    if c.name.startswith("G4") or c.name.startswith("G6"): print("COLL",c.name,[o.name for o in c.objects][:40], c.hide_render)
print("CAMS",[ (o.name,tuple(round(x,2) for x in o.location),o.data.lens) for o in bpy.data.objects if o.type=='CAMERA'])
print("NODEGROUPS",[g.name for g in bpy.data.node_groups if g.name.startswith("CT")])
