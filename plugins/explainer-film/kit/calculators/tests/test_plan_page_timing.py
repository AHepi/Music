"""What this does: tests plan_page_timing.py on page events recorded from the project's own pages (no browser needed):
chapter 2 for newcomers, pages 3 to 5 (the Works, as filmed in round 4 on the estimated timeline), old chapter 2 (all ten
pages on Malina's real recording, shipped in log 20) with its page 10 as it was before the critique (git da5e861), and
the small made-up test chapter (paper-film/scenes/page-events-test.js) with and without its planted faults.
Each check names the number got, the number the project recorded and where, and says whether it proves something or
only repeats a sum. The fixtures are in tests/fixtures/page-timing (see sources.json there).
Run: python3 kit/calculators/tests/test_plan_page_timing.py
"""
import copy
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402
import plan_page_timing as timing  # noqa: E402
from settings import load_settings  # noqa: E402

HERE = os.path.join(FIXTURES, 'page-timing')
KIT = os.path.dirname(CALCULATORS)
SCENES = os.path.join(KIT, 'paper-film', 'scenes')
check = Checker('page timing: pauses, reading times, cuts, margins, words, numbers, stills')
settings = load_settings()


def events(name):
    return timing.Events(timing.load_json(os.path.join(HERE, name)))


def find(problems, check_name, text=None, page=None, verdict=None):
    return [p for p in problems if p['check'] == check_name and (text is None or (p['text'] or '') == text)
            and (page is None or p['page'] == page) and (verdict is None or p['verdict'] == verdict)]


works = events('events-pages-3-5.json.gz')
R4 = 'scratchpad redesign/round4-result.json'

# ---------------------------------------------------------------------------------------- the appear delays
delays = timing.read_appear_delays()
check.close('buildWords appear delay read from graphics.js', delays['buildWords'], 0.14, 1e-9, recorded='graphics.js buildWords presence(..., 0.14)',
            proves='the tool reads the delay from the drawing code itself (the skeptic: the design forgot buildWords\' 0.14 s)')
check.close('a label\'s usual wait (callout)', delays['callout'], 0.55, 1e-9, recorded='graphics.js callout: words 0.3 s after the line, over 0.25 s')
check.close('a label with wordsWithLine', delays['calloutWordsWithLine'], 0.12, 1e-9, recorded='graphics.js callout wordsWithLine (round 5)')
check.equal('the delays read from the file equal the ones the live page reported', {k: round(v, 6) for k, v in works.delays.items()}, delays,
            recorded='page_events.mjs appear_delays (graphics.js APPEAR_DELAYS, read in the browser)',
            proves='the Python reading of graphics.js and the running code agree (parity)')

# ---------------------------------------------------------------------------- MACHINES (round 4) and PRICES UP (round 3)
readable = timing.check_readable(works, settings)
machines = find(readable, 'readable', 'MACHINES', 3)
check.true('MACHINES fails the 1 s reading time', machines and machines[0]['verdict'] == 'fail', details=machines[0]['detail'] if machines else 'not found',
           recorded=f'{R4} critique.findings[7]; round 5 (words with the line: about 0.85-0.9 s)')
if machines:
    m = machines[0]
    check.close('MACHINES readable now (words in with the line), by the sum', m['readable_formula'], 0.85, 0.03,
                recorded='round 5 (log 34): about 0.85 s; skeptic 0.81 with 54.17 s',
                proves='the sum with graphics.js\'s 0.12 s; the timeline gives "machines" at 54.15 s')
    check.close('MACHINES readable now, counted frame by frame on the drawn opacity', m['readable_measured'], m['readable_formula'], 1.0 / 30 + 1e-6,
                proves='the frames the page really drew agree with the sum to within a frame')
    check.close('MACHINES with the usual 0.55 s wait (as round 4 filmed it)', m['readable_with_usual_wait'], 0.4, 0.06,
                recorded=f'{R4} critique.findings[7] (words start 54.60, full 54.70, cut 55.10: about 0.4 s); film.summary item 1 (about 0.45 s)',
                proves='graphics.js\'s 0.55 s wait matches what round 4 measured on the film (not the same sum)')
    check.true('the fix offered: start MACHINES on "and" (53.93 s), readable 1.05 s', '"and" (53.93 s): readable 1.05 s' in m['fix'], details=m['fix'],
               proves='the earlier-word search inside the sentence "all its workers, materials and machines"')
prices_up = find(readable, 'readable', '→ PRICES UP', 5)
check.true('→ PRICES UP on "prices" passes', prices_up and prices_up[0]['verdict'] == 'pass', details=prices_up[0]['detail'] if prices_up else '',
           recorded='round3-result.json checked.findings[4] (moved to "prices": about 1.2 s, full on the last frame); round 4 film "PRICES UP stays up about 1.2 seconds"')
if prices_up:
    check.close('→ PRICES UP readable at full strength', prices_up[0]['readable_formula'], 1.05, 0.01,
                recorded='skeptic (log 35): with the 0.14 s fade the 1.19 s is 1.05 s at full strength')
    check.close('→ PRICES UP up before the cut, counted from when it starts to appear', prices_up[0]['up_before_cut'], 1.19, 0.03,
                recorded='round 3 check: about 1.2 s (107.15 - 105.96)')
# round 3's version: the same words on "up" (106.48 s); the item is moved in a copy of the events (start, full strength,
# and its drawn frames shift together)
round3 = copy.deepcopy(works.data)
item = next(i for i in round3['items'] if i.get('text') == '→ PRICES UP')
shift = 106.485 - item['at']
frames = round(shift * 30)
item['at'] += shift
item['fullAt'] += shift
item['runs'] = [[a + frames, min(b, 3214)] for a, b in item['runs']]
item['track'] = [[p[0] + frames] + p[1:] for p in item['track'] if p[0] + frames <= 3214]
r3 = find(timing.check_readable(timing.Events(round3), settings), 'readable', '→ PRICES UP', 5)
r3_read = [p for p in r3 if 'readable' in p['detail'] and 'conclusion' not in p['detail']]
r3_up = [p for p in r3 if 'conclusion' in p['detail']]
check.true('round 3\'s → PRICES UP on "up" fails', bool(r3_read) and r3_read[0]['verdict'] == 'fail', details='; '.join(p['detail'] for p in r3))
if r3_read:
    check.close('round 3\'s → PRICES UP readable at full strength', r3_read[0]['readable_formula'], 0.53, 0.01, recorded='skeptic (log 35): 0.67 s less the 0.14 s fade')
if r3_up:
    check.close('round 3\'s → PRICES UP up before the cut (the cut counted at its first frame, 107.167 s)', r3_up[0]['up_before_cut'], 0.67, 1 / 30 + 1e-6,
                recorded='round3-result.json checked.findings[4]: about 0.65 s, last frame already faded; design (log 35): 107.15 - 106.48 = 0.67',
                proves='the conclusion rule fails what round 3 failed and passes what it passed (the rule\'s 1.2 s was set from these two cases)')
    check.true('the fix offered for round 3: start on "prices"', '"prices"' in r3_up[0]['fix'], details=r3_up[0]['fix'])

# ------------------------------------------------------------------------------------------------------ lookups
lookups = timing.check_lookups(timing.add_contexts(works.data['lookups'], works), settings, works.asked_pages)
ambiguous = sorted((p['page'], p['text']) for p in lookups if p['verdict'] == 'fail')
check.equal('lookups that leave out which time, pages 3-5', ambiguous,
            [(3, 'In'), (3, 'More'), (3, 'machines'), (3, 'workers'), (5, 'More'), (5, 'prices'), (5, 'spare'), (5, 'up')],
            recorded='page-3.js and page-5.js (each takes the first time, which is the one meant; nothing lists them today)',
            proves='every lookup the pages make is noted while they build, with every time the word is said')
static = timing.lookups_from_page_files(timing.load_json(os.path.join(HERE, 'timeline-estimated.json.gz')),
                                        [os.path.join(SCENES, 'inflation-chapter-2-newcomers', 'page-3.js') + ':3',
                                         os.path.join(SCENES, 'inflation-chapter-2-newcomers', 'page-5.js') + ':5'])
static_ambiguous = sorted((p['page'], p['text']) for p in timing.check_lookups(static, settings) if p['verdict'] == 'fail')
check.equal('the same lookups read from the page files without a browser', static_ambiguous, ambiguous, proves='the static reading and the noted one agree')
old_timeline = timing.load_json(os.path.join(KIT, 'examples', 'inflation-chapter-2', 'timeline.json'))
with tempfile.TemporaryDirectory() as folder:
    for page, word, lesson in ((2, 'war', 28), (3, 'machines', 46)):
        source = open(os.path.join(SCENES, 'inflation-chapter-2', f'page-{page}.js')).read()
        asked = f"kit.at('{word}', 2)"
        check.true(f'old chapter 2 page {page} asks for "{word}" with its time today', asked in source, recorded=f'lesson {lesson} (the fix)')
        before = os.path.join(folder, f'page-{page}.js')
        open(before, 'w').write(source.replace(asked, f"kit.at('{word}')"))
        found = [p for p in timing.check_lookups(timing.lookups_from_page_files(old_timeline, [f'{before}:{page}']), settings)
                 if p['verdict'] == 'fail' and p['text'] == word]
        check.true(f'without its time, "{word}" (lesson {lesson}) is caught on Malina\'s real recording', bool(found) and len(found[0]['said']) >= 2,
                   details=found[0]['detail'] if found else 'not caught', recorded=f'Lessons.md lesson {lesson}; examples/inflation-chapter-2/timeline.json',
                   proves='the recorded fault is caught on the real narration (the page file with the fix taken out)')

# ------------------------------------------------------------------------------------------------- pauses and joins
pause_problems, gaps = timing.check_pauses(works, settings)
by_page = {g['page']: g for g in gaps}
check.close('pause after page 3 (a plain peel: 0.3 + 0.85 + 0.15)', by_page[3]['recommended'], 1.30, 1e-6, recorded='cinema-chapter.js DEFAULT_JOIN; skeptic settle 0.15',
            proves='only repeats the sum; the timeline has 1.5 (estimate_timeline\'s default)')
check.close('pause after page 4 (run-on in the 4 s guess hold)', by_page[4]['recommended'], 4.0, 1e-6, recorded='timeline-estimated.json pauses_after_page 4 = 4.0; plan 34 "4-second guess hold"',
            proves='the hold is kept: the design\'s clamp would have cut it to 1.7 (skeptic)')
check.close('pause after page 5 (peel after the 2 s rule hold)', by_page[5]['recommended'], 3.0, 1e-6, recorded='page-5.js join after 2.0, 0.85 long; the timeline has 3.5',
            proves='the formula needs 3.0 s; the timeline\'s 3.5 is reported as 0.5 s longer than needed (information)')
check.true('the pauses after pages 4 and 5 are not clamped to 1.7', by_page[4]['recommended'] > 1.7 and by_page[5]['recommended'] > 1.7)
check.true('no join ends less than 0.1 s before the next first word on pages 3-5', not find(pause_problems, 'pauses', verdict='fail'))
check.true('page 4 into 5 is a run-on into the same view, which passes', find(pause_problems, 'joins', 'page 4 -> 5 join', verdict='pass'),
           recorded='page-4.js join run-on; round 4 film: "the run-on from page 4 into 5 ... show no jump"')

# --------------------------------------------------------------------------------------------- fades at cuts
fades = timing.check_fades_at_cuts(works, settings)
check.equal('words ending on the two cuts, all whole until the cut (fadeOut 0)', (len(fades), len(find(fades, 'fade at cut', verdict='fail'))), (10, 0),
            recorded='round4-result.json pageFixes (fadeOut 0); round 4 film: "the frame before each cut changes only as much as an ordinary frame"')
round3_fade = copy.deepcopy(works.data)
for i in round3_fade['items']:
    if i.get('text') == 'PICTURE TWO FACTORIES':
        i['fadeOut'] = 0.3
check.true('with round 3\'s fade (0.3 s) the same words fail', find(timing.check_fades_at_cuts(timing.Events(round3_fade), settings), 'fade at cut', 'PICTURE TWO FACTORIES', verdict='fail'),
           recorded='round3-result.json checked.findings[16] (change 2.7 against 0.5 in the frame before each cut)', proves='only that the rule reads fadeOut')

# ------------------------------------------------------------------------------------------------------ margins
margins = timing.check_margins(works, settings)
check.true('no margin fails on pages 3-5', not find(margins, 'margins', verdict='fail'), recorded='round 4 film: every line inside 0.90; heading 0.061 down')
info = {p['page']: p for p in find(margins, 'margins', verdict='info')}
check.close('page 5: the highest letters (MOST ECONOMISTS AGREE) start 0.061 down', info[5]['top_down'], 0.061, 0.001,
            recorded=f'{R4} film.summary ("MOST ECONOMISTS AGREE starts 0.061 down"); round4-result.json stills: 0.0609')
check.close('pages 4-5: the longest line ends 0.897 across (WHAT HAPPENS TO PRICES?)', info[4]['right_across'], 0.895, 0.004,
            recorded='round 4 film still 93.00 s, measured: 967 px = 0.895 (round 4\'s own note "every line ends by 0.86" missed this line)',
            proves='the font-measured box agrees with the filmed pixels (hold-out: the stills were drawn by the film tool, not by this sum)')
edges = json.load(open(os.path.join(HERE, 'round4-film-text-edges.json')))
items = {i['text']: i for i in works.items if i['kind'] == 'words' and not works.carried(i)}
worst = 0
for line in edges['lines']:
    box = works.boxes(items[line['text']])[0]
    worst = max(worst, abs(box[0] - line['left']), abs(box[2] - line['right']), abs(box[1] - line['top']))
check.within('6 typed lines: font-measured boxes against the round 4 film stills, largest difference in pixels', worst, 0, 4,
             recorded='fixtures/page-timing/round4-film-text-edges.json (measured on round4-film/stills)', proves='hold-out: no rendering was used for the boxes')

# ------------------------------------------------------------------------------------------ typed words and numbers
typed, counted, digits = timing.check_typed_words(works, settings)
check.equal('typed lines on pages 3-5: new, and carried over from page 4 by the run-on', (counted['new'], counted['carried']), (29, 2),
            recorded='round4-film/words-check.txt and round 4 film.summary ("All 29 typed lines")')
check.equal('typed words not said on their page (round 4: 0 problems)', len(find(typed, 'typed words', verdict='fail')), 0, recorded='round4-film/words-check.txt "0 problem(s)"')
check.equal('digits on screen, pages 3-5', digits, [], recorded='round 4 film.summary ("No typed digits")')
old = events('events-old-chapter-2.json.gz')
ledger = json.load(open(os.path.join(HERE, 'old-chapter-2-ledger.json')))
numbers = timing.check_numbers(old, settings, ledger)
claims = [p for p in numbers if p.get('ledger')]
check.true('old chapter 2: every number on screen matches the fact-checked ledger within rounding, with its qualifier',
           claims and all(p['verdict'] == 'pass' for p in claims), details=f'{len(claims)} numbers; ' + '; '.join(p['detail'] for p in claims if p['verdict'] != 'pass'),
           recorded='chapter-2-inflation/fact-recheck-2026-10-12.json; Decisions.md 330-337', proves='only that the shipped screen agrees with a ledger built from the same check')
reversed_fix = copy.deepcopy(old.data)
for i in reversed_fix['items']:
    if i.get('text') == 'UP TO +25%':
        i['text'] = '+25%'
undone = [p for p in timing.check_numbers(timing.Events(reversed_fix), settings, ledger) if p['text'] == '+25%']
check.true('with decision 21\'s fix undone (+25% without UP TO), the number fails', undone and undone[0]['verdict'] == 'fail', details=undone[0]['detail'] if undone else '',
           recorded='Decisions.md item 21: "Changed on screen: UP TO +25% (Glasgow)"', proves='the qualifier rule catches the fault the checkers fixed')
after = {p['text']: p for p in numbers if p['check'] == 'numbers' and p.get('held') is not None}
before_events = events('events-old-ch2-page10-before-critique.json.gz')
before = {p['text']: p for p in timing.check_numbers(before_events, settings, None) if p.get('held') is not None}
check.true('old page 10 before the critique: 5.6% fails (held still about 0 s after it lands)', before.get('5.6%', {}).get('verdict') == 'fail',
           details=before.get('5.6%', {}).get('detail', 'not found'), recorded='Lessons.md lesson 53 ("a key figure still counting while said"); git da5e861 page-10.js',
           proves='the recorded fault is caught on the page as it was (run in the stage), on the real recording')
check.true('old page 10 after the fix: 5.6% lands as she says "five point six" and holds', after.get('5.6%', {}).get('verdict') == 'pass',
           details=after.get('5.6%', {}).get('detail', 'not found'), recorded='page-10.js now: "the count lands on 5.6 as she says five, then holds still"; log 19')
check.close('old page 10 after the fix: seconds 5.6% holds still', after.get('5.6%', {}).get('held'), 1.35, 0.05, proves='measured from the drawn frames')

# --------------------------------------------------------------------------------------- groups, slides, frozen
groups = {p['page']: p for p in timing.check_word_groups(works, settings) if p['page']}
check.equal('word groups on pages 3, 4, 5 against their limits', [(groups[n]['groups'], groups[n]['limit']) for n in (3, 4, 5)], [(8, 8), (5, 5), (7, 7)],
            recorded='plan 34 (3 to 5 a page, more for figures and named placements)', proves='judged rule; only repeats plan 34\'s counting')
slides = find(timing.check_slides(works, settings), 'slides', verdict='pass')
check.equal('slides start and stop on words 2.6-4.1 s apart', sorted(round(p['seconds'], 2) for p in slides), [2.89, 3.07],
            recorded='plan 34 (W1 "Workers" to "Call", W2 "No" to "factory"); round 4 film: both slides land on their words')
check.true('nothing is frozen while she speaks on pages 3-5 (live smoke and flicker)', not find(timing.check_frozen(works, settings), 'frozen', verdict='fail'))

# ------------------------------------------------------------------------------- still lists and planned cuts
stills = timing.still_list(works, settings)
moments = json.load(open(os.path.join(HERE, 'round4-moments.json')))
hand = []
for key, note in moments.items():
    seconds = int(key[1:]) / 30 if key.startswith('f') else float(key)
    tied = any(word in note for word in ('"', 'cut', 'slide', 'turn', 'frame', 'step', 'page'))
    hand.append((seconds, tied, note))
near = lambda s: min(abs(s - x['t']) for x in stills)
tied = [h for h in hand if h[1]]
covered = [h for h in tied if near(h[0]) <= 0.35]
check.true(f'the automatic still list ({len(stills)} stills) covers the round 4 helpers\' moments tied to an event, within 0.35 s',
           len(covered) >= 0.9 * len(tied), details=f'{len(covered)} of {len(tied)} event moments; all moments: {sum(1 for h in hand if near(h[0]) <= 0.35)} of {len(hand)}; '
           f'missed: {"; ".join(h[2] for h in tied if near(h[0]) > 0.35)}',
           recorded='round4-film/moments.json (74 moments picked by hand)', proves='hold-out: the round 4 helpers chose these by hand; pass mark 90% (judged)')
jumps = open(os.path.join(HERE, 'round4-film-jumps.txt')).read()
measured = sorted({float(x) for x in re.findall(r'planned cut into frame \d+ \([\d.]+ s\): change [\d.]+, around it [\d.]+\s+\[chapter ([\d.]+) s\]', jumps)})
planned = [c['t'] for c in timing.planned_cuts(works, 47.3667) if not c.get('gradual')]
matched = [m for m in measured if any(abs(m - p) <= 1.5 / 30 for p in planned)]
check.equal('every jump find_jumps.py measured on the round 4 film is a planned cut from the page events', (len(matched), len(measured)), (6, 6),
            recorded='round4-film/jumps/report.txt (55.10, 67.27, 68.77, 69.04, 69.30, 107.17 s)',
            proves='hold-out: those were measured on the filmed pixels; these come from the page code without drawing')
first = next(c for c in timing.planned_cuts(works, 47.3667) if abs(c['t'] - 55.1) < 0.05)
check.close('the cut to W1 in the first round 4 piece\'s own seconds', first['film_seconds'], 7.73, 0.01, recorded='round4-film/jumps/report.txt: "planned cut into frame 232 (7.73 s)"')

# ------------------------------------------------------------------------------------------------- re-filming
with tempfile.TemporaryDirectory() as folder:
    estimated = timing.load_json(os.path.join(HERE, 'timeline-estimated.json.gz'))
    chunks = os.path.join(folder, 'chunks.txt')
    names = ['chunk-01421-to-01699', 'chunk-01699-to-01976', 'chunk-01976-to-02254', 'chunk-02254-to-02457', 'chunk-02457-to-02661',
             'chunk-02661-to-02864', 'chunk-02864-to-03074', 'chunk-03074-to-03284', 'chunk-03284-to-03494', 'chunk-03494-to-03704']
    open(chunks, 'w').write('\n'.join(n + '.mp4' for n in names))
    longer = copy.deepcopy(estimated)
    for page in longer['pages']:
        if page['page'] >= 4:
            for w in page['words']:
                w['start'] += 0.5
                w['end'] += 0.5
            page['first_word_at'] += 0.5
            page['last_word_end_at'] += 0.5
    old_path, new_path = os.path.join(folder, 'old.json'), os.path.join(folder, 'new.json')
    json.dump(estimated, open(old_path, 'w'))
    json.dump(longer, open(new_path, 'w'))
    args = type('A', (), {'old_timeline': old_path, 'new_timeline': new_path, 'chunks': chunks, 'fps': 30})
    result, _ = timing.run_refilm(args, settings)
    check.equal('page 4 re-recorded 0.5 s longer, everything after it moved: chunks to film again', [r['chunk'] for r in result['refilm']], [n + '.mp4' for n in names[2:]],
                recorded='round 4 chunk list (round4-film/film/chunks)', proves='self-consistency only: the pages\' frame windows against the chunk ranges')
    absorbed = copy.deepcopy(estimated)
    page4 = next(p for p in absorbed['pages'] if p['page'] == 4)
    for w in page4['words']:
        w['start'] += 0.25
        w['end'] += 0.25
    page4['first_word_at'] += 0.25
    page4['last_word_end_at'] += 0.25
    json.dump(absorbed, open(new_path, 'w'))
    result, _ = timing.run_refilm(args, settings)
    check.equal('page 4 re-recorded, the pauses absorb it: only the chunks page 4 and its run-on join are drawn in', [r['chunk'] for r in result['refilm']],
                [n + '.mp4' for n in names[2:7]],
                proves='self-consistency only (chunk 02864-03074 is in: the run-on join into page 5 moves 0.25 s with page 4, frames 2865-2871)')

# ------------------------------------------------------------------- the test chapter: clean, and with its faults
clean = timing.Events(timing.load_json(os.path.join(HERE, 'events-test-clean.json.gz')))
faults = timing.Events(timing.load_json(os.path.join(HERE, 'events-test-faults.json.gz')))
test_ledger = json.load(open(os.path.join(HERE, 'page-events-test-ledger.json')))


def every_check(ev):
    out = timing.check_lookups(ev.data['lookups'], settings) + timing.check_pauses(ev, settings)[0] + timing.check_readable(ev, settings)
    out += timing.check_fades_at_cuts(ev, settings) + timing.check_same_place(ev, settings) + timing.check_margins(ev, settings)
    out += timing.check_typed_words(ev, settings)[0] + timing.check_numbers(ev, settings, test_ledger)
    return out


clean_problems = every_check(clean)
check.equal('the clean test chapter: nothing to fix', [p['detail'] for p in clean_problems if p['verdict'] == 'fail'], [])
fault_problems = [p for p in every_check(faults) if p['verdict'] == 'fail']
planted = {
    'a word said three times without its time': find(fault_problems, 'lookups', 'prices'),
    'a line drawn over a fading one': find(fault_problems, 'same place'),
    'letters 0.047 down': [p for p in find(fault_problems, 'margins', 'MOST PEOPLE AGREE') if '0.047' in p['detail']],
    'a line past 0.90 across': [p for p in find(fault_problems, 'margins') if 'across' in p['detail']],
    'words fading a frame before a cut': find(fault_problems, 'fade at cut', '→ PRICES GO UP AND THE PRICES STAY UP'),
    'a label readable under a second': find(fault_problems, 'readable', 'PRICES'),
    'a run-on join into another view': find(fault_problems, 'joins'),
    'a count landing after its number': [p for p in find(fault_problems, 'numbers', '4%') if 'lands' in p['detail']],
    'a figure dropping the ledger\'s "about"': [p for p in find(fault_problems, 'numbers', '4%') if 'about' in p['detail']],
}
check.equal('the planted faults each caught', {k: bool(v) for k, v in planted.items()}, {k: True for k in planted},
            recorded='paper-film/scenes/page-events-test.js ?variant=faults', proves='each rule fires on its planted case (plants, not recorded cases)')

# ------------------------------------------------------------------------------------- the command line and accepted
with tempfile.TemporaryDirectory() as folder:
    accepted = os.path.join(folder, 'accepted.json')
    json.dump([{'check': 'readable', 'page': 3, 'text': 'MACHINES', 'reason': 'kept at about 0.85 s', 'who': 'test', 'date': '2026-10-16'},
               {'check': 'lookups', 'text': ''}], open(accepted, 'w'))
    run = subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'plan_page_timing.py'), 'check', os.path.join(HERE, 'events-pages-3-5.json.gz'),
                          '--accepted', accepted, '--film-start', '47.3667', '--json'], capture_output=True, text=True, timeout=120)
    result = json.loads(run.stdout) if run.stdout.strip().startswith('{') else {}
    check.true('with MACHINES and the lookups accepted, pages 3-5 have nothing to fix (exit 0)', run.returncode == 0 and result.get('verdicts', {}).get('fail') == 0,
               details=f'exit {run.returncode}, {result.get("verdicts")}, known {result.get("verdicts", {}).get("known")} ' + run.stderr[-300:])
    check.true('the JSON names the settings it used', 'page_timing.settle_after_join_seconds' in result.get('settings_used', {}))
    check.true('the stills command is space-separated (lesson 50)', ',' not in result.get('stills', {}).get('command', ',').split('--stills')[1])
    plain_run = subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'plan_page_timing.py'), 'check', os.path.join(HERE, 'events-pages-3-5.json.gz')],
                               capture_output=True, text=True, timeout=120)
    check.equal('without the accepted list it exits 1 (MACHINES and 8 lookups to fix)', plain_run.returncode, 1)
    check.true('the plain report lists the settings used', 'Settings used (film-settings.json):' in plain_run.stdout)
check.finish()
