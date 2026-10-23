"""What this does: tests how parts built side by side by different owners are combined safely (place_kit/checks/ownership.py, fingerprint.py, combine.py).
Part A (plain Python, always runs): made-up fingerprints. A stage that changes another owner's object is a violation; a new object with no owner is one; an object the actor made itself is not;
a changed shared material, a changed existing node group and a changed frozen setting (camera, lights, render) are violations (except for the ground part named in frozen.set_by, which makes
the cameras, lights, world and render settings that everyone else then finds frozen); a copy number in a new name is only a warning; the
`ownership-diff` command exits 1 on a violation and 0 on a clean change, and 2 when an input is missing.
Part B (needs Blender; otherwise skipped and said): real stage files in a temporary folder run in a tiny scene: two good stages combine with no violations, are idempotent, and give the same
scene in plain and reverse order (--order both); a stage that moves another owner's object is caught and named; a stage that adds a new object every time it runs is called not idempotent;
a stage that only works after another stage is called order dependent; a fingerprint changes when one vertex moves.
Run: python3 kit/calculators/tests/test_place_combine.py
"""
import copy
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, blender_program  # noqa: E402

PLACE_KIT = os.path.join(KIT, 'place-kit')
sys.path.insert(0, PLACE_KIT)
from place_kit.checks import ownership  # noqa: E402

check = Checker('place combine: ownership between builders, and stage files run in two orders')
folder = tempfile.mkdtemp(prefix='place-combine-test-')

OWNERS = {'owners': {'roads': {'objects': ['^Lane'], 'materials': ['Lane material'], 'collections': []},
                     'huts': {'objects': ['^Hut'], 'materials': ['Hut material'], 'collections': []}},
          'frozen': {'render': True, 'cameras': True, 'world': True, 'lights': True}}


def fingerprint(**objects):
    return {'objects': {name: dict({'type': 'MESH', 'owner': None, 'made': False, 'mesh': 'aaa', 'matrix': [0] * 16}, **entry) for name, entry in objects.items()},
            'materials': {'Lane material': 'm1', 'Shared': 's1'}, 'node_groups': {'Group': 'g1'}, 'collections': {},
            'frozen': {'render': {'engine': 'X'}, 'cycles': {}, 'view': {}, 'camera': {'name': 'C', 'lens': 35}, 'world': None, 'lights': ['Sun']}}


start = fingerprint(**{'Lane 1': {'owner': 'roads'}, 'Hut 1': {'owner': 'huts'}})

# ---------------------------------------------------------------- part A
end = copy.deepcopy(start)
end['objects']['Lane 1']['mesh'] = 'bbb'
result = ownership.diff(start, end, OWNERS, actor='huts')
check.true('a stage that changes another owner\'s object is a violation that names both', any('huts changed the object "Lane 1", which roads owns' in v for v in result['violations']), str(result['violations']))
check.equal('the same change by its owner is clean', ownership.diff(start, end, OWNERS, actor='roads')['violations'], [])
end = copy.deepcopy(start)
end['objects']['Hut 2'] = dict(end['objects']['Hut 1'], owner=None)
check.true('a new object with no owner is a violation', any('Hut 2' in v and 'no place_owner' in v for v in ownership.diff(start, end, OWNERS, actor='huts')['violations']))
end['objects']['Hut 2']['owner'] = 'huts'
check.equal('a new object that says whose it is is clean', ownership.diff(start, end, OWNERS, actor='huts')['violations'], [])
end['objects']['Hut 2']['owner'] = 'roads'
check.true('a new object marked as another owner\'s is a violation', bool(ownership.diff(start, end, OWNERS, actor='huts')['violations']))
end = copy.deepcopy(start)
del end['objects']['Lane 1']
check.true('removing another owner\'s object is a violation', any('removed the object "Lane 1"' in v for v in ownership.diff(start, end, OWNERS, actor='huts')['violations']))
end = copy.deepcopy(start)
end['materials']['Shared'] = 's2'
check.true('changing a shared material is a violation that says copy it', any('copy it and change the copy' in v for v in ownership.diff(start, end, OWNERS, actor='huts')['violations']))
end = copy.deepcopy(start)
end['node_groups']['Group'] = 'g2'
check.true('changing an existing node group is a violation', any('node group "Group" changed' in v for v in ownership.diff(start, end, OWNERS, actor='huts')['violations']))
end = copy.deepcopy(start)
end['frozen']['camera']['lens'] = 50
end['frozen']['lights'] = ['Sun', 'Extra']
frozen = ownership.diff(start, end, OWNERS, actor='huts')['violations']
check.true('a changed camera and a changed light set are violations', any('camera' in v for v in frozen) and any('lights' in v for v in frozen), str(frozen))
end = copy.deepcopy(start)
end['objects']['Hut 3.001'] = dict(end['objects']['Hut 1'], owner='huts')
check.true('a copy number in a new name is a warning, not a violation', ownership.diff(start, end, OWNERS, actor='huts')['violations'] == [] and bool(ownership.diff(start, end, OWNERS, actor='huts')['warnings']))
# the ground part is built first and makes the view cameras and the lights; they are frozen for everyone else (plugin 1.4.0 fix round)
OWNERS_SET = dict(OWNERS, frozen=dict(OWNERS['frozen'], set_by='roads'))
end = copy.deepcopy(start)
end['objects']['View A'] = {'type': 'CAMERA', 'owner': None, 'made': False, 'matrix': [0] * 16}
end['objects']['View sun'] = {'type': 'LIGHT', 'owner': None, 'made': False, 'matrix': [0] * 16}
end['frozen']['camera'] = {'name': 'View A', 'lens': 35}
end['frozen']['lights'] = ['Sun', 'View sun']
check.equal('the ground part (frozen.set_by) may make the camera and the lights: no violation', ownership.diff(start, end, OWNERS_SET, actor='roads')['violations'], [])
other = ownership.diff(start, end, OWNERS_SET, actor='huts')['violations']
check.true('any other part that makes a camera or a light is a violation (they are frozen for everyone else)', any('View A' in v for v in other) and any('camera' in v for v in other) and any('lights' in v for v in other), str(other))
check.true('with no frozen.set_by nobody may make them: the ground part is a violation too (so the field is what lets it through)', len(ownership.diff(start, end, OWNERS, actor='roads')['violations']) >= 3)
launcher = os.path.join(PLACE_KIT, 'place_command.py')
files = {}
for name, data in (('start', start), ('clean', start), ('dirty', None), ('owners', OWNERS)):
    if name == 'dirty':
        data = copy.deepcopy(start)
        data['objects']['Lane 1']['mesh'] = 'bbb'
    files[name] = os.path.join(folder, name + '.json')
    json.dump(data, open(files[name], 'w'))
done = subprocess.run([sys.executable, '-I', '-B', launcher, 'ownership-diff', '--start', files['start'], '--end', files['dirty'], '--owners', files['owners'], '--actor', 'huts'], capture_output=True, text=True)
check.true('the ownership-diff command exits 1 on a violation and says so', done.returncode == 1 and 'FAIL huts changed the object "Lane 1"' in done.stdout, done.stdout[-160:])
done = subprocess.run([sys.executable, '-I', '-B', launcher, 'ownership-diff', '--start', files['start'], '--end', files['clean'], '--owners', files['owners'], '--actor', 'huts'], capture_output=True, text=True)
check.equal('the ownership-diff command exits 0 on a clean change', done.returncode, 0)
done = subprocess.run([sys.executable, '-I', '-B', launcher, 'ownership-diff', '--start', files['start']], capture_output=True, text=True)
check.equal('the ownership-diff command exits 2 when an input is missing', done.returncode, 2)

# ---------------------------------------------------------------- part B
blender = blender_program()
if not blender:
    check.note('part B skipped: Blender was not found (set BLENDER, run explainer-film-setup, or put blender on the PATH)')
    check.finish()

STAGE_HEADER = '''import bpy
import bmesh


def remove_mine(prefix):
    for obj in [o for o in bpy.data.objects if o.name.startswith(prefix)]:
        mesh = obj.data
        bpy.data.objects.remove(obj)
        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def make_box(name, size, location, owner):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    for vertex in builder.verts:
        vertex.co.x *= size[0]; vertex.co.y *= size[1]; vertex.co.z *= size[2]
    builder.to_mesh(mesh)
    builder.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj['place_owner'] = owner
    bpy.context.scene.collection.objects.link(obj)
    return obj
'''
STAGES = {
    'stage_roads.py': STAGE_HEADER + '''
OWNER = 'roads'


def apply(options):
    remove_mine('Lane')
    make_box('Lane 1', (8, 2, 0.05), (0, 0, 0.025), 'roads')
''',
    'stage_huts.py': STAGE_HEADER + '''
OWNER = 'huts'


def apply(options):
    remove_mine('Hut')
    for index in range(int(options.get('huts', 2))):
        make_box(f'Hut {index + 1}', (2, 2, 2), (index * 3, 3, 1), 'huts')
''',
    'stage_meddler.py': STAGE_HEADER + '''
OWNER = 'huts'


def apply(options):
    bpy.data.objects['Lane 1'].data.vertices[0].co.z += 0.5
''',
    'stage_forgetful.py': STAGE_HEADER + '''
OWNER = 'huts'


def apply(options):
    count = len([o for o in bpy.data.objects if o.name.startswith('Hut')])
    make_box(f'Hut {count + 1}', (2, 2, 2), (count * 3, 3, 1), 'huts')
''',
    'stage_ground_camera.py': STAGE_HEADER + '''
OWNER = 'roads'


def apply(options):
    remove_mine('Lane')
    make_box('Lane 1', (8, 2, 0.05), (0, 0, 0.025), 'roads')
    for obj in [o for o in bpy.data.objects if o.name in ('View A', 'View sun')]:
        data = obj.data
        bpy.data.objects.remove(obj)
        for collection in (bpy.data.cameras, bpy.data.lights):
            if data in collection.values() and data.users == 0:
                collection.remove(data)
    camera = bpy.data.objects.new('View A', bpy.data.cameras.new('View A'))
    camera.location = (0, -10, 4)
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    sun = bpy.data.objects.new('View sun', bpy.data.lights.new('View sun', 'SUN'))
    bpy.context.scene.collection.objects.link(sun)
''',
    'stage_needy.py': STAGE_HEADER + '''
OWNER = 'huts'


def apply(options):
    remove_mine('Hut')
    lane = bpy.data.objects.get('Lane 1')
    make_box('Hut 1', (2, 2, 2), (0, 3 if lane else 5, 1), 'huts')
''',
}
stage_folder = os.path.join(folder, 'stages')
os.makedirs(stage_folder)
for name, text in STAGES.items():
    open(os.path.join(stage_folder, name), 'w').write(text)
json.dump(OWNERS, open(os.path.join(folder, 'ownership.json'), 'w'))
json.dump(OWNERS_SET, open(os.path.join(folder, 'ownership-set-by.json'), 'w'))
empty_scene = os.path.join(folder, 'empty.blend')
make = subprocess.run([blender, '-b', '--disable-autoexec', '--python-expr', f'import bpy; bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.wm.save_as_mainfile(filepath={empty_scene!r})'], capture_output=True, text=True, timeout=120)
assert os.path.exists(empty_scene), make.stdout[-300:] + make.stderr[-300:]
environment = dict(os.environ, BLENDER=blender)


def combine(stages, *extra, saved=None, owners='ownership.json'):
    command = [sys.executable, '-I', '-B', launcher, 'combine', '--scene', empty_scene, '--owners', os.path.join(folder, owners), '--stages'] + [os.path.join(stage_folder, s) for s in stages] + list(extra)
    done = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=300)
    return done


def last(done):
    lines = [line for line in done.stdout.splitlines() if line.strip()]
    return ' | '.join(lines[-3:])[:220]


done = combine(['stage_roads.py', 'stage_huts.py'])
check.true('two good stages combine with no violation and are idempotent', done.returncode == 0 and 'PASS idempotent' in done.stdout and 'FAIL' not in done.stdout, last(done))
done = combine(['stage_roads.py', 'stage_huts.py'], '--order', 'both')
check.true('plain and reverse order give the same scene for two good stages', done.returncode == 0 and 'PASS order' in done.stdout, last(done))
done = combine(['stage_roads.py', 'stage_huts.py'], '--options', '{"huts": 3}')
check.true('--options reaches the stages (three huts: exit 0)', done.returncode == 0, last(done))
done = combine(['stage_ground_camera.py', 'stage_huts.py'], owners='ownership-set-by.json')
check.true('a ground stage that makes the view camera and the sun combines clean when ownership.json names it in frozen.set_by, and stays idempotent', done.returncode == 0 and 'FAIL' not in done.stdout and 'PASS idempotent' in done.stdout, last(done))
done = combine(['stage_ground_camera.py', 'stage_huts.py'])
check.true('the same stage with no frozen.set_by fails and names the camera (so the field is what let it through)', done.returncode == 1 and 'View A' in done.stdout, last(done))
done = combine(['stage_roads.py', 'stage_meddler.py'])
check.true('a stage that moves another owner\'s object fails and the report names the object and both owners', done.returncode == 1 and 'huts changed the object "Lane 1", which roads owns' in done.stdout, last(done))
done = combine(['stage_roads.py', 'stage_forgetful.py'])
check.true('a stage that adds a new object every time it runs is called not idempotent', done.returncode == 1 and 'FAIL idempotent' in done.stdout, last(done))
done = combine(['stage_roads.py', 'stage_needy.py'], '--order', 'both')
check.true('a stage that only works after another stage is called order dependent', done.returncode == 1 and 'FAIL order' in done.stdout, last(done))
done = combine(['stage_missing.py'])
check.true('a stage file that is not there exits 2 with a sentence', done.returncode == 2 and 'not there' in done.stdout, last(done))
check.true('combine with no stage files is refused with a sentence', subprocess.run([sys.executable, '-I', '-B', launcher, 'combine', '--scene', empty_scene], capture_output=True, text=True, env=environment, timeout=120).returncode == 2)
fingerprint_out = os.path.join(folder, 'fp.json')
done = subprocess.run([sys.executable, '-I', '-B', launcher, 'fingerprint', '--scene', empty_scene, '--out', fingerprint_out], capture_output=True, text=True, env=environment, timeout=120)
check.true('the fingerprint verb writes a fingerprint file', done.returncode == 0 and os.path.exists(fingerprint_out) and 'objects' in json.load(open(fingerprint_out)), last(done))
check.finish()
