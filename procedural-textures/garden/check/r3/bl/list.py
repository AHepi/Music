import bpy, re
pat = re.compile(r'pier|step|cap|lantern|stringer|wall|plinth|hedge|Fix', re.I)
for o in bpy.data.objects:
    if pat.search(o.name) and o.type in ('MESH','LIGHT','EMPTY'):
        print('OBJ', o.name, o.type, tuple(round(x,3) for x in o.location), len(o.data.polygons) if o.type=='MESH' else '', o.get('garden_owner'), 'hide', o.hide_render)
print('N objects', len(bpy.data.objects), 'materials', len(bpy.data.materials))
