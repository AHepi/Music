"""What this does: works out, from a page's own events, everything about WHEN things happen on a cinema page, which
this project used to find by hand for every page (logs 07-34):
  - word lookups that leave out which time a word is said, for a word said more than once on the page (lessons 12,
    28, 46): each is listed with every time the word is said and three words either side;
  - the pause each page needs after its last word: its join's wait plus the join's length plus about 0.15 s to settle,
    and any hold (a guess ring's 4 s), clamped to 1.1-1.7 s only for a plain peel (skeptic, log 35); checked against
    the timeline, written as --pauses for assemble_chapter_narration.py and --pause-after for estimate_timeline.py;
    a run-on join must join the same view, and every join must end at least 0.1 s before the next page's first word;
  - how long each group of words is readable at full strength before it goes or the picture cuts (at least 1 s), with
    each kind's appear delay taken from graphics.js (buildWords 0.14 s, a label 0.55 s or 0.12 s with wordsWithLine);
    a conclusion (words starting with an arrow) must be up 1.2 s before the cut; when it is short, the earlier word of
    its sentence it could start on;
  - words that end on a cut but fade a frame early (they need fadeOut 0), and a new line drawn where another is still
    fading (round 3, NO SPARE);
  - margins: no letter left of 65 px or right of 972 px (0.90 across), no letter top above 0.06 down, nothing to read
    below 0.80 down, typed lines in the top band;
  - every typed word against the narration (said on the page, near its moment; numbers as words), numbers against the
    research ledger (within half the last shown digit, with its "up to" or "about"), a counting number finished on its
    word and held still long enough to read;
  - word groups per page, slides tied to words 2.6-4.1 s apart, stretches where nothing at all changes while she talks;
  - the stills to check (every event, each move's start, middle and end, each cut, each page turn in one run) as a
    render-paper-film.mjs command, and the planned cuts to give find_jumps.py;
  - after a re-record: which pages moved and which filmed chunks to delete and film again (refilm).
The events come from paper-film/tools/page_events.mjs, which runs the pages without filming them.

Use:
  python3 plan_page_timing.py check EVENTS.json[.gz] [--ledger LEDGER.json] [--accepted ACCEPTED.json] [--film-start S]
        [--conclusion "PRICES UP" ...] [--scene NAME]
  python3 plan_page_timing.py lookups TIMELINE.json PAGE_FILE.js:PAGE_NUMBER ...   (no browser: reads the page files)
  python3 plan_page_timing.py refilm OLD_TIMELINE.json NEW_TIMELINE.json --chunks FOLDER_OR_LIST [--fps 30]
  python3 plan_page_timing.py delays [--graphics paper-film/scenes/graphics.js]
--ledger    the numbers a film may show: {"numbers": [{"id": "C2-H3", "value": 0.95, "unit": "%", "qualifier": "under",
            "said": "under one percent", "source": "..."}], "not_claims": ["FACTORY 1"]} (unit one of %, $, x, count,
            year; qualifier: a word the screen must keep; not_claims: words on screen whose numbers name things)
--accepted  problems the project chose to keep: [{"check": "readable", "page": 3, "text": "MACHINES", "reason": ...,
            "who": ..., "date": ...}]; a matching problem is reported as known, not failed
--film-start  the chapter second a filmed piece starts at, for the find_jumps.py command (default: the events' start)
--conclusion  words to treat as a page's conclusion (besides any part starting with an arrow)
Every command takes --json, --out FILE, --report FILE and --settings FILE, and names the film-settings.json values it
used. check and lookups exit 1 when anything fails; 0 otherwise.
"""
import argparse
import glob
import gzip
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings  # noqa: E402
from calculator_output import add_output_options, finish, run_main  # noqa: E402

KIT = os.path.dirname(HERE)
GRAPHICS_JS = os.path.join(KIT, 'paper-film', 'scenes', 'graphics.js')
WORD_KINDS = ('words', 'label', 'tag', 'hook', 'counter', 'title', 'credit')   # things whose words must be read
VERDICT_ORDER = {'fail': 0, 'look': 1, 'known': 2, 'info': 3, 'pass': 4}


# ------------------------------------------------------------------------------------------------- small helpers
def word_key(text):
    """The same matching the kit's wordClock uses: lowercase, keep letters, digits, ' and dots, drop trailing dots."""
    return re.sub(r'\.+$', '', re.sub(r"[^a-z0-9'.]", '', text.lower()))


def plain(text):
    return re.sub(r"[^a-z0-9\-']", '', text.lower().replace('\u2019', "'").replace('\u2018', "'"))


def load_json(path):
    """A JSON file, or a gzipped one (.gz)."""
    with (gzip.open(path, 'rt') if path.endswith('.gz') else open(path)) as handle:
        return json.load(handle)


def fmt(seconds):
    return 'never' if seconds is None else f'{seconds:.2f} s'


def problem(check, verdict, page, text, detail, fix='', **numbers):
    entry = {'check': check, 'verdict': verdict, 'page': page, 'text': text, 'detail': detail, 'fix': fix}
    entry.update(numbers)
    return entry


def context_words(words, index, either_side=3):
    before = ' '.join(w['text'] for w in words[max(0, index - either_side):index])
    after = ' '.join(w['text'] for w in words[index + 1:index + 1 + either_side])
    return f'...{before} [{words[index]["text"]}] {after}...'.replace('... ', '...').replace(' ...', '...')


def read_appear_delays(path=GRAPHICS_JS):
    """APPEAR_DELAYS from graphics.js: the named fade-in numbers (const NAME = 0.14, ...) and the table that sums them."""
    source = open(path).read()
    numbers = {}
    for declaration in re.findall(r'^const ([A-Z_][A-Z0-9_ ,=.]*?);', source, flags=re.M):
        for name, value in re.findall(r'([A-Z_][A-Z0-9_]*)\s*=\s*([0-9.]+)', declaration):
            numbers[name] = float(value)
    table = re.search(r'export const APPEAR_DELAYS = \{(.*?)\n\};', source, flags=re.S)
    if not table:
        raise SystemExit(f'{path} has no APPEAR_DELAYS table (the plugin kit\'s graphics.js has one)')
    delays = {}
    for key, expression in re.findall(r'^\s*([A-Za-z]+):\s*([^,\n]+),', table.group(1), flags=re.M):
        total = 0.0
        for term in expression.split('+'):
            term = term.strip()
            total += numbers[term] if term in numbers else float(term)
        delays[key] = round(total, 6)
    return delays


# ---------------------------------------------------------------------------------------------- reading the events
class Events:
    def __init__(self, data):
        self.data = data
        self.fps = data['fps']
        self.zero = data['frame_zero_seconds']
        self.width, self.height = data['frame_size']
        self.pages = {p['number']: p for p in data['pages']}
        self.order = [p['number'] for p in data['pages']]
        self.items = data['items']
        self.frames = data['frames']
        self.delays = data['appear_delays']
        self.sampled_pages = sorted({p['page'] for row in self.frames for p in row['pages']})
        self.asked_pages = data.get('pages_asked') or self.sampled_pages
        self._cuts = None

    def time(self, frame):
        return self.zero + frame / self.fps

    def frame(self, seconds):
        return int(math.ceil((seconds - self.zero) * self.fps - 1e-6))

    def next_page(self, number):
        index = self.order.index(number)
        return self.pages[self.order[index + 1]] if index + 1 < len(self.order) else None

    def previous_page(self, number):
        index = self.order.index(number)
        return self.pages[self.order[index - 1]] if index > 0 else None

    def cuts(self):
        """Planned cuts: a page's shot changing (the picture changes at once), its own still value stepping while the
        camera holds (a time cut, a window step), and the joins between pages. [{page, t, frame, kind, what}]"""
        if self._cuts is not None:
            return self._cuts
        cuts, last = [], {}
        for row in self.frames:
            for p in row['pages']:
                before = last.get(p['page'])
                if before and before['f'] == row['f'] - self.data.get('step', 1):
                    if p['shot'] != before['shot']:
                        cuts.append({'page': p['page'], 't': row['t'], 'frame': row['f'], 'kind': 'shot', 'what': f'cut to {p["shot"]}'})
                    elif (p['page_still'] != before['page_still'] and p['page_still'] is not None and before['page_still'] is not None
                          and p['camera'] == before['camera']):
                        cuts.append({'page': p['page'], 't': row['t'], 'frame': row['f'], 'kind': 'state', 'what': 'held picture steps',
                                     'from': before['page_still'], 'to': p['page_still']})
                last[p['page']] = {'f': row['f'], 'shot': p['shot'], 'page_still': p['page_still'], 'camera': p['camera']}
        for number in self.sampled_pages:
            join = self.pages[number].get('join')
            if join and self.next_page(number):
                cuts.append({'page': number, 't': join['start'], 'frame': self.frame(join['start']), 'kind': f'join ({join["kind"]})',
                             'what': f'page {number} starts to leave ({join["kind"]}, {join["length"]:.2f} s)', 'end': join['end']})
        self._cuts = sorted(cuts, key=lambda c: c['t'])
        return self._cuts

    def picture_cuts_after(self, page, seconds):
        """The next moment the page's picture is replaced at once or begins to leave: a shot change or a join start."""
        # a cut within a frame after `seconds` is the same moment (words that come in with a cut are drawn from it)
        later = [c['t'] for c in self.cuts() if c['page'] == page and c['t'] > seconds + 1.0 / self.fps + 1e-6
                 and (c['kind'] == 'shot' or (c['kind'].startswith('join') and 'run-on' not in c['kind']))]
        return min(later) if later else None

    @staticmethod
    def strength_at(item, point):
        if item['kind'] in ('label', 'title') and point[3] is not None:
            return point[3]
        if item['kind'] == 'arrow' and point[3] is not None:
            return point[3]
        return point[1]

    def points_by_frame(self, item):
        """Every sampled frame the item is drawn in, with its track values at that frame."""
        step = self.data.get('step', 1)
        track = item['track']
        out, index = [], 0
        for start, end in item['runs']:
            for frame in range(start, end + 1, step):
                while index + 1 < len(track) and track[index + 1][0] <= frame:
                    index += 1
                out.append((frame, track[index]))
        return out

    def full_stretch(self, item, full=0.99, before=None):
        """(first frame at full strength, last frame at full strength in the first unbroken stretch) or None. Full strength
        is measured against the item's own strongest frame (a credit is drawn at 0.9 at most); `before`: stop there."""
        points = self.points_by_frame(item)
        peak = max((self.strength_at(item, p) for _, p in points), default=0)
        first = last = None
        for frame, point in points:
            if before is not None and self.time(frame) >= before - 1e-6:
                break
            if peak > 0 and self.strength_at(item, point) >= full * peak:
                if first is None:
                    first = frame
                last = frame
            elif first is not None:
                break
        return (first, last) if first is not None else None

    def boxes(self, item, at_least=0.1):
        return [point[2] for _, point in self.points_by_frame(item) if point[2] and self.strength_at(item, point) >= at_least]

    def carried(self, item):
        """Drawn by a page but put up before the page's first word (a page that runs on repeats the last page's words)."""
        page = self.pages[item['page']]
        return item.get('at') is not None and item['at'] < page['first_word_at'] - 1.0


# ------------------------------------------------------------------------------------------------------- lookups
def check_lookups(lookups, settings, pages_wanted=None):
    out = []
    for look in lookups:
        if pages_wanted and look['page'] not in pages_wanted:
            continue
        said = look['said']
        asked = f"kit.{look['which']}('{look['word']}'" + (f", {look['n']})" if look['n'] is not None else ')')
        where = re.sub(r'^.*?/paper-film/scenes/', '', look.get('asked_from') or '')
        where = re.sub(r'^\S+ \(', '', where).rstrip(')')
        if look['n'] is None and len(said) > 1:
            times = ', '.join(f"{w['start']:.2f}" for w in said)
            out.append(problem('lookups', 'fail', look['page'], look['word'],
                               f"{asked} ({where}) leaves out which time: \"{look['word']}\" is said {len(said)} times on page {look['page']} "
                               f"({times}); it takes the first, {look['start']:.2f}.",
                               f"write kit.{look['which']}('{look['word']}', N) with the time you mean (1 for the first).",
                               said=[{'start': w['start'], 'words': w.get('context', w['text'])} for w in said], took=look['start'], asked_from=where))
        else:
            out.append(problem('lookups', 'pass', look['page'], look['word'], f'{asked} -> {look["start"]:.2f} ({where})'))
    return out


STATIC_LOOKUP = re.compile(r"""\b(?:kit|this)\.(at|end)\(\s*(['"])(.+?)\2\s*(?:,\s*(\d+)\s*)?\)""")


def lookups_from_page_files(timeline, page_files):
    """The lookups a page file asks for, read from its text (no browser): [(page, which, word, n, line)]."""
    pages = {p['page']: p for p in timeline['pages']}
    lookups = []
    for spec in page_files:
        path, _, number = spec.rpartition(':')
        if not path or not number.isdigit():
            raise SystemExit(f'give each page file as FILE.js:PAGE_NUMBER (got {spec})')
        number = int(number)
        if number not in pages:
            raise SystemExit(f'the timeline has no page {number}')
        words = pages[number]['words']
        for line_number, line in enumerate(open(path), 1):
            for which, _, word, n in STATIC_LOOKUP.findall(line):
                said = [dict(w, context=context_words(words, i)) for i, w in enumerate(words) if word_key(w['text']) == word_key(word)]
                n = int(n) if n else None
                found = said[(n or 1) - 1] if len(said) >= (n or 1) else None
                lookups.append({'page': number, 'which': which, 'word': word, 'n': n, 'start': found['start'] if found else None,
                                'said': said, 'asked_from': f'{os.path.basename(path)}:{line_number}'})
    return lookups


def add_contexts(lookups, events):
    for look in lookups:
        words = events.pages.get(look['page'], {}).get('words', [])
        for w in look['said']:
            index = next((i for i, x in enumerate(words) if abs(x['start'] - w['start']) < 1e-6), None)
            if index is not None:
                w['context'] = context_words(words, index)
    return lookups


# ---------------------------------------------------------------------------------------------- pauses and joins
def check_pauses(events, settings):
    settle = settings.value('page_timing.settle_after_join_seconds')
    clear = settings.value('page_timing.join_clear_of_next_word_seconds')
    low, high = settings.value('timing.page_pause_range_seconds')
    plain_wait = settings.value('timing.turn_after_last_word_seconds')
    guess_hold = settings.value('timing.guess_hold_seconds')
    longer_by = settings.value('page_timing.pause_longer_than_needed_seconds')
    rows, out = [], []
    for number in events.order[:-1]:
        page, following = events.pages[number], events.next_page(number)
        join = page['join'] or {'kind': 'peel', 'after': plain_wait, 'length': settings.value('timing.peel_length_seconds')}
        needed = join['after'] + join['length'] + settle
        rings = [i for i in events.items if i['page'] == number and i['kind'] == 'ring' and not events.carried(i)]
        hold = guess_hold if rings else 0.0
        plain_peel = join['kind'] == 'peel' and abs(join['after'] - plain_wait) < 1e-6 and not hold
        recommended = max(needed, hold)
        if plain_peel:
            recommended = min(high, max(low, recommended))
        actual = following['first_word_at'] - page['last_word_end_at']
        clear_by = following['first_word_at'] - (page['last_word_end_at'] + join['after'] + join['length'])
        row = {'page': number, 'next_page': following['number'], 'join': join['kind'], 'join_after': join['after'], 'join_length': join['length'],
               'hold': hold, 'needed': round(needed, 3), 'recommended': round(recommended, 3), 'in_timeline': round(actual, 3),
               'join_clear_of_next_word': round(clear_by, 3), 'sampled': number in events.sampled_pages, 'plain_peel': plain_peel}
        rows.append(row)
        if number not in events.asked_pages and following['number'] not in events.asked_pages:
            continue   # only the pages looked at (and the joins into and out of them) are judged
        label = f'page {number} -> {following["number"]}'
        why = (f'{join["kind"]} {join["after"]:.2f} s after the last word, {join["length"]:.2f} s long, + {settle:.2f} s to settle'
               + (f'; guess hold {hold:.1f} s' if hold else '') + ('; a plain peel, kept within 1.1-1.7 s' if plain_peel else ''))
        if clear_by < clear - 1e-6:
            out.append(problem('pauses', 'fail', number, label, f'the join ends {clear_by:.2f} s before page {following["number"]}\'s first word '
                               f'(needs at least {clear:.2f}); pause in the timeline {actual:.2f} s, needed {recommended:.2f} s ({why})',
                               f'make the pause after page {number} at least {recommended:.2f} s', gap=row))
        elif rings and any((r.get('filledAt') or 0) > following['first_word_at'] for r in rings):
            out.append(problem('pauses', 'fail', number, label, f'the guess ring is not full before page {following["number"]}\'s first word',
                               f'make the pause after page {number} at least {recommended:.2f} s', gap=row))
        elif actual > recommended + longer_by:
            out.append(problem('pauses', 'info', number, label, f'pause {actual:.2f} s is {actual - recommended:.2f} s longer than this join needs '
                               f'({recommended:.2f} s: {why}); the extra time is a rest before the next page', gap=row))
        else:
            out.append(problem('pauses', 'pass', number, label, f'pause {actual:.2f} s; needs {recommended:.2f} s ({why})', gap=row))
    # a run-on join must hand over the same view; the same view across a peel looks like a fault
    for number in events.sampled_pages:
        page, following = events.pages[number], events.next_page(number)
        if not following or following['number'] not in events.sampled_pages or not page.get('join'):
            continue
        join = page['join']
        before = [p['camera'] for row in events.frames if row['t'] < join['start'] for p in row['pages'] if p['page'] == number]
        after = [p['camera'] for row in events.frames if row['t'] >= join['start'] for p in row['pages'] if p['page'] == following['number']]
        if not before or not after:
            continue
        same = max(abs(a - b) for a, b in zip(before[-1], after[0])) < 1e-3
        label = f'page {number} -> {following["number"]} join'
        if join['kind'] == 'run-on' and not same:
            out.append(problem('joins', 'fail', number, label, 'a run-on join (a plain blend) between two different views: the blend shows',
                               'use a peel or dissolve, or start the next page on the same view and frame'))
        elif join['kind'] != 'run-on' and same:
            out.append(problem('joins', 'look', number, label, f'the next page starts on the same view and frame, but the join is a {join["kind"]}',
                               "use the 'run-on' join (a plain blend with no dip): a peel over an unchanged picture looks like a fault"))
        else:
            out.append(problem('joins', 'pass', number, label, f'{join["kind"]}; ' + ('the same view runs on' if same else 'a new view')))
    return out, rows


# ------------------------------------------------------------------------------------------------- readable times
def earlier_word(page, item_at, needed_from_cut, cut, delay):
    """The latest earlier word of the same sentence the item could start on and be readable long enough."""
    words = page['words']
    index = next((i for i, w in enumerate(words) if abs(w['start'] - item_at) < 0.02), None)
    if index is None:
        return None
    for i in range(index - 1, -1, -1):
        if re.search(r'[.?!]$', words[i]['text']) or words[i]['text'].endswith('...'):
            break
        if cut - (words[i]['start'] + delay) >= needed_from_cut - 1e-6:
            return words[i]
    return None


def check_readable(events, settings, conclusions=()):
    least = settings.value('timing.label_readable_min_seconds')
    conclusion_up = settings.value('page_timing.conclusion_on_screen_seconds')
    one_frame = 1.0 / events.fps
    out = []
    for item in events.items:
        if item['page'] not in events.asked_pages or item['kind'] not in WORD_KINDS + ('arrow',) or not item.get('text'):
            continue
        if events.carried(item):
            continue
        page = events.pages[item['page']]
        at = item['at']
        full_at = item.get('fullAt')
        cut = events.picture_cuts_after(item['page'], at)
        until = item.get('until')
        fade_out = item.get('fadeOut') or 0
        ends = [x for x in (cut, (until - fade_out) if until is not None else None) if x is not None]
        leaves = min(ends) if ends else None
        stretch = events.full_stretch(item, before=leaves)
        measured = ((stretch[1] - stretch[0] + 1) / events.fps) if stretch else 0.0
        formula = (leaves - full_at) if (leaves is not None and full_at is not None) else None
        label = item['text']
        numbers = {'at': at, 'full_at': full_at, 'leaves': leaves, 'cut': cut, 'readable_measured': round(measured, 3),
                   'readable_formula': round(formula, 3) if formula is not None else None, 'fn': item['fn']}
        if item['kind'] == 'arrow':
            out.append(problem('readable', 'info', item['page'], f'{label} (word on an arrow)', f'readable {measured:.2f} s (it names the arrow; not counted)', **numbers))
            continue
        is_conclusion = label.startswith('→') or any(c.lower() in label.lower() for c in conclusions)
        if leaves is None or (until is None and cut is None):
            out.append(problem('readable', 'pass', item['page'], label, f'up from {fmt(full_at)} until the page leaves', **numbers))
            continue
        verdicts = []
        if formula is not None and formula < least - 1e-6:
            delay = full_at - at
            fix = []
            if item['fn'] == 'callout' and not item.get('wordsWithLine'):
                with_line = leaves - (at + events.delays['calloutWordsWithLine'])
                fix.append(f'bring its words in with the line (wordsWithLine): readable {with_line:.2f} s')
                delay = events.delays['calloutWordsWithLine'] if with_line >= least else delay
            word = earlier_word(page, at, least, leaves, delay)
            if word:
                fix.append(f"start it on \"{word['text']}\" ({word['start']:.2f} s): readable {leaves - (word['start'] + delay):.2f} s")
            fix.append('or move the cut one word later')
            verdicts.append(('fail', f'readable {formula:.2f} s at full strength (measured {measured:.2f} s) before it '
                                     f'{"is cut" if leaves == cut else "goes"} at {leaves:.2f} s; at least {least:.1f} s', '; '.join(fix)))
            if item['fn'] == 'callout':
                numbers['readable_with_usual_wait'] = round(leaves - (at + events.delays['callout']), 3)
                numbers['readable_with_words_with_line'] = round(leaves - (at + events.delays['calloutWordsWithLine']), 3)
        if is_conclusion and cut is not None and cut - at < conclusion_up - one_frame - 1e-6:
            word = earlier_word(page, at, conclusion_up - one_frame, cut, 0.0)
            verdicts.append(('fail', f'a conclusion up only {cut - at:.2f} s before the cut at {cut:.2f}; it needs {conclusion_up:.1f} s',
                             f"start it on \"{word['text']}\" ({word['start']:.2f} s), the first word of its clause" if word else 'start it earlier'))
        numbers['conclusion'] = is_conclusion
        if is_conclusion and cut is not None:
            numbers['up_before_cut'] = round(cut - at, 3)
        if not verdicts:
            extra = f'; a conclusion, up {cut - at:.2f} s before the cut' if is_conclusion and cut is not None else ''
            out.append(problem('readable', 'pass', item['page'], label, f'readable {formula:.2f} s (measured {measured:.2f} s){extra}', **numbers))
        for verdict, detail, fix in verdicts:
            out.append(problem('readable', verdict, item['page'], label, detail, fix, **numbers))
    return out


def check_fades_at_cuts(events, settings):
    one_frame = 1.0 / events.fps
    out = []
    cuts = [c for c in events.cuts() if c['kind'] == 'shot']
    for item in events.items:
        if item['page'] not in events.asked_pages or item['kind'] not in WORD_KINDS + ('arrow', 'pointer', 'card', 'ring'):
            continue
        until = item.get('until')
        if until is None:
            continue
        cut = next((c for c in cuts if c['page'] == item['page'] and abs(c['t'] - until) <= one_frame + 1e-6), None)
        if not cut:
            continue
        before = [point for frame, point in events.points_by_frame(item) if frame == cut['frame'] - events.data.get('step', 1)]
        strength = events.strength_at(item, before[0]) if before else None
        label = item.get('text') or item['kind']
        if (item.get('fadeOut') or 0) > 0 or (strength is not None and strength < 0.99 and item['kind'] != 'pointer'):
            out.append(problem('fade at cut', 'fail', item['page'], label,
                               f'ends on the cut at {cut["t"]:.2f} s but fades out over {item.get("fadeOut") or 0:.2f} s '
                               f'(strength {strength if strength is not None else 0:.2f} in the frame before the cut): the cut takes two steps',
                               'give it fadeOut: 0 (whole until the cut, gone after it)', cut=cut['t'], fadeOut=item.get('fadeOut')))
        else:
            out.append(problem('fade at cut', 'pass', item['page'], label, f'whole until the cut at {cut["t"]:.2f} s (fadeOut 0)', cut=cut['t']))
    return out


def boxes_meet(a, b, by):
    return min(a[2], b[2]) - max(a[0], b[0]) > by and min(a[3], b[3]) - max(a[1], b[1]) > by


def check_same_place(events, settings):
    """A new line drawn where another is still showing (round 3: NO SPARE over the fading question)."""
    least = settings.value('page_timing.overlap_opacity_min')
    by = settings.value('page_timing.overlap_pixels_min')
    out = []
    texts = [i for i in events.items if i['page'] in events.asked_pages and (i['kind'] in WORD_KINDS or i['kind'] == 'card')]
    tracks = {i['id']: dict(events.points_by_frame(i)) for i in texts}
    for k, a in enumerate(texts):
        for b in texts[k + 1:]:
            if a['page'] != b['page'] or (a.get('group') and a.get('group') == b.get('group')):
                continue
            if a.get('within') and a.get('within') == b.get('within'):
                continue
            if (a['kind'] == 'card' and b.get('within') == a.get('id')) or (b['kind'] == 'card' and a.get('within') == b.get('id')):
                continue
            both = sorted(set(tracks[a['id']]) & set(tracks[b['id']]))
            frames = [f for f in both if events.strength_at(a, tracks[a['id']][f]) > least and events.strength_at(b, tracks[b['id']][f]) > least
                      and tracks[a['id']][f][2] and tracks[b['id']][f][2] and boxes_meet(tracks[a['id']][f][2], tracks[b['id']][f][2], by)]
            if not frames:
                continue
            older, newer = sorted((a, b), key=lambda i: (i.get('at') if i.get('at') is not None else -1e9))
            new_at = newer.get('at')
            fix = (f"end {older['text']!r} by {new_at - 1 / events.fps:.2f} s (until = new.at - 1 frame; its fade counts inside until), "
                   f"or start {newer['text']!r} after {older['text']!r} has gone") if new_at is not None else 'move one of them'
            out.append(problem('same place', 'fail', a['page'], f"{newer['text']} over {older['text']}",
                               f'{len(frames)} frames ({events.time(frames[0]):.2f} to {events.time(frames[-1]):.2f} s) with both showing in the same place',
                               fix, frames=len(frames), first=events.time(frames[0]), last=events.time(frames[-1])))
    if not out:
        out.append(problem('same place', 'pass', None, 'all lines', f'no two lines showing in the same place at once ({len(texts)} things with words)'))
    return out


# ------------------------------------------------------------------------------------------------------- margins
def check_margins(events, settings):
    left_limit = settings.value('safe_area.text_left_pixels')
    right_limit = settings.value('safe_area.text_right_pixels')
    top_limit = settings.value('safe_area.letter_top_min_down') * events.height
    bottom_limit = settings.value('safe_area.nothing_to_read_below_down') * events.height
    band = settings.value('safe_area.title_band_down')
    card_band = settings.value('safe_area.rule_cards_down')
    out, extremes = [], {}
    for item in events.items:
        if item['page'] not in events.asked_pages or item['kind'] not in WORD_KINDS + ('card',) or not item.get('text') and item['kind'] != 'card':
            continue
        boxes = events.boxes(item)
        if not boxes:
            continue
        left, top = min(b[0] for b in boxes), min(b[1] for b in boxes)
        right, bottom = max(b[2] for b in boxes), max(b[3] for b in boxes)
        label = item.get('text') or item['kind']
        page = item['page']
        e = extremes.setdefault(page, {'right': 0, 'top': events.height, 'right_text': '', 'top_text': ''})
        if item['kind'] != 'card':
            if right > e['right']:
                e.update(right=right, right_text=label)
            if top < e['top']:
                e.update(top=top, top_text=label)
        shown = dict(left=round(left, 1), right=round(right, 1), top=round(top, 1), bottom=round(bottom, 1),
                     right_across=round(right / events.width, 4), top_down=round(top / events.height, 4))
        faults = []
        if item['kind'] != 'card' and right > right_limit + 0.5:
            faults.append((f'its letters reach {right:.0f} px ({right / events.width:.3f} across); the phone\'s buttons start at {right_limit} px', 'move it left or shorten it'))
        if left < left_limit - 1.5 and item['kind'] != 'card':
            faults.append((f'its letters start at {left:.0f} px; keep them right of {left_limit} px', 'move it right'))
        if top < top_limit - 0.5:
            faults.append((f'the top of its letters is {top / events.height:.3f} down ({top:.0f} px); keep at least {top_limit / events.height:.2f} down', f'lower it by {top_limit - top:.0f} px'))
        if bottom > bottom_limit + 0.5:
            faults.append((f'it reaches {bottom / events.height:.3f} down; nothing to read below {bottom_limit / events.height:.2f} down (buttons and captions)', 'move it up'))
        for detail, fix in faults:
            out.append(problem('margins', 'fail', page, label, detail, fix, **shown))
        if not faults and item['kind'] == 'words' and not item.get('within') and not events.carried(item):
            low, high = band
            high_cards = card_band[-1][-1]
            if top < low * events.height - 0.5 or bottom > max(high, high_cards) * events.height + 0.5:
                out.append(problem('margins', 'look', page, label, f'a typed line outside the top band ({top / events.height:.3f} to {bottom / events.height:.3f} down; '
                                   f'band {low:.2f} to {high:.2f}, rule cards to {high_cards:.2f})', 'keep typed lines in the top band unless they label something', **shown))
                continue
        if not faults:
            out.append(problem('margins', 'pass', page, label, f'{shown["right_across"]:.3f} across at most, top {shown["top_down"]:.3f} down', **shown))
    for page, e in sorted(extremes.items()):
        out.append(problem('margins', 'info', page, f'page {page}', f'longest line ends {e["right"] / events.width:.3f} across ({e["right_text"]}); '
                           f'highest letters {e["top"] / events.height:.4f} down ({e["top_text"]})',
                           right_across=round(e['right'] / events.width, 4), top_down=round(e['top'] / events.height, 4)))
    return out


# -------------------------------------------------------------------------------------- typed words and numbers
ONES = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
TENS = 'twenty thirty forty fifty sixty seventy eighty ninety'.split()
IRREGULAR = {'spent': 'spend', 'made': 'make', 'paid': 'pay', 'bought': 'buy', 'sold': 'sell', 'went': 'go', 'gone': 'go', 'kept': 'keep',
             'lost': 'lose', 'built': 'build', 'fell': 'fall', 'fallen': 'fall', 'rose': 'rise', 'risen': 'rise', 'grew': 'grow', 'cut': 'cut'}
SIGNS = {'+', '=', '→', '?', '&', '-', '–', '—', '·', ':', '/', '...'}


def number_words(n):
    n = int(n)
    if n < 20:
        return [ONES[n]]
    if n < 100:
        return [TENS[n // 10 - 2]] + ([ONES[n % 10]] if n % 10 else [])
    if n < 1000:
        return [ONES[n // 100], 'hundred'] + (['and'] + number_words(n % 100) if n % 100 else [])
    if n < 1000000:
        return number_words(n // 1000) + ['thousand'] + (number_words(n % 1000) if n % 1000 else [])
    return number_words(n // 1000000) + ['million'] + (number_words(n % 1000000) if n % 1000000 else [])


def spoken_forms(token):
    """Spoken words that can stand for an on-screen number token: '25%' -> twenty five percent; '1915' -> nineteen fifteen."""
    clean = token.replace(',', '').strip('+$×x%½')
    forms = set()
    if re.fullmatch(r'\d+(\.\d+)?', clean):
        whole, _, decimal = clean.partition('.')
        words = number_words(whole)
        if decimal:
            words += ['point'] + [ONES[int(d)] for d in decimal]
        forms |= set(words)
        if len(whole) == 4 and 1100 <= int(whole) <= 2099:   # years: nineteen fifteen, twenty twenty
            forms |= set(number_words(whole[:2]) + number_words(whole[2:]))
        forms.add(clean)
    if '½' in token:
        forms |= {'half'}
    if token.startswith(('×', 'x')) and clean.isdigit():
        forms |= {'times', 'quadruples' if clean == '4' else 'times'}
    forms -= {'and', 'point', 'hundred', 'thousand'}
    return forms


def stem(word):
    word = IRREGULAR.get(word, word)
    for ending in ('ing', 'ed', 'es', 's'):
        if len(word) > len(ending) + 2 and word.endswith(ending):
            return word[: -len(ending)]
    return word


def spoken_index(words):
    index = []
    for w in words:
        key = plain(w['text'])
        parts = {key, *key.split('-'), stem(key), *[stem(p) for p in key.split('-')]}
        index.append((w['start'], {p for p in parts if p}))
    return index


def check_typed_words(events, settings):
    window = settings.value('page_timing.typed_word_window_seconds')
    out, counted = [], {'new': 0, 'carried': 0}
    indexes = {n: spoken_index(p['words']) for n, p in events.pages.items()}
    for item in events.items:
        if item['page'] not in events.asked_pages or not item.get('text') or item['kind'] not in WORD_KINDS + ('arrow',):
            continue
        page = item['page']
        carried = events.carried(item)
        counted['carried' if carried else 'new'] += 1
        if item['kind'] == 'credit':
            out.append(problem('typed words', 'info', page, item['text'], 'a credit (who said it, or the source) is not narration'))
            continue
        text = (item['track'][-1][5] or item['text']) if item['kind'] == 'counter' else item['text']   # a counter: where it lands
        tokens = [t for t in re.split(r'\s+', text.replace('→', ' ').replace('—', ' ')) if t and t not in SIGNS]
        missing, far, earlier = [], [], []
        for token in tokens:
            word = plain(token)
            if not word:
                continue
            if re.search(r'\d', token):
                wanted = spoken_forms(token)
            else:
                wanted = {word, stem(word), *word.split('-')}
            here = [start for start, keys in indexes[page] if keys & wanted]
            at = item.get('at') if item.get('at') is not None else events.pages[page]['first_word_at']
            if here and min(abs(s - at) for s in here) <= window:
                continue
            if here and not carried:
                far.append((token, min(here, key=lambda s: abs(s - at))))
                continue
            before = [n for n in events.order[:events.order.index(page)] if any(keys & wanted for _, keys in indexes[n])]
            if before:
                earlier.append((token, before[-1]))
                continue
            missing.append(token)
        label = text
        if missing:
            out.append(problem('typed words', 'fail', page, label, f'not said on this page or before it: {", ".join(missing)}',
                               'a word on screen she does not say is a new claim: cut it, or have it said', missing=missing))
        elif far:
            out.append(problem('typed words', 'look', page, label, '; '.join(f'"{t}" is said at {s:.2f} s, {abs(s - (item.get("at") or 0)):.1f} s from when it shows' for t, s in far),
                               f'show it within {window:.0f} s of when it is said'))
        elif earlier:
            out.append(problem('typed words', 'info' if (carried or item['kind'] == 'tag') else 'look', page, label,
                               '; '.join(f'"{t}" was said on page {n}' for t, n in earlier) + (' (carried over)' if carried else ''),
                               '' if (carried or item['kind'] == 'tag') else 'a name carried from an earlier page: fine for a tag; otherwise have it said here'))
        else:
            out.append(problem('typed words', 'pass', page, label, 'every word is said on the page near its moment' + (' (carried over)' if carried else '')))
    digits = [i['text'] for i in events.items if i['page'] in events.asked_pages and i.get('text') and re.search(r'\d', i['text'])]
    return out, counted, digits


def parse_number(token):
    match = re.search(r'(\d[\d,]*(?:\.\d+)?)', token)
    if not match:
        return None
    text = match.group(1).replace(',', '')
    decimals = len(text.partition('.')[2])
    unit = '%' if '%' in token else '$' if '$' in token else 'x' if re.match(r'[×x]\d', token) else 'year' if (len(text) == 4 and text.isdigit() and 1100 <= int(text) <= 2099) else 'count'
    return {'value': float(text), 'decimals': decimals, 'unit': unit, 'shown': token}


NUMBER_WORDS = set(ONES) | set(TENS) | {'hundred', 'thousand', 'million', 'point', 'and', 'a', 'half', 'quarter', 'quarters'}


def settled_time(events, item, final):
    """When a counter stopped changing: the first frame of its last unchanging stretch (or its own count end, if later)."""
    track = item['track']
    settled = track[0][0]
    for k in range(1, len(track)):
        if track[k][5] != track[k - 1][5]:
            settled = track[k][0]
    return max(events.time(settled), item.get('countEnd') or -1e9)


def completing_forms(token):
    """The spoken words that can complete a number ("thousand" in twenty thousand, "half" in five and a half) and the word
    it must start with, or (set(), None) when the token holds no number."""
    clean = token.replace(',', '').strip('+$×x%½')
    if not re.fullmatch(r'\d+(\.\d+)?', clean):
        return set(), None
    whole, _, decimal = clean.partition('.')
    words = number_words(whole)
    forms = set(words)
    if decimal:
        forms |= {ONES[int(d)] for d in decimal} | {'point'}
        forms |= {'5': {'half'}, '25': {'quarter'}, '75': {'quarters', 'quarter'}}.get(decimal, set())
    if len(whole) == 4 and 1100 <= int(whole) <= 2099:
        forms |= set(number_words(whole[:2]) + number_words(whole[2:]))
    return forms - {'and', 'point', 'a'}, words[0]


def number_word_near(words, token, when):
    """The spoken word that completes the number nearest `when` ("six" in "five point six", "thousand" in "twenty
    thousand"), or None when the number is not said."""
    forms, first = completing_forms(token)
    if not forms:
        return None
    runs, current = [], []
    for w in words:
        key = plain(w['text'])
        if key in NUMBER_WORDS or key in forms or re.fullmatch(r'\d[\d.,]*', key or ''):
            current.append(w)
        else:
            if current:
                runs.append(current)
            current = []
    if current:
        runs.append(current)
    candidates = []
    for run in runs:
        while run and plain(run[0]['text']) in ('and', 'a'):
            run = run[1:]
        keys = [plain(w['text']) for w in run]
        if not keys or keys[0] != first:   # a number is said from its leading word ("three point two" is not 2.75)
            continue
        numeric = [w for w in run if plain(w['text']) in forms]
        if numeric:
            candidates.append(numeric[-1])
    return min(candidates, key=lambda w: abs(w['start'] - when)) if candidates and when is not None else None


def check_numbers(events, settings, ledger):
    hold_least = settings.value('timing.key_number_hold_seconds')
    hold_base, hold_per = settings.value('page_timing.number_hold_seconds')
    after_word = settings.value('page_timing.count_end_after_word_max_seconds')
    out = []
    numbered = [i for i in events.items if i['page'] in events.asked_pages and i.get('text') and re.search(r'\d', i['text']) and i['kind'] != 'counter']
    counters = [i for i in events.items if i['page'] in events.asked_pages and i['kind'] == 'counter']
    shown = []
    for item in numbered:
        for token in item['text'].split():
            number = parse_number(token)
            if number:
                shown.append((item, number))
    for item in counters:
        final = item['track'][-1][5] or item['text']
        token = next((tok for tok in final.split() if re.search(r'\d', tok)), final)
        number = parse_number(token)
        if number:
            shown.append((item, number))
        # a count must land by its spoken number and then hold still: when it stopped changing is read from the track
        page = events.pages[item['page']]
        count_end = settled_time(events, item, final)
        word = number_word_near(page['words'], token, count_end)
        cut = events.picture_cuts_after(item['page'], item['at'])
        leaves = min(x for x in ((item.get('until') if item.get('until') is not None else 1e9) - (item.get('fadeOut') or 0), cut or 1e9,
                                 events.time(item['runs'][0][1]) + 1.0 / events.fps))
        held = leaves - count_end
        needed = max(hold_least, hold_base + hold_per * len(token))
        numbers = {'count_end': round(count_end, 3), 'held': round(held, 3), 'needed': round(needed, 3),
                   'number_word': word['text'] if word else None, 'number_word_at': word['start'] if word else None}
        faults = []
        if word is not None and count_end > word['start'] + after_word + 1e-6:
            faults.append((f'the count lands at {count_end:.2f} s, after the word that completes its number ("{word["text"]}" at {word["start"]:.2f} s)',
                           f'finish the count by {word["start"] + after_word:.2f} s'))
        if held < needed - 1e-6:
            faults.append((f'held still {held:.2f} s after it lands; {token} needs {needed:.2f} s to read', 'hold it longer or land the count earlier'))
        for detail, fix in faults:
            out.append(problem('numbers', 'fail', item['page'], final, detail, fix, **numbers))
        if not faults:
            out.append(problem('numbers', 'pass', item['page'], final, f'lands at {count_end:.2f} s' + (f' (its number is completed by "{word["text"]}" at {word["start"]:.2f} s)' if word else '')
                               + f', held still {held:.2f} s (needs {needed:.2f} s)', **numbers))
    if ledger is None:
        if shown:
            out.append(problem('numbers', 'look', None, ', '.join(n['shown'] for _, n in shown), 'numbers on screen but no ledger given (--ledger)',
                               'check each against the research ledger'))
        else:
            out.append(problem('numbers', 'pass', None, 'no numbers', 'no number is shown on these pages'))
        return out
    entries = ledger['numbers']
    names = [n.lower() for n in ledger.get('not_claims', [])]
    for item, number in shown:
        if any(name in (item.get('text') or '').lower() for name in names):
            out.append(problem('numbers', 'info', item['page'], item.get('text'), f'{number["shown"]} names a thing (the ledger\'s not_claims)'))
            continue
        unit_matches = [e for e in entries if e.get('unit', 'count') == number['unit']]
        half = 0.5 * 10 ** (-number['decimals'])
        close = [e for e in unit_matches if abs(e['value'] - number['value']) <= half + 1e-9]
        text = item.get('text') if item['kind'] != 'counter' else (item['track'][-1][5] or item['text'])
        if not close:
            nearest = min(unit_matches, key=lambda e: abs(e['value'] - number['value']), default=None)
            out.append(problem('numbers', 'fail', item['page'], number['shown'],
                               f'no ledger number within rounding (±{half:g})' + (f'; nearest {nearest["id"]} = {nearest["value"]:g}' if nearest else ''),
                               'show the ledger value, rounded honestly', nearest=nearest['id'] if nearest else None))
            continue
        entry = close[0]
        qualifier = entry.get('qualifier')
        if qualifier and qualifier.lower() not in (text or '').lower() and not (qualifier.lower() == 'under' and '<' in (text or '')):
            out.append(problem('numbers', 'fail', item['page'], text, f'{number["shown"]} matches {entry["id"]} ({entry["value"]:g}) but drops its "{qualifier}"',
                               f'keep "{qualifier.upper()}" on screen', ledger=entry['id']))
        else:
            out.append(problem('numbers', 'pass', item['page'], text, f'{number["shown"]} = {entry["id"]} ({entry["value"]:g}{" " + qualifier if qualifier else ""}) within ±{half:g}',
                               ledger=entry['id']))
    return out


# ------------------------------------------------------------------------- groups, slides, frozen stretches
def check_word_groups(events, settings):
    every = settings.value('timing.word_group_every_seconds')
    _, most = settings.value('timing.word_groups_per_page')
    out, total, seconds_total = [], 0, 0.0
    for number in events.asked_pages:
        page = events.pages[number]
        items = [i for i in events.items if i['page'] == number and not events.carried(i) and i.get('text')]
        groups = {i.get('group') or i['id'] for i in items if i['kind'] == 'words' and not i.get('within')}
        cards = [i for i in items if i['kind'] == 'card']
        placements = [i for i in items if i['kind'] in ('label', 'tag')]
        figures = [i for i in items if i['kind'] in ('counter',) or re.search(r'\d', i.get('text') or '')]
        others = [i for i in items if i['kind'] in ('hook', 'title', 'credit')]
        count = len(groups) + len(cards) + len(placements) + len(others)
        seconds = page['last_word_end_at'] - page['first_word_at']
        limit = max(most, round(seconds / every)) + len(figures) + len(placements)
        total += count
        seconds_total += seconds
        detail = (f'{count} groups of words in {seconds:.1f} s ({len(groups)} lines, {len(cards)} cards, {len(placements)} labels and tags, {len(others)} other); '
                  f'limit {limit} (the larger of {most} and one every {every:.0f} s, plus {len(figures)} figures and {len(placements)} placements)')
        out.append(problem('word groups', 'fail' if count > limit else 'pass', number, f'page {number}', detail,
                           'let the pictures carry more; keep figures and named placements' if count > limit else '', groups=count, limit=limit))
    if events.asked_pages:
        out.append(problem('word groups', 'info', None, 'these pages', f'{total} groups in {seconds_total:.0f} s: one every {seconds_total / max(1, total):.1f} s '
                           f'(plan 34 aims at about one every {every:.0f} s over the chapter)', groups=total, seconds=round(seconds_total, 2)))
    return out


def word_at_time(page, seconds):
    return next((w for w in page['words'] if abs(w['start'] - seconds) < 0.02), None)


def check_slides(events, settings):
    low, high = settings.value('camera.slide_seconds_range')
    per_page = settings.value('camera.slides_per_page_max')
    out = []
    for number in events.asked_pages:
        page = events.pages[number]
        moves = [(plan['name'], m) for plan in page['camera_plans'] for m in plan['moves'] if m['kind'] != 'focus']
        for name, move in moves:
            start, stop = word_at_time(page, move['from']), word_at_time(page, move['to'])
            gap = move['to'] - move['from']
            words = f'from "{start["text"] if start else "?"}" ({move["from"]:.2f}) to "{stop["text"] if stop else "?"}" ({move["to"]:.2f})'
            faults = []
            if not start or not stop:
                faults.append('it does not start and stop on spoken words')
            if not (low - 1e-6 <= gap <= high + 1e-6):
                faults.append(f'{gap:.2f} s long; slides are {low}-{high} s')
            # a look, not a fail: the slide rule is plan 34's for built and painted sets; camera_audit.py judges other moves
            out.append(problem('slides', 'look' if faults else 'pass', number, f'{name}: {move["kind"]}',
                               f'{words}, {gap:.2f} s' + (': ' + '; '.join(faults) if faults else ''),
                               'in a built set, tie a slide\'s start and stop to words 2.6 to 4.1 s apart' if faults else '', seconds=round(gap, 3)))
        if len(moves) > per_page:
            out.append(problem('slides', 'look', number, f'page {number}', f'{len(moves)} moves; built sets use at most {per_page} slide a page',
                               'cut to a new shot instead of a second move'))
    return out


def check_frozen(events, settings):
    """Stretches while she speaks where nothing at all changes: no flat graphic changes, no live thing, a held camera."""
    longest = settings.value('timing.rest_without_change_max_seconds')
    end_card = settings.value('timing.end_card_rest_max_seconds')
    out = []
    changes = {}
    for item in events.items:
        for point in item['track']:
            changes.setdefault((item['page'], point[0]), True)
        for start, end in item['runs']:
            changes[(item['page'], start)] = True
            changes[(item['page'], end + 1)] = True
    last_number = events.order[-1]
    for number in events.asked_pages:
        page = events.pages[number]
        rows = [(row['f'], p) for row in events.frames for p in row['pages'] if p['page'] == number]
        frozen_from, worst, held_throughout = None, (0.0, None, True), True
        previous = None
        for frame, p in rows:
            t = events.time(frame)
            speaking = any(w['start'] <= t <= w['end'] + 0.3 for w in page['words'])
            live = (p.get('effects_shown') if 'effects_shown' in p else len(p.get('effects', []))) > 0
            moved = previous is not None and p['camera'] != previous['camera']
            stepped = previous is not None and p['page_still'] != previous['page_still']
            still = not live and not moved and not stepped and not changes.get((number, frame))
            if still and speaking:
                if frozen_from is None:
                    frozen_from, held_throughout = frame, True
                held_throughout = held_throughout and p['page_still'] is not None
                length = (frame - frozen_from + 1) / events.fps
                if length > worst[0]:
                    worst = (length, frozen_from, held_throughout)
            else:
                frozen_from = None
            previous = p
        limit = end_card if number == last_number else longest
        if worst[0] > limit + 1e-6:
            # with a held-shot key, nothing marked moving means nothing moves; without one, live things are not marked and
            # so cannot be seen in the events (dust, flames): look at the film there
            verdict = 'fail' if worst[2] else 'look'
            out.append(problem('frozen', verdict, number, f'page {number}', f'no flat graphic, camera or held picture changes for {worst[0]:.2f} s from {events.time(worst[1]):.2f} s while she speaks (limit {limit:.1f} s)'
                               + ('' if worst[2] else '; the page marks no live things (kit.moving), so dust or flames there cannot be seen here'),
                               'add a beat on a word in that stretch, or a slow named camera move', seconds=round(worst[0], 3)))
        else:
            out.append(problem('frozen', 'pass', number, f'page {number}', f'longest stretch with nothing changing while she speaks: {worst[0]:.2f} s (limit {limit:.1f} s)',
                               seconds=round(worst[0], 3)))
    return out


# --------------------------------------------------------------------------------------- stills and planned cuts
def still_list(events, settings):
    after_event = settings.value('page_timing.still_after_event_seconds')
    turn_after = settings.value('page_timing.page_turn_stills_after_last_word_seconds')
    merge = settings.value('page_timing.merge_stills_within_seconds')
    one_frame = 1.0 / events.fps
    moments = []
    for item in events.items:
        if item['page'] in events.asked_pages and item.get('at') is not None and not events.carried(item) and item['kind'] != 'shade':
            when = max(item['at'] + after_event, (item.get('fullAt') or item['at']) + 0.05)
            moments.append((when, f'page {item["page"]}: {item.get("text") or item["kind"]} in'))
    # every word a page asks for is a moment it cares about (a state, a burst, a cut), and each page's first word
    for look in events.data.get('lookups', []):
        if look['page'] in events.asked_pages and look.get('start') is not None:
            moments.append((look['start'] + after_event, f'page {look["page"]}: "{look["word"]}"'))
    for number in events.asked_pages:
        page = events.pages[number]
        moments.append((page['first_word_at'], f'page {number}: first word'))
        for plan in page['camera_plans']:
            for move in plan['moves']:
                for share, name in ((0.0, 'starts'), (0.5, 'middle'), (1.0, 'ends (the weights view)')):
                    moments.append((move['from'] + share * (move['to'] - move['from']), f'page {number}: {plan["name"]} {move["kind"]} {name}'))
        for extra in turn_after:
            moments.append((page['last_word_end_at'] + extra, f'page {number}: last word + {extra:.1f} s (page turn)'))
    for cut in events.cuts():
        if cut['page'] not in events.asked_pages:
            continue
        if cut['kind'] == 'shot' or cut['kind'] == 'state':
            moments.append((cut['t'] - one_frame, f'page {cut["page"]}: last frame before {cut["what"]}'))
            moments.append((cut['t'], f'page {cut["page"]}: {cut["what"]} (the projector view)' if cut['kind'] == 'shot' else f'page {cut["page"]}: {cut["what"]}'))
        else:
            moments.append((cut['t'] - one_frame, f'page {cut["page"]}: last frame before the {cut["kind"]}'))
            moments.append(((cut['t'] + cut['end']) / 2, f'page {cut["page"]}: {cut["kind"]} middle'))
            moments.append((cut['end'], f'page {cut["page"]}: first frame after the {cut["kind"]}'))
    for number in events.asked_pages:
        first = next((row['t'] for row in events.frames for p in row['pages'] if p['page'] == number), None)
        if first is not None:
            moments.append((first, f'page {number}: first frame (the projector view)'))
    moments.sort()
    kept = []
    for when, why in moments:
        when = round(events.zero + round((when - events.zero) * events.fps) / events.fps, 3)   # on a frame
        if kept and when - kept[-1][0] < merge:
            kept[-1][1].append(why)
        else:
            kept.append((when, [why]))
    return [{'t': round(t, 2), 'why': whys} for t, whys in kept]


def planned_cuts(events, film_start):
    one_frame = 1.0 / events.fps
    out = []
    for cut in events.cuts():
        if cut['page'] not in events.asked_pages:
            continue
        if cut['kind'] in ('shot', 'state'):
            out.append({'t': cut['t'], 'what': f'page {cut["page"]}: {cut["what"]}', 'film_seconds': round(cut['t'] - film_start, 3)})
        elif 'dissolve' in cut['kind'] or 'dip' in cut['kind'] or 'peel' in cut['kind']:
            out.append({'t': cut['t'], 'what': f'page {cut["page"]}: {cut["kind"]} starts (gradual: not a jump)', 'film_seconds': round(cut['t'] - film_start, 3), 'gradual': True})
    return [c for c in out if c['t'] >= film_start - one_frame]


# --------------------------------------------------------------------------------------------- the accepted list
def apply_accepted(problems, accepted):
    for p in problems:
        if p['verdict'] != 'fail':
            continue
        for a in accepted:
            if a.get('check') == p['check'] and (a.get('page') in (None, p['page'])) and a.get('text', '').lower() in (p['text'] or '').lower():
                p['verdict'] = 'known'
                p['accepted'] = {k: a.get(k) for k in ('reason', 'who', 'date')}
    return problems


# ------------------------------------------------------------------------------------------------------ commands
def run_check(args, settings):
    data = load_json(args.events)
    events = Events(data)
    ledger = load_json(args.ledger) if args.ledger else None
    accepted = load_json(args.accepted) if args.accepted else []
    film_start = args.film_start if args.film_start is not None else data['from_seconds']
    problems = []
    lookups = add_contexts(data['lookups'], events)
    problems += check_lookups(lookups, settings, events.asked_pages)
    pause_problems, pause_rows = check_pauses(events, settings)
    problems += pause_problems
    problems += check_readable(events, settings, args.conclusion or ())
    problems += check_fades_at_cuts(events, settings)
    problems += check_same_place(events, settings)
    problems += check_margins(events, settings)
    typed, counted, digits = check_typed_words(events, settings)
    problems += typed
    problems += check_numbers(events, settings, ledger)
    problems += check_word_groups(events, settings)
    problems += check_slides(events, settings)
    problems += check_frozen(events, settings)
    problems = apply_accepted(problems, accepted)
    stills = still_list(events, settings)
    cuts = planned_cuts(events, film_start)
    scene = args.scene or data['scene']
    recommended = [r['recommended'] for r in pause_rows]
    default_pause = settings.value('timing.default_page_pause_seconds')
    plain = [r['recommended'] for r in pause_rows if r['plain_peel']]
    usual = max(set(plain), key=plain.count) if plain else default_pause
    different = [r for r in pause_rows if abs(r['recommended'] - usual) > 1e-6]
    estimate_options = f'--default-pause {usual:.2f}' + (' --pause-after ' + ' '.join(f'{r["page"]}={r["recommended"]:.2f}' for r in different) if different else '')
    windows = settings.value('timing.camera_plan_window_seconds')
    result = {
        'scene': scene, 'pages': events.asked_pages, 'frames_sampled': data.get('sampled_frames'),
        'verdicts': {v: sum(1 for p in problems if p['verdict'] == v) for v in VERDICT_ORDER},
        'problems': sorted(problems, key=lambda p: (VERDICT_ORDER[p['verdict']], p['check'], p['page'] or 0)),
        'typed_lines': counted, 'typed_digits': digits,
        'pauses': {'gaps': pause_rows, 'usual': usual, 'table_default': default_pause,
                   'assemble_option': '--pauses ' + ','.join(f'{x:.2f}' for x in recommended),
                   'estimate_options': estimate_options},
        'stills': {'times': stills, 'command': f'node paper-film/tools/render-paper-film.mjs {scene} STILLS_FOLDER --stills ' + ' '.join(f'{s["t"]:.2f}' for s in stills)},
        'planned_cuts': {'film_start': film_start, 'cuts': cuts,
                         'find_jumps_command': 'python3 -I paper-film/tools/find_jumps.py FILM.mp4 SHEET.jpg 4 '
                         + ' '.join(f'{c["film_seconds"]:.3f}' for c in cuts if not c.get('gradual'))},
        'camera_audit_windows': [{'page': n, 'from': round(events.pages[n]['first_word_at'] - windows['before_first_word'], 3),
                                  'to': round(events.pages[n]['last_word_end_at'] + windows['after_last_word_end'], 3)} for n in events.asked_pages],
        'appear_delays': events.delays, 'order_differences': len(data.get('order_differences', [])),
    }
    return result


def report_lines(result):
    lines = [f'Page timing for {result["scene"]}, pages {", ".join(map(str, result["pages"]))} ({result["frames_sampled"]} frames looked at).']
    v = result['verdicts']
    lines.append(f'{v["fail"]} to fix, {v["look"]} to look at, {v["known"]} known and kept, {v["pass"]} passed.')
    lines.append(f'Typed lines: {result["typed_lines"]["new"]} new and {result["typed_lines"]["carried"]} carried over from the page before; '
                 f'digits on screen: {", ".join(result["typed_digits"]) or "none"}.')
    current = None
    for p in result['problems']:
        if p['verdict'] == 'pass':
            continue
        if p['check'] != current:
            current = p['check']
            lines.append('')
            lines.append(current.upper())
        where = f'page {p["page"]}' if p['page'] is not None else 'all'
        lines.append(f'  {p["verdict"].upper():5s} {where}: {p["text"]}: {p["detail"]}')
        if p.get('fix'):
            lines.append(f'        fix: {p["fix"]}')
        if p.get('accepted'):
            lines.append(f'        accepted: {p["accepted"].get("reason")} ({p["accepted"].get("who")}, {p["accepted"].get("date")})')
    lines.append('')
    lines.append('PAUSES AFTER EACH PAGE (the join\'s wait + its length + settle, plus any hold)')
    others = []
    for g in result['pauses']['gaps']:
        line = (f'  page {g["page"]} -> {g["next_page"]}: {g["join"]} after {g["join_after"]:.2f} s for {g["join_length"]:.2f} s'
                + (f', hold {g["hold"]:.1f} s' if g['hold'] else '') + f': needs {g["recommended"]:.2f} s; the timeline has {g["in_timeline"]:.2f} s')
        if g['page'] in result['pages'] or g['next_page'] in result['pages']:
            lines.append(line)
        else:
            others.append(g['page'])
    if others:
        lines.append(f'  pages {", ".join(map(str, others))} were not looked at: their pauses below come from their files\' joins only (no holds known)')
    lines.append(f'  for assemble_chapter_narration.py: {result["pauses"]["assemble_option"]}')
    lines.append(f'  for estimate_timeline.py: {result["pauses"]["estimate_options"]}')
    lines.append('')
    lines.append(f'STILLS TO CHECK ({len(result["stills"]["times"])}, drawn in one run so page turns are right):')
    lines.append('  ' + result['stills']['command'])
    lines.append('')
    lines.append(f'PLANNED CUTS for find_jumps.py (film starting at {result["planned_cuts"]["film_start"]:.3f} s):')
    for c in result['planned_cuts']['cuts']:
        lines.append(f'  {c["t"]:.3f} s ({c["film_seconds"]:.3f} s into the film): {c["what"]}')
    lines.append('  ' + result['planned_cuts']['find_jumps_command'])
    if result['order_differences']:
        lines.append('')
        lines.append(f'{result["order_differences"]} moments came out different when drawn out of order: run tools/check_page_layout.mjs on the events.')
    return lines


def run_lookups(args, settings):
    timeline = load_json(args.timeline)
    lookups = lookups_from_page_files(timeline, args.page_files)
    problems = check_lookups(lookups, settings)
    result = {'timeline': args.timeline, 'page_files': args.page_files, 'lookups': len(lookups),
              'verdicts': {v: sum(1 for p in problems if p['verdict'] == v) for v in VERDICT_ORDER}, 'problems': problems}
    lines = [f'{len(lookups)} word lookups read from {len(args.page_files)} page files; {result["verdicts"]["fail"]} leave out which time for a word said more than once.']
    for p in problems:
        if p['verdict'] == 'fail':
            lines.append(f'  FAIL page {p["page"]}: {p["detail"]}')
            for said in p.get('said', []):
                lines.append(f'        {said["start"]:.2f} s  {said["words"]}')
            lines.append(f'        fix: {p["fix"]}')
    return result, lines


CHUNK_NAME = re.compile(r'chunk-(\d+)-to-(\d+)')


def run_refilm(args, settings):
    old, new = load_json(args.old_timeline), load_json(args.new_timeline)
    fps = args.fps
    drawn = settings.value('timing.page_drawn_window_seconds')
    names = []
    if os.path.isdir(args.chunks):
        names = sorted(set(os.path.basename(p) for p in glob.glob(os.path.join(args.chunks, '*')) if CHUNK_NAME.search(os.path.basename(p))))
    else:
        names = [line.strip() for line in open(args.chunks) if CHUNK_NAME.search(line)]
    chunks = sorted({(int(CHUNK_NAME.search(n).group(1)), int(CHUNK_NAME.search(n).group(2))): n for n in names}.items())
    old_pages, new_pages = {p['page']: p for p in old['pages']}, {p['page']: p for p in new['pages']}
    tolerance = 0.5 / fps
    moved = []
    for number in sorted(old_pages):
        a, b = old_pages[number], new_pages.get(number)
        if b is None or len(a['words']) != len(b['words']) or any(abs(x['start'] - y['start']) > tolerance or abs(x['end'] - y['end']) > tolerance
                                                                  for x, y in zip(a['words'], b['words'])):
            moved.append(number)
    windows = []
    for number in moved:
        for pages in (old_pages, new_pages):
            page = pages.get(number)
            if not page:
                continue
            previous = pages.get(number - 1)
            start = (previous['last_word_end_at'] + drawn['from_previous_last_word']) if previous else 0.0
            following = pages.get(number + 1)
            end = page['last_word_end_at'] + max(drawn['after_own_last_word'], (following['first_word_at'] - page['last_word_end_at']) if following else 0)
            windows.append((start, end))
    frames = [(int(math.floor(s * fps)), int(math.ceil(e * fps))) for s, e in windows]
    redo = [{'chunk': name, 'from_frame': a, 'to_frame': b} for (a, b), name in chunks if any(a <= f2 and b >= f1 for f1, f2 in frames)]
    keep = [name for (a, b), name in chunks if not any(a <= f2 and b >= f1 for f1, f2 in frames)]
    result = {'moved_pages': moved, 'windows_seconds': [[round(s, 3), round(e, 3)] for s, e in windows], 'chunks': len(chunks),
              'refilm': redo, 'keep': keep}
    lines = [f'Pages whose word times changed: {", ".join(map(str, moved)) or "none"}.']
    if moved:
        lines.append('Frames they are drawn in (old and new timing): ' + ', '.join(f'{s:.2f}-{e:.2f} s' for s, e in windows))
    lines.append(f'Delete and film again {len(redo)} of {len(chunks)} chunks: ' + (', '.join(r['chunk'] for r in redo) or 'none'))
    lines.append(f'Keep: {", ".join(keep) or "none"}')
    if moved and moved[-1] == max(old_pages) and len(moved) > 1:
        lines.append('Everything after the first changed page moved. If only one page was re-recorded, change the pause after it to absorb the '
                     'difference in length, and only that page needs filming again.')
    return result, lines


def main(argv=None):
    parser = argparse.ArgumentParser(description='Works out when things happen on cinema pages: lookups, pauses, reading times, cuts, margins, '
                                                 'typed words, numbers, stills to check, planned cuts, chunks to re-film.')
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('check', help='check pages from a page events file (paper-film/tools/page_events.mjs)')
    check.add_argument('events', help='the page events JSON')
    check.add_argument('--ledger', help='the research ledger numbers (JSON)')
    check.add_argument('--accepted', help='problems the project chose to keep (JSON list)')
    check.add_argument('--film-start', type=float, help='chapter second the filmed piece starts at (for find_jumps.py)')
    check.add_argument('--conclusion', action='append', help='words to treat as a conclusion (besides parts starting with an arrow)')
    check.add_argument('--scene', help='the scene name for the stills command (default: the events\' scene)')
    lookups = commands.add_parser('lookups', help='check the word lookups in page files against a timeline, without a browser')
    lookups.add_argument('timeline')
    lookups.add_argument('page_files', nargs='+', help='FILE.js:PAGE_NUMBER')
    refilm = commands.add_parser('refilm', help='after a re-record: the pages that moved and the filmed chunks to film again')
    refilm.add_argument('old_timeline')
    refilm.add_argument('new_timeline')
    refilm.add_argument('--chunks', required=True, help='a folder of chunk-AAAAA-to-BBBBB files, or a text file listing them')
    refilm.add_argument('--fps', type=int, default=30)
    delays = commands.add_parser('delays', help='the appear delays read from graphics.js')
    delays.add_argument('--graphics', default=GRAPHICS_JS)
    for sub in (check, lookups, refilm, delays):
        add_output_options(sub)
    args = parser.parse_args(argv)
    settings = load_settings(args.settings)
    if args.command == 'check':
        result = run_check(args, settings)
        finish('plan_page_timing check', result, report_lines(result), settings, args)
        return 1 if result['verdicts']['fail'] else 0
    if args.command == 'lookups':
        result, lines = run_lookups(args, settings)
        finish('plan_page_timing lookups', result, lines, settings, args)
        return 1 if result['verdicts']['fail'] else 0
    if args.command == 'refilm':
        result, lines = run_refilm(args, settings)
        finish('plan_page_timing refilm', result, lines, settings, args)
        return 0
    table = read_appear_delays(args.graphics)
    finish('plan_page_timing delays', {'graphics': args.graphics, 'appear_delays': table},
           [f'Seconds from an item\'s start until its words are at full strength (from {args.graphics}):'] + [f'  {k}: {v:g}' for k, v in table.items()],
           settings, args)
    return 0


if __name__ == '__main__':
    sys.exit(run_main(main, 'plan_page_timing'))
