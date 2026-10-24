# Renders close-up check views of the saved street set (not part of the deliverable).
import bpy, sys, math
from mathutils import Vector
out = sys.argv[sys.argv.index('--')+1]
scene = bpy.context.scene
views = {
 'cottage_right': ((1.0, 14.0, 2.6), (4.15, 20.0, 3.5)),
 'cottage_left': ((-0.5, 22.0, 3.2), (-4.15, 27.0, 4.0)),
 'roofs': ((0.0, 10.0, 10.0), (-6, 30.0, 9.0)),
 'colliery': ((3.0, 70.0, 7.0), (0.0, 86.0, 14.0)),
}
for name, (eye, target) in views.items():
    cam_data = bpy.data.cameras.new(name); cam_data.angle = math.radians(50)
    cam = bpy.data.objects.new(name, cam_data); scene.collection.objects.link(cam)
    cam.location = eye
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = 640, 480
    scene.eevee.taa_render_samples = 12
    scene.render.filepath = f'{out}/close_{name}.png'
    bpy.ops.render.render(write_still=True)
