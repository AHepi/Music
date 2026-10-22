import bpy, sys, math
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
for n in ('Rock 0','Stepping stone 1','Lantern base','Bridge pier 1','Water basin','Veranda step'):
    ob = bpy.data.objects[n]
    print('==', n, 'props', {k: (v if not hasattr(v,'to_dict') else v.to_dict()) for k,v in ob.items()}, 'rotmode', ob.rotation_mode, tuple(round(x,3) for x in ob.rotation_quaternion), tuple(round(x,3) for x in ob.location))
    print('  base mesh', len(ob.data.vertices), len(ob.data.polygons), [m.name if m else None for m in ob.data.materials])
    for m in ob.modifiers:
        print('  mod', m.name, m.type, getattr(m,'width',None), m.show_viewport, m.show_render)
        if m.type=='NODES':
            ng=m.node_group
            print('    group', ng.name, [ (s.name, s.in_out, getattr(s,'default_value',None)) for s in ng.interface.items_tree if s.item_type=='SOCKET'])
            for k in dir(m.properties.inputs) if False else []: pass
    ev = ob.evaluated_get(dg); me = ev.to_mesh()
    zs=[v.co.z for v in me.vertices]; print('  eval local z', min(zs), max(zs), 'faces', len(me.polygons), 'sides', sorted(set(len(p.vertices) for p in me.polygons)), 'smooth', sum(p.use_smooth for p in me.polygons), 'attrs', [a.name for a in me.attributes])
    print('  eval mats', [m.name if m else None for m in me.materials], 'uv', [u.name for u in me.uv_layers])
    ev.to_mesh_clear()
for m in bpy.data.materials:
    if m.name.startswith('CT / Stone painterly surface') and m.name.endswith('.025') or m.name=='CT / Stone painterly surface':
        print(m.name, dict(m.items()))
# ground local check: ground z at stones
