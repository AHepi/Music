"""What this does: runs every calculator test in this folder (each file named test_*.py), one Python process each, and
prints a plain summary: which passed, which failed (with the end of their output), which were skipped and why, how many
single checks passed, failed and were skipped, and how long it all took. It exits 1 if any test failed, so it can guard
a change. Every builder's test is picked up just by being named test_SOMETHING.py here.

A test passes by exiting 0, fails by exiting with anything else, and is skipped by exiting 77 (for example when a tool
it needs, such as node, is missing). Pytest is not needed: each test is a plain Python file. A test that needs files the
plugin does not ship (the project's large pictures, recordings, Blender scenes, or its working files) skips those parts
with the reason; see tests/checks.py for the settings that point to them (FILM_PROJECT, FILM_KIT, FILM_WORKING_FILES,
BLENDER).

Use:
    python3 kit/calculators/tests/run_all.py                 run them all
    python3 kit/calculators/tests/run_all.py --show          also print every test's full output
    python3 kit/calculators/tests/run_all.py frame settings  run only tests whose names contain these words
    python3 kit/calculators/tests/run_all.py --list          list the tests without running them
    --timeout SECONDS  stop a test that runs longer (default 600)
"""
import argparse
import glob
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SKIPPED = 77


def main():
    parser = argparse.ArgumentParser(description='Runs every tests/test_*.py of the calculators and prints a plain summary.')
    parser.add_argument('words', nargs='*', help='run only tests whose file names contain one of these words')
    parser.add_argument('--show', action='store_true', help='print each test\'s full output')
    parser.add_argument('--list', action='store_true', help='list the tests and stop')
    parser.add_argument('--timeout', type=float, default=600, help='seconds before a test is stopped (default 600)')
    args = parser.parse_args()
    tests = sorted(glob.glob(os.path.join(HERE, 'test_*.py')))
    if args.words:
        tests = [t for t in tests if any(w in os.path.basename(t) for w in args.words)]
    if args.list or not tests:
        print('\n'.join(os.path.basename(t) for t in tests) or 'no tests found')
        return 0 if tests or args.list else 1
    results = []
    began = time.time()
    for test in tests:
        name = os.path.basename(test)
        started = time.time()
        try:
            run = subprocess.run([sys.executable, '-I', '-B', test], capture_output=True, text=True, timeout=args.timeout, cwd=HERE)
            code, output = run.returncode, run.stdout + run.stderr
        except subprocess.TimeoutExpired as stopped:
            partial = stopped.stdout or ''
            if isinstance(partial, bytes):
                partial = partial.decode(errors='replace')
            code, output = 'timeout', partial + f'\nFAIL  stopped after {args.timeout:.0f} s'
        seconds = time.time() - started
        verdict = 'passed' if code == 0 else 'skipped' if code == SKIPPED else 'FAILED'
        results.append((name, verdict, seconds, output))
        counted = [line for line in output.splitlines() if line.startswith('-- ')]
        print(f'{verdict:7s}  {name}  ({seconds:.1f} s)' + (f'  {counted[-1][3:]}' if counted else ''))
        if args.show or verdict == 'FAILED':
            shown = output if args.show else '\n'.join([l for l in output.splitlines() if l.startswith(('FAIL', '==', '--', 'Traceback', '  File', 'SKIP'))
                                                        or 'Error' in l][-40:])
            print('    ' + shown.replace('\n', '\n    '))
        elif verdict == 'skipped':
            reason = [l for l in output.splitlines() if l.startswith('SKIP')]
            print('    ' + (reason[-1] if reason else 'skipped'))
    failed = [r for r in results if r[1] == 'FAILED']
    skipped = [r for r in results if r[1] == 'skipped']
    checks_passed = checks_failed = parts_skipped = 0
    skip_reasons = []
    for name, verdict, seconds, output in results:
        tally = [l for l in output.splitlines() if l.startswith('-- ')]
        found = re.search(r'(\d+) of (\d+) checks passed', tally[-1]) if tally else None
        if found:
            checks_passed += int(found.group(1))
            checks_failed += int(found.group(2)) - int(found.group(1))
        elif verdict == 'FAILED':
            checks_failed += 1   # a test that stopped before its tally counts as one failed check
        parts = re.search(r'(\d+) part\(s\) skipped', tally[-1]) if tally else None
        if parts:
            parts_skipped += int(parts.group(1))
            skip_reasons += [f'{name}: {l[6:]}' for l in output.splitlines() if l.startswith('NOTE') and
                             ('skipped' in l.lower() or 'not run' in l.lower() or 'not checked' in l.lower())]
        if verdict == 'skipped':
            reason = [l for l in output.splitlines() if l.startswith('SKIP')]
            skip_reasons.append(f'{name}: the whole test ({reason[-1][6:] if reason else "skipped"})')
    took = time.time() - began
    print(f'\n{len(results)} test files: {len(results) - len(failed) - len(skipped)} passed, {len(failed)} failed, {len(skipped)} skipped.')
    print(f'Checks: {checks_passed} passed, {checks_failed} failed, {parts_skipped + len(skipped)} skipped '
          f'({parts_skipped} part(s) of tests and {len(skipped)} whole test file(s), each with its reason below).')
    print(f'Time: {int(took // 60)} min {took % 60:.0f} s.')
    if skip_reasons:
        print('Skipped, and why:')
        for reason in skip_reasons:
            print(f'  - {reason}')
    if failed:
        print('Failed: ' + ', '.join(r[0] for r in failed))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
