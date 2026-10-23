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
from . import cards, compare, keys, sheet, spec as spec_module


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
            'quality': numbers.value('place_variations.jpeg_quality'), 'check_reset': bool(check_reset and any(e.get('is_baseline') for e in job['entries'])), 'entries': entries}


# ------------------------------------------------------------------ the plan
def make_plan(options, say=print, ledger_entries=None, for_run=False):
    """Reads and checks everything that costs nothing. Returns the plan dictionary; raises spec.SpecProblem (exit 2) or BatchRefused (exit 1)."""
    spec = spec_module.read_spec(options.spec, scene=getattr(options, 'scene', None), settings=getattr(options, 'settings', None), cameras=getattr(options, 'cameras', None),
                                 engine=getattr(options, 'engine', None) if getattr(options, 'engine', None) not in (None, 'auto') else None,
                                 size=_size_option(getattr(options, 'size', None)), samples=getattr(options, 'samples', None))
    checked = spec_module.check_before(spec)
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
    jobs = spec_module.split_jobs(checked['kept'], getattr(options, 'jobs', None))
    asked_jobs = getattr(options, 'jobs', None)
    if asked_jobs and int(asked_jobs) > len(jobs):
        say(f'LOOK jobs: {asked_jobs} jobs were asked for but at most {len(jobs)} make sense here (at most {numbers.value("place_render.workers_max")} cards at once, and at least '
            f'{numbers.value("place_variations.min_variations_per_job")} variations for each so that a wake-up is shared)')
    card_seconds, elapsed_seconds, pictures = spec_module.estimate(jobs, len(spec['cameras']))
    counts = ', '.join(str(len([e for e in job['entries'] if not e.get('is_baseline')])) for job in jobs)
    where_baseline = next(job['index'] for job in jobs if any(e.get('is_baseline') for e in job['entries']))
    say(f'PASS plan: {len(checked["kept"])} variation(s) and the baseline in {len(jobs)} job(s) ({counts} variations; the baseline is drawn in job {where_baseline}), '
        f'{pictures} small picture(s) {spec["size"][0]} x {spec["size"][1]} through {max(1, len(spec["cameras"]))} camera(s); about {card_seconds:.0f} card seconds in all and about {elapsed_seconds:.0f} s from sending to the last picture '
        f'(an estimate from the house numbers; the first real batch gives better ones)')
    return {'spec': spec, 'checked': checked, 'jobs': jobs, 'big_batch_override': big_batch_override, 'estimate_card_seconds': card_seconds, 'estimate_elapsed_seconds': elapsed_seconds, 'pictures': pictures}


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
    command = [blender, '-b', '--disable-autoexec', '--python-exit-code', '1', scene, '--python', os.path.join(numbers.PLACE_KIT, 'blender_run.py'), '--', 'variations-worker', '--job', job_file, '--where', 'local']
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
def draw_on_cards(plan, run_folder, backend, check_reset, helper, role, ledger, say):
    """Uploads once, sends every job at the same time, waits, brings the pictures back, writes the seconds into the ledger. Returns (job records, timing dictionary)."""
    spec = plan['spec']
    store = backend.store_folder
    timing = {'started': time.time()}
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
    base = f'{store}/place-jobs/variations-{run_id}'
    extras = client_module.extra_uploads(spec['scene'], {})
    megabytes = (os.path.getsize(spec['scene']) + sum(client_module.size_of(path) for path, _ in extras)) / 1e6
    limit = numbers.value('place_render.upload_megabytes_max')
    if megabytes > limit:
        raise cards.CardProblem(f'the scene and its files come to {megabytes:.0f} MB, over {limit} MB: upload it once by hand and name it in the variations file')
    remote_scene = f'{base}/{os.path.basename(spec["scene"])}'
    backend.upload(spec['scene'], remote_scene)
    for path, name in extras:
        backend.upload(path, f'{base}/{name}')
    remote_settings = None
    if spec['settings']:
        remote_settings = f'{base}/settings/{os.path.basename(spec["settings"])}'
        backend.upload(spec['settings'], remote_settings)
        try:
            owners = json.load(open(spec['settings'], encoding='utf-8')).get('owners')
        except (OSError, ValueError):
            owners = None
        if isinstance(owners, str) and not os.path.isabs(owners):
            owner_file = os.path.join(os.path.dirname(spec['settings']), owners)
            if os.path.exists(owner_file):
                backend.upload(owner_file, f'{base}/settings/{owners}')
    hook_paths = {}
    for variation in spec['variations']:
        script = variation.get('script')
        if script and script not in hook_paths:
            hook_paths[script] = f'{base}/hooks/{len(hook_paths) + 1}-{os.path.basename(script)}'
            backend.upload(script, hook_paths[script])
    records, submitted = [], []
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
    timing['set_up_done'] = time.time()
    job_ids = []
    for job, command, out_remote in submitted:
        job_ids.append(backend.submit(command, base, numbers.value('place_render.job_minutes_max') * 60))
    timing['sent'] = time.time()
    say(f'PASS jobs sent: {len(job_ids)} job(s) at the same time ({", ".join(uploaded_note)}; the scene and the job files are on the store)')
    try:
        for (job, command, out_remote), job_id in zip(submitted, job_ids):
            summary = backend.wait(job_id, numbers.value('place_render.job_minutes_max') * 60 + 120)
            records.append({'index': job['index'], 'job_id': job_id, 'where': 'a rented card', 'remote': out_remote, **{k: summary.get(k) for k in ('runpod_status', 'return_code', 'seconds', 'wake_up_ms', 'billed_work_ms', 'log_tail')}})
    finally:
        timing['jobs_done'] = time.time()
        small = backend.small_jobs()
        small_entry = None
        if small:
            small_entry = card_time.log_small_jobs(ledger, helper, role, small, f'set-up and download for the variations batch "{spec["change"]}"')
        elif backend.wall_seconds():
            small_entry = card_time.log_wall_clock(ledger, helper, role, backend.wall_seconds(), f'uploads and downloads of the variations batch "{spec["change"]}" (wall clock)')
        timing['small_seconds'] = small_entry['card_seconds'] if small_entry else 0.0
        timing['small_measured'] = bool(small_entry and small_entry.get('measured', True))
        for record in records:
            card_time.log_job(ledger, helper, role, {'id': record['job_id'], 'billed_work_ms': record['billed_work_ms'], 'wake_up_ms': record['wake_up_ms'], 'runpod_status': record['runpod_status']},
                              f'variations job {record["index"]} of {len(plan["jobs"])} for "{spec["change"]}"')
    for record in records:
        say(f'{"PASS" if record["runpod_status"] == "COMPLETED" and record["return_code"] == 0 else "FAIL"} job {record["index"]} (a rented card): {record["runpod_status"]}, exit {record["return_code"]}, '
            f'work {record["billed_work_ms"] / 1000.0 if record["billed_work_ms"] else 0:.1f} s billed, wake-up {record["wake_up_ms"] / 1000.0 if record["wake_up_ms"] else 0:.1f} s (the job\'s own clock: {record["seconds"]} s)')
        if record['runpod_status'] != 'COMPLETED' or record['return_code'] != 0:
            say('      the end of its log: ' + str(record.get('log_tail') or '')[-700:].replace('\n', '\n      '))
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
    timing['downloaded'] = time.time()
    return records, timing


# ------------------------------------------------------------------ reading what the jobs wrote
def collect(plan, records, run_folder):
    """The result of every variation, from the files the workers wrote. A variation with no file is a failed one, said plainly."""
    spec = plan['spec']
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
    """Adds plain 'flags' to each result from the pair check and from the worker's own notes. Returns lines for the sheet and the report."""
    number = {r['name']: i for i, r in enumerate(results)}
    lines = []
    for result in results:
        result['flags'] = []
        for note in result.get('notes', []):
            if note.startswith(('the layer ', 'no wear layer', 'state and look wrote')):
                result['flags'].append('changes nothing here: ' + note)
    for first, second in pairs['nearly_same']:
        a, b = (first, second) if number[first] < number[second] else (second, first)
        if a == 'baseline':
            target = next(r for r in results if r['name'] == b)
            target['flags'].append('does not show in these cameras (nearly the same as the baseline)')
            lines.append(f'"{b}" came out nearly the same as the baseline (mean difference '
                         f'{next(p for p in pairs["pairs"] if {p["a"], p["b"]} == {a, b})["mean_difference"]:.2f} of 255): the change does not show from these cameras, or it changes nothing in this scene')
        else:
            later = next(r for r in results if r['name'] == b)
            later['flags'].append(f'nearly the same as #{number[a]} {a}')
            pair = next(p for p in pairs['pairs'] if {p['a'], p['b']} == {a, b})
            lines.append(f'"{b}" and "{a}" came out nearly the same (mean difference {pair["mean_difference"]:.2f} of 255, {pair["changed_share"]:.2%} of pixels changed): keep one')
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
    if timing.get('sent') and timing.get('jobs_done'):
        lines.append(f'The {len(records)} job(s) ran side by side: from sending to the last result took {timing["jobs_done"] - timing["sent"]:.0f} s. Wake-up times (waiting for a card to start): '
                     + ', '.join(f'{(r.get("wake_up_ms") or 0) / 1000.0:.1f} s' for r in records) + '.')
    return lines, total


# ------------------------------------------------------------------ the verb
def run_variations(options, say=print, backend=None, blender=None, environ=None):
    """`variations plan | run | sheet`. Returns the exit code."""
    action = getattr(options, 'action', None) or 'run'
    helper, role = card_time.who(options, environ)
    ledger = card_time.ledger_path(getattr(options, 'ledger', None), environ)
    try:
        entries, _ = card_time.read_ledger(ledger)
        if action == 'sheet':
            return rebuild_sheet(options, say)
        plan = make_plan(options, say, entries, for_run=(action == 'run'))
        spec = plan['spec']
        where = (getattr(options, 'where', None) or 'auto')
        card_wanted = where in ('rented',) or (where == 'auto' and (backend is not None or getattr(options, 'card_client', None) or not client_module.read_settings(environ).missing()))
        batch_check = card_time.check_batch(entries, helper, spec['change_id'], getattr(options, 'over_allowance', None))
        for line in batch_check['lines']:
            say(line)
        if card_wanted:
            gate = card_time.check(entries, helper, role, plan['estimate_card_seconds'], getattr(options, 'over_allowance', None), f'this batch ({len(plan["jobs"])} job(s))')
            for line in gate['lines']:
                say(line)
            say(f'ledger: {ledger}')
        else:
            say('PASS card time: this batch is drawn on this computer, so no rented-card seconds are used.')
            gate = {'status': 'ok', 'override': False}
        if action == 'plan':
            say(f'NEXT: to draw it, run the same command with `run`' + (' (it is refused as it stands)' if 'refuse' in (gate['status'], batch_check['status']) else '') + '.')
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
            records, drawn_timing = draw_on_cards(plan, run_folder, backend, check_reset, helper, role, ledger, say)
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
    sheet_path = os.path.join(run_folder, f'{spec["change_id"]}-sheet.jpg')
    made = sheet.make_sheet(sheet_path, results, cameras, {'change': 'Variations: ' + spec['change'], 'scene': os.path.basename(spec['scene']), 'engine': engine.lower(),
                                                              'size': f'{spec["size"][0]} x {spec["size"][1]}', 'dropped': [f'Dropped before drawing: "{d["name"]}": {d["why"]}.' for d in plan['checked']['dropped']],
                                                              'pair_lines': ['Nearly the same: ' + line for line in pair_lines], 'card_lines': card_lines})
    result_path = os.path.join(run_folder, 'variations-result.json')
    document = {'change': spec['change'], 'change_id': spec['change_id'], 'scene': spec['scene'], 'settings': spec['settings'], 'cameras': cameras, 'engine': engine, 'size': spec['size'],
                'variations': [{'name': v['name'], 'set': v['set'], 'args': v['args'], 'script': v['script']} for v in plan['checked']['kept']],
                'dropped': plan['checked']['dropped'], 'jobs': records, 'job_summaries': summaries,
                'results': [_result_document(r, run_folder) for r in results],
                'pairs': pairs['pairs'], 'nearly_the_same': pairs['nearly_same'], 'invisible': pairs['invisible'], 'reset_check': reset_note, 'sheet': made,
                'card_seconds': card_total, 'card_lines': card_lines, 'estimate_card_seconds': plan['estimate_card_seconds'], 'estimate_elapsed_seconds': plan['estimate_elapsed_seconds'],
                'where': 'this computer' if local else 'a rented card', 'helper': helper, 'role': role, 'ledger': ledger}
    _write_json(result_path, document)
    say(f'{"PASS" if not failed else "LOOK"} pictures: {sum(len(r["pictures"]) for r in results)} drawn for {len(results) - 1} variation(s) and the baseline, {engine.lower()}, {spec["size"][0]} x {spec["size"][1]}' +
        (f'; {len(failed)} variation(s) failed: {", ".join(r["name"] for r in failed)}' if failed else ''))
    for r in failed:
        say(f'FAIL {r["name"]}: ' + ' '.join(r.get('notes') or ['it was not drawn']))
    for line in pair_lines:
        say(f'LOOK nearly the same: {line}')
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
    pairs = compare.pair_differences(results)
    pair_lines = flag_results(results, pairs)
    sheet_path = os.path.join(run_folder, f'{document["change_id"]}-sheet.jpg')
    made = sheet.make_sheet(sheet_path, results, document['cameras'], {'change': 'Variations: ' + document['change'], 'scene': os.path.basename(document['scene']), 'engine': str(document.get('engine', '')).lower(),
                                                                          'size': f'{document["size"][0]} x {document["size"][1]}', 'dropped': [f'Dropped before drawing: "{d["name"]}": {d["why"]}.' for d in document.get('dropped', [])],
                                                                          'pair_lines': ['Nearly the same: ' + line for line in pair_lines], 'card_lines': document.get('card_lines', [])},
                            max_kilobytes=getattr(options, 'max_kilobytes', None))
    say(f'PASS sheet: {made["path"]} ({made["bytes"] // 1024} KB) made again from the pictures already drawn; no card seconds were used')
    return 0
