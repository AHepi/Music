# What this does (plain words): the honesty checker's own copy of integration/score_colour.sh in Python. It scores the colour picture(s) given on the
# command line against the slate reference with lib/texture_compare.py, borrowing height and normal from outputs/default exactly as the project's
# script does (only the COLOUR group means anything), but working in a temporary folder inside verify/after_look_fixes/.
# Use: python3 -I rescore_colour_only.py COLOUR1.png [COLOUR2.png ...]   -> prints one line per picture: name, colour group, feature-size part.
import json, os, shutil, subprocess, sys, tempfile
PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
SL = PROC + '/recipes/slate_layers'
HERE = SL + '/verify/after_look_fixes'
for path in sys.argv[1:]:
    d = tempfile.mkdtemp(dir=HERE)
    shutil.copy(path, d + '/colour.png')
    shutil.copy(SL + '/outputs/default/height.png', d + '/height.png')
    shutil.copy(SL + '/outputs/default/normal.png', d + '/normal.png')
    subprocess.run(['python3', '-I', PROC + '/lib/texture_compare.py', 'slate', d, '--json', d + '/score.json'], capture_output=True)
    s = json.load(open(d + '/score.json'))
    shutil.rmtree(d)
    print(os.path.basename(path), 'colour group', s['groups']['colour'], 'colour_scale', s['scores']['colour_scale'], flush=True)
