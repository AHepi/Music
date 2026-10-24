import sys, os
sys.path.insert(0, os.path.join(HERE, 'lib')); sys.path.insert(0, os.path.join(HERE, 'modules'))
import mine_common as mc
# chimney pulled back/in toward the engine-house back-left corner
mc.LAYOUT['chimney']['centre_x'] = -5.1
mc.LAYOUT['chimney']['centre_y'] = 9.0
import chimney_and_smoke as cs
G = cs.TOTAL_HEIGHT
cs.PLUME_POINTS = [
    (-5.10, 9.00, G + 0.25),
    (-5.10, 8.95, 19.0),
    (-4.60, 8.60, 21.4),
    (-3.40, 7.90, 23.8),
    (-1.40, 7.00, 26.2),
    (1.60, 5.80, 28.8),
    (5.20, 4.40, 31.6),
    (9.50, 2.80, 34.6),
    (14.50, 1.00, 38.0),
    (20.00, -1.00, 41.5),
    (26.00, -3.00, 45.0),
]
cs.PLUME_BIG_RADIUS = 1.8
cs.PLUME_BIG_AT = 28.0
import village_and_sky as vs
vs.BRICK_TINTS[:] = [(0.62, 0.52, 0.48), (0.55, 0.50, 0.48), (0.50, 0.52, 0.55), (0.60, 0.55, 0.50), (0.50, 0.42, 0.38),
                     (0.50, 0.50, 0.50), (0.58, 0.50, 0.45), (0.45, 0.45, 0.46), (0.55, 0.54, 0.50), (0.50, 0.52, 0.55)]
for ring in vs.HILL_RINGS:
    if ring['name'] == 'Near hills':
        ring.update(r_in=40.0, r_crest=135.0, low=10.0, high=25.0, mist=0.06)
    if ring['name'] == 'Middle hills':
        ring.update(colour=(0.09, 0.12, 0.16))
    if ring['name'] == 'Far hills':
        ring.update(colour=(0.18, 0.24, 0.30), mist=0.35)
import ground_and_yard as gy
for p in gy.PUDDLES:
    if p['name'] == 'front left pool': p.update(centre=(-9.5, -17.5), size=(3.6, 1.9))
    if p['name'] == 'middle pool': p.update(size=(3.2, 1.5))
    if p['name'] == 'back yard pool': p.update(size=(3.8, 1.9))

cs.PLUME_SMALL_RADIUS = 0.42
def _radius(arc_length):
    grown = min(arc_length / cs.PLUME_BIG_AT, 1.7)
    return cs.PLUME_SMALL_RADIUS + (cs.PLUME_BIG_RADIUS - cs.PLUME_SMALL_RADIUS) * grown ** 1.5
cs.plume_radius = _radius
