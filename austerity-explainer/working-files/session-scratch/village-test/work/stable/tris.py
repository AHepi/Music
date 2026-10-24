import bpy
dg=bpy.context.evaluated_depsgraph_get()
rows=[]
for o in bpy.data.objects:
    if o.get('place_owner')!='stable': continue
    o.data.calc_loop_triangles(); a=len(o.data.loop_triangles)
    e=o.evaluated_get(dg); m=e.to_mesh(); m.calc_loop_triangles(); b=len(m.loop_triangles); e.to_mesh_clear()
    rows.append((b,a,o.name,[md.name for md in o.modifiers]))
rows.sort(reverse=True)
for r in rows[:25]: print('TRI',r)
print('SUM', sum(r[0] for r in rows), sum(r[1] for r in rows))
