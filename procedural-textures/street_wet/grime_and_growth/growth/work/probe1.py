import bpy, time
print('NODE', hasattr(bpy.types,'GeometryNodeInputActiveCamera'), hasattr(bpy.types,'GeometryNodeImageTexture'), hasattr(bpy.types,'GeometryNodeDistributePointsOnFaces'))
for n in ('street_setts','street_pavements','street_channels','street_kerbs'):
    o=bpy.data.objects.get(n)
    if o: print(n, o.type, len(o.data.vertices), len(o.data.polygons), tuple(round(v,2) for v in o.matrix_world.translation), [m.type for m in o.modifiers])
print('cam', bpy.context.scene.camera.name, tuple(bpy.context.scene.camera.location))
print(bpy.app.version_string)
import numpy; print(numpy.__version__)
