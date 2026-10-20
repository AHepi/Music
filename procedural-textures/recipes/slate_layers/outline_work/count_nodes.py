# What this does (plain words): counts the nodes inside the OUTLINE AND SHADOW box (and the other layer boxes for comparison). Run inside Blender:
#   blender -b --disable-autoexec --python count_nodes.py
import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'layers'))
import layer_interface as li  # noqa: E402
import outline_and_shadow, damage, moss, colour_and_fade, layout  # noqa: E402
for module in (outline_and_shadow, damage, moss, colour_and_fade, layout):
    tree = module.build_group({})
    print('NODES', module.GROUP_NAME, len(tree.nodes))
