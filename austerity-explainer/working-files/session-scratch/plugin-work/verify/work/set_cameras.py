"""What this does: moves/adds cameras in a trial copy of a scene file so composition can be tried. Run: blender -b IN.blend --python set_cameras.py -- OUT.blend"""
import sys
import bpy
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
def aim(name, location, target, lens):
    cam = bpy.data.objects.get(name)
    if cam is None:
        data = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    cam.rotation_euler = (Vector(target) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
aim('Camera A', (-4.8, 3.4, 1.3), (0.9, -0.4, -0.75), 24)
aim('Camera A2', (-5.5, 3.3, 1.5), (1.8, 0.0, -0.8), 26)
aim('Camera A3', (-2.2, 3.5, 1.2), (2.8, 0.2, -0.7), 28)
aim('Camera B', (1.2, 1.9, -0.1), (3.6, 0.5, -0.8), 28)
bpy.ops.wm.save_as_mainfile(filepath=out)
