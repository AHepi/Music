# What this does: puts together the "notice corner" shot (log 31): the pit village street (street.blend)
# dressed after the composition the user liked in log 30 ("30 Test - composed by Nano Banana - own
# camera"), rebuilt with our own props and our own correct lock-out notice, following
# "07 Composing a shot.md":
#   - the camera stands on the right-hand pavement at about standing height above the props' ground,
#     level, turned a little left so the street's lines meet just beside the notice board
#   - the story props touch as one group at the board: the drum burning in front of the board's
#     lower-left corner, a kitchen chair with its back to the board and its seat to the fire, a lit
#     hurricane lantern on the seat, a pail at the chair's feet, and a gas lamp on its post behind
#   - the work props stay small and far up the street: the handcart and coal sacks on the left, a
#     barrel and dustbins by doorways, the coal tub behind the colliery's shut gates
# The shot is one slide toward the notice without turning (rule 11): the camera starts 1.5 m back
# along the line to the notice and ends on the composed frame. The plate is drawn from the start,
# a little wider than the film's lens, so the whole slide stays inside the painting.
# Then, when asked:
#   --preview FILE   a quick small picture (540 x 960) of the view named by --view (end, the composed
#                    frame, or start), with the film's lens
#   --plate FILE     the plate (1536 x 2730) from the start of the slide, with the plate's wider lens
#   --export         notice-corner-set.glb, notice-corner-signs.glb and notice-corner-camera.json
# Run (EEVEE needs a virtual screen):
#   Xvfb :96 -screen 0 1920x1080x24 &
#   DISPLAY=:96 blender -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_notice_corner.py -- --preview out.png
# Units are metres; Blender is z-up, the street runs along +y and rises 4 degrees.

import json
import math
import os
import sys

import bpy
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from set_dressing import SET_FOLDER, ground_height, place_prop, wooden_post, glow_material, make_glow, brazier_fire, tint, render, export_for_film   # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def option(name, default=None):
    return arguments[arguments.index(name) + 1] if name in arguments else default

# the street (from build_street.py): kerb faces at x = +-2.5, kerb tops to +-2.68, house fronts at
# +-4.15, pavements 13 cm above the road's channel, the ground rising 4 degrees up +y
RISE_PER_METRE = math.tan(math.radians(4.0))
def pavement_height(y):
    return y * RISE_PER_METRE + 0.13

# the story group, round the notice board (rule 3: one touching group)
BOARD = Vector((3.45, 22.75))        # the board's centre: its left edge in line with the camera, so the
                                     # street's lines meet at that edge (rule 1); 0.75 m behind the fire, so the
                                     # fire wouldn't scorch it (critic, log 31)
BOARD_SCALE = 1.11                   # from 4.9 m it fills the same width as the board in the picture the user liked
BOARD_LIFT = 0.46                    # its bottom edge above the pavement, below the drum's rim, so the rim
                                     # overlaps the board's corner clearly (rule 4); the notice's top just
                                     # under where the street's lines meet
DRUM = Vector((2.78, 22.0))          # on the kerb's edge, its right side clearly over the board's corner, clear of the notice (rule 4)
CHAIR = Vector((3.27, 21.75))        # under the notice, back to the board, seat turned to the fire and the
CHAIR_TURN_DEGREES = -40.0           # the model's back is on its +y side: back to the board, seat to the fire           # camera; only a little bigger than life, so its back covers just the
CHAIR_SCALE = 1.05                   # notice's bottom edge from standing height (rule 3)
COAL_TOP = 0.70                      # the coal bed's height above the ground (the drum is 0.86 m)
FIRE_LIGHT_ABOVE_COALS = 0.55        # the fire's light 0.4 m over the rim, where the live flames are: lower, the rim
                                     # throws a wide hard shadow ring and floods the road beyond it (critics, log 31)
FIRE_WATTS = 160                     # was 900: the drum's top, the notice and the board came out pure white; 300 still
                                     # spread warm light over 4.4% of the frame (rule 6 allows 3); in deep orange 220 W
                                     # spread 6.3% and 140 W 4.5%, so it keeps its own, paler orange
LANTERN_WATTS = 5                    # was 60, then 15: the seat right under it came out the brightest thing in the
                                     # frame (its flicker is added live in the film)
NOTICE_GLOW_WATTS = 480              # a warm spot from just over the coals onto the notice's lower part: lit from below (rule 6)
BOARD_DARKER = 0.5                   # the board's timber at half its colour, so the cream notice stands out on it
PAIL = Vector((3.28, 21.15))         # in front of the chair's legs
PAIL_SCALE = 0.85                    # the reference draws it a little smaller next to the chair
LANTERN_SCALE = 1.28                 # the lantern reads on a phone (rule 8); its handle clearly over the board's bottom edge and clear of the notice (rule 4)
LAMP_POST = Vector((3.72, 23.25))     # a gas lamp on its post behind the board, its head above the notice
                                     # as in the picture the user liked, clear of the winding wheels (rule 4)

# the camera (rule 2: where a person would stand; rule 1: turned so the lines meet by the board).
# Height, turn and lens were matched to the picture the user liked by lining up its winding wheels,
# chimney, colliery gate, left roofline and kerbs with ours (log 31, match_camera.py)
EYE_HEIGHT = 1.81                    # above the pavement under the camera: a person standing there
CAMERA_END = Vector((3.10, 17.85))   # the composed frame: 4.4 m from the board. Slid 0.14 m right of the first
                                     # match (2.96), without turning, so the notice and the board clear the phone
                                     # buttons (rule 12) while where the lines meet stays put (the shot checker, log 31)
CAMERA_YAW_DEGREES = float(option('--yaw', '6.87'))  # turned left of straight up the street
SLIDE_METRES = 1.5                   # the start is this far back along the line to the notice
FILM_FOV_DEGREES = 60.4              # top to bottom of the tall frame
PLATE_FOV_DEGREES = 64.4


def build_scene():
    # the street's own lamp behind the camera would flood the near road with light, where the eye enters
    # the frame (rule 8): turned down
    if 'gas_lamp_0_light' in bpy.data.objects:
        bpy.data.objects['gas_lamp_0_light'].data.energy = 70
    # the street's own lamps at y 39 and 64.5 would stand just above the board's top and its left post from
    # here, the far one right where the lines meet (rule 4)
    for name in ('gas_lamp_2_post', 'gas_lamp_2_glass', 'gas_lamp_2_light', 'gas_lamp_4_post', 'gas_lamp_4_glass', 'gas_lamp_4_light'):
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
    for name in ('props', 'signs'):
        if name not in bpy.data.collections:
            collection = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(collection)
    camera_end = CAMERA_END.copy()
    # the notice board on two posts, turned square to the composed frame's camera
    facing = math.degrees(math.atan2(camera_end.x - BOARD.x, -(camera_end.y - BOARD.y)))
    # (every ray starts low: from high up it meets the houses' eaves, which overhang the pavement)
    low = lambda y: pavement_height(y) + 2.0
    board = place_prop('notice-on-board.glb', BOARD.x, BOARD.y, turn_degrees=facing, lift=BOARD_LIFT,
                       collection='signs', scale=BOARD_SCALE, start=low(BOARD.y))
    bpy.context.view_layer.update()
    board_timber = next((m for o in board.children_recursive if o.type == 'MESH' for m in o.data.materials
                         if m and m.name.startswith('grey-timber')), None)
    posts = []
    for dx in (-0.32, 0.32):   # in from the board's ends, so the drum's edge doesn't just meet the left post (rule 4)
        corner = board.matrix_world @ Vector((dx, 0.06, 0))
        posts.append(wooden_post(corner.x, corner.y, BOARD_LIFT + 1.18 * BOARD_SCALE + 0.02, start=board.location.z - 0.02,
                                 material=board_timber, turn_degrees=facing, name='notice-board-post'))   # level with the board's top
    grey = (BOARD_DARKER,) * 3
    tint([o for o in board.children_recursive if o.name.startswith('notice-board')] + posts, grey)   # dark timber, the notice untouched
    # the fire in the drum, its light low over the coals so it lights the notice from below (rule 6)
    place_prop('brazier-drum.glb', DRUM.x, DRUM.y, turn_degrees=25, start=low(DRUM.y))
    # a bed that has burnt down 15 cm below the rim, mostly dark lumps glowing between (the white-stone
    # look of a full bright bed painted badly, critic, log 31); the light stays just over the rim
    brazier_fire(DRUM.x, DRUM.y, light_above_coals=FIRE_LIGHT_ABOVE_COALS, coal_top=COAL_TOP, dark_every=1.33, glow=3.0,
                 energy=FIRE_WATTS, shadow_soft=0.35)
    # the fire's glow on the notice: a warm spot just over the coals, aimed at the notice, its cone narrow
    # enough to stay off the road (the fire's own light is kept low so the road isn't floodlit)
    coals = Vector((DRUM.x, DRUM.y, ground_height(DRUM.x, DRUM.y) + COAL_TOP + 0.25))
    bpy.ops.object.light_add(type='SPOT', location=coals)
    glow = bpy.context.active_object
    glow.name = 'fire_glow_on_notice'
    glow.data.color = (1.0, 0.42, 0.12)   # deep orange: where it is strong the paper still reads warm, not white
    glow.data.energy = NOTICE_GLOW_WATTS
    glow.data.spot_size = math.radians(20)
    glow.data.spot_blend = 0.9   # strongest at the notice's bottom, fading toward its top
    glow.data.use_shadow = False   # the chair's back stands in its way and would shade the notice's bottom
    glow.rotation_mode = 'QUATERNION'
    glow.rotation_quaternion = (notice_centre() - Vector((0, 0, 0.36 * BOARD_SCALE)) - coals).to_track_quat('-Z', 'Y')   # its bottom edge
    # the empty chair, the lantern on its seat (stood on whatever the ray finds first: the seat), the pail
    chair = place_prop('kitchen-chair.glb', CHAIR.x, CHAIR.y, turn_degrees=CHAIR_TURN_DEGREES, scale=CHAIR_SCALE, start=low(CHAIR.y))
    tint(chair.children_recursive, (0.52, 0.47, 0.38))   # grubby cream, not clean white: stays under the notice (rule 5)
    bpy.context.view_layer.update()
    seat = CHAIR + Vector((0.005, -0.18))   # the front of the seat, toward the fire: its top clearly over the board's bottom edge
                                             # and clear of the lamp post behind (rule 4; the shot checker, log 31)
    lantern = place_prop('hurricane-lantern.glb', seat.x, seat.y, turn_degrees=20, scale=LANTERN_SCALE,
                         start=pavement_height(seat.y) + 0.8 * CHAIR_SCALE)   # below the chair's back rail
    # its flame: a small glowing teardrop inside the glass, and its light, which shines through the glass
    flame_at = lantern.location + Vector((0, 0, 0.095 * LANTERN_SCALE))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=1, location=flame_at)
    flame = bpy.context.active_object
    flame.name = 'lantern_flame'
    flame.scale = (0.011 * LANTERN_SCALE, 0.011 * LANTERN_SCALE, 0.026 * LANTERN_SCALE)
    flame.data.materials.append(glow_material('lantern flame', (1.0, 0.62, 0.22), 30.0))
    for o in lantern.children_recursive:
        for m in (o.data.materials if o.type == 'MESH' else []):
            if m and 'glass' in m.name:
                make_glow(m, (1.0, 0.7, 0.4), 2.0)
    bpy.ops.object.light_add(type='POINT', location=flame_at)
    lantern_light = bpy.context.active_object
    lantern_light.name = 'lantern_light'
    lantern_light.data.color = (1.0, 0.62, 0.3)
    lantern_light.data.energy = LANTERN_WATTS
    lantern_light.data.shadow_soft_size = 0.03
    lantern_light.data.use_shadow = False   # the glass and the lantern's own frame would block it
    pail = place_prop('wooden-pail.glb', PAIL.x, PAIL.y, turn_degrees=30, scale=PAIL_SCALE, start=pavement_height(PAIL.y) + 1.2)
    for o in list(pail.children_recursive):   # its thin wire handle would be smeared by the painter and left as a ghost
        if o.name.startswith('wooden_bucket_01_handle'):
            bpy.data.objects.remove(o, do_unlink=True)
    # the gas lamp on its post behind the board, a little dimmer than the street's own lamps so the
    # notice stays the brightest thing (rule 5); its light sits in the lamp's glass
    lamp = place_prop('gas-lamp-post.glb', LAMP_POST.x, LAMP_POST.y, turn_degrees=0, start=low(LAMP_POST.y))
    for o in lamp.children_recursive:
        for m in (o.data.materials if o.type == 'MESH' else []):
            if m and m.name.endswith('_bulb'):
                make_glow(m, (1.0, 0.72, 0.4), 8.0)   # the mantle: small and bright, but not a white blaze
            elif m and m.name.endswith('_glass'):
                make_glow(m, (1.0, 0.6, 0.25), 0.6)   # amber gas light, clearly darker than the notice (it was near white)
    glass_at = lamp.location + Vector((0, 0, 3.27))   # the gas mantle inside its glass
    bpy.ops.object.light_add(type='POINT', location=glass_at)
    lamp_light = bpy.context.active_object
    lamp_light.name = 'corner_lamp_light'
    lamp_light.data.color = (1.0, 0.97, 0.94)   # paler than the fire, so the notice's top reads cooler than its bottom
    lamp_light.data.energy = 12   # its glass glows on its own; the notice is lit from below, cool at the top (rule 6)
    lamp_light.data.shadow_soft_size = 0.12
    # the work props, small and far up the street (rule 8)
    # the handcart loaded with coal sacks, and more sacks against the house wall: a small, dim echo of
    # the story group on the other side of the street, as in the picture the user liked
    place_prop('handcart.glb', -0.15, 28.3, turn_degrees=-75, start=low(28.3))   # where and as big as in the reference; detail on the quiet side (rule 10)
    bpy.context.view_layer.update()
    for spot, turn, scale, start in (((-0.15, 28.25), -75, 0.62, pavement_height(28.3) + 1.6), ((-3.4, 34.0), 95, 0.8, low(34.0))):
        sacks = place_prop('coal-sacks.glb', *spot, turn_degrees=turn, scale=scale, start=start)
        for o in list(sacks.children_recursive):   # the standing sacks read as clay jars once painted (log 29)
            if o.name.startswith('sack-standing'):
                bpy.data.objects.remove(o, do_unlink=True)
    place_prop('wooden-barrel.glb', 3.72, 30.6, start=low(30.6))
    place_prop('dustbins.glb', -3.4, 38.0, turn_degrees=-90, start=low(38.0))   # sacks and bins in view on the quiet side (rule 10)
    # a soft cool light on the left-hand house fronts, so the quiet side is dim but not an empty black mass
    # (rule 10: the picture the user liked has its houses at about 0.6 of its sky's brightness)
    bpy.ops.object.light_add(type='AREA', location=(0.5, 33.0, pavement_height(33.0) + 5.0))
    fill = bpy.context.active_object
    fill.name = 'left_houses_fill'
    fill.data.shape = 'RECTANGLE'
    fill.data.size, fill.data.size_y = 3.0, 18.0
    fill.data.color = (0.62, 0.72, 1.0)
    fill.data.energy = 350   # the houses at about 0.6 of the sky's brightness
    fill.data.use_shadow = False
    fill.rotation_euler = (0, math.radians(75), 0)   # facing the left-hand house fronts (-x), a little downward
    # the colliery gates shut across the top of the street, its name board, and the idle tub inside
    place_prop('iron-gates-pair.glb', -1.5, 71.5)
    place_prop('iron-gates-pair.glb', 1.5, 71.5)
    place_prop('colliery-name-board.glb', 0.0, 72.4, collection='signs', scale=1.35)
    place_prop('coal-tub-on-track.glb', -1.0, 76.5, turn_degrees=90)


def light_left_windows(camera, how_many=2):
    """Lights a couple of dark upstairs windows on the left-hand terrace, dimly: one or two small lights on the
    quiet side (rule 10), between 0.05 and 0.35 across and 0.28 and 0.45 down in the composed frame."""
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    lit = bpy.data.materials.get('window_lit_glow_1')
    if lit is None:
        return []
    dim = lit.copy()
    dim.name = 'window_lit_dim'
    for node in dim.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            node.inputs['Emission Strength'].default_value = 1.2
    chosen = []
    for o in sorted(scene.objects, key=lambda o: o.name):
        if o.type != 'MESH' or not o.material_slots or not any(s.material and s.material.name.startswith('window_dark') for s in o.material_slots):
            continue
        where = world_to_camera_view(scene, camera, o.matrix_world.translation)
        if where.z > 0 and 0.05 <= where.x <= 0.35 and 0.28 <= 1 - where.y <= 0.45 and o.matrix_world.translation.x < 0:
            chosen.append((where.x, o))
    picked = [o for _, o in sorted(chosen, key=lambda c: c[0])][::3][:how_many]   # spread out, not side by side
    for o in picked:
        for slot in o.material_slots:
            if slot.material and slot.material.name.startswith('window_dark'):
                slot.material = dim
    return [o.name for o in picked]


def notice_centre():
    return Vector((BOARD.x, BOARD.y, pavement_height(BOARD.y) + BOARD_LIFT + 0.59 * BOARD_SCALE))


def camera_spot(which):
    """The camera's place at the end of the slide (the composed frame) or at its start: 1.2 m back
    along the level line from the end to the notice, at the same height (rule 11: slide, never turn)."""
    end = Vector((CAMERA_END.x, CAMERA_END.y, pavement_height(CAMERA_END.y) + EYE_HEIGHT))
    if which == 'end':
        return end
    towards = notice_centre() - end
    towards.z = 0
    return end - towards.normalized() * SLIDE_METRES


def set_camera(which, fov_degrees):
    camera = bpy.data.objects.get('main_camera')
    camera.location = camera_spot(which)
    camera.rotation_mode = 'XYZ'
    camera.rotation_euler = Euler((math.radians(90), 0, math.radians(CAMERA_YAW_DEGREES)), 'XYZ')   # level
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.angle_y = math.radians(fov_degrees)
    camera.data.shift_x = camera.data.shift_y = 0.0
    camera.data.clip_start = 0.1
    camera.data.clip_end = 1500
    bpy.context.scene.camera = camera
    return camera


def write_shot_settings():
    """The slide for the film page (notice-corner.js), in Blender space: where it starts and ends,
    the film's lens, and where the story props stand (for the fire, the shadows and the lights)."""
    settings = {
        'about': 'The notice corner shot (assemble_notice_corner.py, log 31), Blender space (x, y, z), metres. '
                 'three.js is (x, z, -y). The camera slides from start to end without turning.',
        'camera_start': [round(v, 4) for v in camera_spot('start')],
        'camera_end': [round(v, 4) for v in camera_spot('end')],
        'yaw_degrees': CAMERA_YAW_DEGREES, 'film_fov_degrees': FILM_FOV_DEGREES, 'plate_fov_degrees': PLATE_FOV_DEGREES,
        'notice_centre': [round(v, 4) for v in notice_centre()],
        'drum': [DRUM.x, DRUM.y, round(pavement_height(DRUM.y), 4)],
        'coals_z': round(bpy.data.objects['brazier_light'].location.z - FIRE_LIGHT_ABOVE_COALS, 4),   # the coal bed's top
        'fire_light': [round(v, 4) for v in bpy.data.objects['brazier_light'].location],   # the fire's light, for the film's own light
        'chair': [CHAIR.x, CHAIR.y], 'pail': [PAIL.x, PAIL.y], 'lamp_post': [LAMP_POST.x, LAMP_POST.y],
        'lantern_light': [round(v, 4) for v in bpy.data.objects['lantern_light'].location],
        'corner_lamp_light': [round(v, 4) for v in bpy.data.objects['corner_lamp_light'].location],
    }
    with open(os.path.join(SET_FOLDER, 'notice-corner-shot.json'), 'w') as handle:
        json.dump(settings, handle, indent=1)


build_scene()
print('lit windows:', light_left_windows(set_camera('end', FILM_FOV_DEGREES)))
if option('--preview'):
    set_camera(option('--view', 'end'), FILM_FOV_DEGREES)
    render(option('--preview'), 540, 960, int(option('--samples', '16')))
if option('--still'):
    set_camera(option('--view', 'end'), FILM_FOV_DEGREES)
    render(option('--still'), 1080, 1920, int(option('--samples', '32')))
camera = set_camera('start', PLATE_FOV_DEGREES)
if option('--plate'):
    render(option('--plate'), 1536, 2730, int(option('--samples', '48')))
if '--export' in arguments:
    export_for_film(camera, 'notice-corner', PLATE_FOV_DEGREES, 'assemble_notice_corner.py')
    write_shot_settings()
if option('--save'):
    bpy.ops.wm.save_as_mainfile(filepath=option('--save'), relative_remap=True)
# leave the camera on the asked-for view, for a script run after this one (shot_facts.py)
if option('--view'):
    set_camera(option('--view'), FILM_FOV_DEGREES)
print('assemble_notice_corner: done')
