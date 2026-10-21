# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Writes sol2_street.json: the second solution tests. The first try (joint_b, joint_c) made the joints jet black with ragged edges (contrast 0.85 where the dry road has 0.33),
# so these use the SOFTER joint picture (joint_cavity_soft.png) and weaker settings; and the real geometry tests of the first list. Close view, lighting A, wet.
#   soft1  colour 0.7, roughness 0.9, specular x0.5, coat x0.35     soft2  colour 0.6, 0.95, 0.35, 0.25     soft3  colour 0.8, 0.9, 0.6, 0.5
# Run: python3 -I b06c_make_solution_jobs_2.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from b06_make_jobs import job, write  # noqa: E402

SOFT = 'joint_cavity_soft.png'
S1 = {'colour_mult': 0.7, 'rough_to': 0.9, 'spec_keep': 0.5, 'coat_keep': 0.35, 'picture': SOFT}
S2 = {'colour_mult': 0.6, 'rough_to': 0.95, 'spec_keep': 0.35, 'coat_keep': 0.25, 'picture': SOFT}
S3 = {'colour_mult': 0.8, 'rough_to': 0.9, 'spec_keep': 0.6, 'coat_keep': 0.5, 'picture': SOFT}
GEO = {'y_min': 3.0, 'y_max': 14.0, 'level': 6, 'depth': 0.025}
GEO_SHARP = {'y_min': 3.0, 'y_max': 14.0, 'level': 6, 'depth': 0.02, 'picture': 'joint_height.png'}
cl = dict(w=640, h=480, samples=24)
jobs = []
for tag, a in (('soft1', S1), ('soft2', S2), ('soft3', S3)):
    jobs.append(job('close', 'close_road', 'A', 'wet', 'joint_picture', a, tag=tag, **cl))
jobs.append(job('close', 'close_road', 'A', 'dry', 'joint_picture', S2, tag='soft2', **cl))
jobs.append(job('close', 'close_road', 'A', 'wet', 'geometry', GEO, tag='geometry', **cl))
jobs.append(job('close', 'close_road', 'A', 'wet', 'geometry', GEO_SHARP, tag='geometry_sharp', **cl))
jobs.append(job('close', 'close_road', 'A', 'wet', 'combo', {'parts': [['joint_picture', S2], ['geometry', GEO_SHARP]]}, tag='combo_soft2_geosharp', **cl))
write('sol2_street.json', [['main', 540, 960], ['close_road', 640, 480]], jobs)
