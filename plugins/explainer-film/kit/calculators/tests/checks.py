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
"""
import os
import sys

TESTS = os.path.dirname(os.path.abspath(__file__))
CALCULATORS = os.path.dirname(TESTS)
FIXTURES = os.path.join(TESTS, 'fixtures')
if CALCULATORS not in sys.path:
    sys.path.insert(0, CALCULATORS)

SKIPPED = 77


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
        print(f'NOTE  {text}')
        self.notes.append(text)

    def finish(self):
        total = self.passed + len(self.failed)
        print(f'-- {self.title}: {self.passed} of {total} checks passed' + (f'; FAILED: {", ".join(self.failed)}' if self.failed else ''))
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
