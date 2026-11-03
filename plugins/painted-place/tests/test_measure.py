"""
What this file does: checks the kit's measure tool (brief/measure.py): every reference picture sits inside every band,
and a picture that is too dark is called too dark.
    python3 tests/test_measure.py
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import BRIEF, check  # noqa: E402

sys.path.insert(0, BRIEF)
import measure  # noqa: E402


def main():
    reference = os.path.join(BRIEF, 'reference')
    pictures = sorted(f for f in os.listdir(reference) if f.lower().endswith(('.jpg', '.png')))
    check(len(pictures) >= 5, 'fewer than five reference pictures in %s' % reference)
    for name in pictures:
        judged = measure.verdicts(measure.measure(Image.open(os.path.join(reference, name))))
        check(all(v == 'inside' for v in judged.values()), 'reference picture %s is outside a band: %s' % (name, judged))
    dark = Image.open(os.path.join(reference, pictures[0])).convert('RGB').point(lambda v: v // 4)
    check(measure.verdicts(measure.measure(dark))['brightness'] == 'low', 'a picture at a quarter brightness was not called too dark')
    print('PASS test_measure: %d reference pictures inside every band; a dark picture is called too dark' % len(pictures))


if __name__ == '__main__':
    main()
