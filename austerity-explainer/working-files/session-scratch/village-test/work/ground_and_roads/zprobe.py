import sys
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy, numpy as np
from place_kit import parts
parts.refresh_ground()
for x,y in [(-52,-3.2),(-54,-2.5),(-33,-2.7),(-6,2.1),(0,1),(24,30),(24,30.2)]:
    print(x,y,round(parts.ground_height_at(x,y),3))
