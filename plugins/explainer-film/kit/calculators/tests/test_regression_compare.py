"""What this does: tests regression_compare.py (several draws per version; the old-against-old spread first) on made-up
pictures, so it needs no project files:
  - a speckle that also appears between two draws of the OLD version must not be called real;
  - the house sample's case (the old code itself gives two outcomes, 7.7 percent of dots apart) must not be called real;
  - a true change (a patch made lighter in every new draw) must be called real;
  - fewer than 3 draws of a version is refused (exit 2), and the report always says how many pictures and draws it compared.
Run: python3 kit/calculators/tests/test_regression_compare.py
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, work_folder  # noqa: E402

import cv2  # noqa: E402
import numpy as np  # noqa: E402

TOOL = os.path.join(CALCULATORS, 'regression_compare.py')
check = Checker('regression_compare: several draws, the control first')
work = work_folder('regression-compare-test-')
generator = np.random.default_rng(7)
base = generator.integers(20, 200, size=(120, 90, 3)).astype(np.uint8)


def speckled(picture, count, seed):
    """The picture with a few dots changed by 3 levels at random places (ordinary drawing noise)."""
    out = picture.copy()
    spots = np.random.default_rng(seed)
    for _ in range(count):
        y, x = spots.integers(0, picture.shape[0]), spots.integers(0, picture.shape[1])
        out[y, x] = np.clip(out[y, x].astype(int) + 3, 0, 255)
    return out


def write_set(folder, name, pictures):
    os.makedirs(folder, exist_ok=True)
    for k, picture in enumerate(pictures, 1):
        cv2.imwrite(os.path.join(folder, f'{name}-{k}.png'), picture)


def run(old, new, *extra):
    out = os.path.join(work, 'result.json')
    done = subprocess.run([sys.executable, '-I', '-B', TOOL, '--old', old, '--new', new, '--out', out, *extra],
                          capture_output=True, text=True, timeout=120)
    result = json.load(open(out)) if done.returncode in (0, 1) and os.path.exists(out) else None
    if os.path.exists(out):
        os.remove(out)
    return done, result


# 1. a speckle: old draws 1 and 3 are clean, old draw 2 has a speckle; new draws carry speckles in other places
old_folder, new_folder = os.path.join(work, 'speckle-old'), os.path.join(work, 'speckle-new')
write_set(old_folder, 'street', [base, speckled(base, 40, 1), base])
write_set(new_folder, 'street', [speckled(base, 40, 2), base, speckled(base, 35, 3)])
done, result = run(old_folder, new_folder)
first = result['pictures'][0] if result else {}
check.true('a speckle that the old version also shows between its own draws is "within ordinary variation"',
           done.returncode == 0 and first.get('verdict') == 'within ordinary variation',
           details=f'exit {done.returncode}; verdict {first.get("verdict")}; spread {first.get("spread_changed_share")}',
           proves='a one-draw comparison (new 1 against old 1 differs) is not read as a fault when the control shows the same')
check.true('the report prints the old-against-old spread before old against new',
           0 <= done.stdout.find('old against old') < done.stdout.find('old against new'), details=done.stdout[:300])
check.true('the report says how many pictures and draws it compared', 'Compared 1 picture(s)' in done.stdout and '6 picture files' in done.stdout,
           details=[l for l in done.stdout.splitlines() if l.startswith('Compared')][:1])

# 2. the house sample's case: the unchanged old code itself gives two outcomes (7.7 percent of dots, at most 7 levels apart)
outcome_b = base.copy()
mask = np.random.default_rng(4).random(base.shape[:2]) < 0.077
outcome_b[mask] = np.clip(outcome_b[mask].astype(int) + 7, 0, 255).astype(np.uint8)
old_folder, new_folder = os.path.join(work, 'two-outcomes-old'), os.path.join(work, 'two-outcomes-new')
write_set(old_folder, 'house-sample-20s', [base, outcome_b, base])
write_set(new_folder, 'house-sample-20s', [outcome_b, base, outcome_b])
done, result = run(old_folder, new_folder)
first = result['pictures'][0] if result else {}
check.true('two outcomes of the unchanged old code (7.7 percent of dots) are "within ordinary variation"',
           done.returncode == 0 and first.get('verdict') == 'within ordinary variation',
           details=f'exit {done.returncode}; verdict {first.get("verdict")}',
           recorded='project story logs 37 to 39 (the house sample at 20 s drawn ten times with the old stage)')

# 3. a true change: a patch made 30 levels lighter in every new draw, on top of ordinary speckles
changed = base.copy()
changed[30:70, 20:60] = np.clip(changed[30:70, 20:60].astype(int) + 30, 0, 255).astype(np.uint8)
old_folder, new_folder = os.path.join(work, 'change-old'), os.path.join(work, 'change-new')
write_set(old_folder, 'street', [base, speckled(base, 40, 5), speckled(base, 40, 6)])
write_set(new_folder, 'street', [speckled(changed, 40, 7), changed, speckled(changed, 40, 8)])
done, result = run(old_folder, new_folder)
first = result['pictures'][0] if result else {}
check.true('a true change in every new draw is called "real" (exit 1)', done.returncode == 1 and first.get('verdict') == 'real',
           details=f'exit {done.returncode}; verdict {first.get("verdict")}; draws outside the spread {first.get("draws_outside_the_spread")}',
           proves='the tool does not just say "within" to everything: this case must fail')

# 4. a change in only one new draw is not a proof of a change
old_folder, new_folder = os.path.join(work, 'one-draw-old'), os.path.join(work, 'one-draw-new')
write_set(old_folder, 'street', [base, base, base])
write_set(new_folder, 'street', [changed, base, base])
done, result = run(old_folder, new_folder)
first = result['pictures'][0] if result else {}
check.true('a difference in only one of three new draws is "within ordinary variation"', first.get('verdict') == 'within ordinary variation',
           details=f'verdict {first.get("verdict")}')

# 5. fewer than 3 draws is refused
old_folder, new_folder = os.path.join(work, 'few-old'), os.path.join(work, 'few-new')
write_set(old_folder, 'street', [base, base])
write_set(new_folder, 'street', [base, base, base])
done, _ = run(old_folder, new_folder)
check.true('two draws of the old version are refused (exit 2) with the reason', done.returncode == 2 and 'at least 3' in done.stderr,
           details=f'exit {done.returncode}; {done.stderr.strip()[:200]}')

# 6. a NAME in one folder only is refused
write_set(new_folder, 'yard', [base, base, base])
write_set(old_folder, 'street', [base, base, base])
done, _ = run(old_folder, new_folder)
check.true('a picture drawn only with the new version is refused (exit 2)', done.returncode == 2 and 'yard' in done.stderr,
           details=f'exit {done.returncode}; {done.stderr.strip()[:200]}')
check.finish()
