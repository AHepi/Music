"""What this does: rewrites the canned helper answers of the build-a-place workflow test around a small canal lock (a neutral place the project really built) instead of the one request that was used while the plugin was written."""
import glob
import json
import os
import re

FIX = '/home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/place-workflow'

TEXT = [
    ('roads_and_ground', 'ground_and_water'),
    ('forest_edge', 'bank_planting'),
    ('cottages', 'walls_and_steps'),
    ('AUDITSTABLE', 'AUDITGATE'),
    ('"stable"', '"lock_gate"'),
    ('stage_stable.py', 'stage_lock_gate.py'),
    ('stable bench plank', 'lock_gate board'),
    ('a bench plank floats 3 cm above its posts', 'a gate board floats 3 cm above its rails'),
    ('the bench plank still floats 1 cm', 'the gate board still floats 1 cm'),
    ('lower the plank onto the posts', 'lower the board onto the rails'),
    ('a bench plank floats', 'a gate board floats'),
    ('stable bench', 'lock_gate boards'),
    ('stable door', 'lock_gate leaf'),
    ('a small gap under the lock_gate leaf', 'a small gap under the gate leaf'),
    ('a small gap under the stable door after the fix', 'a small gap under the gate leaf after the fix'),
    ('the thatch ridge is too regular', 'the coping stones are too regular'),
    ('"should_fix_now": "the thatch ridge"', '"should_fix_now": "the coping stones"'),
    ('the ridge of the thatch may be too regular', 'the joints between the coping stones may be too regular'),
    ('lane_close', 'towpath_close'),
    ('lane close view', 'towpath close view'),
    ('the lane edge looks slightly too clean', 'the towpath edge looks slightly too clean'),
    ('forest floor weeds', 'verge weeds'),
    ('a lit window in one cottage', 'a lit lantern on the gate post'),
    ('on every lane', 'on every towpath'),
    ('a height profile across the lane', 'a height profile across the towpath'),
    ('inside 1.2 m of each lane centre line the ground is as it is', 'inside 1.2 m of each road centre line the ground is as it is'),
    ('wetness dial raised for the lane roles', 'wetness dial raised for the towpath roles'),
    ('the lighter plan masks on a village-size scene', 'the lighter plan masks on a scene much bigger than the small test places'),
    ('"element": "wheel ruts"', '"element": "towpath ruts"'),
    ('every doorway of the {owner} part has a floor behind it (measured: 7 doorways, gap 0.03 m, PLANT-7716)', 'every post of the {owner} part stands on the ground (measured: 6 posts, gap 0.01 m, PLANT-7716)'),
    ('construction.json opening_floor_gap_m PLANT-3390', 'construction.json ground_gap_m PLANT-3390'),
    ('"the shared lamp is slightly off centre"', '"the shared lamp is slightly off centre"'),
]


def read(name):
    return open(os.path.join(FIX, name), encoding='utf-8').read()


def write(name, text):
    open(os.path.join(FIX, name), 'w', encoding='utf-8').write(text)


for path in sorted(glob.glob(os.path.join(FIX, '*.json'))):
    name = os.path.basename(path)
    text = read(name)
    for old, new in TEXT:
        text = text.replace(old, new)
    # any claim that began "[cottages] the cottages part ..." has already become walls_and_steps
    write(name, text)

# ------------------------------------------------------------------------------------------------------- the plan
FEATURES = [
    ('brick courses with moss', ['brick', 'moss']),
    ('stone coping with chips', ['coping', 'chip']),
    ('stone steps with worn edges', ['step', 'tread']),
    ('rutted gravel towpath with puddles', ['rut', 'puddle', 'towpath']),
    ('weeds along the towpath edge', ['weed', 'tuft']),
    ('silvered gate boards', ['silver', 'board', 'plank']),
    ('balance beams with iron straps', ['beam', 'strap']),
    ('rusty bollards', ['bollard', 'rust']),
    ('a barrel with iron bands', ['barrel', 'band']),
    ('a coil of rope', ['rope', 'coil']),
    ('a wooden crate', ['crate']),
    ('a dark waterline stain on the wall', ['waterline', 'stain']),
    ('dark water in the lock chamber', ['water', 'chamber']),
    ('cracked bricks', ['crack']),
    ('a gate leaf that leans', ['leaning', 'crooked', 'leans']),
    ('leaves and litter on the towpath', ['leaves', 'litter']),
]
PARTS = [
    ('ground and water', 'ground_and_water', 'The graded ground, the gravel towpath with ruts, the verges, puddle hollows, the water of the chamber and the view cameras.',
     ['graded ground mesh', 'towpath shape', 'verges and puddle hollows', 'water and view cameras'], 150000),
    ('walls and steps', 'walls_and_steps', 'The brick lock wall with stone coping, a trench in the towpath and a flight of stone steps down to the water.',
     ['wall panels and coping', 'trench and steps', 'roles and the part pass'], 250000),
    ('lock gate', 'lock_gate', 'A two-leaf timber gate: heel posts, mitre posts, rails tenoned into both posts, boards, iron straps and balance beams.',
     ['posts and rails', 'boards and straps', 'roles and the part pass'], 120000),
    ('props', 'props', 'Two bollards, a crate, a barrel with two iron bands and a coil of rope.',
     ['bollards and crate', 'barrel and rope', 'roles and the part pass'], 60000),
    ('bank planting', 'bank_planting', 'Grass verges, reeds, nettles and bramble on the bank, kept off the towpath.',
     ['verge tufts', 'reeds and bramble', 'roles and the part pass'], 100000),
]


def rewrite_plan(name):
    data = json.loads(read(name))
    data['place'] = 'canal lock'
    data['place_type'] = 'harbour'
    data['ground_owner'] = 'ground_and_water'
    data['parts'][:5] = [
        {'name': n, 'owner': o, 'collection': 'Place: ' + o, 'region': [0, 0, 20, 20], 'brief': b, 'steps_in_order': s, 'triangle_budget': t}
        for n, o, b, s, t in PARTS]
    data['readable_features'] = [{'name': n, 'keywords': k} for n, k in FEATURES]
    data['renderer_hint'] = 'a lit lantern on the gate post, and water in view, mean Cycles'
    data['open_questions'] = ['the lock wall thickness and the balance beam length are guesses until a source confirms them']
    data['contracts'] = ['inside 1.2 m of each road centre line the ground is as it is']
    data['views'] = [
        {'name': 'wide', 'camera': 'View wide', 'size': [1200, 800]},
        {'name': 'towpath_close', 'camera': 'View towpath_close', 'size': [1200, 800]},
        {'name': 'detail_close', 'camera': 'View detail_close', 'size': [1200, 800]},
    ]
    write(name, json.dumps(data, indent=1) + '\n')


rewrite_plan('plan.json')
rewrite_plan('plan-many.json')

# ----------------------------------------------------------------------------------------------------- the readers
write('blind-1.json', json.dumps({'seen': [
    'green moss on a brick wall', 'chipped stone slabs along the top of the wall', 'a short flight of steps', 'a gravel path with two ruts and a puddle',
    'weeds at the edge of the path', 'grey weathered boards on a big gate', 'long beams with iron straps', 'rusty short posts', 'a barrel with iron bands',
    'a coil of rope', 'a wooden crate', 'a dark stain along the bottom of the wall', 'dark water in the chamber', 'a stack of logs'], 'notes': ''}, indent=1) + '\n')
write('blind-2.json', json.dumps({'seen': ['two ruts with puddles', 'a brick wall', 'a barrel', 'some weeds', 'a tall wooden frame'], 'notes': ''}, indent=1) + '\n')
print('done')
