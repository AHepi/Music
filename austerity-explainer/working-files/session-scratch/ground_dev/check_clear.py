# dev check: do the clutter and puddle objects keep clear of the track and the building footprints?
import sys
ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work'
sys.path.insert(0, ROOT + '/lib'); sys.path.insert(0, ROOT + '/modules')
import numpy as np, bpy
import mine_common as mc
import ground_and_yard as g
mc.clear_scene()
g.build('Mine ground and yard')
plan = g.GroundPlan()
for name in (g.LUMPS_OBJECT_NAME, g.PROPS_OBJECT_NAME, g.PUDDLE_OBJECT_NAME):
    obj = bpy.data.objects[name]
    co = np.array([v.co[:] for v in obj.data.vertices])
    dt = plan.distance_to_track(co[:, 0], co[:, 1])
    db = plan.distance_to_buildings(co[:, 0], co[:, 1])
    print('%-52s verts %6d  min distance to track %.2f  to building footprints %.2f' % (name, len(co), dt.min(), db.min()))
# also the heap lumps near the track?
for k, rect in enumerate(g.BUILDING_FOOTPRINTS):
    print('footprint', k, [round(v, 2) for v in rect])
print('track from', mc.track_point(0.0), 'to', mc.track_point(1.0))
obj = bpy.data.objects[g.PROPS_OBJECT_NAME]
co = np.array([v.co[:] for v in obj.data.vertices])
db = plan.distance_to_buildings(co[:, 0], co[:, 1])
close = co[db < 0.8]
print('props vertices within 0.8 m of a footprint:', len(close), close[:5].round(2).tolist())
