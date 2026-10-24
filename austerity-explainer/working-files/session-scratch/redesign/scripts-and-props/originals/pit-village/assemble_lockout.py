# What this does: puts together the "lockout" scene for the plan 3 test (log 29): the pit village
# street (street.blend) with props from the props library placed in it, in 1926 during the miners'
# lockout, at dusk:
#   - a handcart with coal sacks in the street near the camera (coal picked from the tips)
#   - a brazier burning on the right, with a lit glow, beside a notice board on posts carrying the
#     colliery's lock-out notice
#   - dustbins, a barrel, pails and a coal pile by the doorways further up
#   - the colliery's iron gates shut across the top of the street, with its name board
# Then, when asked:
#   --plate FILE    renders the plate (the picture the repaint starts from) from the main camera
#   --preview FILE  renders a quick small version of the same view
#   --export        writes the scene for the film engine: lockout-set.glb (everything the painting is
#                   shone onto) and lockout-signs.glb (the name board and the notice, which keep their
#                   own lettering), and lockout-camera.json (the plate camera, for the projector)
# Run (EEVEE needs a virtual screen):
#   Xvfb :96 -screen 0 1920x1080x24 &
#   DISPLAY=:96 blender -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_lockout.py -- --preview out.png
# Units are metres; Blender is z-up, the street runs along +y and rises 4 degrees.

import math
import os
import sys

import bpy
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from set_dressing import ground_height, place_prop, wooden_post, brazier_fire, render, export_for_film   # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def option(name, default=None):
    return arguments[arguments.index(name) + 1] if name in arguments else default

# the plate camera: a little left of the street's middle, eye height, looking up the street and a
# little to the right, so the right-hand cottages, the brazier and the notice are in view and the
# pithead rises above the roofs. The plate is drawn a little wider than the film frame (44 against
# 40 degrees), so the camera can move without running off the painting.
CAMERA_POSITION = Vector((-1.0, 1.2, 0.0))
CAMERA_EYE_HEIGHT = 1.55
CAMERA_YAW_DEGREES = -6.0          # turn to the right (negative about z)
CAMERA_PITCH_DEGREES = 8.0         # look up a little
PLATE_FOV_DEGREES = 44.0


def build_scene():
    for name in ('props', 'signs'):
        if name not in bpy.data.collections:
            collection = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(collection)
    # near the camera: the handcart with coal sacks, and a few lumps of coal in the road
    # (the sacks go down first, so they stand on the road, not on the cart)
    sacks = place_prop('coal-sacks.glb', -0.2, 8.4, turn_degrees=18)
    for o in list(sacks.children_recursive):   # the two standing sacks read as clay jars once painted
        if o.name.startswith('sack-standing'):
            bpy.data.objects.remove(o, do_unlink=True)
    place_prop('handcart.glb', -1.75, 9.6, turn_degrees=-70)
    place_prop('coal-pile.glb', 0.75, 8.0, turn_degrees=-20, scale=0.25)   # a few picked lumps: coal was scarce
    place_prop('wooden-pail.glb', 1.75, 9.0, turn_degrees=40)
    place_prop('hurricane-lantern.glb', -0.55, 10.1, turn_degrees=10)
    place_prop('spade.glb', -1.15, 8.9, turn_degrees=70)
    # the brazier with its fire, and the notice board on two posts beside it
    place_prop('brazier-drum.glb', 0.95, 10.4)
    brazier_fire(0.95, 10.4)
    board = place_prop('notice-on-board.glb', 2.25, 13.6, turn_degrees=-17, lift=1.05, collection='signs')
    bpy.context.view_layer.update()   # so the board's matrix_world holds its new place
    board_timber = next((m for o in board.children_recursive if o.type == 'MESH' for m in o.data.materials
                         if m and m.name.startswith('grey-timber')), None)
    for dx in (-0.36, 0.36):
        corner = board.matrix_world @ Vector((dx, 0.06, 0))
        # the ray starts under the board, so it finds the road, not the board's own top
        wooden_post(corner.x, corner.y, 2.2, start=board.location.z - 0.02, material=board_timber, turn_degrees=-17)
    # by the doorways further up the street
    place_prop('dustbins.glb', 3.55, 14.2, turn_degrees=90)
    place_prop('wooden-barrel.glb', -3.6, 15.5)
    place_prop('wooden-pail.glb', 3.6, 19.3)
    place_prop('wooden-wash-tub.glb', -3.55, 22.0)
    place_prop('coal-pile.glb', 3.2, 24.5, turn_degrees=30, scale=0.35)
    place_prop('step-ladder.glb', -3.7, 28.0, turn_degrees=90)
    # the colliery gates shut across the top of the street, with the name board beside them
    place_prop('iron-gates-pair.glb', -1.5, 71.5)
    place_prop('iron-gates-pair.glb', 1.5, 71.5)
    place_prop('colliery-name-board.glb', 0.0, 72.4, collection='signs', scale=1.35)   # big enough to read from the street
    place_prop('coal-tub-on-track.glb', -1.0, 76.5, turn_degrees=90)


def set_camera():
    camera = bpy.data.objects.get('main_camera')
    position = CAMERA_POSITION.copy()
    position.z = ground_height(position.x, position.y) + CAMERA_EYE_HEIGHT
    camera.location = position
    camera.rotation_mode = 'XYZ'
    camera.rotation_euler = Euler((math.radians(90 + CAMERA_PITCH_DEGREES), 0, math.radians(CAMERA_YAW_DEGREES)), 'XYZ')
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.angle_y = math.radians(PLATE_FOV_DEGREES)
    camera.data.clip_start = 0.1
    camera.data.clip_end = 1500
    bpy.context.scene.camera = camera
    return camera


build_scene()
camera = set_camera()
if option('--preview'):
    render(option('--preview'), 540, 960, 16)
if option('--plate'):
    render(option('--plate'), 1536, 2730, int(option('--samples', '48')))
if '--export' in arguments:
    export_for_film(camera, 'lockout', PLATE_FOV_DEGREES, 'assemble_lockout.py')
if option('--save'):
    bpy.ops.wm.save_as_mainfile(filepath=option('--save'), relative_remap=True)
print('assemble_lockout: done')
