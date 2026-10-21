# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# The ONE script that changes the street copy's road: it puts the JOINTS layer (joint_layer.py) on the road material "street_setts" AFTER the wetness layer, so that the joints
# between the setts read as grooves between raised stones in every light and every wetness. The street file itself is not changed on disk: like the wetness layer
# (tools/apply_wetness_to_set.py), the layer is put on inside Blender each time a picture is drawn. Nothing in the film project's own folder is touched.
#
# Use (inside Blender, with the street copy open):
#     import apply_wetness_to_set as aw
#     import apply_joints_to_set as aj
#     aw.apply(wetness=0.85, puddles=0.5)       # the wetness layer first (round 2)
#     aj.apply()                                 # the JOINTS layer with the chosen settings (see DEFAULTS in joint_layer.py)
#     aj.apply(strength=0.6)                     # a milder joint: every effect of the layer scaled to 0.6 (0 = off = round 2 exactly)
#     aj.set_dials(strength=0.8, darkness=0.4)   # change a setting of the layer that is already on
#     aj.apply_real_grooves()                    # OPTIONAL, plate only: real 8 mm grooves cut into the road between y 0 and 22 m (not in the glb)
#     aj.remove()                                # take it all off again
# As a "run this after the layer is on" script for the study's picture runner (a job file's "after_apply"), use apply_joints_after_wetness.py.
#
# Dials (short names; the long names are on the layer's node): strength, darkness, dullness, relief, edge_shade, puddle_cover, photo_relief_in_joints, spec_cut, coat_cut,
# dull_roughness, shadow, far_share, fade_start, fade_end. What each does is at the top of joint_layer.py and in the recipe note.
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))        # street_wet
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402
import joint_layer as jl  # noqa: E402

_STATE = {}


def apply(**dials):
    """Puts the JOINTS layer on the road. Call it after aw.apply(). Returns the layer's node. Calling it twice takes the first one off first."""
    remove()
    wetness_node = aw.APPLIED['street_setts'][0]
    node, undo = jl.add_joints_to_material(bpy.data.materials['street_setts'], wetness_node, **dials)
    _STATE['node'], _STATE['undo'] = node, undo
    return node


def set_dials(**dials):
    """Changes dials of the layer that is already on (by short name). 'shadow' only takes effect if it was above 0 when the layer was put on."""
    node = _STATE['node']
    for key, value in dials.items():
        node.inputs[jl.DIAL_SOCKETS[key]].default_value = value


def apply_real_grooves(**options):
    """Plate only: real grooves on the near road (y_min, y_full, y_max, level, depth; see joint_layer.add_real_groove_geometry). The layer's own relief is best set to 0 then."""
    _STATE['undo_geometry'] = jl.add_real_groove_geometry(bpy.data.objects['street_setts'], **options)


def remove():
    if _STATE.get('undo_geometry'):
        _STATE.pop('undo_geometry')()
    if _STATE.get('undo'):
        _STATE.pop('undo')()
        _STATE.pop('node', None)
