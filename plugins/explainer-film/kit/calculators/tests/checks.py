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
"""
import os
import shutil
import sys

TESTS = os.path.dirname(os.path.abspath(__file__))
CALCULATORS = os.path.dirname(TESTS)
FIXTURES = os.path.join(TESTS, 'fixtures')
KIT = os.path.dirname(CALCULATORS)
PLUGIN = os.path.dirname(KIT)
if CALCULATORS not in sys.path:
    sys.path.insert(0, CALCULATORS)

SKIPPED = 77


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
        sys.exit(1 if self.failed else 0)


def skip(title, reason):
    print(f'== {title}\nSKIP  {reason}')
    sys.exit(SKIPPED)


def fmt(value):
    if value is None:
        return 'nothing'
    if isinstance(value, float):
        return f'{value:.6g}'
    return str(value)
