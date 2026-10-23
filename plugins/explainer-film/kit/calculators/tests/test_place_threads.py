"""What this does: tests the Blender thread limit (lessons round, 23 October): with the environment variable EXPLAINER_FILM_BLENDER_THREADS=N set,
every Blender run the place kit starts gets -t N, so several helpers on one computer do not starve each other (the coal mine's six builders each
ran blender -t 2); unset, the command is exactly as before.
  1. place_command.blender_command and the variations runner's local command: unset gives the old command; 2 adds -t 2 right after -b; a value
     that is not a whole number of 1 or more is ignored with a LOOK line (the case that must not slip through).
  2. The real launcher, started with a stand-in Blender that writes down how it was started: -t 2 reaches the Blender command line.
  3. With Blender on this machine (BLENDER), Blender itself accepts -t 2 in that place (a one-line script exits 0); skipped without Blender.
Run: python3 kit/calculators/tests/test_place_threads.py
"""
import contextlib
import io
import json
import os
import stat
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, blender_program, work_folder  # noqa: E402

PLACE_KIT = os.path.join(KIT, 'place-kit')
sys.path.insert(0, PLACE_KIT)
import place_command  # noqa: E402
from place_kit import cli  # noqa: E402
from place_kit.variations import runner  # noqa: E402

check = Checker('place kit: the Blender thread limit (EXPLAINER_FILM_BLENDER_THREADS)')
VARIABLE = 'EXPLAINER_FILM_BLENDER_THREADS'
saved = os.environ.pop(VARIABLE, None)
try:
    old = place_command.blender_command('blender', '/tmp/scene.blend', 'audit', ['--out', 'a.json'])
    check.equal('unset: the command is as it always was', old[:5], ['blender', '-b', '--disable-autoexec', '--python-exit-code', '1'])
    check.true('unset: no -t anywhere', '-t' not in old and '-t' not in runner.local_command('blender', 'scene.blend', 'job.json'))
    os.environ[VARIABLE] = '2'
    limited = place_command.blender_command('blender', '/tmp/scene.blend', 'audit', ['--out', 'a.json'])
    check.equal('set to 2: -t 2 comes right after -b', limited[:4], ['blender', '-b', '-t', '2'])
    check.true('set to 2: the rest of the command is unchanged', limited[:2] + limited[4:] == old)
    local = runner.local_command('blender', 'scene.blend', 'job.json')
    check.true('set to 2: the variations runner\'s own Blender command gets -t 2 too', local[local.index('-b') + 1:local.index('-b') + 3] == ['-t', '2'], ' '.join(local[:8]))
    for wrong in ('two', '0', '-1', '1.5'):
        os.environ[VARIABLE] = wrong
        said = io.StringIO()
        with contextlib.redirect_stderr(said):
            arguments = cli.blender_thread_arguments()
        check.true(f'the case that must not slip through: "{wrong}" is ignored with a LOOK line', arguments == [] and 'LOOK' in said.getvalue(), said.getvalue().strip())

    # 2. the real launcher with a stand-in Blender that writes down its own command line
    work = work_folder('place-threads-test-')
    record = os.path.join(work, 'started-with.json')
    stand_in = os.path.join(work, 'blender')
    with open(stand_in, 'w') as handle:
        handle.write('#!/usr/bin/env python3\n# What this does: a stand-in Blender that writes down how it was started, then exits 0.\n'
                     'import json, os, sys\njson.dump(sys.argv[1:], open(os.environ["THREADS_TEST_RECORD"], "w"))\n')
    os.chmod(stand_in, os.stat(stand_in).st_mode | stat.S_IEXEC)
    scene = os.path.join(work, 'scene.blend')
    open(scene, 'wb').write(b'a stand-in scene file')
    environment = dict(os.environ, THREADS_TEST_RECORD=record, PLACE_NO_XVFB='1')
    for value, expected in (('2', True), ('', False)):
        environment[VARIABLE] = value
        done = subprocess.run([sys.executable, '-I', '-B', os.path.join(PLACE_KIT, 'place_command.py'), 'fingerprint', '--scene', scene, '--blender', stand_in],
                              capture_output=True, text=True, timeout=60, env=environment)
        started = json.load(open(record)) if os.path.exists(record) else []
        if os.path.exists(record):
            os.remove(record)
        has = started[:3] == ['-b', '-t', '2']
        check.true(f'the launcher with {VARIABLE}={value or "(unset)"}: -t 2 {"reaches" if expected else "does not reach"} Blender',
                   done.returncode == 0 and has == expected, f'exit {done.returncode}; started with {" ".join(started[:6])}')

    # 3. Blender itself accepts -t 2 where the launcher puts it
    blender = blender_program()
    if blender:
        os.environ[VARIABLE] = '2'
        command = [blender, '-b'] + cli.blender_thread_arguments() + ['--disable-autoexec', '--python-exit-code', '1', '--python-expr', 'import bpy; print("THREADS-OK")']
        done = subprocess.run(command, capture_output=True, text=True, timeout=300)
        check.true('Blender accepts -b -t 2 --disable-autoexec ... and runs the script', done.returncode == 0 and 'THREADS-OK' in done.stdout, f'exit {done.returncode}')
    else:
        check.note('part 3 skipped: Blender was not found (set BLENDER)')
finally:
    os.environ.pop(VARIABLE, None)
    if saved is not None:
        os.environ[VARIABLE] = saved
check.finish()
