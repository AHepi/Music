"""What this does: reads the place kit's house numbers (the place_* sections of kit/film-settings.json) through the
calculators' own reader (calculators/settings.py), so a number lives in one table and no file of the kit keeps its own
copy. It also remembers which numbers a run read, so a report can name them.
Plain Python (standard library only): it works inside Blender's own Python and outside it.

A concrete example: house_numbers.value('place_construction.float_gap_millimetres_fail') gives 5. A key that is not in
the table stops with a plain sentence naming the nearest real keys (that is settings.py's message).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLACE_KIT = os.path.dirname(HERE)
KIT = os.path.dirname(PLACE_KIT)
CALCULATORS = os.path.join(KIT, 'calculators')
if CALCULATORS not in sys.path:
    sys.path.insert(0, CALCULATORS)

import settings as film_settings  # noqa: E402  (the calculators' reader; standard library only)

_cache = {}


def settings_path():
    return os.environ.get('FILM_SETTINGS') or os.path.join(KIT, 'film-settings.json')


def table():
    """The loaded settings table (read once per run)."""
    path = settings_path()
    if path not in _cache:
        _cache[path] = film_settings.load_settings(path)
    return _cache[path]


def value(key):
    """The number (or list, or text) at a dotted key such as 'place_wear.litter_clearance_metres'."""
    return table().value(key)


def entry(key):
    return table().entry(key)


def section(key):
    return table().section(key)


def has(key):
    return table().has(key)


def used_lines():
    """Plain lines naming every house number read so far (put them in a report)."""
    return table().used_lines()


def used_json():
    return table().used_json()
