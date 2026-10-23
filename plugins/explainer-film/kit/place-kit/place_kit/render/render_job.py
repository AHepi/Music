"""What this does: draws the pictures of a RENDER JOB with the renderer rule (Cycles where lamps, glowing things or fires are lit, EEVEE when they are off),
at the sizes and sample counts in the house numbers (place_render.*), one JSON log per picture. It runs inside Blender (the launcher starts it); on a
rented card the same file runs there, started by the rented-card client.

A render job is a small JSON file:
    {"out_folder": "pictures/round1",                         where the pictures and their logs go (made when missing)
     "views": [{"name": "lane_a", "camera": "Camera A",       the camera object (when missing: the scene's own camera)
                "kind": "final",                              the size of the picture drawn with --finals: final (default) or close_up (house numbers)
                "width": 1200, "height": 800, "samples": 96,  optional: your own numbers
                "engine": "cycles"}],                         optional: force one view's renderer (the rule decides when missing)
     "format": "JPEG"}                                        optional: JPEG (default for previews) or PNG (default for finals)
A view may also say "kinds": ["final"] (or ["close_up"], or ["preview", "final"]): exactly the pictures to draw for it, at the sizes you gave. That is the way to get ONE picture at one size
on this computer without drawing a preview as well (without "kinds", a view is drawn as a preview, and with --finals as a preview and a final).
"scene" may also be in the job; otherwise the scene that is open is drawn.
By default every view is drawn once at PREVIEW size (small JPG, quick). With --finals each view is drawn again at its final size (PNG).
A local picture is kept tiny (this computer is slow: place_render.local_cycles_* and local_eevee_* numbers) unless --finals is given;
on a rented card (--where on-card, set by the client) the real sizes are used and the card is chosen: OptiX, then CUDA, then HIP, then the processor.
A concrete example: a scene with one point lamp draws with Cycles at 1200 x 800, 96 samples on a card; locally it draws at 320 x 240 with 16 samples (EEVEE: 480 x 320, 8 samples). Every picture
gets lane_a_preview.json saying the engine, the reasons, the device, the size, the samples, the seconds, and whether the picture came out nearly black.
Plain lines start with PASS, LOOK or FAIL. Exit: 0 every picture drawn, 1 a picture failed, 2 the job file is missing or unusable.
"""
import hashlib
import json
import os
import time

import bpy

from .. import house_numbers as numbers
from . import renderer_choice

CYCLES_DEVICES = ('OPTIX', 'CUDA', 'HIP', 'ONEAPI', 'METAL')


class JobProblem(Exception):
    """The job file or the scene cannot be used (the launcher turns this into exit 2)."""


def read_job(path):
    if not path:
        raise JobProblem('give the job file: explainer-film-place render --job JOB.json (see the note at the top of place_kit/render/render_job.py for its shape)')
    if not os.path.exists(path):
        raise JobProblem(f'the job file {path} is not there')
    try:
        with open(path, encoding='utf-8') as handle:
            job = json.load(handle)
    except ValueError as problem:
        raise JobProblem(f'the job file {path} is not valid JSON ({problem})')
    if not isinstance(job, dict) or not isinstance(job.get('views'), list) or not job['views']:
        raise JobProblem(f'the job file {path} needs a "views" list with at least one view: {{"views": [{{"name": "a", "camera": "Camera"}}]}}')
    if not job.get('out_folder'):
        raise JobProblem(f'the job file {path} needs an "out_folder" (where the pictures go)')
    names = [view.get('name') for view in job['views']]
    if any(not isinstance(name, str) or not name for name in names) or len(set(names)) != len(names):
        raise JobProblem(f'every view in {path} needs its own non-empty "name" (the picture file is named after it)')
    return job


def sizes_for(view, kind, on_card, engine, finals):
    """(width, height, samples) for one view at one kind (preview, close_up, final)."""
    key = {'preview': 'place_render.preview_size_pixels', 'close_up': 'place_render.close_up_size_pixels', 'final': 'place_render.final_size_pixels'}[kind]
    width, height = numbers.value(key)
    if engine == 'CYCLES':
        samples = numbers.value('place_render.final_samples' if kind == 'final' else 'place_render.preview_samples')
    else:
        samples = numbers.value('place_render.eevee_samples')
    if view.get('width') and view.get('height'):
        width, height = int(view['width']), int(view['height'])
    if view.get('samples'):
        samples = int(view['samples'])
    capped = False
    if not on_card and not finals:
        engine_key = 'cycles' if engine == 'CYCLES' else 'eevee'
        local_width, local_height = numbers.value(f'place_render.local_{engine_key}_preview_size_pixels')
        local_samples = numbers.value(f'place_render.local_{engine_key}_samples')
        scale = min(1.0, local_width / width, local_height / height)
        if scale < 1.0 or samples > local_samples:
            capped = True
        width, height = max(16, int(width * scale)), max(16, int(height * scale))
        samples = min(samples, local_samples)
    return width, height, samples, capped


def choose_engine(view, forced):
    """(engine, reasons): a forced engine (--engine or the view's own), else the renderer rule."""
    wanted = (forced if forced and forced != 'auto' else view.get('engine') or '').lower()
    decision = renderer_choice.renderer_for_scene()
    if wanted in ('cycles', 'eevee'):
        return wanted.upper(), [f'forced to {wanted} (the rule says {decision["engine"].lower()}: ' + ('; '.join(decision['reasons'][:2]) or 'nothing is lit') + ')']
    return decision['engine'], decision['reasons'] or ['no lamp but the sun, nothing glows: daylight only']


def pick_cycles_device(scene, on_card):
    """Sets Cycles to a graphics card when this machine has one (on a rented card, always tried), else the processor. Returns a plain name for the log."""
    scene.cycles.device = 'CPU'
    if not on_card:
        return 'CPU (this computer)'
    try:
        preferences = bpy.context.preferences.addons['cycles'].preferences
        for kind in CYCLES_DEVICES:
            try:
                preferences.compute_device_type = kind
                preferences.get_devices()
            except (TypeError, ValueError):
                continue
            chosen = [device for device in preferences.devices if device.type == kind]
            if chosen:
                for device in preferences.devices:
                    device.use = device.type == kind
                scene.cycles.device = 'GPU'
                return f'{kind} ({chosen[0].name})'
    except Exception as problem:   # noqa: BLE001 - a missing driver must not stop the picture; it falls back to the processor
        return f'CPU (no card found: {problem})'
    return 'CPU (no card found)'


def set_up_engine(scene, engine, width, height, samples, on_card):
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = width, height, 100
    if engine == 'CYCLES':
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        return pick_cycles_device(scene, on_card), {}
    scene.render.engine = 'BLENDER_EEVEE'
    applied = {}
    for name, key in (('taa_render_samples', None), ('shadow_ray_count', 'place_render.eevee_shadow_rays'), ('shadow_step_count', 'place_render.eevee_shadow_steps')):
        value = samples if key is None else numbers.value(key)
        if hasattr(scene.eevee, name):
            setattr(scene.eevee, name, int(value))
            applied[name] = int(value)
    return 'EEVEE', applied


def picture_format(view, kind, job):
    chosen = (view.get('format') or job.get('format') or ('PNG' if kind == 'final' else 'JPEG')).upper()
    return ('PNG', '.png') if chosen == 'PNG' else ('JPEG', '.jpg')


def mean_luminance(path):
    """The mean luminance 0..1 of a drawn picture (read back from the file; a big picture is sampled sparsely)."""
    import numpy as np
    image = bpy.data.images.load(path, check_existing=False)
    try:
        width, height = image.size
        pixels = np.empty(width * height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        rgb = pixels.reshape(-1, 4)[:, :3]
        step = max(1, len(rgb) // 400000)
        rgb = rgb[::step]
        return float((0.2126 * rgb[:, 0] + 0.7152 * rgb[:, 1] + 0.0722 * rgb[:, 2]).mean())
    finally:
        bpy.data.images.remove(image)


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def draw_one(job, view, kind, forced_engine, finals, on_card, out_folder, lines):
    """Draws one view at one kind. Returns the log dictionary (with 'ok')."""
    scene = bpy.context.scene
    name = view['name']
    camera = bpy.data.objects.get(view['camera']) if view.get('camera') else scene.camera
    kind_word = kind.replace('_', '')
    label = name if name.lower().endswith(kind_word) else f'{name}_{kind_word}'          # a view called "closeup" is not drawn as closeup_closeup
    if camera is None or camera.type != 'CAMERA':
        lines.append(f'FAIL {label}: ' + (f'there is no camera object named "{view["camera"]}"' if view.get('camera') else 'the scene has no camera (give "camera" in the view, or set one)'))
        return {'view': name, 'kind': kind, 'ok': False}
    scene.camera = camera
    engine, reasons = choose_engine(view, forced_engine)
    width, height, samples, capped = sizes_for(view, kind, on_card, engine, finals)
    device, applied = set_up_engine(scene, engine, width, height, samples, on_card)
    file_format, extension = picture_format(view, kind, job)
    scene.render.image_settings.file_format = file_format
    if file_format == 'JPEG':
        scene.render.image_settings.quality = 90
    scene.render.use_file_extension = True
    base = os.path.join(out_folder, label)
    scene.render.filepath = base
    started = time.time()
    try:
        bpy.ops.render.render(write_still=True)
    except Exception as problem:   # noqa: BLE001 - the log must say what failed
        lines.append(f'FAIL {label}: the picture could not be drawn ({problem})')
        return {'view': name, 'kind': kind, 'ok': False}
    seconds = round(time.time() - started, 2)
    picture = base + extension
    ok = os.path.exists(picture) and os.path.getsize(picture) > 0
    log = {'view': name, 'kind': kind, 'camera': camera.name, 'engine': engine, 'reasons': reasons, 'device': device, 'eevee_settings': applied,
           'width': width, 'height': height, 'samples': samples, 'kept_tiny_for_this_computer': capped, 'seconds': seconds, 'picture': os.path.basename(picture),
           'picture_bytes': os.path.getsize(picture) if ok else 0, 'scene': os.path.basename(bpy.data.filepath) if bpy.data.filepath else None,
           'scene_sha256': file_sha256(bpy.data.filepath) if bpy.data.filepath and os.path.exists(bpy.data.filepath) else None, 'where': 'card' if on_card else 'local', 'ok': ok}
    if not ok:
        lines.append(f'FAIL {label}: Blender finished but wrote no picture at {picture}')
        return log
    dark_limit = numbers.value('place_render.dark_picture_mean_luminance_min')
    try:
        mean = mean_luminance(picture)
    except Exception:   # noqa: BLE001 - the dark check is a courtesy; the picture itself is fine
        mean = None
    log['mean_luminance'] = mean
    with open(base + '.json', 'w', encoding='utf-8') as handle:
        json.dump(log, handle, indent=1)
    lines.append(f'PASS {label}: {engine.lower()} {width} x {height}, {samples} samples, {seconds} s on {device} -> {os.path.basename(picture)} (' + '; '.join(reasons[:2]) + ')')
    if capped:
        lines.append(f'LOOK {label}: kept tiny because this computer is slow; send the job to a rented card (--where rented) for the real size')
    if mean is not None and mean < dark_limit:
        lines.append(f'FAIL {label}: the picture is nearly black (mean luminance {mean:.4f}, under {dark_limit}): the scene has no light the camera sees; run explainer-film-place light')
        log['ok'] = False
    return log


def run_command(parsed):
    """The `render` verb inside Blender. parsed.job, parsed.engine, parsed.finals and parsed.where come from place_kit/cli.py."""
    from ..commands import InputMissing
    try:
        job = read_job(parsed.job)
    except JobProblem as problem:
        raise InputMissing(str(problem))
    if job.get('scene') and os.path.abspath(job['scene']) != os.path.abspath(bpy.data.filepath or ''):
        if not os.path.exists(job['scene']):
            raise InputMissing(f'the scene {job["scene"]} named in the job is not there')
        bpy.ops.wm.open_mainfile(filepath=job['scene'], load_ui=False)
    on_card = (parsed.where == 'on-card')
    out_folder = os.path.abspath(job['out_folder'])
    os.makedirs(out_folder, exist_ok=True)
    lines, logs = [], []
    for view in job['views']:
        explicit = [k for k in view.get('kinds', []) if k in ('preview', 'close_up', 'final')] if isinstance(view.get('kinds'), list) else []
        if explicit:
            kinds = explicit
        else:
            kinds = ['preview']
            if parsed.finals:
                kinds.append(view.get('kind') if view.get('kind') in ('close_up', 'final') else 'final')
        wants_real_size = parsed.finals or any(k in ('close_up', 'final') for k in explicit)
        for kind in kinds:
            logs.append(draw_one(job, view, kind, parsed.engine, wants_real_size, on_card, out_folder, lines))
    failed = [log for log in logs if not log.get('ok')]
    for line in lines:
        print(line)
    print(f'{"FAIL" if failed else "PASS"} render: {len(logs) - len(failed)} of {len(logs)} picture(s) drawn into {out_folder}')
    return 1 if failed else 0
