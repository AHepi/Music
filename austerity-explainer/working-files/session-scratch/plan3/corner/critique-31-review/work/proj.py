import math
import numpy as np
YAW = math.radians(6.87)
END = np.array([3.10, 17.85, 3.1882]); START = np.array([2.9931, 16.3538, 3.1882])
def proj(P, C=END, vfov=60.4, aspect=1080/1920):
    P = np.asarray(P, float); d = P - C
    f = np.array([-math.sin(YAW), math.cos(YAW), 0]); r = np.array([math.cos(YAW), math.sin(YAW), 0])
    z = d @ f; x = d @ r; y = d[2]
    t = math.tan(math.radians(vfov/2))
    return 0.5 + (x/z)/(2*t*aspect), 0.5 - (y/z)/(2*t), z
def pavement(y): return y*math.tan(math.radians(4)) + 0.13
