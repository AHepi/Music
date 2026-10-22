# usage: blender -b courtyard.blend -P preview_kit.py -- KITDIR OUTPREFIX
# Small EEVEE previews (480 x 320, 16 samples) of the photo camera and the roof-edge camera with the weathering kit put on in memory (nothing is saved).
import sys, json, time, math
args = sys.argv[sys.argv.index('--')+1:]
kitdir, prefix = args[0], args[1]
sys.path.insert(0, kitdir); sys.dont_write_bytecode = True
import bpy
from mathutils import Vector
import apply_weathering as aw
t0 = time.time()
w = aw.apply('japanese_courtyard', 'mossy_courtyard_rough', pieces=False, strict=False, earlier=False)
print('APPLY', round(time.time()-t0, 1), 's')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.eevee.taa_render_samples = 16
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 480, 320, 100
sc.render.image_settings.file_format = 'JPEG'; sc.render.image_settings.quality = 85
cams = {c['name']: c for c in w.kit.settings.get('cameras')}
def make_cam(name):
    spec = cams[name]
    if name in bpy.data.objects: return bpy.data.objects[name]
    cd = bpy.data.cameras.new(name); cd.sensor_fit = 'VERTICAL'
    cd.angle_y = math.radians(spec['fov_v']); cd.clip_end = 400
    ob = bpy.data.objects.new(name, cd); sc.collection.objects.link(ob)
    ob.location = Vector(spec['location'])
    d = Vector(spec['look_at']) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob
for name in (args[2].split(',') if len(args) > 2 else ('photo', 'roof_edge')):
    cam = bpy.data.objects.get('Camera') if name == 'photo' and bpy.data.objects.get('Camera') else make_cam(name)
    if name == 'photo' and sc.camera is not None: cam = sc.camera
    sc.camera = cam
    try: w.camera(cam, plate_height=320)
    except Exception as e: print('camera hook', repr(e)[:120])
    sc.render.filepath = f'{prefix}_{name}.jpg'
    t = time.time(); bpy.ops.render.render(write_still=True)
    print('RENDERED', name, round(time.time()-t, 1), 's')
