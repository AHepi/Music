"""
What this file does: what every store test shares: where the kit and the store are, a fresh empty scene, and a check
that prints PASS lines and stops at the first failure with a plain message.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
BRIEF = os.path.join(PLUGIN, 'brief')
STORE = os.path.join(BRIEF, 'store')
TOOLS = os.path.join(STORE, 'tools')
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)


def fresh_scene():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def check(condition, message):
    if not condition:
        raise AssertionError(message)
