# What this does: checks that the shared helper scripts in lib/contrib can be imported inside Blender.
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib')); sys.path.insert(0, os.path.join(HERE, '..', 'lib', 'contrib'))
import bpy
for name in ('builder', 'stone_tools', 'hp_tools', 'gn_tools', 'layout_tools', 'relax_tools'):
    try:
        __import__(name); print('IMPORT OK', name)
    except Exception as problem:
        print('IMPORT FAILED', name, repr(problem))
