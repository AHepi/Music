# Where the wall-bracket lamp's glass is (which end of the bracket is the wall).
import bpy, mathutils
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/props/gas-lamp-wall-bracket.glb')
o=bpy.data.objects['street_lamp_02']
for mi,m in enumerate(o.data.materials):
    vs=set()
    for p in o.data.polygons:
        if p.material_index==mi: vs.update(p.vertices)
    pts=[o.matrix_world @ o.data.vertices[v].co for v in vs]
    print('MAT', m.name, [round(min(p[i] for p in pts),3) for i in range(3)], [round(max(p[i] for p in pts),3) for i in range(3)])
