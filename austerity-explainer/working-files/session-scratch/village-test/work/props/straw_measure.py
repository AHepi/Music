import bpy, json, numpy as np, sys
o=bpy.data.objects['Prop straw scraps']
me=o.data; n=len(me.vertices)
co=np.array([tuple(v.co) for v in me.vertices])
# loose parts by union-find on edges
parent=list(range(n))
def f(a):
    while parent[a]!=a:
        parent[a]=parent[parent[a]]; a=parent[a]
    return a
for e in me.edges:
    a,b=f(e.vertices[0]),f(e.vertices[1])
    if a!=b: parent[a]=b
groups={}
for i in range(n): groups.setdefault(f(i),[]).append(i)
rows=[]
for g in groups.values():
    p=co[g]; ext=p.max(0)-p.min(0)
    rows.append((float(ext.max()), float(p[:,2].min()), float(p[:,2].max()-p[:,2].min()), float(p[:,0].mean()), float(p[:,1].mean())))
print('SCRAPS', len(rows), 'longest', round(max(r[0] for r in rows),3), 'tallest', round(max(r[2] for r in rows),3), 'z range', round(min(r[1] for r in rows),3), round(max(r[1] for r in rows),3))
xs=[r[3] for r in rows]; ys=[r[4] for r in rows]
print('x', round(min(xs),2), round(max(xs),2), 'y', round(min(ys),2), round(max(ys),2))
json.dump({'count':len(rows),'longest_m':max(r[0] for r in rows),'tallest_m':max(r[2] for r in rows),'x_range':[min(xs),max(xs)],'y_range':[min(ys),max(ys)]}, open('straw_measure.json','w'))
