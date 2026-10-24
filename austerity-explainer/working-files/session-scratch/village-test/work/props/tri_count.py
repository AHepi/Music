import bpy
dg=bpy.context.evaluated_depsgraph_get()
rows=[]
for o in bpy.data.objects:
    if o.type!='MESH' or o.get('place_owner')!='props': continue
    ev=o.evaluated_get(dg); me=ev.to_mesh(); me.calc_loop_triangles(); n=len(me.loop_triangles); ev.to_mesh_clear()
    base=len(o.data.loop_triangles) if False else None
    rows.append((o.name,o.get('place_role'),n,[m.type for m in o.modifiers]))
tot=sum(r[2] for r in rows if r[1]!='never.scatter')
sc=sum(r[2] for r in rows if r[1]=='never.scatter')
print('NON-SCATTER objects',len([r for r in rows if r[1]!='never.scatter']),'tris',tot,'| scatter objects',len([r for r in rows if r[1]=='never.scatter']),'tris',sc)
for r in sorted(rows,key=lambda r:-r[2])[:14]: print(r)
