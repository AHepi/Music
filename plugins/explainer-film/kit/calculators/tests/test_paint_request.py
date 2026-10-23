"""What this does: tests paint_request.py (the painter's request builder and plate preflight) against the project's recorded
cases. Part A needs only the fixtures: the price (it repeats the ledger's own sum, said so), the template's fixed words
(an echo, said so), and the port of the stage's colour finish against coat colours sampled from filmed stills. Part B
uses the project's plates and their plate facts (read only; skipped when they are not on this machine: the film kit through
FILM_KIT or austerity-explainer/film-kit next to the plugins folder, the working files through FILM_WORKING_FILES): the notice corner's
and the people test's prompts rebuilt from their plates, against the prompts they sent (paintings ledgers); the preflight
on the people test plate (lesson 138's glowing hollow, lesson 135's long shadows), round 2's people test plate (red coats)
and the notice corner's plates before and after log 32's fixes; and, as a hold-out the rules were not written from, the
Works W1 plate of round 5 (no painting exists yet, so its results are predictions). Planted faults: a render fault in
the log, a light problem in the shot report, a real person's name.
Run: python3 kit/calculators/tests/test_paint_request.py
"""
import json
import os
import shutil
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES, film_kit_folder, working_files_folder, PROJECT_WORDS, WORKING_FILES_WORDS  # noqa: E402

import numpy as np  # noqa: E402

import paint_request as pr  # noqa: E402
import painting_measures as pm  # noqa: E402
from settings import load_settings  # noqa: E402

settings = load_settings()
check = Checker('paint_request: prompts, preflight and price against the recorded cases')
PAINTING = os.path.join(FIXTURES, 'painting')
WORKING = working_files_folder() or '(working files not given)'
PROJECT = os.path.join(film_kit_folder() or '(film kit not found)', 'assets', 'models')
NOTICE_FACTS = f'{WORKING}/plan3/corner/final/plate-facts-3'
NOTICE_PLATE = f'{WORKING}/plan3/corner/paint/notice-corner-plate-3.jpg'
PEOPLE_FACTS = f'{WORKING}/redesign/people-paint/plate-facts'
PEOPLE_PLATE = f'{PROJECT}/inflation-chapter-2-newcomers/people-test/people-test-plate.jpg'
PEOPLE_HELPER = f'{PROJECT}/inflation-chapter-2-newcomers/people-test/people-test-helper-plate.jpg'
ROUND2 = f'{WORKING}/redesign/round2-figures/plates'
W1_FACTS = f'{WORKING}/redesign/round5-set/state/w1-plate-facts/facts'
WORKS = f'{PROJECT}/inflation-chapter-2-newcomers/works'
NOTICE_LEDGER = json.load(open(os.path.join(FIXTURES, 'notice-corner', 'notice-corner-paintings.json')))
PEOPLE_LEDGER = json.load(open(os.path.join(FIXTURES, 'people-test', 'people-test-paintings.json')))

# ------------------------------------------------------------------------------------------------ A. price, template, finish
args = types.SimpleNamespace(returned=None, send=None, behind=True, rate_cents=None, spent_dollars=None)
cost, _, _ = pr.command_price(args, settings)
check.close('main painting, US cents', cost['main_painting']['cents'], 44.5, 0.05,
            recorded='design (log 35) test case: 4.8 c/MP x (4.02 out + 4.19 plate + 1.05 style)',
            proves='only repeats the rate x (output + inputs) sum the ledger estimate was made with; fal showed no exact charge (story log 34)')
check.close('behind painting, US cents', cost['behind_painting']['cents'], 39.4, 0.05, recorded='design (log 35): 39.4 c',
            proves='only repeats the sum')
check.close('both, US cents', cost['total_cents'], 83.9, 0.1, recorded='people-test-paintings.json note: "about 85 US cents for the two"',
            proves='only repeats the sum the ledger itself made')
big = pr.price(settings, (1504, 2672), [(1536, 2730), (1536, 2730)], 2.4)['cents'] - pr.price(settings, (1504, 2672), [(1536, 2730), (768, 1368)], 2.4)['cents']
check.close('sending the style picture at plate size instead of 1 MP, US cents at 2.4 c/MP', big, 7.5, 0.1,
            recorded='design (log 35): "would add 7.5 c at 2.4 c/MP (plan: about 7 c)"', proves='only repeats the sum')
work = tempfile.mkdtemp(prefix='paint-request-test-')
charges = os.path.join(work, 'charges.json')
json.dump([{'request_id': 'a', 'cents': 50.0, 'output': '1504x2672', 'inputs': ['1536x2730', '768x1368']},
           {'request_id': 'b', 'cents': 44.4, 'output': '1504x2672', 'inputs': ['1536x2730']}], open(charges, 'w'))
fitted, _, _ = pr.command_fit_price(types.SimpleNamespace(charges=charges), settings)
check.close('fit-price recovers a rate from two charges', fitted['fitted_rate_cents_per_megapixel'], 5.4, 0.01,
            recorded='invented charges made at 5.4 c/MP', proves='only that fit-price\'s least squares works; no real fal charge has been read yet')
lines, sentences = pr.load_template('paint-prompt.txt')
header = ' '.join(lines[:1])
check.true('the style header is the ledgers\' first two sentences word for word', NOTICE_LEDGER['paintings'][0]['prompt'].startswith(header)
           and PEOPLE_LEDGER['paintings'][0]['prompt'].startswith(header), recorded='notice-corner-paintings.json and people-test-paintings.json prompts',
           proves='only that the template holds the words (an echo); lesson 97 is why they matter')
dry_never, dry_keep = pr.wetness_words(sentences, False)
wet_never, wet_keep = pr.wetness_words(sentences, True)
check.true('the default words forbid every puddle and reflection and keep nothing wet (the notice corner\'s and people test\'s words, unchanged)', dry_never.startswith('puddles or reflections;') and dry_keep == '',
           recorded='notice-corner-paintings.json and people-test-paintings.json prompts end "Never add: ...; puddles or reflections; a moon..."')
check.true('--keep-wetness keeps the wet ground and forbids only NEW puddles and reflections (a place built wet is not painted dry)', wet_never.startswith('new puddles or reflections') and 'wet ground' in wet_keep and 'image 1' in wet_keep,
           proves='the painter template\'s wet-place words no longer have to be changed by hand for a place built wet')
look = dict(settings.value('painting_tools.paint_request.film_look'))
film = pm.stage_finish(np.array([[46, 39, 32]], float), look)[0]
hue, _ = pm.hue_degrees_and_saturation(film)
check.true('round 3\'s grey coats (plate about 46/39/32) come out olive through the ported finish', all(abs(a - b) <= 4 for a, b in zip(film, (27, 16, 3)))
           and 25 <= hue <= 40, details=f'got {np.round(film).astype(int).tolist()}, hue {hue:.0f} degrees; filmed 27/16/3 and 30/16/3, hue about 30',
           recorded='round3-result.json fixes.summary (the coats sampled on a filmed still)',
           proves='the Python port of cinema-stage.js\'s finish matches a filmed sample within 4 levels (glow, grain and softening left out)')

stage = open(os.path.join(os.path.dirname(CALCULATORS), 'paper-film', 'stage', 'cinema-stage.js')).read()
import re  # noqa: E402
shader = {name: [float(v) for v in re.search(name + r': \{ value: (?:new THREE\.Vector3\()?([-\d., ]+)', stage).group(1).split(',')]
          for name in ('shadowTint', 'highlightTint', 'tintAmount', 'lift', 'contrast')}
same = (shader['shadowTint'] == look['shadow_tint'] and shader['highlightTint'] == look['highlight_tint'] and shader['tintAmount'][0] == look['tint_amount']
        and shader['lift'][0] == look['lift'] and shader['contrast'][0] == look['contrast'])
check.true('the film look in film-settings.json is the stage shader\'s own defaults (no drift)', same, details=json.dumps(shader),
           recorded='paper-film/stage/cinema-stage.js finish pass uniforms', proves='a change to the stage\'s finish is caught here, so the colour check follows it')

# ------------------------------------------------------------------------------------------------ B. the project's plates
have = all(os.path.exists(p) for p in (NOTICE_FACTS, NOTICE_PLATE, PEOPLE_FACTS, PEOPLE_PLATE, PEOPLE_HELPER))
if not have:
    check.note('part B skipped: the project\'s plates and plate facts are not on this machine ('
               + (PROJECT_WORDS if not film_kit_folder() else WORKING_FILES_WORDS) + ')')
    shutil.rmtree(work, ignore_errors=True)
    check.finish()


def view_of(check_file, facts, plate, brief=None, place=None, view=None):
    return pr.View(types.SimpleNamespace(check=check_file, facts=facts, plate=plate, brief=brief, place_facts=place, view=view), settings)


def run_preflight(**extra):
    base = dict(render_log=None, shot_report=None, real_names=None, helper_plate=None, allow_long_shadows=False, work_folder=work, out=None,
                exposure=None, hollow=None, facts=None, plate=None)
    base.update(extra)
    a = types.SimpleNamespace(**base)
    v = view_of(extra['check'], extra['facts'], extra['plate'], extra.get('brief'), extra.get('place_facts'), extra.get('view'))
    return {f['check']: f for f in pr.preflight(v, a)}


nc_check, nc_brief = os.path.join(PAINTING, 'notice-corner-paint-check.json'), os.path.join(PAINTING, 'notice-corner-brief.json')
nc_place = os.path.join(FIXTURES, 'notice-corner', 'notice-corner-place-facts.json')
nc = view_of(nc_check, NOTICE_FACTS, NOTICE_PLATE, nc_brief, nc_place, 'end')
text, numbers = pr.main_prompt(nc)
ledger = NOTICE_LEDGER['paintings'][0]['prompt']
order = [p for p in numbers['parts'] if p != 'fixed']
check.equal('notice corner: the prompt\'s parts, in order', order, ['place_sentence', 'keep', 'notes', 'lamps', 'colour', 'warm', 'brightest', 'thin', 'edges', 'never_add'],
            recorded='the ledger\'s prompt runs header, place, keep-camera, Keep, gates, lamps, gutter and colours, warm, brightest, thin, edges, never add',
            proves='the template gives the ledger\'s structure; the brief\'s words fill it')
warm_sentence = 'Warm light stays only where it already is: round the drum, on the board, on the chair seat, at the lamps and in the few lit windows.'
check.true('notice corner: where warm light stays, word for word', warm_sentence in text and warm_sentence in ledger, details=numbers['warm']['named'],
           recorded='notice-corner-paintings.json prompt', proves='which places are named and their order are measured (a fire in the drum, the notice and '
           'chair owning warm pixels, two lamps, 1.9% on the set); the words for each place are the brief\'s. The 1.5% share limit was set on this case')
check.true('notice corner: "Nothing is brighter than the notice." (the notice is over 1.8 times the frame\'s brightness)', 'Nothing is brighter than the notice.' in text,
           details=numbers['brightest'], recorded='the ledger has the sentence', proves='decided from the plate and the still-life profile, not typed')
ledger_thin = {'lantern', 'lamp post', 'gates', 'chair', 'winding wheels'}
check.true('notice corner: thin parts found on the plate include all five the ledger named', ledger_thin <= set(numbers['thin']['groups']),
           details=f'found {numbers["thin"]["shares"]}; ledger: the lantern\'s wire handle, the lamp arms, the gate bars, the chair rungs, the winding rope',
           recorded='notice-corner-paintings.json prompt', proves='measured from the solo masks (thin = the prop minus its 6 px opening); the chair (4.7%) set the 3% '
                                                                  'limit, so the chair is a repeat; the handcart (7.3%) is an extra the ledger did not name')
pairs = {tuple(sorted((p['a'], p['b']))) for p in numbers['edges']['pairs']}
check.true('notice corner: the near pairs include the drum and the board, and the chair over the notice', ('board', 'drum') in pairs and ('chair', 'notice') in pairs,
           details=sorted(pairs), recorded='ledger: "the drum\'s side and the board\'s left post ... the chair back across the bottom of the notice"',
           proves='measured from the masks (signed distance within twice the clear overlap and gap); the ledger\'s wall pipe and downpipes are not groups, '
                  'so a person adds them in the brief')
check.true('notice corner: the hidden barrel goes in "no ... barrel" with the absent library props', 'barrel' in numbers['never_add']['absent_library_props']
           and 'no coal tub, rails, barrel, crates or litter' in text, recorded='ledger: "extra props (no coal tub, rails, barrel, crates or litter ...)"',
           proves='the barrel group shows 0% of the plate, so it is absent; the library list is the brief\'s')
check.true('notice corner: "a handle on the pail" (a part removed in log 31) in never add', 'a handle on the pail' in text, recorded='ledger', proves='from the brief')
check.true('notice corner: the far work props are grouped "far up on the left"', 'far up on the left the small two-wheeled handcart seen from behind' in text,
           recorded='ledger: "far up on the left the small two-wheeled handcart seen from behind, the coal sacks and the dustbins"',
           proves='side and distance (over 10 m) measured; the words are the check file\'s paint_as')
darker = [g for g in numbers['kept_groups'] if g in ('chair', 'drum', 'pail')]
check.true('notice corner: only the pale chair gets "darker than the notice"', text.count('darker than the notice') == 1
           and 'a small flame inside), darker than the notice;' in text, recorded='ledger: only the chair has "darker than the notice"',
           proves='a repeat: the limit (a story prop\'s brightest 5% at half the notice\'s median) was set on this case (chair 0.55, drum 0.37, pail 0.25)')
near, parallax = pr.behind_list(nc, types.SimpleNamespace(behind_remove=None))
check.equal('notice corner: what the behind painting removes (the slide moves past them by over 10 px)', sorted(near),
            sorted(['notice', 'board', 'drum', 'chair', 'lantern', 'pail', 'lamp post']),
            recorded='notice-corner-paintings.json second prompt: drum, chair with lantern, pail, board with notice, gas lamp; kept the handcart, sacks, dustbins',
            proves='a repeat: the 10 px limit was chosen on this case (handcart 5.8 px kept, lamp post 15 px removed); the parallax itself is frame_geometry\'s sum')
behind_text, _ = pr.behind_prompt(nc, near)
check.true('notice corner: the behind prompt\'s frame is the ledger\'s', behind_text.startswith('Remove these objects from the picture completely:')
           and 'Where each one was, continue exactly what lies behind it:' in behind_text and behind_text.endswith('Add nothing new: no people, no new objects, no flames, smoke, glows or shadows.'),
           recorded='notice-corner-paintings.json second prompt', proves='template echo; what lies behind is the brief\'s words (Blender rays would give them)')

pt_check, pt_brief = os.path.join(PAINTING, 'people-test-paint-check.json'), os.path.join(PAINTING, 'people-test-brief.json')
pt_place = os.path.join(FIXTURES, 'people-test', 'people-test-place-facts.json')
pt = view_of(pt_check, PEOPLE_FACTS, PEOPLE_PLATE, pt_brief, pt_place, 'still')
text, numbers = pr.main_prompt(pt)
people = numbers['people']
check.equal('people test: near men and which way they face', (people['near'], sorted(p['facing'] for p in people['figures'] if p['near'])),
            (5, ['away', 'away', 'away', 'away', 'toward']), recorded='ledger: "five men: four seen from behind ... and one on the left facing us"',
            proves='counted from the plate\'s masks and the place facts\' facing against the plate camera')
check.true('people test: "one on the left facing us, whose face is lost in deep shadow ... with no lit cheek"',
           'and one on the left facing us, whose face is lost in deep shadow under the peak of his cap, with no lit cheek' in text,
           recorded='ledger (without "no lit cheek"); the figures helper found a lit cheek (check-result.json figures)',
           proves='side measured; "no lit cheek" is the skeptic\'s new clause')
check.equal('people test: far figures counted', people['far'], 5, recorded='ledger said six; check-result.json: "The sixth walker is also in neither picture" (0 px)',
            proves='the tool counts only figures that show, so it corrects the ledger\'s six')
check.true('people test: far walkers "flat dark shapes with no pale spots", "Keep the figures as dark as they are in image 1", "No faces anywhere"',
           'they are flat dark shapes with no pale spots' in text and 'Keep the figures as dark as they are in image 1.' in text and 'No faces anywhere' in text,
           details=f'largest head on the film frame {people["largest_head_film_pixels"]:.0f} px (limit {settings.value("people.facing_head_max_pixels")})',
           recorded='skeptic (log 35): far walkers got pale dots; the men went to about 50% of their surround; ledger: "No faces anywhere"',
           proves='the faces sentence is decided by head size (0.23 m at 6.6 m = 58 px); the other two are the new fixed clauses')
check.true('people test: no "Nothing is brighter" sentence for a dark brazier', 'Nothing is brighter' not in text, details=numbers['brightest'],
           recorded='the ledger has none', proves='decided from the plate: the brazier is not 1.8 times the frame\'s brightness')
check.true('people test: never add says "animals or birds", not "people"', 'animals or birds' in text and 'people, animals or birds' not in text,
           recorded='ledger: "animals or birds" (people handled by "Add no people and remove none")', proves='decided by figures being present')
check.true('people test: thin parts include the lamp post, gates and winding wheels', {'lamp post', 'gates', 'winding wheels'} <= set(numbers['thin']['groups']),
           details=numbers['thin']['shares'], recorded='ledger: "the lamp posts and arms, the gate bars, the spokes of the winding wheels"', proves='measured')
check.true('people test: the edges include each man and the next and the men and the lamp post', 'each of the men and the next' in text and
           'the men and the lamp post' in text, recorded='ledger: "each man and the drum, each man and the next, the men and the lamp post"', proves='measured')
near, _ = pr.behind_list(pt, types.SimpleNamespace(behind_remove=None))
behind_text, _ = pr.behind_prompt(pt, near)
check.true('people test: the behind prompt removes all the people and their shadows', behind_text.startswith('Remove all the people from the picture completely:')
           and 'Remove their shadows with them.' in behind_text and len(near) == 10, details=near,
           recorded='people-test-paintings.json second prompt', proves='the people who leave come from the brief\'s "remove": ["figures"]; the count is measured')

found = run_preflight(check=pt_check, facts=PEOPLE_FACTS, plate=PEOPLE_PLATE, helper_plate=PEOPLE_HELPER, place_facts=pt_place, view='still')
glow = found['glow inside a hollow']
check.true('people test plate: the brazier\'s glowing top fails (lesson 138)', glow['verdict'] == 'fail', details=json.dumps(glow['numbers']),
           recorded='Lessons.md 138: the painter lifted the drum\'s faint inner glow into a bright band (people test)',
           proves='a repeat: the 2% limit sits between this plate (8%) and the notice corner\'s kept plate (0.4%)')
shadows = found['figures casting long shadows']
check.true('people test plate: the men\'s long shadows fail (lesson 135)', shadows['verdict'] == 'fail' and abs(shadows['numbers']['mask_share'] - 0.423) < 0.005,
           details=json.dumps(shadows['numbers']), recorded='round3-fixes/state/people-test-state.log: mask 42.3%, outlines 7.5%; Lessons.md 135',
           proves='make_state_picture.py\'s own numbers on the same plates (a repeat); the 3 times limit has this one bad case')
check.equal('people test plate: heads, cloth, surround', (found['heads from behind']['verdict'], found['cloth through the film\'s finish']['verdict'],
                                                          found['figures against their surround']['verdict']), ('pass', 'pass', 'look'),
            recorded='round 3 fixed the heads and coats; the two right-hand men (0.64 of their surround) came out pale khaki, the weakest read (check-looks)',
            proves='the surround warning names the two men the looks helper found weakest')
if os.path.exists(f'{ROUND2}/people-test-plate.png'):
    found = run_preflight(check=pt_check, facts=f'{ROUND2}/plate-facts', plate=f'{ROUND2}/people-test-plate.png', place_facts=pt_place, view='still')
    cloth = found['cloth through the film\'s finish']
    red = {g: v['film'] for g, v in cloth['numbers'].items() if 'suggested_plate' in v}
    check.true('round 2 plate: the two tan coats come out red through the finish', cloth['verdict'] == 'fail' and set(red) == {'man hand on bar', 'man leaning'},
               details=json.dumps(red), recorded='round2-result.json: "a sample of the right man\'s coat reads 26/1/0, a pure red hue"; round 3: 19/1/1 and 23/2/1',
               proves='the ported finish on the plate\'s coat colour predicts the red the film showed (hold-out: the port was not tuned on round 2)')
    check.equal('round 2 plate: the figures against their surround pass (darker tan coats)', found['figures against their surround']['verdict'], 'pass',
                proves='round 3\'s greyer coats fixed the red but read paler: the two checks pull against each other, as the rounds found')
else:
    check.note('round 2\'s plate is not on this machine: skipped')
notice_plates = [(f'{WORKING}/plan3/corner/final/notice-corner-plate.png', 'fail'), (f'{WORKING}/plan3/corner/final/notice-corner-plate-2.png', 'fail'),
                 (f'{WORKING}/plan3/corner/final/notice-corner-plate-3.png', 'pass')]
verdicts = []
for plate, _ in notice_plates:
    if os.path.exists(plate):
        found = run_preflight(check=nc_check, facts=NOTICE_FACTS, plate=plate)
        verdicts.append((found['glow inside a hollow']['verdict'], found['even discs and dark holes']['verdict']))
check.equal('notice corner plates 1, 2 and 3: (glowing hollow, black hole) verdicts', verdicts, [('fail', 'fail'), ('fail', 'fail'), ('pass', 'pass')],
            recorded='log 32: the drum\'s lit lining (lighting round 18) and the pure-black doorway behind the gates were fixed before plate 3 was painted; the '
                     'painting kept a dark sooty hollow and shut-looking gates',
            proves='the hollow limit (2%) was set with plate 3 and the people test, so plate 3 is a repeat; plates 1 and 2 (32% and 15% lit, 0.25% black) were not used')
# planted faults
log = os.path.join(work, 'render.log')
open(log, 'w').write('Fra:1 Mem:...\nShadow buffer full\n')
report = os.path.join(work, 'report.md')
open(report, 'w').write('# Shot check\n\n## Problems\n\n1. **rule 5: notice is the biggest bright thing.** Of the brightest parts ...\n\n## Passed\n\n- rule 2: fine\n')
names = os.path.join(work, 'names.json')
json.dump({'names': ['Clara E. Mattei']}, open(names, 'w'))
brief = json.load(open(nc_brief))
brief['notes'].append('Clara E. Mattei stands at the board.')
planted_brief = os.path.join(work, 'brief.json')
json.dump(brief, open(planted_brief, 'w'))
found = run_preflight(check=nc_check, facts=NOTICE_FACTS, plate=NOTICE_PLATE, render_log=log, shot_report=report, real_names=names, brief=planted_brief)
check.equal('planted: a render fault, a light problem and a real name all fail', (found['render log']['verdict'], found['light rules']['verdict'],
                                                                                  found['real people']['verdict']), ('fail', 'fail', 'fail'),
            proves='the three gates stop a request (a planted fault each)')
# hold-out: the Works W1 plate (round 5), not painted yet
if os.path.exists(W1_FACTS) and os.path.exists(f'{WORKS}/works-w1-plate.jpg'):
    w1_check = os.path.join(FIXTURES, 'works', 'works-w1-shot-check.json')
    w1_place = os.path.join(FIXTURES, 'works', 'works-place-facts.json')
    found = run_preflight(check=w1_check, facts=W1_FACTS, plate=f'{WORKS}/works-w1-plate.jpg', helper_plate=f'{WORKS}/works-w1-behind-plate.jpg',
                          place_facts=w1_place, view='w1', exposure=1.6, hollow=['brazier'])
    check.equal('hold-out W1: the men cast no long shadows (round 3 drew them with only a patch at their feet)', found['figures casting long shadows']['verdict'], 'pass',
                recorded='works-shot.json decisions.men_shadows; round5-set/state/w1-behind.log (7.1%)', proves='a place the rules were not written from')
    check.note(f'hold-out W1 prediction (no painting yet): the brazier\'s top is lit over {found["glow inside a hollow"]["numbers"]["brazier"]["glow_share_of_top"]:.0%} '
               f'(the people test\'s band came from 8%): darken it before painting. Heads, cloth (at page 3\'s exposure 1.6) and surround: '
               f'{found["heads from behind"]["verdict"]}, {found["cloth through the film\'s finish"]["verdict"]}, {found["figures against their surround"]["verdict"]}.')
    w1 = view_of(w1_check, W1_FACTS, f'{WORKS}/works-w1-plate.jpg', pt_brief, w1_place, 'w1')
    text, numbers = pr.main_prompt(w1)
    check.equal('hold-out W1: seven near men, all seen from behind', (numbers['people']['near'], {p['facing'] for p in numbers['people']['figures'] if p['near']}),
                (7, {'away'}), recorded='works-shot.json men_at_no_1 (7 men, turned -14 to 12 degrees, "backs to the lane", round 5 decisions)',
                proves='counted and judged from W1\'s plate masks and the Works place facts, which the rules were not written from')
else:
    check.note('the round 5 W1 plate facts are not on this machine: the W1 hold-out skipped')
shutil.rmtree(work, ignore_errors=True)
check.finish()
