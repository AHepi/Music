"""What this does: tests model_lint.py (paper-film/blender/model_lint.py) against the faults the project found by eye:
stripes (round 3's find_stripes.py counts), surfaces on one plane (lesson 85), floors just over ground (round 2's yards),
'.001' roots (round 1: eight props), glass alpha read from a picture (log 32), glowing light bases (lesson 89), index
sizes (round 1: the jacket), and fronts. Each check says what it proves or only repeats.
Parts:
  A. always: small made-up models (written here as .glb), the real chimney part of round 3 and round 4 (fixtures, 17 KB
     each) and round 1's node names (fixture)
  B. when the project is on this machine (fixtures/views-and-models/project.json, or FILM_PROJECT): the whole round 3
     and round 4 model files and round 1's props from the project's git history, the pit-village lamps
  C. when Blender is there too (BLENDER, or project.json): the notice corner scene, the Works lane with the factories laid
     on its unlowered ground (round 2's state), and the assembled Works (round 5); about a minute; VIEWS_AND_MODELS_NO_BLENDER=1 skips it
Run: python3 kit/calculators/tests/test_model_lint.py
"""
import json
import os
import struct
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402
from settings import load_settings  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
BLENDER_FOLDER = os.path.join(KIT, 'paper-film', 'blender')
sys.path.insert(0, BLENDER_FOLDER)
import model_lint  # noqa: E402

HERE_FIXTURES = os.path.join(FIXTURES, 'views-and-models')
check = Checker('model_lint: model faults before plates')
settings = load_settings()
TO_GLTF = lambda p: [p[0], p[2], -p[1]]   # Blender (x, y, z) -> glTF (x, z, -y)


def png_rgb(alpha=False):
    """A 2 x 2 PNG (colour type 6 with alpha, 2 without): enough for the alpha-channel test."""
    import zlib
    kind, channels = (6, 4) if alpha else (2, 3)
    raw = b''.join(b'\0' + bytes([200] * channels * 2) for _ in range(2))
    def chunk(name, data):
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, kind, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


def write_glb(path, objects, materials=(), root=None, image=None):
    """objects: [{'name', 'points' (Blender metres), 'triangles', 'uvs' (or None), 'material' index}]; materials: glTF dicts."""
    binary, views, accessors, meshes, nodes = b'', [], [], [], []

    def add(array, kind, component):
        nonlocal binary
        data = np.ascontiguousarray(array)
        while len(binary) % 4:
            binary += b'\0'
        views.append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': data.nbytes})
        binary += data.tobytes()
        accessor = {'bufferView': len(views) - 1, 'componentType': component, 'count': int(data.shape[0]), 'type': kind}
        if kind == 'VEC3':
            accessor['min'], accessor['max'] = data.min(axis=0).tolist(), data.max(axis=0).tolist()
        accessors.append(accessor)
        return len(accessors) - 1
    for obj in objects:
        points = np.array([TO_GLTF(p) for p in obj['points']], dtype=np.float32)
        attributes = {'POSITION': add(points, 'VEC3', 5126)}
        if obj.get('uvs') is not None:
            attributes['TEXCOORD_0'] = add(np.array(obj['uvs'], dtype=np.float32), 'VEC2', 5126)
        primitive = {'attributes': attributes, 'indices': add(np.array(obj['triangles'], dtype=np.uint32).reshape(-1), 'SCALAR', 5125)}
        if obj.get('material') is not None:
            primitive['material'] = obj['material']
        meshes.append({'name': obj['name'], 'primitives': [primitive]})
        nodes.append({'name': obj['name'], 'mesh': len(meshes) - 1})
    gltf = {'asset': {'version': '2.0'}, 'scene': 0, 'nodes': nodes, 'meshes': meshes, 'materials': list(materials), 'accessors': accessors,
            'bufferViews': views, 'buffers': [{'byteLength': 0}]}
    if image is not None:
        while len(binary) % 4:
            binary += b'\0'
        views.append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(image)})
        binary += image
        gltf['images'] = [{'bufferView': len(views) - 1, 'mimeType': 'image/png'}]
        gltf['textures'] = [{'source': 0}]
    if root:
        nodes.append({'name': root, 'children': list(range(len(objects)))})
        gltf['scenes'] = [{'nodes': [len(nodes) - 1]}]
    else:
        gltf['scenes'] = [{'nodes': list(range(len(objects)))}]
    while len(binary) % 4:
        binary += b'\0'
    gltf['buffers'][0]['byteLength'] = len(binary)
    text = json.dumps(gltf).encode()
    while len(text) % 4:
        text += b' '
    with open(path, 'wb') as handle:
        handle.write(struct.pack('<4sII', b'glTF', 2, 28 + len(text) + len(binary)))
        handle.write(struct.pack('<II', len(text), 0x4E4F534A) + text + struct.pack('<II', len(binary), 0x004E4942) + binary)


def quad(name, corners, uvs=((0, 0), (1, 0), (1, 1), (0, 1)), material=None):
    return {'name': name, 'points': corners, 'triangles': [(0, 1, 2), (0, 2, 3)], 'uvs': list(uvs), 'material': material}


def flat(name, x0, y0, x1, y1, z, material=None, facing_up=True):
    corners = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    return quad(name, corners if facing_up else corners[::-1], material=material)


def lint(paths, only, as_set=False, index=None, prop=None):
    models = [model_lint.parts_from_glb(p) for p in paths]
    return model_lint.lint(models, settings, tuple(only), as_set, index, prop)[0]


folder = tempfile.mkdtemp(prefix='model-lint-test-')
try:
    # ---------------------------------------------------------------------------------------------------- A. made-up models
    wall = os.path.join(folder, 'wall.glb')
    good = quad('good-wall', [(0, 0, 0), (4, 0, 0), (4, 0, 3), (0, 0, 3)])
    squashed = quad('striped-wall', [(0, 1, 0), (4, 1, 0), (4, 1, 3), (0, 1, 3)], uvs=((0, 0), (1, 0), (1, 1e-6), (0, 1e-6)))
    mixed = {'name': 'pier', 'points': [(0, 2, 0), (2, 2, 0), (2, 2, 2), (0, 2, 2), (0, 3, 0), (2, 3, 0), (2, 3, 2), (0, 3, 2)],
             'triangles': [(0, 1, 2), (0, 2, 3), (4, 5, 6)], 'uvs': [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0), (1, 0), (1, 0.0), (0, 0)], 'material': None}
    write_glb(wall, [good, squashed, mixed])
    found = {s['part']: s for s in lint([wall], ['stripes'])['stripes']}
    check.true('a part whose faces are all squashed is striped; a well-mapped one is not', 'striped-wall' not in found and 'good-wall' not in found,
               details=f'found {sorted(found)} (a part whose every face is squashed has a squashed median too: it needs the median of the part)')
    check.true('a part with one squashed face among good ones is striped', 'pier' in found and found['pier']['striped_square_metres'] == 2.0,
               details=f'pier {found.get("pier")}', proves='the per-part median rule of find_stripes.py (ratio under 0.02 of the median, over 0.5 square metres)')

    floors = os.path.join(folder, 'yard.glb')
    write_glb(floors, [flat('ground', -10, -10, 10, 10, 0.0), flat('yard-setts', 0, 0, 5, 5, 0.02), flat('step', -8, -8, -6, -6, 0.08)])
    found = lint([floors], ['floors'])['floors_over_ground']
    check.true('setts 2 cm over the ground are found; a step 8 cm up is not', len(found) == 1 and {found[0]['floor'], found[0]['over']} == {'yard-setts', 'ground'},
               details=json.dumps(found), proves='round 2\'s yards (the rule; the real case is in part C)')
    decal = os.path.join(folder, 'decal.glb')
    write_glb(decal, [flat('ground', -10, -10, 10, 10, 0.0), flat('foot-shadow', 0, 0, 1.5, 1.5, 0.006, material=0)],
              materials=[{'name': 'foot-shadow', 'alphaMode': 'BLEND', 'pbrMetallicRoughness': {'baseColorFactor': [0, 0, 0, 0.4]}}])
    check.equal('a see-through shadow patch laid on the ground is not a floor', lint([decal], ['floors'])['floors_over_ground'], [],
                recorded='assemble_works.py foot_shadow (the men\'s soft patches 6-9 mm over the pavement)')

    planes = os.path.join(folder, 'room.glb')
    room_floor, room_ceiling = flat('room', 0, 0, 3, 3, 0.0), flat('room', 0, 0, 3, 3, 2.5, facing_up=False)
    room = {'name': 'room', 'points': room_floor['points'] + room_ceiling['points'], 'triangles': [(0, 1, 2), (0, 2, 3), (4, 5, 6), (4, 6, 7)],
            'uvs': room_floor['uvs'] + room_ceiling['uvs'], 'material': None}          # a room: its floor at 0, its ceiling (facing down) at 2.5
    slab_bottom, slab_top = flat('slab-above', -1, -1, 4, 4, 2.5, facing_up=False), flat('slab-above', -1, -1, 4, 4, 2.8)
    slab = {'name': 'slab-above', 'points': slab_bottom['points'] + slab_top['points'], 'triangles': [(0, 1, 2), (0, 2, 3), (4, 5, 6), (4, 6, 7)],
            'uvs': slab_bottom['uvs'] + slab_top['uvs'], 'material': None}          # the slab over it, its underside at 2.5
    write_glb(planes, [room, slab, flat('box-base', 6, 6, 7, 7, 0.0, facing_up=False), flat('floor-under-box', 5, 5, 8, 8, 0.0, facing_up=False)])
    found = lint([planes], ['same-plane'])['same_plane']
    names = [set(p['objects']) for p in found]
    check.true('a room\'s ceiling on the slab above (same plane, same way) is found', {'room', 'slab-above'} in names,
               recorded='Lessons.md 85 (the kitchen ceiling swapped colour in one frame)', proves='the rule on a made-up room')
    check.true('two bases at the very bottom of their objects are not reported', {'box-base', 'floor-under-box'} not in names)
    moved = os.path.join(folder, 'room-mended.glb')
    lowered = dict(room, points=room_floor['points'] + [(x, y, 2.49) for x, y, _ in room_ceiling['points']])
    write_glb(moved, [lowered, slab])
    check.equal('the same ceiling 1 cm lower (the fix) is not reported', lint([moved], ['same-plane'])['same_plane'], [],
                recorded='models.coplanar_gap_metres (lesson 85: a hair apart)')

    lamp = os.path.join(folder, 'street-lamp.glb')
    glass = {'name': 'street_lamp_01_glass', 'alphaMode': 'BLEND', 'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}}}
    write_glb(lamp, [quad('glass', [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], material=0)], materials=[glass], root='street-lamp', image=png_rgb(False))
    found = lint([lamp], ['glass'])['glass_alpha_from_picture']
    check.true('glass blending from a picture with no alpha channel is found', len(found) == 1 and found[0]['picture_has_alpha'] is False,
               details=json.dumps(found), recorded='log 32 (the gas lamps\' glass took its see-through value from its picture, which has none)',
               proves='the rule; the real lamp files are in part B')
    opaque = os.path.join(folder, 'opaque-lamp.glb')
    write_glb(opaque, [quad('glass', [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], material=0)],
              materials=[{'name': 'street_lamp_01_glass', 'pbrMetallicRoughness': {'baseColorFactor': [0.8, 0.6, 0.3, 1]}}])
    check.equal('glass with its value set (no picture alpha) passes', lint([opaque], ['glass'])['glass_alpha_from_picture'], [])

    glow = os.path.join(folder, 'glows.glb')
    write_glb(glow, [quad('flame', [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], material=0), quad('coals', [(2, 0, 0), (3, 0, 0), (3, 0, 1), (2, 0, 1)], material=1)],
              materials=[{'name': 'white-flame', 'emissiveFactor': [1, 0.5, 0.2], 'pbrMetallicRoughness': {'baseColorFactor': [0.9, 0.9, 0.9, 1]}},
                         {'name': 'brazier coals', 'emissiveFactor': [1, 0.16, 0.015], 'pbrMetallicRoughness': {'baseColorFactor': [0, 0, 0, 1]}}])
    found = [g['material'] for g in lint([glow], ['glow'])['glowing_light_base']]
    check.equal('a glow with a light base is found; a black-based glow is not', found, ['white-flame'],
                recorded='Lessons.md 89; set_dressing.glow_material (a black base)', proves='the rule on made-up materials')

    # sizes: the jacket's round 1 index entry against its measured outline (the outline numbers are model_lint's own
    # measurement of the round 1 file, written as a box here: this checks the description test, not the measuring)
    jacket = os.path.join(folder, 'jacket-and-cap-on-nail.glb')
    box = [(0, 0, 0), (0.516, 0, 0), (0.516, 0, 0.815), (0, 0, 0.815)]
    write_glb(jacket, [quad('front', box), quad('back', [(x, 0.132, z) for x, _, z in box])], root='jacket-and-cap-on-nail')
    entry = {'file': 'jacket-and-cap-on-nail.glb', 'what': 'a dark wool work jacket ... about 0.6 m wide and 0.86 m from hem to nail',
             'size_metres': {'width_x': 0.516, 'depth': 0.132, 'height': 0.815}}
    problems = lint([jacket], ['sizes'], index=[entry])['sizes']['jacket-and-cap-on-nail.glb']['problems']
    check.true('the jacket\'s "about 0.6 m wide" against 0.516 m measured is flagged', any('0.6 m wide' in p for p in problems),
               details='; '.join(problems), recorded='round1-result.json checked.findings[5] (jacket 0.6 m against 0.516 m measured)')

    signs = os.path.join(folder, 'board.glb')
    write_glb(signs, [quad('letters', [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], material=0)], materials=[{'name': 'gate-board-no-1-lettering'}], root='board')
    both = os.path.join(folder, 'hanging-sign.glb')
    write_glb(both, [quad('front', [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], material=0), quad('back', [(0, 0, 1), (1, 0, 1), (1, 0, 0), (0, 0, 0)], material=0)],
              materials=[{'name': 'bank-sign-lettering'}], root='hanging-sign')
    fronts = lint([signs, both], ['front'])['fronts']
    check.true('fronts: a board lettered on its -y face, a sign lettered both ways', fronts['board.glb']['front'] == '-y' and fronts['hanging-sign.glb']['front'] == '+-y',
               details=json.dumps(fronts), recorded='props/index.json ("faces -y (three.js +z)")', proves='the lettered faces\' normals give the front')

    # real fixture: No. 2's chimney a, round 3 against round 4 (cut from the project's own files)
    round3 = os.path.join(HERE_FIXTURES, 'no-2-chimney-a-round3.glb')
    round4 = os.path.join(HERE_FIXTURES, 'no-2-chimney-a-round4.glb')
    found3 = {s['material']: s for s in lint([round3], ['stripes'])['stripes']}
    found4 = lint([round4], ['stripes'])['stripes']
    check.within('round 3 chimney a: share of its brick striped', found3['no-2-brick']['share'], 0.60, 0.85,
                 recorded='round3-result.json checked.findings[0] ("about 60 to 85% of the brick on No. 2\'s two square chimneys")',
                 proves='finds the recorded fault on the real geometry (63%)')
    check.within('round 3 chimney a: share of its chimney brick striped', found3['no-2-chimney-brick']['share'], 0.60, 0.85, recorded='as above (83%)')
    check.equal('round 4 chimney a (rebuilt): striped parts', len(found4), 0, recorded='round4-result.json set.summary (0 after the rebuild)')

    # real fixture: round 1's props' names (eight with 'name.001' roots)
    trees = json.load(open(os.path.join(HERE_FIXTURES, 'round1-props-names.json')))
    failed = []
    for file_name, tree in trees.items():
        model = {'file': file_name, 'parts': [], 'names': [n['name'] for n in tree['nodes']], 'roots': tree['roots'], 'blender_extras': {}}
        if model_lint.check_names(model, settings, one_prop=True)['fails']:
            failed.append(file_name)
    check.equal('round 1 props with a copy-numbered root', len(failed), 8,
                recorded='round1-result.json checked.findings (eight props had a "name.001" root)', proves='the prop-file names rule; ' + ', '.join(sorted(failed)))

    # ---------------------------------------------------------------------------------------------------- B. the project's files
    project_note = json.load(open(os.path.join(HERE_FIXTURES, 'project.json')))
    project = os.environ.get('FILM_PROJECT', project_note['project'])
    in_git = subprocess.run(['git', '-C', project, 'rev-parse', '--is-inside-work-tree'], capture_output=True, text=True).stdout.strip() == 'true' \
        if os.path.isdir(project) else False
    if not in_git:
        check.note(f'part B skipped: the project is not at {project} (set FILM_PROJECT)')
    else:
        works = './film-kit/assets/models/inflation-chapter-2-newcomers/works'
        def from_git(commit, path, out):
            with open(out, 'wb') as handle:
                subprocess.run(['git', '-C', project, 'show', f'{commit}:{path}'], stdout=handle, check=True)
            return out
        counts = {}
        for label, commit in (('round 3', project_note['commits']['round 3 models (find_stripes.py: 15, 27, 33 striped parts)']),
                              ('round 4', project_note['commits']['round 4 models (rebuilt: 0 striped parts)'])):
            paths = [from_git(commit, f'{works}/{name}', os.path.join(folder, f'{label}-{name}'))
                     for name in ('no-1-quiet-factory.glb', 'no-2-flat-out-factory.glb', 'far-town.glb', 'works-set-lane.glb')]
            stripes = lint(paths, ['stripes'])['stripes']
            counts[label] = [sum(1 for s in stripes if s['file'] == os.path.basename(p)) for p in paths]
            for p in paths:
                os.remove(p)
        check.equal('round 3 striped parts (No. 1, No. 2, far town, lane)', counts['round 3'], [15, 27, 33, 4],
                    recorded='round3-result.json checked.findings[0] (15, 27 and 33; the lane 1.3 square metres on four roofs)',
                    proves='the same numbers as the tool that found them, on the files as they were (git 7b3fe7d)')
        check.equal('round 4 striped parts (No. 1, No. 2, far town, lane)', counts['round 4'], [0, 0, 0, 4],
                    recorded='round4-result.json critique.summary (0, except 1.3 square metres on four roofs)')
        props_commit = project_note['commits']["round 1 props (eight with 'name.001' roots)"]
        props_path = './film-kit/assets/models/inflation-chapter-2-newcomers/props'
        listing = subprocess.run(['git', '-C', project, 'ls-tree', '--name-only', props_commit, props_path + '/'], capture_output=True, text=True).stdout.split()
        prop_files = [from_git(props_commit, f'{props_path}/{os.path.basename(n)}', os.path.join(folder, os.path.basename(n))) for n in listing if n.endswith('.glb')]
        index = json.loads(subprocess.run(['git', '-C', project, 'show', f'{props_commit}:{props_path}/index.json'], capture_output=True, text=True).stdout)
        result = lint(prop_files, ['names', 'sizes'], index=index, prop=True)
        failed = sorted(f for f, n in result['names'].items() if n['fails'])
        check.equal('round 1 prop files (git) with a copy-numbered root', len(failed), 8, recorded='round1-result.json checked.findings', proves=', '.join(failed))
        jacket_problems = result['sizes']['jacket-and-cap-on-nail.glb']['problems']
        check.true('round 1 jacket file: "about 0.6 m wide" against its measured 0.516 m', any('0.6 m wide' in p and '0.516' in p for p in jacket_problems),
                   details='; '.join(jacket_problems), recorded='round1-result.json checked.findings[5]', proves='measured from the real file')
        for p in prop_files:
            os.remove(p)
        props = os.path.join(project, 'film-kit', 'assets', 'models', 'pit-village', 'props')
        lamps = [os.path.join(props, n) for n in ('gas-lamp-post.glb', 'gas-lamp-wall-bracket.glb', 'hurricane-lantern.glb')]
        found = lint(lamps, ['glass'])['glass_alpha_from_picture']
        check.equal('pit-village lamp and lantern files: glass reading alpha from a picture with none', sorted(g['material'] for g in found),
                    ['Lantern_01_glass', 'street_lamp_01_glass', 'street_lamp_02_glass'],
                    recorded='story log 32 (the gas lamps and the lantern looked like flat amber cards)', proves='finds the recorded fault in the real files')

    # ---------------------------------------------------------------------------------------------------- C. Blender
    blender = os.environ.get('BLENDER', project_note['blender'])
    kit_folder = os.path.join(project, 'film-kit')
    if os.environ.get('VIEWS_AND_MODELS_NO_BLENDER') or not os.path.exists(blender) or not os.path.isdir(kit_folder):
        check.note('part C skipped: no Blender or no project (set BLENDER and FILM_PROJECT; VIEWS_AND_MODELS_NO_BLENDER=1 skips it)')
    else:
        environment = dict(os.environ, DISPLAY=os.environ.get('BLENDER_DISPLAY', project_note['display']))
        lint_script = os.path.join(BLENDER_FOLDER, 'model_lint.py')

        def blender_lint(arguments, out_name, before=()):
            out = os.path.join(folder, out_name)
            command = [blender, '-b'] + list(arguments) + [a for b in before for a in ('--python', b)] + ['--python', lint_script, '--']
            return command, out

        # C1. the notice corner scene: its script unhooks the lamps' glass (see_through), so the scene passes
        out = os.path.join(folder, 'notice-corner-lint.json')
        run = subprocess.run([blender, '-b', os.path.join(kit_folder, 'assets', 'models', 'pit-village', 'notice-corner.blend'), '--disable-autoexec',
                              '--python', lint_script, '--', '--only', 'glass,glow', '--out', out], capture_output=True, text=True, env=environment, timeout=300)
        scene = json.load(open(out)) if os.path.exists(out) else {}
        check.equal('notice corner scene: glass reading alpha from a picture', scene.get('glass_alpha_from_picture'), [],
                    recorded='assemble_notice_corner.py lines 193, 217, 236 (see_through: "setting the number alone was ignored, log 32")',
                    proves='the lint tells the mended scene from the unmended prop files of part B')
        # C2. round 2's state: the factories laid on the lane's own ground (not lowered under the yards)
        helper = os.path.join(folder, 'lay.py')
        with open(helper, 'w') as handle:
            handle.write('import sys, bpy\nargv = sys.argv[sys.argv.index("--") + 1:]\nbpy.ops.import_scene.gltf(filepath=argv[argv.index("--glb") + 1])\n')
        factories = os.path.join(folder, 'works-set-factories.glb')
        with open(factories, 'wb') as handle:
            subprocess.run(['git', '-C', project, 'show', f'{project_note["commits"]["round 4 models (rebuilt: 0 striped parts)"]}:'
                            './film-kit/assets/models/inflation-chapter-2-newcomers/works/works-set-factories.glb'], stdout=handle, check=True)
        out = os.path.join(folder, 'lane-lint.json')
        run = subprocess.run([blender, '-b', os.path.join(kit_folder, 'assets', 'models', 'inflation-chapter-2-newcomers', 'works', 'works-lane.blend'),
                              '--disable-autoexec', '--python', helper, '--python', lint_script, '--', '--glb', factories, '--only', 'floors', '--out', out],
                             capture_output=True, text=True, env=environment, timeout=300)
        floors = json.load(open(out))['floors_over_ground'] if os.path.exists(out) else []
        pairs = [{f['floor'], f['over']} for f in floors]
        check.true('round 2 state: the lane\'s ground within 5 cm of both yards\' setts', {'ground', 'no-1-yard-setts'} in pairs and {'ground', 'no-2-yard-setts'} in pairs,
                   details='; '.join(f'{f["floor"]} / {f["over"]} {f["square_metres"]} square metres' for f in floors),
                   recorded='round2-result.json checked.findings[9] (dark patches across the yard setts, 2 cm above ground 0; the lane\'s ground showing through)',
                   proves='finds round 2\'s fault in the real scene')
        os.remove(factories)
        # C3. the assembled Works (round 5): assemble_works.py lowers the ground under the yards
        assemble_real = os.path.join(kit_folder, 'paper-film', 'blender', 'inflation-chapter-2-newcomers', 'works', 'assemble_works.py')
        assemble_copy = os.path.join(folder, 'assemble_works.py')
        with open(assemble_copy, 'wb') as handle:
            subprocess.run(['git', '-C', project, 'show', f'{project_note["commits"]["round 5 Works assembly matching the final checks (redrawn plates)"]}:'
                            './film-kit/paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py'], stdout=handle, check=True)
        runner = os.path.join(folder, 'run_as.py')
        with open(runner, 'w') as handle:
            handle.write('import sys\nargv = sys.argv[sys.argv.index("--") + 1:]\nscript, real = argv[argv.index("--script") + 1], argv[argv.index("--as") + 1]\n'
                         'exec(compile(open(script).read(), real, "exec"), {"__name__": "__main__", "__file__": real})\n')
        out = os.path.join(folder, 'works-lint.json')
        run = subprocess.run([blender, '-b', os.path.join(kit_folder, 'assets', 'models', 'inflation-chapter-2-newcomers', 'works', 'works-lane.blend'),
                              '--python', runner, '--python', lint_script, '--', '--script', assemble_copy, '--as', assemble_real, '--view', 'w1',
                              '--only', 'floors,glass', '--out', out], capture_output=True, text=True, env=environment, timeout=600)
        works_lint = json.load(open(out)) if os.path.exists(out) else {}
        yards = [f for f in works_lint.get('floors_over_ground', []) if 'yard-setts' in f['floor'] + f['over']]
        check.true('assembled Works (round 5): no yard over the ground any more', os.path.exists(out) and not yards,
                   details=f'{len(works_lint.get("floors_over_ground", []))} floor pair(s), none with a yard',
                   recorded='round3-result.json works.summary (round 3 lowered the ground under the yards)', proves='the mended scene passes')
        glass = sorted(g['material'] for g in works_lint.get('glass_alpha_from_picture', []))
        check.note(f'finding: in the assembled Works the glass of {", ".join(glass) or "nothing"} still reads alpha from its picture '
                   '(assemble_works.py makes it glow but never unhooks it, as the notice corner does): solid glowing glass, the "flat amber card" '
                   'look of log 32; look at the W1 plate before changing it')
finally:
    for name in os.listdir(folder):
        os.remove(os.path.join(folder, name))
    os.rmdir(folder)
check.finish()
