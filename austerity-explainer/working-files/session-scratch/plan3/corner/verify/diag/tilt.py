import sys, json, math, numpy as np
sys.path.insert(0, '/home/user/work/paper-pop-up-film-kit/paper-film/tools')
import check_shot as cs
check = json.load(open('/home/user/work/paper-pop-up-film-kit/examples/notice-corner/shot-check.json'))
match = check['reference']['camera_match']; size = match['picture_size']
facts = json.load(open('tests/e-camera-tilted/facts.json')); cam = facts['camera']
def project_tilted(camera, point, size, tilt):
    x, y, z, turn, fov = camera; w, h = size
    yaw = math.radians(turn); t = math.radians(tilt)
    ahead0 = np.array([-math.sin(yaw), math.cos(yaw), 0.0]); right = np.array([math.cos(yaw), math.sin(yaw), 0.0])
    ahead = ahead0*math.cos(t) + np.array([0,0,1.0])*math.sin(t); up = np.cross(right, ahead)
    v = np.array(point) - np.array([x, y, z]); depth = v @ ahead
    focal = (h/2)/math.tan(math.radians(fov)/2)
    return np.array([w/2 + focal*(v@right)/depth, h/2 - focal*(v@up)/depth]), depth
ours = (cam['at'][0], cam['at'][1], cam['at'][2], cam['turn_degrees'], cam['vertical_fov_degrees'])
s = 1080/size[0]
for name, item in match['points'].items():
    lv, _ = cs.project(ours, item['at'], size); lt, _ = project_tilted(ours, item['at'], size, cam['tilt_degrees'])
    print(f"{name}: level model error {np.hypot(*(lv-item['seen']))*s:.0f} px, with the real 3-degree tilt {np.hypot(*(lt-item['seen']))*s:.0f} px (at 1080 wide)")
# sanity: tilted model reproduces facts lines_meet for e
d = np.array([0,1,0.069927]); far = np.array(cam['at']) + d/np.linalg.norm(d)*1e5
p,_ = project_tilted(ours, far, (1080,1920), cam['tilt_degrees']); print('tilted model street meet', p/[1080,1920], 'facts', facts['lines_meet']['street'])
p,_ = cs.project(ours, far, (1080,1920)); print('check_shot.project (level) street meet', p/[1080,1920])
