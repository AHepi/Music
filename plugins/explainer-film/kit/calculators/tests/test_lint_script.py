"""What this does: tests narration-tools/lint_script.py (the script and narration gate) on chapter 2's two scripts (the
recorded one of log 19 and the newcomer rewrite of log 33), chapter 1's script as it was before the voice fix of log 09
(mood cues), the real word times, timelines and transcripts of chapters 1 and 2, and chapter 2's recordings (read from
the project when present; the test skips those checks without them). Each check names the number got, the number the
project recorded and where, and says whether it proves something or only repeats.
The hold-outs: the length estimate of each chapter made from the OTHER chapter's recording; the guess pages and the
main rule found in the newcomer script without being told; the cue and capital faults of chapter 1's old script; the
first-word lateness found in chapter 2's recordings against the corrections extract_word_times.py made.
Run: python3 kit/calculators/tests/test_lint_script.py
"""
import copy
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, FIXTURES  # noqa: E402
from settings import load_settings  # noqa: E402

KIT = os.path.dirname(CALCULATORS)
NARRATION_TOOLS = os.path.join(KIT, 'narration-tools')
sys.path.insert(0, NARRATION_TOOLS)
import lint_script as lint  # noqa: E402

check = Checker('script and narration gate: before recording and after')
settings = load_settings()
SCRIPTS = os.path.join(FIXTURES, 'script')
OLD = os.path.join(SCRIPTS, 'old-chapter-2-narration-script.json')
NEW = os.path.join(SCRIPTS, 'newcomer-narration-script.json')
CH1_BEFORE_09 = os.path.join(SCRIPTS, 'chapter-1-narration-script-before-log-09.json')
CH1 = os.path.join(KIT, 'examples', 'austerity-chapter-1')
CH2 = os.path.join(KIT, 'examples', 'inflation-chapter-2')
NEW_TIMELINE = os.path.join(KIT, 'examples', 'inflation-chapter-2-newcomers', 'timeline-estimated.json')
RECORDINGS = '/home/user/Music/austerity-explainer/chapter-2-inflation/narration/recordings'
WORK = tempfile.mkdtemp()


def problems(result, check_name=None, verdict=None, page=None):
    return [p for p in result['problems'] if (check_name is None or p['check'] == check_name) and (verdict is None or p['verdict'] == verdict)
            and (page is None or p['page'] == page)]


def write(data, name):
    path = os.path.join(WORK, name)
    json.dump(data, open(path, 'w'), ensure_ascii=False, indent=1)
    return path


# 1. the recorded chapter 2 script (log 19), judged on its real recording's timeline
old = lint.lint_before(OLD, settings, timeline_path=os.path.join(CH2, 'timeline.json'))
check.true('the recorded chapter 2 script is stopped before recording', old['errors'] > 0, details=old['verdict'])
check.true('its main rule is never said twice word for word', bool(problems(old, 'main rule', 'error')),
           recorded='log 33 audit: the main rule said once, 3 minutes in', proves='found without being told which sentence is the rule')
page8 = [p for p in problems(old, 'sentences', 'error', 8) if 'So yes' in p['text']]
check.true('the rule\'s own sentence on page 8 is flagged as too long (30 words counted; the audit counted 28 without "So yes...")', bool(page8),
           details=page8[0]['text'][:60] if page8 else 'not flagged', recorded='log 33 audit: one 28-word sentence', proves='the long-sentence limit catches it')
check.within('spoken figures in the recorded script', old['figures'], 33, 41, recorded='log 33 teaching plan: about 37 spoken numbers (0,3,0,3,7,3,6,3,5,7 by page)',
             proves='the counter agrees with a count made by hand (see the per-page note)')
check.note('figures by page: ' + ', '.join(f'{p["page"]}: {len(p["figures"])}' for p in old['per_page']) + ' (the teaching plan: 0, 3, 0, 3, 7, 3, 6, 3, 5, 7)')
check.true(f'{old["figures_per_minute"]:.1f} figures a minute of speech is over the limit of {settings.value("script_gate.figures_per_minute_max")}',
           bool(problems(old, 'figures', 'error')), recorded='skeptic log 35: 37 in 252 s, 8.8 a minute (too many)', proves='the limit fails the script log 33 rejected')
check.true('years said out of order are listed', bool(problems(old, 'years', 'look')), details=str(old['years']),
           recorded='log 33 audit: time changes direction 8 times (counting the years not said)', proves='the zigzag is seen from the years said')
price = next((t for t in old['term_table'] if t['word'] == 'price'), None)
check.true('"price" is in the table of repeated words with every sentence it is in', price is not None and len(price['sentences']) >= 6,
           details=f'{len(price["sentences"])} sentences' if price else 'missing', recorded='log 33 audit: "price" used for six different things',
           proves='a person gets the sentences to judge; the tool does not count meanings')
old_marked = json.load(open(OLD))
old_marked['pages'][7]['key'] = True
old_key = lint.lint_before(write(old_marked, 'old-key.json'), settings, timeline_path=os.path.join(CH2, 'timeline.json'))
key_error = problems(old_key, 'key page', 'error', 8)
check.true('with page 8 marked "key" (the page holding the rule), its 175 words a minute against the median 164 fails', bool(key_error),
           details=key_error[0]['text'][:90] if key_error else 'not flagged', recorded='log 33: the key page at 175 against 164 (lesson 126)',
           proves='the key-page rule catches what the 1.1 x median rule misses (175 is under 1.1 x 164)')
check.close('words a minute on page 8 of the real recording', next(s for s in old['speeds'] if s['page'] == 8)['words_a_minute'], 175, 1,
            recorded='log 33 audit table (page 8: 175)', proves='only repeats the recording\'s own timing')
check.equal('credits for the recorded script (letters sent, cue included)', old['credits'], 4297, recorded='Status.md: about 4,300 credits',
            proves='only repeats: the logs also counted by text length')

# 2. the newcomer script as written (log 33): only the missing marks stop it
new = lint.lint_before(NEW, settings, word_times=os.path.join(CH2, 'word-times.json'), default_pause=1.5)
other_errors = [p for p in problems(new, verdict='error') if p['check'] != 'key page']
check.equal('the newcomer script has no error but the missing "key" mark', [p['check'] for p in other_errors], [],
            recorded='log 33: the rewrite was accepted', proves='cue, capitals, names, sentences and figures pass on the script the project accepted')
guesses = sorted(int(k) for k, v in new['pauses_after_page'].items() if v['why'].startswith('a guess'))
check.equal('guess holds found from the text alone', guesses, [4, 8, 10],
            recorded='the script\'s own note: "Pages 4, 8 and 10 end on a guess: leave a gap of about 4 seconds"', proves='no page was marked')
rule_pages = sorted({tuple(v) for v in new['main_rule']['repeated_sentences'].values()})
check.equal('the main rule found said word for word on pages 5 and 16', rule_pages, [(5, 16)],
            recorded='33 Script ... for newcomers.md (the rule said twice in identical words)', proves='found without being told')
check.within('figures a minute of speech in the newcomer script', new['figures_per_minute'], 0, settings.value('script_gate.figures_per_minute_look'),
             recorded='skeptic log 35: 28 figures, 4.1 a minute (accepted)', proves='the limit passes the accepted script')
check.within('spoken figures counted in the newcomer script', new['figures'], 20, 30, recorded='log 33: about 28 (round 2: about 24, then about 27)',
             proves='the count is in the range the project counted by hand (the counter skips counts of things like "two factories")')
check.within('words a sentence on average', new['mean_words_a_sentence'], 8.5, 9.5, recorded='round 2 test findings: sentences average 9 words',
             proves='the sentence splitter agrees with the project\'s count')
check.within('the longest sentence', new['longest_sentence_words'], 19, 20, recorded='round 2 test findings: the longest is 19', proves='as above')
check.true('page 9 ends on a question with no guess phrase: listed for a person, not held as a guess', bool(problems(new, 'guess holds', 'look', 9)),
           recorded='the script\'s note gives page 9 a card hold, not a guess hold', proves='a question alone is not taken for a guess')
marked = json.load(open(NEW))
marked['pages'][4]['key'] = True
marked['pages'][8]['held_card'] = True
marked['main_rule'] = ['When new money is spent... and there are spare workers, materials and machines... it mostly gets more things made.',
                       'When nothing is spare... it mostly pushes prices up.']
marked_path = write(marked, 'newcomer-marked.json')
timeline_out = os.path.join(WORK, 'timeline-estimated.json')
done = lint.lint_before(marked_path, settings, word_times=os.path.join(CH2, 'word-times.json'), default_pause=1.5, timeline_out=timeline_out)
check.equal('with page 5 marked key, page 9 a held card and the rule named: no errors', [p['text'][:60] for p in problems(done, verdict='error')], [],
            proves='the marks the gate asks for are enough')
recorded_timeline = json.load(open(NEW_TIMELINE))
check.equal('the pauses after pages equal the shipped estimated timeline\'s', {k: v['seconds'] for k, v in done['pauses_after_page'].items()},
            {k: float(v) for k, v in recorded_timeline['pauses_after_page'].items()}, recorded='examples/inflation-chapter-2-newcomers/timeline-estimated.json',
            proves='the guess holds are found; the 3.5 s after pages 5 and 9 only repeat the marks added from the script\'s note')
made = json.load(open(timeline_out))
check.close('chapter length from estimate_timeline.py, called by the gate', made['chapter_seconds'], recorded_timeline['chapter_seconds'], 1e-6,
            recorded='timeline-estimated.json (406.938 s)', proves='only repeats: the same tool on the same files (the gate passes the pauses through untouched)')
check.equal('words in the newcomer script', sum(len(p['words']) for p in made['pages']), 1021, recorded='log 33 and Status.md (1,021 words)')
check.close('credits and dollars for the newcomer script', done['dollars'], 1.10, 0.01, recorded='Status.md: about 6,300 credits, about US$1.10',
            proves='only repeats the rate (counted by text length, no bill)')
if done['speeds']:
    check.note('estimated pages over 170 words a minute (listed for a person): ' + ', '.join(str(p['page']) for p in problems(done, 'speed', 'look')))

# 3. hold-out of the length estimate: each chapter from the OTHER chapter's recording (same narrator)
for script, measured_from, real, name in ((os.path.join(CH1, 'narration-script.json'), os.path.join(CH2, 'word-times.json'), os.path.join(CH1, 'timeline.json'),
                                          'chapter 1 from chapter 2\'s recording'),
                                         (OLD, os.path.join(CH1, 'word-times.json'), os.path.join(CH2, 'timeline.json'), 'chapter 2 from chapter 1\'s recording')):
    result = lint.lint_before(script, settings, word_times=measured_from, timeline_out=os.path.join(WORK, 'holdout.json'))
    real_timeline = json.load(open(real))
    real_speech = sum(p['last_word_end_at'] - p['first_word_at'] for p in real_timeline['pages'])
    estimated = sum(s['seconds'] for s in result['speeds'])
    check.within(f'{name}: speech estimated against the real recording (error share)', estimated / real_speech - 1, -0.03, 0.03,
                 recorded=f'{os.path.relpath(real, KIT)} ({real_speech:.1f} s of speech)', proves='the estimate holds on a script it was not measured on')
    worst = max(abs(s['seconds'] / (p['last_word_end_at'] - p['first_word_at']) - 1) for s, p in zip(result['speeds'], real_timeline['pages']))
    check.note(f'{name}: {estimated:.1f} s against {real_speech:.1f} s; the worst page is off by {worst * 100:.0f}% (so a page\'s words a minute '
               'on an estimate is good to about 10%)')
same = lint.lint_before(OLD, settings, word_times=os.path.join(CH2, 'word-times.json'), timeline_out=os.path.join(WORK, 'same.json'))
check.close('chapter 2 from its own recording: seconds of speech', sum(s['seconds'] for s in same['speeds']), 251.7, 0.5,
            recorded='log 34: 252 s predicted against 251.7 s', proves='only repeats: the estimate is scaled to reproduce the recording it was measured on')

# 4. chapter 1 before the voice fix (log 09): mood cues and their effects
before09 = lint.lint_before(CH1_BEFORE_09, settings)
script09 = json.load(open(CH1_BEFORE_09))
inner_pages = sorted(p['page'] for p in script09['pages'] if lint.split_cue(p['text'])[1].count('[') > 0)
flagged_pages = sorted(p['page'] for p in problems(before09, 'cue', 'error') if p['page'])
check.equal('chapter 1\'s old script: every page with a mood cue inside its text is stopped', flagged_pages, inner_pages,
            recorded='log 09: [urgent], [wry], [serious] and other cues moved the voice up and down between pages', proves='the real faulty script fails')
check.true('and the different opening cues across pages are stopped', any('different cues' in p['text'] for p in problems(before09, 'cue', 'error')),
           details=next((p['text'][:80] for p in problems(before09, 'cue', 'error') if 'different cues' in p['text']), ''))
capitals = sorted(p['text'].split('"')[1] for p in problems(before09, 'capitals', 'error'))
check.equal('its words in capitals for emphasis are stopped', capitals, ['CHOSE', 'SHELLS', 'STOPPING'],
            recorded='log 09: "no words in capitals (capitals make the voice push)"', proves='the real faulty script fails')
planted = json.load(open(NEW))
planted['pages'][2]['text'] = planted['pages'][2]['text'].replace('Picture two factories.', 'Picture TWO factories. [excited]').replace(
    'Call it the quiet factory.', 'Call it the quiet factory, Mattei says.')
faults = lint.lint_before(write(planted, 'planted.json'), settings)
check.equal('planted faults on page 3: a cue inside the text, capitals, a name in plain spelling',
            sorted({p['check'] for p in problems(faults, verdict='error', page=3)}), ['capitals', 'cue', 'names'], proves='each kind is caught')

# 5. the research ledger: dates and who says it (a ledger built from the project's recorded cases; no such ledger exists)
ledger = {'claims': [
    {'id': 'C2-N05', 'claim': 'prices rose 4.1% in the year to June 2026 (Stats NZ)', 'said_by': 'Stats NZ', 'valid_until': '2026-10-22'},
    {'id': 'C2-N13', 'claim': 'unemployment about 5.6% in the June quarter', 'said_by': 'Stats NZ', 'valid_until': '2026-11-04'},
    {'id': 'C2-H18', 'claim': 'fewer jobs as the cure\'s aim', 'said_by': 'Clara E. Mattei'},
    {'id': 'C2-X01', 'claim': '"unfortunate costs" of fighting inflation', 'said_by': 'Jerome Powell (America\'s Federal Reserve)'}]}
lesson131 = json.load(open(NEW))
lesson131['pages'][13]['text'] = '[in a warm, steady New Zealand accent] Our Reserve Bank says the cure would probably mean fewer jobs. Clara E. /məˈteɪi/ argues that fewer jobs are the main goal.'
lesson131['pages'][13]['ledger'] = ['C2-X01', 'C2-H18']
lesson131['pages'][14]['ledger'] = ['C2-N05']
dated = lint.lint_before(write(lesson131, 'lesson131.json'), settings, ledger=ledger, today='2026-10-23')
out_of_date = problems(dated, 'out-of-date facts', 'error')
check.true('on 23 October the 4.1% (due to change on 22 October) must be checked again; the 4 November figure not yet',
           len(out_of_date) == 1 and 'C2-N05' in out_of_date[0]['text'], details='; '.join(p['text'][:60] for p in out_of_date),
           recorded='the Traps: inflation may change on 22 October, unemployment on 4 November', proves='made-up ledger: the date check works')
speaker = problems(dated, 'who says it', 'look', 14)
check.true('"Our Reserve Bank says" resting on Powell\'s words is flagged; Mattei\'s own line is not', len(speaker) == 1 and 'Reserve Bank' in speaker[0]['text'],
           details='; '.join(p['text'][:80] for p in speaker), recorded='lesson 131 (a line about our Reserve Bank rested on Powell\'s speech)',
           proves='made-up ledger built on the recorded case')

# 6. after recording: chapter 2's real transcripts
after = lint.lint_after(OLD, settings, os.path.join(SCRIPTS, 'old-chapter-2-transcripts'))
check.equal('chapter 2\'s transcripts: no page to record again', after['rerecord'], {},
            recorded='log 19 (no cue read aloud; the word times match the recording)', proves='no false alarm on ten real pages')
lengths = [r['cue_word_median_seconds'] for r in after['pages']]
check.within('the cue\'s words last (middle word, longest page)', max(lengths), 0, settings.value('timing.bracket_cue_max_seconds'),
             recorded='log 07 (each cue lasts under a fifth of a second)', proves='the per-word limit passes cues that were not read aloud, although a '
             'whole cue can stretch to 0.51 s when the first word is placed late')
after1 = lint.lint_after(os.path.join(CH1, 'narration-script.json'), settings, os.path.join(CH1, 'transcripts'))
check.equal('chapter 1\'s transcripts: no page to record again', after1['rerecord'], {}, recorded='logs 09-10', proves='as above, ten more pages')
pauses = after['thinking_pauses']
check.true(f'all {len(pauses)} "..." in chapter 2 leave under 1 s (the word and its pause last {min(p["word_and_gap"] for p in pauses):.2f} to '
           f'{max(p["word_and_gap"] for p in pauses):.2f} s)', all(p['word_and_gap'] < 1.1 for p in pauses) and min(p['word_and_gap'] for p in pauses) >= 0.4,
           recorded='log 33: a word followed by "..." lasts 0.4 to 1.0 seconds; no time to think', proves='the recorded measurement is reproduced')
read_aloud = json.load(open(os.path.join(SCRIPTS, 'old-chapter-2-transcripts', 'page2-words.json')))
t = 0.0
for w in read_aloud['words'][:7]:
    w['start'], w['end'] = round(t, 3), round(t + 0.3, 3)
    t += 0.35
os.makedirs(os.path.join(WORK, 'read-aloud'), exist_ok=True)
for page in range(1, 11):
    data = read_aloud if page == 2 else json.load(open(os.path.join(SCRIPTS, 'old-chapter-2-transcripts', f'page{page}-words.json')))
    json.dump(data, open(os.path.join(WORK, 'read-aloud', f'page{page}-words.json'), 'w'))
planted_after = lint.lint_after(OLD, settings, os.path.join(WORK, 'read-aloud'))
check.equal('a cue read aloud (its words 0.3 s each, as spoken words last) sends that page back', sorted(planted_after['rerecord']), [2],
            proves='made-up transcript: the check fires')
heard = os.path.join(WORK, 'heard')
os.makedirs(heard, exist_ok=True)
words9 = [w for w in json.load(open(os.path.join(SCRIPTS, 'old-chapter-2-transcripts', 'page9-words.json')))['words'] if w.get('type') == 'word'][7:]
json.dump({'words': [dict(w, text=('Matty' if lint.word_key(w['text']) in ('məteɪi', 'mattei') or '/' in w['text'] else w['text'])) for w in words9]},
          open(os.path.join(heard, 'page9-words.json'), 'w'), ensure_ascii=False)
named = lint.lint_after(OLD, settings, os.path.join(SCRIPTS, 'old-chapter-2-transcripts'), heard=heard)
check.true('a name heard wrongly ("Matty" for Mattei) sends page 9 back', 9 in named['rerecord'] and 'name' in named['rerecord'][9],
           details=named['rerecord'].get(9, 'not flagged'), recorded='log 05: Mattei said the Italian way; log 19 used the transcript to check names',
           proves='made-up heard transcript: the check fires')
if os.path.isdir(RECORDINGS):
    with_audio = lint.lint_after(OLD, settings, os.path.join(SCRIPTS, 'old-chapter-2-transcripts'), recordings=RECORDINGS)
    word_times = json.load(open(os.path.join(CH2, 'word-times.json')))
    corrected = {}
    for page in word_times['pages']:
        raw = [w for w in json.load(open(os.path.join(SCRIPTS, 'old-chapter-2-transcripts', f'page{page["page"]}-words.json')))['words'] if w.get('type') == 'word']
        moved = raw[7]['start'] - page['words'][0]['start']
        if moved > 0:
            corrected[page['page']] = round(moved, 3)
    found = {row['page']: next((w['late_by'] for w in row.get('late_words', []) if w['first_word']), None) for row in with_audio['pages']}
    found = {k: v for k, v in found.items() if v}
    check.equal('first words found late in the recordings = the ones extract_word_times.py moved, by the same amounts', found, corrected,
                recorded='examples/inflation-chapter-2/word-times.json against the raw transcripts (9 of 10 pages, 0.05 to 0.50 s)',
                proves='the gate\'s onset finder agrees with the tool that made the word times (the same method, so a consistency check)')
    later = [w for row in with_audio['pages'] for w in row.get('late_words', []) if not w['first_word']]
    check.note(f'words placed late after a silence of 0.5 s or more inside a page: {len(later)} found in chapter 2 (no record to compare with)')
    silences = [p['silence'] for p in with_audio['thinking_pauses']]
    check.true(f'the real silence in each "..." measured from the recordings: {min(silences):.2f} to {max(silences):.2f} s, all under 1 s',
               max(silences) < 1.0, recorded='log 33 (each "..." gave under a second)', proves='measured on the audio, not inferred from the transcript')
else:
    check.note(f'chapter 2 recordings not found at {RECORDINGS}: the audio checks were not run')

# 7. the command line
run = subprocess.run([sys.executable, '-I', '-B', os.path.join(NARRATION_TOOLS, 'lint_script.py'), 'before', OLD, '--timeline', os.path.join(CH2, 'timeline.json'),
                      '--settings', settings.path], capture_output=True, text=True)
check.true('before, from the command line: exit 1 on the recorded script, the report names the settings used', run.returncode == 1
           and 'Settings used (film-settings.json)' in run.stdout and 'script_gate.figures_per_minute_max' in run.stdout,
           details=(run.stdout + run.stderr).strip().splitlines()[0][:120])
run = subprocess.run([sys.executable, '-I', '-B', os.path.join(NARRATION_TOOLS, 'lint_script.py'), 'before', marked_path, '--word-times',
                      os.path.join(CH2, 'word-times.json'), '--json', '--settings', settings.path], capture_output=True, text=True)
check.true('before --json on the marked newcomer script: exit 0 and JSON with settings_used', run.returncode == 0 and 'settings_used' in json.loads(run.stdout),
           details=run.stderr[-200:])
help_run = subprocess.run([sys.executable, '-I', '-B', os.path.join(NARRATION_TOOLS, 'lint_script.py'), '--help'], capture_output=True, text=True)
check.true('lint_script.py answers --help and opens with its note', help_run.returncode == 0 and 'usage' in help_run.stdout
           and open(os.path.join(NARRATION_TOOLS, 'lint_script.py')).read().startswith('"""What this does'))
check.finish()
