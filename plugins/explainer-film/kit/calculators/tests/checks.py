"""What this does: the small shared helper every test in this folder uses to say, line by line, what it checked, the number
it got, the number the project recorded and where that number is recorded, and what the check proves (or only repeats).
A test file builds a Checker, adds checks, and ends with checker.finish(), which prints a plain summary and exits 1 if any
check failed (77 if the whole test was skipped, for example when node is missing).

Use in a test:
    from checks import Checker, CALCULATORS, FIXTURES
    check = Checker('frame geometry: recorded cases')
    check.close('notice corner meeting point across', got, 0.68401, 0.0001, recorded='experiments/31 .../facts.json lines_meet',
                proves='our sums agree with Blender\\'s own camera')
    check.true('settings file has no problems', not problems, details=...)
    check.controls('the new measure tells alike from unlike', {'shuffled copy': 0.99}, {'blurred copy': 0.17, 'another surface': 0.09}, 0.9, 0.3)
    check.finish()
(Not itself a test: run_all.py runs only files named test_*.py.)

Where a test finds files that do not ship with the plugin (the plugin must stand alone: a test never names one machine's
folders; when a file is not found the check is skipped with a plain reason, never failed):
    project_folder()        the project the plugin was made in: FILM_PROJECT, else the folder austerity-explainer next to the
                            plugins folder (this repository's layout: REPO/plugins/explainer-film and REPO/austerity-explainer)
    film_kit_folder()       that project's film kit: FILM_KIT, else PROJECT/film-kit (its large pictures, models and Blender scenes)
    working_files_folder()  the project's working files from the redesign rounds (redesign/..., plan3/..., held-back/...),
                            which were never put in the repository: FILM_WORKING_FILES, else none
    blender_program()       BLENDER, else the kit's machine-settings.env (written by explainer-film-setup), else blender on the PATH
    missing(paths)          the paths that are not there (a test skips a part when this is not empty)
    work_folder(prefix)     a new temporary folder for the test's own files, removed when the test ends; kept (and its path printed) only
                            when a check failed or the test stopped early, so the files can be looked at
"""
import atexit
import os
import shutil
import sys
import tempfile

TESTS = os.path.dirname(os.path.abspath(__file__))
CALCULATORS = os.path.dirname(TESTS)
FIXTURES = os.path.join(TESTS, 'fixtures')
KIT = os.path.dirname(CALCULATORS)
PLUGIN = os.path.dirname(KIT)
if CALCULATORS not in sys.path:
    sys.path.insert(0, CALCULATORS)

SKIPPED = 77

# The tests never download anything: the place kit's surface pass would fetch the free Poly Haven scans when there is a network, and a test must give the same
# answer on any machine, so every test runs with downloads off (the made-in-code surfaces), unless PLACE_KIT_NETWORK_TESTS=1 asks for the one network check in
# test_place_scans.py. A test that wants scans makes its own small library of pictures (the "own_surfaces" route) in its work folder.
if os.environ.get('PLACE_KIT_NETWORK_TESTS') != '1':
    os.environ.setdefault('PLACE_KIT_OFFLINE', '1')
    os.environ.setdefault('PLACE_KIT_SCAN_CACHE', os.path.join(tempfile.gettempdir(), 'explainer-film-tests-no-scan-cache'))     # never the machine's own cache


def project_folder():
    """The project the plugin was made in (its git history, recordings and films), or None when it is not on this machine."""
    folder = os.environ.get('FILM_PROJECT') or os.path.normpath(os.path.join(PLUGIN, '..', '..', 'austerity-explainer'))
    return folder if os.path.isdir(folder) else None


def film_kit_folder():
    """The project's film kit (large paintings, plates, models, Blender scenes), or None."""
    project = project_folder()
    folder = os.environ.get('FILM_KIT') or (os.path.join(project, 'film-kit') if project else '')
    return folder if folder and os.path.isdir(folder) else None


def working_files_folder():
    """The project's working files from the redesign rounds (never in the repository), named by FILM_WORKING_FILES, or None."""
    folder = os.environ.get('FILM_WORKING_FILES', '')
    return folder if folder and os.path.isdir(folder) else None


def blender_program():
    """The Blender program: BLENDER, else the kit's machine-settings.env, else blender on the PATH; None when there is none."""
    candidates = [os.environ.get('BLENDER', '')]
    for settings_file in (os.path.join(KIT, 'machine-settings.env'),):
        if os.path.exists(settings_file):
            for line in open(settings_file):
                if line.startswith('BLENDER='):
                    candidates.append(line.strip().split('=', 1)[1])
    candidates.append(shutil.which('blender') or '')
    return next((c for c in candidates if c and os.path.exists(c)), None)


def missing(paths):
    """The paths (files or folders) that are not there; a None counts as missing."""
    return [p for p in paths if not p or not os.path.exists(p)]


_WORK_FOLDERS = []
_ENDED_CLEANLY = [False]          # set by Checker.finish (no check failed) and by skip(); a test that stops with an error leaves it False


def work_folder(prefix='explainer-film-test-'):
    """A new temporary folder for this test's own files. It is removed when the test ends, unless a check failed or the test stopped with an
    error: then it is kept and its path printed, so the files can be looked at. Before the fix round of 23 October 2026 the tests never removed
    theirs: /tmp held 833 MB of them on a disk with 1.4 GB free (measured), and a full disk makes checks fail for the wrong reason."""
    folder = tempfile.mkdtemp(prefix=prefix)
    if not _WORK_FOLDERS:
        atexit.register(_remove_work_folders)
    _WORK_FOLDERS.append(folder)
    return folder


def _remove_work_folders():
    for folder in _WORK_FOLDERS:
        if not os.path.isdir(folder):
            continue
        if _ENDED_CLEANLY[0]:
            shutil.rmtree(folder, ignore_errors=True)
        else:
            print(f'NOTE  kept this test\'s own folder for a look (a check failed or the test stopped early): {folder}')


WORKING_FILES_WORDS = ('set FILM_WORKING_FILES to the folder holding the project\'s working files from the redesign rounds '
                       '(redesign/, plan3/, held-back/ ...) to run it')
PROJECT_WORDS = ('the project\'s files are not on this machine (FILM_PROJECT, or the folder austerity-explainer next to the plugins folder; '
                 'FILM_KIT for its film kit)')


class Checker:
    def __init__(self, title):
        self.title = title
        self.passed, self.failed, self.notes = 0, [], []
        print(f'== {title}')

    def _line(self, ok, name, text, recorded, proves):
        mark = 'PASS' if ok else 'FAIL'
        print(f'{mark}  {name}: {text}')
        if recorded:
            print(f'      recorded in: {recorded}')
        if proves:
            print(f'      proves: {proves}')
        if ok:
            self.passed += 1
        else:
            self.failed.append(name)
        return ok

    def close(self, name, got, expected, tolerance, recorded='', proves=''):
        ok = got is not None and abs(got - expected) <= tolerance
        text = f'got {fmt(got)}, recorded {fmt(expected)} (allowed difference {fmt(tolerance)})'
        return self._line(ok, name, text, recorded, proves)

    def within(self, name, got, low, high, recorded='', proves=''):
        ok = got is not None and low <= got <= high
        return self._line(ok, name, f'got {fmt(got)}, must lie in [{fmt(low)}, {fmt(high)}]', recorded, proves)

    def true(self, name, condition, details='', recorded='', proves=''):
        return self._line(bool(condition), name, details or ('yes' if condition else 'no'), recorded, proves)

    def equal(self, name, got, expected, recorded='', proves=''):
        return self._line(got == expected, name, f'got {got!r}, expected {expected!r}', recorded, proves)

    def controls(self, name, must_be_high, must_be_low, high_at_least, low_at_most, recorded='', proves=''):
        """A new measure's controls, before it is trusted: copies it must score HIGH and copies it must score LOW. In the textures work a
        shuffled copy of a picture scored about 0.99, a blurred copy 0.17 and another surface 0.09 (measured); a first version scored 0 even
        for alike pictures. must_be_high and must_be_low are {case: score}; the check passes only when both are given, every high case is at
        least high_at_least and every low case at most low_at_most."""
        bad = [f'{case} {fmt(score)} (needs at least {fmt(high_at_least)})' for case, score in must_be_high.items() if score is None or score < high_at_least]
        bad += [f'{case} {fmt(score)} (needs at most {fmt(low_at_most)})' for case, score in must_be_low.items() if score is None or score > low_at_most]
        if not must_be_high or not must_be_low:
            bad.append('a control is missing: give at least one case that must score high and one that must score low')
        text = ('controls hold: ' if not bad else 'controls FAIL: ') + '; '.join(
            bad or [f'high {", ".join(f"{c} {fmt(v)}" for c, v in must_be_high.items())}; low {", ".join(f"{c} {fmt(v)}" for c, v in must_be_low.items())}'])
        return self._line(not bad, name, text, recorded, proves)

    def note(self, text):
        """A note; a note that says a part was skipped (with its reason) is counted as a skipped part."""
        print(f'NOTE  {text}')
        self.notes.append(text)

    def skipped_parts(self):
        return [n for n in self.notes if 'skipped' in n.lower() or 'not run' in n.lower() or 'not checked' in n.lower()]

    def finish(self):
        total = self.passed + len(self.failed)
        skipped = self.skipped_parts()
        print(f'-- {self.title}: {self.passed} of {total} checks passed' + (f'; {len(skipped)} part(s) skipped' if skipped else '')
              + (f'; FAILED: {", ".join(self.failed)}' if self.failed else ''))
        _ENDED_CLEANLY[0] = not self.failed
        sys.exit(1 if self.failed else 0)


def skip(title, reason):
    print(f'== {title}\nSKIP  {reason}')
    _ENDED_CLEANLY[0] = True
    sys.exit(SKIPPED)


def fmt(value):
    if value is None:
        return 'nothing'
    if isinstance(value, float):
        return f'{value:.6g}'
    return str(value)
