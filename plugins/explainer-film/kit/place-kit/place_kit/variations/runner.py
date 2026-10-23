"""What this does: runs a whole BATCH OF VARIATIONS, start to finish, and is what `explainer-film-place variations` calls. In order:
  1. read the variations file and CHECK BEFORE DRAWING that the variations are measurably different (near-duplicates are dropped, and the sentence says which and why) (spec.py);
  2. split them across up to 3 card jobs that run at the same time (spec.py), estimate the card seconds, and pass the card-time gate (the helper's allowance and the batch rule: one batch, look,
     at most one more) (card_time.py);
  3. draw: each job opens the scene once, and for each of its variations applies it, draws small quick pictures through every camera, measures nothing yet, and puts the scene back
     (worker.py and apply.py, inside Blender). On a rented card the jobs go out together; with --where local they run here, one after the other, on a tiny scene, for tests;
  4. CHECK AFTER DRAWING that the pictures differ (pairs that came out nearly the same are flagged), measure every picture against the baseline (compare.py);
  5. make ONE labelled contact sheet (sheet.py), write variations-result.json, and write every job's billed seconds into the card-time ledger.
The actions: `plan` (steps 1 and 2 only: free, draws nothing), `run` (all five), `sheet` (step 4 and 5 again from the pictures already in the run folder).
Exit: 0 done (read the LOOK lines), 1 a variation or a job failed, or the batch was refused (allowance, batch rule, nothing left to draw), 2 an input is missing or unusable.
Plain Python (standard library, numpy and Pillow for the pictures); Blender is started as a program only for --where local.

A concrete example: `explainer-film-place variations run moss.json --where rented --helper builder-walls --role builder` draws 10 variations through 2 cameras in 3 card jobs
(about 4 minutes of card seconds), then prints where the sheet is and the seconds each job billed.
"""
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

from .. import card_time, house_numbers as numbers
from ..render import client as client_module
from . import cards, compare, keys, scout as scout_module, sheet, spec as spec_module


class BatchRefused(Exception):
    """The batch was refused before anything was sent (the FAIL line was said)."""


# ------------------------------------------------------------------ small helpers
def _write_json(path, payload):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=1)


def _sha8(path):
    return client_module.file_checksum(path)[:8]


def default_run_folder(spec):
    return os.path.join(spec['folder'], os.path.splitext(os.path.basename(spec['path']))[0] + '-run')


def job_file_content(job, spec, scene, settings, out_folder, cameras, check_reset, hook_paths=None):
    """The job file the worker reads (place_kit/variations/worker.py describes it)."""
    entries = []
    for entry in job['entries']:
        item = {'name': entry['name'], 'is_baseline': bool(entry.get('is_baseline')), 'set': entry['set'], 'args': entry.get('args') or {}, 'reset': entry.get('reset', 'auto'), 'script': entry.get('script')}
        if item['script'] and hook_paths:
            item['script'] = hook_paths[item['script']]
        entries.append(item)
    return {'job': job['index'], 'scene': scene, 'settings': settings, 'out_folder': out_folder, 'cameras': cameras, 'engine': spec['engine'], 'size': spec['size'], 'samples': spec['samples'],
            'quality': numbers.value('place_variations.jpeg_quality'), 'check_reset': bool(check_reset and any(e.get('is_baseline') for e in job['entries'])), 'scout': bool(job.get('scout')),
            'entries': entries}


# ------------------------------------------------------------------ the plan
def make_plan(options, say=print, ledger_entries=None, for_run=False, drawn_here=False):
    """Reads and checks everything that costs nothing. Returns the plan dictionary; raises spec.SpecProblem (exit 2) or BatchRefused (exit 1).
    When a free scout of the same file and scene was drawn (scout.py), its pictures decide too: what the scout found nearly the same is dropped here, before any card.
    drawn_here: the batch will be drawn on this computer, so the card-seconds estimate is said as 'if it were sent to the cards'."""
    spec = spec_module.read_spec(options.spec, scene=getattr(options, 'scene', None), settings=getattr(options, 'settings', None), cameras=getattr(options, 'cameras', None),
                                 engine=getattr(options, 'engine', None) if getattr(options, 'engine', None) not in (None, 'auto') else None,
                                 size=_size_option(getattr(options, 'size', None)), samples=getattr(options, 'samples', None))
    scout_document, scout_line = scout_module.find_scout(spec, getattr(options, 'scout', None), bool(getattr(options, 'no_scout', False)))
    if scout_line:
        say(scout_line)
    saved = (scout_document or {}).get('saved_values') or None
    checked = spec_module.check_before(spec, saved)
    for line in checked['lines']:
        say(line)
    big_batch_override = False
    if checked['status'] == 'refuse':
        over = (getattr(options, 'over_allowance', None) or '').strip()
        if checked.get('too_many') and len(over) >= int(numbers.value('place_card_time.override_reason_letters_min')):
            big_batch_override = True
            say(f'LOOK before drawing: more than {numbers.value("place_variations.batch_size_max")} variations is allowed only because of the reason you wrote: "{over}".')
        else:
            raise BatchRefused('nothing was drawn')
    if scout_document:
        kept, scout_dropped, unscouted = scout_module.drops_from_scout(scout_document, checked['kept'])
        for drop in scout_dropped:
            say(f'LOOK dropped "{drop["name"]}": {drop["why"]}.')
        if unscouted:
            say(f'LOOK scout: {len(unscouted)} variation(s) were not in the scout (new or changed since), so it says nothing about them: ' + ', '.join(f'"{n}"' for n in unscouted) + '.')
        if not scout_dropped:
            say(f'PASS scout: none of the {len(kept)} variation(s) came out nearly the same in the scout.')
        faint_pairs = scout_module.faint_in_scout(scout_document, kept)
        if faint_pairs:
            shown = '; '.join(f'"{a}" and "{b}"' for a, b in faint_pairs[:4]) + (f'; and {len(faint_pairs) - 4} more' if len(faint_pairs) > 4 else '')
            say(f'LOOK scout: {len(faint_pairs)} pair(s) differ in the scout only by a faint, even shift, measurably but maybe not visibly ({shown}). They are kept: look at the '
                'scout sheet, and take out of the file any variation you cannot tell apart before sending, so card time is not spent on it.')
        checked = dict(checked, kept=kept, dropped=checked['dropped'] + scout_dropped)
        if not kept:
            say('FAIL before drawing: in the free scout every variation came out nearly the same as the saved scene. Change a setting that shows in these cameras, or spread wider, and scout again.')
            raise BatchRefused('nothing was drawn')
        if len(kept) < int(numbers.value('place_variations.batch_size_min')):
            say(f'LOOK before drawing: only {len(kept)} variation(s) would show. Spread the settings wider, or over the part of a dial that shows (`variations make ... --range KEY LOW HIGH`), and scout again.')
    jobs = spec_module.split_jobs(checked['kept'], getattr(options, 'jobs', None))
    asked_jobs = getattr(options, 'jobs', None)
    if asked_jobs and int(asked_jobs) > len(jobs):
        say(f'LOOK jobs: {asked_jobs} jobs were asked for but at most {len(jobs)} make sense here (at most {numbers.value("place_render.workers_max")} cards at once, and at least '
            f'{numbers.value("place_variations.min_variations_per_job")} variations for each so that a wake-up is shared)')
    card_seconds, elapsed_seconds, pictures = spec_module.estimate(jobs, len(spec['cameras']))
    counts = ', '.join(str(len([e for e in job['entries'] if not e.get('is_baseline')])) for job in jobs)
    where_baseline = next(job['index'] for job in jobs if any(e.get('is_baseline') for e in job['entries']))
    say(f'PASS plan: {len(checked["kept"])} variation(s) and the baseline in {len(jobs)} job(s) ({counts} variations; the baseline is drawn in job {where_baseline}), '
        f'{pictures} small picture(s) {spec["size"][0]} x {spec["size"][1]}' + (' (the film\'s tall shape: the place settings say "for_film": true)' if spec.get('for_film') else '')
        + f' through {max(1, len(spec["cameras"]))} camera(s); '
        + (f'drawn here it uses no card seconds (if it were sent to the cards: about {card_seconds:.0f} card seconds)' if drawn_here else
           f'about {card_seconds:.0f} card seconds in all and about {elapsed_seconds:.0f} s from sending to the last picture '
           f'(an estimate from the house numbers; the first real batch gives better ones)'))
    return {'spec': spec, 'checked': checked, 'jobs': jobs, 'big_batch_override': big_batch_override, 'estimate_card_seconds': card_seconds, 'estimate_elapsed_seconds': elapsed_seconds, 'pictures': pictures,
            'scout': (scout_document or {}).get('path'), 'saved_values': saved}


def _size_option(text):
    if not text:
        return None
    if isinstance(text, (list, tuple)):
        return [int(text[0]), int(text[1])]
    try:
        width, height = str(text).lower().split('x')
        return [int(width), int(height)]
    except ValueError:
        raise spec_module.SpecProblem(f'--size must look like 600x400, not {text}')


# ------------------------------------------------------------------ drawing: here
def local_command(blender, scene, job_file):
    from .. import cli
    command = [blender, '-b'] + cli.blender_thread_arguments() + ['--disable-autoexec', '--python-exit-code', '1', scene, '--python', os.path.join(numbers.PLACE_KIT, 'blender_run.py'), '--', 'variations-worker', '--job', job_file, '--where', 'local']
    if not os.environ.get('DISPLAY') and not os.environ.get('PLACE_NO_XVFB') and shutil.which('xvfb-run'):
        command = ['xvfb-run', '-a'] + command
    return command


def draw_here(plan, run_folder, blender, check_reset, say):
    """Runs the jobs on this computer, one after the other. Returns the job records."""
    spec = plan['spec']
    records = []
    environment = dict(os.environ, EXPLAINER_FILM_KIT=numbers.KIT)
    for job in plan['jobs']:
        out_folder = os.path.join(run_folder, 'pictures', f'job-{job["index"]}')
        os.makedirs(out_folder, exist_ok=True)
        job_file = os.path.join(run_folder, 'jobs', f'job-{job["index"]}.json')
        _write_json(job_file, job_file_content(job, spec, spec['scene'], spec['settings'], out_folder, spec['cameras'], check_reset))
        started = time.time()
        run = subprocess.run(local_command(blender, spec['scene'], job_file), capture_output=True, text=True, env=environment, timeout=numbers.value('place_render.job_minutes_max') * 60)
        wall = round(time.time() - started, 1)
        tail = '\n'.join((run.stdout + run.stderr).strip().splitlines()[-12:])
        records.append({'index': job['index'], 'folder': out_folder, 'where': 'this computer', 'runpod_status': 'COMPLETED' if run.returncode == 0 else 'FAILED', 'return_code': run.returncode,
                        'seconds': wall, 'wall_seconds': wall, 'wake_up_ms': 0, 'billed_work_ms': 0, 'job_id': None, 'log_tail': tail})
        say(f'{"PASS" if run.returncode == 0 else "FAIL"} job {job["index"]} (this computer): exit {run.returncode} in {wall} s')
        if run.returncode != 0:
            say('      ' + tail.replace('\n', '\n      '))
    return records


# ------------------------------------------------------------------ drawing: on rented cards
STATE_FILE = 'run-state.json'


def _log_small(backend, ledger, helper, role, what):
    """Writes the small jobs the backend ran since the last call (uploads, checks, downloads) into the ledger, then forgets them. Returns (seconds, measured)."""
    small = backend.small_jobs()
    entry = None
    if small:
        entry = card_time.log_small_jobs(ledger, helper, role, small, what)
    elif backend.wall_seconds():
        entry = card_time.log_wall_clock(ledger, helper, role, backend.wall_seconds(), what + ' (wall clock)')
    backend.clear_small()
    return (entry['card_seconds'], bool(entry.get('measured', True))) if entry else (0.0, True)


def send_jobs(plan, run_folder, backend, check_reset, helper, role, ledger, say, card_text=None):
    """Uploads once, then sends every job at the same time. The moment each job is sent a "sent" line goes into the ledger (it counts at the job's estimate until its billed seconds are in),
    and the run's state file (run-state.json in the run folder) is written, so `variations collect RUN-FOLDER` can finish the batch if this command is cut off. Returns the state.
    When an upload fails, the small jobs it already ran are still written into the ledger before the failure is passed on."""
    try:
        return _send_jobs(plan, run_folder, backend, check_reset, helper, role, ledger, say, card_text)
    except Exception:
        _log_small(backend, ledger, helper, role, f'set-up (uploads and checks, stopped by a failure) for the variations batch "{plan["spec"]["change"]}"')
        raise


def _send_jobs(plan, run_folder, backend, check_reset, helper, role, ledger, say, card_text=None):
    spec = plan['spec']
    store = backend.store_folder
    started = time.time()
    uploaded_note = []
    with tempfile.TemporaryDirectory() as work:
        bundle = client_module.kit_bundle_folder(os.path.join(work, 'kit-bundle'))
        remote_kit = f'{store}/place-kit-run/{client_module.folder_digest(bundle)}'
        marker = remote_kit + '/kit/place-kit/blender_run.py'
        if backend.have_file(marker):
            uploaded_note.append('kit already on the store')
        else:
            backend.upload(os.path.dirname(bundle), remote_kit)
            uploaded_note.append('kit uploaded')
    run_id = f'{spec["change_id"]}-{int(time.time())}'
    base = f'{store}/place-jobs/variations-{run_id}'                       # this batch's own jobs and pictures
    scene_home = f'{store}/place-jobs/scenes/{_sha8(spec["scene"])}'         # the scene waits here under its own checksum, so a second batch on the same scene does not upload it again
    extras = client_module.extra_uploads(spec['scene'], {})
    megabytes = (os.path.getsize(spec['scene']) + sum(client_module.size_of(path) for path, _ in extras)) / 1e6
    limit = numbers.value('place_render.upload_megabytes_max')
    if megabytes > limit:
        raise cards.CardProblem(f'the scene and its files come to {megabytes:.0f} MB, over {limit} MB: upload it once by hand and name it in the variations file')
    remote_scene = f'{scene_home}/{os.path.basename(spec["scene"])}'
    backend.upload(spec['scene'], remote_scene)                             # an upload of a file that is already there is only a check
    for path, name in extras:
        backend.upload(path, f'{scene_home}/{name}')
    remote_settings = None
    if spec['settings']:
        owners, owner_file = None, None
        try:
            owners = json.load(open(spec['settings'], encoding='utf-8')).get('owners')
        except (OSError, ValueError):
            owners = None
        if isinstance(owners, str) and not os.path.isabs(owners):
            owner_file = os.path.join(os.path.dirname(spec['settings']), owners)
            owner_file = owner_file if os.path.exists(owner_file) else None
        settings_home = f'{scene_home}/settings-{_sha8(spec["settings"])}' + (f'-{_sha8(owner_file)}' if owner_file else '')
        remote_settings = f'{settings_home}/{os.path.basename(spec["settings"])}'
        backend.upload(spec['settings'], remote_settings)
        if owner_file:
            backend.upload(owner_file, f'{settings_home}/{owners}')
    hook_paths = {}
    for variation in plan['checked']['kept']:
        script = variation.get('script')
        if script and script not in hook_paths:
            hook_paths[script] = f'{base}/hooks/{len(hook_paths) + 1}-{os.path.basename(script)}'
            backend.upload(script, hook_paths[script])
    submitted = []
    for job in plan['jobs']:
        out_remote = f'{base}/job-{job["index"]}'
        job_content = job_file_content(job, spec, remote_scene, remote_settings, out_remote, spec['cameras'], check_reset, hook_paths)
        job_local = os.path.join(run_folder, 'jobs', f'job-{job["index"]}.json')
        _write_json(job_local, job_content)
        remote_job = f'{base}/job-{job["index"]}.json'
        backend.upload(job_local, remote_job)
        tar_remote = f'{base}/job-{job["index"]}.tar'
        command = (f'{shlex.quote(backend.remote_blender)} -b --disable-autoexec --python-exit-code 1 {shlex.quote(remote_scene)} '
                   f'--python {shlex.quote(remote_kit + "/kit/place-kit/blender_run.py")} -- variations-worker --job {shlex.quote(remote_job)} --where on-card; '
                   f'code=$?; tar -cf {shlex.quote(tar_remote)} -C {shlex.quote(out_remote)} . ; exit $code')
        submitted.append((job, command, out_remote))
    set_up_seconds, set_up_measured = _log_small(backend, ledger, helper, role, f'set-up (uploads and checks) for the variations batch "{spec["change"]}"')
    set_up_done = time.time()
    state = {'about': 'The state of one variations batch sent to rented cards. `explainer-film-place variations collect THIS-FOLDER` finishes it if the command that sent it was cut off.',
             'spec': spec, 'checked': {'kept': plan['checked']['kept'], 'dropped': plan['checked']['dropped']}, 'jobs': plan['jobs'], 'estimate_card_seconds': plan['estimate_card_seconds'],
             'estimate_elapsed_seconds': plan['estimate_elapsed_seconds'], 'pictures': plan.get('pictures'), 'saved_values_before': plan.get('saved_values'), 'scout': plan.get('scout'),
             'base': base, 'helper': helper, 'role': role, 'ledger': ledger, 'card': {'kind': backend.kind, 'card_client': card_text, 'store_folder': store},
             'check_reset': bool(check_reset), 'uploaded_note': uploaded_note, 'sent': [], 'finished': False,
             'timing': {'started': started, 'set_up_done': set_up_done, 'small_seconds': set_up_seconds, 'small_measured': set_up_measured}}
    cameras = len(spec['cameras'])
    for job, command, out_remote in submitted:
        job_id = backend.submit(command, base, numbers.value('place_render.job_minutes_max') * 60)
        card_time.log_sent(ledger, helper, role, job_id, spec_module.estimate_job(job, cameras), f'variations job {job["index"]} of {len(plan["jobs"])} for "{spec["change"]}"')
        state['sent'].append({'index': job['index'], 'job_id': job_id, 'remote': out_remote})
        _write_json(os.path.join(run_folder, STATE_FILE), state)
    state['timing']['sent'] = time.time()
    _write_json(os.path.join(run_folder, STATE_FILE), state)
    say(f'PASS jobs sent: {len(state["sent"])} job(s) at the same time ({", ".join(uploaded_note)}; the scene and the job files are on the store). If this command is cut off, '
        f'`explainer-film-place variations collect {run_folder}` finishes the batch without sending anything again.')
    return state


def bring_back(state, run_folder, backend, say):
    """Waits for every sent job, writes its billed seconds into the ledger (once), and brings its pictures back in one bundle. Returns (job records, timing)."""
    spec, base, ledger, helper, role = state['spec'], state['base'], state['ledger'], state['helper'], state['role']
    timing = dict(state.get('timing') or {})
    records = []
    try:
        for sent in state['sent']:
            summary = backend.wait(sent['job_id'], numbers.value('place_render.job_minutes_max') * 60 + 120)
            records.append({'index': sent['index'], 'job_id': sent['job_id'], 'where': 'a rented card', 'remote': sent['remote'],
                            **{k: summary.get(k) for k in ('runpod_status', 'return_code', 'seconds', 'wake_up_ms', 'billed_work_ms', 'log_tail')}})
    finally:
        timing['jobs_done'] = time.time()
        for record in records:
            if record.get('runpod_status') in client_module.DONE:
                card_time.log_job(ledger, helper, role, {'id': record['job_id'], 'billed_work_ms': record['billed_work_ms'], 'wake_up_ms': record['wake_up_ms'], 'runpod_status': record['runpod_status']},
                                  f'variations job {record["index"]} of {len(state["sent"])} for "{spec["change"]}"')
    for record in records:
        finished = record['runpod_status'] == 'COMPLETED' and record['return_code'] == 0
        say(f'{"PASS" if finished else "FAIL"} job {record["index"]} (a rented card): {record["runpod_status"]}, exit {record["return_code"]}, '
            f'work {record["billed_work_ms"] / 1000.0 if record["billed_work_ms"] else 0:.1f} s billed, wake-up {record["wake_up_ms"] / 1000.0 if record["wake_up_ms"] else 0:.1f} s (the job\'s own clock: {record["seconds"]} s)')
        if not finished:
            say('      the end of its log: ' + str(record.get('log_tail') or '')[-700:].replace('\n', '\n      '))
        if record['runpod_status'] not in client_module.DONE:
            say(f'LOOK job {record["index"]} is still {record["runpod_status"]}: its billed seconds are not in the ledger yet (its "sent" line counts at the estimate). Run `variations collect {run_folder}` later.')
        folder = os.path.join(run_folder, 'pictures', f'job-{record["index"]}')
        os.makedirs(folder, exist_ok=True)
        record['folder'] = folder
        tar_local = os.path.join(run_folder, f'job-{record["index"]}.tar')
        try:
            backend.download(f'{base}/job-{record["index"]}.tar', tar_local)
            with tarfile.open(tar_local) as archive:
                archive.extractall(folder, filter='data') if sys.version_info >= (3, 12) else archive.extractall(folder)
            os.remove(tar_local)
        except (cards.CardProblem, client_module.RentFailed, tarfile.TarError, OSError) as problem:
            say(f'FAIL job {record["index"]}: the pictures did not come back ({problem})')
            record['download_failed'] = str(problem)
    seconds, measured = _log_small(backend, ledger, helper, role, f'downloads for the variations batch "{spec["change"]}"')
    timing['small_seconds'] = float(timing.get('small_seconds') or 0.0) + seconds
    timing['small_measured'] = bool(timing.get('small_measured', True) and measured)
    timing['downloaded'] = time.time()
    return records, timing


def draw_on_cards(plan, run_folder, backend, check_reset, helper, role, ledger, say, card_text=None):
    """Sends every job at the same time, waits, brings the pictures back, writes the seconds into the ledger. Returns (job records, timing dictionary)."""
    state = send_jobs(plan, run_folder, backend, check_reset, helper, role, ledger, say, card_text)
    return bring_back(state, run_folder, backend, say)


# ------------------------------------------------------------------ reading what the jobs wrote
def collect(plan, records, run_folder):
    """The result of every variation, from the files the workers wrote. A variation with no file is a failed one, said plainly."""
    by_job = {record['index']: record for record in records}
    results, summaries = [], {}
    for job in plan['jobs']:
        folder = os.path.join(run_folder, 'pictures', f'job-{job["index"]}')
        summary_path = os.path.join(folder, 'job-result.json')
        if os.path.exists(summary_path):
            summaries[job['index']] = json.load(open(summary_path, encoding='utf-8'))
        for position, entry in enumerate(job['entries'], 1):
            path = os.path.join(folder, keys.file_label(position, entry['name']) + '.json')
            if os.path.exists(path):
                result = json.load(open(path, encoding='utf-8'))
                for picture in result.get('pictures', []):
                    if picture.get('file'):
                        picture['path'] = os.path.join(folder, picture['file'])
                    if picture.get('path') and not os.path.exists(picture['path']):
                        picture['ok'] = False
            else:
                reason = by_job.get(job['index'], {}).get('download_failed') or 'no result came back from this job'
                result = {'name': entry['name'], 'is_baseline': bool(entry.get('is_baseline')), 'set': entry['set'], 'args': entry.get('args') or {}, 'script': entry.get('script'), 'ok': False,
                          'pictures': [], 'notes': [reason]}
            result['job'] = job['index']
            results.append(result)
    order = {entry['name']: i for i, entry in enumerate([spec_module.as_baseline()] + plan['checked']['kept'])}
    results.sort(key=lambda r: order.get(r['name'], 999))
    return results, summaries


def flag_results(results, pairs):
    """Adds plain 'flags' to each result from the pair check and from the worker's own notes. Returns the lines for the sheet and the report.
    Short on purpose: every variation that came out nearly the same as the baseline is named in ONE line (they are then nearly the same as each other too, which is not said again pair by pair);
    only a pair of variations that DO show against the baseline gets a line of its own. The full list of pairs stays in the result file."""
    number = {r['name']: i for i, r in enumerate(results)}
    by_name = {r['name']: r for r in results}
    lines = []
    for result in results:
        result['flags'] = []
        for note in result.get('notes', []):
            if note.startswith(('the layer ', 'no wear layer', 'state and look wrote')):
                result['flags'].append('changes nothing here: ' + note)
    pair_of = {frozenset((p['a'], p['b'])): p for p in pairs['pairs']}
    hidden = sorted(set(pairs.get('invisible', [])), key=lambda name: number[name])
    for name in hidden:
        by_name[name]['flags'].append('does not show in these cameras (nearly the same as the baseline)')
    if hidden:
        means = [pair_of[frozenset(('baseline', name))]['mean_difference'] for name in hidden if frozenset(('baseline', name)) in pair_of]
        spread = ('under the limit' if not means else f'{min(means):.2f}' if len(set(round(m, 2) for m in means)) == 1 else f'{min(means):.2f} to {max(means):.2f}')
        names = ', '.join(f'"{name}"' for name in hidden)
        unit = '' if not means else ' of 255'
        verb = 'came' if len(hidden) == 1 else 'all came'
        lines.append(f'{names} {verb} out nearly the same as the baseline (mean difference {spread}{unit}): the change does not show from these cameras, or it changes nothing in this scene'
                     + ('' if len(hidden) == 1 else ', and so they are nearly the same as each other too'))
    # the rest: variations that DO show against the baseline but came out nearly the same as each other. Groups of such variations (a pair, or several that are all alike) get ONE line each.
    close = [(a, b) for a, b in pairs['nearly_same'] if 'baseline' not in (a, b) and not (a in hidden and b in hidden)]
    parent = {}

    def find(name):
        parent.setdefault(name, name)
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    for a, b in close:
        parent[find(a)] = find(b)
    groups = {}
    for name in list(parent):
        groups.setdefault(find(name), []).append(name)
    for members in sorted((sorted(group, key=lambda n: number[n]) for group in groups.values()), key=lambda group: number[group[0]]):
        first_member = members[0]
        for later in members[1:]:
            by_name[later]['flags'].append(f'nearly the same as #{number[first_member]} {first_member}')
        gaps = [pair_of[frozenset((a, b))]['mean_difference'] for a, b in close if a in members and b in members]
        names = ' and '.join([', '.join(f'"{n}"' for n in members[:-1]), f'"{members[-1]}"']) if len(members) > 1 else f'"{members[0]}"'
        lines.append(f'{names} came out nearly the same as each other (mean difference {min(gaps):.2f}' + (f' to {max(gaps):.2f}' if len(gaps) > 1 and abs(max(gaps) - min(gaps)) >= 0.005 else '')
                     + ' of 255; they differ in their settings but not in these cameras): keep one of them')
    return lines


def faint_lines(results, pairs):
    """Plain lines for the pairs that are MEASURABLY but maybe not VISIBLY different (compare.pair_differences 'faint': only the mean moved; in every camera fewer than the
    changed-share limit of pixels moved by more than the pixel step). They are kept, not dropped; each gets a note. Adds a flag to each variation that differs from the baseline
    only faintly. Returns the lines (one for the baseline, one for the pairs of variations), or [] when there is none."""
    by_name = {r['name']: r for r in results}
    number = {r['name']: i for i, r in enumerate(results)}
    pair_of = {frozenset((p['a'], p['b'])): p for p in pairs.get('pairs', [])}
    share = pairs.get('changed_share_limit')
    step = pairs.get('pixel_step')
    how = (f'in every camera fewer than {share * 100:.1f} percent of the pixels changed by more than {step} levels' if share is not None and step is not None
           else 'almost no pixel changed by more than the pixel step')
    lines = []
    against_baseline = sorted(set(pairs.get('faint_against_baseline') or []), key=lambda name: number.get(name, 0))
    for name in against_baseline:
        if name in by_name:
            by_name[name].setdefault('flags', []).append('may not be visible (a faint, even shift from the baseline)')
    if against_baseline:
        means = [pair_of[frozenset(('baseline', name))]['mean_difference'] for name in against_baseline if frozenset(('baseline', name)) in pair_of]
        spread = f'{min(means):.2f}' if means and abs(max(means) - min(means)) < 0.005 else (f'{min(means):.2f} to {max(means):.2f}' if means else 'over the limit')
        names = ', '.join(f'"{name}"' for name in against_baseline)
        lines.append(f'{names} {"differs" if len(against_baseline) == 1 else "each differ"} from the baseline only by a faint, even shift (mean difference {spread} of 255, but {how}): '
                     'measurably, not always visibly, different. Look at the sheet; if you cannot see the change, it does not show from these cameras')
    # a pair of one variation nearly the same as the baseline and one that differs from it only faintly says nothing new (the baseline line says it already)
    hidden = set(pairs.get('invisible') or [])
    faint_from_baseline = set(against_baseline)
    others = [(a, b) for a, b in (pairs.get('faint') or []) if 'baseline' not in (a, b)
              and not ((a in hidden and b in faint_from_baseline) or (b in hidden and a in faint_from_baseline))]
    if others:
        others.sort(key=lambda pair: (number.get(pair[0], 0), number.get(pair[1], 0)))
        shown = others[:6]
        means = [pair_of[frozenset(pair)]['mean_difference'] for pair in others if frozenset(pair) in pair_of]
        spread = f'{min(means):.2f}' if means and abs(max(means) - min(means)) < 0.005 else (f'{min(means):.2f} to {max(means):.2f}' if means else 'over the limit')
        listed = '; '.join(f'"{a}" and "{b}"' for a, b in shown) + (f'; and {len(others) - len(shown)} more pair(s) (all in the result file)' if len(others) > len(shown) else '')
        lines.append(f'{listed} differ from each other only by a faint, even shift (mean difference {spread} of 255, but {how}): measurably, not always visibly, different. '
                     'If you cannot tell a pair apart on the sheet, keep one of the two')
    return lines


def _result_document(result, run_folder):
    document = {key: value for key, value in result.items() if key != 'pictures'}
    document['pictures'] = []
    for picture in result.get('pictures', []):
        row = {key: value for key, value in picture.items() if key != 'path'}
        row['path'] = os.path.relpath(picture['path'], run_folder) if picture.get('path') else None
        document['pictures'].append(row)
    return document


def card_lines_for(records, timing, ledger_entries, helper, where_local):
    if where_local:
        seconds = sum(r.get('wall_seconds') or 0 for r in records)
        return [f'Drawn on this computer in {seconds:.0f} s; no rented-card seconds were used.'], 0.0
    pieces, total = [], 0.0
    for record in records:
        parts = card_time.card_seconds_of(record.get('billed_work_ms'), record.get('wake_up_ms'))
        total += parts['card_seconds']
        pieces.append(f'job {record["index"]}: work {parts["work_seconds"]} + wake-up {parts["wake_up_seconds"]} + idle tail {parts["idle_tail_seconds"]:g} = {parts["card_seconds"]} s')
    small_seconds = float(timing.get('small_seconds') or 0.0)
    total += small_seconds
    lines = ['Card seconds (work + wake-up + the idle tail): ' + '; '.join(pieces) + (f'; set-up and downloads {small_seconds:.0f} s' + ('' if timing.get('small_measured', True) else ' (an estimate from the wall clock)') if small_seconds else '') + f'; in all {total:.0f} s, '
             + card_time.dollars_text(total) + '.']
    wake_text = ', '.join(f'{(r.get("wake_up_ms") or 0) / 1000.0:.1f} s' for r in records)
    if timing.get('collected_later'):
        lines.append(f'The {len(records)} job(s) were sent side by side and collected later (`variations collect`). Wake-up times (waiting for a card to start): {wake_text}.')
    elif timing.get('sent') and timing.get('jobs_done'):
        lines.append(f'The {len(records)} job(s) ran side by side: from sending to the last result took {timing["jobs_done"] - timing["sent"]:.0f} s. Wake-up times (waiting for a card to start): '
                     + wake_text + '.')
    return lines, total


# ------------------------------------------------------------------ the verb
def run_variations(options, say=print, backend=None, blender=None, environ=None):
    """`variations plan | run | sheet | scout | collect`. Returns the exit code."""
    action = getattr(options, 'action', None) or 'run'
    helper, role = card_time.who(options, environ)
    ledger = card_time.ledger_path(getattr(options, 'ledger', None), environ)
    try:
        entries, _ = card_time.read_ledger(ledger)
        if action == 'sheet':
            return rebuild_sheet(options, say)
        if action == 'scout':
            return scout_module.run_scout(options, say, blender)
        if action == 'collect':
            return collect_batch(options, say, backend, environ)
        where = (getattr(options, 'where', None) or 'auto')
        card_wanted = where in ('rented',) or (where == 'auto' and (backend is not None or getattr(options, 'card_client', None) or not client_module.read_settings(environ).missing()))
        plan = make_plan(options, say, entries, for_run=(action == 'run'), drawn_here=not card_wanted)
        spec = plan['spec']
        batch_check = card_time.check_batch(entries, helper, spec['change_id'], getattr(options, 'over_allowance', None))
        for line in batch_check['lines']:
            say(line)
        if card_wanted and not plan.get('scout') and not getattr(options, 'no_scout', False):
            say(f'LOOK no free scout of this file: `explainer-film-place variations scout {os.path.basename(spec["path"])}` draws the same batch HERE, tiny, for no card seconds, and says which '
                'variations would not show (on two real batches it called exactly the same pairs nearly the same as the cards did). Skip it only when this computer is too slow to open the scene.')
        if card_wanted:
            gate = card_time.check(entries, helper, role, plan['estimate_card_seconds'], getattr(options, 'over_allowance', None), f'this batch ({len(plan["jobs"])} job(s))')
            for line in gate['lines']:
                say(line)
            if gate.get('double_run') and action == 'run':
                card_time.log_double_run(ledger, helper, role, f'variations batch "{spec["change"]}"', gate['in_flight'])
            say(f'ledger: {ledger}')
        else:
            say('PASS card time: this batch is drawn on this computer, so no rented-card seconds are used. It still counts as one of the '
                f'{numbers.value("place_card_time.batches_per_change_max")} batches for this change (a look is a look); the free scout (`variations scout`) does not.')
            gate = {'status': 'ok', 'override': False}
        if action == 'plan':
            say('NEXT: to draw it, run the same command with `run`' + (' (it is refused as it stands)' if 'refuse' in (gate['status'], batch_check['status']) else '') + '.')
            return 1 if 'refuse' in (gate['status'], batch_check['status']) else 0
        if 'refuse' in (gate['status'], batch_check['status']):
            return 1
        if gate.get('override') or batch_check.get('override') or plan.get('big_batch_override'):
            card_time.log_override(ledger, helper, role, (getattr(options, 'over_allowance', None) or '').strip(), f'variations batch "{spec["change"]}"')
        run_folder = os.path.abspath(getattr(options, 'run_folder', None) or default_run_folder(spec))
        os.makedirs(run_folder, exist_ok=True)
        card_time.log_batch(ledger, helper, role, spec['change_id'], batch_check['number'], len(plan['checked']['kept']), len(plan['jobs']))
        check_reset = bool(getattr(options, 'check_reset', False))
        timing = {'batch_key': f'{spec["change_id"]}-{batch_check["number"]}'}
        began = time.time()
        if card_wanted:
            backend = backend or make_backend(options, environ)
            say(f'PASS card: {backend.kind}')
            card_text = getattr(options, 'card_client', None) or (environ or os.environ).get('PLACE_CARD_CLIENT')
            records, drawn_timing = draw_on_cards(plan, run_folder, backend, check_reset, helper, role, ledger, say, card_text)
            timing.update(drawn_timing)
        else:
            blender = blender or _find_blender(options)
            if not blender:
                say('FAIL Blender was not found: give --blender PATH, set BLENDER, or put blender on the PATH (a batch drawn here needs it; --where rented does not).')
                return 2
            records = draw_here(plan, run_folder, blender, check_reset, say)
        results, summaries = collect(plan, records, run_folder)
        return finish_batch(options, plan, records, results, summaries, run_folder, ledger, helper, role, timing, not card_wanted, began, say)
    except spec_module.SpecProblem as problem:
        say(f'FAIL {problem}')
        return 2
    except keys.KeyProblem as problem:
        say(f'FAIL {problem}')
        return 2
    except card_time.LedgerProblem as problem:
        say(f'FAIL {problem}')
        return 2
    except BatchRefused as problem:
        say(f'FAIL {problem}')
        return 1
    except client_module.RentProblem as problem:
        say(f'FAIL {client_module.scrubbed(problem, environ)}')
        return 2
    except (client_module.RentFailed, cards.CardProblem) as problem:
        say(f'FAIL {client_module.scrubbed(problem, environ)}')
        return 1


def collect_batch(options, say=print, backend=None, environ=None):
    """`variations collect RUN-FOLDER`: finishes a batch whose command was cut off after its jobs were sent (a time limit, a lost connection). Nothing is sent again: it waits for the jobs
    named in run-state.json, writes their billed seconds into the ledger (once), brings the pictures back, and makes the sheet and the result. Returns the exit code."""
    target = options.spec
    if not target:
        raise spec_module.SpecProblem('collect needs the run folder of the batch (it holds run-state.json): explainer-film-place variations collect RUN-FOLDER')
    path = target if target.endswith('.json') else os.path.join(target, STATE_FILE)
    if not os.path.exists(path):
        raise spec_module.SpecProblem(f'{path} is not there: give the run folder of a batch that was sent to rented cards (the folder the run printed)')
    state = json.load(open(path, encoding='utf-8'))
    run_folder = os.path.dirname(os.path.abspath(path))
    if state.get('finished'):
        say(f'PASS collect: this batch was already finished; its sheet and result are in {run_folder}. Nothing was asked of a card.')
        return 0
    if not state.get('sent'):
        say('FAIL collect: no job of this batch was sent, so there is nothing to collect. Run the batch again (`variations run`).')
        return 1
    card = state.get('card') or {}
    if backend is None:
        text = getattr(options, 'card_client', None) or card.get('card_client') or (environ or os.environ).get('PLACE_CARD_CLIENT')
        if text:
            backend = cards.CommandCard.from_text(text, store_folder=getattr(options, 'store_folder', None) or card.get('store_folder') or '/workspace')
        else:
            backend = make_backend(options, environ)
    say(f'PASS collect: {len(state["sent"])} job(s) of "{state["spec"]["change"]}" were sent earlier; waiting for them and bringing the pictures back (nothing is sent again).')
    plan = {'spec': state['spec'], 'checked': state['checked'], 'jobs': state['jobs'], 'estimate_card_seconds': state.get('estimate_card_seconds'),
            'estimate_elapsed_seconds': state.get('estimate_elapsed_seconds'), 'scout': state.get('scout'), 'saved_values': state.get('saved_values_before')}
    began = time.time()
    records, timing = bring_back(state, run_folder, backend, say)
    timing['collected_later'] = True
    results, summaries = collect(plan, records, run_folder)
    return finish_batch(options, plan, records, results, summaries, run_folder, state['ledger'], state['helper'], state['role'], timing, False, began, say)


def _find_blender(options):
    here = numbers.PLACE_KIT
    if here not in sys.path:
        sys.path.insert(0, here)
    import place_command
    return place_command.find_blender(getattr(options, 'blender', None), numbers.KIT)


def make_backend(options, environ=None):
    text = getattr(options, 'card_client', None) or (environ or os.environ).get('PLACE_CARD_CLIENT')
    if text:
        return cards.CommandCard.from_text(text, store_folder=getattr(options, 'store_folder', None) or '/workspace')
    settings = client_module.require_settings(environ)
    return cards.ClientCard(client_module.Client(client_module.WebTransport(settings)), settings)


def finish_batch(options, plan, records, results, summaries, run_folder, ledger, helper, role, timing, local, began, say):
    """Measures, compares, makes the sheet and the result file, and says what happened. Returns the exit code."""
    spec = plan['spec']
    drawn = [r for r in results if r.get('ok') and r.get('pictures')]
    if not drawn:
        say('FAIL pictures: no picture was drawn. Read the end of each job\'s log above.')
        _write_json(os.path.join(run_folder, 'variations-result.json'), {'change': spec['change'], 'ok': False, 'records': records})
        return 1
    compare.measure_variations(results)
    pairs = compare.pair_differences(results)
    pair_lines = flag_results(results, pairs)
    faint = faint_lines(results, pairs)
    failed = [r for r in results if not r.get('ok')]
    reset_note = None
    for job_index, summary in summaries.items():
        if summary.get('reset_check') and summary['reset_check'].get('ok'):
            base_picture = next((p for p in results[0].get('pictures', []) if p['camera'] == summary['reset_check']['camera']), None)
            drift = compare.reset_drift((base_picture or {}).get('path'), os.path.join(run_folder, 'pictures', f'job-{job_index}', summary['reset_check']['file']))
            reset_note = {'job': job_index, 'mean_difference_of_255': drift}
    entries, _ = card_time.read_ledger(ledger)
    card_lines, card_total = card_lines_for(records, timing, entries, helper, local)
    engine = next((s.get('engine') for s in summaries.values() if s.get('engine')), '?')
    cameras = spec['cameras'] or sorted({p['camera'] for r in results for p in r.get('pictures', [])})
    saved = {}
    for summary in summaries.values():
        saved.update({key: value for key, value in (summary.get('saved_values') or {}).items() if value is not None})
    baseline_note = scout_module.saved_values_text(saved)
    sheet_path = os.path.join(run_folder, f'{spec["change_id"]}-sheet.jpg')
    made = sheet.make_sheet(sheet_path, results, cameras, {'change': 'Variations: ' + spec['change'], 'scene': os.path.basename(spec['scene']), 'engine': engine.lower(),
                                                              'size': f'{spec["size"][0]} x {spec["size"][1]}', 'dropped': [f'Dropped before drawing: "{d["name"]}": {d["why"]}.' for d in plan['checked']['dropped']],
                                                              'pair_lines': ['Nearly the same: ' + line for line in pair_lines] + ['May not be visible: ' + line for line in faint],
                                                              'card_lines': card_lines, 'baseline_note': baseline_note})
    result_path = os.path.join(run_folder, 'variations-result.json')
    document = {'change': spec['change'], 'change_id': spec['change_id'], 'scene': spec['scene'], 'settings': spec['settings'], 'cameras': cameras, 'engine': engine, 'size': spec['size'],
                'variations': [{'name': v['name'], 'set': v['set'], 'args': v['args'], 'script': v['script']} for v in plan['checked']['kept']],
                'dropped': plan['checked']['dropped'], 'jobs': records, 'job_summaries': summaries,
                'results': [_result_document(r, run_folder) for r in results],
                'pairs': pairs['pairs'], 'nearly_the_same': pairs['nearly_same'], 'invisible': pairs['invisible'], 'faint': pairs.get('faint', []),
                'faint_against_baseline': pairs.get('faint_against_baseline', []), 'reset_check': reset_note, 'sheet': made,
                'card_seconds': card_total, 'card_lines': card_lines, 'estimate_card_seconds': plan['estimate_card_seconds'], 'estimate_elapsed_seconds': plan['estimate_elapsed_seconds'],
                'where': 'this computer' if local else 'a rented card', 'helper': helper, 'role': role, 'ledger': ledger, 'saved_values': saved, 'scout': plan.get('scout')}
    _write_json(result_path, document)
    state_path = os.path.join(run_folder, STATE_FILE)
    if not local and os.path.exists(state_path):
        try:
            state = json.load(open(state_path, encoding='utf-8'))
            state['finished'] = all(record.get('runpod_status') in client_module.DONE for record in records) and len(records) == len(state.get('sent') or [])
            _write_json(state_path, state)
        except (OSError, ValueError):
            pass
    say(f'{"PASS" if not failed else "LOOK"} pictures: {sum(len(r["pictures"]) for r in results)} drawn for {len(results) - 1} variation(s) and the baseline, {engine.lower()}, {spec["size"][0]} x {spec["size"][1]}' +
        (f'; {len(failed)} variation(s) failed: {", ".join(r["name"] for r in failed)}' if failed else ''))
    for r in failed:
        say(f'FAIL {r["name"]}: ' + ' '.join(r.get('notes') or ['it was not drawn']))
    for line in pair_lines:
        say(f'LOOK nearly the same: {line}')
    for line in faint:
        say(f'LOOK may not be visible: {line}')
    for r in results:
        for flag in r.get('flags', []):
            if flag.startswith('changes nothing here'):
                say(f'LOOK {r["name"]} {flag}')
    if reset_note is not None and reset_note['mean_difference_of_255'] is not None:
        say(f'{"PASS" if reset_note["mean_difference_of_255"] < 0.5 else "LOOK"} reset: the baseline drawn again after all the variations differs from the first by {reset_note["mean_difference_of_255"]:.3f} of 255 '
            '(0 = the scene was put back exactly)')
    say(f'PASS sheet: {made["path"]} ({made["bytes"] // 1024} KB, {made["width"]} x {made["height"]})' + (' LOOK it is over the size limit even at the smallest size' if made.get('over_limit') else ''))
    for line in card_lines:
        say(('PASS card seconds: ' if line.startswith('Card seconds') else 'PASS ') + line)
    say(f'PASS result: {result_path}')
    say('NEXT: look at the sheet with the Read tool; pick one variation, or combine two or three, and draw at most ONE more batch (`explainer-film-place variations refine ' + os.path.basename(result_path)
        + ' --pick NAME NAME`); then apply the pick in the real scene, and go on. Draw full-size pictures only once, at the very end.')
    if getattr(options, 'json', False):
        print(json.dumps(document, indent=1))
    return 1 if failed else 0


def rebuild_sheet(options, say):
    """`variations sheet RESULT-OR-FOLDER`: measures and makes the sheet again from the pictures already drawn (no drawing, no card)."""
    target = options.spec
    path = target if os.path.isfile(target) else os.path.join(target, 'variations-result.json')
    if not os.path.exists(path):
        raise spec_module.SpecProblem(f'{path} is not there: give the variations-result.json of a finished run (or its folder)')
    document = json.load(open(path, encoding='utf-8'))
    run_folder = os.path.dirname(os.path.abspath(path))
    results = document['results']
    for r in results:
        for p in r.get('pictures', []):
            p['path'] = os.path.join(run_folder, p['path']) if p.get('path') else None
    compare.measure_variations(results)
    is_scout = bool(document.get('scout') is True)
    pairs = compare.pair_differences(results, scout=is_scout)
    pair_lines = flag_results(results, pairs)
    faint = faint_lines(results, pairs)
    sheet_path = os.path.join(run_folder, f'{document["change_id"]}-scout-sheet.jpg' if is_scout else f'{document["change_id"]}-sheet.jpg')
    card_lines = document.get('card_lines') or ([f'Drawn on this computer in {document.get("seconds", 0):.0f} s; no rented-card seconds were used; a scout is not a batch.'] if is_scout else [])
    made = sheet.make_sheet(sheet_path, results, document['cameras'], {'change': ('Free scout (drawn here, tiny): ' if is_scout else 'Variations: ') + document['change'], 'scene': os.path.basename(document['scene']),
                                                                          'engine': str(document.get('engine', '')).lower(), 'size': f'{document["size"][0]} x {document["size"][1]}',
                                                                          'dropped': [f'Dropped before drawing: "{d["name"]}": {d["why"]}.' for d in document.get('dropped', [])],
                                                                          'pair_lines': [('Nearly the same in the scout: ' if is_scout else 'Nearly the same: ') + line for line in pair_lines]
                                                                          + ['May not be visible: ' + line for line in faint], 'card_lines': card_lines,
                                                                          'baseline_note': scout_module.saved_values_text(document.get('saved_values'))},
                            max_kilobytes=getattr(options, 'max_kilobytes', None))
    say(f'PASS sheet: {made["path"]} ({made["bytes"] // 1024} KB) made again from the pictures already drawn; no card seconds were used')
    return 0
