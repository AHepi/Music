"""What this does: checks a narration script before any credits are spent on the voice, and checks the recordings after,
so the faults this project found by ear and by hand (logs 04-34) are caught by counting instead.

Before recording (lint_script.py before SCRIPT.json ...). Errors stop the paid step (exit 1):
  - the delivery cue: exactly one [..] at the start of every page, the same on every page (the script's
    accent_instruction), and no other brackets (lesson 17: a multi-word cue is one cue; mood cues moved the voice);
  - no word in capitals for emphasis (capitals make the voice push), except allowed short forms (NZ, GDP ...);
  - names only in their sound spelling: a name in phonetic_names never appears in its plain spelling;
  - sentences: about 9 words on average (more than 12 fails), none over 20;
  - spoken figures (years, amounts, percentages, lengths of time) per minute of speech: more than 6 fails (calibrated
    on chapter 2: the recorded script about 8 a minute, the newcomer script about 4);
  - the main rule said twice in identical words (the script's main_rule; without one, sentences said twice are found
    and offered); a page marked "key": true carries the main idea, and it must not be faster than the chapter's median
    page (log 33: the key page ran at 175 words a minute against a median of 164);
  - facts in a research ledger whose valid_until date has passed, and 'X says' lines whose ledger source is not X.
Lists for a person (verdict "look"): pages faster than 170 words a minute or 1.1 x the median, words a newcomer may not
know (with the sentence after, so an explanation can be seen), whether the stakes come in the first 30 seconds, a table
of repeated words with every sentence they are in (one word, one meaning), years said out of order, names to check.
It also fills the guess holds (a page whose last sentences hold "Have a guess" or similar waits 4 s after it; a page
marked "key" or "held_card" adds 2 s for its card), makes the estimated timeline with estimate_timeline.py (the same
tool, called as it is) from an earlier recording of the same voice, and prices the recording (credits = letters sent,
the cue included; dollars from film-settings.json).

After recording (lint_script.py after SCRIPT.json --transcripts DIR ...): a cue read aloud (its words last over 0.2 s each), words
that differ from the script and names said wrongly (with a heard, speech-to-text transcript: --heard DIR), each '...'
that gave less than 1 s of silence, words placed late after a silence of 0.5 s or more (with the recordings), missing
downloads, and the pages to re-record with their credits and dollars.

Use:
  python3 -I lint_script.py before SCRIPT.json [--word-times EARLIER_WORD_TIMES.json] [--timeline TIMELINE.json]
        [--timeline-out OUT.json] [--default-pause S] [--ledger LEDGER.json] [--today YYYY-MM-DD] [--common-words FILE]
  python3 -I lint_script.py after SCRIPT.json --transcripts DIR [--recordings DIR] [--heard DIR]
--word-times  an earlier word-times file of the SAME voice: the estimated timeline is made from it (estimate_timeline.py)
--timeline    a timeline to judge speeds on instead (a real recording's, or an estimate made earlier)
--ledger      {"claims": [{"id": "C2-N05", "claim": "...", "said_by": "Stats NZ", "valid_until": "2026-10-22"}]}; a page
              may list the ids it rests on: "ledger": ["C2-N05"]
--common-words  a list of common English words, one a line (e.g. the 5,000 most used); without it, long and capitalised
              words are listed
SCRIPT.json: {"accent_instruction": "[...]", "phonetic_names": {"/m@'teIi/": "Mattei"}, "main_rule": "sentence" or
  ["sentence", ...], "allowed_capitals": ["NZ"], "pages": [{"page": 1, "name": "...", "text": "[...] ...", "key": true,
  "held_card": true, "guess": true, "pause_after": 4.0, "ledger": ["id"]}]}
Every command takes --json, --out FILE, --report FILE and --settings FILE (kit/film-settings.json), and names the
settings it used. Exit 1 when anything must be fixed before paying (before) or a page must be re-recorded (after).
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from datetime import date

sys.dont_write_bytecode = True   # the gates import their sibling tools; leave no __pycache__ in the kit
HERE = os.path.dirname(os.path.abspath(__file__))
CALCULATORS = os.path.join(os.path.dirname(HERE), 'calculators')
if CALCULATORS not in sys.path:
    sys.path.insert(0, CALCULATORS)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings  # noqa: E402
from calculator_output import add_output_options, finish  # noqa: E402

ESTIMATE_TIMELINE = os.path.join(HERE, 'estimate_timeline.py')
STOP_WORDS = set('''a about above after again against all almost already also always am an and any are aren't as at be because
been before being below between both but by can can't cannot could couldn't did didn't do does doesn't doing don't down during
each even ever every few for from further get gets got had hadn't has hasn't have haven't having he he'd he'll he's her here
here's hers herself him himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself just let's like made
make makes many may me more most much must my myself no nor not now of off on once one only or other ought our ours ourselves
out over own same she she'd she'll she's should shouldn't so some such than that that's the their theirs them themselves then
there there's these they they'd they'll they're they've this those through to too under until up upon us very was wasn't we
we'd we'll we're we've were weren't what what's when when's where where's which while who who's whom why why's will with
won't would wouldn't you you'd you'll you're you've your yours yourself yourselves go goes going gone went come came still
again yes say says said back next time well really just only way thing things'''.split())
# long words (9 letters or more) almost every listener knows: left out of the "may not know" list when no common-words
# list is given (a rough list, invented for this gate)
COMMON_LONG_WORDS = set('''everything something sometimes everyone everybody anything anywhere everywhere somewhere government
governments important different difference community beautiful buildings business businesses children yesterday tomorrow
together families materials factories countries thousands hundreds happened happening questions remember remembered
understand understood themselves ourselves yourselves otherwise therefore including following information education
experience president presidents millions billions probably possible actually certainly generally usually especially
completely available necessary recently currently beginning wonderful newspaper telephone breakfast afternoon christmas
september november december february wednesday thursday saturday situation condition attention direction operation
position character structure shopping travelled travelling particular important interested interesting understand
everything somebody something whatever whenever wherever expensive different difficult carefully everybody yesterday
neighbours neighbour neighbourhood restaurant supermarket checkout tomorrow worldwide nineteen seventeen eighteen fourteen
thirteen seventy hundred thousand million billion trillion percent quarter president explained explains explain'''.split())
SMALL = {'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'}
TEENS = {'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'}
TENS = {'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'}
BIG = {'hundred', 'hundreds', 'thousand', 'thousands', 'million', 'millions', 'billion', 'billions', 'trillion', 'trillions'}
FRACTIONS = {'half', 'quarter'}
CHANGES = {'double', 'doubled', 'doubles', 'triple', 'tripled', 'quadruple', 'quadruples', 'quadrupled', 'halve', 'halved'}
NUMBER_WORDS = SMALL | TEENS | TENS | BIG | FRACTIONS | {'zero', 'point', 'percent'}
UNITS = {'percent', 'cent', 'cents', 'year', 'years', 'month', 'months', 'week', 'weeks', 'day', 'days', 'hour', 'hours', 'minute',
         'minutes', 'dollar', 'dollars', 'pound', 'pounds', 'yen', 'marks', 'times'} | BIG
SPEAKING_VERBS = r'(?:says|said|argues|argued|thinks|believes|writes|wrote|calls|called|claims|warns|insists|has said)'
VERDICTS = ('error', 'look', 'info')


# ------------------------------------------------------------------------------------------------- reading a script
def load_json(path):
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def split_cue(text):
    """(cue, the spoken text) of a page: the cue is everything from a leading '[' to its ']'."""
    stripped = text.strip()
    found = re.match(r'^(\[[^\]]*\])\s*', stripped)
    return (found.group(1), stripped[found.end():]) if found else (None, stripped)


def plain_text(script, text):
    """The spoken words as plain spelling: no cue, and every sound spelling turned back into its name."""
    _, spoken = split_cue(text)
    for sound, plain in (script.get('phonetic_names') or {}).items():
        spoken = spoken.replace(sound, plain)
    return spoken


def sentences_of(text):
    """Sentences: split after . ? ! when a capital (or a sound spelling) follows; a '...' followed by a small letter and a
    single initial ('Clara E. Mattei') do not end a sentence."""
    parts, start = [], 0
    for m in re.finditer(r'[.?!]+(?=\s+["\'(/]?[A-Z/])', text):
        before = text[max(0, m.start() - 2):m.start()]
        if re.match(r'^(\s|^)[A-Z]$', before) or re.match(r'^ [A-Z]$', before):
            continue
        parts.append(text[start:m.end()].strip())
        start = m.end()
    tail = text[start:].strip()
    if tail:
        parts.append(tail)
    return [p for p in parts if p]


def words_of(text):
    return re.findall(r"[A-Za-z0-9À-ɏɐ-ʯˈˌ'/]+(?:[-.,][A-Za-z0-9]+)*", text)


def word_key(word):
    return re.sub(r"[^a-z0-9']", '', word.lower().replace('’', "'"))


def normalised_words(text):
    return [word_key(w) for w in words_of(text) if word_key(w)]


def stem(word):
    """A rough stem for counting repeats: a plural's s comes off ('prices' -> 'price', 'factories' -> 'factory')."""
    if word.endswith("'s"):
        word = word[:-2]
    if word.endswith('ies') and len(word) > 4:
        return word[:-3] + 'y'
    if word.endswith('s') and not word.endswith('ss') and len(word) > 3:
        return word[:-1]
    return word


# ------------------------------------------------------------------------------------------------- counting
def spoken_figures(text):
    """Years, amounts, percentages, multiples and lengths of time, each counted once ('four point one percent' is one).
    A small count of things ('two factories', 'no one') is not a figure; with a unit ('two years') it is."""
    toks = re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?%?", text.lower().replace('-', ' '))
    found, i = [], 0
    while i < len(toks):
        t = toks[i]
        if re.match(r'^\d', t) or t in NUMBER_WORDS or t in CHANGES:
            j = i + 1
            while j < len(toks):
                if toks[j] in NUMBER_WORDS or re.match(r'^\d', toks[j]):
                    j += 1
                elif toks[j] in ('and', 'a', 'of') and any(x in NUMBER_WORDS for x in toks[j + 1:j + 3]) \
                        and not (toks[j] == 'and' and j + 1 < len(toks) and toks[j + 1] in SMALL | TENS and toks[j - 1] in SMALL):
                    j += 1
                elif toks[j] == 'in' and toks[j + 1:j + 3] in (['a', 'hundred'], ['a', 'thousand']):
                    j += 1
                elif toks[i] == 'one' and j == i + 1 and toks[j + 1:j + 4] == ['in', 'a', 'hundred']:
                    j += 1
                else:
                    break
            run, after = toks[i:j], toks[j] if j < len(toks) else ''
            keep = run not in (['point'], ['percent'])
            if len(run) == 1 and run[0] in SMALL:
                keep = after in UNITS or (j + 1 < len(toks) and after != 'of' and toks[j + 1] in ('dollar', 'dollars', 'percent'))
            if keep:
                found.append(' '.join(run) + (f' {after}' if after in UNITS and after not in run else ''))
            i = j
        else:
            i += 1
    return found


def years_in(text):
    """Years as written or said: '1915', 'nineteen fifteen', 'twenty twenty-one', 'twenty thirteen'."""
    found = []
    lowered = text.lower().replace('-', ' ')
    for m in re.finditer(r'\b(1[0-9]{3}|20[0-9]{2})\b|\b(nineteen|twenty) (oh \w+|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|'
                         r'seventeen|eighteen|nineteen|twenty(?: one| two| three| four| five| six| seven| eight| nine)?|thirty(?: \w+)?|'
                         r'forty(?: \w+)?|fifty(?: \w+)?|sixty(?: \w+)?|seventy(?: \w+)?|eighty(?: \w+)?|ninety(?: \w+)?)\b', lowered):
        if m.group(1):
            found.append(int(m.group(1)))
            continue
        century = 1900 if m.group(2) == 'nineteen' else 2000
        rest = m.group(3).split()
        units = {w: n for n, w in enumerate('zero one two three four five six seven eight nine'.split())}
        tens = {'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
                'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
                'eighty': 80, 'ninety': 90}
        if rest[0] == 'oh':
            value = units.get(rest[1], 0)
        else:
            value = tens.get(rest[0], 0) + (units.get(rest[1], 0) if len(rest) > 1 and rest[1] in units else 0)
        found.append(century + value)
    return found


def direction_changes(years):
    changes, direction = 0, 0
    for a, b in zip(years, years[1:]):
        if b == a:
            continue
        step = 1 if b > a else -1
        if direction and step != direction:
            changes += 1
        direction = step
    return changes


# ------------------------------------------------------------------------------------------------- timeline
def guess_page(page, sentences, settings):
    """True when the page asks the viewer to guess: marked "guess", or a guess phrase in its last two sentences."""
    if 'guess' in page:
        return bool(page['guess'])
    phrases = settings.value('script_gate.guess_phrases')
    ending = ' '.join(sentences[-2:]).lower()
    return any(p in ending for p in phrases)


def pauses_after(script, settings, default_pause):
    """Each page's pause after it: pause_after if given; else a guess hold, or the default plus a card hold."""
    pauses, why = {}, {}
    guess = settings.value('timing.guess_hold_seconds')
    hold = settings.value('timing.rule_hold_seconds')
    for page in script['pages'][:-1]:
        sentences = sentences_of(plain_text(script, page['text']))
        number = page['page']
        if 'pause_after' in page:
            pauses[number], why[number] = float(page['pause_after']), 'pause_after in the script'
        elif guess_page(page, sentences, settings):
            pauses[number], why[number] = guess, 'a guess: hold the picture still'
        elif page.get('key') or page.get('held_card'):
            pauses[number], why[number] = default_pause + hold, 'a card to read' + (' (the key page)' if page.get('key') else '')
        else:
            pauses[number], why[number] = default_pause, 'default'
    return pauses, why


def estimated_timeline(script_path, word_times, pauses, default_pause, out_path):
    """Runs estimate_timeline.py as it is, with the pauses filled in."""
    command = [sys.executable, '-I', ESTIMATE_TIMELINE, script_path, word_times, out_path, '--default-pause', str(default_pause)]
    extra = [f'{page}={seconds}' for page, seconds in pauses.items() if abs(seconds - default_pause) > 1e-9]
    if extra:
        command += ['--pause-after'] + extra
    run = subprocess.run(command, capture_output=True, text=True)
    if run.returncode != 0:
        raise SystemExit(f'lint_script: estimate_timeline.py failed: {run.stderr.strip()[-400:]}')
    return load_json(out_path), run.stdout.strip()


def page_speeds(timeline):
    rows = []
    for page in timeline['pages']:
        seconds = page['last_word_end_at'] - page['first_word_at']
        rows.append({'page': page['page'], 'words': len(page['words']), 'seconds': round(seconds, 2),
                     'words_a_minute': round(len(page['words']) / seconds * 60, 1) if seconds > 0 else None,
                     'first_word_at': page['first_word_at'], 'last_word_end_at': page['last_word_end_at']})
    return rows


# ------------------------------------------------------------------------------------------------- before recording
def lint_before(script_path, settings, word_times=None, timeline_path=None, timeline_out=None, default_pause=None, ledger=None,
                today=None, common_words=None):
    script = load_json(script_path)
    found = []

    def add(verdict, check, text, page=None, **extra):
        found.append(dict({'verdict': verdict, 'check': check, 'page': page, 'text': text}, **extra))

    pages = script['pages']
    accent = script.get('accent_instruction')
    allowed = set(settings.value('script_gate.allowed_capitals')) | set(script.get('allowed_capitals') or [])
    names = script.get('phonetic_names') or {}
    # cue, capitals, names
    cues = set()
    for page in pages:
        cue, spoken = split_cue(page['text'])
        if cue is None:
            add('error', 'cue', 'no delivery cue at the start (every page opens with the same one)', page['page'])
        else:
            cues.add(cue)
            if accent and cue != accent:
                add('error', 'cue', f'the cue {cue} is not the script\'s accent_instruction {accent}', page['page'])
        if '[' in spoken or ']' in spoken:
            add('error', 'cue', f'another bracket in the text: {spoken[spoken.find("["):spoken.find("[") + 40] or spoken[:40]} '
                                '(one cue per page, at the start; mood cues moved the voice)', page['page'])
        without_sounds = re.sub(r'/[^/\s]+/', ' ', spoken)
        for token in re.findall(r"\b[A-Z][A-Z'’]+\b", without_sounds):
            if len(re.sub(r"[^A-Z]", '', token)) >= 2 and token not in allowed:
                add('error', 'capitals', f'"{token}" in capitals (capitals make the voice push; write it plainly)', page['page'])
        for sound, plain in names.items():
            if re.search(r'\b' + re.escape(plain) + r'\b', spoken):
                add('error', 'names', f'"{plain}" in plain spelling: write it as {sound} so the voice says it right', page['page'])
    if len(cues) > 1:
        add('error', 'cue', f'{len(cues)} different cues across pages ({", ".join(sorted(cues))}): use one, the same on every page')
    used_sounds = {s for s in names if any(s in p['text'] for p in pages)}
    for sound in sorted(set(names) - used_sounds):
        add('info', 'names', f'{sound} ({names[sound]}) is never used')
    # sentences
    per_page = []
    all_sentences = []
    for page in pages:
        sentences = sentences_of(plain_text(script, page['text']))
        counts = [len(words_of(s)) for s in sentences]
        per_page.append({'page': page['page'], 'sentences': len(sentences), 'words': sum(counts),
                         'mean_words_a_sentence': round(statistics.mean(counts), 1) if counts else 0,
                         'figures': spoken_figures(plain_text(script, page['text']))})
        all_sentences += [(page['page'], s, c) for s, c in zip(sentences, counts)]
    longest = settings.value('script_gate.sentence_words_max')
    mean_max = settings.value('script_gate.sentence_words_mean_max')
    mean_words = statistics.mean(c for _, _, c in all_sentences)
    for number, sentence, count in all_sentences:
        if count > longest:
            add('error', 'sentences', f'{count} words in one sentence (at most {longest}): "{sentence[:90]}..."', number)
    if mean_words > mean_max:
        add('error', 'sentences', f'{mean_words:.1f} words a sentence on average (at most {mean_max}; aim about {settings.value("script.words_per_sentence")})')
    # main rule
    repeated = {}
    for number, sentence, count in all_sentences:
        if count >= settings.value('script_gate.repeated_sentence_words_min'):
            repeated.setdefault(' '.join(normalised_words(sentence)), set()).add(number)
    repeated = {k: sorted(v) for k, v in repeated.items() if len(v) > 1}
    rule = script.get('main_rule')
    times = settings.value('script.main_rule_said_times')
    rule_report = {'given': rule, 'repeated_sentences': repeated}
    if rule:
        rule_parts = [rule] if isinstance(rule, str) else list(rule)
        whole = ' '.join(' '.join(normalised_words(plain_text(script, p['text']))) for p in pages)
        for part in rule_parts:
            key = ' '.join(normalised_words(part))
            said = len(re.findall(r'(?:^| )' + re.escape(key) + r'(?= |$)', whole))
            rule_report.setdefault('said', {})[part] = said
            if said != times:
                add('error', 'main rule', f'the main rule is said {said} time(s) in these words, not {times}: "{part[:80]}"')
    elif repeated:
        add('look', 'main rule', 'no main_rule named; these sentences are said word for word on more than one page: '
            + '; '.join(f'"{k}" (pages {", ".join(map(str, v))})' for k, v in repeated.items()) + '. Name the rule with main_rule.')
    else:
        add('error', 'main rule', f'no sentence of {settings.value("script_gate.repeated_sentence_words_min")} or more words is said twice word for word: '
                                  f'say the main rule {times} times in identical words (log 33: said once, as one 28-word sentence)')
    key_pages = [p['page'] for p in pages if p.get('key')]
    if not key_pages:
        add('error', 'key page', 'no page is marked "key": true (the page carrying the main idea; it gets a card hold and must not be '
                                 'faster than the median page)')
    # timeline and speeds
    default_pause = settings.value('timing.default_page_pause_seconds') if default_pause is None else default_pause
    pauses, pause_why = pauses_after(script, settings, default_pause)
    timeline, estimate_line = None, ''
    if timeline_path:
        timeline = load_json(timeline_path)
    elif word_times:
        out = timeline_out or os.path.join(tempfile.mkdtemp(), 'timeline-estimated.json')
        timeline, estimate_line = estimated_timeline(script_path, word_times, pauses, default_pause, out)
    speeds = page_speeds(timeline) if timeline else []
    figures_total = sum(len(p['figures']) for p in per_page)
    speech_minutes = sum(s['seconds'] for s in speeds) / 60 if speeds else None
    if speeds:
        median = statistics.median(s['words_a_minute'] for s in speeds)
        fast = settings.value('script_gate.page_words_a_minute_max')
        share = settings.value('script_gate.page_speed_over_median_share')
        for s in speeds:
            if s['words_a_minute'] > fast:
                add('look', 'speed', f'{s["words_a_minute"]:.0f} words a minute (over {fast}): fewer words, or shorter sentences', s['page'])
            elif s['words_a_minute'] > share * median:
                add('look', 'speed', f'{s["words_a_minute"]:.0f} words a minute, over {share} x the median {median:.0f}', s['page'])
            if s['page'] in key_pages and s['words_a_minute'] > median:
                add('error', 'key page', f'the key page runs at {s["words_a_minute"]:.0f} words a minute, faster than the median page '
                                         f'({median:.0f}): give the main idea a slower page with fewer words', s['page'])
        limit = settings.value('script_gate.figures_per_minute_max')
        warn = settings.value('script_gate.figures_per_minute_look')
        rate = figures_total / speech_minutes
        if rate > limit:
            add('error', 'figures', f'{figures_total} spoken figures in {speech_minutes:.1f} minutes of speech: {rate:.1f} a minute (at most {limit})')
        elif rate > warn:
            add('look', 'figures', f'{figures_total} spoken figures, {rate:.1f} a minute of speech (over {warn}: say fewer, as people or pictures)')
        # stakes in the first seconds
        within = settings.value('script.stakes_within_seconds')
        early = []
        for page in timeline['pages']:
            for w in page['words']:
                if w['start'] - timeline['pages'][0]['first_word_at'] <= within:
                    early.append(w['text'])
        early_text = ' '.join(early)
        stake_hits = sorted({w for w in settings.value('script_gate.stake_words') if re.search(r'\b' + re.escape(w), early_text.lower())})
        add('look', 'stakes', f'the first {within} s say: "{early_text[-200:]}"; words about what is at stake: '
            + (', '.join(stake_hits) if stake_hits else 'none found') + ' (a person judges whether the stakes are said this early)')
    else:
        add('look', 'speed', 'no timeline: give --word-times (an earlier recording of the same voice) to estimate speeds and the figures a minute')
    # years
    years = [y for page in pages for y in years_in(plain_text(script, page['text']))]
    changes = direction_changes(years)
    if changes > settings.value('script_gate.year_direction_changes_max'):
        add('look', 'years', f'the years said change direction {changes} times ({", ".join(map(str, years))}): keep the cases in time order')
    # unfamiliar words, names to check, repeated words
    common = None
    if common_words:
        common = {line.strip().lower() for line in open(common_words, encoding='utf-8') if line.strip()}
    sentence_list = [(n, s) for n, s, _ in all_sentences]
    unfamiliar, names_to_check, seen = [], [], set()
    plain_names = {v.lower() for v in names.values()}
    long_letters = settings.value('script_gate.long_word_letters')
    for index, (number, sentence) in enumerate(sentence_list):
        for i, word in enumerate(words_of(sentence)):
            key = word_key(word)
            parts = [word_key(x) for x in re.split(r'[-\s]', word) if word_key(x)]
            if not key or len(key) < 2 or key in seen or key in STOP_WORDS or re.match(r'^\d', key) \
                    or all(x in NUMBER_WORDS | TENS | TEENS | SMALL for x in parts):
                continue
            after = sentence_list[index + 1][1] if index + 1 < len(sentence_list) else ''
            if word[0].isupper() and i > 0:
                seen.add(key)
                names_to_check.append({'name': word.strip(".,?!'"), 'page': number, 'sentence': sentence})
                continue
            if common is not None:
                rare = key not in common and stem(key) not in common
            else:
                rare = len(key) >= long_letters and key not in COMMON_LONG_WORDS and stem(key) not in COMMON_LONG_WORDS
            if rare and key not in plain_names:
                seen.add(key)
                unfamiliar.append({'word': word.strip(".,?!'"), 'page': number, 'sentence': sentence, 'next_sentence': after})
    if unfamiliar:
        add('look', 'unfamiliar words', f'{len(unfamiliar)} words a newcomer may not know' + (f' (no common-words list given: words of '
            f'{long_letters} letters or more are listed)' if common is None else '') + ': ' + ', '.join(u['word'] for u in unfamiliar[:40])
            + (' ...' if len(unfamiliar) > 40 else '') + '. Each needs an explanation within two sentences, or cut it.')
    if names_to_check:
        add('look', 'names', 'names and places (is each introduced? will the voice say it right?): '
            + ', '.join(dict.fromkeys(n['name'] for n in names_to_check)))
    counts = {}
    for number, sentence in sentence_list:
        for word in words_of(sentence):
            key = stem(word_key(word))
            if key and key not in STOP_WORDS and len(key) >= 4 and not re.match(r'^\d', key) and key not in NUMBER_WORDS:
                counts.setdefault(key, []).append((number, sentence))
    # every word said on two or more pages, most said first (the report shows the first 15; the JSON holds them all)
    terms = sorted(((k, v) for k, v in counts.items() if len({n for n, _ in v}) > 1), key=lambda kv: -len(kv[1]))
    term_table = [{'word': k, 'times': len(v), 'pages': sorted({n for n, _ in v}),
                   'sentences': list(dict.fromkeys(s for _, s in v))} for k, v in terms]
    if term_table:
        add('look', 'one word, one meaning', 'repeated words, to read with their sentences (each should mean one thing): '
            + ', '.join(f'{t["word"]} x{t["times"]}' for t in term_table[:15]))
    # speakers and the ledger
    speakers = []
    for number, sentence in sentence_list:
        m = re.search(r"([A-Z][\w'’.]*(?:\s+[A-Z][\w'’.]*)*|[Ss]he|[Hh]e|[Tt]hey|[Ii]t)\s+" + SPEAKING_VERBS + r'\b', sentence)
        if m:
            speakers.append({'page': number, 'who': m.group(1), 'sentence': sentence})
    if ledger:
        claims = {c['id']: c for c in ledger.get('claims', [])}
        today_date = date.fromisoformat(today) if today else date.today()
        for claim in claims.values():
            if claim.get('valid_until') and date.fromisoformat(claim['valid_until']) < today_date:
                pages_using = [p['page'] for p in pages if claim['id'] in (p.get('ledger') or [])]
                add('error', 'out-of-date facts', f'{claim["id"]} ("{claim.get("claim", "")[:70]}") was due to change on {claim["valid_until"]}: '
                    f'check it again before recording' + (f' (pages {", ".join(map(str, pages_using))})' if pages_using else ''))
        for s in speakers:
            page = next(p for p in pages if p['page'] == s['page'])
            sources = [claims[i] for i in (page.get('ledger') or []) if i in claims]
            said_by = [c.get('said_by', '') for c in sources if c.get('said_by')]
            who = s['who'].lower()
            if said_by and not any(who in sb.lower() or sb.lower() in who for sb in said_by) and who not in ('she', 'he', 'they', 'it'):
                add('look', 'who says it', f'"{s["who"]}" speaks here, but the page\'s ledger sources are by {", ".join(said_by)}: '
                    f'"{s["sentence"][:80]}"', s['page'])
    if speakers:
        add('info', 'who says it', 'lines that quote someone (check each against its source): '
            + '; '.join(f'page {s["page"]}: {s["who"]}' for s in speakers))
    # cost
    characters = sum(len(p['text']) for p in pages)
    credits = characters * settings.value('money.elevenlabs_credits_per_letter')
    dollars = credits * settings.value('money.elevenlabs_dollars_per_credit')
    pause_lines = {str(k): {'seconds': v, 'why': pause_why[k]} for k, v in pauses.items()}
    for number, entry in pause_lines.items():
        if entry['why'].startswith('a guess'):
            add('info', 'guess holds', f'ends on a guess: {entry["seconds"]} s held after it (hold the shot still through it)', int(number))
    for page in pages:
        sentences = sentences_of(plain_text(script, page['text']))
        if page is not pages[-1] and sentences and sentences[-1].endswith('?') and not guess_page(page, sentences, settings) \
                and 'pause_after' not in page:
            add('look', 'guess holds', f'ends on a question without a guess phrase ("{sentences[-1][:60]}"): if the viewer should '
                                       'think, end with "Have a guess." or mark "guess": true', page['page'])
    errors = [f for f in found if f['verdict'] == 'error']
    return {'script': script_path, 'pages': len(pages), 'problems': found, 'errors': len(errors),
            'verdict': 'fix before recording' if errors else 'ready to record (after a person reads the lists)',
            'per_page': per_page, 'figures': figures_total, 'speech_minutes': round(speech_minutes, 2) if speech_minutes else None,
            'figures_per_minute': round(figures_total / speech_minutes, 2) if speech_minutes else None,
            'mean_words_a_sentence': round(mean_words, 2), 'longest_sentence_words': max(c for _, _, c in all_sentences),
            'main_rule': rule_report, 'key_pages': key_pages, 'pauses_after_page': pause_lines, 'speeds': speeds,
            'median_words_a_minute': statistics.median(s['words_a_minute'] for s in speeds) if speeds else None,
            'timeline_seconds': timeline.get('chapter_seconds') if timeline else None, 'estimate_timeline_said': estimate_line,
            'timeline_out': timeline_out, 'years': years, 'year_direction_changes': changes, 'unfamiliar_words': unfamiliar,
            'term_table': term_table, 'names_to_check': names_to_check, 'speakers': speakers, 'characters': characters, 'credits': credits, 'dollars': round(dollars, 2)}


# ------------------------------------------------------------------------------------------------- after recording
def read_transcripts(path, pages):
    if os.path.isdir(path):
        found = {}
        for page in pages:
            file = os.path.join(path, f'page{page["page"]}-words.json')
            if os.path.exists(file):
                found[page['page']] = load_json(file)['words']
        return found
    data = load_json(path)
    return {page['page']: t['words'] for page, t in zip(pages, data['transcripts'])}


def voice_loudness(recording):
    """10 ms loudness (dB) of a recording, as extract_word_times.py measures where a voice begins."""
    import numpy
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', recording, '-ac', '1', '-ar', '48000', '-f', 'f32le', '-'], check=True,
                         capture_output=True).stdout
    samples = numpy.frombuffer(raw, dtype=numpy.float32)
    window = 480
    count = len(samples) // window
    return 20 * numpy.log10(numpy.sqrt((samples[:count * window].reshape(count, window) ** 2).mean(axis=1)) + 1e-9)


def late_after_silence(loudness, words, silence, tolerance, below=35.0):
    """Words that start after a silence of `silence` seconds or more (and the first word), whose voice really began
    earlier than the transcript says by more than `tolerance`: [{text, start, voice_starts, late_by}]."""
    import numpy
    loud = loudness > loudness.max() - below
    found = []
    for i, word in enumerate(words):
        gap_start = words[i - 1]['end'] if i else 0.0
        if i and word['start'] - gap_start < silence:
            continue
        a, b = int(round(gap_start * 100)), int(round(word['start'] * 100))
        if b <= a:
            continue
        quiet = numpy.where(~loud[a:b])[0]
        if not len(quiet):
            continue
        onset = a + quiet[-1] + 1
        voiced = numpy.where(loud[onset:b])[0]
        if not len(voiced):
            continue
        starts = (onset + voiced[0]) * 0.01
        if word['start'] - starts > tolerance:
            found.append({'text': word['text'], 'start': word['start'], 'voice_starts': round(float(starts), 3), 'late_by': round(float(word['start'] - starts), 3),
                          'first_word': i == 0})
    return found


def longest_quiet(loudness, start, end, below=35.0):
    """The longest stretch (seconds) between start and end where the recording is quiet (35 dB under its loudest 10 ms)."""
    if loudness is None:
        return None
    a, b = int(round(start * 100)), int(round(end * 100))
    quiet = loudness[a:b] <= loudness.max() - below
    best = run = 0
    for q in quiet:
        run = run + 1 if q else 0
        best = max(best, run)
    return float(best * 0.01)


def lint_after(script_path, settings, transcripts, recordings=None, heard=None):
    script = load_json(script_path)
    pages = script['pages']
    words_by_page = read_transcripts(transcripts, pages)
    heard_by_page = read_transcripts(heard, pages) if heard else {}
    names = script.get('phonetic_names') or {}
    cue_max = settings.value('timing.bracket_cue_max_seconds')
    pause_min = settings.value('timing.thinking_pause_min_seconds')
    silence = settings.value('script_gate.silence_before_late_word_seconds')
    tolerance = settings.value('timing.first_word_tolerance_seconds')
    rows, rerecord = [], {}
    pause_gaps = []
    for page in pages:
        number = page['page']
        row = {'page': number, 'problems': [], 'look': []}
        words = [w for w in words_by_page.get(number, []) if w.get('type', 'word') == 'word']
        if not words:
            row['problems'].append('no transcript')
            rows.append(row)
            rerecord[number] = 'no transcript'
            continue
        cue, spoken_text = split_cue(page['text'])
        cue_words = len(cue.split()) if cue else 0
        cue_part, spoken = words[:cue_words], words[cue_words:]
        if cue_part:
            # a cue word read aloud lasts like a spoken word (about 0.37 s at 164 words a minute); unspoken cue words last
            # 0.004-0.16 s (20 pages of chapters 1 and 2). The whole cue can stretch to a late-placed first word (0.5 s on
            # chapter 2's page 6, where the voice began at 0.04 s), so each word is judged, by the middle one
            lengths = sorted(w['end'] - w['start'] for w in cue_part)
            middle = statistics.median(lengths)
            row['cue_seconds'] = round(cue_part[-1]['end'] - cue_part[0]['start'], 3)
            row['cue_word_median_seconds'] = round(middle, 3)
            if middle > cue_max:
                row['problems'].append(f'the cue\'s words last {middle:.2f} s each (over {cue_max} s): it was read aloud')
        expected = normalised_words(spoken_text)
        got = [word_key(w['text']) for w in spoken]
        if got != expected:
            row['problems'].append(f'the transcript\'s words differ from the script ({len(got)} against {len(expected)} words)')
        if heard_by_page.get(number):
            heard_words = [word_key(w['text']) for w in heard_by_page[number] if w.get('type', 'word') == 'word']
            plain_expected = normalised_words(plain_text(script, page['text']))
            import difflib
            matcher = difflib.SequenceMatcher(a=plain_expected, b=heard_words, autojunk=False)
            for op, a1, a2, b1, b2 in matcher.get_opcodes():
                if op == 'equal':
                    continue
                said_wrong = plain_expected[a1:a2]
                heard_as = heard_words[b1:b2]
                plain_names = {word_key(v) for v in names.values()}
                if any(w in plain_names for w in said_wrong):
                    row['problems'].append(f'a name was heard as "{" ".join(heard_as)}" (script: "{" ".join(said_wrong)}")')
                elif cue and any(w in normalised_words(cue) for w in heard_as):
                    row['problems'].append(f'cue words were spoken: "{" ".join(heard_as)}"')
                else:
                    row['look'].append(f'heard "{" ".join(heard_as)}" where the script has "{" ".join(said_wrong)}"')
        loudness = None
        if recordings:
            recording = os.path.join(recordings, f'page{number}.mp3')
            if not os.path.exists(recording):
                row['problems'].append(f'no recording at {recording} (download each page at once: the links stop working)')
            else:
                loudness = voice_loudness(recording)
                late = late_after_silence(loudness, spoken, silence, tolerance)
                row['late_words'] = late
                for item in late:
                    row['look'].append(f'"{item["text"]}" starts {item["late_by"]:.2f} s late (voice at {item["voice_starts"]:.2f} s)'
                                       + (' - extract_word_times.py moves the first word back' if item['first_word'] else ''))
        for i, w in enumerate(spoken[:-1]):
            if w['text'].endswith('...') or w['text'].endswith('\u2026'):
                # the transcript puts the pause inside the word, so the word's start to the next word is the most the pause can be;
                # with the recording, the longest quiet stretch in between is measured
                upper = spoken[i + 1]['start'] - w['start']
                quiet = longest_quiet(loudness, w['start'], spoken[i + 1]['start']) if loudness is not None else None
                pause_gaps.append({'page': number, 'word': w['text'], 'word_and_gap': round(upper, 3),
                                   'silence': None if quiet is None else round(quiet, 3)})
                shown = quiet if quiet is not None else upper
                if shown < pause_min:
                    row['look'].append(f'"{w["text"]}" leaves ' + (f'{quiet:.2f} s of silence' if quiet is not None else
                                       f'at most {upper:.2f} s from the word to the next') + f' (a thinking pause needs {pause_min} s: hold the picture instead)')
        if row['problems']:
            rerecord[number] = '; '.join(row['problems'])
        rows.append(row)
    credits = sum(len(p['text']) for p in pages if p['page'] in rerecord) * settings.value('money.elevenlabs_credits_per_letter')
    return {'script': script_path, 'pages': rows, 'rerecord': rerecord, 'rerecord_credits': credits,
            'rerecord_dollars': round(credits * settings.value('money.elevenlabs_dollars_per_credit'), 2), 'thinking_pauses': pause_gaps,
            'verdict': 'record again: ' + ', '.join(map(str, rerecord)) if rerecord else 'no page needs recording again'}


# ------------------------------------------------------------------------------------------------- report
def report_before(result):
    lines = [f'Script check before recording: {result["script"]} ({result["pages"]} pages): {result["verdict"].upper()}']
    lines.append(f'  sentences: {result["mean_words_a_sentence"]:.1f} words on average, longest {result["longest_sentence_words"]}')
    if result['figures_per_minute'] is not None:
        lines.append(f'  spoken figures: {result["figures"]} in {result["speech_minutes"]:.1f} minutes of speech ({result["figures_per_minute"]:.1f} a minute)')
    else:
        lines.append(f'  spoken figures: {result["figures"]}')
    if result['speeds']:
        lines.append(f'  speed: median page {result["median_words_a_minute"]:.0f} words a minute; chapter {result["timeline_seconds"]:.1f} s')
        lines.append('  page  words  seconds  words a minute')
        for s in result['speeds']:
            lines.append(f'  {s["page"]:4d}  {s["words"]:5d}  {s["seconds"]:7.1f}  {s["words_a_minute"]:6.0f}'
                         + ('  (key)' if s['page'] in result['key_pages'] else ''))
    holds = {k: v for k, v in result['pauses_after_page'].items() if v['why'] != 'default'}
    if holds:
        lines.append('  pauses after pages: ' + ', '.join(f'{k}: {v["seconds"]} s ({v["why"]})' for k, v in holds.items()))
    lines.append(f'  recording: {result["characters"]:,} letters = about {result["credits"]:,.0f} credits, about US${result["dollars"]:.2f} '
                 '(an estimate by text length; ask the user before recording)')
    for verdict in VERDICTS:
        for p in result['problems']:
            if p['verdict'] == verdict:
                lines.append(f'{verdict.upper():5s} {p["check"]}' + (f', page {p["page"]}' if p['page'] else '') + f': {p["text"]}')
    if result['timeline_out']:
        lines.append(f'Estimated timeline written to {result["timeline_out"]}')
    return lines


def report_after(result):
    lines = [f'Recording check: {result["script"]}: {result["verdict"].upper()}']
    for row in result['pages']:
        for p in row['problems']:
            lines.append(f'RE-RECORD page {row["page"]}: {p}')
        for p in row['look']:
            lines.append(f'LOOK  page {row["page"]}: {p}')
    if result['thinking_pauses']:
        short = [p for p in result['thinking_pauses'] if (p['silence'] if p['silence'] is not None else p['word_and_gap']) < 1.0]
        lines.append(f'"..." pauses: {len(result["thinking_pauses"])}, of which {len(short)} leave under 1 s of silence '
                     f'(the word and its pause last {min(p["word_and_gap"] for p in result["thinking_pauses"]):.2f} to '
                     f'{max(p["word_and_gap"] for p in result["thinking_pauses"]):.2f} s)')
    if result['rerecord']:
        lines.append(f'Re-recording these pages: about {result["rerecord_credits"]:,.0f} credits, about US${result["rerecord_dollars"]:.2f}; ask first.')
    return lines


def main():
    parser = argparse.ArgumentParser(description='Checks a narration script before recording, and the recordings after '
                                                 '(see the note at the top of this file).')
    sub = parser.add_subparsers(dest='command', required=True)
    p = add_output_options(sub.add_parser('before', help='check a script before paying for the voice'))
    p.add_argument('script')
    p.add_argument('--word-times', help='an earlier word-times file of the same voice (for the estimated timeline)')
    p.add_argument('--timeline', help='judge speeds on this timeline instead of estimating one')
    p.add_argument('--timeline-out', help='where to write the estimated timeline')
    p.add_argument('--default-pause', type=float, help='seconds between pages (default: film-settings.json timing.default_page_pause_seconds)')
    p.add_argument('--ledger')
    p.add_argument('--today', help='the date to judge valid_until against (default: today)')
    p.add_argument('--common-words')
    p = add_output_options(sub.add_parser('after', help='check the recordings and transcripts'))
    p.add_argument('script')
    p.add_argument('--transcripts', required=True, help='a folder of pageN-words.json, or ElevenLabs\' status reply')
    p.add_argument('--recordings', help='the folder of pageN.mp3')
    p.add_argument('--heard', help='a folder of speech-to-text transcripts (pageN-words.json) of what was actually heard')
    args = parser.parse_args()
    settings = load_settings(args.settings)
    if args.command == 'before':
        result = lint_before(args.script, settings, args.word_times, args.timeline, args.timeline_out, args.default_pause,
                             load_json(args.ledger) if args.ledger else None, args.today, args.common_words)
        lines = report_before(result)
        code = 1 if result['errors'] else 0
    else:
        result = lint_after(args.script, settings, args.transcripts, args.recordings, args.heard)
        lines = report_after(result)
        code = 1 if result['rerecord'] else 0
    finish(f'lint_script {args.command}', result, lines, settings, args)
    return code


if __name__ == '__main__':
    sys.exit(main())
