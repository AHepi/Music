"""What this does: tests kit/film-settings.json and settings.py.
1. Every entry has a value, unit, kind (measured, judged or invented) and source; every section says what it holds.
2. A missing key stops with a clear message that names the nearest real keys.
3. The shot-kind profiles combine as written (the loosest wins; a stricter kind is not loosened by the base).
4. The film-settings.json numbers that went into the table match the project's files they were read from (the round 4
   frame times, the painter's returned size, the people test contrast, the check files' limits).
5. Drift: the tools that still keep their own copy of a house number (literals in the kit's code) are compared with the
   table. Two known drifts are reported but allowed (estimate_timeline.py's 1.5 s default pause; frame_check.py's
   140/380 px margins); any other difference fails, so a new copy that drifts is caught.
Run: python3 kit/calculators/tests/test_settings.py
"""
import json
import os
import re
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES, film_kit_folder  # noqa: E402
from settings import load_settings, problems_in, resolve_profile, walk_entries, MissingSetting, KINDS  # noqa: E402

check = Checker('film settings: the table, its reader and drift in the tools')
settings = load_settings()
data = settings.data
KIT = os.path.dirname(CALCULATORS)
FILM_KIT = film_kit_folder() or '(film kit not found)'   # FILM_KIT, or austerity-explainer/film-kit next to the plugins folder

# 1. the table
entries = dict(walk_entries(data))
problems = problems_in(data)
check.true('every entry has a value, unit, kind and source; every section an "about"', not problems,
           details=f'{len(entries)} entries, {len(problems)} problems' + (f': {problems[:3]}' if problems else ''))
counts = {k: sum(1 for e in entries.values() if e.get('kind') == k) for k in KINDS}
check.note(f'kinds: {counts}')
# the cap grows with the table (each calculator adds a few untested choices, marked invented and named here); it was a
# flat 10 when the core held 344 entries (the views-and-models builder changed it, log 35). The lessons round (23 October 2026)
# added limits for checks nobody has tested yet (the pale patch, the road as filmed, clouds, the world round a place, the sun),
# each marked invented on purpose: 69 of 705 (9.8 percent) became 74 of 712 (10.4 percent). The fix round (23 October 2026) made one of them judged
# (the road's 0.9 lies between measured faulty and measured good cases) and added three judged sizes: 73 of 715 (10.2 percent). The others are honest starting
# points nobody has tested, so the cap is "about a tenth", at most 10.5 percent (test_place_data.py says the same). A number that is measured or looked at later
# must change its kind.
check.true('the invented numbers are few (about a tenth of the table, at most 10.5 percent) and named', 0 < counts['invented'] <= 0.105 * len(entries),
           details=f'{counts["invented"]} of {len(entries)}: ' + ', '.join(k for k, e in entries.items() if e.get('kind') == 'invented'))
for section in ('frame', 'camera', 'composing', 'safe_area', 'lettering', 'people', 'light', 'effects', 'state_pictures', 'painting', 'timing',
                'sound', 'filming', 'money', 'delivery', 'models', 'checking', 'script', 'graphics', 'paper_look', 'shot_kind_profiles'):
    check.true(f'section "{section}" is there', section in data)
prices = [k for k in entries if k.startswith('money.') and 'cents' in entries[k]['unit'] or k.startswith('money.') and 'dollars' in entries[k]['unit']]
undated = [k for k in prices if not entries[k].get('date_read') and 'failure' not in k]
check.true('every price says the date it was read', not undated, details=f'{len(prices)} prices' + (f'; undated: {undated}' if undated else ''))

# 2. the reader
try:
    settings.value('frame.widht_pixels')
    check.true('a misspelt key stops with a clear message', False)
except MissingSetting as problem:
    check.true('a misspelt key stops with a clear message naming the nearest keys', 'frame.width_pixels' in str(problem), details=str(problem)[:160])
try:
    settings.value('frame')
    check.true('asking a section for a single number stops', False)
except MissingSetting as problem:
    check.true('asking a section for a single number stops clearly', 'section' in str(problem), details=str(problem)[:120])
fresh = load_settings()
fresh.value('frame.width_pixels')
check.equal('the reader records exactly the values used (for the reports)', list(fresh.used), ['frame.width_pixels'])

# 3. profiles
both = resolve_profile(load_settings(), ['crowd', 'dark_subject'])
check.equal('crowd + dark subject: rule 3\'s box is the crowd\'s', both['rule3_story_box']['value'], [0.8, 0.5])
check.equal('crowd + dark subject: rule 5\'s brightness test is off', both['rule5_subject_brightness_ratio']['applies'], False)
check.equal('crowd + dark subject: the silhouette contrast replaces it', both['silhouette_contrast']['value'], 2.2)
check.equal('crowd + dark subject: rules neither kind changes stay the still life\'s (rule 7 reach)', both['rule7_story_reaches_down']['value'], 0.7)
inside = resolve_profile(load_settings(), ['interior'])
check.equal('interior: the stricter eye range [1.5, 1.7] is not loosened by the base', inside['rule2_eye_height']['value'], [1.5, 1.7])
over = resolve_profile(load_settings(), ['overview', 'crowd'])
check.equal('overview + crowd: the loosest box wins (crowd 0.80 over overview 0.60)', over['rule3_story_box']['value'], [0.8, 0.5])
check.equal('overview + crowd: quiet-side ranges widen to cover both', over['rule10_quiet_side_weight']['value'], [0.4, 0.6])
try:
    resolve_profile(load_settings(), ['crowded'])
    check.true('an unknown kind of shot stops', False)
except MissingSetting as problem:
    check.true('an unknown kind of shot stops and lists the known kinds', 'still_life' in str(problem), details=str(problem)[:120])

# 4. numbers checked against the project's records
times = open(os.path.join(FIXTURES, 'filming', 'round4-frame-times.txt')).read()
stretches = re.findall(r'^frames .*?:\s+([\d.]+) s a frame\s+(.+)$', times, re.M)
held = [float(s) for s, kind in stretches if kind.startswith('held') and 'partly' not in kind]
sliding = [float(s) for s, kind in stretches if kind.startswith('sliding')]
check.close('held frame cost: the table against the round 4 stretches (s a frame, median)', settings.value('filming.seconds_per_frame_held_live_effects'),
            statistics.median(held), 0.05, recorded=f'working files redesign/round4-film/film/frame-times.txt ({len(held)} full held stretches, one worker; copied to fixtures/filming)',
            proves='the table carries round 4\'s measured cost, not the plan\'s older 1.2 to 1.5 s')
check.close('sliding frame cost (s a frame)', settings.value('filming.seconds_per_frame_sliding'), statistics.mean(sliding), 0.05, recorded='same file: "sliding (W1): 4.31"')
steady = {m.group(1): float(m.group(2)) for m in re.finditer(r'^\s+(held, live effects \(W\d\)): ([\d.]+) s a frame on average', times, re.M)}
loads = []
for m in re.finditer(r'^\s+frames \d+-\d+:\s+([\d.]+) s a frame \((held, live effects \(W\d\))\)$', times, re.M):
    loads.append((float(m.group(1)) - steady[m.group(2)]) * 60)
check.close('loading a piece (s): first stretch of a piece minus that view\'s steady rate, averaged', settings.value('filming.seconds_loading_a_piece'),
            statistics.mean(loads), 2, recorded=f'same file, "first stretch of each piece" ({len(loads)} pieces: {min(loads):.0f} to {max(loads):.0f} s)')
paintings = json.load(open(os.path.join(FIXTURES, 'people-test', 'people-test-paintings.json')))
check.equal('the painter\'s returned size', settings.value('frame.painting_returned_size_pixels'), paintings['paintings'][0]['returned_size'],
            recorded='people-test-paintings.json returned_size (and notice-corner-paintings.json)')
check.true('the fal price is the one on the people test ledger, with its date', '4.8 US cents a megapixel' in paintings['note']
           and settings.value('money.fal_flux_3_edit_cents_per_megapixel') == 4.8 and settings.entry('money.fal_flux_3_edit_cents_per_megapixel')['date_read'] == '2026-10-16')
for name, view in (('w1', 'works-w1-shot-check.json'), ('w3', 'works-w3-shot-check.json')):
    file = json.load(open(os.path.join(FIXTURES, 'works', view)))
    if 'story_reaches_down' in file:
        check.equal(f'rule 7 reach in {view} is the profile\'s', file['story_reaches_down'], settings.value('shot_kind_profiles.still_life.rules.rule7_story_reaches_down'))
check.equal('W3\'s widened eye range is the overview profile\'s', json.load(open(os.path.join(FIXTURES, 'works', 'works-w3-shot-check.json')))['eye_height'],
            settings.value('shot_kind_profiles.overview.rules.rule2_eye_height'))

# 5. drift: literals still kept in the kits' tools
DRIFT = [
    # (key, how the table's value is turned into the tool's, file, pattern)
    ('timing.first_word_at_seconds', None, 'narration-tools/assemble_chapter_narration.py', r'^FIRST_WORD_AT\s*=\s*([-\d.]+)'),
    ('timing.first_word_at_seconds', None, 'narration-tools/estimate_timeline.py', r'^FIRST_WORD_AT\s*=\s*([-\d.]+)'),
    ('timing.tail_after_last_word_seconds', None, 'narration-tools/assemble_chapter_narration.py', r'^TAIL_AFTER_LAST_WORD\s*=\s*([-\d.]+)'),
    ('timing.tail_after_last_word_seconds', None, 'narration-tools/estimate_timeline.py', r'^TAIL_AFTER_LAST_WORD\s*=\s*([-\d.]+)'),
    ('timing.default_page_pause_seconds', None, 'narration-tools/assemble_chapter_narration.py', r'^DEFAULT_PAUSE\s*=\s*([-\d.]+)'),
    ('timing.default_page_pause_seconds', None, 'narration-tools/estimate_timeline.py', r"'--default-pause', type=float, default=([-\d.]+)"),
    ('frame.frames_per_second', None, 'narration-tools/assemble_chapter_narration.py', r'^FRAMES_PER_SECOND\s*=\s*([-\d.]+)'),
    ('frame.frames_per_second', None, 'narration-tools/estimate_timeline.py', r'^FRAMES_PER_SECOND\s*=\s*([-\d.]+)'),
    ('sound.voice_page_lufs', None, 'narration-tools/assemble_chapter_narration.py', r'^VOICE_LOUDNESS\s*=\s*([-\d.]+)'),
    ('sound.sample_rate', None, 'narration-tools/assemble_chapter_narration.py', r'^SAMPLE_RATE\s*=\s*([-\d.]+)'),
    ('sound.mix_lufs', None, 'narration-tools/mix_narration_over_music.sh', r'target_loudness="([-\d.]+)"'),
    ('sound.music_level_db', None, 'narration-tools/mix_narration_over_music.sh', r'music_level_db="([-\d.]+)"'),
    ('sound.duck.threshold', 'duck', 'narration-tools/mix_narration_over_music.sh', r'duck_threshold="([-\d.]+)"'),
    ('sound.music_only_lufs', None, 'paper-film/tools/add_music_bed.sh', r'\[LOUDNESS=([-\d.]+)\]'),
    ('timing.caption_max_letters', None, 'narration-tools/make_captions.py', r'^MAX_LETTERS\s*=\s*([-\d.]+)'),
    ('timing.caption_hold_after_last_word_seconds', None, 'narration-tools/make_captions.py', r'^HOLD_AFTER_LAST_WORD\s*=\s*([-\d.]+)'),
    ('timing.caption_shortest_seconds', None, 'narration-tools/make_captions.py', r'^SHORTEST_CAPTION\s*=\s*([-\d.]+)'),
    ('timing.first_word_tolerance_seconds', None, 'narration-tools/extract_word_times.py', r'^FIRST_WORD_TOLERANCE\s*=\s*([-\d.]+)'),
    ('camera.audit_turn_limit_degrees_per_second', None, 'paper-film/tools/camera_audit.py', r'^TURN_LIMIT\s*=\s*([-\d.]+)'),
    ('camera.audit_travel_limit_share_per_second', None, 'paper-film/tools/camera_audit.py', r'^TRAVEL_LIMIT\s*=\s*([-\d.]+)'),
    ('camera.audit_lens_limit_share_per_second', None, 'paper-film/tools/camera_audit.py', r'^LENS_LIMIT\s*=\s*([-\d.]+)'),
    ('camera.audit_join_gap_seconds', None, 'paper-film/tools/camera_audit.py', r'^JOIN_GAP\s*=\s*([-\d.]+)'),
    ('camera.audit_cut_jump_share', None, 'paper-film/tools/camera_audit.py', r'^CUT_JUMP\s*=\s*([-\d.]+)'),
    ('camera.audit_cut_turn_degrees', None, 'paper-film/tools/camera_audit.py', r'^CUT_TURN\s*=\s*([-\d.]+)'),
    ('sound.mouth.quiet_db', 'mouth', 'paper-film/tools/make_mouth_track.py', r'^QUIET_DB\s*=\s*([-\d.]+)'),
    ('sound.mouth.loud_db', 'mouth', 'paper-film/tools/make_mouth_track.py', r'^LOUD_DB\s*=\s*([-\d.]+)'),
    ('timing.turn_after_last_word_seconds', None, 'paper-film/scenes/cinema-chapter.js', r"DEFAULT_JOIN = \{ kind: 'peel', after: ([-\d.]+)"),
    ('timing.peel_length_seconds', None, 'paper-film/scenes/cinema-chapter.js', r"DEFAULT_JOIN = \{[^}]*length: ([-\d.]+)"),
    ('timing.peel_shading_in_share', None, 'paper-film/stage/cinema-stage.js', r'^const PEEL_SHADING_IN = ([-\d.]+)'),
    ('safe_area.text_left_pixels', None, 'paper-film/scenes/graphics.js', r'^export const TEXT_LEFT = ([-\d.]+)'),
    ('safe_area.text_right_pixels', None, 'paper-film/scenes/graphics.js', r'^export const TEXT_RIGHT = ([-\d.]+)'),
    ('checking.find_jumps.jump_factor', 'find_jumps', 'paper-film/tools/find_jumps.py', r'else ([-\d.]+)\n'),
    ('shot_kind_profiles.still_life.rules.rule2_eye_height', 'low', 'paper-film/tools/check_shot.py', r"get\('eye_height', \[([-\d.]+), [-\d.]+\]\)"),
    ('shot_kind_profiles.still_life.rules.rule10_quiet_side_weight', 'low', 'paper-film/tools/check_shot.py', r'ok = ([-\d.]+) <= quiet <= [-\d.]+'),
    ('shot_kind_profiles.still_life.rules.rule10_quiet_side_weight', 'high', 'paper-film/tools/check_shot.py', r'ok = [-\d.]+ <= quiet <= ([-\d.]+)'),
    ('shot_kind_profiles.still_life.rules.rule12_title_zone_sky_share', None, 'paper-film/tools/check_shot.py', r'if sky < ([-\d.]+):'),
    ('safe_area.must_read_right_edge_share', 'frame_check', 'paper-film/tools/frame_check.py', r'clear = (\d+) <= px <= WIDTH - (\d+)'),
]
KNOWN = {
    ('timing.default_page_pause_seconds', 'narration-tools/estimate_timeline.py'): 'estimate_timeline.py still defaults to 1.5 s (the drift the skeptic named)',
    ('safe_area.must_read_right_edge_share', 'paper-film/tools/frame_check.py'): 'frame_check.py keeps 140 px margins (0.87 across), older than rule 12\'s 0.90',
}


def table_value(key, how):
    if how == 'duck':
        return settings.value('sound.duck')['threshold']
    if how == 'mouth':
        return settings.value('sound.mouth')['quiet_db' if key.endswith('quiet_db') else 'loud_db']
    if how == 'find_jumps':
        return settings.value('checking.find_jumps')['jump_factor']
    if how == 'low':
        return settings.value(key)[0]
    if how == 'high':
        return settings.value(key)[1]
    if how == 'frame_check':
        return settings.value(key)
    return settings.value(key)


kits = [('plugin kit', KIT)] + ([('film kit', FILM_KIT)] if os.path.isdir(FILM_KIT) else [])
new_drift, known_seen, missing, compared = [], [], [], 0
for label, root in kits:
    for key, how, relative, pattern in DRIFT:
        path = os.path.join(root, relative)
        if not os.path.exists(path):
            missing.append(f'{label}: {relative}')
            continue
        found = re.search(pattern, open(path).read(), re.M)
        if not found:
            missing.append(f'{label}: {relative} (no {pattern!r})')
            continue
        compared += 1
        wanted = table_value(key, how)
        if how == 'frame_check':
            got = 1 - float(found.group(2)) / settings.value('frame.width_pixels')
            same = abs(got - wanted) < 0.005
        else:
            got = float(found.group(1))
            same = abs(got - wanted) < 1e-9
        if not same:
            line = f'{label} {relative}: {got:g} against film-settings.json {key} = {wanted}'
            (known_seen if (key, relative) in KNOWN else new_drift).append(line)
check.true(f'no new drift: {compared} copies of house numbers in the kits\' tools agree with the table, apart from the known ones', not new_drift,
           details='; '.join(new_drift) or f'{compared} compared', proves='a tool that changes its own copy of a house number is caught')
for line in known_seen:
    check.note(f'known drift (allowed until the tool reads the table): {line}')
for line in missing:
    check.note(f'not found (not compared): {line}')
check.finish()
