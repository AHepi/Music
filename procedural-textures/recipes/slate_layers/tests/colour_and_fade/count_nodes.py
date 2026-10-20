# What this file does (plain words): builds the COLOUR AND FADE box inside Blender and prints how many nodes it has (so its cost can be
# compared with the other boxes). Use: tests/blender.sh tests/colour_and_fade/count_nodes.py
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'layers'))
import colour_and_fade, layout
tree = colour_and_fade.build_group({})
print('NODES colour_and_fade', len(tree.nodes))
print('NODES layout', len(layout.build_group({}).nodes))
