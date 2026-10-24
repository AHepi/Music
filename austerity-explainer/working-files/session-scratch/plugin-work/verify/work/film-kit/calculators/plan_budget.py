"""What this does: plans the money, the filming time and the machine for a film, so these are worked out from the
film's own files instead of being guessed or searched for again each time (logs 10-34). It answers:
  - what each paid step will cost (paintings by the megapixels returned AND sent, sketches, the narration's credits and
    dollars, a repaint and re-record reserve), and how much of the user's allowance is left, counted from the date the
    allowance began, from a spend ledger; a next paid step larger than what is left, or one that would pass the
    allowance's spending line (its "spending_line", else film-settings.json money.user_allowance_dollars for an allowance
    of that size; paint_request.py uses the same line), is refused (exit 2);
  - how long filming will take, from each frame's kind (held, held with live effects, moving, a page join), read from
    the page events (paper-film/tools/page_events.mjs), priced by MEASURED seconds a frame: best from a few short
    profile pieces filmed first (profile-commands, then measure), else from an earlier filming of the same pages, and
    only as a last resort from the table in film-settings.json (round 4: 0.9 s held, 4.3 s sliding, about 34 s loading
    a piece, one worker);
  - how many workers, how big a piece (each piece loads its pages once and is kept as soon as it is filmed, so a
    restart loses at most one piece), whether the chapter must load lazily, whether memory suffices, and the stretches
    that each fit in a 2-hour background job, with their FILM_FROM/FILM_TO commands;
  - the disk a filming or export needs, a check of files before they are pushed to a public repository or sent in chat,
    and whether a filming run is still going (status).
Nothing here spends money or calls a paid service: prices come from film-settings.json (with the date each was read) or
from a rate you read yourself today (--rate).

Use:
  python3 plan_budget.py cost PLAN.json [--rate CENTS_PER_MEGAPIXEL] [--ledger LEDGER.json] [--allowance NAME]
  python3 plan_budget.py ledger LEDGER.json [--allowance NAME] [--next-cost DOLLARS] [--today YYYY-MM-DD]
  python3 plan_budget.py frames EVENTS.json[.gz] [--from-frame A] [--to-frame B]
  python3 plan_budget.py profile-commands EVENTS.json[.gz] --scene SCENE
  python3 plan_budget.py measure LOGS --events EVENTS.json[.gz] [--leave-out-chunks]
  python3 plan_budget.py filming EVENTS.json[.gz] --scene SCENE [--rates RATES.json] [--from-frame A] [--to-frame B]
        [--processors N] [--free-memory-gb G] [--heavy-pages N] [--views-per-page N]
        [--blender-running yes|no|auto] [--free-disk-gb G]
  python3 plan_budget.py disk --seconds S [--copies N] [--exports-megabytes M] [--stills N] [--free-disk-gb G]
  python3 plan_budget.py push [FILE_OR_FOLDER ...] [--git REPO]
  python3 plan_budget.py status CHUNKS_FOLDER [--piece-seconds S]
PLAN.json (cost):  {"paintings": [{"name": "W1 plate", "returned": [1504, 2672], "sent": [[1536, 2730], [768, 1368]],
                   "count": 1}], "sketches": 2, "narration_scripts": ["narration-script.json"] or "narration_characters":
                   6300, "rerecord_pages": 1, "other_dollars": [{"what": "...", "dollars": 0.12}]}
                   A paintings ledger (people-test-paintings.json: "paintings" with returned_size and images_sent) also
                   works as a plan: it prices what those requests cost.
LEDGER.json:       {"allowances": [{"name": "chapter 2 pictures", "dollars": 10, "start": "2026-10-12T12:00",
                   "covers": ["fal"], "spending_line": 6}], "entries": [{"when": "2026-10-12T14:00", "service": "fal", "what": "...",
                   "dollars": 1.03}]}  (an entry without "dollars" but with "cents" is read too)
LOGS (measure):    filming logs: a chunk folder of film-chapter-parallel.sh (*.mp4.log and the SCENE-filming.log next
                   to it), single render-paper-film.mjs logs, or one text file holding their lines (== headers).
RATES.json:        what measure writes: {"seconds_per_frame": {"held_still":, "held_live":, "moving":, "join":},
                   "seconds_loading_a_piece":, "source": ...}
Every command takes --json, --out FILE, --report FILE and --settings FILE, and names the film-settings.json values it
used. cost, ledger and push exit 2 when they refuse; filming exits 1 when the plan does not fit (memory, disk, Blender).
"""
import argparse
import glob
import gzip
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from settings import load_settings  # noqa: E402
from calculator_output import add_output_options, finish, run_main  # noqa: E402

KIT = os.path.dirname(HERE)
CLASSES = ('held_still', 'held_live', 'moving', 'join')
CLASS_WORDS = {'held_still': 'held, nothing live', 'held_live': 'held, live effects', 'moving': 'moving (a slide)',
               'join': 'a page join (two pages drawn)'}
AUDIO_VIDEO = ('.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.opus', '.mp4', '.mov', '.mkv', '.webm', '.avi', '.m4v')
SECRET_PATTERNS = [
    ('a private key', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('an AWS access key', re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
    ('an API token (sk-...)', re.compile(r'\bsk-[A-Za-z0-9_-]{20,}')),
    ('a GitHub token', re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}')),
    ('a Google API key', re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b')),
    ('a fal key (id:secret)', re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:[0-9a-f]{32}\b')),
    # RunPod rented-card settings. The key's form (it begins rpa_) is a BELIEF about RunPod's keys, not something read from their documents here; the settings-name
    # pattern below does not depend on that belief, so a key of any other form written next to its name is still caught.
    ('a RunPod API key (a belief: such keys begin rpa_)', re.compile(r'\brpa_[A-Za-z0-9]{20,}')),
    ('a rented-card setting written out (RUNPOD_API_KEY or RUNPOD_ENDPOINT_ID set to a value)',
     re.compile(r'\bRUNPOD_(?:API_KEY|ENDPOINT_ID)\b["\']?\s*[:=]\s*["\']?(?!your|YOUR|example|EXAMPLE|xxx|XXX|VALUE|NAME|\.\.\.|<|\$)[A-Za-z0-9_-]{16,}')),
    ('a rented-card endpoint address with its id', re.compile(r'api\.runpod\.ai/v2/[A-Za-z0-9]{10,}/')),
    ('a key or password written out', re.compile(r'(?i)\b(api[_-]?key|secret|password|access[_-]?token)\b["\']?\s*[:=]\s*["\'][^"\'\s]{12,}["\']')),
]


# ------------------------------------------------------------------------------------------------- small helpers
def load_json(path):
    """A JSON file, or a gzipped one (.gz)."""
    with (gzip.open(path, 'rt') if path.endswith('.gz') else open(path)) as handle:
        return json.load(handle)


def parse_size(value):
    """[w, h] from a list or from text like 'people-test-plate.jpg (1536 x 2730)'."""
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return [float(value[0]), float(value[1])]
    found = re.search(r'(\d+)\s*[x×]\s*(\d+)', str(value))
    return [float(found.group(1)), float(found.group(2))] if found else None


def megapixels(size):
    return size[0] * size[1] / 1e6


def when(text):
    """A date or date-time in ISO form ('2026-10-12' or '2026-10-12T14:00')."""
    text = str(text).strip()
    for form in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(text, form)
        except ValueError:
            pass
    raise SystemExit(f'plan_budget: "{text}" is not a date like 2026-10-12 or 2026-10-12T14:00')


def minutes_text(seconds):
    hours, rest = divmod(int(round(seconds)), 3600)
    return f'{hours} h {rest // 60:02d} min' if hours else f'{rest / 60:.1f} min'


# ------------------------------------------------------------------------------------------------- money
def narration_characters(script_path):
    """Credits are about the letters of page text sent, the bracketed cue included (logs 04, 07, 19, 33)."""
    script = load_json(script_path)
    return sum(len(page['text']) for page in script['pages'])


def plan_paintings(plan):
    """The paintings of a plan, or of a paintings ledger (returned_size, images_sent)."""
    rows = []
    for item in plan.get('paintings', []):
        returned = parse_size(item.get('returned') or item.get('returned_size'))
        sent = [parse_size(s) for s in (item.get('sent') or item.get('images_sent') or [])]
        if returned is None:
            raise SystemExit(f'plan_budget: painting "{item.get("name") or item.get("file")}" has no returned size')
        missing = [s for s, parsed in zip(item.get('sent') or item.get('images_sent') or [], sent) if parsed is None]
        rows.append({'name': item.get('name') or item.get('file') or 'painting', 'count': int(item.get('count', 1)),
                     'returned': returned, 'sent': [s for s in sent if s], 'sent_without_size': missing})
    return rows


def cost_plan(plan, settings, rate_cents=None, rate_date=None):
    """Prices a plan. rate_cents: today's fal rate (US cents a megapixel) if read; else the table's, with its date."""
    rate_entry = settings.entry('money.fal_flux_3_edit_cents_per_megapixel')
    rate = rate_cents if rate_cents is not None else rate_entry['value']
    rate_from = f'read today ({rate_date})' if rate_cents is not None else f'film-settings.json, read {rate_entry.get("date_read")}'
    rows, paint_cents = [], 0.0
    for p in plan_paintings(plan):
        mp_out, mp_in = megapixels(p['returned']), sum(megapixels(s) for s in p['sent'])
        cents = rate * (mp_out + mp_in)
        paint_cents += cents * p['count']
        rows.append({'what': p['name'], 'count': p['count'], 'megapixels_returned': round(mp_out, 3),
                     'megapixels_sent': round(mp_in, 3), 'cents_each': round(cents, 2), 'dollars': round(cents * p['count'] / 100, 4),
                     'note': ('a picture sent has no size: give it, it is charged too' if p['sent_without_size'] else '')})
    repaint_share = settings.value('budget_planner.repaint_share')
    repaint_cents = paint_cents * repaint_share
    sketches = int(plan.get('sketches', 0))
    sketch_cents = sketches * settings.value('money.nano_banana_pro_cents')
    characters = int(plan.get('narration_characters', 0))
    for path in plan.get('narration_scripts', []):
        characters += narration_characters(path)
    credits = characters * settings.value('money.elevenlabs_credits_per_letter')
    dollars_per_credit = settings.value('money.elevenlabs_dollars_per_credit')
    narration_dollars = credits * dollars_per_credit
    rerecord_pages = int(plan.get('rerecord_pages', settings.value('budget_planner.rerecord_reserve_pages') if characters else 0))
    pages = sum(len(load_json(p)['pages']) for p in plan.get('narration_scripts', [])) or int(plan.get('narration_pages', 0)) or None
    rerecord_dollars = (narration_dollars / pages * rerecord_pages) if (pages and rerecord_pages) else 0.0
    other = [{'what': o.get('what', 'other'), 'dollars': float(o['dollars'])} for o in plan.get('other_dollars', [])]
    lines = rows + ([{'what': f'repaint reserve ({repaint_share:g} of the paintings)', 'dollars': round(repaint_cents / 100, 4)}] if paint_cents else [])
    if sketches:
        lines.append({'what': f'{sketches} sketches (Nano Banana Pro)', 'dollars': round(sketch_cents / 100, 4)})
    if characters:
        lines.append({'what': f'narration: {characters:,} characters = {credits:,.0f} credits', 'dollars': round(narration_dollars, 4)})
    if rerecord_dollars:
        lines.append({'what': f're-record reserve ({rerecord_pages} page)', 'dollars': round(rerecord_dollars, 4)})
    lines += other
    total = round(paint_cents / 100 + repaint_cents / 100 + sketch_cents / 100 + narration_dollars + rerecord_dollars
                  + sum(o['dollars'] for o in other), 4)
    return {'rate_cents_per_megapixel': rate, 'rate_from': rate_from, 'lines': lines,
            'paintings_dollars': round(paint_cents / 100, 4), 'narration_characters': characters, 'narration_credits': credits,
            'narration_dollars': round(narration_dollars, 4), 'total_dollars': total}


def ledger_state(ledger, allowance_name=None, today=None, settings=None):
    """What has been spent from an allowance, counted from the date it began, and what is left."""
    allowances = ledger.get('allowances', [])
    if not allowances:
        raise SystemExit('plan_budget: the ledger has no "allowances" (each: name, dollars, start)')
    if allowance_name:
        chosen = [a for a in allowances if a['name'] == allowance_name]
        if not chosen:
            raise SystemExit(f'plan_budget: no allowance "{allowance_name}" (the ledger has: {", ".join(a["name"] for a in allowances)})')
        allowance = chosen[0]
    else:
        allowance = max(allowances, key=lambda a: when(a['start']))
    start = when(allowance['start'])
    end = when(allowance['end']) if allowance.get('end') else None
    until = when(today) if today else None
    covers = set(allowance.get('covers') or [])
    counted, skipped = [], []
    for entry in ledger.get('entries', []):
        moment = when(entry['when'])
        dollars = float(entry['dollars']) if 'dollars' in entry else float(entry.get('cents', 0)) / 100
        inside = moment >= start and (end is None or moment < end) and (until is None or moment <= until)
        if inside and (not covers or entry.get('service') in covers):
            counted.append(dict(entry, dollars=dollars))
        else:
            skipped.append(dict(entry, dollars=dollars))
    spent = round(sum(e['dollars'] for e in counted), 4)
    line, line_from = allowance.get('spending_line'), 'the ledger\'s allowance'
    if line is None and settings is not None:
        house = settings.value('money.user_allowance_dollars')
        if isinstance(house, dict) and float(house.get('allowance', -1)) == float(allowance['dollars']):
            line, line_from = house.get('spending_line'), 'film-settings.json money.user_allowance_dollars'
    return {'allowance': allowance['name'], 'allowance_dollars': float(allowance['dollars']), 'start': allowance['start'],
            'spending_line_dollars': float(line) if line is not None else None, 'spending_line_from': line_from if line is not None else None,
            'spent_dollars': spent, 'left_dollars': round(float(allowance['dollars']) - spent, 4),
            'entries_counted': len(counted), 'entries_before_or_outside': len(skipped), 'counted': counted,
            'spent_all_entries_dollars': round(sum(e['dollars'] for e in counted + skipped), 4)}


# ------------------------------------------------------------------------------------------------- frames
def camera_key(camera):
    return tuple(round(float(v), 6) for v in camera) if camera else None


def classify_frames(events):
    """Each frame's kind, from page events: a page join (two pages drawn), moving (the same shot's camera changed since the
    last frame: a slide), held with live effects (smoke, flame, flicker shown) or held with nothing live. A cut (a new
    shot) counts as held. Returns [{'frame', 'kind', 'view', 'page'}] in frame order."""
    frames = sorted(events['frames'], key=lambda item: item['f'])
    previous, found = {}, []
    for item in frames:
        drawn = [p for p in item['pages'] if p.get('drew', True)]
        if not drawn:
            continue
        if item.get('join'):
            kind, main = 'join', drawn[0]
        else:
            main = drawn[0]
            before = previous.get(main['page'])
            moved = before is not None and before[0] == main.get('shot') and before[1] != camera_key(main.get('camera'))
            kind = 'moving' if moved else ('held_live' if (main.get('effects_shown') or 0) > 0 else 'held_still')
        for p in drawn:
            previous[p['page']] = (p.get('shot'), camera_key(p.get('camera')))
        found.append({'frame': item['f'], 'kind': kind, 'view': main.get('shot') or f'page {main["page"]}', 'page': main['page']})
    return found


def frame_mix(classified, first, last):
    """Counts of each kind (and of each kind per view) for frames first <= f < last."""
    mix, by_view = {k: 0 for k in CLASSES}, {}
    for item in classified:
        if first <= item['frame'] < last:
            mix[item['kind']] += 1
            by_view.setdefault(item['view'], {k: 0 for k in CLASSES})[item['kind']] += 1
    return mix, by_view


def scene_info(events):
    """frames and page_edge_frames as render-paper-film.mjs --info gives them (the same rounding)."""
    start, end, fps = events.get('scene_start', 0.0), events['scene_end'], events.get('fps', 30)
    return {'start': start, 'end': end, 'frames': int(round((end - start) * fps)),
            'page_edge_frames': [int(round((s - start) * fps)) for s in events.get('page_edges', [])]}


def chunk_list(info, chunk_frames):
    """The chunks film-chapter-parallel.sh films: page edges first, then each page cut into pieces of at most
    CHUNK_FRAMES (the same sum as its python lines, Python's own round())."""
    edges = [0] + list(info['page_edge_frames']) + [info['frames']]
    chunks = []
    for a, b in zip(edges, edges[1:]):
        n = max(1, round((b - a) / chunk_frames))
        cuts = [a + round(i * (b - a) / n) for i in range(n + 1)]
        chunks += list(zip(cuts, cuts[1:]))
    return chunks


def pieces_of(a, b, piece_frames):
    return [(x, min(x + piece_frames, b)) for x in range(a, b, piece_frames)]


# ------------------------------------------------------------------------------------------------- rates
def table_rates(settings, workers=1):
    """The fallback: film-settings.json's measured costs (round 4, one worker)."""
    held_still = settings.value('filming.seconds_per_frame_held_nothing_live')
    return {'seconds_per_frame': {'held_still': held_still['one_worker'], 'held_live': settings.value('filming.seconds_per_frame_held_live_effects'),
                                  'moving': settings.value('filming.seconds_per_frame_sliding'),
                                  'join': settings.value('filming.seconds_per_frame_held_live_effects') * settings.value('filming.peel_frames_cost_factor')},
            'seconds_loading_a_piece': settings.value('filming.seconds_loading_a_piece'),
            'source': 'the table in film-settings.json (round 4, one worker): a fallback, not measured on this film'}


def read_logs(paths):
    """Pieces and chunks from filming logs. Returns {'pieces': [{first, last (exclusive), wall, stretches:
    [(first, last, seconds, is_first)]}], 'chunks': {(first, last): seconds}}."""
    texts = []
    for path in paths:
        if os.path.isdir(path):
            for log in sorted(glob.glob(os.path.join(path, '*.mp4.log'))):
                texts.append(open(log).read())
            for log in glob.glob(os.path.join(path, '..', '*filming.log')) + glob.glob(os.path.join(path, '*filming.log')):
                texts.append(open(log).read())
        else:
            texts.append(open(path).read())
    pieces, chunks = [], {}
    for text in texts:
        current = None
        for line in text.splitlines():
            m = re.match(r'frames (\d+)-(\d+) filmed in (\d+) s', line)
            if m:
                chunks[(int(m.group(1)), int(m.group(2)))] = float(m.group(3))
                continue
            m = re.match(r'scene .* drawing (\d+) to (\d+)', line)
            if m:
                current = {'first': int(m.group(1)), 'last': int(m.group(2)) + 1, 'wall': None, 'marks': []}
                pieces.append(current)
                continue
            m = re.match(r'frame (\d+)/\d+, (\d+) ms a frame', line)
            if m and current is not None:
                current['marks'].append((int(m.group(1)), int(m.group(2)) / 1000.0))
                continue
            m = re.match(r'wrote .* in (\d+) s', line)
            if m and current is not None:
                current['wall'] = float(m.group(1))
                current = None
    for piece in pieces:
        stretches, total_before, count_before = [], 0.0, 0
        for frame, average in piece.pop('marks'):
            count = frame - piece['first'] + 1
            total = average * count
            stretches.append((piece['first'] + count_before, frame + 1, total - total_before, count_before == 0))
            total_before, count_before = total, count
        piece['stretches'] = stretches
    return {'pieces': [p for p in pieces if p['wall'] is not None], 'chunks': chunks}


def counts_for(classified, first, last, join_factor):
    """The unknowns' counts for frames first <= f < last: held frames (a join frame counts as join_factor held frames)
    and moving frames per view."""
    counts = {'held': 0.0}
    for item in classified:
        if first <= item['frame'] < last:
            if item['kind'] == 'moving':
                counts[('moving', item['view'])] = counts.get(('moving', item['view']), 0) + 1
            else:
                counts['held'] += join_factor if item['kind'] == 'join' else 1
    return counts


def equations(logs, classified, join_factor, chunks=None):
    """Least-squares rows: each whole piece (its wall time = its frames' costs + one load) and each later 60-frame stretch
    inside it (frames' costs only). Returns rows of (chunk, counts, loads, seconds)."""
    rows = []
    for piece in logs['pieces']:
        owner = next(((a, b) for (a, b) in (chunks or []) if a <= piece['first'] and piece['last'] <= b), None)
        rows.append((owner, counts_for(classified, piece['first'], piece['last'], join_factor), 1, piece['wall']))
        for first, last, seconds, is_first in piece['stretches']:
            if not is_first:
                rows.append((owner, counts_for(classified, first, last, join_factor), 0, seconds))
    return rows


def fit_rates(rows, join_factor):
    """Seconds a frame held, seconds a frame moving in each view (a view whose slide is not in the rows gets the mean of
    the others) and seconds loading a piece, by least squares (numpy)."""
    import numpy
    keys = ['held'] + sorted({k for _, counts, _, _ in rows for k in counts if k != 'held' and counts[k] > 0}, key=str) + ['load']
    matrix = numpy.array([[counts.get(k, 0) for k in keys[:-1]] + [loads] for _, counts, loads, _ in rows], float)
    target = numpy.array([seconds for _, _, _, seconds in rows], float)
    present = matrix.sum(axis=0) > 0
    solution = numpy.zeros(len(keys))
    solution[present] = numpy.linalg.lstsq(matrix[:, present], target, rcond=None)[0]
    fitted = dict(zip(keys, (float(x) for x in solution)))
    moving_by_view = {k[1]: v for k, v in fitted.items() if isinstance(k, tuple)}
    moving = statistics.mean(moving_by_view.values()) if moving_by_view else 0.0
    return {'seconds_per_frame': {'held_still': fitted['held'], 'held_live': fitted['held'], 'moving': moving,
                                  'join': fitted['held'] * join_factor},
            'moving_by_view': moving_by_view, 'seconds_loading_a_piece': fitted['load']}


def predict_seconds(mix, pieces, rates, speed_up=1.0, moving_by_view=None):
    """Seconds to film frames of these kinds (mix: counts by kind; moving_by_view: moving counts by view, priced at each
    view's own rate when the rates have one) plus one load per piece, divided by the workers' speed-up."""
    spf = rates['seconds_per_frame']
    own = rates.get('moving_by_view') or {}
    frames_cost = sum(mix[k] * spf[k] for k in CLASSES if k != 'moving')
    if moving_by_view:
        frames_cost += sum(n * own.get(view, spf['moving']) for view, n in moving_by_view.items())
    else:
        frames_cost += mix['moving'] * spf['moving']
    return (frames_cost + pieces * rates['seconds_loading_a_piece']) / speed_up


def moving_counts(by_view):
    return {view: counts['moving'] for view, counts in by_view.items() if counts['moving']}


def measure_rates(logs, classified, settings, leave_out=False):
    """Rates fitted on the logs; with leave_out, also each chunk predicted from rates fitted on the OTHER chunks."""
    join_factor = settings.value('filming.peel_frames_cost_factor')
    chunks = sorted(logs['chunks'])
    rows = equations(logs, classified, join_factor, chunks)
    fitted = fit_rates(rows, join_factor)
    fitted['source'] = f'measured: fitted to {len(logs["pieces"])} filmed pieces ({len(rows)} timings) from the logs given'
    result = {'rates': fitted, 'held_by_view': steady_held_by_view(logs, classified)}
    if leave_out and chunks:
        checks = []
        for chunk in chunks:
            others = fit_rates([r for r in rows if r[0] != chunk], join_factor)
            own = [p for p in logs['pieces'] if chunk[0] <= p['first'] and p['last'] <= chunk[1]]
            mix, by_view = frame_mix(classified, chunk[0], chunk[1])
            predicted = predict_seconds(mix, len(own), others, moving_by_view=moving_counts(by_view))
            checks.append({'chunk': list(chunk), 'measured_seconds': logs['chunks'][chunk], 'predicted_seconds': round(predicted, 1),
                           'pieces': len(own)})
        measured = sum(c['measured_seconds'] for c in checks)
        predicted = sum(c['predicted_seconds'] for c in checks)
        result['leave_one_chunk_out'] = {'chunks': checks, 'measured_seconds': measured, 'predicted_seconds': round(predicted, 1),
                                         'error_share': round(predicted / measured - 1, 4),
                                         'largest_chunk_error_share': round(max(abs(c['predicted_seconds'] / c['measured_seconds'] - 1) for c in checks), 4)}
    return result


def steady_held_by_view(logs, classified):
    """Seconds a frame of later stretches that are all held frames of one view (for the report)."""
    found = {}
    for piece in logs['pieces']:
        for first, last, seconds, is_first in piece['stretches']:
            if is_first:
                continue
            kinds = {(c['kind'], c['view']) for c in classified if first <= c['frame'] < last}
            if len(kinds) == 1:
                kind, view = kinds.pop()
                found.setdefault(f'{CLASS_WORDS[kind]} ({view})', []).append(seconds / (last - first))
    return {k: {'seconds_a_frame': round(statistics.mean(v), 3), 'stretches': len(v)} for k, v in sorted(found.items())}


def profile_stretches(classified, length=60):
    """The short pieces to film before planning, each 2 x length frames: the first stretch takes the page loading, the
    second is measured clean (render-paper-film.mjs prints the time of every 60 frames). For each view one held piece,
    and for each slide one piece whose second stretch is the slide."""
    runs = []
    for item in classified:
        if runs and runs[-1]['kind'] == item['kind'] and runs[-1]['view'] == item['view'] and runs[-1]['last'] == item['frame']:
            runs[-1]['last'] = item['frame'] + 1
        else:
            runs.append({'kind': item['kind'], 'view': item['view'], 'first': item['frame'], 'last': item['frame'] + 1})
    first_frame = classified[0]['frame'] if classified else 0
    chosen, seen = [], set()
    for run in runs:
        if run['kind'] in ('held_live', 'held_still') and ('held', run['view']) not in seen and run['last'] - run['first'] >= 2 * length:
            seen.add(('held', run['view']))
            chosen.append({'why': f'held ({run["view"]})', 'first': run['first'], 'last': run['first'] + 2 * length,
                           'measured': [run['first'] + length, run['first'] + 2 * length]})
        if run['kind'] == 'moving' and ('moving', run['view']) not in seen and run['last'] - run['first'] >= length:
            seen.add(('moving', run['view']))
            start = max(first_frame, run['first'] - length)
            chosen.append({'why': f'moving ({run["view"]})', 'first': start, 'last': start + 2 * length,
                           'measured': [start + length, start + 2 * length]})
    return chosen


# ------------------------------------------------------------------------------------------------- machine
def free_memory_gb():
    try:
        for line in open('/proc/meminfo'):
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) / 1024 / 1024
    except OSError:
        pass
    return None


def blender_running():
    """Process numbers of running Blender programs (read from /proc; nothing is stopped)."""
    found = []
    for folder in glob.glob('/proc/[0-9]*'):
        try:
            name = open(os.path.join(folder, 'comm')).read().strip()
        except OSError:
            continue
        if name.lower().startswith('blender'):
            found.append(int(os.path.basename(folder)))
    return sorted(found)


def piece_frames_for(load_seconds, seconds_a_frame, settings):
    """Frames a piece should hold: big enough that loading is at most budget_planner.piece_load_share_max of it, small
    enough that a restart loses at most budget_planner.restart_loss_max_seconds, and never under piece_frames_min."""
    share = settings.value('budget_planner.piece_load_share_max')
    loss = settings.value('budget_planner.restart_loss_max_seconds')
    smallest = settings.value('budget_planner.piece_frames_min')
    by_load = math.ceil(load_seconds / (share * seconds_a_frame)) if seconds_a_frame > 0 else smallest
    by_loss = math.floor(loss / seconds_a_frame) if seconds_a_frame > 0 else by_load
    return max(smallest, min(by_load, by_loss)), {'by_load': by_load, 'by_loss': by_loss}


def plan_filming(events, settings, scene, rates=None, first=None, last=None, processors=None, free_memory=None,
                 heavy_pages=None, views_per_page=1, blender=None, free_disk=None):
    classified = classify_frames(events)
    info = scene_info(events)
    first = first if first is not None else min(c['frame'] for c in classified)
    last = last if last is not None else max(c['frame'] for c in classified) + 1
    rates = rates or table_rates(settings)
    spf = rates['seconds_per_frame']
    load = rates['seconds_loading_a_piece']
    mix, by_view = frame_mix(classified, first, last)
    frames = sum(mix.values())
    steady = predict_seconds(mix, 0, rates, 1.0, moving_counts(by_view)) / frames if frames else 0.0
    problems, notes = [], []
    # workers: one on 2 processors, two on 4 or more (two are about 17% faster held; no gain while moving)
    processors = processors or os.cpu_count() or 1
    workers_table = settings.value('filming.workers')
    workers = workers_table['two_processors'] if processors <= 2 else workers_table['four_processors']
    memory_per_piece = settings.value('filming.memory_per_piece_gb')[1]
    reserve = settings.value('budget_planner.memory_reserve_gb')
    free_memory = free_memory if free_memory is not None else free_memory_gb()
    if free_memory is not None:
        fits = int((free_memory - reserve) // (memory_per_piece * max(1, views_per_page)))
        if fits < 1:
            problems.append(f'memory: {free_memory:.1f} GB free is not enough for one worker ({memory_per_piece} GB a piece x '
                            f'{views_per_page} view(s) + {reserve} GB kept free)')
        elif fits < workers:
            notes.append(f'memory allows only {fits} worker(s) ({free_memory:.1f} GB free)')
            workers = fits
    moving_share = mix['moving'] / frames if frames else 0
    speed_up = 1 + settings.value('filming.workers')['two_workers_speed_gain'] * (1 - moving_share) if workers >= 2 else 1.0
    # lazy loading: a chapter that is not lazy loads every page's set at once; each loaded set takes memory_per_piece_gb
    # (measured, log 34), so with more heavy pages than the free memory holds, only lazy loading works
    lazy_reasons = []
    if heavy_pages is not None and free_memory is not None and heavy_pages * memory_per_piece > free_memory - reserve:
        lazy_reasons.append(f'{heavy_pages} pages carrying painted sets need about {heavy_pages * memory_per_piece:.0f} GB loaded at once, '
                            f'more than the {free_memory:.1f} GB free (less {reserve} GB kept free)')
    lazy = bool(lazy_reasons)
    # piece and chunk size
    piece_frames, piece_why = piece_frames_for(load, steady, settings)
    chunk_frames = piece_frames
    chunks = [c for c in chunk_list(info, chunk_frames) if c[0] >= first and c[1] <= last]
    if not chunks:
        chunks = [(first, last)]
    # stretches under 2 hours of a background job (minus a margin)
    limit = settings.value('filming.stretch_max_hours') * 3600 - settings.value('budget_planner.stretch_margin_minutes') * 60
    stretches, current = [], None
    for a, b in chunks:
        chunk_mix, chunk_views = frame_mix(classified, a, b)
        seconds = predict_seconds(chunk_mix, len(pieces_of(a, b, piece_frames)), rates, speed_up, moving_counts(chunk_views))
        if current and current['seconds'] + seconds > limit:
            stretches.append(current)
            current = None
        if current is None:
            current = {'from': a, 'to': b, 'seconds': 0.0}
        current['to'] = b
        current['seconds'] += seconds
    if current:
        stretches.append(current)
    total = sum(s['seconds'] for s in stretches)
    for s in stretches:
        s['command'] = (f'FILM_FROM={s["from"]} FILM_TO={s["to"]} PIECE_FRAMES={piece_frames} '
                        f'bash paper-film/tools/film-chapter-parallel.sh {scene} {workers} {chunk_frames}')
        s['seconds'] = round(s['seconds'], 1)
    pieces_total = sum(len(pieces_of(a, b, piece_frames)) for a, b in chunks)
    # Blender and disk
    blender = blender_running() if blender is None else blender
    if blender:
        busy = settings.value('budget_planner.busy_machine_factor')
        problems.append(f'Blender is running (process {", ".join(map(str, blender))}): filming alongside it runs about {busy} times '
                        f'slower and can run out of memory; wait for it to finish (the plan below assumes it has)')
    film_megabytes = frames / settings.value('frame.frames_per_second') * settings.value('filming.film_with_grain_megabytes_per_second') \
        * settings.value('budget_planner.film_copies')
    free_disk = free_disk if free_disk is not None else shutil.disk_usage(KIT).free / 1e9
    disk_reserve = settings.value('budget_planner.disk_free_reserve_gb')
    if free_disk - film_megabytes / 1000 < disk_reserve:
        problems.append(f'disk: filming needs about {film_megabytes / 1000:.2f} GB and would leave {free_disk - film_megabytes / 1000:.2f} GB '
                        f'free (keep {disk_reserve} GB)')
    return {'scene': scene, 'frames': [first, last], 'frame_count': frames, 'frame_kinds': mix, 'frame_kinds_by_view': by_view,
            'rates': rates, 'steady_seconds_a_frame': round(steady, 3), 'workers': workers, 'speed_up': round(speed_up, 3),
            'processors': processors, 'free_memory_gb': None if free_memory is None else round(free_memory, 1),
            'piece_frames': piece_frames, 'piece_frames_why': piece_why, 'chunk_frames': chunk_frames, 'pieces': pieces_total,
            'chunks': len(chunks), 'predicted_seconds': round(total, 1), 'stretches': stretches, 'stretch_limit_seconds': limit,
            'lazy': lazy, 'lazy_reasons': lazy_reasons, 'film_megabytes': round(film_megabytes), 'free_disk_gb': round(free_disk, 2),
            'blender_running': blender, 'problems': problems, 'notes': notes}


# ------------------------------------------------------------------------------------------------- disk, push, status
def disk_needed(settings, seconds, copies=None, exports_megabytes=0.0, stills=0, still_megabytes=0.5):
    copies = copies or settings.value('budget_planner.film_copies')
    film = seconds * settings.value('filming.film_with_grain_megabytes_per_second') * copies
    return {'film_megabytes': round(film, 1), 'exports_megabytes': exports_megabytes, 'stills_megabytes': stills * still_megabytes,
            'total_gb': round((film + exports_megabytes + stills * still_megabytes) / 1000, 3)}


def files_to_check(paths, repo=None):
    found = []
    if repo:
        listing = subprocess.run(['git', '-C', repo, 'status', '--porcelain', '--untracked-files=all'], capture_output=True, text=True).stdout
        for line in listing.splitlines():
            name = line[3:].strip().strip('"')
            if ' -> ' in name:
                name = name.split(' -> ')[1]
            full = os.path.join(repo, name)
            if os.path.isfile(full) and not line.startswith(' D') and not line.startswith('D '):
                found.append(full)
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__')]
                found += [os.path.join(root, f) for f in files]
        elif os.path.isfile(path):
            found.append(path)
    return sorted(set(found))


def check_push(files, settings):
    """Refuses audio and video, files over the repository limit and anything that looks like a key; packs the rest into
    pushes under the batch limit and chat parts under the sendable limit (largest first)."""
    file_limit = settings.value('delivery.repository_file_max_megabytes') * 1e6
    batch_limit = settings.value('delivery.repository_batch_max_megabytes') * 1e6
    part_limit = settings.value('delivery.sendable_megabytes') * 1e6
    refused, sizes = [], {}
    for path in files:
        size = os.path.getsize(path)
        sizes[path] = size
        if path.lower().endswith(AUDIO_VIDEO):
            refused.append({'file': path, 'why': 'audio or video (the user\'s rule: none in the repository)'})
            continue
        if size > file_limit:
            refused.append({'file': path, 'why': f'{size / 1e6:.1f} MB, over {file_limit / 1e6:.0f} MB (GitHub refuses 100 MB)'})
            continue
        if size < 5e6:
            try:
                text = open(path, encoding='utf-8').read()
            except (UnicodeDecodeError, OSError):
                continue
            for what, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    refused.append({'file': path, 'why': f'looks like it holds {what}'})
                    break
    kept = sorted((p for p in files if p not in {r['file'] for r in refused}), key=lambda p: -sizes[p])

    def pack(limit):
        bins = []
        for path in kept:
            for b in bins:
                if b['bytes'] + sizes[path] <= limit:
                    b['files'].append(path)
                    b['bytes'] += sizes[path]
                    break
            else:
                bins.append({'files': [path], 'bytes': sizes[path]})
        return [{'files': len(b['files']), 'megabytes': round(b['bytes'] / 1e6, 2)} for b in bins]
    return {'files': len(files), 'refused': refused, 'megabytes': round(sum(sizes[p] for p in kept) / 1e6, 2),
            'pushes': pack(batch_limit), 'chat_parts': pack(part_limit)}


def filming_status(folder, piece_seconds, settings):
    """running / stalled / stopped / finished, from the newest file's age and the render processes still alive."""
    files = [os.path.join(folder, f) for f in os.listdir(folder)] if os.path.isdir(folder) else []
    newest = max((os.path.getmtime(f) for f in files), default=None)
    age = time.time() - newest if newest else None
    alive = []
    for proc in glob.glob('/proc/[0-9]*'):
        try:
            command = open(os.path.join(proc, 'cmdline')).read().replace('\0', ' ')
        except OSError:
            continue
        if 'render-paper-film.mjs' in command and os.path.basename(folder.rstrip('/')).replace('-chunks', '') in command:
            alive.append(int(os.path.basename(proc)))
    stalled_after = settings.value('budget_planner.stalled_after_piece_times') * piece_seconds
    log = sorted(glob.glob(os.path.join(os.path.dirname(folder.rstrip('/')), '*filming.log')))
    last_line = open(log[-1]).read().strip().splitlines()[-1] if log and open(log[-1]).read().strip() else ''
    if not alive and 'joined:' in last_line:
        state = 'finished'
    elif not alive:
        state = 'stopped'
    elif age is not None and age > stalled_after:
        state = 'stalled'
    else:
        state = 'running'
    return {'state': state, 'newest_file_age_seconds': None if age is None else round(age), 'stalled_after_seconds': stalled_after,
            'render_processes': alive, 'last_log_line': last_line}


# ------------------------------------------------------------------------------------------------- command line
def report_filming(plan):
    lines = [f'Filming plan for {plan["scene"]}, frames {plan["frames"][0]} to {plan["frames"][1] - 1} ({plan["frame_count"]} frames):']
    for kind in CLASSES:
        if plan['frame_kinds'][kind]:
            lines.append(f'  {plan["frame_kinds"][kind]:5d} frames {CLASS_WORDS[kind]} at {plan["rates"]["seconds_per_frame"][kind]:.2f} s')
    lines.append(f'  loading: {plan["pieces"]} pieces x {plan["rates"]["seconds_loading_a_piece"]:.0f} s')
    lines.append(f'  rates from: {plan["rates"]["source"]}')
    lines.append(f'Predicted: {minutes_text(plan["predicted_seconds"])} with {plan["workers"]} worker(s) on {plan["processors"]} processors '
                 f'(speed-up {plan["speed_up"]:.2f}).')
    lines.append(f'Pieces of {plan["piece_frames"]} frames (loading stays under its share: {plan["piece_frames_why"]["by_load"]}; a restart '
                 f'loses at most {plan["piece_frames_why"]["by_loss"]} frames), chunks of {plan["chunk_frames"]}.')
    lines.append(f'Lazy loading: {"ON" if plan["lazy"] else "off"}' + (f' ({"; ".join(plan["lazy_reasons"])})' if plan['lazy_reasons'] else ''))
    lines.append(f'{len(plan["stretches"])} stretch(es), each under {minutes_text(plan["stretch_limit_seconds"])} (run each as its own job; '
                 'running a command again carries on where it stopped):')
    for s in plan['stretches']:
        lines.append(f'  {minutes_text(s["seconds"]):>12}  {s["command"]}')
    lines.append(f'Disk: about {plan["film_megabytes"]} MB of film; {plan["free_disk_gb"]} GB free.')
    for note in plan['notes']:
        lines.append(f'NOTE  {note}')
    for problem in plan['problems']:
        lines.append(f'STOP  {problem}')
    lines.append('Watch it with: python3 kit/calculators/plan_budget.py status paper-film/out/SCENE-chunks (stalled = no new file '
                 'for twice a piece\'s time). Stop a run only by its own process number, never with pkill -f.')
    return lines


def main():
    parser = argparse.ArgumentParser(description='Plans money, filming time, workers, pieces, memory, disk and pushes '
                                                 '(see the note at the top of this file).')
    sub = parser.add_subparsers(dest='command', required=True)
    p = add_output_options(sub.add_parser('cost', help='price a plan of paid steps'))
    p.add_argument('plan')
    p.add_argument('--rate', type=float, help='today\'s fal rate in US cents a megapixel (read it before every paid batch)')
    p.add_argument('--rate-date', default=datetime.now().strftime('%Y-%m-%d'))
    p.add_argument('--ledger')
    p.add_argument('--allowance')
    p = add_output_options(sub.add_parser('ledger', help='what is spent and left of an allowance'))
    p.add_argument('ledger')
    p.add_argument('--allowance')
    p.add_argument('--next-cost', type=float, help='dollars the next paid step would cost: refused (exit 2) if over what is left')
    p.add_argument('--today')
    p = add_output_options(sub.add_parser('frames', help='each frame\'s kind, counted, from page events'))
    p.add_argument('events')
    p.add_argument('--from-frame', type=int)
    p.add_argument('--to-frame', type=int)
    p = add_output_options(sub.add_parser('profile-commands', help='the short pieces to film first, to measure this film\'s costs'))
    p.add_argument('events')
    p.add_argument('--scene', required=True)
    p = add_output_options(sub.add_parser('measure', help='seconds a frame and loading, fitted to filming logs'))
    p.add_argument('logs', nargs='+')
    p.add_argument('--events', required=True)
    p.add_argument('--leave-out-chunks', action='store_true', help='also predict each chunk from the others (a fair check)')
    p = add_output_options(sub.add_parser('filming', help='the filming plan: time, workers, pieces, stretches, lazy, memory, disk'))
    p.add_argument('events')
    p.add_argument('--scene', required=True)
    p.add_argument('--rates', help='RATES.json from measure (else the table in film-settings.json)')
    p.add_argument('--from-frame', type=int)
    p.add_argument('--to-frame', type=int)
    p.add_argument('--processors', type=int)
    p.add_argument('--free-memory-gb', type=float)
    p.add_argument('--heavy-pages', type=int, help='how many pages carry painted sets')
    p.add_argument('--views-per-page', type=int, default=1)
    p.add_argument('--blender-running', choices=['yes', 'no', 'auto'], default='auto')
    p.add_argument('--free-disk-gb', type=float)
    p = add_output_options(sub.add_parser('disk', help='disk a filming or export needs'))
    p.add_argument('--seconds', type=float, required=True)
    p.add_argument('--copies', type=int)
    p.add_argument('--exports-megabytes', type=float, default=0.0)
    p.add_argument('--stills', type=int, default=0)
    p.add_argument('--free-disk-gb', type=float)
    p = add_output_options(sub.add_parser('push', help='check files before pushing or sending'))
    p.add_argument('paths', nargs='*')
    p.add_argument('--git', help='a repository: check its changed and new files')
    p = add_output_options(sub.add_parser('status', help='is a filming run still going?'))
    p.add_argument('folder')
    p.add_argument('--piece-seconds', type=float, default=None)
    args = parser.parse_args()
    settings = load_settings(args.settings)
    lines, result, code = [], {}, 0

    if args.command == 'cost':
        plan = load_json(args.plan)
        result = cost_plan(plan, settings, args.rate, args.rate_date if args.rate is not None else None)
        lines.append(f'Cost of {args.plan} at {result["rate_cents_per_megapixel"]} US cents a megapixel ({result["rate_from"]}):')
        for row in result['lines']:
            extra = f' ({row["megapixels_returned"]} MP returned + {row["megapixels_sent"]} MP sent, {row["cents_each"]} c each)' if 'cents_each' in row else ''
            lines.append(f'  US${row["dollars"]:.2f}  {row["what"]}' + (f' x {row["count"]}' if row.get('count', 1) > 1 else '') + extra
                         + (f'  NOTE: {row["note"]}' if row.get('note') else ''))
        lines.append(f'Total: about US${result["total_dollars"]:.2f}. Prices are estimates: fal shows no exact charge, and ElevenLabs\' '
                     'dollars a credit was counted by text length, not billed.')
        if args.ledger:
            state = ledger_state(load_json(args.ledger), args.allowance, settings=settings)
            result['ledger'] = {k: v for k, v in state.items() if k != 'counted'}
            lines.append(f'Allowance "{state["allowance"]}": US${state["spent_dollars"]:.2f} spent since {state["start"]}, US${state["left_dollars"]:.2f} left.')
            if result['total_dollars'] > state['left_dollars']:
                lines.append(f'REFUSED: this plan (US${result["total_dollars"]:.2f}) is more than is left. Ask the user for more, or plan less.')
                code = 2
        lines.append('Ask the user with these numbers before any paid call; a vague reply ("that\'s ok") is not a yes to spending.')
    elif args.command == 'ledger':
        state = ledger_state(load_json(args.ledger), args.allowance, args.today, settings)
        result = state
        lines.append(f'Allowance "{state["allowance"]}": US${state["allowance_dollars"]:.2f} from {state["start"]}.')
        lines.append(f'  spent since then: US${state["spent_dollars"]:.2f} ({state["entries_counted"]} entries); left: US${state["left_dollars"]:.2f}')
        lines.append(f'  (all entries in the ledger, any date: US${state["spent_all_entries_dollars"]:.2f}; only those since the start count)')
        line = state.get('spending_line_dollars')
        if line is not None:
            lines.append(f'  spending line: US${line:.2f} of it ({state["spending_line_from"]}): paid steps stop there and the user is asked again; '
                         f'US${line - state["spent_dollars"]:.2f} before it')
        if args.next_cost is not None:
            result['next_cost_dollars'] = args.next_cost
            if args.next_cost > state['left_dollars']:
                lines.append(f'REFUSED: the next step (US${args.next_cost:.2f}) is more than the US${state["left_dollars"]:.2f} left.')
                code = 2
            elif line is not None and state['spent_dollars'] + args.next_cost > line:
                lines.append(f'REFUSED: the next step (US${args.next_cost:.2f}) would pass the spending line (US${line:.2f}; US${state["spent_dollars"]:.2f} '
                             'spent). Ask the user before going past it (paint_request.py refuses it too).')
                result['past_spending_line'] = True
                code = 2
            else:
                lines.append(f'The next step (US${args.next_cost:.2f}) fits; US${state["left_dollars"] - args.next_cost:.2f} would be left. '
                             'Still ask the user, with these numbers.')
    elif args.command == 'frames':
        events = load_json(args.events)
        classified = classify_frames(events)
        first = args.from_frame if args.from_frame is not None else classified[0]['frame']
        last = args.to_frame if args.to_frame is not None else classified[-1]['frame'] + 1
        mix, by_view = frame_mix(classified, first, last)
        result = {'frames': [first, last], 'frame_kinds': mix, 'frame_kinds_by_view': by_view}
        lines.append(f'Frames {first} to {last - 1}: ' + ', '.join(f'{mix[k]} {CLASS_WORDS[k]}' for k in CLASSES if mix[k]))
        for view, counts in by_view.items():
            lines.append(f'  {view}: ' + ', '.join(f'{counts[k]} {CLASS_WORDS[k]}' for k in CLASSES if counts[k]))
    elif args.command == 'profile-commands':
        events = load_json(args.events)
        chosen = profile_stretches(classify_frames(events))
        result = {'stretches': chosen}
        lines.append(f'Film these {len(chosen)} short pieces first (each loads its page in its first 60 frames, then 60 frames are timed clean; '
                     f'a few minutes each), then run measure on their logs:')
        for c in chosen:
            c['command'] = (f'node paper-film/tools/render-paper-film.mjs {args.scene} paper-film/out/profile-{c["first"]}.mp4 '
                            f'--frames {c["first"]} {c["last"]} > paper-film/out/profile-{c["first"]}.log 2>&1')
            lines.append(f'  {c["why"]}: {c["command"]}')
        lines.append(f'Then: python3 kit/calculators/plan_budget.py measure paper-film/out/profile-*.log --events {args.events} --out rates.json')
    elif args.command == 'measure':
        events = load_json(args.events)
        logs = read_logs(args.logs)
        if not logs['pieces']:
            raise SystemExit('plan_budget measure: no filmed pieces found in the logs given')
        result = measure_rates(logs, classify_frames(events), settings, args.leave_out_chunks)
        r = result['rates']
        lines.append(f'From {len(logs["pieces"])} filmed pieces: held {r["seconds_per_frame"]["held_live"]:.3f} s a frame, moving '
                     f'{r["seconds_per_frame"]["moving"]:.3f} s, a join {r["seconds_per_frame"]["join"]:.3f} s, loading '
                     f'{r["seconds_loading_a_piece"]:.1f} s a piece.')
        for view, v in result['held_by_view'].items():
            lines.append(f'  {view}: {v["seconds_a_frame"]:.2f} s a frame over {v["stretches"]} stretch(es)')
        if 'leave_one_chunk_out' in result:
            lo = result['leave_one_chunk_out']
            lines.append(f'Each chunk predicted from the other chunks only: {minutes_text(lo["predicted_seconds"])} against '
                         f'{minutes_text(lo["measured_seconds"])} measured ({lo["error_share"] * 100:+.1f}%).')
            for c in lo['chunks']:
                lines.append(f'  frames {c["chunk"][0]}-{c["chunk"][1]}: predicted {c["predicted_seconds"]:.0f} s, filmed in {c["measured_seconds"]:.0f} s')
        result = dict(result)
    elif args.command == 'filming':
        events = load_json(args.events)
        rates = load_json(args.rates)['rates'] if args.rates and 'rates' in load_json(args.rates) else (load_json(args.rates) if args.rates else None)
        blender = None if args.blender_running == 'auto' else ([0] if args.blender_running == 'yes' else [])
        result = plan_filming(events, settings, args.scene, rates, args.from_frame, args.to_frame, args.processors, args.free_memory_gb,
                              args.heavy_pages, args.views_per_page, blender, args.free_disk_gb)
        lines = report_filming(result)
        code = 1 if result['problems'] else 0
    elif args.command == 'disk':
        result = disk_needed(settings, args.seconds, args.copies, args.exports_megabytes, args.stills)
        free = args.free_disk_gb if args.free_disk_gb is not None else shutil.disk_usage(KIT).free / 1e9
        reserve = settings.value('budget_planner.disk_free_reserve_gb')
        result.update({'free_disk_gb': round(free, 2), 'left_after_gb': round(free - result['total_gb'], 2)})
        lines.append(f'Needs about {result["total_gb"]:.2f} GB ({result["film_megabytes"]:.0f} MB of film, {result["exports_megabytes"]:.0f} MB exports, '
                     f'{result["stills_megabytes"]:.0f} MB stills); {free:.2f} GB free, {free - result["total_gb"]:.2f} GB after.')
        if free - result['total_gb'] < reserve:
            lines.append(f'STOP: that leaves less than {reserve} GB free. Delete pieces of film already joined and checked first.')
            code = 1
    elif args.command == 'push':
        files = files_to_check(args.paths, args.git)
        result = check_push(files, settings)
        lines.append(f'{result["files"]} files, {result["megabytes"]} MB that may go: {len(result["pushes"])} push(es) under '
                     f'{settings.value("delivery.repository_batch_max_megabytes")} MB, {len(result["chat_parts"])} chat part(s) under '
                     f'{settings.value("delivery.sendable_megabytes")} MB.')
        for r in result['refused']:
            lines.append(f'REFUSED  {r["file"]}: {r["why"]}')
        if result['refused']:
            code = 2
        lines.append('Before a public push also check the repository is meant to be public (gh repo view --json visibility).')
    elif args.command == 'status':
        piece = args.piece_seconds or (settings.value('filming.piece_frames')['lazy_chapter'] * settings.value('filming.seconds_per_frame_held_live_effects')
                                       + settings.value('filming.seconds_loading_a_piece'))
        result = filming_status(args.folder, piece, settings)
        lines.append(f'Filming in {args.folder}: {result["state"].upper()} (newest file {result["newest_file_age_seconds"]} s old; stalled after '
                     f'{result["stalled_after_seconds"]:.0f} s; render processes: {result["render_processes"] or "none"}).')
        if result['last_log_line']:
            lines.append(f'  last log line: {result["last_log_line"]}')
        if result['state'] in ('stalled', 'stopped'):
            lines.append('  Run the same filming command again: finished pieces are kept and it carries on. Stop a stalled run '
                         'with kill PROCESS_NUMBER (the numbers above), never pkill -f.')
    finish(f'plan_budget {args.command}', result, lines, settings, args)
    return code


if __name__ == '__main__':
    sys.exit(run_main(main, 'plan_budget'))
