"""What this does: tests the four after_painting.py checks added in the lessons round (23 October), on made-up pictures,
so it runs without the project's paintings (test_after_painting.py skips without the working files):
  - the pale patch (--behind): a dry behind picture behind a wet painting FAILS with "pale patch"; a matched behind
    picture (another painting of the same wet road, so different dot for dot) passes;
  - the road as filmed (--toe 0|1): a dark wet road gives a LOOK with "arrives at" under 0.9 with toe 0, and arrives
    brighter with toe 1;
  - the bottom of the frame: a bottom fifth much darker than the middle gives a LOOK with "bottom fifth"; an even
    picture passes;
  - a plain sky: pale blotches in the plate's sky area give a LOOK with "clouds"; a plain graded sky passes.
Each check has a case that must fail (or warn) and one that must pass. Also: the pale-patch and clouds measures' controls through
checks.py's controls helper (which itself refuses a one-sided test); the "sky" command, which lays the plate's plain sky exactly
inside the plate's sky area into a new file (a thin rail stays as painted, the clouds LOOK stops); and earlier outputs kept as
NAME-previous.png, never written over.
Run: python3 kit/calculators/tests/test_after_painting_lessons.py
"""
import os
import subprocess
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, work_folder  # noqa: E402

import cv2  # noqa: E402
import numpy as np  # noqa: E402

import after_painting as ap  # noqa: E402
from settings import load_settings  # noqa: E402

settings = load_settings()
check = Checker('after_painting: pale patch, the road as filmed, the bottom fifth, clouds')
WIDTH, HEIGHT = 384, 683            # a quarter of the 1536 x 2730 plate
random = np.random.default_rng(11)


def road_texture(mean, spread=14, seed=0):
    """A painted road: soft blotches round a mean brightness (each seed is a different painting of it)."""
    noise = np.random.default_rng(seed).normal(0, 1, (HEIGHT, WIDTH)).astype(np.float32)
    noise = cv2.GaussianBlur(noise, (0, 0), 2) * spread * 2
    grey = np.clip(mean + noise, 0, 255)
    return np.stack([grey * 1.02, grey, grey * 0.95], axis=2).astype(np.float32)


def verdicts(found):
    return {f['check']: f for f in found}


# ------------------------------------------------------------------------------------------------ pale patch
prop = np.zeros((HEIGHT, WIDTH), bool)
prop[420:540, 140:240] = True                      # a near prop (sacks) on the road
wet_front = road_texture(55, seed=1)
wet_front[prop] = 25                               # the prop itself, dark
wet_behind = road_texture(55, seed=2)              # another painting of the same wet road, no prop
dry_behind = road_texture(95, seed=3)              # the old dry behind painting: pale and dry
matched = ap.pale_patch(wet_front, wet_behind, prop, prop, settings)
dry = ap.pale_patch(wet_front, dry_behind, prop, prop, settings)
found = []
ap.judge_pale_patch(found, matched, settings)
ap.judge_pale_patch(found, dry, settings)
check.true('a matched wet behind picture passes (two paintings differ dot for dot, so local brightness is compared)',
           found[0]['verdict'] == 'pass', details=f'lighter share {matched["lighter_share"]:.3f}: {found[0]["what"][:160]}')
check.true('the case that must fail: a dry behind picture behind a wet painting FAILS with "pale patch"',
           found[1]['verdict'] == 'fail' and 'pale patch' in found[1]['what'],
           details=f'lighter share {dry["lighter_share"]:.3f}: {found[1]["what"][:160]}',
           recorded='film kit 05 "A dark painted street" (log 37): 59 percent of the hidden road dots lighter with the dry behind painting')
check.true('the limit is marked invented in film-settings.json', settings.entry('painting_tools.after_painting.pale_patch')['kind'] == 'invented'
           if hasattr(settings, 'entry') else True)

# ------------------------------------------------------------------------------------------------ a fake view for the look checks
SKY_ROWS = int(0.3 * 1920)


def fake_shot():
    """A view at the facts size (1080 x 1920): sky in the top 30 percent, the ground from 0.45 down, one prop."""
    sky = np.zeros((1920, 1080), bool)
    sky[:SKY_ROWS, :] = True
    sacks = np.zeros((1920, 1080), bool)
    sacks[1200:1500, 400:700] = True
    return types.SimpleNamespace(sky=sky, height=1920, ground_horizon=0.45 * 1920, facts={'groups': {'sacks': {}}}, visible={'sacks': sacks})


def picture(sky_mean, ground_mean, clouds=False, bottom_mean=None):
    out = road_texture(ground_mean, seed=5)
    rows = int(0.3 * HEIGHT)
    grade = np.linspace(sky_mean - 6, sky_mean + 6, rows)[:, None]          # an evenly graded plain sky
    out[:rows] = np.stack([grade * 0.9, grade * 0.95, grade * 1.1], axis=2) * np.ones((1, WIDTH, 1))
    if clouds:
        blotches = cv2.GaussianBlur(random.normal(0, 1, (rows, WIDTH)).astype(np.float32), (0, 0), 12)
        blotches = np.clip(blotches / blotches.std(), 0, None) * 45                    # heavy pale clouds
        out[:rows] += blotches[:, :, None]
    if bottom_mean is not None:
        out[int(0.8 * HEIGHT):] = bottom_mean
    return np.clip(out, 0, 255)


shot = fake_shot()
dark_wet = picture(20, 40)
found = []
toe0 = ap.look_checks(dark_wet, shot, 0, settings, found)['road']
road0 = verdicts(found)['the road as filmed']
found = []
toe1 = ap.look_checks(dark_wet, shot, 1, settings, found)['road']
road1 = verdicts(found)['the road as filmed']
check.true('the case that must warn: a dark wet road with toe 0 arrives under 0.9 (LOOK, "arrives at")',
           road0['verdict'] == 'look' and 'arrives at' in road0['what'] and toe0['arrives_share'] < 0.9,
           details=road0['what'][:200], recorded='the wet lockout road arrived at 0.75 to 0.86 without a toe (log 37)')
check.true('toe 1 lets the same road arrive brighter, and the line still says "arrives at"',
           toe1['arrives_share'] > toe0['arrives_share'] and 'arrives at' in road1['what'],
           details=f'toe 0: {toe0["arrives_share"]:.3f}, toe 1: {toe1["arrives_share"]:.3f}; {road1["verdict"]}')
check.true('the fix line for toe 0 names look.toe and vignette 0.25', 'toe: 1' in road0['fix'] and 'vignette: 0.25' in road0['fix'], details=road0['fix'])

found = []
ap.look_checks(picture(20, 110), shot, 0, settings, found)
even = verdicts(found)
check.true('an even picture passes the bottom-of-frame check', even['the bottom of the frame']['verdict'] == 'pass',
           details=even['the bottom of the frame']['what'])
check.true('a plain graded sky passes the sky check', even['a plain sky']['verdict'] == 'pass', details=even['a plain sky']['what'])
found = []
ap.look_checks(picture(20, 110, bottom_mean=35), shot, 0, settings, found)
floor = verdicts(found)['the bottom of the frame']
check.true('the case that must warn: a bottom fifth much darker than the middle gives a LOOK with "bottom fifth"',
           floor['verdict'] == 'look' and 'bottom fifth' in floor['what'], details=floor['what'][:200],
           recorded='composing.bottom_fifth_darker_max_share 0.3 (log 26 review)')
found = []
ap.look_checks(picture(20, 110, clouds=True), shot, 0, settings, found)
sky = verdicts(found)['a plain sky']
check.true('the case that must warn: pale blotches in the plate\'s sky area give a LOOK with "clouds"',
           sky['verdict'] == 'look' and 'clouds' in sky['what'], details=sky['what'][:200], recorded='textures logs 19, 24, 25')

# the measures' controls (a case each must score high and one it must score low), through the shared helper
cloudy = ap.sky_clouds(picture(20, 110, clouds=True), shot.sky, settings)['spread_levels']
plain = ap.sky_clouds(picture(20, 110), shot.sky, settings)['spread_levels']
check.controls('the pale-patch measure: a dry behind picture scores high, a matched one low', {'dry behind picture': dry['lighter_share']},
               {'matched wet behind picture': matched['lighter_share']}, 0.5, 0.1)
check.controls('the clouds measure: a cloudy sky scores high, a plain graded sky low', {'cloudy sky': cloudy}, {'plain graded sky': plain}, 8.0, 2.0)
a_control_missing = Checker.__new__(Checker)
a_control_missing.passed, a_control_missing.failed, a_control_missing.notes, a_control_missing.title = 0, [], [], 'scratch'
import contextlib, io  # noqa: E401,E402
with contextlib.redirect_stdout(io.StringIO()):
    held = a_control_missing.controls('one-sided', {'only a high case': 1.0}, {}, 0.5, 0.1)
check.true('the controls helper refuses a measure tested with only one side (a control that must score low is missing)', held is False)

# the plain sky helper (sky): the plate's plain sky laid exactly inside the plate's sky area, into a new file; earlier outputs kept
import tempfile  # noqa: E402
work = work_folder('after-painting-sky-')
facts = os.path.join(work, 'facts')
os.makedirs(facts)
ids = np.full((1920, 1080, 3), 90, np.uint8)
ids[:SKY_ROWS] = 0                                                   # nothing drawn: the sky
ids[SKY_ROWS - 200:SKY_ROWS, 530:550] = 90                           # a thin chimney rail standing into the sky
cv2.imwrite(os.path.join(facts, 'ids.png'), ids)
cloudy_painting = picture(20, 110, clouds=True)
plate_picture = picture(30, 100)
for name, rgb in (('painting.png', cloudy_painting), ('plate.png', plate_picture)):
    cv2.imwrite(os.path.join(work, name), np.clip(rgb, 0, 255).astype(np.uint8)[:, :, ::-1])
target = os.path.join(work, 'painting-plain-sky.png')
for _ in range(2):
    done = subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'after_painting.py'), 'sky', '--painting', os.path.join(work, 'painting.png'),
                           '--plate', os.path.join(work, 'plate.png'), '--facts', facts, '--to', target], capture_output=True, text=True, timeout=120)
result = cv2.imread(target)[:, :, ::-1].astype(np.float32)
sky_here = ap.sky_mask_from_facts(facts, (WIDTH, HEIGHT))
check.true('sky: the plate\'s sky is laid in exactly inside the sky area, and the rest of the painting is untouched',
           done.returncode == 0 and np.abs(result[sky_here] - np.round(plate_picture[sky_here])).max() <= 1 and np.abs(result[~sky_here] - np.round(cloudy_painting[~sky_here])).max() <= 1,
           details=done.stdout.splitlines()[2] if len(done.stdout.splitlines()) > 2 else done.stderr[-200:])
check.true('sky: the thin rail inside the sky stays as painted (the exact outline, no blur)', not sky_here[int((SKY_ROWS - 100) * HEIGHT / 1920), int(540 * WIDTH / 1080)])
check.true('sky: a second run keeps the earlier picture as NAME-previous.png instead of writing over it', os.path.exists(os.path.join(work, 'painting-plain-sky-previous.png'))
           and 'kept as painting-plain-sky-previous.png' in done.stdout, details=done.stdout[:200])
check.true('sky: the clouds LOOK no longer fires on the result', ap.sky_clouds(result, shot.sky, settings)['spread_levels'] <= settings.value('painting_tools.after_painting.sky_clouds')['spread_levels_max'])
refused = subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'after_painting.py'), 'sky', '--painting', os.path.join(work, 'painting.png'),
                          '--plate', os.path.join(work, 'plate.png'), '--facts', facts, '--to', os.path.join(work, 'painting.png')], capture_output=True, text=True, timeout=120)
check.true('sky: writing over the painting itself is refused', refused.returncode != 0 and 'never written over' in (refused.stdout + refused.stderr))
first = os.path.join(work, 'kept.png')
open(first, 'w').write('first')
check.true('keep_previous: an output that is there is kept as NAME-previous.png', ap.keep_previous(first) == os.path.join(work, 'kept-previous.png')
           and open(os.path.join(work, 'kept-previous.png')).read() == 'first' and not os.path.exists(first))

done = subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'after_painting.py'), 'check', '--help'],
                      capture_output=True, text=True, timeout=60)
check.true('after_painting.py check takes --toe 0|1', done.returncode == 0 and '--toe {0,1}' in done.stdout, details=done.stdout[-300:])
check.finish()
