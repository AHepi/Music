# What this does: checks set_dressing.export_for_film's required folder in an empty scene: called with no
# folder it must stop with its plain message; called with a scratch folder it must write the three files.
import os
import sys

import bpy

sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/pit-village')
import set_dressing  # noqa: E402

out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.object.camera_add(location=(0, -5, 1.6))
camera = bpy.context.active_object
bpy.ops.mesh.primitive_cube_add(size=1)
try:
    set_dressing.export_for_film(camera, 'guard-test', 60.4, 'export_guard_test.py')
    print('GUARD FAILED: it wrote without a folder')
except SystemExit as stop:
    print('GUARD STOPPED:', stop)
set_dressing.export_for_film(camera, 'guard-test', 60.4, 'export_guard_test.py', folder=out)
print('WROTE:', sorted(os.listdir(out)))
