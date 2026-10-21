# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Writes sol4_street.json: the fourth solution tests.
#   * the milder joint picture (mild1) with the texture filter turned up to 16 (the default in a background Blender run is 2): does the grazing road look sharper?
#   * mild1 together with a SHALLOW real-geometry groove (8 mm, sharp profile), close view and main view: the "hybrid" (the picture makes the joints dark everywhere, the geometry
#     makes the nearest stones catch the light and cast a shadow)
#   * the main camera at 1080 x 1920 (twice the area of 540 x 960; the film's pictures are 1080 wide), baseline and mild1: do the joints still read at the size the painter sees?
# Run: python3 -I b06e_make_solution_jobs_4.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from b06_make_jobs import job, write  # noqa: E402

MILD1 = {'colour_mult': 0.85, 'rough_to': 0.9, 'spec_keep': 0.65, 'coat_keep': 0.55, 'picture': 'joint_cavity_closed.png'}
GEO8 = {'y_min': 3.0, 'y_max': 14.0, 'level': 6, 'depth': 0.008, 'picture': 'joint_height.png'}
GEO8_MAIN = {'y_min': 3.0, 'y_max': 18.0, 'level': 6, 'depth': 0.008, 'picture': 'joint_height.png'}
cl = dict(w=640, h=480, samples=24)
jobs = []
aniso = job('close', 'close_road', 'A', 'wet', 'joint_picture', MILD1, tag='mild1_aniso16b', **cl)
aniso['aniso'] = 'FILTER_16'
jobs.append(aniso)
jobs.append(job('close', 'close_road', 'A', 'wet', 'combo', {'parts': [['joint_picture', MILD1], ['geometry', GEO8]]}, tag='mild1_geo8', **cl))
jobs.append(job('main', 'main', 'A', 'wet', 'combo', {'parts': [['joint_picture', MILD1], ['geometry', GEO8_MAIN]]}, tag='mild1_geo8'))
big = dict(w=1080, h=1920, samples=16)
jobs.append(job('big', 'main', 'A', 'wet', 'baseline', **big))
jobs.append(job('big', 'main', 'A', 'wet', 'joint_picture', MILD1, tag='mild1', **big))
write('sol4_street.json', [['main', 540, 960], ['main', 1080, 1920], ['close_road', 640, 480]], jobs)
