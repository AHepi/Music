import bpy
res = {}
for f in ['factory-a', 'factory-candidate-a', 'factory-b', 'factory-candidate-b']:
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    bpy.ops.import_scene.gltf(filepath=f'/home/user/work/paper-pop-up-film-kit/assets/models/inflation-chapter-2/{f}.glb')
    lo = [9, 9, 9]; hi = [-9, -9, -9]; front_low = -0.0; front_any = 0.0; low_x = []
    for o in bpy.context.scene.objects:
        if o.type != 'MESH' or o.name.startswith(('forecourt', 'kerb', 'rail')): continue
        mw = o.matrix_world
        for v in o.data.vertices:
            p = mw @ v.co
            for i in range(3): lo[i] = min(lo[i], p[i]); hi[i] = max(hi[i], p[i])
            if p.y < -1.0:
                front_any = min(front_any, p.y)
                if p.z < 0.4 and abs(abs(p.x) - 1.6) > 0.25 and abs(p.x) < 1.6: low_x.append((round(p.x, 2), round(p.y, 3), round(p.z, 2), o.name))
    res[f] = {'bbox_lo': [round(c, 3) for c in lo], 'bbox_hi': [round(c, 3) for c in hi], 'most_forward_y': round(front_any, 3),
              'low_in_front_mid': sorted(set((n) for *_, n in low_x)), 'low_front_min_y': min([q[1] for q in low_x], default=None)}
result = res
