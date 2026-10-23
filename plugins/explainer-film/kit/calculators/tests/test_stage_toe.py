"""What this does: tests the page look's "toe" setting (copied from the project's film kit, lessons round of 23 October).
A dark or wet painted place lost brightness in the stage's filmic curve: the wet lockout road arrived at 0.75 to 0.86 of
how bright it was painted (measured). look.toe 1 lets the curve brighten a value but never darken it; toe 0 (the
default) is the curve as it always was. This test checks:
  - the stage (paper-film/stage/cinema-stage.js) carries the toe lines exactly as the film kit has them, and no bare
    "c = aces(c);" is left;
  - the lockout test page sets "vignette: 0.25, toe: 1";
  - the Python copy of the finish pass (painting_measures.py) on a ramp of values: toe 0, and a look with no toe at all,
    give exactly the old numbers (the old sum is kept here as a copy); toe 1 never gives a value darker than the input
    (the curve alone, and the whole finish with a plain look); and, as the case that must fail, toe 0 does darken
    dark values (so the toe check above could catch a curve that darkens).
By reading the code: mix(filmicValue, max(filmicValue, c), 0) is filmicValue itself, so a page without a toe is unchanged.
Run: python3 kit/calculators/tests/test_stage_toe.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT  # noqa: E402

import numpy as np  # noqa: E402

import painting_measures as pm  # noqa: E402
from settings import load_settings  # noqa: E402

check = Checker('stage toe: dark painted values stay as painted; toe 0 changes nothing')
STAGE = os.path.join(KIT, 'paper-film', 'stage', 'cinema-stage.js')
LOCKOUT = os.path.join(KIT, 'paper-film', 'scenes', 'lockout-test.js')
stage = open(STAGE).read()
for line in ('uniform float toe;', 'vec3 filmicValue = aces(c);', 'c = mix(filmicValue, max(filmicValue, c), toe);',
             'toe: { value: 0 },', 'toe: 0,', 'u.toe.value = look.toe;'):
    check.true(f'the stage has "{line}"', line in stage, recorded='the film kit\'s paper-film/stage/cinema-stage.js lines 216-334')
check.true('the stage has no bare "c = aces(c);" left', 'c = aces(c);' not in stage)
check.true('the lockout test page sets "vignette: 0.25, toe: 1"', 'vignette: 0.25, toe: 1' in open(LOCKOUT).read(),
           recorded='the film kit\'s scenes/lockout-test.js line 180')


def old_stage_finish(rgb, look):
    """The Python finish pass as it was before the toe (copied unchanged from painting_measures.py)."""
    c = pm.srgb_to_linear(rgb) * look['exposure']
    c = np.clip((c * (2.51 * c + 0.03)) / (c * (2.43 * c + 0.59) + 0.14), 0, 1)
    luma = c @ np.array([0.2126, 0.7152, 0.0722])
    c = luma[..., None] + (c - luma[..., None]) * look['saturation']
    c = (c - 0.5) * look['contrast'] + 0.5
    t = np.clip((luma - 0.05) / 0.70, 0, 1)
    t = t * t * (3 - 2 * t)
    shadow, high = np.array(look['shadow_tint']), np.array(look['highlight_tint'])
    tint = shadow + (high - shadow) * t[..., None]
    c = c + (c * tint * 2.0 - c) * look['tint_amount']
    c = c + look['lift'] * (1 - c)
    return pm.linear_to_srgb(np.clip(c, 0, 1))


film_look = dict(load_settings().value('painting_tools.paint_request.film_look'))
ramp = np.stack([np.arange(256.0)] * 3, axis=1)                          # grey ramp 0..255
colours = np.random.default_rng(3).integers(0, 256, size=(2000, 3)).astype(float)
for name, values in (('a grey ramp 0-255', ramp), ('2000 random colours', colours)):
    old = old_stage_finish(values, film_look)
    check.true(f'toe 0 gives exactly the old numbers ({name}, the film look)', np.array_equal(pm.stage_finish(values, dict(film_look, toe=0)), old),
               proves='a page without a toe looks as it always did')
    check.true(f'a look with no toe gives exactly the old numbers ({name})', np.array_equal(pm.stage_finish(values, film_look), old))

linear = np.linspace(0.0, 1.5, 3001)
check.true('toe 1: the curve never gives a value darker than the input (0 to 1.5 linear)',
           bool((pm.filmic_curve(linear, 1) >= linear - 1e-12).all()),
           details=f'smallest output minus input {float((pm.filmic_curve(linear, 1) - linear).min()):.3g}')
plain_look = {'exposure': 1.0, 'saturation': 1.0, 'contrast': 1.0, 'shadow_tint': [0.5, 0.5, 0.5], 'highlight_tint': [0.5, 0.5, 0.5],
              'tint_amount': 0.0, 'lift': 0.0, 'toe': 1}
through = pm.stage_finish(ramp, plain_look)
check.true('toe 1: the whole finish with a plain look never darkens a ramp value', bool((through >= ramp - 1e-6).all()),
           details=f'smallest output minus input {float((through - ramp).min()):.3g} levels')
darkened = pm.filmic_curve(linear, 0) < linear - 1e-6
check.true('the case that must fail: toe 0 does darken dark values (so the check above can catch a darkening curve)',
           bool(darkened[(linear > 0.001) & (linear < 0.06)].all()),   # the ACES curve darkens linear values below about 0.062
           details=f'linear 0.05 comes out {float(pm.filmic_curve(np.array([0.05]), 0)[0]):.4f} with toe 0, '
                   f'{float(pm.filmic_curve(np.array([0.05]), 1)[0]):.4f} with toe 1')
check.finish()
