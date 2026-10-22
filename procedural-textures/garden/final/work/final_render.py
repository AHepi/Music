# What this does (plain words): draws SEVERAL pictures of one saved garden scene in ONE Blender start (so the card pays for one start-up, not one per picture).
# For each picture it (1) tells the weathering kit how big one picture dot is for that camera and height (the 'camera_for_picture' step of the surfaces stage,
# done here directly on the kit's scale nodes so the kit code does not have to travel) and (2) calls the light builder's render_job.main() with that picture's options.
# Run on the card: /workspace/blender/blender -b --disable-autoexec FILE.blend -P final_render.py -- JOBS.json
# JOBS.json = {"pictures": [{"out": "/abs/base", "camera": "photo", "size": "2400x1600", "samples": 512, "seed": 7, "exr": true, "extra": ["--check-groups"]}, ...]}
import bpy, sys, os, json, math, time, traceback

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.join(os.path.dirname(HERE), 'stage')
sys.path.insert(0, STAGE)
import render_job

jobs = json.load(open(sys.argv[sys.argv.index('--') + 1]))
t_all = time.time()


def set_dot_angle(camera, height):
    """Same as weathering_stage.camera_for_picture: Dot Angle on every kit scale node = angular size of one picture dot."""
    if camera is None or camera.type != 'CAMERA':
        return 0
    val = 2.0 * math.tan(camera.data.angle_y / 2.0) / float(height)
    n = 0
    for m in bpy.data.materials:
        nt = m.node_tree
        if nt is None:
            continue
        for node in nt.nodes:
            if node.get('wk') == 'scale':
                node.inputs['Dot Angle'].default_value = val
                n += 1
    return n


# optional extra cameras for close views: jobs['views'] = {name: {"loc": [x,y,z], "target": [x,y,z], "fov_v": degrees}}  (made in memory only, never saved)
from mathutils import Vector
for vname, v in (jobs.get('views') or {}).items():
    cd = bpy.data.cameras.new(vname)
    cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(v['fov_v'])
    co = bpy.data.objects.new(vname, cd)
    bpy.context.scene.collection.objects.link(co)
    co.location = v['loc']
    co.rotation_euler = (Vector(v['target']) - Vector(v['loc'])).to_track_quat('-Z', 'Y').to_euler()

results = []
for p in jobs['pictures']:
    t = time.time()
    cam = bpy.data.objects.get(p.get('camera', 'photo'))
    h = int(p['size'].lower().split('x')[1])
    nscale = set_dot_angle(cam, h) if jobs.get('look', 'real') == 'real' else 0
    argv = ['--out', p['out'], '--camera', p.get('camera', 'photo'), '--size', p['size'], '--samples', str(p.get('samples', 384)), '--seed', str(p.get('seed', 7)),
            '--require-gpu'] + (['--exr'] if p.get('exr') else []) + list(p.get('extra', []))
    sys.argv = [sys.argv[0], '--'] + argv
    print('FINAL_RENDER_START', p['out'], 'dot-angle nodes set:', nscale, flush=True)
    try:
        render_job.main()
        results.append((p['out'], 'ok', round(time.time() - t, 1)))
    except SystemExit as e:
        results.append((p['out'], 'exit: ' + str(e), round(time.time() - t, 1)))
        print('FINAL_RENDER_EXIT', e, flush=True)
    except Exception:
        results.append((p['out'], 'error', round(time.time() - t, 1)))
        traceback.print_exc()
print('FINAL_RENDER_ALL', json.dumps(results), 'total seconds', round(time.time() - t_all, 1), flush=True)
