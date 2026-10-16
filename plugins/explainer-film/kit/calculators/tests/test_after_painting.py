"""What this does: tests after_painting.py (the checks every returned painting goes through) on the project's real paintings:
the people test's and the notice corner's paintings as the painter returned them (the project's working files, read only)
and as kept in the film kit (film-kit/assets/models/..., read only), with their plates and plate facts. It reproduces the recorded
line-ups (paintings ledgers), the figures helper's outline measures (redesign/people-paint/check-figures/outline-chamfer.json),
the looks helper's tone and style measures (check-looks), the leftover shadows of lesson 135 and the kept shadows of
lessons 122 and 125, and catches planted faults: a painting shifted past the search, a person added, a man lost.
The project's pictures are needed: the film kit (FILM_KIT, or austerity-explainer/film-kit next to the plugins folder) and
the working files (FILM_WORKING_FILES: redesign/people-paint and plan3/corner); the test is skipped (exit 77) with the
reason when they are not on this machine.
Run: python3 kit/calculators/tests/test_after_painting.py   (about two minutes)
"""
import json
import os
import shutil
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, FIXTURES, skip, film_kit_folder, working_files_folder, missing, PROJECT_WORDS, WORKING_FILES_WORDS  # noqa: E402

import cv2  # noqa: E402
import numpy as np  # noqa: E402

import after_painting as ap  # noqa: E402
import painting_measures as pm  # noqa: E402
from settings import load_settings  # noqa: E402

FILM_KIT, WORKING = film_kit_folder(), working_files_folder()
if not FILM_KIT:
    skip('after_painting: the project\'s paintings', PROJECT_WORDS)
if not WORKING:
    skip('after_painting: the project\'s paintings', 'the paintings as the painter returned them and their plate facts are in the working files; '
         + WORKING_FILES_WORDS)
PROJECT = f'{FILM_KIT}/assets/models'
PEOPLE = f'{PROJECT}/inflation-chapter-2-newcomers/people-test'
PEOPLE_RAW = f'{WORKING}/redesign/people-paint/downloads'
PEOPLE_FACTS = f'{WORKING}/redesign/people-paint/plate-facts'
CHAMFER = os.path.join(FIXTURES, 'painting', 'people-test-outline-chamfer.json')   # the figures helper's outline numbers (small; copied)
CORNER = f'{WORKING}/plan3/corner'
NOTICE = f'{PROJECT}/pit-village'
needed = [f'{PEOPLE}/people-test-plate.jpg', f'{PEOPLE}/people-test-painting.png', f'{PEOPLE_RAW}/painted-1.png', f'{PEOPLE_RAW}/behind-1.png',
          f'{PEOPLE_FACTS}/ids.png', f'{CORNER}/paint/downloads/painted-1-raw.png', f'{CORNER}/final/plate-facts-3/ids.png', f'{NOTICE}/notice-corner-painted.jpg']
if missing(needed):
    skip('after_painting: the project\'s paintings', f'{len(missing(needed))} of its pictures or plate facts are not on this machine '
         f'(first: {missing(needed)[0]})')

settings = load_settings()
check = Checker('after_painting: the arrival checks on the real paintings')
PAINTING = os.path.join(FIXTURES, 'painting')
work = tempfile.mkdtemp(prefix='after-painting-test-')


def run(**extra):
    base = dict(behind=None, near=None, near_list=None, helper_plate=None, figures=None, standard=None, out_folder=work)
    base.update(extra)
    result, lines, code = ap.command_check(types.SimpleNamespace(**base), settings)
    return result, {c['check']: c for c in result['checks']}, code


# ------------------------------------------------------------------------------------------------ the people test, as returned
pt_check = os.path.join(PAINTING, 'people-test-paint-check.json')
result, found, code = run(painting=f'{PEOPLE_RAW}/painted-1.png', plate=f'{PEOPLE}/people-test-plate.jpg', check=pt_check, facts=PEOPLE_FACTS,
                          behind=f'{PEOPLE_RAW}/behind-1.png', helper_plate=f'{PEOPLE}/people-test-helper-plate.jpg',
                          out_folder=os.path.join(work, 'people'))
a = result['alignment']
check.true('people test: lined up 0.874 to 0.903 at stretch 1.0010, shift +1.0, +0.5', (a['before'], a['after'], a['stretch'], a['shift']) == (0.874, 0.903, 1.001, [1.0, 0.5])
           and found['lined up with the plate']['verdict'] == 'pass', details=a['printed'], recorded='people-test-paintings.json lined_up',
           proves='the chain (Lanczos resize, then align_painting.py) reproduces the recorded line-up; align_painting.py was built on the notice corner (log 32), '
                  'so this is a hold-out for the tool, not for the pass logic')
aligned = cv2.imread(result['aligned']).astype(int)
kept = cv2.imread(f'{PEOPLE}/people-test-painting.png').astype(int)
check.equal('people test: the lined-up painting equals the film kit\'s people-test-painting.png', int(np.abs(aligned - kept).max()), 0,
            recorded='film-kit/assets/models/inflation-chapter-2-newcomers/people-test/people-test-painting.png', proves='the same file, pixel for pixel')
recorded = json.load(open(CHAMFER)) if os.path.exists(CHAMFER) else {}
outlines = result['figures']['outlines']
worst = max((abs(outlines[g]['within_painting'] - v['within3']) for g, v in recorded.items() if g in outlines), default=None)
check.true('people test: each figure\'s outline share within 3 px matches the figures helper\'s, painting and plate baseline', worst is not None and worst <= 0.005
           and max(abs(outlines[g]['within_plate_baseline'] - v['base_within3']) for g, v in recorded.items() if g in outlines) <= 0.005,
           details=f'largest difference {worst}', recorded='redesign/people-paint/check-figures/outline-chamfer.json (10 figures)',
           proves='the same measure as the helper\'s scripts/chamfer.py')
moved = sorted(g for g, v in outlines.items() if v['within_painting'] < v['within_plate_baseline'] - 0.05)
check.equal('people test: the skeptic\'s outline rule fails only walkers 4 and 5', moved, ['walker 4', 'walker 5'],
            recorded='check-result.json figures: walker 4 (31% visible in the plate) was painted whole beside the post; the bag of the walker behind walker 1 '
                     '(walker 5, the man with the bag) was lost. The five near men keep their poses; the old rule (IoU 0.85) failed two of them',
            proves='both flags are real changes, and the hand-on-bar man (0.945 against a noisy 0.838 baseline) passes')
tones = result['figures']['tones']
front = [tones[g] for g in ('man stooped', 'man arms folded', 'man facing')]
check.true('people test: the front men go from about 0.15 to about 0.50 of their surround and fail', all(0.12 <= t['plate'] <= 0.17 and 0.45 <= t['painting'] <= 0.53 for t in front)
           and found['figures as dark as in the plate']['verdict'] == 'fail', details=json.dumps({g: tones[g] for g in ('man stooped', 'man arms folded', 'man facing')}),
           recorded='check-result.json looks: "In the plate the men were about 15% as bright as what surrounds them ... In the painting they are about 50%" (a must-fix)',
           proves='the looks helper\'s measure (measure1.py) reproduced; the pass mark (0.35 or 1.5 times the plate) is invented between these numbers')
heads = result['figures']['heads']
check.true('people test: skin added on the hand-on-bar man\'s head (none in the plate) is flagged to look at', heads['man hand on bar']['plate'] == 0
           and heads['man hand on bar']['painting'] >= 100 and found['no skin added on heads']['verdict'] == 'look', details=json.dumps(heads),
           recorded='check-result.json figures: "0 skin-coloured pixels in the plate, 183 in the painting" (in a 110 px box round his head)',
           proves='the same skin rule in the head region gives 0 and 165; the facing man\'s lit cheek (143 to 779) is flagged too. The leaning and stooped men gain '
                  'skin pixels as the whole painting lightens (the helper called their ear edges old), so this is a "look", not a failure')
style = found['style against the standard painting']
got = style['numbers']['got']
check.true('people test: only the warm ground differs from the standard (10.0% against 19.7%)', style['verdict'] == 'look' and 'warm light on' in style['what']
           and 'brightness' not in style['what'] and abs(got['brightness'] - 77.4) < 0.1 and abs(got['spread'] - 26.1) < 0.1,
           details=json.dumps(got), recorded='check-looks: brightness 77.4/77.4, spread 26.1/26.1, colour 45/50, ink 6.4%/6.7%; warm ground 11.6% (film crop) '
                                             'against 19.7%, "the warm heart of the picture is small"',
           proves='the looks helper\'s measures; over the whole painting the warm ground is 10.0% (11.6% was measured on the film\'s crop)')
behind = found['behind painting lined up against the painting']
check.true('people test: the behind painting lines up at 0.999 against the painting', behind['numbers']['before'] == 0.999 and behind['numbers']['after'] == 0.999,
           details=behind['numbers']['printed'], recorded='people-test-paintings.json: "0.999 before and after (shift +1.0, 0 pixels)"', proves='reproduced')
behind_out = cv2.imread(result['behind']['aligned']).astype(int)
recorded_behind = f'{WORKING}/redesign/people-paint/behind-1-aligned.png'
if os.path.exists(recorded_behind):
    check.equal('people test: the lined-up behind painting equals the one the state picture was made from', int(np.abs(behind_out - cv2.imread(recorded_behind).astype(int)).max()), 0,
                recorded='redesign/people-paint/behind-1-aligned.png', proves='the same file, pixel for pixel')
left = found['leaving people took their shadows']
check.true('people test: the men\'s cast shadows left in the behind painting fail (lesson 135)', left['verdict'] == 'fail'
           and left['numbers']['expected_brightening'] > 10 and abs(left['numbers']['painted_brightening']) < 2, details=json.dumps(left['numbers']),
           recorded='check-result.json painter-faults: helper plate 11.3 L brighter there; the people-out painting differs from the painting by only 0.7 L (must-fix)',
           proves='found from the plates alone: where the plate is under 0.75 of the helper plate outside the men, the behind painting did not brighten')
check.equal('people test: the chain says fail (a re-ask or a free fix is needed)', code, 1, proves='the failures above stop the painting being used as it is')

# ------------------------------------------------------------------------------------------------ the notice corner, as returned
nc_check = os.path.join(PAINTING, 'notice-corner-paint-check.json')
result, found, code = run(painting=f'{CORNER}/paint/downloads/painted-1-raw.png', plate=f'{CORNER}/paint/notice-corner-plate-3.jpg', check=nc_check,
                          facts=f'{CORNER}/final/plate-facts-3', behind=f'{CORNER}/paint/downloads/behind-1-raw.png', out_folder=os.path.join(work, 'notice'))
a = result['alignment']
check.true('notice corner: lined up 0.70 to 0.96 at stretch 1.0065, shift +3, +3', abs(a['before'] - 0.70) < 0.005 and abs(a['after'] - 0.96) < 0.005
           and a['stretch'] == 1.0065 and a['shift'] == [3.0, 3.0], details=a['printed'], recorded='notice-corner-paintings.json lined_up; lesson 123',
           proves='reproduced (the case the tool was built on: a repeat)')
behind = found['behind painting lined up against the painting']
check.true('notice corner: the behind painting lines up 0.990 to 0.991 at -0.5, -1.0', (behind['numbers']['before'], behind['numbers']['after'], behind['numbers']['shift'])
           == (0.99, 0.991, [-0.5, -1.0]), details=behind['numbers']['printed'], recorded='notice-corner-paintings.json: "0.990 before, 0.991 after (shift -0.5, -1.0 pixels)"',
           proves='reproduced with the check file\'s story props as the removed things (the ledger also removed the lamp post: with it, 0.997)')
bands = result['behind']['bands']
check.true('notice corner: with the shadows kept, the ground beside every near prop changes under 2 levels; the raw behind painting lifts it by the pail',
           all(v['combined_change'] <= 2 for v in bands.values()) and bands['pail']['behind_change'] >= 10, details=json.dumps(bands),
           recorded='log 32 (lessons 122, 125): the pavement patch beside the pail stayed 70 to 71 once the shadows were kept, against 89 before',
           proves='keep_painted_shadows.py does its job (a repeat of log 32 with the ring 10-30 px beside each prop: the pail\'s ring rises 24 levels without it)')
check.equal('notice corner: the style measures are the standard (it is the standard painting)', found['style against the standard painting']['verdict'], 'pass',
            proves='only repeats where the standard numbers came from')

# ------------------------------------------------------------------------------------------------ the film kit's kept paintings
result, found, code = run(painting=f'{NOTICE}/notice-corner-painted.jpg', plate=f'{CORNER}/paint/notice-corner-plate-3.jpg', check=nc_check,
                          facts=f'{CORNER}/final/plate-facts-3', out_folder=os.path.join(work, 'kept'))
check.equal('film kit\'s notice-corner-painted.jpg: a JPEG (look), already lined up (pass)', (found['kept lossless']['verdict'], found['lined up with the plate']['verdict'],
                                                                                            'already lined up' in found['lined up with the plate']['what'].lower()), ('look', 'pass', True),
            recorded='round 2 (a JPEG moves every pixel); the people test ledger keeps its main painting as PNG',
            proves='a lined-up painting passes without a gain; the JPEG is named for whoever uses it as a base')
plate_style = ap.style_measures(pm.read_rgb(f'{PEOPLE}/people-test-plate.jpg', (1536, 2730)), settings)
found_style = []
ap.style_check(pm.read_rgb(f'{PEOPLE}/people-test-plate.jpg', (1536, 2730)), settings, found_style)
check.true('the people test plate (a 3D render) fails the style match on brightness and colour', found_style[0]['verdict'] == 'look'
           and 'brightness' in found_style[0]['what'] and 'colour' in found_style[0]['what'], details=json.dumps(plate_style),
           recorded='check-looks: the plate 48.9 brightness, colour 69, against the paintings\' 77.4 and 45-50',
           proves='the style measures tell a render from a painting (a stand-in for lesson 97\'s near-photograph, which was not kept)')

# ------------------------------------------------------------------------------------------------ planted faults
plate_size = (1536, 2730)
shifted = np.roll(pm.read_rgb(f'{PEOPLE}/people-test-painting.png'), (0, 30), axis=(0, 1))
shifted_path = os.path.join(work, 'shifted.png')
ap.write_png(shifted_path, shifted)
numbers = pm.align(pt_check, PEOPLE_FACTS, shifted_path, os.path.join(work, 'shifted-aligned.png'))
verdict, words = ap.judge_alignment(numbers, settings)
check.true('planted: a painting shifted 30 px (21 px at 1080 wide) fails at the edge of the search', verdict == 'fail' and 'edge of the search' in words,
           details=numbers['printed'], proves='a shift past the 12 px search is caught instead of passing on a partial fit')
painting = pm.read_rgb(f'{PEOPLE}/people-test-painting.png')
plate = pm.read_rgb(f'{PEOPLE}/people-test-plate.jpg', plate_size)
shot = pm.load_shot(pt_check, PEOPLE_FACTS)
figures = shot.check['figures']
found_real = []
ap.figure_checks(painting, plate, shot, figures, settings, found_real)
check.equal('the people test painting: no added person found', {f['check']: f['verdict'] for f in found_real}['no added people'], 'pass',
            recorded='check-result.json figures: "The painter added nobody and took nobody away"', proves='no false alarm on the real painting (one door panel '
            'a person\'s height for where it stands is rejected by its fill, set on this case)')
feet = 1450
tall = ap.standing_height_pixels(shot, feet / 2730, settings) * 2730
added = painting.copy()
cv2.ellipse(added, (250, int(feet - 0.45 * tall)), (int(tall / 8), int(0.42 * tall)), 0, 0, 360, (12, 10, 9), -1)
cv2.circle(added, (250, int(feet - 0.93 * tall)), int(tall / 13), (12, 10, 9), -1)
found_added = []
ap.figure_checks(added, plate, shot, figures, settings, found_added)
check.equal(f'planted: a dark standing person ({tall:.0f} px, a person\'s height where his feet are) on the left pavement is noticed',
            {f['check']: f['verdict'] for f in found_added}['no added people'], 'look', proves='a person-sized dark shape with no plate figure there is reported')
lost = painting.copy()
behind_picture = pm.read_rgb(f'{PEOPLE}/people-test-painting-behind.jpg', plate_size)
man = cv2.dilate(pm.mask_at(shot.visible['man arms folded'], plate_size).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
lost[man] = behind_picture[man]
found_lost = []
result_lost = ap.figure_checks(lost, plate, shot, figures, settings, found_lost)
outline = result_lost['outlines']['man arms folded']
check.true('planted: a man painted out fails his outline check', outline['within_painting'] < outline['within_plate_baseline'] - 0.05
           and {f['check']: f['verdict'] for f in found_lost}['figures kept their outlines'] == 'fail', details=json.dumps(outline),
           proves='a lost person is caught by his own outline (the arms-folded man, 0.999 when painted)')
shutil.rmtree(work, ignore_errors=True)
check.finish()
