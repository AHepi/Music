import bpy
from mathutils import Vector
sc = bpy.context.scene
for name, loc, target, lens in (('Place cottages_south cam 1', (-19.5, -3.2, 3.2), (-25.5, -10.2, 2.3), 30), ('Place cottages_south cam 2', (10.5, -3.5, 2.8), (4.2, -8.0, 1.8), 30)):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_end = 1500
    cam = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(cam)
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/cottages_south/batch.blend')
