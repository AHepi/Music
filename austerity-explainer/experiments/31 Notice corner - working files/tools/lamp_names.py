# Imports the gas lamp prop twice and prints its objects' and materials' names.
import bpy, sys, os
sys.path.insert(0, 'KIT/paper-film/blender/pit-village')
from set_dressing import PROPS_FOLDER
bpy.ops.wm.read_factory_settings(use_empty=True)
for i in range(2):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PROPS_FOLDER, 'gas-lamp-post.glb'))
    new = [o for o in bpy.data.objects if o not in before]
    print('IMPORT', i, [(o.name, [m.name for m in getattr(o.data, 'materials', [])]) for o in new])
