"""What this does: tests two things explainer-film-setup prints since the lessons round (23 October):
  1. the "Blender 5.2 probe" block (with Blender on this machine): which way of setting a Geometry Nodes modifier input works in the
     installed Blender, and how a collection's light-linking entries pair with its objects (kit/place-kit/probe_blender.py);
  2. the film kit's files changed after the plugin's last copy (the newest date in a heading of kit/kit-sync-notes.md): a made-up film kit
     with one file dated after that copy and one before must list the first only; a film kit that is not there is said plainly.
The setup copies the kit into a scratch folder (about 10 MB, a few seconds); a stand-in node_modules/three keeps it from running npm.
Run: BLENDER=/path/to/blender python3 kit/calculators/tests/test_setup_probe.py   (part 1 is skipped without Blender)
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, PLUGIN, blender_program  # noqa: E402

check = Checker('explainer-film-setup: the Blender 5.2 probe and the film kit files newer than the last copy')
SETUP = os.path.join(PLUGIN, 'bin', 'explainer-film-setup')
work = tempfile.mkdtemp(prefix='setup-probe-test-')
try:
    target = os.path.join(work, 'film-kit-copy')
    os.makedirs(os.path.join(target, 'paper-film', 'node_modules', 'three'))
    film_kit = os.path.join(work, 'made-up-film-kit')
    os.makedirs(os.path.join(film_kit, 'paper-film', 'stage'))
    newer, older = os.path.join(film_kit, 'paper-film', 'stage', 'changed-later.js'), os.path.join(film_kit, 'paper-film', 'stage', 'copied-already.js')
    open(newer, 'w').write('// changed after the last copy\n')
    open(older, 'w').write('// copied already\n')
    later = time.time() + 30 * 86400
    os.utime(newer, (later, later))
    os.utime(older, (time.time() - 60 * 86400, time.time() - 60 * 86400))
    environment = {k: v for k, v in os.environ.items() if k not in ('RUNPOD_API_KEY', 'RUNPOD_ENDPOINT_ID', 'RENDER_SETTINGS_FILE')}
    environment['FILM_KIT'] = film_kit
    blender = blender_program()
    if blender:
        environment['BLENDER'] = blender
    else:
        environment.pop('BLENDER', None)
    done = subprocess.run(['bash', SETUP, target], capture_output=True, text=True, timeout=900, env=environment, cwd=work)
    out = done.stdout
    check.true('the setup runs to the end', done.returncode == 0 and 'next: read the make-explainer-film skill' in out, f'exit {done.returncode}: {done.stderr[-300:]}')
    listing = [line for line in out.splitlines() if line.startswith('film kit (')]
    check.true('the film kit\'s file changed after the last copy is listed', listing and '1 file(s) changed after the plugin\'s last copy' in listing[0]
               and 'paper-film/stage/changed-later.js' in out, listing[0] if listing else out[-300:])
    check.true('the case that must not be listed: a file older than the last copy', 'copied-already.js' not in out)
    environment['FILM_KIT'] = os.path.join(work, 'no-such-film-kit')
    environment['FILM_PROJECT'] = os.path.join(work, 'no-such-project')
    again = subprocess.run(['bash', SETUP, target], capture_output=True, text=True, timeout=900, env=environment, cwd=work)
    check.true('a film kit that is not on this machine is said plainly', 'film kit: not on this machine' in again.stdout, [l for l in again.stdout.splitlines() if 'film kit' in l][:1])
    if blender:
        block = out[out.find('Blender 5.2 probe'):].splitlines()[:3] if 'Blender 5.2 probe' in out else []
        check.true('with Blender, the setup prints a "Blender 5.2 probe" block', len(block) == 3 and block[1].strip().startswith('Geometry Nodes inputs:')
                   and block[2].strip().startswith('light linking:'), '\n'.join(block))
        check.true('...which names the way that works here (Blender 5.2: mod.properties.inputs.<identifier>.value) and the light-linking pairing',
                   'mod.properties.inputs.' in out and 'works' in out and 'pair them with collection.objects in the same order' in out, '\n'.join(block))
    else:
        check.note('part 1 skipped: Blender was not found (set BLENDER), so the probe block was not tried')
finally:
    shutil.rmtree(work, ignore_errors=True)
check.finish()
