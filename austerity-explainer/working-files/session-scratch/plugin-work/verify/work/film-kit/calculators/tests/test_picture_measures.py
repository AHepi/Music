"""What this does: tests picture_measures.py on made-up pictures whose answers are known.
1. A flat grey picture has every 96 x 96 window flat, so the check fails its flat-windows line; a picture of fine noise has a large detail energy and no flat window.
2. A blurred copy of the noise has a lower detail energy than the noise (the measure sees the difference).
3. Two identical pictures have a squint similarity of 1.0; a picture and its light-and-dark opposite have a low one.
4. A saturated patch is counted as a share of strong colour; a cyan patch is counted as turquoise; a white square is found as a blown-out patch of the right size.
5. A guard made from a picture passes that same picture and fails a flattened copy (the value range and the detail energy both move).
6. A 2600 pixel wide picture is shrunk to at most 2400 with a float32 buffer and still measures.
7. The command line works end to end (measure, make-guard, check, squint, crops) and the exit code is 1 on a failed check and 2 on a missing picture.
Run: python3 kit/calculators/tests/test_picture_measures.py
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, skip  # noqa: E402

try:
    import numpy as np
    from PIL import Image
except ImportError:
    skip('picture measures', 'numpy and Pillow are needed (pip install numpy pillow)')

import picture_measures as pm  # noqa: E402
from settings import load_settings  # noqa: E402

check = Checker('picture measures: made-up pictures with known answers')
settings = load_settings()
folder = tempfile.mkdtemp(prefix='picture-measures-test-')


def save(name, array):
    path = os.path.join(folder, name)
    Image.fromarray(np.clip(array * 255.0 + 0.5, 0, 255).astype(np.uint8)).save(path)
    return path


def run(args):
    return subprocess.run([sys.executable, '-I', '-B', os.path.join(CALCULATORS, 'picture_measures.py')] + args, capture_output=True, text=True, timeout=180)


rng = np.random.default_rng(3)
size = 256
flat = np.full((size, size, 3), 0.45, dtype=np.float32)
noise = np.clip(0.45 + rng.normal(0, 0.12, (size, size, 1)), 0, 1).repeat(3, axis=2).astype(np.float32)
blurred_noise = np.stack([pm.gaussian_blur(noise[..., 0], 3.0)] * 3, axis=2)
gentle = np.clip(0.45 + np.random.default_rng(4).normal(0, 0.03, (size, size, 1)), 0, 1).repeat(3, axis=2).astype(np.float32)
blurred_gentle = np.stack([pm.gaussian_blur(gentle[..., 0], 3.0)] * 3, axis=2)
flat_path, noise_path, blurred_path = save('flat.png', flat), save('noise.png', noise), save('blurred.png', blurred_noise)
gentle_path, blurred_gentle_path = save('gentle.png', gentle), save('blurred-gentle.png', blurred_gentle)

# 1. flat versus noise
flat_measure = pm.measure_picture(flat_path, settings)
noise_measure = pm.measure_picture(noise_path, settings)
windows = flat_measure['flat_windows']
check.true('flat grey: every window is flat', windows['windows'] > 0 and windows['flat'] == windows['windows'], f'{windows["flat"]} of {windows["windows"]} flat',
           recorded='a flat picture has a spread of 0 in every window (made here)', proves='the flat-window measure finds plain colour')
check.true('noise: no window is flat', noise_measure['flat_windows']['flat'] == 0, f'{noise_measure["flat_windows"]["flat"]} flat of {noise_measure["flat_windows"]["windows"]}')
check.true('noise has a larger detail energy than flat grey', noise_measure['detail_energy']['all'] > flat_measure['detail_energy']['all'] + 3.0,
           f'noise {noise_measure["detail_energy"]["all"]:.2f}, flat {flat_measure["detail_energy"]["all"]:.2f}')
check.close('flat grey has a detail energy of 0', flat_measure['detail_energy']['all'], 0.0, 0.05)

# 2. blur lowers detail
blurred_noise_measure = pm.measure_picture(blurred_path, settings)
check.true('a blurred copy has a lower detail energy', blurred_noise_measure['detail_energy']['all'] < 0.6 * noise_measure['detail_energy']['all'],
           f'blurred {blurred_noise_measure["detail_energy"]["all"]:.2f}, noise {noise_measure["detail_energy"]["all"]:.2f}')

# 3. squint
same, _ = pm.squint_similarity(pm.load_picture(noise_path), pm.load_picture(noise_path))
check.close('identical pictures: squint similarity is 1', same, 1.0, 0.001)
ramp = np.tile(np.linspace(0.1, 0.9, size, dtype=np.float32)[None, :, None], (size, 1, 3))
opposite, _ = pm.squint_similarity(ramp, 1.0 - ramp)
check.true('light-and-dark opposite pictures: squint similarity is low', opposite < 0.2, f'got {opposite:.3f}')

# 4. colour shares
patch = np.full((size, size, 3), 0.4, dtype=np.float32)
patch[:64, :64] = (1.0, 0.0, 0.0)
patch_path = save('red-patch.png', patch)
patch_measure = pm.measure_picture(patch_path, settings)
check.close('a red patch of a sixteenth is counted as strong colour', patch_measure['strong_saturation_share'], 1 / 16, 0.01)
cyan = np.full((size, size, 3), 0.4, dtype=np.float32)
cyan[:64, :64] = (0.0, 0.8, 0.8)
cyan_measure = pm.measure_picture(save('cyan-patch.png', cyan), settings)
check.close('a cyan patch of a sixteenth is counted as turquoise', cyan_measure['turquoise_share'], 1 / 16, 0.01)
check.true('a red patch is not counted as turquoise', patch_measure['turquoise_share'] < 0.001, f'{patch_measure["turquoise_share"]:.4f}')
white = np.full((size, size, 3), 0.3, dtype=np.float32)
white[100:140, 50:90] = 1.0
white_measure = pm.measure_picture(save('white-square.png', white), settings)
check.equal('a white square of 40 x 40 is found as a patch of 1600 pixels', white_measure['white_patch_pixels'], 1600)

# 5. guard (made from gentle noise: a picture of fine, strong noise is over the busy cap even against its own guard)
gentle_measure = pm.measure_picture(gentle_path, settings)
blurred_measure = pm.measure_picture(blurred_gentle_path, settings)
busy = {f['check'].split(': ')[1]: f['verdict'] for f in pm.check_picture(noise_measure, pm.make_guard(noise_measure), settings)}
check.equal('a very busy picture fails detail energy even against its own guard (the cap)', busy['detail energy'], 'fail')
guard = pm.make_guard(gentle_measure)
check.true('a guard from a picture is marked provisional', guard['provisional'] is True)
own = pm.check_picture(gentle_measure, guard, settings)
check.true('a guard passes its own picture', all(f['verdict'] in ('pass', 'warn') for f in own), ', '.join(f'{f["check"].split(": ")[1]} {f["verdict"]}' for f in own))
flattened = pm.check_picture(flat_measure, guard, settings)
flat_verdicts = {f['check'].split(': ')[1]: f['verdict'] for f in flattened}
check.equal('the guard fails the flattened copy on flat windows', flat_verdicts['flat windows'], 'fail')
check.equal('the guard fails the flattened copy on detail energy', flat_verdicts['detail energy'], 'fail')
blurred_checks = {f['check'].split(': ')[1]: f['verdict'] for f in pm.check_picture(blurred_measure, guard, settings)}
check.equal('the guard fails the blurred copy on detail energy (too flat)', blurred_checks['detail energy'], 'fail')

# 6. a large picture is shrunk
large_path = os.path.join(folder, 'large.png')
Image.fromarray((np.random.default_rng(1).random((120, 2600, 3)) * 255).astype(np.uint8)).save(large_path)
large = pm.load_picture(large_path)
check.true('a 2600 wide picture is shrunk to at most 2400 and kept as float32', large.shape[1] <= pm.MAX_SIDE and large.dtype == np.float32, f'shape {large.shape}, type {large.dtype}')

# 7. the command line
done = run(['measure', noise_path, '--json'])
check.equal('measure exits 0', done.returncode, 0)
guard_path = os.path.join(folder, 'guard.json')
done = run(['make-guard', gentle_path, '--out', guard_path])
check.true('make-guard writes a provisional guard', done.returncode == 0 and os.path.exists(guard_path) and json.load(open(guard_path)).get('provisional') is True, 'exit ' + str(done.returncode))
done = run(['check', gentle_path, '--guard', guard_path])
check.equal('check passes the same picture (exit 0)', done.returncode, 0)
done = run(['check', flat_path, '--guard', guard_path])
check.equal('check fails the flattened picture (exit 1)', done.returncode, 1)
check.true('the failed check says which line failed', 'FAIL place pictures: flat windows' in done.stdout, done.stdout[:300])
done = run(['squint', noise_path, noise_path])
check.true('squint of identical pictures passes', done.returncode == 0 and 'PASS' in done.stdout, done.stdout[:200])
done = run(['check', os.path.join(folder, 'not-there.png'), '--guard', guard_path])
check.equal('a missing picture exits 2', done.returncode, 2)
done = run(['crops', gentle_path, '--boxes', '10,10,64,64', '--out-folder', os.path.join(folder, 'crops'), '--previous', blurred_gentle_path])
check.true('crops writes a crop and a before-and-after strip', done.returncode == 0 and len(os.listdir(os.path.join(folder, 'crops'))) == 2, done.stdout[-200:] + done.stderr[-200:])
check.finish()
