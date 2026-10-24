import sys, json
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0, KIT)
import numpy as np
from apply import kit as kit_module
from masks import geom, ground_plan
k = kit_module.Kit.load('pit_village_street', scene_id='street', strict=True)
geo = geom.RoleGeometry(k.role_map)
settings = k.settings
spec = settings.geometry['steps']
data = geo.triangles(spec['from'])
v, t = data[0], data[1]
n = np.cross(v[t[:,1]]-v[t[:,0]], v[t[:,2]]-v[t[:,0]])
area = np.linalg.norm(n,axis=1)*0.5
up = (n[:,2]/np.maximum(np.linalg.norm(n,axis=1),1e-12) >= 0.9) & (area>1e-5)
centre = (v[t[:,0]]+v[t[:,1]]+v[t[:,2]])/3.0
ents = ground_plan.entrances(geo, settings)
print('entrances', len(ents), ents[:3])
near = np.zeros(len(t), bool)
for ex,ey,ez,_ in ents:
    near |= np.hypot(centre[:,0]-ex, centre[:,1]-ey) <= 0.9
sel = up & near & (centre[:,2] > -1)
print('up triangles near entrances', int(sel.sum()))
idx = np.nonzero(sel)[0]
# size of each triangle's xy bounding box, height z of centre
rows=[]
for i in idx:
    tri = v[t[i]]
    bb = (tri[:,0].max()-tri[:,0].min(), tri[:,1].max()-tri[:,1].min())
    rows.append((round(float(centre[i,2]),2), round(float(area[i]),3), round(float(bb[0]),2), round(float(bb[1]),2), round(float(centre[i,0]),2), round(float(centre[i,1]),2)))
rows.sort(key=lambda r:-r[1])
print('largest 15 (z, area, bbx, bby, cx, cy):')
for r in rows[:15]: print(r)
print('count by height band:', {b:int(sum(1 for r in rows if lo<=r[0]<hi)) for b,(lo,hi) in {'<0.3':(-9,0.3),'0.3-0.6':(0.3,0.6),'0.6-1.2':(0.6,1.2),'1.2-3':(1.2,3),'>3':(3,99)}.items()})
print('area>1:', sum(1 for r in rows if r[1]>1.0), 'area>0.5:', sum(1 for r in rows if r[1]>0.5))
print('---- with the ground height')
timer = geom.Timer()
grid, arrays, stats = ground_plan.make(geo, settings, timer)
H = arrays['ground_height']; has = arrays['has_ground']
ci = np.clip(((centre[:,0]-grid.x0)/grid.dot).astype(int),0,grid.width-1); cj = np.clip(((centre[:,1]-grid.y0)/grid.dot).astype(int),0,grid.height-1)
above = centre[:,2]-H[cj,ci]
ok = up & near & (above>=spec.get('min_height_m',0.05)) & has[cj,ci]
idx = np.nonzero(ok)[0]
print('selected triangles', len(idx))
rows=[]
for i in idx:
    tri=v[t[i]]
    rows.append((round(float(above[i]),2), round(float(area[i]),3), round(float(tri[:,0].max()-tri[:,0].min()),2), round(float(tri[:,1].max()-tri[:,1].min()),2), round(float(centre[i,0]),2), round(float(centre[i,1]),2)))
import collections
print('by above-ground band', {b:int(sum(1 for r in rows if lo<=r[0]<hi)) for b,(lo,hi) in {'0.05-0.3':(0.05,0.3),'0.3-0.6':(0.3,0.6),'0.6-1.2':(0.6,1.2),'1.2-3':(1.2,3),'>3':(3,99)}.items()})
big=[r for r in rows if r[1]>0.1 or r[2]>0.6 or r[3]>1.5]
print('big ones', len(big)); [print(r) for r in sorted(big,key=lambda r:-r[1])[:12]]
print('x range of selected centres', min(r[4] for r in rows), max(r[4] for r in rows))
print('tall ones (above>0.7):'); [print(r) for r in sorted(rows,key=lambda r:-r[0])[:8]]
print('---- extents with max_height 0.8')
ok2 = ok & (above <= 0.8)
idx = np.nonzero(ok2)[0]
ext = np.array([max(v[t[i]][:,0].max()-v[t[i]][:,0].min(), v[t[i]][:,1].max()-v[t[i]][:,1].min()) for i in idx])
print('selected', len(idx))
for lo,hi in ((0,0.3),(0.3,0.6),(0.6,1.0),(1.0,1.3),(1.3,1.6),(1.6,2.5),(2.5,5),(5,99)):
    sel=(ext>=lo)&(ext<hi); print(f'  extent {lo}-{hi}: {int(sel.sum())} triangles; above-ground mean {float(np.mean([above[i] for i,s in zip(idx,sel) if s]) if sel.any() else 0):.2f}; x centres {sorted(set(round(float(centre[i,0]),1) for i,s in zip(idx,sel) if s))[:10]}')
