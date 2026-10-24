"""What this does: tests plan_budget.py on the project's own records: the three filmings of chapter 2's pages 3 to 5 (rounds
3, 4 and 5: the same 2,283 frames on three different sets and machine loads; their logs are in fixtures/budget), the page
events of those pages (fixtures/page-timing/events-pages-3-5.json.gz), the people test's paintings ledger, the two
chapter 2 narration scripts and a spend ledger transcribed from the logs. Each check names the number got, the number
recorded and where, and says whether it proves something or only repeats a sum.
The fair checks of filming time are:
  - leave one chunk out: each chunk's time predicted from rates fitted on the OTHER chunks only (never on itself);
  - a profile: rates from 8 short stretches (one held stretch per view, the stretch with most of each slide, one piece's
    loading: 480 of the 2,283 frames), as profile-commands would film before planning, predicting all 2,283 frames;
  - the table (round 4's numbers) predicting rounds 3 and 5, which it was not measured on.
Run: python3 kit/calculators/tests/test_plan_budget.py
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402
import plan_budget as budget  # noqa: E402
from settings import load_settings, Settings  # noqa: E402

check = Checker('budget planner: money, filming time, pieces, stretches, memory, disk, pushes')
settings = load_settings()
HERE = os.path.join(FIXTURES, 'budget')
EVENTS = os.path.join(FIXTURES, 'page-timing', 'events-pages-3-5.json.gz')
KIT = os.path.dirname(CALCULATORS)
events = budget.load_json(EVENTS)
classified = budget.classify_frames(events)
FIRST, LAST = 1421, 3704
mix, by_view = budget.frame_mix(classified, FIRST, LAST)
logs = {r: budget.read_logs([os.path.join(HERE, f'round{r}-filming-logs.txt')]) for r in (3, 4, 5)}
measured = {r: sum(logs[r]['chunks'].values()) for r in logs}
JOIN = settings.value('filming.peel_frames_cost_factor')

# 1. frame kinds from the page events, against the hand-made list of round 4's frame_times.py
check.equal('pages 3-5 hold 2,283 frames (1421 to 3703)', sum(mix.values()), 2283,
            recorded='round4-result.json film.summary (2,283 frames)', proves='the events cover exactly the frames filmed')
w1 = by_view['3b the quiet gate']['moving']
w2 = by_view['4a the flat-out gate']['moving']
check.within('the W1 slide found from the camera moving: frames', w1, 90, 94,
             recorded='round4-film/tools/frame_times.py KINDS: sliding (W1) 57.932-60.998 s = 92 frames',
             proves='frames are classed from the page events alone, matching a list a helper made by hand')
check.within('the W2 slide: frames', w2, 85, 89, recorded='frame_times.py KINDS: sliding (W2) 81.979-84.872 s = 87 frames',
             proves='as above')
check.within('page-turn frames (two pages drawn)', mix['join'], 50, 58,
             recorded='frame_times.py KINDS: two page peels of 0.85 s (25.5 frames each) plus the page 4-5 run-on',
             proves='joins are found from the events')

# 2. the chunks film-chapter-parallel.sh makes, rebuilt from the events' page edges
info = budget.scene_info(events)
chunks = [c for c in budget.chunk_list(info, 240) if c[0] >= FIRST and c[1] <= LAST]
check.equal('chunks of 240 frames over pages 3-5 are the ones round 4 filmed', chunks, sorted(logs[4]['chunks']),
            recorded='round4-film/film/filming.log (frames 1421-1699, 1699-1976, ... 3494-3704)',
            proves='FILM_FROM/FILM_TO stretches land on the same chunk edges the filming script uses')

# 3. leave one chunk out: rates from the other chunks only
for r, recorded in ((3, 'round3-pages/film filming.log: 70 minutes (4,188 s)'), (4, 'round4-film/film/filming.log: 53 minutes (3,166 s)'),
                    (5, 'round5-film/film/filming.log: 110 minutes (6,580 s), other helpers running Blender at the same time')):
    result = budget.measure_rates(logs[r], classified, settings, leave_out=True)['leave_one_chunk_out']
    check.within(f'round {r}: each chunk predicted from the other chunks, summed (error share)', result['error_share'], -0.03, 0.03,
                 recorded=recorded, proves='the frame kinds plus one load a piece explain the filming time; no chunk sees its own timing')
    check.note(f'round {r}: {result["predicted_seconds"]:.0f} s predicted against {result["measured_seconds"]:.0f} s; the worst single chunk is off '
               f'by {result["largest_chunk_error_share"] * 100:.0f}% (the chunk holding a slide loses that view\'s only slide data when left out)')

# 4. a profile: one held stretch per view, the stretch with most of each slide, one piece's loading
def profile_rows(log):
    rows, seen, frames = [], set(), 0
    stretches = [st for p in log['pieces'] for st in p['stretches']]
    for a, b, seconds, first in stretches:
        kinds = {(c['kind'], c['view']) for c in classified if a <= c['frame'] < b}
        if not first and len(kinds) == 1:
            kind, view = next(iter(kinds))
            if kind == 'held_live' and view not in seen:
                seen.add(view)
                rows.append((None, budget.counts_for(classified, a, b, JOIN), 0, seconds))
                frames += b - a
    for view in [v for v, c in by_view.items() if c['moving']]:
        def moving_in(st):
            return sum(1 for c in classified if st[0] <= c['frame'] < st[1] and c['kind'] == 'moving' and c['view'] == view)
        a, b, seconds, first = max(stretches, key=lambda st: (moving_in(st), not st[3]))
        rows.append((None, budget.counts_for(classified, a, b, JOIN), 1 if first else 0, seconds))
        frames += b - a
    a, b, seconds, first = log['pieces'][0]['stretches'][0]
    rows.append((None, budget.counts_for(classified, a, b, JOIN), 1, seconds))
    return rows, frames + (b - a)


table = budget.table_rates(settings)
moving_views = budget.moving_counts(by_view)
pieces = sum(len(budget.pieces_of(a, b, 240)) for a, b in chunks)
check.equal('pieces of 240 frames in those chunks', pieces, sum(1 for _ in logs[4]['pieces']), recorded='round 4 chunk logs (13 pieces)',
            proves='the piece count (one page load each) is worked out the way film-chapter-parallel.sh cuts them')
for r in (3, 4, 5):
    rows, frames_used = profile_rows(logs[r])
    rates = budget.fit_rates(rows, JOIN)
    predicted = budget.predict_seconds(mix, pieces, rates, 1.0, moving_views)
    share = predicted / measured[r] - 1
    check.within(f'round {r}: planned from a profile of {len(rows)} stretches ({frames_used} of 2,283 frames), error share', share, -0.08, 0.04,
                 recorded=f'round {r} filming.log total {measured[r]:.0f} s',
                 proves='a few minutes of profiling per film predicts the whole filming (partly in-sample: the profile frames are part of the total)')
    check.note(f'round {r} profile: held {rates["seconds_per_frame"]["held_live"]:.2f} s, slides '
               + ', '.join(f'{v} {s:.2f} s' for v, s in rates['moving_by_view'].items()) + f', loading {rates["seconds_loading_a_piece"]:.0f} s; '
               f'{predicted / 60:.1f} min against {measured[r] / 60:.1f} min')
    table_share = budget.predict_seconds(mix, pieces, table, 1.0, moving_views) / measured[r] - 1
    if r == 4:
        check.within('round 4 from the table (0.9 / 4.3 / 34 s): error share', table_share, -0.03, 0.03, recorded='round 4 filming.log 3,166 s',
                     proves='only repeats: the table was measured on this very filming')
    else:
        check.true(f'round {r} from the round 4 table is off by more than 20% ({table_share * 100:+.0f}%)', abs(table_share) > 0.20,
                   recorded=f'round {r} filming.log {measured[r]:.0f} s',
                   proves='the table alone misleads on another set or a busy machine, which is why the planner profiles first')

pieces_to_profile = budget.profile_stretches(classified)
views = {c['view'] for c in classified if FIRST <= c['frame'] < LAST and c['kind'] != 'join'}
clean = []
for piece in pieces_to_profile:
    a, b = piece['measured']
    kinds = {(c['kind'], c['view']) for c in classified if a <= c['frame'] < b}
    clean.append(len(kinds) == 1 and next(iter(kinds))[0] == ('moving' if piece['why'].startswith('moving') else 'held_live'))
check.true(f'profile-commands: {len(pieces_to_profile)} pieces of 120 frames, one held per view and one per slide, each timed stretch all of one kind',
           len([p for p in pieces_to_profile if p['why'].startswith('held')]) == len(views) and len([p for p in pieces_to_profile if p['why'].startswith('moving')]) == 2
           and all(p['last'] - p['first'] == 120 for p in pieces_to_profile) and all(clean),
           details='; '.join(f'{p["why"]} {p["first"]}-{p["last"]}' for p in pieces_to_profile),
           proves='the profile measures each view\'s held cost and each slide clean of loading (as the fair check above does with round logs)')

# 5. the filming plan: pieces, stretches, commands, workers, memory, lazy loading
rates4 = budget.measure_rates(logs[4], classified, settings)['rates']
plan = budget.plan_filming(events, settings, 'inflation-chapter-2-newcomers', rates4, FIRST, LAST, processors=1, free_memory=15.0,
                           blender=[], free_disk=50.0)
lazy_example = budget.piece_frames_for(40, 1.6, settings)[0]
check.within('a lazy chapter (loading 40 s, 1.6 s a frame): piece frames', lazy_example, 240, 260,
             recorded='Plan 34 lines 1212-1221 and Workflows.md: PIECE_FRAMES 240 for lazy chapters (pieces of 240 to 300 frames)',
             proves='repeats the design\'s own example: the rule gives the size the project chose by judgement')
check.note(f'with round 4\'s measured rates (loading {rates4["seconds_loading_a_piece"]:.0f} s, {plan["steady_seconds_a_frame"]:.2f} s a frame) the '
           f'rule asks for pieces of {plan["piece_frames"]} frames: {plan["pieces"]} loads for pages 3-5 instead of round 4\'s 13 (the 10% loading '
           f'share is invented, not tested by filming)')
check.within('pages 3-5 with round 4\'s rates, one worker: minutes', plan['predicted_seconds'] / 60, 48, 56, recorded='round 4: 53 minutes',
             proves='only partly: these rates were fitted on round 4 itself (bigger pieces, so fewer loads, than round 4 used)')
check.equal('one stretch is enough for 53 minutes', len(plan['stretches']), 1, proves='the stretch rule (each under 1 h 50 min)')
paper = budget.piece_frames_for(2, settings.value('filming.seconds_per_frame_paper'), settings)[0]
check.equal('paper pages (loading about 2 s, 0.85 s a frame): pieces', paper, 60, recorded='film-chapter-parallel.sh PIECE_FRAMES 60 for paper pages',
            proves='repeats the design\'s rule on its own example')
model_pages, why = budget.piece_frames_for(30, 12, settings)
check.equal('model pages at 12 s a frame: pieces', model_pages, 60, recorded='lesson 71 (60-frame pieces; at most about 13 minutes lost)',
            proves='repeats the design\'s rule; 60 frames x 12 s = 12 minutes lost at most')
short = Settings(json.loads(json.dumps(settings.data)), settings.path)
short.data['filming']['stretch_max_hours']['value'] = 0.5
plan_short = budget.plan_filming(events, short, 'inflation-chapter-2-newcomers', rates4, FIRST, LAST, processors=1, free_memory=15.0,
                                 blender=[], free_disk=50.0)
limit = plan_short['stretch_limit_seconds']
edges_ok = all(a['to'] == b['from'] for a, b in zip(plan_short['stretches'], plan_short['stretches'][1:]))
check.true(f'with 30-minute jobs the plan splits into {len(plan_short["stretches"])} stretches, each under {limit / 60:.0f} min, end to end',
           len(plan_short['stretches']) >= 3 and all(s['seconds'] <= limit for s in plan_short['stretches']) and edges_ok
           and plan_short['stretches'][0]['from'] == FIRST and plan_short['stretches'][-1]['to'] == LAST,
           details='; '.join(f'{s["from"]}-{s["to"]} {s["seconds"] / 60:.1f} min' for s in plan_short['stretches']),
           proves='stretches never pass the job limit and leave no gap (a test of the splitting, with a made-up 30-minute limit)')
check.true('each stretch prints a FILM_FROM/FILM_TO command', all(s['command'].startswith(f'FILM_FROM={s["from"]} FILM_TO={s["to"]} ')
                                                                   and 'film-chapter-parallel.sh inflation-chapter-2-newcomers' in s['command']
                                                                   for s in plan_short['stretches']))
two = budget.plan_filming(events, settings, 's', rates4, FIRST, LAST, processors=2, free_memory=15.0, blender=[], free_disk=50.0)
four = budget.plan_filming(events, settings, 's', rates4, FIRST, LAST, processors=4, free_memory=15.0, blender=[], free_disk=50.0)
check.equal('workers on 2 and 4 processors', [two['workers'], four['workers']], [1, 2], recorded='lesson 34; Workflows traps (1.44 against 1.68 s a frame)',
            proves='repeats the rule')
tight = budget.plan_filming(events, settings, 's', rates4, FIRST, LAST, processors=4, free_memory=6.0, blender=[], free_disk=50.0)
none_ = budget.plan_filming(events, settings, 's', rates4, FIRST, LAST, processors=4, free_memory=4.0, blender=[], free_disk=50.0)
check.true('6 GB free allows one worker; 4 GB free stops the plan', tight['workers'] == 1 and not tight['problems'] and none_['problems'],
           details=f'{tight["workers"]} worker; {none_["problems"][:1]}', recorded='Plan 34 F1 (about 2.6-2.8 GB a piece, 16 GB machine, no swap)',
           proves='made-up memory figures: the memory rule is applied')
lazy = budget.plan_filming(events, settings, 's', rates4, FIRST, LAST, processors=4, free_memory=15.0, heavy_pages=16, blender=[], free_disk=50.0)
small = budget.plan_filming(events, settings, 's', rates4, FIRST, LAST, processors=4, free_memory=15.0, heavy_pages=1, blender=[], free_disk=50.0)
check.true('16 heavy pages turn lazy loading on (about 45 GB at once); one does not', lazy['lazy'] and not small['lazy'],
           details=lazy['lazy_reasons'][0][:100] if lazy['lazy_reasons'] else 'not lazy',
           recorded='log 34 (16 heavy pages ran the 16 GB machine out of memory; a loaded set about 2.6-2.8 GB, measured)',
           proves='the log 34 case follows from the measured memory a set takes')
busy = budget.plan_filming(events, settings, 's', rates4, FIRST, LAST, processors=4, free_memory=15.0, blender=[4242], free_disk=50.0)
check.true('a running Blender stops the plan', any('Blender is running' in p for p in busy['problems']),
           recorded='round 5 filmed the same frames in 110 min against 53 while other helpers ran Blender', proves='the check fires')

# 6. disk: megabytes a second of filmed film
film_rate = settings.value('filming.film_with_grain_megabytes_per_second')
for name, megabytes, seconds in (('old chapter 2 master', 945.602002, 270.333), ('round 4 pages 3-5', 294.889644, 76.1),
                                 ('round 5 pages 3-5 (chunks)', 278.225531, 76.1)):
    check.within(f'{name}: {megabytes / seconds:.2f} MB a second against the table\'s {film_rate}', megabytes / seconds / film_rate, 0.8, 1.15,
                 recorded=f'file sizes read on 2026-10-16 ({megabytes:.0f} MB, {seconds} s)',
                 proves='the disk rate holds on films it was not measured on (the Works pages run about 10% over it)')
need = budget.disk_needed(settings, 406.9)
check.within('a 407 s chapter on disk (film and pieces): GB', need['total_gb'], 2.5, 3.2, recorded='Plan 34 F2: one chapter copy 1.4-1.6 GB',
             proves='repeats 407 s x 3.5 MB x 2 copies')

# 7. money: every money check repeats a rate (no bill exists to check against)
people_ledger = budget.load_json(os.path.join(FIXTURES, 'people-test', 'people-test-paintings.json'))
unsized = budget.cost_plan(people_ledger, settings)
check.true('a picture sent without a size is flagged, not priced as free', any('no size' in row.get('note', '') for row in unsized['lines']),
           details='; '.join(f'{row["what"]}: {row.get("note") or "sized"}' for row in unsized['lines'] if 'cents_each' in row),
           recorded='people-test-paintings.json: the behind painting was sent "people-test-painting.png (lined up)", no size written',
           proves='the trap of log 32 (pictures sent are charged too) cannot pass silently')
people_ledger['paintings'][1]['images_sent'] = ['people-test-painting.png (lined up, resized to the plate: 1536 x 2730)']
people = budget.cost_plan(people_ledger, settings)
check.close('the people test\'s two paintings at 4.8 c a megapixel, the lined-up painting at plate size: cents', people['paintings_dollars'] * 100, 83.9, 0.2,
            recorded='people-test-paintings.json note (about 85 c for the two; the plate size is in the same note)',
            proves='only repeats: the 85 c came from the same rate')
for name, script, credits, where in (('old chapter 2', 'old-chapter-2-narration-script.json', 4300, 'Status.md (about 4,300 credits)'),
                                     ('newcomer chapter 2', 'newcomer-narration-script.json', 6300, 'Status.md (about 6,300 credits, about US$1.10)')):
    cost = budget.cost_plan({'narration_scripts': [os.path.join(FIXTURES, 'script', script)], 'rerecord_pages': 0}, settings)
    check.close(f'{name}: credits from the letters sent, cue included', cost['narration_credits'], credits, 60, recorded=where,
                proves='only repeats: the logs also counted credits by text length (no bill)')
newcomer = budget.cost_plan({'narration_scripts': [os.path.join(FIXTURES, 'script', 'newcomer-narration-script.json')], 'rerecord_pages': 0}, settings)
check.close('newcomer narration in dollars', newcomer['narration_dollars'], 1.10, 0.02, recorded='Status.md (about US$1.10)', proves='only repeats the rate')
plan_with_sent = budget.cost_plan({'paintings': [{'name': 'W1 plate', 'returned': [1504, 2672], 'sent': [[1536, 2730], [768, 1368]]},
                                                 {'name': 'no style picture', 'returned': [1504, 2672], 'sent': [[1536, 2730]]}]}, settings)
rows = plan_with_sent['lines']
check.true('a painting is priced on the pictures sent as well as the one returned (44.5 c with a style picture, 39.4 c without)',
           abs(rows[0]['cents_each'] - 44.5) < 0.1 and abs(rows[1]['cents_each'] - 39.4) < 0.1,
           details=f'{rows[0]["cents_each"]} c and {rows[1]["cents_each"]} c',
           recorded='Plan 34 F10 (about 44 c with a style picture, about 39 c without)', proves='repeats the rate on the plan\'s sizes')

# 8. the spend ledger, counted from each allowance's start (dates assigned in log order: see the fixture's note)
ledger = budget.load_json(os.path.join(HERE, 'spend-ledger-logs-10-to-34.json'))
at_log_26 = budget.ledger_state(ledger, 'chapter 2 pictures', '2026-10-13T12:00')
check.close('left of the US$10 at log 26', at_log_26['left_dollars'], 8.70, 0.05, recorded='Decisions item 31 (about US$8.70 left; helpers told US$3 by mistake)',
            proves='the sum from the allowance\'s start date gives the corrected figure')
check.true('counting every fal entry instead would give a different answer', abs(at_log_26['spent_all_entries_dollars'] - at_log_26['spent_dollars']) > 4,
           details=f'every entry: US${at_log_26["spent_all_entries_dollars"]:.2f}; since the start: US${at_log_26["spent_dollars"]:.2f}',
           proves='the start date matters')
later = budget.ledger_state(ledger, 'chapter 2 pictures', '2026-10-15T00:00')
check.close('left of the US$10 after logs 29-30', later['left_dollars'], 5.40, 0.05, recorded='Status.md (about US$5.40 left, about US$4.58 spent since)',
            proves='as above, a second recorded point')
redesign = budget.ledger_state(ledger, 'full redesign', '2026-10-16T12:00')
check.close('spent of the US$20 by the people test', redesign['spent_dollars'], 0.85, 0.01, recorded='Status.md (about 85 US cents from the US$20)',
            proves='a new allowance starts its own count')
run = subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'plan_budget.py'), 'ledger', os.path.join(HERE, 'spend-ledger-logs-10-to-34.json'),
                      '--allowance', 'chapter 2 pictures', '--today', '2026-10-13T12:00', '--next-cost', '9'] + (['--settings', settings.path]),
                     capture_output=True, text=True)
check.true('a next step of US$9 at log 26 is refused (exit 2) and the report names the settings used', run.returncode == 2 and 'REFUSED' in run.stdout,
           details=run.stdout.strip().splitlines()[-1][:120] if run.stdout.strip() else run.stderr[-200:])

# 9. pushes: the plugin itself, then planted faults
plugin = os.path.dirname(KIT)
clean = budget.check_push(budget.files_to_check([plugin]), settings)
check.equal('the plugin folder has nothing to refuse', [r['file'] for r in clean['refused']], [],
            recorded='kit sync report (no file over 5 MB, no keys)', proves='no false alarms on 300-odd real files')
with tempfile.TemporaryDirectory() as folder:
    open(os.path.join(folder, 'voice.mp3'), 'wb').write(b'\0' * 100)
    open(os.path.join(folder, 'notes.txt'), 'w').write('FAL_KEY = "sk-' + 'a1B2' * 8 + '"\n')
    open(os.path.join(folder, 'key.pem'), 'w').write('-----BEGIN RSA PRIVATE ' + 'KEY-----\nabc\n')
    with open(os.path.join(folder, 'huge.bin'), 'wb') as handle:
        handle.truncate(int(91e6))
    for i in range(3):
        open(os.path.join(folder, f'part{i}.bin'), 'wb').write(b'\1' * int(12e6))
    planted = budget.check_push(budget.files_to_check([folder]), settings)
    check.equal('planted faults refused: audio, a token, a private key, a 91 MB file', sorted(os.path.basename(r['file']) for r in planted['refused']),
                ['huge.bin', 'key.pem', 'notes.txt', 'voice.mp3'], proves='each kind of fault is caught')
    check.true('the three 12 MB files go in chat parts of at most 28 MB', all(p['megabytes'] <= 28 for p in planted['chat_parts']) and len(planted['chat_parts']) == 2,
               details=str(planted['chat_parts']))

# 10. status of a finished-but-incomplete run (round 4's chunk logs: no process alive)
status = budget.filming_status(os.path.join(HERE), 300, settings)
check.equal('a folder with no filming process alive reads as stopped', status['state'], 'stopped')

# 11. the command line
run = subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'plan_budget.py'), 'filming', EVENTS, '--scene', 'inflation-chapter-2-newcomers',
                      '--from-frame', str(FIRST), '--to-frame', str(LAST), '--processors', '1', '--free-memory-gb', '15', '--blender-running', 'no',
                      '--free-disk-gb', '50', '--settings', settings.path], capture_output=True, text=True)
check.true('filming from the command line prints the plan, the commands and the settings used', run.returncode == 0 and 'FILM_FROM=' in run.stdout
           and 'filming.seconds_per_frame_sliding' in run.stdout and 'a fallback, not measured on this film' in run.stdout,
           details=(run.stdout + run.stderr).strip().splitlines()[-1][:120])
check.finish()
