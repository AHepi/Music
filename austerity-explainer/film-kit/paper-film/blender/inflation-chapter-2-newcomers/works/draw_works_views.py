# What this does: draws small check pictures (540 x 960, EEVEE) of the Works' two factories and the far
# town as they come out of build_factories.py and build_far_town.py, loaded from their .glb files the way
# an assemble script would load them, for a contact sheet (make_works_sheet.py lays them out). It never
# saves anything but the pictures.
#
# It opens a test Works lane (a street built by pit-village/build_street.py with the Works' settings, whose
# head is where the works wall stands) for its ground, sky and dusk light, adds a plain stand-in works wall
# (4 m high, two 3 m gateways 7 m apart, piers, a coping, a 6 m dividing wall back to the mill fronts;
# not a model for the film), puts the factories and the town at the wall, and draws these views (each
# camera level and facing straight up the lane, with the film's lens, 60.4 degrees top to bottom):
#   no-1-front, no-2-front   each factory from the front at 40 m, eye 4 m up, the lane, its houses and the
#                            stand-in wall left out
#   no-1-close, no-2-close   the same from 15 m (are the bricks and slates the right size?)
#   w1, w2                   lane level: eye 1.7 m on the pavement in line with each gate's outer pier, 13 m
#                            from the wall (the plan's W1 and W2)
#   w3                       both gates from an upstairs window across the cross street: on the lane's centre
#                            line, 30 m from the wall, eye 4.6 m up (the plan's W3), with the town behind
#   w3-working               W3 with No. 1 working (all windows lit, doors open) and No. 2 slowed (a third lit)
# and writes views.json beside them (what each picture is) and measured.json (for the lane views: how many
# metres of each chimney show over what stands in front of it, found by casting rays, first over the
# factories and the stand-in wall alone, then with the test lane's houses, lamps and street as well; and
# where each chimney's top and the tank fall in the frame). No. 1 is drawn quiet (windows dark, doors shut),
# No. 2 flat out (all windows lit, doors open), except in w3-working.
#
# Run (a virtual screen is needed: Xvfb :96 -screen 0 1920x1080x24 &):
#   DISPLAY=:96 blender -b LANE.blend --python draw_works_views.py -- OUT_FOLDER [--wall-at METRES]
#       [--models FOLDER] [--samples N] [view names ...]
#   --wall-at: where the works wall's face stands along the lane (the lane's length; default 22)
#   --models: where the .glb files are (default assets/models/inflation-chapter-2-newcomers/works)

import json
import math
import os
import sys

import bpy
from mathutils import Euler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import works_kit as kit  # noqa: E402

given = kit.arguments()
OUT = os.path.abspath(given[0])
WALL_AT = float(kit.option('--wall-at', '22'))
MODELS = os.path.abspath(kit.option('--models', kit.WORKS_FOLDER))
SAMPLES = int(kit.option('--samples', '16'))
VERTICAL_LENS = 60.4
skip_values = {kit.option(name) for name in ('--wall-at', '--models', '--samples')}
ONLY = [word for word in given[1:] if not word.startswith('--') and word not in skip_values]

LANE_COLLECTIONS = ('cottages', 'street', 'lamps')      # left out of the "front" and "close" views

VIEWS = {
    # name: (camera x, camera y from the wall, eye height, with the lane?, what it shows)
    'no-1-front': (-11.5, -32.0, 4.0, False, 'No. 1 from the front at 40 m, eye 4 m'),
    'no-2-front': (11.5, -32.0, 4.0, False, 'No. 2 from the front at 40 m, eye 4 m'),
    'no-1-close': (-6.0, -7.0, 3.0, False, 'No. 1 from 15 m: brick and slate sizes'),
    'no-2-close': (6.0, -7.0, 3.0, False, 'No. 2 from 15 m: brick and slate sizes'),
    'w1': (-5.0, -13.0, 1.7, True, 'W1: lane level at No. 1\'s outer pier, 13 m from the wall'),
    'w2': (5.0, -13.0, 1.7, True, 'W2: lane level at No. 2\'s outer pier, 13 m from the wall'),
    'w3': (0.0, -30.0, 4.6, True, 'W3: upstairs window across the cross street, 30 m back, eye 4.6 m'),
    'w3-working': (0.0, -30.0, 4.6, True, 'W3 with No. 1 working (all lit) and No. 2 slowed (a third lit)'),
}


def import_model(file_name):
    """Load a .glb and put its one root at the works wall."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, file_name))
    imported = [part for part in bpy.data.objects if part not in before]
    roots = [part for part in imported if part.parent is None]
    assert len(roots) == 1, f'{file_name} has {len(roots)} roots: {[root.name for root in roots]}'
    roots[0].location = (0, WALL_AT, 0)
    return roots[0], imported


def stand_in_wall():
    """A plain stand-in works wall with two gateways and the dividing wall (not a model for the film)."""
    stone = kit.surface_material('stand-in-wall-stone', 'large_sandstone_blocks', tint=(0.5, 0.48, 0.45), tile_metres=1.5)
    iron = kit.surface_material('stand-in-gate-iron', 'rusty_metal_02', tint=(0.1, 0.1, 0.1), metallic=0.6)
    builder = kit.MeshBuilder()
    y0, y1 = WALL_AT, WALL_AT + 0.6
    edges = [-40.0, -5.0, -2.0, 2.0, 5.0, 40.0]
    for wall_start, wall_end in zip(edges[::2], edges[1::2]):
        builder.box((wall_start, y0, 0.0), (wall_end, y1, 4.0), stone)
        builder.box((wall_start - 0.05, y0 - 0.08, 4.0), (wall_end + 0.05, y1 + 0.08, 4.2), stone)
    for x in (-5.6, -2.0, 1.4, 5.0):                                   # gate piers
        builder.box((x, y0 - 0.1, 0.0), (x + 0.6, y1 + 0.1, 4.6), stone)
        builder.box((x - 0.06, y0 - 0.16, 4.6), (x + 0.66, y1 + 0.16, 4.8), stone)
    builder.box((-0.3, y1, 0.0), (0.3, WALL_AT + 8.0, 6.0), stone)    # the dividing wall
    builder.finish('stand-in-works-wall', collection_name='stand-in')
    gates = kit.MeshBuilder()
    for k in range(16):                                                 # No. 1's gate, shut: upright bars and rails
        x = -5.0 + 0.1 + k * 2.8 / 15
        gates.box((x - 0.02, y0 + 0.25, 0.05), (x + 0.02, y0 + 0.31, 3.3), iron)
    for z in (0.3, 1.6, 3.0):
        gates.box((-5.0, y0 + 0.24, z), (-2.0, y0 + 0.32, z + 0.08), iron)
    for side, hinge in ((-1, 2.0), (1, 5.0)):                           # No. 2's gate, wide open into the yard
        for k in range(8):
            gates.box((hinge - side * 0.04, y1 + 0.1 + k * 0.19, 0.05), (hinge - side * 0.08, y1 + 0.13 + k * 0.19, 3.3), iron)
    gates.finish('stand-in-gates', collection_name='stand-in')


def camera_for(name):
    x, y, height, _, _ = VIEWS[name]
    data = bpy.data.cameras.new(name)
    data.sensor_fit = 'VERTICAL'
    data.angle_y = math.radians(VERTICAL_LENS)
    data.clip_start, data.clip_end = 0.1, 3000.0
    camera = bpy.data.objects.new(name, data)
    camera.location = (x, WALL_AT + y, height)
    camera.rotation_euler = Euler((math.radians(90), 0, 0))
    bpy.context.scene.collection.objects.link(camera)
    return camera


def measure(camera):
    """For each chimney and the tank: how much shows from this camera over whatever stands in front of it
    (rays from the camera to points up the chimney's middle; a point shows when the first thing a ray
    meets is the chimney itself), and where its top falls in the frame (fractions across and down)."""
    from bpy_extras.object_utils import world_to_camera_view
    scene = bpy.context.scene
    graph = bpy.context.evaluated_depsgraph_get()
    found = {}
    for marker_name, part_name in (('no-1-chimney-top', 'no-1-chimney'), ('no-2-chimney-a-top', 'no-2-chimney-a'),
                                   ('no-2-chimney-b-top', 'no-2-chimney-b'), ('no-2-tank-top', 'no-2-water-tank')):
        marker = bpy.data.objects.get(marker_name)
        if marker is None:
            continue
        top = marker.matrix_world.translation.copy()
        height = top.z - (0.3 if 'chimney' in marker_name else 0.0)
        low = 12.0 if 'tank' in marker_name else 0.0
        shown, z = [], low
        while z <= height - 0.1:
            target = top.copy()
            target.z = z
            direction = (target - camera.location).normalized()
            hit, location, normal, index, thing, matrix = scene.ray_cast(graph, camera.location, direction)
            if hit and thing.name.startswith(part_name):
                shown.append(z)
            z += 0.25
        top.z = height
        place = world_to_camera_view(scene, camera, top)
        where = f'top at {1 - place.y:.2f} down, {place.x:.2f} across'
        if 'tank' in marker_name:
            found['tank'] = (f'shows (top in view), {where}' if shown else f'hidden, {where}')
        elif shown:
            found[part_name] = f'shows {height - min(shown):.1f} m of {height:.0f} (from {min(shown):.1f} m up), {where}'
        else:
            found[part_name] = f'hidden, {where}'
    return found


def show_lane(visible):
    for name in LANE_COLLECTIONS + ('stand-in',):
        found = bpy.data.collections.get(name)
        if found is not None:
            found.hide_render = not visible


def main():
    os.makedirs(OUT, exist_ok=True)
    scene = bpy.context.scene
    stand_in_wall()
    for file_name in ('no-1-quiet-factory.glb', 'no-2-flat-out-factory.glb', 'far-town.glb'):
        if os.path.exists(os.path.join(MODELS, file_name)):
            import_model(file_name)
        else:
            print('not there yet:', file_name)
    # the people's own lights: warm light from No. 2's open doorway and gateway
    for name, location, energy in (('no-2-doorway-spill', (2.9, WALL_AT + 6.2, 2.4), 900.0),
                                   ('no-2-gateway-spill', (3.5, WALL_AT + 1.4, 2.6), 500.0)):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, 'POINT'))
        light.data.energy, light.data.color, light.data.shadow_soft_size = energy, (1.0, 0.62, 0.32), 0.6
        light.location = location
        scene.collection.objects.link(light)
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = SAMPLES
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.6
    scene.render.resolution_x, scene.render.resolution_y = 540, 960
    scene.render.resolution_percentage = 100
    written, measured = {}, {}
    for name in [view_name for view_name in VIEWS if not ONLY or view_name in ONLY]:
        working = name == 'w3-working'
        kit.set_windows('no-1', {1, 2, 3} if working else set())
        kit.set_doorway('no-1', working)
        kit.set_windows('no-2', {1} if working else {1, 2, 3})
        kit.set_doorway('no-2', True)
        for side in ('left', 'right'):
            leaf = bpy.data.objects.get(f'no-1-loading-door-{side}')
            if leaf is not None:
                leaf.rotation_mode = 'XYZ'
                leaf.rotation_euler.z = math.radians(100 if side == 'right' else -100) if working else 0.0
        show_lane(VIEWS[name][3])
        scene.camera = camera_for(name)
        scene.render.filepath = os.path.join(OUT, f'{name}.png')
        bpy.ops.render.render(write_still=True)
        written[name] = VIEWS[name][4]
        if VIEWS[name][3]:
            # first over the factories and the stand-in wall alone, then with the test lane's houses,
            # lamps and street in front too
            for collection_name in LANE_COLLECTIONS:
                if bpy.data.collections.get(collection_name):
                    bpy.data.collections[collection_name].hide_viewport = True
            bpy.context.view_layer.update()
            alone = measure(scene.camera)
            for collection_name in LANE_COLLECTIONS:
                if bpy.data.collections.get(collection_name):
                    bpy.data.collections[collection_name].hide_viewport = False
            bpy.context.view_layer.update()
            with_lane = measure(scene.camera)
            measured[name] = {part: (alone[part] if alone[part] == with_lane[part] else f'{alone[part]}; with the test lane: {with_lane[part]}')
                              for part in alone}
            print(name, measured[name])
    with open(os.path.join(OUT, 'views.json'), 'w') as f:
        json.dump(written, f, indent=1)
    with open(os.path.join(OUT, 'measured.json'), 'w') as f:
        json.dump(measured, f, indent=1)


main()
