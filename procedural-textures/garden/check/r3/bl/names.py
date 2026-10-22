import bpy
for o in bpy.data.objects:
    n=o.name
    if any(s in n.lower() for s in ('plank','stringer','ground','cap','hedge','camera','photo','veranda','glow','shoji','kerb','pine pad','maple leaves')):
        print('N', n, o.type, o.get('garden_owner'), len(o.data.polygons) if o.type=='MESH' else '')
print('CAMS', [ (o.name, tuple(round(x,3) for x in o.location)) for o in bpy.data.objects if o.type=='CAMERA'], bpy.context.scene.camera.name)
