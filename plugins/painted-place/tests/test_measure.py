"""
What this file does: checks the measures against the look's bands: every reference picture sits inside every
band; the coal mine as it was fails the warm-light band; the first dark pass fails brightness.
    python3 tests/test_measure.py
"""
import os
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / '..' / 'look'))
import measure  # noqa: E402


def main():
    plugin = HERE.parent
    for picture in sorted((plugin / 'look' / 'reference').glob('*.jpg')):
        judged = measure.verdicts(measure.measure(Image.open(picture)))
        assert all(v == 'inside' for v in judged.values()), (picture.name, judged)
    as_is = measure.verdicts(measure.measure(Image.open(plugin / 'examples' / 'coal-mine' / 'mine-A-as-is.jpg')))
    assert as_is['warm_light_coverage'] == 'low', as_is
    dark = measure.verdicts(measure.measure(Image.open(plugin / 'examples' / 'coal-mine' / 'mine-B-look.jpg')))
    assert dark['brightness'] == 'low', dark
    fixed = measure.verdicts(measure.measure(Image.open(plugin / 'examples' / 'coal-mine' / 'mine-C-look-fixed.jpg')))
    assert all(v == 'inside' for v in fixed.values()), fixed
    assert measure.dial_for('brightness', 'low').startswith('raise exposure')
    print('PASS test_measure')


if __name__ == '__main__':
    main()
