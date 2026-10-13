"""What this does: opens each .glb given and prints its parts: triangle count, size (bounding box),
centre, materials and textures, so we know what SAM 3D returned before placing it in a scene.
Use: blender-env/bin/python inspect_glb.py FILE.glb [FILE.glb ...]"""
import sys
import bpy
from mathutils import Vector

for path in sys.argv[1:]:
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    triangles = 0
    low, high = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    images = set()
    for o in meshes:
        o.data.calc_loop_triangles()
        triangles += len(o.data.loop_triangles)
        for corner in o.bound_box:
            w = o.matrix_world @ Vector(corner)
            low = Vector(map(min, low, w)); high = Vector(map(max, high, w))
        for slot in o.material_slots:
            if slot.material and slot.material.use_nodes:
                for n in slot.material.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image:
                        images.add(f'{n.image.name} {n.image.size[0]}x{n.image.size[1]}')
    size = high - low
    print(f'{path.split("/")[-1]}: {len(meshes)} mesh part(s), {triangles} triangles, '
          f'size (Blender x,y,z) {size.x:.3f} {size.y:.3f} {size.z:.3f}, centre {((low + high) / 2).to_tuple(3)}, '
          f'colours per corner: {any(len(o.data.color_attributes) for o in meshes)}, textures: {sorted(images) or "none"}')
