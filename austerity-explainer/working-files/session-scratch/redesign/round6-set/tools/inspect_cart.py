# What this does: prints the handcart's shape along its length (scratch, round 6): for slices along x, the highest point
import bpy
bpy.ops.import_scene.gltf(filepath='/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/props/handcart.glb')
body = bpy.data.objects['cart-body']
import collections
slices = collections.defaultdict(list)
for v in body.data.vertices:
    p = body.matrix_world @ v.co
    slices[round(p.x * 5) / 5].append(p)
for x in sorted(slices):
    pts = slices[x]
    print(f'x {x:5.1f}: z {min(p.z for p in pts):.2f}..{max(p.z for p in pts):.2f}  y {min(p.y for p in pts):.2f}..{max(p.y for p in pts):.2f}  n {len(pts)}')
mats = collections.Counter()
for poly in body.data.polygons:
    mats[body.data.materials[poly.material_index].name] += 1
print(mats)
for name in ('coal', 'hessian-plain'):
    pts = [body.matrix_world @ body.data.vertices[i].co for poly in body.data.polygons if body.data.materials[poly.material_index].name == name for i in poly.vertices]
    if pts:
        print(name, 'x', round(min(p.x for p in pts), 2), round(max(p.x for p in pts), 2), 'z', round(min(p.z for p in pts), 2), round(max(p.z for p in pts), 2))
