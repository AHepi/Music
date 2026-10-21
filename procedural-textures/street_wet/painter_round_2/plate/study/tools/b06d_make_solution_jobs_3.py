# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Writes sol3_street.json: the third solution tests. The soft joint picture of the second try (soft1 to soft3) made the joints much darker than in the DRY road (contrast 0.6
# where the dry road has 0.33), so these are two MILDER settings on the picture with the gaps in the joint lines bridged (joint_cavity_closed.png), tried in lighting A on both cameras,
# then the hard lightings; and one test of the texture filter ("anisotropic filtering": a setting that keeps a texture sharp when it is seen at a grazing angle, as the road is).
#   mild1  colour 0.85, roughness 0.9, specular x0.65, coat x0.55        mild2  colour 0.9, roughness 0.85, specular x0.75, coat x0.7
# Run: python3 -I b06d_make_solution_jobs_3.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from b06_make_jobs import job, write  # noqa: E402

PIC = 'joint_cavity_closed.png'
M1 = {'colour_mult': 0.85, 'rough_to': 0.9, 'spec_keep': 0.65, 'coat_keep': 0.55, 'picture': PIC}
M2 = {'colour_mult': 0.9, 'rough_to': 0.85, 'spec_keep': 0.75, 'coat_keep': 0.7, 'picture': PIC}
cl = dict(w=640, h=480, samples=24)
jobs = []
for tag, a in (('mild1', M1), ('mild2', M2)):
    jobs.append(job('close', 'close_road', 'A', 'wet', 'joint_picture', a, tag=tag, **cl))
    jobs.append(job('main', 'main', 'A', 'wet', 'joint_picture', a, tag=tag))
jobs.append(job('close', 'close_road', 'A', 'dry', 'joint_picture', M1, tag='mild1', **cl))
jobs.append(job('main', 'main', 'A', 'dry', 'joint_picture', M1, tag='mild1'))
for L in 'CDE':
    jobs.append(job('main', 'main', L, 'wet', 'joint_picture', M1, tag='mild1'))
jobs.append(job('main', 'main', 'E', 'wet', 'joint_picture', M2, tag='mild2'))
jobs.append(job('main', 'main', 'A', 'heavy', 'joint_picture', M1, tag='mild1'))
aniso = job('close', 'close_road', 'A', 'wet', 'joint_picture', M1, tag='mild1_aniso16', **cl)
aniso['aniso'] = 'FILTER_16'
jobs.append(aniso)
write('sol3_street.json', [['main', 540, 960], ['close_road', 640, 480]], jobs)
