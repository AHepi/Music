# What this does: projects Blender points into the composed camera (same maths as check_shot.project), for choosing moves.
import sys, math
import numpy as np
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
from check_shot import project
CAM = (2.96, 17.85, 3.1882, 6.87, 60.4)
def screen(p, cam=CAM):
    (x, y), d = project(cam, p, (1080, 1920))
    return round(x / 1080, 3), round(y / 1920, 3), round(d, 2)
if __name__ == '__main__':
    T = math.tan(math.radians(4))
    for x, y in [(0.0, 20.5), (0.5, 20.5), (0.3, 20.0), (1.0, 20.0), (0.0, 21.0), (-0.5, 21.5), (0.5, 21.0)]:
        road = y * T
        print((x, y), 'centre', screen((x, y, road + 0.436)), 'foot', screen((x, y, road)))
