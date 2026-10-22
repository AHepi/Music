import bpy, bmesh, math, numpy as np
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
def comps(bm):
    seen=set(); out=[]
    for v in bm.verts:
        if v.index in seen: continue
        st=[v]; c=[]
        while st:
            a=st.pop()
            if a.index in seen: continue
            seen.add(a.index); c.append(a)
            for e in a.link_edges: st.append(e.other_vert(a))
        out.append(c)
    return out
for n in ['Astra / varied planks.003','Astra / varied planks.006','Astra / varied planks']:
    ob = bpy.data.objects[n]
    print('==', n, 'parent', ob.parent.name, 'parent loc', tuple(round(x,3) for x in ob.parent.location), 'rot', tuple(round(math.degrees(x),1) for x in ob.parent.rotation_euler), 'mw', [round(x,3) for x in ob.matrix_world.translation])
    print('  mods', [(m.name, m.type, getattr(m,'width',None), getattr(m,'segments',None), getattr(m,'limit_method',None)) for m in ob.modifiers])
    me = ob.data; bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    cs = comps(bm)
    print('  base mesh verts', len(me.vertices), 'faces', len(me.polygons), 'components', len(cs), 'attrs', [a.name for a in me.attributes], 'mats', [m.name for m in me.materials])
    for c in cs[:4] + cs[-2:]:
        xs=[v.co.x for v in c]; ys=[v.co.y for v in c]; zs=[v.co.z for v in c]
        print('   comp', len(c), 'x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f' % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
# the roof instances
roof = bpy.data.objects['Hall roof']
rows = {}
n=0
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.original == roof:
        m = inst.matrix_world; n+=1
        bb = [m @ Vector(c) for c in inst.object.bound_box]
        zs=[b.z for b in bb]; ys=[b.y for b in bb]; xs=[b.x for b in bb]
        key = round(sum(ys)/8, 1)
        rows.setdefault(key, []).append((min(zs), max(zs), sum(xs)/8, inst.object.name))
print('roof instances', n)
for k in sorted(rows):
    r = rows[k]; print('  y %.1f: n %d zmin %.3f zmax %.3f  names %s' % (k, len(r), min(a[0] for a in r), max(a[1] for a in r), sorted(set(a[3] for a in r))[:3]))
