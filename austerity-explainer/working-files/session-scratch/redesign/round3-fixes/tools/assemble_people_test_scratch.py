# What this does: puts together the people test (plan 34, part "People"; order of work step 3): the pit
# village street (street.blend, opened read-only: nothing is saved over it) a few metres back from the notice
# corner, at dusk, with the figures built by paper-film/blender/figures/build_figures.py:
#   - four men from behind, 6 to 9 m from the camera, round a brazier burning on the right-hand pavement:
#     one stooped to warm his hands over it, one with his arms folded, one with a hand raised on a lamp post
#     (standing in for a gate bar), one leaning his shoulder on a house wall. The lamp post and its man stand
#     back from the kerb, right of the brazier as the camera sees it: on the kerb line, straight behind the
#     brazier, the film's live smoke drifted over him and he came out a washed-out grey ghost (round 1)
#   - one man facing the camera at about 7 m, standing in the road with his hands in his pockets, against
#     the lamp-lit road behind him
#   - six small walkers 40 to 60 m up the street, backs to us, men and women, some with a bundle or a bag,
#     walking toward the colliery's shut gates, each turned 25 to 35 degrees across the street (straight up
#     it, their legs hid each other and they didn't seem to be walking)
# The kept notice corner is not touched: this script writes only under the name people-test, into
# assets/models/inflation-chapter-2-newcomers/people-test/ (its own export step, not set_dressing's).
# The camera holds still (no slide): it stands on the right-hand pavement at a standing person's eye height,
# level, turned a little left of straight up the street. The plate is drawn from there with the plate's
# wider lens; the film shows its middle with the film's lens.
# Then, when asked:
#   --preview FILE        a quick small picture (540 x 960) with the film's lens
#   --preview-empty FILE  the same without the figures
#   --plate FILE          the plate (1536 x 2730) with the figures
#   --helper-plate FILE   the helper plate: the same without the figures (the men gone)
#   --export              people-test-set.glb (the street and its props), people-test-signs.glb (the colliery's
#                         name board, which keeps its own lettering), people-test-figures.glb (the people),
#                         people-test-camera.json (the plate camera, as the projector) and people-test-shot.json
#   --save FILE           the dressed scene as a .blend (for looking at; no .blend1 backup)
#   --samples N           EEVEE samples (preview 16, plate 48)
# Run (EEVEE needs a virtual screen):
#   Xvfb :96 -screen 0 1920x1080x24 &
#   DISPLAY=:96 blender -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_people_test.py -- --preview out.png
# The plates, the export and the men's outlines for the plate's camera in one run (about 30 minutes), then the state
# picture the page cuts to (the plate, with the helper plate where the men and their light and shadows were):
#   DISPLAY=:96 blender -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_people_test.py \
#       --python paper-film/blender/shot_facts.py -- --plate PLATE.png --helper-plate HELPER.png --export \
#       --check examples/people-test/shot-check.json --facts PLATE_FACTS --fov 64.4
#   (save the two plates as people-test-plate.jpg and people-test-helper-plate.jpg in the people-test folder)
#   python3 -I paper-film/tools/make_state_picture.py PLATE.jpg HELPER.jpg PLATE.jpg HELPER.jpg people-test-state.jpg \
#       people-test-state-mask.png --outlines PLATE_FACTS "man stooped" "man arms folded" ... "walker 6"
# Units are metres; Blender is z-up, the street runs along +y and rises 4 degrees.

import json
import math
import os
import sys

import bpy
from mathutils import Euler, Quaternion, Vector

sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/pit-village')
from set_dressing import KIT_FOLDER, ground_height, place_prop, glow_material, make_glow, brazier_fire, light_reaches, see_through, render   # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def option(name, default=None):
    return arguments[arguments.index(name) + 1] if name in arguments else default

FIGURES_FOLDER = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round3-fixes/figures/out'
OUT_FOLDER = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round3-fixes/people-test-out'
NAME = 'people-test'

# the street (from build_street.py): kerb faces at x = +-2.5, kerb tops to +-2.68, house fronts at +-4.15,
# pavements 13 cm above the road's channel, the ground rising 4 degrees up +y
RISE_PER_METRE = math.tan(math.radians(4.0))
HOUSE_FRONT_X = 4.15
def pavement_height(y):
    return y * RISE_PER_METRE + 0.13
def low(y):   # rays start below the houses' eaves, which overhang the pavement
    return pavement_height(y) + 2.0

# the camera: on the right-hand pavement, a person's eye height, level, turned a little left
CAMERA = Vector((3.2, 15.0))    # on the pavement, a step in from the kerb; the brazier and the man stooped over it
                                 # stand just left of straight ahead
EYE_HEIGHT = 1.81
CAMERA_YAW_DEGREES = float(option('--yaw', '5.0'))
FILM_FOV_DEGREES = 60.4
PLATE_FOV_DEGREES = 64.4

# the brazier and its fire (as at the notice corner: a burnt-down bed of coals, the light just over the rim)
BRAZIER = Vector((2.55, 22.4))   # at the kerb's edge, as at the notice corner
COAL_TOP = 0.78                # a little higher than at the notice corner: from 7 m the camera sees only just over the rim
FIRE_LIGHT_ABOVE_COALS = 0.55
FIRE_WATTS = 90
ROAD_GLOW_WATTS = 600          # the fire's warm patch on the road behind the man who faces us
LAMP_POST = Vector((3.40, 24.3))   # a gas lamp on the pavement, 0.7 m in from the kerb: the bar the fourth man's raised
                                   # hand holds. At the kerb (2.95, 24.2) its man stood in the brazier's smoke
SKY_STRENGTH = 1.96

# the people: (figure file, holder name, (x, y) of its feet, turn in degrees; 0 faces up the street, its back to us)
with open(os.path.join(FIGURES_FOLDER, 'index.json')) as handle:
    FIGURE_FACTS = {entry['file'][:-4]: entry for entry in json.load(handle)}
grip = FIGURE_FACTS['worker-hand-on-bar']['grip_bar_at']
STOOP_AHEAD = FIGURE_FACTS['worker-stooped-to-brazier']['brazier_ahead']
WAITING = [
    # the stooped man turned 40 degrees toward the brazier, so the fire shows beside him, not hidden by his back
    ('worker-stooped-to-brazier', 'figure-stooped', (BRAZIER.x + STOOP_AHEAD * math.sin(math.radians(40)),
                                                     BRAZIER.y - STOOP_AHEAD * math.cos(math.radians(40))), 40),
    ('worker-arms-folded', 'figure-arms-folded', (1.95, 21.5), -34),   # in the road on the brazier's left, facing it
    ('worker-hand-on-bar', 'figure-hand-on-bar', (LAMP_POST.x - grip[0], LAMP_POST.y - grip[1]), 0),
    ('worker-leaning-on-wall', 'figure-leaning', (HOUSE_FRONT_X - FIGURE_FACTS['worker-leaning-on-wall']['wall_at_x'] - 0.01, 23.4), 0),
    ('worker-hands-in-pockets', 'figure-facing', (1.15, 21.7), 180),   # further out in the road, facing us
]
WALKERS = [
    # spread so that, from the camera, none stands behind a near man's head or the lamp post; each turned 25 to 35
    # degrees across the street toward the gates (+ turns to its left), so its stride shows from behind
    ('walker-man-coat', 'figure-walker-1', (-2.33, 57.0), -30),
    ('walker-woman-shawl', 'figure-walker-2', (-1.48, 59.5), -25),
    ('walker-man-bundle', 'figure-walker-3', (-0.54, 62.5), 35),
    ('walker-woman-bundle', 'figure-walker-4', (2.85, 65.0), 30),
    ('walker-man-bag', 'figure-walker-5', (-3.6, 68.0), -35),
    ('walker-woman-hand-bundle', 'figure-walker-6', (3.78, 70.0), 25),
]


def place_figure(file_name, name, x, y, turn_degrees):
    """Imports a figure and stands it on the ground at (x, y) in the 'figures' collection."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(FIGURES_FOLDER, f'{file_name}.glb'))
    imported = [o for o in bpy.data.objects if o not in before]
    holder = bpy.data.objects.new(name, None)
    figures = bpy.data.collections.get('figures') or bpy.data.collections.new('figures')
    if figures.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(figures)
    figures.objects.link(holder)
    for o in imported:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        figures.objects.link(o)
        if o.parent is None:
            o.parent = holder
    holder.location = (x, y, ground_height(x, y, low(y)))
    holder.rotation_euler = (0, 0, math.radians(turn_degrees))
    return holder


def build_scene():
    for name in ('props', 'signs'):
        if name not in bpy.data.collections:
            bpy.context.scene.collection.children.link(bpy.data.collections.new(name))
    # the street's own lamp just behind the camera would flood the near pavement, where the eye enters the frame
    if 'gas_lamp_0_light' in bpy.data.objects:
        bpy.data.objects['gas_lamp_0_light'].data.energy = 70
    # the brazier, its fire, and a sooty liner (the far inside wall otherwise lights up like a salmon bowl, log 31)
    drum = place_prop('brazier-drum.glb', BRAZIER.x, BRAZIER.y, turn_degrees=25, start=low(BRAZIER.y))
    brazier_fire(BRAZIER.x, BRAZIER.y, light_above_coals=FIRE_LIGHT_ABOVE_COALS, coal_top=COAL_TOP, dark_every=1.33, glow=3.0,
                 energy=FIRE_WATTS, shadow_soft=0.35)
    ground = ground_height(BRAZIER.x, BRAZIER.y, low(BRAZIER.y))
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.255, depth=0.13, end_fill_type='NOTHING',
                                        location=(BRAZIER.x, BRAZIER.y, ground + COAL_TOP + 0.065))
    soot = bpy.context.active_object
    soot.name = 'brazier_soot'
    soot_material = glow_material('brazier soot', (1.0, 0.3, 0.06), 0.15)
    nodes, links = soot_material.node_tree.nodes, soot_material.node_tree.links
    height = nodes.new('ShaderNodeSeparateXYZ')
    links.new(nodes.new('ShaderNodeTexCoord').outputs['Generated'], height.inputs['Vector'])
    fade = nodes.new('ShaderNodeMapRange')
    fade.inputs['To Min'].default_value, fade.inputs['To Max'].default_value = 0.6, 0.0
    links.new(height.outputs['Z'], fade.inputs['Value'])
    links.new(fade.outputs['Result'], nodes['Principled BSDF'].inputs['Emission Strength'])
    soot.data.materials.append(soot_material)
    # the fire's light skips the drum itself (its rim came out as bright as the notice at the notice corner)
    light_reaches(bpy.data.objects['brazier_light'], list(drum.children_recursive), only=False)
    # the gas lamp at the kerb, its glass lit amber, its light in the glass
    lamp = place_prop('gas-lamp-post.glb', LAMP_POST.x, LAMP_POST.y, turn_degrees=0, start=low(LAMP_POST.y))
    for o in lamp.children_recursive:
        for m in (o.data.materials if o.type == 'MESH' else []):
            if m and m.name.endswith('_bulb'):
                make_glow(m, (1.0, 0.72, 0.4), 8.0)
            elif m and m.name.endswith('_glass'):
                make_glow(m, (1.0, 0.45, 0.12), 0.3)
                see_through(m, 0.5)
    bpy.ops.object.light_add(type='POINT', location=lamp.location + Vector((0, 0, 3.27)))
    lamp_light = bpy.context.active_object
    lamp_light.name = 'kerb_lamp_light'
    lamp_light.data.color = (1.0, 0.85, 0.65)
    lamp_light.data.energy = 60
    lamp_light.data.shadow_soft_size = 0.12
    # the fire's warm patch on the road behind the man who faces us: he stands against it
    fire = bpy.data.objects['brazier_light'].location
    bpy.ops.object.light_add(type='SPOT', location=fire)
    road = bpy.context.active_object
    road.name = 'fire_glow_on_road'
    road.data.energy, road.data.color, road.data.use_shadow = ROAD_GLOW_WATTS, (1.0, 0.45, 0.15), False
    road.data.spot_size, road.data.spot_blend = math.radians(45), 0.8
    road.rotation_mode = 'QUATERNION'
    road.rotation_quaternion = (Vector((0.0, 27.0, 27.0 * RISE_PER_METRE)) - fire).to_track_quat('-Z', 'Y')
    # a soft cool light on the left-hand house fronts, so the quiet side is dim but not black (as at the notice corner)
    bpy.ops.object.light_add(type='AREA', location=(0.5, 33.0, pavement_height(33.0) + 5.0))
    fill = bpy.context.active_object
    fill.name = 'left_houses_fill'
    fill.data.shape = 'RECTANGLE'
    fill.data.size, fill.data.size_y = 3.0, 18.0
    fill.data.color = (0.62, 0.72, 1.0)
    fill.data.energy = 350
    fill.data.use_shadow = False
    fill.rotation_euler = (0, math.radians(75), 0)
    # the colliery's shut gates across the top of the street, its name board, the doors dimly lit behind
    place_prop('iron-gates-pair.glb', -1.5, 71.5)
    place_prop('iron-gates-pair.glb', 1.5, 71.5)
    place_prop('colliery-name-board.glb', 0.0, 72.4, collection='signs', scale=1.35)
    bpy.ops.object.light_add(type='POINT', location=(0.0, 77.0, 76 * RISE_PER_METRE + 3.0))
    yard = bpy.context.active_object
    yard.name = 'colliery_yard_light'
    yard.data.energy, yard.data.color, yard.data.use_shadow = 40, (0.7, 0.8, 1.0), False
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0.0, 81.7, 76 * RISE_PER_METRE + 2.2), rotation=(math.radians(90), 0, 0))
    doors = bpy.context.active_object
    doors.name = 'heapstead_shut_doors'
    doors.scale = (3.5, 4.4, 1)
    doors.data.materials.append(glow_material('shut doors', (0.55, 0.62, 0.75), 0.05))
    # the gutter a plain stone colour (its stretched block picture read as steps once painted, log 32)
    plain = bpy.data.materials.new('channel plain stone')
    plain.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.09, 0.09, 0.095, 1.0)
    plain.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.8
    channels = bpy.data.objects.get('street_channels')
    for slot in (channels.material_slots if channels else []):
        slot.material = plain
    world = bpy.context.scene.world
    background = world.node_tree.nodes.get('Background') if world and world.node_tree else None
    if background:
        background.inputs['Strength'].default_value = SKY_STRENGTH
    # the people
    for file_name, name, (x, y), turn in WAITING + WALKERS:
        place_figure(file_name, name, x, y, turn)
    bpy.context.view_layer.update()


def camera_place():
    return Vector((CAMERA.x, CAMERA.y, pavement_height(CAMERA.y) + EYE_HEIGHT))


def set_camera(fov_degrees):
    camera = bpy.data.objects.get('main_camera')
    camera.location = camera_place()
    camera.rotation_mode = 'XYZ'
    camera.rotation_euler = Euler((math.radians(90), 0, math.radians(CAMERA_YAW_DEGREES)), 'XYZ')   # level
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.angle_y = math.radians(fov_degrees)
    camera.data.shift_x = camera.data.shift_y = 0.0
    camera.data.clip_start = 0.1
    camera.data.clip_end = 1500
    bpy.context.scene.camera = camera
    bpy.context.view_layer.update()
    return camera


def show_figures(shown):
    for o in bpy.data.collections['figures'].all_objects:
        o.hide_render = not shown
        o.hide_viewport = not shown


def figure_facts(camera):
    """Each figure's place, its distance from the camera and its height on the film's frame, for the page
    and for checking the plan's distances (6 to 9 m, 7 m, 40 to 60 m)."""
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    facts = []
    for file_name, name, (x, y), turn in WAITING + WALKERS:
        holder = bpy.data.objects[name]
        corners = [o.matrix_world @ Vector(c) for o in holder.children_recursive if o.type == 'MESH' for c in o.bound_box]
        top = max(c.z for c in corners)
        feet = holder.matrix_world.translation
        on_frame = [world_to_camera_view(scene, camera, c) for c in corners]
        facts.append({
            'name': name, 'figure': file_name, 'feet': [round(v, 3) for v in feet], 'turn_degrees': turn,
            'faces': 'the camera' if abs(turn) > 90 else 'away (its back to us)',
            'distance_metres': round((feet.to_2d() - camera.matrix_world.translation.to_2d()).length, 2),
            'height_metres': round(top - feet.z, 3),
            'film_frame_box': [round(min(p.x for p in on_frame), 4), round(1 - max(p.y for p in on_frame), 4),
                               round(max(p.x for p in on_frame), 4), round(1 - min(p.y for p in on_frame), 4)],
        })
    return facts


def export_for_film(camera):
    """The dressed set for the film (people-test-set.glb: everything the painting is shone onto except the
    people; people-test-signs.glb: the 'signs' collection, which keeps its own lettering; people-test-figures.glb:
    the people) and the plate camera as the projector, into OUT_FOLDER only. set_dressing.export_for_film is not
    used: it writes into the pit village folder, beside the notice corner's files."""
    os.makedirs(OUT_FOLDER, exist_ok=True)
    def in_collections(o, names):
        return any(c.name in names for c in o.users_collection)
    def export(path, wanted):
        bpy.ops.object.select_all(action='DESELECT')
        for o in bpy.context.scene.objects:
            if o.type in ('MESH', 'EMPTY') and wanted(o):
                o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_cameras=False,
                                  export_lights=False, export_apply=True)
    show_figures(True)
    left_out = {'signs', 'figures', 'cameras', 'preview_lights', 'markers'}
    export(os.path.join(OUT_FOLDER, f'{NAME}-set.glb'), lambda o: not in_collections(o, left_out))
    export(os.path.join(OUT_FOLDER, f'{NAME}-signs.glb'), lambda o: in_collections(o, {'signs'}))
    export(os.path.join(OUT_FOLDER, f'{NAME}-figures.glb'), lambda o: in_collections(o, {'figures'}))
    # the projector: the plate camera in three.js space (as set_dressing.export_for_film writes it)
    q_blender = camera.matrix_world.to_quaternion()
    q_three = Quaternion((1, 0, 0), math.radians(-90)) @ q_blender
    location = camera.matrix_world.translation
    settings = {
        'about': f'The plate camera of the {NAME} scene (assemble_people_test.py), as the projector for projected-set.js. three.js space (y-up): '
                 'position (x, z, -y) of Blender; quaternion = rotation(-90 deg about x) * Blender quaternion.',
        'position': [round(location.x, 5), round(location.z, 5), round(-location.y, 5)],
        'quaternion': [round(q_three.x, 6), round(q_three.y, 6), round(q_three.z, 6), round(q_three.w, 6)],
        'fov': PLATE_FOV_DEGREES, 'aspect': 1080 / 1920, 'near': 0.1, 'far': 1500,
        'blender': {'location': [round(v, 5) for v in location], 'rotation_quaternion_wxyz': [round(v, 6) for v in q_blender]},
    }
    with open(os.path.join(OUT_FOLDER, f'{NAME}-camera.json'), 'w') as handle:
        json.dump(settings, handle, indent=1)


def write_shot_settings(camera):
    shot = {
        'about': 'The people test (assemble_people_test.py, plan 34 part "People"), Blender space (x, y, z), metres. three.js is (x, z, -y). '
                 'The camera holds still at the plate camera\'s place; the film shows the middle of the plate with the film\'s lens.',
        'camera': [round(v, 4) for v in camera_place()], 'yaw_degrees': CAMERA_YAW_DEGREES,
        'film_fov_degrees': FILM_FOV_DEGREES, 'plate_fov_degrees': PLATE_FOV_DEGREES,
        'brazier': [BRAZIER.x, BRAZIER.y, round(ground_height(BRAZIER.x, BRAZIER.y, low(BRAZIER.y)), 4)],
        'coals_z': round(bpy.data.objects['brazier_light'].location.z - FIRE_LIGHT_ABOVE_COALS, 4),
        'fire_light': [round(v, 4) for v in bpy.data.objects['brazier_light'].location],
        'kerb_lamp_light': [round(v, 4) for v in bpy.data.objects['kerb_lamp_light'].location],
        'figures': figure_facts(set_camera(FILM_FOV_DEGREES)),
    }
    set_camera(PLATE_FOV_DEGREES)
    with open(os.path.join(OUT_FOLDER, f'{NAME}-shot.json'), 'w') as handle:
        json.dump(shot, handle, indent=1)
    return shot


build_scene()
if option('--preview'):
    set_camera(FILM_FOV_DEGREES)
    render(option('--preview'), 540, 960, int(option('--samples', '16')))
if option('--preview-empty'):
    set_camera(FILM_FOV_DEGREES)
    show_figures(False)
    render(option('--preview-empty'), 540, 960, int(option('--samples', '16')))
    show_figures(True)
camera = set_camera(PLATE_FOV_DEGREES)
if option('--plate'):
    show_figures(True)
    render(option('--plate'), 1536, 2730, int(option('--samples', '48')))
if option('--helper-plate'):
    show_figures(False)
    render(option('--helper-plate'), 1536, 2730, int(option('--samples', '48')))
    show_figures(True)
if '--export' in arguments:
    export_for_film(camera)
    print('people test figures:', json.dumps(write_shot_settings(camera)['figures'], indent=1))
elif '--facts' in arguments:
    print('people test figures:', json.dumps(figure_facts(set_camera(FILM_FOV_DEGREES)), indent=1))
if option('--save'):
    bpy.context.preferences.filepaths.save_version = 0   # no .blend1 backup
    bpy.ops.wm.save_as_mainfile(filepath=option('--save'), relative_remap=True)
set_camera(FILM_FOV_DEGREES)   # left on the film's view, for a script run after this one (shot_facts.py)
print('assemble_people_test: done')
