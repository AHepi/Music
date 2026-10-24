import bpy, time, sys
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
scene = bpy.context.scene
print('start', flush=True)
bpy.ops.mesh.primitive_plane_add(size=20)
bpy.ops.mesh.primitive_cube_add(size=2, location=(0,0,1))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
cam.location = (8,-8,5)
import mathutils
d = mathutils.Vector((0,0,1)) - cam.location
cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
scene.camera = cam
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun','SUN'))
scene.collection.objects.link(sun)
sun.rotation_euler = (0.8,0.2,0.5)
scene.render.resolution_x = 360; scene.render.resolution_y = 240
for eng in sys.argv[sys.argv.index('--')+1:]:
    try:
        scene.render.engine = eng
    except Exception as e:
        print('cannot set', eng, e); continue
    if eng=='CYCLES':
        scene.cycles.samples = 8; scene.cycles.device='CPU'
    t=time.time()
    scene.render.filepath = f'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/ground_and_roads/probe_{eng}.png'
    try:
        bpy.ops.render.render(write_still=True)
        print('rendered', eng, time.time()-t, flush=True)
    except Exception as e:
        print('render failed', eng, e, flush=True)
