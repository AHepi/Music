"""What this does: tests the plugin 1.5.0 fix round of the place kit, the faults a real test place showed (a model asked for a settlement among trees with unkept dirt tracks):
  1. PLAIN SURFACES: every surface now comes from a photographed scan when one can be had: the person's own library first (settings "own_surfaces"), then the free Poly Haven
     scan named in data/surfaces.json (downloaded once per machine into a cache outside every repository), else the made-in-code recipe, and the kit says which and why. Each
     scan's normal map is checked against its own height map and turned round when it points the other way; a map that leans as a whole is levelled; the material has the
     scan's colour, normal, roughness and height (real displacement on the ground roles), at the scan's real size, with the wear layers on top. Stones and pebbles are seated
     in unpaved ground, sized by the facts table; puddles lie in hollows and ruts when the place is damp or wet.
  2. WEEDS WITHOUT EDGE LOGIC: plants, litter and stones grow by SITE (wall feet, verges, fence lines, joints, the grass between ruts, damp corners, a thin background), each
     site counted to its own dial, the species' "seam" liking read, and the audit measures the share of each site again.
  3. VISIBLE FAULTS: fern fronds stood on their edge and drew as dark V shapes (they now lie with their faces to the sky, and thin leaves let light through); a clear wet
     film and mirror puddles on a thatched roof drew white sparkles (no film on surfaces that soak water up; puddles only on level ground); two ground surfaces met at a
     ruled line and a strip of the lower one read as a flat brown rectangle (they now blend across their seam, and weeds gather along it).
  4. THE GATE CONTRADICTED ITSELF: the kit's own scatter failed the audit's per-builder budget as "unowned" (it has its own budget now, and the growth step scales its
     counts to stay inside it); the judge read the place's own facts only when given --facts (the audit now carries them).
Part A runs without Blender (the choosing, the sites, the pieces, the data, the judge). Part B needs Blender: a yard is finished with a small library of the person's own
surfaces made here (one of its normal maps deliberately DirectX, one surface with no normal map at all), damp, with a road whose middle grows grass; then again with a tiny
scatter budget. It never downloads (the tests run with PLACE_KIT_OFFLINE=1; PLACE_KIT_NETWORK_TESTS=1 adds one real download of a small scan into a scratch cache).
Run: python3 kit/calculators/tests/test_place_real_surfaces.py   (BLENDER=/path/to/blender for part B, about 3 minutes on a slow machine)
"""
import copy
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, FIXTURES, blender_program  # noqa: E402

PLACE_KIT = os.path.join(KIT, 'place-kit')
sys.path.insert(0, PLACE_KIT)
import numpy as np  # noqa: E402

from place_kit import settings_file  # noqa: E402
from place_kit.surfaces import scans, normals, heights  # noqa: E402
from place_kit.growth import sites, pieces  # noqa: E402

check = Checker('place kit 1.5.0: real photographed surfaces, weeds by site, the visible faults and a gate that agrees with itself')
folder = tempfile.mkdtemp(prefix='place-real-surfaces-test-')
NETWORK = os.environ.get('PLACE_KIT_NETWORK_TESTS') == '1'
os.environ['PLACE_KIT_OFFLINE'] = '1'                  # parts A and B never download, also when the one network check below is asked for
os.environ['PLACE_KIT_SCAN_CACHE'] = os.path.join(folder, 'empty-cache')      # ...and never read this machine's own cache of scans


def network_check():
    """One real download (only when asked: PLACE_KIT_NETWORK_TESTS=1), into a scratch cache that is removed with the test's folder."""
    if not NETWORK:
        check.note('the real download was skipped (set PLACE_KIT_NETWORK_TESTS=1 to try one small scan from Poly Haven)')
        return
    os.environ['PLACE_KIT_SCAN_CACHE'] = os.path.join(folder, 'network-cache')
    os.environ.pop('PLACE_KIT_OFFLINE', None)
    try:
        scan = scans.polyhaven_scan('brown_mud_dry', 1.3, quick=True)
        check.true('NETWORK: a real Poly Haven scan downloads once into the cache, with its licence, its size and a checksum for every picture',
                   all(os.path.exists(p) for p in scan['files'].values()) and scan['info']['licence'].startswith('CC0') and all(v.get('sha256') for v in scan['info']['files'].values()))
        again = scans.polyhaven_scan('brown_mud_dry', 1.3, quick=True)
        check.true('...and a second call reads the cache (no second download)', again['files'] == scan['files'])
    except scans.ScanUnavailable as problem:
        check.true('NETWORK: a real Poly Haven scan downloads', False, details=str(problem))
    finally:
        os.environ['PLACE_KIT_OFFLINE'] = '1'

# ============================================================================================ part A: no Blender
# ---- 1. choosing a scan
old_cache = os.environ.get('PLACE_KIT_SCAN_CACHE')
os.environ['PLACE_KIT_SCAN_CACHE'] = os.path.join(folder, 'my-cache')
check.equal('the scan cache is the folder PLACE_KIT_SCAN_CACHE names (never inside a repository)', scans.cache_folder(), os.path.join(folder, 'my-cache'))
os.environ.pop('PLACE_KIT_SCAN_CACHE')
check.true('...and without it, a folder under the user\'s own cache (~/.cache/explainer-film/surface-scans)', scans.cache_folder().endswith(os.path.join('explainer-film', 'surface-scans'))
           and '.cache' in scans.cache_folder())
if old_cache is not None:
    os.environ['PLACE_KIT_SCAN_CACHE'] = old_cache
check.true('downloads are off when PLACE_KIT_OFFLINE is 1 or the settings say "surface_scans": "off"', scans.offline({}) and scans.offline({'surface_scans': 'off'}))
listing = {'Diffuse': {'2k': {'jpg': {'url': 'https://dl/x_diff_2k.jpg'}}, '1k': {'jpg': {'url': 'https://dl/x_diff_1k.jpg'}}},
           'nor_gl': {'1k': {'png': {'url': 'https://dl/x_nor_gl_1k.png'}, 'jpg': {'url': 'https://dl/x_nor_gl_1k.jpg'}}}, 'nor_dx': {'1k': {'png': {'url': 'https://dl/x_nor_dx_1k.png'}}},
           'Displacement': {'1k': {'jpg': {'url': 'https://dl/x_disp_1k.jpg'}}}}
check.equal('the Poly Haven file list gives the colour at 2k, the OpenGL normal (never the DirectX one) as a lossless PNG, and the height',
            [scans.polyhaven_address(listing, 'colour', '2k')[0], scans.polyhaven_address(listing, 'normal', '1k')[0], scans.polyhaven_address(listing, 'height', '1k')[0]],
            ['https://dl/x_diff_2k.jpg', 'https://dl/x_nor_gl_1k.png', 'https://dl/x_disp_1k.jpg'])
check.equal('...a missing size falls back to the next one, and a map the scan does not have is None', [scans.polyhaven_address(listing, 'normal', '2k')[0], scans.polyhaven_address(listing, 'roughness', '1k')],
            ['https://dl/x_nor_gl_1k.png', None])
surfaces = settings_file.surfaces_table()
named = {k: v for k, v in surfaces.items() if v.get('polyhaven')}
check.true('most surfaces name a photographed scan, and every one that does gives the scan\'s real size in metres (measured from Poly Haven\'s list)',
           len(named) >= 30 and all(v.get('scan_metres') and settings_file.number(v['scan_metres']) > 0 for v in named.values()), details=f'{len(named)} of {len(surfaces)}')
check.true('earth, straw, cloth and thatch soak water up (absorbent); slate, iron and glass do not', all(surfaces[s]['absorbent'] for s in ('dirt_road', 'thatch', 'straw', 'cloth_sack', 'grass'))
           and not any(surfaces[s]['absorbent'] for s in ('slate', 'iron_forged', 'glass_old', 'mud')))
check.true('unpaved grounds (earth, mud, gravel, grass, sand) are marked for stones and puddles; paving and tarmac are not', all(surfaces[s]['unpaved'] for s in ('dirt_road', 'mud', 'gravel_path', 'grass'))
           and not any(surfaces[s]['unpaved'] for s in ('cobble_paving', 'tarmac', 'flagstone')))

# the person's own library: the names of the reference set this project was given (colour, a normal fixed to OpenGL, the DirectX one as uploaded, the height twice)
library = os.path.join(folder, 'library')
reference = os.path.join(library, 'mud')
os.makedirs(reference)
for name in ('colour.png', 'normal.png', 'normal_as_uploaded_directx.png', 'height_as_uploaded.png', 'height.png', 'README.txt'):
    open(os.path.join(reference, name), 'wb').close()
found, conventions = scans.library_files(reference)
check.equal('a library folder is read by the words in its file names: the plain normal and height are chosen over the "as uploaded" and DirectX copies',
            {k: os.path.basename(v) for k, v in found.items()}, {'colour': 'colour.png', 'normal': 'normal.png', 'height': 'height.png'})
only_dx = os.path.join(library, 'only_dx')
os.makedirs(only_dx)
for name in ('albedo.jpg', 'nor_dx.png'):
    open(os.path.join(only_dx, name), 'wb').close()
found, conventions = scans.library_files(only_dx)
check.true('...a folder whose only normal map says DirectX is used, and marked DirectX so it is turned round', found.get('normal', '').endswith('nor_dx.png') and conventions.get('normal') == 'directx')
block = {'folder': library, 'use': {'ground.dirt_road': 'mud', 'wall.*': 'stone', 'thatch': 'reed'}}
check.equal('the library\'s "use" picks an exact role first, then a role pattern, then the surface id',
            [scans.library_choice(block, 'ground.dirt_road', 'dirt_road'), scans.library_choice(block, 'wall.brick', 'brick'), scans.library_choice(block, 'roof.thatch', 'thatch'),
             scans.library_choice(block, 'ground.grass', 'grass')], ['mud', 'stone', 'reed', None])
fake_settings = settings_file.Settings({'own_surfaces': {'folder': os.path.join(folder, 'nowhere'), 'use': {'ground.*': 'mud'}}})
scan, said = scans.choose_scan('ground.grass', 'grass', surfaces['grass'], fake_settings)
check.true('offline, with a library that is not there: no scan, and the sentence says the library could not be used and the made-in-code surface is used',
           scan is None and 'could not be used' in said and 'made-in-code' in said, details=said[:160])
problems = settings_file.validate({'own_surfaces': {'folder': library, 'use': {'grond.dirt_road': 'mud'}, 'metres': {'mud': -1}}, 'surface_scans': 'sometimes'})
check.true('the settings check names a misspelt role in "own_surfaces", a size below 0 and a wrong "surface_scans"', len(problems) == 3, details='; '.join(problems)[:240])

# ---- 2. sites
table = settings_file.species_table()['sites']
cell, shape = 0.1, (60, 80)
x0, y0 = 0.0, 0.0


def blank_grids():
    grids = {name: np.zeros(shape, dtype=np.uint8) for name in ('lowness', 'crown', 'footfall', 'keepclear', 'sheltered', 'shade', 'dampness', 'track', 'seam_blend', 'seam_r', 'seam_g', 'seam_b', 'centre_strip')}
    grids['above_water'] = np.full(shape, 255, np.uint8)
    grids['grows'] = np.full(shape, 255, np.uint8)
    grids['unpaved'] = np.full(shape, 255, np.uint8)
    for name, scale in (('wall_dist', 4.0), ('prop_dist', 4.0), ('verge_dist', 2.0), ('joint_dist', 1.0), ('litter_dist', 1.0)):
        grids[name] = np.full(shape, 255, np.uint8)
    return grids


def distance_grid(marked, scale):
    from place_kit import plan2d
    return np.clip(np.rint(plan2d.distance_to_marked(marked, cell, scale) / scale * 255), 0, 255).astype(np.uint8)


grids = blank_grids()
wall = np.zeros(shape, bool)
wall[50:52, 10:70] = True                                   # a wall 6 m long along x
grids['wall_dist'] = distance_grid(wall, 4.0)
road_edge = np.zeros(shape, bool)
road_edge[10, :] = True                                     # a road's edge along x, 8 m
grids['verge_dist'] = distance_grid(road_edge, 2.0)
grids['centre_strip'][20:24, :] = 255                       # the grass strip between the ruts
joint = np.zeros(shape, bool)
joint[:, 75] = True                                         # a joint across the paving
grids['joint_dist'] = distance_grid(joint, 1.0)
site_grid = sites.site_grids(grids, cell, table)
allowed = sites.gate_grid(grids, {'footfall': 0.6, 'crown': 0.7, 'keepclear': 0.5})
weight = sites.seen_weight(shape, x0, y0, cell, [], 35, 100)
measures = sites.site_measures(site_grid, allowed, weight, cell, table)
check.within('the wall foot is a strip about as long as the wall (6 m), measured from the plan masks', measures['wall_foot']['length_m'], 5.0, 14.0, recorded='18 cm strip both sides of a 6 m wall')
check.within('...the road\'s edge a strip about 8 m long', measures['verge']['length_m'], 7.0, 9.5)
check.true('...and the cells are in exactly one site each', sum(int(site_grid[s].sum()) for s in sites.SITE_ORDER) == shape[0] * shape[1])
counts = sites.targets(measures, table, 'plant', 0.5)
check.close('a site holds its own count: the wall foot gets 6 a metre at full growth times the look (0.5)', counts['wall_foot'], round(6.0 * measures['wall_foot']['seen_length_m'] * 0.5), 0.5)
check.true('...and the background, the largest area, holds only a thin share', counts['background'] / max(sum(counts.values()), 1) < 0.5, details=str(counts))
kinds = {k: v for k, v in settings_file.species_table()['kinds'].items() if v['group'] == 'plant'}
joint_weights = sites.species_weights(kinds, 'joint')
wall_weights = sites.species_weights(kinds, 'wall_foot')
check.true('the species\' "seam" liking is read: in a joint the fern and the bramble (seam 0) never grow, clover and moss do', joint_weights['fern'] == 0 and joint_weights['bramble'] == 0
           and joint_weights['clover'] > 0 and joint_weights['moss_cushion'] > 0)
check.true('...and at a wall foot nettles take a bigger share than in a joint', wall_weights['nettle'] / sum(wall_weights.values()) > joint_weights['nettle'] / sum(joint_weights.values()))
check.true('...and the grass between ruts grows the low plants only (no nettle, fern or bramble share worth naming)', all(sites.species_weights(kinds, 'centre_strip')[k] <= 0.01 for k in ('fern', 'bramble')))
rng = np.random.default_rng(1)
points = sites.pick_cells(rng, site_grid['wall_foot'] & allowed, weight, 200, cell, x0, y0)
named_sites = sites.classify_points(points, grids, x0, y0, cell, table)
check.equal('points picked in a site are classified back into that site (the audit measures what the growth step did)', set(named_sites), {'wall_foot'})
cams = sites.seen_weight(shape, x0, y0, cell, [(-200.0, 0.0)], 35, 100)
check.true('ground farther than the reach from every view camera gets no pieces; a scene with no camera is seen everywhere', float(cams.max()) == 0.0 and float(weight.min()) == 1.0)

# ---- 3. the visible faults, in the pieces
fronds = pieces.make_variants('frond', 6, seed=3)
old_frond = []
rng = np.random.default_rng(3)
for _ in range(6):                                          # the 1.4.0 frond: each blade stood on its edge (its width up and down)
    parts = []
    for _ in range(int(rng.integers(4, 7))):
        angle = rng.uniform(0, 2 * math.pi)
        direction = np.array([math.cos(angle), math.sin(angle), 0.0])
        t = np.linspace(0, 1, 6)
        reach = rng.uniform(0.55, 1.0)
        pts = np.stack([direction[0] * reach * t ** 1.4, direction[1] * reach * t ** 1.4, np.sin(t * 2.2) * 0.55 * reach], axis=1)
        parts.append(pieces._strip(pts, (0.22 * np.sin(np.clip(t, 0.05, 1) * math.pi * 0.9) + 0.03) * reach, (-direction[1], direction[0], 0.0)))
    old_frond.append(pieces.normalise_height(pieces._merge(parts)))
new_up, old_up = float(np.mean([pieces.mean_face_up(v) for v in fronds])), float(np.mean([pieces.mean_face_up(v) for v in old_frond]))
check.controls('a fern frond now lies with its leaf to the sky; the old frond stood on its edge (control): the dark V shapes on the grass and the road',
               {'frond now': new_up}, {'frond as in 1.4.0': old_up}, 0.6, 0.2, recorded='the test place\'s pictures: dark V-shaped specks; keyed by kind, every one was a fern')
check.true('every leafy piece (rosette, frond, leaf) lies mostly flat', all(np.mean([pieces.mean_face_up(v) for v in pieces.make_variants(b, 4, seed=2)]) >= 0.6 for b in pieces.LEAFY_BUILDERS))
stones = settings_file.species_table()['kinds']
facts = {f['id']: f for f in settings_file.facts_table()}
check.true('stones and pebbles are sized by the facts table (the Wentworth scale: pebbles 4 to 64 mm, cobbles 64 to 256 mm) and seated part way into the ground',
           stones['pebble']['size_fact'] == 'pebble_size' and facts['pebble_size']['max'] == 0.064 and facts['cobble_size']['min'] == 0.064 and 0.2 <= stones['pebble']['sink_share'] <= 0.5)

# ---- 4. the judge: the kit's own budget, the facts from the audit, the sites
sys.path.insert(0, os.path.join(KIT, 'calculators'))
import place_audit_check as pac  # noqa: E402
from settings import load_settings  # noqa: E402

house = load_settings()
base = json.load(open(os.path.join(FIXTURES, 'place', 'finished_hut_audit.json'), encoding='utf-8'))


def judge(audit, facts=None):
    findings = pac.Judge(audit, house, facts=facts, skip_freshness=True).run_all()
    return findings, pac.verdict_of(findings)


heavy = copy.deepcopy(base)
heavy['counts']['triangles_by_owner'] = {'hut': 108, 'kit scatter': 1_000_000}
heavy['counts']['triangles'] = 1_000_108
findings, verdict = judge(heavy)
check.true('a million triangles of the kit\'s own scattered pieces are not a builder\'s triangles: no budget failure (they have their own budget, 1.2 million)',
           not any(f['check'] == 'place: budgets' and f['verdict'] == 'fail' for f in findings), recorded='the test place: 2,723,900 scatter triangles failed the per-builder budget as "unowned"')
heavy['counts']['triangles_by_owner']['kit scatter'] = 2_723_900
findings, verdict = judge(heavy)
check.true('...but the kit\'s own scatter over its own budget is still a failure (the growth step must never let it happen)', any(f['check'] == 'place: budgets' and f['verdict'] == 'fail' and 'scattered pieces' in f['text'] for f in findings))
spans = copy.deepcopy(base)
spans['objects'] = [{'name': 'ridge piece', 'role': 'timber.beam', 'exempt': False, 'construction': {'carried': True, 'span_max_m': 3.5, 'max_span_m': 2.5}}]
fact = {'id': 'bay_free_span', 'applies_to_role': '^timber\\.beam$', 'dimension': 'free_span', 'max': 3.9, 'unit': 'metres', 'kind': 'judged', 'source': 'a survey of the period\'s bays', 'confidence': 'weak'}
findings, _ = judge(spans)
check.true('control: a 3.5 m span with no fact fails (a beam may span 2.5 m)', any(f['check'] == 'place: construction' and f['verdict'] == 'fail' for f in findings))
audit_path = os.path.join(folder, 'audit-with-facts.json')
with_facts = dict(copy.deepcopy(spans), place_facts=[fact], facts_files=[{'path': '/x/real-world-facts.json', 'sha1': 'abc'}])
json.dump(with_facts, open(audit_path, 'w'))
run = subprocess.run([sys.executable, '-I', '-B', os.path.join(KIT, 'calculators', 'place_audit_check.py'), 'check', audit_path, '--skip-freshness'], capture_output=True, text=True)
check.true('the judge reads the place\'s own facts from the audit when --facts is not given, so the preflight and the audit agree on the same span',
           'FAIL place: construction' not in run.stdout and 'facts were read from the audit' in run.stdout, details=[l for l in run.stdout.splitlines() if 'construction' in l or 'facts' in l][:3],
           recorded='the test place: the preflight, called without --real-world-facts, failed a 3.50 m ridge span the audit had passed')
even = copy.deepcopy(base)
even['scatter']['sites']['plant'].update(in_sites_share=0.2, shares={'wall_foot': 0.1, 'background': 0.8, 'verge': 0.1})
findings, _ = judge(even)
check.true('the audit says LOOK when most weeds stand on open ground (spread evenly, not where weeds grow)', any(f['check'] == 'place: sites' and f['verdict'] == 'warn' for f in findings))
in_code = copy.deepcopy(base)
in_code['surfaces'] = {'photographed': ['PK ground.dirt_road / dirt_road'], 'made_in_code': ['PK roof.thatch / thatch'], 'fallbacks': {'roof.thatch / thatch': 'no network answer'}}
findings, _ = judge(in_code)
check.true('a material that fell back to the made-in-code surface is a LOOK with the reason, never a FAIL (a place must still finish with no network)',
           any(f['check'] == 'place: surfaces' and f['verdict'] == 'warn' and 'no network' in f['text'] for f in findings) and not any(f['check'] == 'place: surfaces' and f['verdict'] == 'fail' for f in findings))


# ============================================================================================ part B: inside Blender
blender = blender_program()
if not blender:
    check.note('part B skipped: Blender was not found (set BLENDER, run explainer-film-setup, or put blender on the PATH)')
    network_check()
    shutil.rmtree(folder, ignore_errors=True)
    check.finish()
LAUNCHER = os.path.join(PLACE_KIT, 'place_command.py')
PROBE = os.path.join(FIXTURES, 'place', 'probe_real_surfaces.py')
YARD = os.path.join(FIXTURES, 'place', 'make_yard_scene.py')
environment = {name: value for name, value in os.environ.items() if name not in ('RUNPOD_API_KEY', 'RUNPOD_ENDPOINT_ID', 'RENDER_SETTINGS_FILE')}
environment['BLENDER'] = blender
environment['PLACE_KIT_OFFLINE'] = '1'
environment['PLACE_KIT_SCAN_CACHE'] = os.path.join(folder, 'scan-cache')


def place(verb, scene, *arguments, timeout=1200, env=None):
    started = time.time()
    done = subprocess.run([sys.executable, '-I', '-B', LAUNCHER, verb, '--scene', scene] + list(arguments), capture_output=True, text=True, timeout=timeout, env=env or environment)
    return done.returncode, done.stdout + done.stderr, time.time() - started


def probe(scene, name):
    out = os.path.join(folder, f'probe-{name}-{os.path.basename(scene)}.json')
    done = subprocess.run([blender, '-b', '--disable-autoexec', scene, '--python', PROBE, '--', name, out], capture_output=True, text=True, timeout=600, env=environment)
    if not os.path.exists(out):
        raise AssertionError(f'probe {name} wrote nothing: ' + done.stdout[-400:] + done.stderr[-300:])
    return json.load(open(out))


# the person's own library, made here: "earth" (colour, a normal map saved the DirectX way without saying so, a height, 1.5 m a copy) and "stone" (colour and height only)
size = 256
yy, xx = np.mgrid[0:size, 0:size].astype(np.float64) / size
height = 0.5 + 0.25 * np.sin(2 * math.pi * 3 * xx) * np.cos(2 * math.pi * 2 * yy) + 0.15 * np.sin(2 * math.pi * (5 * xx + 4 * yy))
height = (height - height.min()) / (height.max() - height.min())
normal = normals.height_to_normal(heights.calibrate_height(height - height.mean(), 30.0), 1.0, tile=True)
directx = normals.flip_green(normal)
earth = os.path.join(folder, 'own-surfaces', 'earth')
stone = os.path.join(folder, 'own-surfaces', 'stone')
os.makedirs(earth)
os.makedirs(stone)
grey = np.rint(np.stack([height] * 3, axis=-1) * 255).astype(np.uint8)
normals.write_png(os.path.join(earth, 'colour.png'), np.rint(np.stack([0.35 + 0.2 * height, 0.27 + 0.15 * height, 0.18 + 0.1 * height], axis=-1) * 255).astype(np.uint8))
normals.write_png(os.path.join(earth, 'normal.png'), np.rint(normals.to_rgb(directx) * 255).astype(np.uint8))
normals.write_png(os.path.join(earth, 'height.png'), grey)
open(os.path.join(earth, 'metres.txt'), 'w').write('1.5\n')
normals.write_png(os.path.join(stone, 'albedo.png'), np.rint(np.stack([0.5 + 0.2 * height] * 3, axis=-1) * 255).astype(np.uint8))
normals.write_png(os.path.join(stone, 'height.png'), grey)

yard = os.path.join(folder, 'yard', 'yard.blend')
os.makedirs(os.path.dirname(yard))
made = subprocess.run([blender, '-b', '--disable-autoexec', '--python', YARD, '--', yard], capture_output=True, text=True, timeout=300, env=environment)
assert os.path.exists(yard), made.stdout[-300:] + made.stderr[-300:]
settings_path = os.path.join(folder, 'yard', 'place-settings.json')
json.dump({'place': 'test yard', 'look': 'neglected', 'state': 'damp', 'seed': 4,
           'roads': [{'name': 'track', 'polyline': [[-4, 4], [36, 4]], 'width': 3.0, 'gauge': 1.3, 'rut_depth': 0.1, 'centre_grass': True}],
           'own_surfaces': {'folder': os.path.join(folder, 'own-surfaces'), 'use': {'ground.*': 'earth', 'wall.*': 'stone'}}}, open(settings_path, 'w'), indent=1)
finished = os.path.join(folder, 'yard', 'finished.blend')
code, output, seconds = place('finish', yard, '--settings', settings_path, '--save-as', finished)
check.true('the yard finishes with the person\'s own surfaces and passes its audit (exit 0)', code == 0 and os.path.exists(finished), details=f'{seconds:.0f} s; ' + ' | '.join(l for l in output.splitlines() if l.startswith('FAIL'))[:300])
materials = probe(finished, 'materials')['materials']
ground_material = next((m for name, m in materials.items() if name.startswith('PK ground.')), {})
wall_material = next((m for name, m in materials.items() if name.startswith('PK wall.')), {})
check.true('the ground\'s material comes from the person\'s own "earth", the walls\' from their "stone" (nothing was copied: the pictures are read where they are, and packed into the scene)',
           str(ground_material.get('source')) == 'own:earth' and str(wall_material.get('source')) == 'own:stone', details=f'{ground_material.get("source")} / {wall_material.get("source")}')
check.true('...the earth\'s DirectX normal map was caught by the kit\'s own normal test and a corrected copy is the one wired in',
           ground_material.get('normal_pictures') and all('nor' in n for n in ground_material['normal_pictures']), details=str(ground_material.get('normal_pictures')))
cache_info = None
for root, _, files in os.walk(os.path.join(folder, 'scan-cache')):
    for name in files:
        if name == 'info.json' and 'earth' in root:
            cache_info = json.load(open(os.path.join(root, name)))
check.true('...the check is written down once (y read the other way and was turned; x agreed)', bool(cache_info) and cache_info['normal_check']['turned'] == ['y']
           and cache_info['normal_check']['correlation']['x'] > 0.25, details=str((cache_info or {}).get('normal_check'))[:200])
check.true('...the stone, which has no normal map, got one made from its own height', any('made_from_height' in f for root, _, files in os.walk(os.path.join(folder, 'scan-cache')) for f in files))
check.true('...the ground displaces from the scan\'s own height, its middle at the height picture\'s mean (the surface neither rises nor sinks as a whole)',
           ground_material.get('method') == 'BOTH' and ground_material.get('displacement_midlevel') is not None and abs(ground_material['displacement_midlevel'] - float(height.mean())) < 0.05,
           details=f'midlevel {ground_material.get("displacement_midlevel")}, picture mean {height.mean():.3f}')
roof_material = next((m for name, m in materials.items() if name.startswith('PK roof.')), {})
check.true('a surface the library does not name falls back to the made-in-code recipe with the reason (offline here), and the run says so as a LOOK',
           roof_material.get('source') == 'made_in_code' and 'LOOK surfaces: made-in-code surface' in output)
audit = json.load(open(os.path.join(folder, 'yard', 'place-audit.json')))
check.true('the audit lists the photographed and the made-in-code materials, and the normal maps (the corrected one included) all point the right way',
           audit['surfaces']['photographed'] and audit['surfaces']['made_in_code'] and all(i.get('verdict') != 'fail' for i in audit['normal_maps']['images']))
surface_materials = [m for m in materials.values() if m.get('surface')]
check.true('every surface material\'s clear coat is never a mirror (coat roughness 0.15, not Blender\'s 0.03)', surface_materials and all(abs((m.get('coat_roughness') or 0) - 0.15) < 1e-6 for m in surface_materials))
wet = {name: m for name, m in materials.items() if m.get('film_coat') is not None}
absorbent = [m for name, m in wet.items() if m.get('surface') and settings_file.surfaces_table().get(m['surface'], {}).get('absorbent')]
hard = [m for name, m in wet.items() if m.get('surface') and not settings_file.surfaces_table().get(m['surface'], {}).get('absorbent')]
check.true('THATCH SPARKLES: a surface that soaks water up gets no clear wet film (film_coat 0) and stays rough when damp; a hard one keeps its film (control)',
           absorbent and all(m['film_coat'] == 0.0 and m['wet_roughness'] >= 0.55 for m in absorbent) and hard and any(m['film_coat'] > 0 for m in hard),
           details=f'{len(absorbent)} absorbent, {len(hard)} hard', recorded='the test place\'s thatch: white sparkles came from the wetness coat (no coat: none; no wetness: none)')
check.true('...and puddles are drawn only on level ground that holds them: the wetness layer reads the surface\'s "Up", and only ground objects say they hold puddles',
           all('M Up' in m['wetness_masks'] for m in wet.values()))
objects = probe(finished, 'objects')['objects']
check.true('...ground objects hold puddles (pk_holds_puddles 1), a roof never does (0)', all(o['holds_puddles'] == 1.0 for o in objects.values() if (o['role'] or '').startswith('ground.'))
           and all(o['holds_puddles'] == 0.0 for o in objects.values() if (o['role'] or '').startswith('roof.')))
check.true('BROWN RECTANGLES: ground materials blend into the neighbouring ground surface across their seam (seam nodes); walls and roofs do not',
           all(m['seam_nodes'] > 0 for name, m in materials.items() if name.startswith('PK ground.')) and all(m['seam_nodes'] == 0 for name, m in materials.items() if name.startswith(('PK wall.', 'PK roof.'))))
scatter = probe(finished, 'scatter')['scatter']
groups = {}
for row in scatter:
    groups.setdefault(row['group'], 0)
    groups[row['group']] += row['count']
ferns = [r for r in scatter if r['kind'] == 'fern']
check.true('plants, litter and stones were laid (stones only on unpaved ground)', all(groups.get(g, 0) > 0 for g in ('plant', 'litter', 'stone')), details=str(groups))
check.true('DARK SPECKS: the ferns lie with their faces to the sky and every plant and leaf lets some light through (Translucent in the material); stones are rough and bumped',
           (not ferns or all(r['face_up'] >= 0.6 for r in ferns)) and all(r['translucent'] for r in scatter if r['group'] in ('plant', 'litter'))
           and all(r['material'] == 'PK Scatter stone' for r in scatter if r['group'] == 'stone'), details=str([(r['kind'], r['face_up']) for r in ferns][:3]))
plant_sites = audit['scatter']['sites']['plant']
check.true('WEEDS BY SITE: most plants grow at wall feet, verges, fence lines, joints and the grass between ruts; only a thin share on open ground',
           plant_sites['in_sites_share'] >= 0.5 and plant_sites['by_site']['wall_foot'] > 0 and plant_sites['by_site']['verge'] > 0 and plant_sites['by_site']['centre_strip'] > 0,
           details=str(plant_sites['by_site']), recorded='the test place: every species could grow anywhere and a minimum count was topped up across open ground')
record = audit['scatter']['record']['sites']
check.true('...every site holds the count it was planned (laid as planned, and found there again by the audit\'s own recount)',
           all(v['laid'] == v['planned'] for g in record.values() for v in g.values()) and all(audit['scatter']['sites'][g]['by_site'][s] >= 0.95 * v['planned'] for g, by in record.items() for s, v in by.items()),
           details=str({g: {s: (v['planned'], audit['scatter']['sites'][g]['by_site'][s]) for s, v in by.items() if v['planned']} for g, by in record.items()})[:300])
check.true('...the keep-out gates still hold for every group: nothing on a wheel track, a crown, a puddle or a keep-out', all(not any(g.get(k) for k in ('in_keepout', 'in_puddle', 'on_crown', 'on_wheel_track'))
                                                                                                                          for g in audit['scatter']['groups']))
puddles = probe(finished, 'puddles')['puddles']
check.true('PUDDLES: damp ground holds standing water in its ruts and hollows: one flat sheet (role never.puddle, so the renderer rule is unchanged), with a faint ripple, casting no shadow',
           len(puddles) == 1 and puddles[0]['role'] == 'never.puddle' and (puddles[0]['area'] or 0) > 0 and puddles[0]['flat'] is not None and puddles[0]['normal_map'] and not puddles[0]['casts_shadow'],
           details=str(puddles)[:200])
check.true('...and the renderer rule still says EEVEE (a puddle is not a water role)', 'renderer EEVEE' in output)

# ---- the kit never fails its own output: a tiny scatter budget scales every count down instead
small_settings = json.load(open(os.path.join(KIT, 'film-settings.json'), encoding='utf-8'))
small_settings['place_audit']['scatter_triangles_max']['value'] = 20000
small_path = os.path.join(folder, 'film-settings-small-budget.json')
json.dump(small_settings, open(small_path, 'w'), indent=1)
budget_env = dict(environment, FILM_SETTINGS=small_path)
tight = os.path.join(folder, 'yard', 'finished-tight.blend')
code, output, seconds = place('finish', yard, '--settings', settings_path, '--save-as', tight, env=budget_env)
tight_audit = json.load(open(os.path.join(folder, 'yard', 'place-audit.json')))
scatter_triangles = tight_audit['counts']['triangles_by_owner'].get('kit scatter', 0)
check.true('BUDGET: with a scatter budget of 20,000 triangles the growth step scales every count down by one share and stays inside it; the audit does not fail its own scatter',
           code == 0 and scatter_triangles <= 20000 and tight_audit['scatter']['record']['budget_scale'] < 1.0 and 'scaled to' in output,
           details=f'exit {code}, {scatter_triangles} scatter triangles, scale {tight_audit["scatter"]["record"].get("budget_scale")}', recorded='the test place: 87,812 pieces, 2.7 million triangles, failed as "unowned"')
scatter_rows = [o for o in tight_audit['objects'] if str(o.get('name', '')).startswith(('PK scatter', 'PK puddles'))]
check.true('...the scatter is counted as the kit\'s own ("kit scatter"), never as a builder\'s or "unowned"', scatter_rows and all(o['owner'] == 'kit scatter' for o in scatter_rows)
           and scatter_triangles == sum(o['geometry']['triangles'] for o in scatter_rows), details=f'{len(scatter_rows)} objects')

# ---- one real download (only when asked: PLACE_KIT_NETWORK_TESTS=1)
network_check()
shutil.rmtree(folder, ignore_errors=True)
check.finish()
