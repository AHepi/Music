import sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'proc-work/garden/shapes')
import bpy, stage_shapes as S, random, bmesh, numpy as np, time
for name in ('Rock 0', 'Rock 4', 'Pond edge stone 3'):
    ob = bpy.data.objects[name]
    for params in [((0.003, 0.06), 130), ((0.003, 0.09), 180)]:
        bm = S.baked_bmesh(ob); v0 = bm.calc_volume(); f0 = len(bm.faces)
        size = (lambda t: (t[0]*t[1]*t[2])**(1/3))(S.stone_footprint_radius(bm))
        rng = random.Random(1); t = time.time()
        n = S.cut_planes(bm, rng, params[1], params[0], size, top_bias=0.1)
        S.clean(bm, 0.003)
        areas = np.array([f.calc_area() for f in bm.faces])
        print(name, params, 'size %.2f' % size, 'cuts', n, 'faces', f0, '->', len(bm.faces), 'vol loss %.0f%%' % (100*(1-bm.calc_volume()/v0)), 'area p10/p50/p90 cm2 %.0f %.0f %.0f' % tuple(np.percentile(areas, [10,50,90])*1e4), 'sec %.1f' % (time.time()-t), 'manifold', all(e.is_manifold for e in bm.edges))
