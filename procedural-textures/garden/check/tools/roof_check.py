import bpy, sys, json
out=sys.argv[sys.argv.index('--')+1]
dg=bpy.context.evaluated_depsgraph_get()
R={}
for n in ('Hall roof','Eave soffit','Hall posts','Hall beams','Open room back','Raked gravel court','Pond water'):
    o=bpy.data.objects.get(n)
    if not o: continue
    ev=o.evaluated_get(dg); me=ev.to_mesh()
    vs=[ev.matrix_world@v.co for v in me.vertices]
    R[n]={'eval_verts':len(vs),'eval_faces':len(me.polygons),
          'bbox':[[round(min(v[i] for v in vs),3),round(max(v[i] for v in vs),3)] for i in range(3)] if vs else None}
    ev.to_mesh_clear()
json.dump(R,open(out,'w'))
print('ROOF_DONE')
