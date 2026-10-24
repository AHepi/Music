"""Scratch (views-and-models helper): imports a Works set file (the factories, exported from the assembled scene, so already
in the lane's frame) into the open works-lane.blend as it is, without assemble_works.py's lowering of the ground under
the yards: the state round 2 found (the yards' setts 2 cm over the lane's ground). Use:
blender -b works-lane.blend --python lay_factories_on_lane.py --python model_lint.py -- --glb FACTORIES.glb [model_lint options]"""
import sys
import bpy
argv = sys.argv[sys.argv.index('--') + 1:]
path = argv[argv.index('--glb') + 1]
bpy.ops.import_scene.gltf(filepath=path)
print('lay_factories_on_lane: imported', path, flush=True)
