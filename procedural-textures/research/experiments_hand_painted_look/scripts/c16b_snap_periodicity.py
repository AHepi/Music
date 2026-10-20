# What this does: checks that snapping the coordinate to a grid (c16) keeps the tile repeating: runs the 2 x 2 periodicity test for grids 400, 250, 100 and for the non-whole 250.5.
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
src_text = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'c16_coordinate_snap.py')).read().split('grids = [0')[0]
exec(compile(src_text, 'c16head', 'exec'))
res = {}
for g in (400, 250, 100):
    res[f'grid {g}'] = hp.periodicity_check(lambda: snapped(g, name='pc'), 'Colour', 192)
    print(g, res[f'grid {g}'])
res['grid 250.5 (not a whole number)'] = hp.periodicity_check(lambda: snapped(250.5, name='pc2'), 'Colour', 192); print(res['grid 250.5 (not a whole number)'])
json.dump(res, open(os.path.join(hp.OUT, 'data', 'c16_snap_periodicity.json'), 'w'), indent=1)
