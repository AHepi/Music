import bpy, sys, json, re, statistics as st
out=sys.argv[sys.argv.index('--')+1]
R={}
groups={'Rock':r'^Rock \d+$','Gravel rock':r'^Gravel rock \d+$','Pond edge stone':r'^Pond edge stone \d+$','Stepping stone':r'^Stepping stone \d+$'}
for g,rx in groups.items():
    rows=[]
    for o in bpy.data.objects:
        if o.type=='MESH' and re.search(rx,o.name):
            me=o.data; polys=me.polygons
            ar=[p.area for p in polys if p.area>1e-9]
            sm=sum(1 for p in polys if p.use_smooth)/max(1,len(polys))
            # vertex count per polygon: share of triangles and quads
            tri=sum(1 for p in polys if len(p.vertices)==3)/max(1,len(polys))
            quad=sum(1 for p in polys if len(p.vertices)==4)/max(1,len(polys))
            rows.append({'faces':len(polys),'smooth_share':round(sm,3),'tri_share':round(tri,2),'quad_share':round(quad,2),'area_cv':round(st.pstdev(ar)/st.mean(ar),2) if len(ar)>2 else None})
    R[g]={'n':len(rows),'faces_min':min(r['faces'] for r in rows),'faces_max':max(r['faces'] for r in rows),
          'smooth_share_mean':round(sum(r['smooth_share'] for r in rows)/len(rows),3),
          'area_cv_mean':round(sum(r['area_cv'] for r in rows)/len(rows),2),'tri_share_mean':round(sum(r['tri_share'] for r in rows)/len(rows),2)}
for n in ('Astra / Courtyard receiving ground','Raked gravel court','Hills, far','Hills, near'):
    o=bpy.data.objects[n]; me=o.data; polys=me.polygons
    ar=[p.area for p in polys if p.area>1e-12]
    R[n]={'faces':len(polys),'smooth_share':round(sum(1 for p in polys if p.use_smooth)/len(polys),3),'area_cv':round(st.pstdev(ar)/st.mean(ar),2)}
json.dump(R,open(out,'w'),indent=1); print('FACETS_DONE')
