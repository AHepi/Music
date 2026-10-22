import bpy
o = bpy.data.objects['CT / Ceramic pan prototype']
me = o.data
print('verts', len(me.vertices), 'faces', len(me.polygons), 'smooth', [p.use_smooth for p in me.polygons][:5], 'uv', [u.name for u in me.uv_layers], 'attrs', [a.name for a in me.attributes])
for i, v in enumerate(me.vertices): print(i, tuple(round(c, 3) for c in v.co))
for p in me.polygons: print('F', tuple(p.vertices), tuple(round(c,2) for c in p.normal))
print([ (m.name) for m in me.materials], [ (k, o[k]) for k in o.keys()])
print('has set_sharp_from_angle', hasattr(me, 'set_sharp_from_angle'), 'shade_smooth', hasattr(me, 'shade_smooth'))
roof = bpy.data.objects['Hall roof']
print('roof mods', [(m.name, m.type) for m in roof.modifiers], roof.dimensions[:], roof.location[:])
