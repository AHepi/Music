# dev check: does the terrain follow mc.ground_height near buildings and the track, and do the props stay off them?
import sys, os, math
ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work'
sys.path.insert(0, ROOT + '/lib'); sys.path.insert(0, ROOT + '/modules')
import numpy as np, bpy
import mine_common as mc
import ground_and_yard as g
mc.clear_scene()
info = g.build('Mine ground and yard')
plan = g.GroundPlan()
# 1. terrain equals mc.ground_height near the track and buildings
worst_track = 0.0
for t in np.linspace(0, 1, 200):
    x, y = mc.track_point(float(t))
    dx, dy = mc.track_direction(float(t))
    for off in (-1.6, -1.0, 0.0, 1.0, 1.6):
        px, py = x - dy * off, y + dx * off
        h, _ = plan.ground(np.array([px]), np.array([py]))
        worst_track = max(worst_track, abs(float(h[0]) - mc.ground_height(px, py)))
print('worst difference from mc.ground_height within 1.6 m of the track:', round(worst_track, 5))
worst_b = 0.0
for rect in g.BUILDING_FOOTPRINTS:
    xs = np.linspace(rect[0] - 1.2, rect[1] + 1.2, 40); ys = np.linspace(rect[2] - 1.2, rect[3] + 1.2, 40)
    gx, gy = np.meshgrid(xs, ys); gx, gy = gx.ravel(), gy.ravel()
    outside = (gx < rect[0]) | (gx > rect[1]) | (gy < rect[2]) | (gy > rect[3])
    h, _ = plan.ground(gx[outside], gy[outside])
    base = np.array([mc.ground_height(a, b) for a, b in zip(gx[outside], gy[outside])])
    # skip points which are inside the engine house floor dip zone only
    worst_b = max(worst_b, float(np.abs(h - base).max()))
print('worst difference from mc.ground_height within 1.2 m of the buildings:', round(worst_b, 5))
# 2. the mesh follows the height function (ray cast straight down onto the mesh object)
terrain = g.ground_mesh_object()
dg = bpy.context.evaluated_depsgraph_get()
errors = []
rng = np.random.default_rng(3)
for _ in range(300):
    x, y = rng.uniform(-13, 8), rng.uniform(-25, -6)
    hit, loc, normal, idx = terrain.ray_cast((x, y, 20.0), (0, 0, -1))
    h, _ = plan.ground(np.array([x]), np.array([y]))
    errors.append(abs(loc.z - float(h[0])) if hit else 99)
print('mesh vs height function in the fine yard: mean %.4f, max %.4f metres' % (np.mean(errors), np.max(errors)))
# 3. puddles
for p in plan.puddles:
    print(p['name'], 'water level', round(p['water_level'], 3), 'lowest ground', round(p['lowest_ground'], 3))
# 4. mesh sanity
mesh = terrain.data
print('terrain vertices', len(mesh.vertices), 'faces', len(mesh.polygons), 'z range', min(v.co.z for v in mesh.vertices), max(v.co.z for v in mesh.vertices))
# slope check: steepest face in the fine zone
co = np.array([v.co[:] for v in mesh.vertices])
print('x range', co[:, 0].min(), co[:, 0].max(), 'y range', co[:, 1].min(), co[:, 1].max())
for o in bpy.data.objects:
    if o.type == 'MESH':
        bb = np.array([o.matrix_world @ __import__('mathutils').Vector(c) for c in o.bound_box])
        print(o.name, 'bounds x %.1f..%.1f y %.1f..%.1f z %.2f..%.2f' % (bb[:, 0].min(), bb[:, 0].max(), bb[:, 1].min(), bb[:, 1].max(), bb[:, 2].min(), bb[:, 2].max()))
