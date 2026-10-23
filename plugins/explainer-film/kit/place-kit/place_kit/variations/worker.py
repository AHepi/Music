"""What this does (inside Blender): ONE JOB of a variations batch. It runs on this computer or on a rented card, started like this:
    blender -b --disable-autoexec SCENE.blend --python blender_run.py -- variations-worker --job JOB.json --where local|on-card
The scene is opened once (by the command line). For each variation of the job, in order: apply it (apply.py), draw one small quick picture for each camera, then put everything back by
restoring the old values and checking a fingerprint (a variation with a script hook, or one whose restore did not come back exact, makes the worker REOPEN the scene instead). The scene is never
saved. The renderer is chosen ONCE from the baseline scene by the film owner's rule (Cycles where lamps, lit windows or water are in view, EEVEE when nothing is lit) and kept for every
picture, so the pictures of one batch can be compared; --engine in the job overrides it. Pictures are about 600 x 400 (place_variations.picture_size_pixels), low samples, JPEG.

The job file (written by the runner, place_kit/variations/runner.py):
    {"job": 1, "scene": ".../place.blend", "settings": ".../place-settings.json" or null, "out_folder": "...", "cameras": ["Camera A", ...] (empty: the scene's camera),
     "engine": "auto" | "cycles" | "eevee", "size": [600, 400], "samples": null or N, "check_reset": false,
     "entries": [{"name": "baseline", "is_baseline": true, "set": {}, "script": null, "args": {}, "reset": "auto"}, {"name": "moss-heavy", "set": {...}, ...}]}
It writes, into out_folder: NN_<name>__<camera>.jpg for each picture, NN_<name>.json for each variation (the settings, the notes, the seconds it took, how it was put back) and job-result.json
(the whole job: blender version, device, engine and why, seconds in all). Plain lines start with PASS, LOOK or FAIL. Exit: 0 every picture drawn, 1 a picture or a hook failed, 2 the job file or
a camera is missing.

A concrete example: a job of four variations and two cameras draws 8 pictures; with a warm card and EEVEE or low-sample Cycles each picture takes a few seconds.
"""
import json
import os
import time

import bpy

from .. import house_numbers as numbers
from ..render import render_job
from . import apply as apply_module, keys


class JobMissing(Exception):
    """The job file is not usable (exit 2)."""


def read_job(path):
    if not path or not os.path.exists(path):
        raise JobMissing(f'the job file {path} is not there')
    with open(path, encoding='utf-8') as handle:
        job = json.load(handle)
    for field in ('scene', 'out_folder', 'entries'):
        if not job.get(field):
            raise JobMissing(f'the job file {path} has no "{field}"')
    return job


def reopen(scene):
    bpy.ops.wm.open_mainfile(filepath=scene, load_ui=False)


def draw_camera(camera, base, engine, samples, size, quality, on_card, lines, label):
    """Draws the scene through one camera into base + .jpg. Returns the picture's log dictionary."""
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = int(quality)
    scene.render.use_file_extension = True
    scene.render.filepath = base
    started = time.time()
    try:
        bpy.ops.render.render(write_still=True)
    except Exception as problem:   # noqa: BLE001 - the log must say what failed
        lines.append(f'FAIL {label}: the picture could not be drawn ({problem})')
        return {'camera': camera.name, 'ok': False}
    seconds = round(time.time() - started, 2)
    picture = base + '.jpg'
    ok = os.path.exists(picture) and os.path.getsize(picture) > 0
    log = {'camera': camera.name, 'file': os.path.basename(picture), 'engine': engine, 'width': size[0], 'height': size[1], 'samples': samples, 'seconds': seconds,
           'bytes': os.path.getsize(picture) if ok else 0, 'ok': ok}
    if not ok:
        lines.append(f'FAIL {label}: Blender wrote no picture at {picture}')
        return log
    try:
        log['mean_luminance'] = render_job.mean_luminance(picture)
    except Exception:   # noqa: BLE001 - the black check is a courtesy
        log['mean_luminance'] = None
    dark = numbers.value('place_render.dark_picture_mean_luminance_min')
    if log['mean_luminance'] is not None and log['mean_luminance'] < dark:
        lines.append(f'FAIL {label}: the picture is nearly black (mean luminance {log["mean_luminance"]:.4f}): the scene has no light the camera sees')
        log['ok'] = False
    return log


def run_command(parsed):
    """The `variations-worker` verb. Returns the exit code."""
    from ..commands import InputMissing
    try:
        job = read_job(parsed.job)
    except (JobMissing, ValueError) as problem:
        raise InputMissing(str(problem))
    scene_path = job['scene']
    if not os.path.exists(scene_path):
        raise InputMissing(f'the scene {scene_path} named in the job is not there')
    if os.path.abspath(scene_path) != os.path.abspath(bpy.data.filepath or ''):
        reopen(scene_path)
    on_card = parsed.where == 'on-card'
    out_folder = os.path.abspath(job['out_folder'])
    os.makedirs(out_folder, exist_ok=True)
    started = time.time()
    lines, results = [], []
    cameras_wanted = job.get('cameras') or []
    if cameras_wanted:
        missing = [name for name in cameras_wanted if bpy.data.objects.get(name) is None or bpy.data.objects[name].type != 'CAMERA']
        if missing:
            have = ', '.join(sorted(o.name for o in bpy.data.objects if o.type == 'CAMERA')) or 'none'
            raise InputMissing(f'the scene has no camera named {", ".join(missing)} (its cameras: {have}). Nothing was drawn.')
    elif bpy.context.scene.camera is None:
        raise InputMissing('the scene has no camera and the job names none: set one, or give "cameras" in the variations file. Nothing was drawn.')

    def camera_objects():
        return [bpy.data.objects[name] for name in cameras_wanted] if cameras_wanted else [bpy.context.scene.camera]

    forced = job.get('engine') or 'auto'
    engine, reasons = render_job.choose_engine({}, forced)
    size = [int(job['size'][0]), int(job['size'][1])] if job.get('size') else list(numbers.value('place_variations.picture_size_pixels'))
    samples = int(job['samples']) if job.get('samples') else int(numbers.value('place_variations.cycles_samples' if engine == 'CYCLES' else 'place_variations.eevee_samples'))
    quality = job.get('quality') or numbers.value('place_variations.jpeg_quality')
    device, applied = render_job.set_up_engine(bpy.context.scene, engine, size[0], size[1], samples, on_card)
    applier = apply_module.Applier(job.get('settings'))
    baseline_fingerprint = applier.fingerprint()
    summary = {'job': job.get('job'), 'scene': os.path.basename(scene_path), 'blender': bpy.app.version_string, 'device': device, 'engine': engine, 'engine_reasons': reasons[:3], 'size': size,
               'samples': samples, 'where': 'card' if on_card else 'local', 'cameras': [c.name for c in camera_objects()], 'fingerprint_at_start': baseline_fingerprint}
    reopened = 0
    for position, entry in enumerate(job['entries'], 1):
        label = keys.file_label(position, entry['name'])
        result = {'name': entry['name'], 'is_baseline': bool(entry.get('is_baseline')), 'set': entry.get('set') or {}, 'args': entry.get('args') or {}, 'script': entry.get('script'),
                  'notes': [], 'pictures': [], 'ok': True, 'reset': None}
        began = time.time()
        try:
            result['notes'] = applier.apply(entry) if not entry.get('is_baseline') else []
        except (apply_module.HookProblem, Exception) as problem:   # noqa: BLE001 - a variation that cannot be applied is a failed variation; the batch goes on
            result['ok'] = False
            result['notes'].append(str(problem))
            lines.append(f'FAIL {entry["name"]}: {problem}')
        result['seconds_apply'] = round(time.time() - began, 2)
        drawn_started = time.time()
        if result['ok']:
            for camera in camera_objects():
                base = os.path.join(out_folder, f'{label}__{keys.file_word(camera.name)}')
                picture = draw_camera(camera, base, engine, samples, size, quality, on_card, lines, f'{entry["name"]} / {camera.name}')
                result['pictures'].append(picture)
                if not picture.get('ok'):
                    result['ok'] = False
        result['seconds_draw'] = round(time.time() - drawn_started, 2)
        reset_started = time.time()
        last = position == len(job['entries']) and not job.get('check_reset')       # after the last one nothing needs putting back, unless the reset is to be checked
        if not last:
            needs_reopen = entry.get('reset') == 'reopen' or bool(entry.get('script'))
            if not needs_reopen:
                applier.restore()
                if applier.fingerprint() == baseline_fingerprint:
                    result['reset'] = 'restored exactly'
                else:
                    needs_reopen = True
                    result['notes'].append('putting the old values back did not give exactly the saved scene, so the scene was reopened')
            if needs_reopen:
                reopen(scene_path)
                reopened += 1
                applier = apply_module.Applier(job.get('settings'))
                render_job.set_up_engine(bpy.context.scene, engine, size[0], size[1], samples, on_card)
                result['reset'] = result['reset'] or 'reopened'
                if applier.fingerprint() != baseline_fingerprint:
                    result['notes'].append('the reopened scene has another fingerprint than the first time: something in the file changes when it is opened')
        result['seconds_reset'] = round(time.time() - reset_started, 2)
        with open(os.path.join(out_folder, f'{label}.json'), 'w', encoding='utf-8') as handle:
            json.dump(result, handle, indent=1)
        results.append(result)
        for note in result['notes']:
            if result['ok']:
                lines.append(f'LOOK {entry["name"]}: {note}')
        total = sum(p.get('seconds', 0) for p in result['pictures'])
        if result['ok']:
            lines.append(f'PASS {entry["name"]}: {len(result["pictures"])} picture(s) in {total:.1f} s ({result["reset"] or "last of the job"})')
    if job.get('check_reset'):
        first_camera = camera_objects()[0]
        applier.restore()
        base = os.path.join(out_folder, 'reset-check__' + keys.file_word(first_camera.name))
        check = draw_camera(first_camera, base, engine, samples, size, quality, on_card, lines, f'reset check / {first_camera.name}')
        summary['reset_check'] = check
    summary.update({'seconds_in_all': round(time.time() - started, 1), 'reopened': reopened, 'entries': [r['name'] for r in results], 'ok': all(r['ok'] for r in results),
                    'fingerprint_at_end': applier.fingerprint()})
    with open(os.path.join(out_folder, 'job-result.json'), 'w', encoding='utf-8') as handle:
        json.dump(summary, handle, indent=1)
    for line in lines:
        print(line)
    drawn = sum(len(r['pictures']) for r in results)
    print(f'{"PASS" if summary["ok"] else "FAIL"} variations-worker: job {job.get("job")}: {sum(1 for r in results if r["ok"])} of {len(results)} variation(s), {drawn} picture(s), {summary["seconds_in_all"]} s, '
          f'{engine.lower()} on {device}')
    return 0 if summary['ok'] else 1
