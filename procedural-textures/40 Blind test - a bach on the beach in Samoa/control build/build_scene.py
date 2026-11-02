import sys, os, math, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, numpy as np
from mathutils import Vector
from lib import *
import terrain, world, bach, plants, props

random.seed(7); np.random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
G = terrain.ground
t0 = time.time()
terrain.build_terrain(); terrain.build_water()
w, sun = world.build_world(haze=float(os.environ.get('HAZE', '0.00004')), strength=float(os.environ.get('SKY', '0.5')))
sun.data.energy = float(os.environ.get('SUN', '6.0'))
M_ = plants.mats()

# ---------------- camera ----------------
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 31; cam_d.sensor_fit = 'HORIZONTAL'; cam_d.sensor_width = 36
cam_d.clip_start = 0.1; cam_d.clip_end = 20000
cam = bpy.data.objects.new('cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cx, cy = -3.6, 1.0
cam.location = (cx, cy, G(cx, cy) + 1.55)
head = math.radians(4); pitch = math.radians(6)
cam.rotation_euler = (math.pi / 2 + pitch, 0, -head)

cam_d.dof.use_dof = True; cam_d.dof.focus_distance = 13.0; cam_d.dof.aperture_fstop = 9.0
import comp
comp.setup(sc)
# ---------------- the bach ----------------
bx, by = -0.9, 12.6
bz = G(bx, by) + 0.72
bach.build_bach((bx, by, bz), -55)

def near_bach(x, y, r=7.5):
    return (x - bx) ** 2 + (y - by) ** 2 < r * r

# ---------------- palms ----------------
palms = [
 (-5.2, 4.2, 9.0, 335, 2.2, 1),
 (-3.6, 15.5, 8.6, 292, 2.2, 2),
 (6.5, 8.2, 9.5, 20, 1.5, 3),
 (5.2, 17.8, 10.5, 330, 2.0, 4),
 (-3.2, 20.5, 8.8, 280, 2.4, 5),
 (9.5, 14.0, 8.0, 70, 1.5, 6),
 (2.0, 26.0, 11.0, 300, 2.0, 7),
 (11.0, 24.0, 10.0, 10, 1.7, 8),
 (-6.0, 32.0, 9.0, 280, 2.5, 9),
 (8.0, 36.0, 11.0, 320, 1.8, 10),
]
for (px, py, ph, pa, pl, ps) in palms:
    plants.make_palm((px, py, G(px, py)), ph, pa, pl, ps, nfr=15, scale=(0.85 if ps == 1 else 1.0))
rnd = random.Random(21)
for k in range(16):
    y = rnd.uniform(40, 150); d = rnd.uniform(10, 40)
    x = float(terrain.shore_x(y)) + d
    plants.make_palm((x, y, G(x, y)), rnd.uniform(9, 13), rnd.uniform(0, 360), rnd.uniform(1, 2.5), 100 + k, nfr=12)

# ---------------- jungle trees and undergrowth ----------------
rnd = random.Random(33)
cnt = 0
while cnt < 90:
    y = rnd.uniform(14, 170)
    d = rnd.uniform(15, 80) if y > 40 else rnd.uniform(18, 70)
    x = float(terrain.shore_x(y)) + d
    if y < 30 and x < 12: continue
    if near_bach(x, y, 10): continue
    r = rnd.uniform(2.4, 4.8) * (1 + y / 260)
    plants.make_tree((x, y, G(x, y) - 0.3), rnd.uniform(4.5, 8.0) * (1 + y / 300), r, 500 + cnt)
    cnt += 1
for (x, y, s) in [(4.6, 7.4, 1), (6.2, 12.5, 2), (3.9, 17.6, 3), (8.0, 10.0, 4), (-0.2, 19.5, 5), (9.5, 6.0, 6), (7.0, 20.0, 7), (11, 17, 8), (2.0, 22.5, 9)]:
    plants.make_banana((x, y, G(x, y) - 0.1), s, scale=rnd.uniform(0.9, 1.3), nl=9)
for (x, y, s) in [(3.4, 7.9, 1), (-2.6, 17.4, 2), (4.5, 15.6, 4), (6.5, 5.0, 5)]:
    plants.make_shrub((x, y, G(x, y)), rnd.uniform(0.7, 1.1), 40 + s, flowers=True)
# low scrub along the top of the beach and between the trees
for k in range(40):
    y = rnd.uniform(0, 70); d = rnd.uniform(9, 16)
    x = float(terrain.shore_x(y)) + d
    if near_bach(x, y, 8) or (y < 12 and x < 6): continue
    plants.make_shrub((x, y, G(x, y)), rnd.uniform(0.6, 1.2), 200 + k, flowers=(rnd.random() < 0.3))
for k in range(60):
    y = rnd.uniform(10, 120); d = rnd.uniform(14, 36)
    x = float(terrain.shore_x(y)) + d
    if near_bach(x, y, 9): continue
    plants.make_shrub((x, y, G(x, y)), rnd.uniform(1.2, 2.2), 300 + k, flowers=False)

# ---------------- grass ----------------
Gm = plants.m_grass()
pts = []
r2 = np.random.RandomState(5)
while len(pts) < 26000:
    x = r2.uniform(-2, 26); y = r2.uniform(0, 48)
    d = x - float(terrain.shore_x(y))
    n = float(fbm2(np.array([x * 0.6]), np.array([y * 0.6]), 3, 3)[0])
    gm = float(smoothstep(9 + 5 * n, 13 + 5 * n, np.array([d]))[0])
    if r2.rand() < gm * 0.9 + 0.01 and not near_bach(x, y, 4.2):
        pts.append((x, y, G(x, y) - 0.01))
plants.grass_field('lawn', np.array(pts), Gm, 0.12, 0.30, 5, 3)
# beach grass tufts at the top of the sand
pts2 = []
while len(pts2) < 1500:
    y = r2.uniform(0, 40); d = r2.uniform(7, 11.5)
    x = float(terrain.shore_x(y)) + d
    if near_bach(x, y, 4.2): continue
    pts2.append((x, y, G(x, y) - 0.01))
Gm2 = plants.m_grass((0.12, 0.2, 0.04), (0.55, 0.55, 0.2))
plants.grass_field('beachgrass', np.array(pts2), Gm2, 0.25, 0.55, 6, 8)

# ---------------- rocks, canoe, driftwood ----------------
Mb = plants.m_basalt()
rr = random.Random(3)
for (yy, off, r) in [(10.5, 0.2, 0.7), (11.2, -0.4, 0.5), (10.0, 1.1, 0.35), (13.5, 0.4, 0.55), (14.3, -0.2, 0.9), (13.0, 1.4, 0.3), (19.0, 0.3, 0.8), (19.8, -0.5, 0.5), (20.4, 0.9, 0.4), (27.0, 0.0, 1.0), (27.8, -0.8, 0.6)]:
    x = float(terrain.shore_x(yy)) + off
    plants.make_rock((x, yy, G(x, yy) + r * 0.1), r, int(yy * 10), Mb, 0.62)
Mwd = props.m_wood_weathered()
props.make_canoe((-1.7, 6.2), 262, L=3.3)
props.make_log((-0.2, 3.3), 2.6, 0.13, 78, 1, Mwd)
props.make_log((-5.2, 12.0), 1.8, 0.1, 100, 2, Mwd)
props.make_log((1.6, 8.2), 1.4, 0.09, 40, 3, Mwd)
# fallen fronds on the sand
pool = plants.frond_pool()
for k in range(5):
    x = rr.uniform(-3.5, 2.0); y = rr.uniform(2, 14)
    o = bpy.data.objects.new('fallen', pool[k % 5])
    o.location = (x, y, G(x, y) + 0.04)
    o.rotation_euler = (0.05, 0.12, rr.uniform(0, 6.28))
    o.scale = (0.8, 0.8, 0.8)
    sc.collection.objects.link(o)
# pebbles / shells / husks
rp = np.random.RandomState(9)
Mpb = simple_mat('pebble', (0.42, 0.34, 0.26, 1), 0.7)
Mpk = simple_mat('shell_pink', (0.7, 0.45, 0.4, 1), 0.5)
for k in range(150):
    x = rp.uniform(-6.5, 3); y = rp.uniform(1.5, 12)
    d = x - float(terrain.shore_x(y))
    if d < 1.2: continue
    s = rp.uniform(0.012, 0.03)
    plants.make_blob('peb', (x, y, G(x, y) + s * 0.2), s, (Mpb if rp.rand() < 0.6 else Mpk) if rp.rand() < 0.93 else Mb, k, 0.6, 1, 0.3)
for k in range(5):
    x = rp.uniform(-4, 1); y = rp.uniform(2, 9)
    plants.make_blob('husk', (x, y, G(x, y) + 0.06), 0.11, simple_mat('husk', (0.20, 0.12, 0.06, 1), 0.95), k + 400, 0.6, 2, 0.6)

# ---------------- distant islands ----------------
Mi = plants.m_leafy('island', (0.015, 0.07, 0.03), (0.04, 0.16, 0.06), 0.02, 0.1)
props.island('island1', (-330, 1700, -15), 230, 175, 4, Mi)
props.island('island2', (-40, 2300, -15), 170, 90, 9, Mi)

# creeping beach plants on the open sand
for k in range(10):
    x = rp.uniform(-2.5, 3.0); y = rp.uniform(1.5, 9)
    d = x - float(terrain.shore_x(y))
    if d < 5: continue
    pp = []
    for q in range(50):
        pp.append((x + rp.normal(0, 0.35), y + rp.normal(0, 0.35), G(x, y) - 0.01))
    plants.grass_field('clump%d' % k, np.array(pp), Gm2, 0.15, 0.4, 5, 30 + k)
# footprints from the steps down to the water
fp = simple_mat('footprint', (0.20, 0.15, 0.10, 1), 0.3)
sx0, sy0 = -4.0, 9.2
ex, ey = float(terrain.shore_x(5.0)) + 1.0, 5.0
for i in range(16):
    t = i / 15
    x = sx0 + (ex - sx0) * t + 0.3 * math.sin(t * 5)
    y = sy0 + (ey - sy0) * t
    side = 0.11 if i % 2 else -0.11
    hdg = math.atan2(ex - sx0, ey - sy0)
    px_ = x + math.cos(hdg) * side; py_ = y - math.sin(hdg) * side
    o = sphere('fp', 0.1, (px_, py_, G(px_, py_) + 0.004), fp, seg=8, ring=6, scale=(0.75, 1.9, 0.03))
    o.rotation_euler = (0, 0, -hdg)
# tide-line debris
Mdeb = simple_mat('debris', (0.16, 0.13, 0.06, 1), 0.9)
for k in range(45):
    y = rp.uniform(2, 34)
    x = float(terrain.shore_x(y)) + 3.3 + 0.5 * math.sin(y * 0.5) + rp.normal(0, 0.15)
    plants.make_blob('deb', (x, y, G(x, y) + 0.01), rp.uniform(0.02, 0.06), Mdeb, k, 0.25, 1, 0.6)
print('build time', round(time.time() - t0, 1))
OUT = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'bach.blend'))
