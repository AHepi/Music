import sys, bpy
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit import scene_read
o=bpy.data.objects['Dirt road ribbon']
pl,w=scene_read.lane_skeleton(o)
print('SKEL',pl,w)
import math
print('SKEL true start', (0.0,0.0), 'true end', (50, 6*math.sin(50/8)))
