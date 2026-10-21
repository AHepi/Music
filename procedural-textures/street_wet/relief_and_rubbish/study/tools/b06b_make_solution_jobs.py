# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Writes the job file of the first solution tests (street file): sol1_street.json. The solutions are variants of the road material (see b02_lighting_and_variants.py):
#   joint_a   the joint picture, colour only          (joints 0.45 as bright as the stone)
#   joint_b   the joint picture, colour + dull joints  (colour 0.45, roughness 0.95, specular x0.25, coat x0.15 in the joints)
#   joint_c   the joint picture, strong                (colour 0.30, roughness 1.0, specular x0.05, coat 0)
#   geometry  real geometry (a modifier cuts the near road into small faces and presses the joints down 2.5 cm by the soft cavity picture)
#   geometry_sharp  real geometry with a sharp groove profile (2 cm deep, stone tops flat)
#   combo     the joint picture and real geometry together
# Run: python3 -I b06b_make_solution_jobs.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from b06_make_jobs import job, write  # noqa: E402

JP_B = {'colour_mult': 0.45, 'rough_to': 0.95, 'spec_keep': 0.25, 'coat_keep': 0.15}
JP_A = {'colour_mult': 0.45, 'rough_to': None, 'spec_keep': None, 'coat_keep': None}
JP_C = {'colour_mult': 0.30, 'rough_to': 1.0, 'spec_keep': 0.05, 'coat_keep': 0.0}
GEO = {'y_min': 3.0, 'y_max': 14.0, 'level': 6, 'depth': 0.025}
GEO_SHARP = {'y_min': 3.0, 'y_max': 14.0, 'level': 6, 'depth': 0.02, 'picture': 'joint_height.png'}
GEO_MAIN_SHARP = {'y_min': 3.0, 'y_max': 18.0, 'level': 6, 'depth': 0.02, 'picture': 'joint_height.png'}
cl = dict(w=640, h=480, samples=24)
sol = []
sol.append(job('close', 'close_road', 'A', 'wet', 'joint_picture', JP_A, tag='joint_a', **cl))
sol.append(job('close', 'close_road', 'A', 'wet', 'joint_picture', JP_B, tag='joint_b', **cl))
sol.append(job('close', 'close_road', 'A', 'wet', 'joint_picture', JP_C, tag='joint_c', **cl))
sol.append(job('close', 'close_road', 'A', 'wet', 'geometry', GEO, tag='geometry', **cl))
sol.append(job('close', 'close_road', 'A', 'wet', 'geometry', GEO_SHARP, tag='geometry_sharp', **cl))
sol.append(job('close', 'close_road', 'A', 'wet', 'combo', {'parts': [['joint_picture', JP_B], ['geometry', GEO_SHARP]]}, tag='combo_b_geosharp', **cl))
sol.append(job('close', 'close_road', 'A', 'dry', 'joint_picture', JP_B, tag='joint_b', **cl))
sol.append(job('main', 'main', 'A', 'wet', 'joint_picture', JP_B, tag='joint_b'))
sol.append(job('main', 'main', 'A', 'wet', 'joint_picture', JP_C, tag='joint_c'))
sol.append(job('main', 'main', 'A', 'wet', 'geometry', GEO_MAIN_SHARP, tag='geometry_sharp'))
sol.append(job('main', 'main', 'A', 'wet', 'combo', {'parts': [['joint_picture', JP_B], ['geometry', GEO_MAIN_SHARP]]}, tag='combo_b_geosharp'))
sol.append(job('main', 'main', 'A', 'dry', 'joint_picture', JP_B, tag='joint_b'))
for L in 'CDE':
    sol.append(job('main', 'main', L, 'wet', 'joint_picture', JP_B, tag='joint_b'))
for L in 'CDE':
    sol.append(job('close', 'close_road', L, 'wet', 'joint_picture', JP_B, tag='joint_b', **cl))
sol.append(job('main', 'main', 'A', 'heavy', 'joint_picture', JP_B, tag='joint_b'))
sol.append(job('main', 'main', 'E', 'heavy', 'joint_picture', JP_B, tag='joint_b'))
sol.append(job('close', 'close_road', 'E', 'wet', 'geometry', GEO_SHARP, tag='geometry_sharp', **cl))
sol.append(job('close', 'close_road', 'D', 'wet', 'geometry', GEO_SHARP, tag='geometry_sharp', **cl))
write('sol1_street.json', [['main', 540, 960], ['close_road', 640, 480]], sol)
