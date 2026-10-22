import bpy
for n in ['Lantern base','Lantern post','Lantern gallery','Lantern firebox','Lantern cap','Lantern finial','Lantern window glow']:
    o = bpy.data.objects[n]
    me = o.data
    print(n, 'loc', tuple(round(c,3) for c in o.location), 'rot', tuple(round(c,3) for c in o.rotation_euler), 'scale', tuple(round(c,3) for c in o.scale), 'dim', tuple(round(c,3) for c in o.dimensions), 'verts', len(me.vertices))
cap = bpy.data.objects['Lantern cap']
for v in cap.data.vertices[:60]:
    print('  v', tuple(round(c,3) for c in v.co))
