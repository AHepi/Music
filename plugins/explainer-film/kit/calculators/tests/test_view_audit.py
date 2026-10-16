"""What this does: tests view_audit.py (letters in pixels at every view, drum turns, loud unnamed signs, backs of signs,
landmark tops, heads and figures, continuity counts, title contrast) against the project's recorded cases, and says for
each check whether it proves something or only repeats a sum it came from.
Hold-out cases (not used to set any rule): the people test's figure heights against Blender's own masks
(redesign/people-paint/check-figures/figure-boxes.json), round 5's W4 men against Blender's frame boxes
(works-shot.json men_seen), and the checkout's letter sizes against the checkout helper's own numbers.
Run: python3 kit/calculators/tests/test_view_audit.py   (plain Python; no Blender)
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402
import frame_geometry as geometry  # noqa: E402
import view_audit  # noqa: E402
from settings import load_settings  # noqa: E402

check = Checker('view_audit: lettering, figures and landmarks per view')
settings = load_settings()
works = json.load(open(os.path.join(FIXTURES, 'works', 'works-place-facts.json')))
shot = json.load(open(os.path.join(FIXTURES, 'works', 'works-shot.json')))
notice = json.load(open(os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json')))
people = json.load(open(os.path.join(FIXTURES, 'people-test', 'people-test-place-facts.json')))
timeline = os.path.join(os.path.dirname(CALCULATORS), 'examples', 'inflation-chapter-2-newcomers', 'timeline-estimated.json')
SHOT = 'works-shot.json (assemble_works.py, round 5)'


def letter(result, view, sign):
    entry = result['views'][view]
    return entry['signs'][sign][entry['reading_spot']]


# 1. letter heights reproduce the build's own numbers (same sum for upright signs: repeats, not a measurement)
everything = view_audit.audit(works, settings)
for key, view, sign in (('w3 bank sign', 'w3', 'bank sign'), ('w3 No. 1 board', 'w3', 'no-1 board'), ('w3 No. 2 board', 'w3', 'no-2 board'),
                        ('w1 No. 1 board', 'w1', 'no-1 board'), ('w2 No. 2 board', 'w2', 'no-2 board'), ('w1 PETROL', 'w1', 'no-1-drum-petrol'),
                        ('w2 PETROL', 'w2', 'no-2-drum-petrol')):
    check.close(f'{key} letters (px)', round(letter(everything, view, sign)['letter_pixels'], 1), shot['letter_pixels'][key], 0.05,
                recorded=f'{SHOT} letter_pixels', proves='repeats the build\'s sum (h f / d) through the exact projection of a letter')

# 2. the skeptic's correction: turning a board sideways narrows its letters, it does not shorten them; tipping it does
camera = geometry.camera_from_turn([0, 0, 1.7], 0, 0, 0, 60.4, 1080, 1920)
upright = {'name': 'test board', 'centre': [0, 8, 1.7], 'normal': [0, -1, 0], 'letter_height_metres': 0.1, 'words': 'TEST', 'must_read': True}
turned = dict(upright, normal=[0.866025, -0.5, 0])                        # turned 60 degrees about the vertical
tipped = dict(upright, normal=[0, -0.5, 0.866025])                        # tipped back 60 degrees
m_up, m_turn, m_tip = (view_audit.letter_measure(s, camera) for s in (upright, turned, tipped))
check.close('board turned 60 degrees: letter height kept', m_turn['letter_pixels'] / m_up['letter_pixels'], 1.0, 0.002,
            proves='letter height comes from the up-and-down part of the view (skeptic, log 35); the design\'s |n.v| would give 0.5')
check.close('board turned 60 degrees: letter width halved', m_turn['width_factor'], 0.5, 0.01, proves='width comes from the across part')
check.close('board tipped back 60 degrees: letter height halved', m_tip['letter_pixels'] / m_up['letter_pixels'], 0.5, 0.03,
            proves='tipping toward or away from the camera shortens letters')

# 3. WAGES lying flat against standing up, from W4's composed spot (round 2: flat 1 to 2 px, standing about 5 px; round 2's
#    camera stood elsewhere, so this agrees in kind only)
w4 = view_audit.film_camera(works, settings, next(v for v in works['views'] if v['name'] == 'w4'), 'composed')
envelope = next(s for s in works['signs'] if s['name'] == 'wages envelope')
flat = view_audit.letter_measure(dict(envelope, normal=[0, 0, 1]), w4)['letter_pixels']
standing = view_audit.letter_measure(envelope, w4)['letter_pixels']
check.within('WAGES lying flat from W4 (px)', flat, 1.0, 2.0, recorded='round2-result.json checked.findings[5] ("1 to 2 px tall foreshortened")',
             proves='a flat sign\'s letters shrink by the view\'s slope (here about 0.23)')
check.within('WAGES standing up from W4 (px)', standing, 4.5, 7.0, recorded='round 2 ("about 5 px" at 6 m; W4 now 5.1 m away)',
             proves='agrees in kind: round 2\'s camera spot was different')

# 4. pass marks from the evidence (skeptic): PETROL at 22 px warns, does not fail; PITS WILL BE CLOSED at 11 px fails
petrol = letter(everything, 'w1', 'no-1-drum-petrol')
check.equal('W1 PETROL at 22.1 px is "readable, small" (a warning)', petrol['verdict'], 'readable, small',
            recorded='round4-result.json film.summary ("PETROL and DIESEL are fully readable in W1 and W2")',
            proves='the 25 px single-word rule no longer fails what round 4 read easily')
corner = view_audit.audit(notice, settings)
pits = letter(corner, 'end', 'notice')
check.equal('PITS WILL BE CLOSED is "too small"', pits['verdict'], 'too small', recorded='story log 32 "Left for later" (11 px; about 18 would read)',
            proves='the 20 px floor fails it (the 11 px itself is circular: its letter height was derived from 11 px)')
check.close('letters PITS WILL BE CLOSED needs for 20 px (m)', view_audit.needed_height(notice['signs'][0], pits, 20), 0.0325 * 20 / pits['letter_pixels'], 1e-9,
            proves='only repeats the arithmetic (target px x depth / f, with the facing kept)')

# 5. BANK: loud unnamed sign (rounds 3-4), calibrated limit; the page names neither it nor the factories' boards' words
named = ['no-1 board', 'no-2 board']
lit_facts = copy.deepcopy(works)
for sign in lit_facts['signs']:
    sign.pop('dim_until_named', None)
lit = view_audit.audit(lit_facts, settings, ['w3'], named, None, {'w3': {'bank sign': 118, 'no-1 board': 120, 'no-2 board': 120}})
bank = next(s for s in lit['loud_signs'] if s['sign'] == 'bank sign')
check.equal('BANK lit (round 3) is too loud', bank['verdict'], 'too loud', recorded='round3-result.json checked.findings[7] (29 px, 118 levels; boards 14 px, 120)',
            proves='the check flags what round 3 found (this case also set the limit, so it is not independent)')
check.close('BANK lit: share of the No. 1 board (the least legible named sign that reads)', bank['share_of_least_named'], 29.0 * 118 / (14.7 * 120), 0.01,
            proves='repeats the sum (the No. 2 board, 13.8 px, is under the 14 px "not meant to be read" line, so it is no yardstick)')
filmed = view_audit.audit(works, settings, ['w3'], named, None, {'w3': {'bank sign': {'filmed': 52}, 'no-1 board': 120, 'no-2 board': 120}})
bank3 = next(s for s in filmed['loud_signs'] if s['sign'] == 'bank sign')
check.equal('BANK dimmed to 0.3 (52 levels) is still too loud', bank3['verdict'], 'too loud',
            recorded='round4-result.json critique.findings[14] (dimmed to 30%, "still a clear word at phone size"); 52 against 120 levels',
            proves='a dim the critic rejected fails (also used to set the limit)')
dimmed = view_audit.audit(works, settings, ['w3'], named, None, {'w3': {'bank sign': 118, 'no-1 board': 120, 'no-2 board': 120}})
bank15 = next(s for s in dimmed['loud_signs'] if s['sign'] == 'bank sign')
check.equal('BANK at the accepted dim 0.15 is quiet enough', bank15['verdict'], 'quiet enough', recorded='works-effects.js BANK_SIGN.dim 0.15 (round 5)',
            proves='only repeats the calibration: the 0.15 level (32 levels) is predicted from the dim curve, never measured')
check.close('dim the tool asks for BANK (lit levels given)', bank['dim_needed'], 0.15, 0.02, recorded='works-effects.js BANK_SIGN.dim 0.15 (chosen by eye)',
            proves='repeats the calibration (the limit was set from this case)')
page9 = view_audit.audit(works, settings, ['w3'], None, view_audit.narration_of_page(timeline, 9), None)
check.true('page 9 says "banks", so BANK is named there and not judged loud', not any(s['sign'] == 'bank sign' for s in page9['loud_signs']),
           recorded='plan 34 (the bank stays dim until page 9); examples timeline-estimated.json page 9', proves='the narration match works')
check.true('BANK never shows in W1 (behind both spots)', not letter(everything, 'w1', 'bank sign')['in_front'],
           recorded='assemble_works.py lines 165-167 (high enough that W1, which stands under it, never sees it)', proves='plain geometry')

# 6. drums: the turn facing every camera that reads them (maximin), against the hand values +12 and +8
turns = {t['sign']: t for t in everything['stencil_turns']}
check.close('No. 1 PETROL best turn (degrees)', turns['no-1-drum-petrol']['best_turn_degrees'], 12.0, 1.0,
            recorded='assemble_works.py DRUM_SPOTS (+12, chosen by hand)', proves='within the skeptic\'s 1 degree')
check.close('No. 1 DIESEL best turn (degrees)', turns['no-1-drum-diesel']['best_turn_degrees'], 8.0, 2.0,
            recorded='assemble_works.py DRUM_SPOTS (+8)', proves='within the design\'s 2 degrees only (1.5 off): the hand value favours W3, '
            'the formula splits W1 and W3; the end letter changes 1.5 degrees (cos 0.68 against 0.70)')
check.close('No. 2 PETROL best turn mirrors No. 1 (degrees)', turns['no-2-drum-petrol']['best_turn_degrees'], -12.0, 1.2,
            recorded='DRUM_SPOTS (-12)', proves='the mirrored view gives the mirrored turn (W2 stands 0.1 m nearer No. 2\'s drum line)')

# 7. landmark tops and the words band (round 2's conflict; W3 clear but for No. 1's chimney, just under the band)
tops = {(l['view'], l['spot'], l['landmark']): l for l in everything['landmarks']}
for name, expected in (('no-1-chimney-top', 0.020), ('no-2-chimney-a-top', 0.040), ('no-2-chimney-b-top', 0.110)):
    check.close(f'W1 composed {name} down', tops[('w1', 'composed', name)]['down'], expected, 0.001,
                recorded='design (log 35) test cases, round2-result.json "A conflict in the plan"', proves='repeats the projection; inside the band')
check.true('W1 tops are a dark-band matter for a crowd view, not a failure', all(tops[('w1', 'composed', n)].get('dark_band') for n in
           ('no-1-chimney-top', 'no-2-chimney-a-top', 'no-2-chimney-b-top')), recorded='shot_kind_profiles.crowd rule12 (round 5: only 27% of the band is sky)')
for name, expected, verdict in (('no-1-chimney-top', 0.228, 'just under the band'), ('no-2-chimney-a-top', 0.241, 'below the words band'),
                                ('no-2-chimney-b-top', 0.280, 'below the words band')):
    land = tops[('w3', 'plate', name)]
    check.close(f'W3 {name} down', land['down'], expected, 0.001, recorded='design (log 35) test cases', proves='repeats the projection')
    check.equal(f'W3 {name} verdict', land['verdict'], verdict, proves='0.228 sits 0.008 under the band\'s 0.22 bottom: a "look", not a pass')

# 8. a sign's back in a view (round 4 critic: No. 2's board a blank plank from inside its yard)
check.true('No. 2\'s board shows its back in W4', any('no-2 board' in p and 'back' in p and 'w4' in p for p in everything['problems']),
           recorded='round4-result.json critique.findings[9]', proves='found from the facing alone (round 5 added a second, back-to-back board; '
           'the place facts still describe one)')

# 9. heads (formula repeats) and the continuity counts (plan 34: 7, 7, 0, 0, 8, 8)
check.close('head at 6.5 m (px)', geometry.size_in_pixels(camera, settings.value('people.head_height_metres'), 6.5), 58.4, 0.05,
            recorded='design (log 35) test cases', proves='repeats f x 0.23 / d')
counts = view_audit.audit(works, settings, None, None, None, None, {'men at No. 1': 'men_1', 'men at No. 2': 'men_2'},
                          ['men at No. 1', 'men at No. 2'], {'w3/quiet': 7, 'w1/quiet': 7, 'w1/working': 0, 'w2/quiet': 0, 'w2/slowed': 8, 'w4/w4': 8})
for key, expected in (('w3/quiet', 7), ('w1/quiet', 7), ('w1/working', 0), ('w2/quiet', 0), ('w2/slowed', 8)):
    check.equal(f'waiting men in {key}', counts['continuity'][key]['total'], expected,
                recorded='round3-result.json works.summary (continuity sheet: 7, 7, 0, 0, 8, 8)')
check.equal('waiting men in W4 (round 5 layout)', counts['continuity']['w4/w4']['total'], 6,
            recorded='works-shot.json men_seen "w4 composed": Blender\'s boxes put no-2-man-4 and no-2-man-8 wholly left of the frame',
            proves='a finding: round 5\'s W4 shows 6 of the 8 (round 3\'s count of 8 was another layout)')
check.true('the W4 count disagreement is reported as a problem', any('w4/w4' in p for p in counts['problems']))

# 10. hold-out: every man's in-frame verdict against Blender's own frame boxes (works-shot.json men_seen)
by_view = {'w1 composed': ('w1', 'composed'), 'w1 plate': ('w1', 'plate'), 'w3': ('w3', 'plate'), 'w2 composed (slowed)': ('w2', 'composed'),
           'w4 composed (silhouettes)': ('w4', 'composed')}
agree, total = 0, 0
for key, (view_name, spot) in by_view.items():
    cam = view_audit.film_camera(works, settings, next(v for v in works['views'] if v['name'] == view_name), spot)
    figures = {f['name']: f for f in works['figures']}
    for man in shot['men_seen'][key]:
        box = man['film_frame_box']
        blender_in = box[2] >= 0 and box[0] <= 1 and box[3] >= 0 and box[1] <= 1
        ours_in = view_audit.figure_box(cam, figures[man['name']], settings.value('views_and_models.view_audit.figure_half_width_metres')) is not None
        agree += blender_in == ours_in
        total += 1
check.equal('men in or out of the frame, ours against Blender\'s boxes (5 views, 37 men)', agree, total,
            recorded='works-shot.json men_seen (assemble_works.py men_frame_facts: Blender\'s projected outline boxes)',
            proves='hold-out: the figure box agrees with Blender on every man, including W4\'s two outside')

# 11. hold-out: the people test's figures, height on the plate against Blender's id masks
boxes = json.load(open(os.path.join(FIXTURES, 'views-and-models', 'people-test-figure-boxes.json')))
view = people['views'][0]['camera']
plate = geometry.camera_from_turn(view['plate'], view['turn_degrees'], 0, 0, settings.value('frame.plate_vertical_fov_degrees'),
                                  settings.value('frame.plate_width_pixels'), settings.value('frame.plate_height_pixels'))
names = {'figure-facing': 'man facing', 'figure-arms-folded': 'man arms folded', 'figure-stooped': 'man stooped',
         'figure-hand-on-bar': 'man hand on bar', 'figure-leaning': 'man leaning', **{f'figure-walker-{i}': f'walker {i}' for i in range(1, 7)}}
worst = 0.0
for figure in people['figures']:
    box = view_audit.figure_box(plate, figure, settings.value('views_and_models.view_audit.figure_half_width_metres'))
    ratio = (box[3] - box[1]) * plate['frame'][1] / boxes[names[figure['name']]]['h_px']
    worst = max(worst, abs(ratio - 1))
check.within('people test: worst figure height against the masks (share off)', worst, 0.0, 0.06,
             recorded='redesign/people-paint/check-figures/figure-boxes.json (h_px, plate pixels; 11 figures)',
             proves='hold-out: figure size on the plate within 6% (the stooped man\'s box overstates him most)')
people_audit = view_audit.audit(people, settings)
facing = next(f for f in people_audit['figures'] if f['figure'] == 'figure-facing')
walkers = [f for f in people_audit['figures'] if 'walker' in f['figure']]
check.true('the facing man can show his face; the far walkers cannot', facing['face_can_show'] and not any(w['face_can_show'] for w in walkers))
check.true('faces are a "look", never a failure', not people_audit['problems'] and any('can show their faces' in w for w in people_audit['warnings']),
           recorded='people-paint check-result.json: the facing man got a blank face; the far walkers got face dots (the painter did the opposite '
           'of the geometry)', proves='the head-size rule cannot predict the painter, so it only asks a person to look')

# 12. hold-out: the checkout's letters from its own build numbers (letter heights 0.10, 0.11, 0.42 m from assemble_checkout.py)
checkout_shot = json.load(open(os.path.join(FIXTURES, 'checkout-c1', 'checkout-shot.json')))
spots = checkout_shot['spots']
checkout = {'place_facts_version': 1, 'place': 'checkout', 'views': [{'name': 'c1', 'kind_of_shot': ['interior'], 'subject': {'name': 'bill', 'point': spots['bill']},
            'camera': {'composed': checkout_shot['views']['c1']['composed'], 'plate': checkout_shot['views']['c1']['plate'], 'turn_degrees': 0.0}}],
            'signs': [{'name': 'bill', 'centre': spots['bill-words'], 'normal': [0, -1, 0], 'letter_height_metres': 0.10, 'words': 'NEW MONEY PRICES WILL GO UP', 'must_read': True},
                      {'name': 'checkout sign', 'centre': spots['checkout-sign'], 'normal': [0, -1, 0], 'letter_height_metres': 0.11, 'words': 'CHECKOUT', 'must_read': True, 'both_faces': True},
                      {'name': 'petrol fascia', 'centre': spots['petrol-fascia'], 'normal': [0, -1, 0], 'letter_height_metres': 0.42, 'words': 'PETROL DIESEL', 'must_read': True}],
            'figures': [], 'landmark_tops': [], 'states': {}}
checked = view_audit.audit(checkout, settings)
for sign, key in (('bill', 'bill big words'), ('checkout sign', 'CHECKOUT'), ('petrol fascia', 'PETROL · DIESEL')):
    check.close(f'checkout {key} letters (px)', round(letter(checked, 'c1', sign)['letter_pixels'], 1), checkout_shot['letter_pixels'][key], 0.25,
                recorded='checkout-shot.json letter_pixels (the checkout helper\'s own numbers)', proves='hold-out place; the same formula in other code (a cross-check, not a measurement)')
check.close('checkout bill letters at the plate spot (px)', round(checked['views']['c1']['signs']['bill']['plate']['letter_pixels'], 1),
            checkout_shot['letter_pixels']['bill big words, plate spot'], 0.25, recorded='checkout-shot.json letter_pixels')
page1 = view_audit.audit(checkout, settings, None, None, view_audit.narration_of_page(timeline, 1), None)
fascia = next((s for s in page1['loud_signs'] if s['sign'] == 'petrol fascia'), None)
check.note(f'prediction nobody has judged yet: on page 1 (which does not say petrol) PETROL DIESEL reads at '
           f'{fascia["share_of_least_named"]:.2f} of CHECKOUT by letter size alone ({fascia["verdict"]}; limit {fascia["limit"]}); measure its '
           f'brightness on the plate before acting on it')

# 13. title contrast: the band arithmetic on made-up pictures (no recorded case)
import tempfile  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
with tempfile.TemporaryDirectory() as folder:
    grey = os.path.join(folder, 'grey.png')
    Image.fromarray(np.full((192, 108, 3), 128, dtype=np.uint8)).save(grey)
    result, _ = view_audit.title_contrast(grey, [0.1, 0.1, 0.9, 0.3], [255, 255, 255], settings)
    background = view_audit.relative_luminance([128, 128, 128])
    check.close('white words on 128 grey: band opacity', result['band_opacity_needed'], 1 - ((1.05 / 4.5) - 0.05) / background, 1e-9,
                proves='only the arithmetic: a = 1 - ((L_text + 0.05)/4.5 - 0.05)/L_background')
    dark = os.path.join(folder, 'dark.png')
    Image.fromarray(np.full((192, 108, 3), 30, dtype=np.uint8)).save(dark)
    result, _ = view_audit.title_contrast(dark, [0.1, 0.1, 0.9, 0.3], [255, 255, 255], settings)
    check.equal('white words on near-black need no band', result['band_opacity_needed'], 0.0)

# 14. the command line: a report with the settings it used, and exit 1 on problems
import subprocess  # noqa: E402
run = subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'view_audit.py'), 'audit', '--place-facts',
                      os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json')], capture_output=True, text=True, timeout=60)
check.true('command line: exits 1 on a problem and names the settings used', run.returncode == 1 and 'Settings used' in run.stdout
           and 'lettering.must_read_min_pixels' in run.stdout, details=f'exit {run.returncode}')
check.finish()
