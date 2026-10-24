# What this does: a STAND-IN for the Works assembly, only for developing the page code of chapter 2's pages 3 to 5
# (works-effects.js, page-3.js, page-4.js, page-5.js) while the real Works assembly is still being built by another
# helper. It is NOT a set for the film and is kept in scratch. It opens the round 1 test lane (works-lane.blend),
# puts a plain stand-in works wall at its head with two gateways, the two factories and the far town (from
# assets/models/inflation-chapter-2-newcomers/works), a brazier, a lantern and a lunch tin, PETROL and DIESEL drums,
# the gate boards "No. 1" and "No. 2", crates in No. 2's gateway and seven waiting men at No. 1 (no bank:
# pages 3 to 5 don't need it).
# It draws small plates (768 x 1365, EEVEE) for the views the pages use, and writes the files the pages read, in the
# same shapes the real assembly is expected to write:
#   works-set.glb       everything the painting is shone onto (with the men)
#   works-signs.glb     the lettered things that keep their own surfaces (gate boards, drums)
#   works-gates.glb     the gate leaves, the chain and padlock (own surfaces, never in a plate)
#   works-pop-up.glb    the crates that pop up in No. 1's open gateway on "things" (own surfaces, never in a plate)
#   works-camera-w1.json, -w2.json, -w3.json   each view's plate camera (the projector)
#   works-shot.json     where things are (Blender space): views (plate and composed spots), brazier, lantern, gates,
#                       gate lamps, the waiting men's names
#   plates: works-w3-plate.jpg, works-w1-plate.jpg (quiet: men, windows dark), works-w1-men-gone-plate.jpg (men gone,
#   No. 1's cart doors open and its doorway lit, windows dark), works-w1-working-plate.jpg (the same with every window
#   lit), works-w2-plate.jpg (flat out)
# Run: DISPLAY=:96 blender -b works-lane.blend --python assemble_works_stand_in.py -- OUT_FOLDER [--samples 16]
#      [--width 768] [--only w3,w1,...] [--no-export]
import json
import math
import os
import sys

import bpy
from mathutils import Quaternion

KIT = '/home/user/Music/austerity-explainer/film-kit'
sys.path.insert(0, f'{KIT}/paper-film/blender/inflation-chapter-2-newcomers/works')
sys.path.insert(0, f'{KIT}/paper-film/blender/pit-village')
import works_kit as kit          # noqa: E402
import set_dressing as dressing  # noqa: E402

given = kit.arguments()
OUT = os.path.abspath(given[0])
SAMPLES = int(kit.option('--samples', '16'))
WIDTH = int(kit.option('--width', '768'))
ONLY = (kit.option('--only', '') or '').split(',') if kit.option('--only') else []
EXPORT = not kit.flag('--no-export')
WALL_AT = 22.0
MODELS = f'{KIT}/assets/models/inflation-chapter-2-newcomers/works'
PROPS_2 = f'{KIT}/assets/models/inflation-chapter-2-newcomers/props'
FIGURES = f'{KIT}/assets/models/inflation-chapter-2-newcomers/figures'
FILM_FOV, PLATE_FOV = 60.4, 64.4
VIEWS = {   # name: plate spot, composed spot (Blender x, y, z), eye height
    'w3': ((0.0, WALL_AT - 30.0, 4.6), None),
    'w1': ((-4.2, WALL_AT - 13.0, 1.7), (-4.2, WALL_AT - 11.8, 1.7)),
    'w2': ((4.2, WALL_AT - 13.0, 1.7), (4.2, WALL_AT - 11.8, 1.7)),
}
bpy.context.preferences.filepaths.save_version = 0
dressing.set_ground_fallback(0.0, 0.0)


def import_glb(path, location=(0, 0, 0), turn=0.0, collection_name='works', name=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    imported = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in imported if o.parent is None]
    target = kit.collection(collection_name)
    for o in imported:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        target.objects.link(o)
    holder = bpy.data.objects.new(name or os.path.basename(path)[:-4], None)
    target.objects.link(holder)
    for root in roots:
        root.parent = holder
    holder.location = location
    holder.rotation_euler = (0, 0, math.radians(turn))
    return holder, imported


def stand_in_wall():
    stone = kit.surface_material('stand-in-wall-stone', 'large_sandstone_blocks', tint=(0.5, 0.48, 0.45), tile_metres=1.5)
    iron = kit.plain_material('stand-in-iron', (0.03, 0.03, 0.03), roughness=0.6, metallic=0.5)
    builder = kit.MeshBuilder()
    y0, y1 = WALL_AT, WALL_AT + 0.6
    for a, b in ((-40.0, -5.0), (-2.0, 2.0), (5.0, 40.0)):
        builder.box((a, y0, 0.0), (b, y1, 4.0), stone)
        builder.box((a - 0.05, y0 - 0.08, 4.0), (b + 0.05, y1 + 0.08, 4.2), stone)
    for x in (-5.6, -2.0, 1.4, 5.0):
        builder.box((x, y0 - 0.1, 0.0), (x + 0.6, y1 + 0.1, 4.6), stone)
        builder.box((x - 0.06, y0 - 0.16, 4.6), (x + 0.66, y1 + 0.16, 4.8), stone)
    builder.box((-0.3, y1, 0.0), (0.3, WALL_AT + 8.0, 6.0), stone)          # the dividing wall
    for centre in (-3.5, 3.5):                                                 # an iron bar over each gateway for its board
        builder.box((centre - 1.5, y0 + 0.02, 4.32), (centre + 1.5, y0 + 0.1, 4.4), iron)
    builder.finish('stand-in-works-wall', collection_name='works')


def figure(file_name, x, y, turn=0.0, name=None):
    holder, _ = import_glb(f'{FIGURES}/{file_name}', (x, y, dressing.ground_height(x, y)), turn, 'men', name)
    return holder


def main():
    os.makedirs(OUT, exist_ok=True)
    scene = bpy.context.scene
    stand_in_wall()
    for file_name in ('no-1-quiet-factory.glb', 'no-2-flat-out-factory.glb', 'far-town.glb'):
        import_glb(f'{MODELS}/{file_name}', (0, WALL_AT, 0))
    bpy.context.view_layer.update()

    # No. 1's gate: the brazier against its left pier, a lantern and a lunch tin on the PETROL drum by its right pier
    brazier = dressing.place_prop('brazier-drum.glb', -4.6, WALL_AT - 0.55, collection='works')
    fire_light = dressing.brazier_fire(-4.6, WALL_AT - 0.55, energy=600)
    for name, file_name, x, y, turn in (('no-1-petrol', 'steel-drum-petrol.glb', -1.75, WALL_AT - 0.5, 10),
                                        ('no-1-diesel', 'steel-drum-diesel.glb', -1.7, WALL_AT - 1.15, -15),
                                        ('no-2-petrol', 'steel-drum-petrol.glb', 4.75, WALL_AT - 0.5, -10),
                                        ('no-2-diesel', 'steel-drum-diesel.glb', 4.7, WALL_AT - 1.15, 15)):
        dressing.place_prop(file_name, x, y, turn, name=name, collection='signs', folder=PROPS_2)
    lantern = dressing.place_prop('hurricane-lantern.glb', -1.62, WALL_AT - 0.42, collection='works', start=0.95)
    dressing.place_prop('lunch-tin.glb', -1.9, WALL_AT - 0.6, 20, collection='works', folder=PROPS_2, start=0.95)
    for material in bpy.data.materials:
        if material.name.startswith('Lantern_01_glass'):
            dressing.make_glow(material, (1.0, 0.62, 0.3), 6.0)
    lantern_light = bpy.data.objects.new('lantern_light', bpy.data.lights.new('lantern_light', 'POINT'))
    lantern_light.data.energy, lantern_light.data.color, lantern_light.data.shadow_soft_size = 25.0, (1.0, 0.6, 0.3), 0.05
    lantern_light.location = (-1.62, WALL_AT - 0.42, 0.88 + 0.16)
    scene.collection.objects.link(lantern_light)
    # the gate boards over the gateways (their lettering faces the lane)
    dressing.place_prop('gate-board-no-1.glb', -3.5, WALL_AT - 0.06, collection='signs', folder=PROPS_2, lift=3.6, start=0.1)
    dressing.place_prop('gate-board-no-2.glb', 3.5, WALL_AT - 0.06, collection='signs', folder=PROPS_2, lift=3.6, start=0.1)
    # No. 2's gateway: crates stacked inside, a handcart's shafts over them
    for x, y, lift, turn in ((2.95, WALL_AT + 1.3, 0.0, 4), (3.85, WALL_AT + 1.45, 0.0, -6), (3.35, WALL_AT + 1.35, 0.5, 2)):
        dressing.place_prop('crate-this-way-up.glb', x, y, turn, collection='works', folder=PROPS_2, lift=lift, start=0.1)
    dressing.place_prop('handcart.glb', 3.6, WALL_AT + 2.6, 90, collection='works')
    # the people's own lights: No. 2's doorway and gateway, a gate lamp on each gate's outer pier
    lamps = {}
    for name, location, energy, colour in (('no-2-doorway-spill', (2.9, WALL_AT + 6.2, 2.4), 900.0, (1.0, 0.62, 0.32)),
                                           ('no-2-gateway-spill', (3.5, WALL_AT + 1.4, 2.6), 500.0, (1.0, 0.62, 0.32)),
                                           ('no-1-gate-lamp', (-5.3, WALL_AT - 0.35, 3.6), 120.0, (1.0, 0.72, 0.45)),
                                           ('no-2-gate-lamp', (5.3, WALL_AT - 0.35, 3.6), 120.0, (1.0, 0.72, 0.45))):
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, 'POINT'))
        light.data.energy, light.data.color, light.data.shadow_soft_size = energy, colour, 0.4
        light.location = location
        scene.collection.objects.link(light)
        lamps[name] = list(location)

    # seven men waiting at No. 1, backs to us, in single file along the pavement, the front one at the gate
    men = [figure('worker-hand-on-bar.glb', -4.0, WALL_AT - 0.55, 0, 'man-1'),
           figure('worker-stooped-to-brazier.glb', -4.75, WALL_AT - 1.25, -15, 'man-2'),
           figure('worker-arms-folded.glb', -3.75, WALL_AT - 1.75, 8, 'man-3'),
           figure('worker-hands-in-pockets.glb', -3.6, WALL_AT - 2.55, -5, 'man-4'),
           figure('worker-arms-folded.glb', -3.7, WALL_AT - 3.35, 12, 'man-5'),
           figure('worker-hands-in-pockets.glb', -3.55, WALL_AT - 4.15, 3, 'man-6'),
           figure('worker-leaning-on-wall.glb', -4.95, WALL_AT - 4.9, -90, 'man-7')]

    # own surfaces, never in a plate: the gate leaves (No. 1 shut and chained; No. 2 the same model) and the pop-up crates
    gates = {}
    for prefix, centre in (('no-1', -3.5), ('no-2', 3.5)):
        holder, _ = import_glb(f'{KIT}/assets/models/pit-village/props/iron-gates-pair.glb', (centre, WALL_AT + 0.3, 0.0), 0, 'gates', f'{prefix}-gate')
        gates[prefix] = {'centre': [centre, WALL_AT + 0.3, 0.0], 'width': 2.95}
    import_glb(f'{PROPS_2}/chain-and-padlock.glb', (-3.5, WALL_AT + 0.24, 1.15), 0, 'gates', 'no-1-chain')
    for k, (x, y, lift, turn) in enumerate(((-3.95, WALL_AT + 1.4, 0.0, -5), (-3.1, WALL_AT + 1.5, 0.0, 7), (-3.55, WALL_AT + 1.45, 0.5, 2))):
        import_glb(f'{PROPS_2}/crate-this-way-up.glb', (x, y, dressing.ground_height(x, y) + lift), turn, 'pop-up', f'no-1-crate-{k + 1}')

    # cameras: level, facing straight up the lane (+y), the plate's wider lens
    cameras = {}
    for name, (plate, composed) in VIEWS.items():
        data = bpy.data.cameras.new(name)
        data.sensor_fit = 'VERTICAL'
        data.angle_y = math.radians(PLATE_FOV)
        data.clip_start, data.clip_end = 0.1, 3000.0
        camera = bpy.data.objects.new(f'camera-{name}', data)
        camera.location = plate
        camera.rotation_mode = 'XYZ'
        camera.rotation_euler = (math.radians(90), 0, 0)
        kit.collection('cameras').objects.link(camera)
        cameras[name] = camera
    bpy.context.view_layer.update()

    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.6
    kit.collection('gates').hide_render = True
    kit.collection('pop-up').hide_render = True
    height = round(WIDTH * 16 / 9)
    plates = {   # picture name: (view, men shown, No. 1's windows lit, No. 1's doors open and doorway lit)
        'works-w3-plate': ('w3', True, False, False),
        'works-w1-plate': ('w1', True, False, False),
        'works-w1-men-gone-plate': ('w1', False, False, True),
        'works-w1-working-plate': ('w1', False, True, True),
        'works-w2-plate': ('w2', True, False, False),
    }
    for picture, (view, men_shown, lit, doors) in plates.items():
        if ONLY and picture not in ONLY and view not in ONLY:
            continue
        kit.collection('men').hide_render = not men_shown
        kit.set_windows('no-1', {1, 2, 3} if lit else set())
        kit.set_doorway('no-1', doors)
        for side in ('left', 'right'):
            leaf = bpy.data.objects.get(f'no-1-loading-door-{side}')
            if leaf is not None:
                leaf.rotation_mode = 'XYZ'
                leaf.rotation_euler.z = math.radians(100 if side == 'right' else -100) if doors else 0.0
        scene.camera = cameras[view]
        dressing.render(os.path.join(OUT, f'{picture}.png'), WIDTH, height, SAMPLES)
    kit.collection('men').hide_render = False
    kit.set_windows('no-1', set())
    kit.set_doorway('no-1', False)
    for side in ('left', 'right'):
        leaf = bpy.data.objects.get(f'no-1-loading-door-{side}')
        if leaf is not None:
            leaf.rotation_euler.z = 0.0
    if not EXPORT:
        return

    def export(path, collections, leave_out=()):
        bpy.ops.object.select_all(action='DESELECT')
        for o in scene.objects:
            names = {c.name for c in o.users_collection}
            if o.type not in ('MESH', 'EMPTY'):
                continue
            if (collections is None and not names & set(leave_out)) or (collections is not None and names & set(collections)):
                o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_yup=True, export_cameras=False,
                                  export_lights=False, export_apply=True)
    export(os.path.join(OUT, 'works-set.glb'), None, ('signs', 'gates', 'pop-up', 'cameras'))
    export(os.path.join(OUT, 'works-signs.glb'), ('signs',))
    export(os.path.join(OUT, 'works-gates.glb'), ('gates',))
    export(os.path.join(OUT, 'works-pop-up.glb'), ('pop-up',))
    turn = Quaternion((1, 0, 0), math.radians(-90))
    for name, camera in cameras.items():
        q_blender = camera.matrix_world.to_quaternion()
        q_three = turn @ q_blender
        location = camera.matrix_world.translation
        with open(os.path.join(OUT, f'works-camera-{name}.json'), 'w') as handle:
            json.dump({'about': f'STAND-IN: the plate camera of view {name.upper()} (assemble_works_stand_in.py), the projector for projected-set.js; three.js space.',
                       'position': [round(location.x, 5), round(location.z, 5), round(-location.y, 5)],
                       'quaternion': [round(q_three.x, 6), round(q_three.y, 6), round(q_three.z, 6), round(q_three.w, 6)],
                       'fov': PLATE_FOV, 'aspect': 1080 / 1920, 'near': 0.1, 'far': 1500}, handle, indent=1)
    coal_top = dressing.ground_height(-4.6, WALL_AT - 0.55) + 0.80
    facts = {
        'about': 'STAND-IN Works shot facts (assemble_works_stand_in.py), Blender space (x, y, z), metres; three.js is (x, z, -y).',
        'film_fov_degrees': FILM_FOV, 'plate_fov_degrees': PLATE_FOV,
        'views': {name: {'plate': list(plate), 'composed': list(composed) if composed else None} for name, (plate, composed) in VIEWS.items()},
        'brazier': list(brazier.location), 'coals_z': coal_top, 'fire_light': list(fire_light.location),
        'lantern_light': list(lantern_light.location), 'gate_lamps': {'no-1': lamps['no-1-gate-lamp'], 'no-2': lamps['no-2-gate-lamp']},
        'gates': gates, 'men': [m.name for m in men],
        'queue_front': [-4.0, WALL_AT - 0.55, 0.0], 'no-2-crates': [3.35, WALL_AT + 1.35, 0.5], 'no-1-gateway': [-3.5, WALL_AT + 1.4, 0.0],
    }
    with open(os.path.join(OUT, 'works-shot.json'), 'w') as handle:
        json.dump(facts, handle, indent=1)
    print('stand-in written to', OUT)


main()
