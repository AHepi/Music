import bpy
dg=bpy.context.evaluated_depsgraph_get()
rows=[]
for o in bpy.data.objects:
    if o.type!='MESH' or o.get('place_owner')!='props': continue
    ev=o.evaluated_get(dg); me=ev.to_mesh(); me.calc_loop_triangles(); n=len(me.loop_triangles); ev.to_mesh_clear()
    base=o.data; base.calc_loop_triangles(); b=len(base.loop_triangles)
    mods=[(m.name,m.type,getattr(m,'levels',None),getattr(m,'render_levels',None),getattr(m,'subdivision_type',None)) for m in o.modifiers if m.type=='SUBSURF']
    rows.append((o.name,b,n,mods))
for r in sorted(rows,key=lambda r:-r[2]): print(f'{r[0]:26s} raw {r[1]:6d} evaluated {r[2]:7d} {r[3]}')
