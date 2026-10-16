"""What this does: tests plan_states.py (the state picture planner) on the Works' pages 3, 4 and 12 and on the people test.
Part A needs only the fixtures: the plates the pages need (round 4 found the windows-only slowed plate missing for page 12),
the two-sub-changes error, the lesson 136 warning, the behind plate for W1's slide only, the workers' head sizes, a cue in
the words band, and planted faults (a change inside a slide; a behind picture from the wrong state, round 3's lit doorway).
Part B measures the Works' and the people test's real plates with make_state_picture.py (skipped when they are not on
this machine: the plates come from the film kit, FILM_KIT or austerity-explainer/film-kit next to the plugins folder; their
plate facts from the working files, FILM_WORKING_FILES): the swap shares the round logs recorded, cut or blend, the
long-shadow error and the thresholds from noise.
Run: python3 kit/calculators/tests/test_plan_states.py
"""
import json
import os
import shutil
import sys
import tempfile
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, FIXTURES, film_kit_folder, working_files_folder, PROJECT_WORDS, WORKING_FILES_WORDS  # noqa: E402

import plan_states as ps  # noqa: E402
from settings import load_settings  # noqa: E402

settings = load_settings()
check = Checker('plan_states: helper plates, cut or blend, against the Works and the people test')
PAINTING = os.path.join(FIXTURES, 'painting')
WORKING = working_files_folder() or '(working files not given)'
MODELS = os.path.join(film_kit_folder() or '(film kit not found)', 'assets', 'models', 'inflation-chapter-2-newcomers')
WORKS = os.path.join(MODELS, 'works')
PEOPLE = os.path.join(MODELS, 'people-test')
WHY_SKIPPED = PROJECT_WORDS if not film_kit_folder() else WORKING_FILES_WORDS
work = tempfile.mkdtemp(prefix='plan-states-test-')


def plan(path, measure=False, plate_folder=None, facts=None, edit=None):
    if edit:
        data = json.load(open(path))
        edit(data)
        data['place_facts'] = os.path.join(os.path.dirname(path), data['place_facts'])
        path = os.path.join(work, 'plan.json')
        json.dump(data, open(path, 'w'))
    a = types.SimpleNamespace(plan=path, measure=measure, work_folder=os.path.join(work, 'trial'), out_folder=None, plate_folder=plate_folder,
                              facts_folder=facts)
    result, lines, code = ps.command_plan(a, settings)
    return result, code


works_plan = os.path.join(PAINTING, 'works-state-plan.json')
result, code = plan(works_plan)
plates = [(p['view'], p['state']) for p in result['plates']]
check.true('the Works: the plates of works-shot.json are all planned', all(p in plates for p in [('w3', 'quiet'), ('w1', 'quiet'), ('w1', 'men gone'),
           ('w1', 'working'), ('w1', 'quiet, no men'), ('w2', 'quiet'), ('w2', 'slowed')]), details=plates,
           recorded='works-shot.json "plates" (W3, W1 main, working, men gone, behind = quiet with no men, W2 main, W2 slowed)',
           proves='derived from the page plan and the place facts\' states, not listed by hand')
check.true('the Works: page 12 needs the windows-only slowed plate round 4 found missing', ('w2', 'slowed (only windows_2, gate_2, workers_2)') in plates,
           recorded='round4-result.json pageFixes: "Page 12 still needs a second slowed state picture with only the windows dark"; Status task 43',
           proves='found from the words: "slows" changes the windows and gate, "workers" (1.4 s later) brings the men')
errors = [p for p in result['problems'] if p['kind'] == 'error']
check.true('the Works: the round 5 slowed plate is reported as two sub-changes on one plate', len(errors) == 1 and errors[0]['word'] == 'slows'
           and errors[0]['fields_later'] == {'men_2': 'workers'}, details=errors[0]['what'] if errors else 'none',
           recorded='round 4: "one slowed picture held both the dark windows and the men, so a window blend on slows would fade the men in as ghosts"',
           proves='the skeptic\'s new error, on the case it was named for (a repeat of round 4\'s finding, made automatically)')
warnings = [p['what'] for p in result['problems'] if p['kind'] == 'warning']
check.true('the Works: men appearing alone on "workers" get lesson 136\'s warning; "go" does not (the gate and doorway change too)',
           any('"workers": only people change' in w for w in warnings) and not any('"go": only people' in w for w in warnings),
           recorded='Lessons.md 136; works-shot.json states (go opens the gate and No. 1\'s cart doors and lights its doorway)',
           proves='decided from which state fields change on each word')
behinds = {b['view']: b for b in result['behind_plates']}
check.true('the Works: W1\'s slide needs the behind plate "quiet, no men"; W2\'s does not (nobody waits there)', behinds['w1']['behind_state'] == 'quiet, no men'
           and behinds['w1']['near_people_groups'] == ['men at No. 1'] and behinds['w2']['behind_state'] is None,
           details=json.dumps({v: (b['behind_state'], b['near_people_pixels']) for v, b in behinds.items()}),
           recorded='works-shot.json plates: works-w1-behind-plate.jpg ("quiet, no men"); page-3.js hides the men in the behind ring; page 4 has none',
           proves='the men slide 2.2 to 4.9 px over the 1.2 m slide (frame_geometry\'s parallax sums); the 2 px figures\' limit was set on this case, so this is a repeat')
heads = [v for b in result['busy_states'] if b['view'] in ('w1', 'w2') for v in b['worker_heads_pixels'].values()]
check.within('the Works: workers in the lit doorways have heads of', min(heads), 15, 24, recorded='round 4 critic and round 5: "heads 20 to 24 px" at 17 m or more',
             proves='frame_geometry\'s sizes from the place facts; all under the 24 px limit (smallest shown)')
check.within('the Works: largest worker head (px)', max(heads), 15, 24, proves='no face can show (people.facing_head_max_pixels 24, invented)')
start = next(c for c in result['changes'] if c['word'] == 'start')
check.true('the Works: "start"\'s chimney cue sits in the words band (warned)', start['cue']['inside_share'] < 0.6 and start['cue']['box'][3] < 0.22,
           details=json.dumps(start['cue']), recorded='safe_area.landmark_top_min_down (round 2-3: chimney tops at 0.07 to 0.14 down sat in the words band)',
           proves='projected with the core\'s sums: the smoke on "start" rises from the top 0.04 of W1\'s frame, under the words')
# planted faults
result, code = plan(works_plan, edit=lambda d: d['pages'][1]['changes'][0].update(time=59.0))
check.true('planted: "go" moved inside the slide is an error', code == 1 and any('falls inside the slide' in p['what'] for p in result['problems']),
           recorded='plan T9: a state changes only while the camera holds', proves='a planted fault')
result, code = plan(works_plan, edit=lambda d: d['pages'][1].update(behind_state='men gone'))
wrong = next((p for p in result['problems'] if 'behind picture comes from' in p['what']), None)
check.true('planted: a behind picture from "men gone" is an error naming the doorway that would light', wrong is not None and 'doorway_1' in wrong['fields'],
           details=wrong['what'] if wrong else 'none', recorded='round3-result.json pages: No. 1\'s doorway lit as soon as the slide started (the behind picture came from '
                                                                 'another state)', proves='round 3\'s fault, planted again')

# ------------------------------------------------------------------------------------------------ B. the real plates
w1_facts = f'{WORKING}/redesign/round5-set/state/w1-plate-facts/facts'
w2_facts = f'{WORKING}/redesign/round5-set/state/w2-plate-facts/facts'
if all(os.path.exists(p) for p in (f'{WORKS}/works-w1-plate.jpg', f'{WORKS}/works-w1-men-gone-plate.jpg', f'{WORKS}/works-w1-working-plate.jpg',
                                   f'{WORKS}/works-w1-behind-plate.jpg', w1_facts)):
    result, code = plan(works_plan, measure=True, plate_folder=WORKS, facts=[f'w1={w1_facts}', f'w2={w2_facts}'])
    changes = {c['word']: c for c in result['changes']}
    go, begin = changes['go'], changes['start']
    check.close('W1 "go": the share of the frame swapped', go['share'], 0.103, 0.003, recorded='round5-set/state/w1-men-gone.log: 10.3% (round 5)',
                proves='make_state_picture.py\'s own number on the same plates (a repeat; it checks the planner runs it the same way)')
    check.true('W1 "go" is a time cut on the word; "start" a stepped blend of 0.8 s in 3 steps', go['how'].startswith('time cut on "go"')
               and begin['how'].startswith('stepped blend') and '0.8 s in 3 steps' in begin['how'], details=f'{go["how"]}; {begin["how"]} ({begin["share"]:.1%})',
               recorded='page-3.js: a time cut on "go", steppedBlend(0.8 s, 3 steps) on "start"; skeptic: 0.12 separates the cuts (7-10%) from the blends (41-76%)',
               proves='the cut-or-blend choice matches the page; NOTE the core\'s state_pictures.cut_when_mask_share_max (0.10) would have made "go" (10.3%) a blend')
    w1 = next(b for b in result['behind_plates'] if b['view'] == 'w1')
    check.close('W1 behind plate: the share swapped', w1['measured']['mask_share'], 0.071, 0.003, recorded='round5-set/state/w1-behind.log: 7.1%',
                proves='a repeat of make_state_picture.py\'s number')
    check.true('W1: thresholds stay 6 and 3 with the measured noise', all(t['threshold'] == 6 and t['faint'] == 3 for t in result['thresholds'].values())
               and max(t['noise_levels'] for t in result['thresholds'].values()) <= 1.0, details=json.dumps(result['thresholds']),
               recorded='round 2: render noise 0.2 to 0.6 levels; round 5 logs 0.0 to 0.5', proves='max(6, 3 x noise) and max(3, 3 x smooth noise) from these plates')
    check.true('W1 "start" swaps over 15% of the frame and is warned', any('"start" swaps' in p['what'] for p in result['problems']),
               recorded='round 4 finding 15: the working state picture swapped 76% at "start", which will change a lot of brushwork once painted',
               proves='state_pictures.flag_mask_share (0.15) applied')
else:
    check.note(f'part B for the Works skipped: its plates or plate facts are not on this machine ({WHY_SKIPPED})')
people_plan = os.path.join(PAINTING, 'people-test-state-plan.json')
people_facts = f'{WORKING}/redesign/people-paint/plate-facts'
if os.path.exists(f'{PEOPLE}/people-test-plate.jpg') and os.path.exists(people_facts):
    result, code = plan(people_plan, measure=True, plate_folder=PEOPLE, facts=[f'still={people_facts}'])
    cut = result['changes'][0]
    check.close('people test: the share of the frame swapped', cut['share'], 0.423, 0.003, recorded='round3-fixes/state/people-test-state.log: 42.3%',
                proves='a repeat of make_state_picture.py\'s number')
    check.true('people test: the men\'s long shadows (5.6 times their outlines) are an error, and lesson 136\'s warning is given', code == 1
               and any('5.6 times the people' in p['what'] for p in result['problems']) and any('only people change' in p['what'] for p in result['problems']),
               details=cut['how'], recorded='round 2 and 3: 42% of the frame for people covering 7.5%; lesson 135; first-viewer check: the cut read as a glitch (lesson 136)',
               proves='the 3 times limit has this one bad case (Works round 5: 1.3 to 1.9), so the error is a repeat; the warning is decided from the state fields')
else:
    check.note(f'part B for the people test skipped: its plates or plate facts are not on this machine ({WHY_SKIPPED})')
shutil.rmtree(work, ignore_errors=True)
check.finish()
