import sys, json, math, types, numpy as np, cv2
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
import check_shot as cs
d = sys.argv[1]
args = types.SimpleNamespace(check='/home/user/work/paper-pop-up-film-kit/examples/notice-corner/shot-check.json', facts=d, picture=None)
check, facts, visible, alone, _ = cs.load(args)
W, H = facts['size']; cam = facts['camera']
f = (H/2)/math.tan(math.radians(cam['vertical_fov_degrees'])/2)
meet = np.array(facts['lines_meet']['street']) * [W, H]
outline = cv2.Canny(visible['board'].astype(np.uint8)*255, 50, 150) > 0
ys, xs = np.nonzero(outline)
def turn_left(pts, deg):
    """screen points (x right, y down) after the (level) camera turns left by deg: a pure rotation about the vertical"""
    a = math.radians(deg)
    u = pts[:,0] - W/2; v = pts[:,1] - H/2
    # direction in camera space: (u, f, -v) ; camera turning left by a rotates world directions right by a
    x = u*math.cos(a) + f*math.sin(a); z = -u*math.sin(a) + f*math.cos(a)
    return np.stack([W/2 + f*x/z, H/2 + f*v/z], 1)
pts = np.stack([xs, ys], 1).astype(float)
for deg in (0, 1.6, -1.6, 1.0):
    p = turn_left(pts, deg); m = turn_left(meet[None].astype(float), deg)[0]
    dist = np.hypot(p[:,0]-m[0], p[:,1]-m[1]); k = dist.argmin()
    print(f'turn left {deg:+.1f} deg: meet at {m[0]/W:.3f},{m[1]/H:.3f}; nearest board edge {dist[k]/W:.4f} of width (dx {(p[k,0]-m[0]):.0f} px, dy {(p[k,1]-m[1]):.0f} px)')
