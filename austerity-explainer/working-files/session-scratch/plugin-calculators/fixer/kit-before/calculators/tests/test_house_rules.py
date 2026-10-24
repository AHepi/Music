"""What this does: checks the house rules every file in kit/calculators keeps, for every builder's calculator, not only
the core's: each Python file (and each test) opens with a plain note starting "What this does", and every one that can be
run from the command line answers --help (exit 0) within a minute. It also checks the page-side twin frame-geometry.js
opens with its note. A new calculator that forgets its note or its --help fails here.
Run: python3 kit/calculators/tests/test_house_rules.py
"""
import ast
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, TESTS  # noqa: E402

check = Checker('house rules: a plain note at the top and a --help')
files = sorted(glob.glob(os.path.join(CALCULATORS, '*.py'))) + sorted(glob.glob(os.path.join(TESTS, '*.py')))
no_note, no_help, helped = [], [], 0
for path in files:
    name = os.path.relpath(path, CALCULATORS)
    source = open(path).read()
    try:
        tree = ast.parse(source)
        note = ast.get_docstring(tree) or ''
    except SyntaxError as problem:
        check.true(f'{name} is valid Python', False, details=str(problem))
        continue
    if not note.strip().startswith('What this does'):
        no_note.append(name)
    runnable = "__name__ == '__main__'" in source or '__name__ == "__main__"' in source
    if runnable and os.path.dirname(path) == CALCULATORS:
        run = subprocess.run([sys.executable, '-I', '-B', path, '--help'], capture_output=True, text=True, timeout=60, cwd=CALCULATORS)
        if run.returncode != 0 or 'usage' not in (run.stdout + run.stderr).lower():
            no_help.append(f'{name} (exit {run.returncode})')
        else:
            helped += 1
check.true(f'every file in kit/calculators opens with a "What this does" note ({len(files)} files)', not no_note, details=', '.join(no_note) or 'all do')
check.true(f'every calculator that runs from the command line answers --help ({helped} answered)', not no_help, details=', '.join(no_help) or 'all do')
twin = os.path.join(os.path.dirname(CALCULATORS), 'paper-film', 'scenes', 'frame-geometry.js')
check.true('frame-geometry.js opens with its note', open(twin).read().startswith('// What this does'))
check.finish()
