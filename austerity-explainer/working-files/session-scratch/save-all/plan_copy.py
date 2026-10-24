# What this does: turns the list of unsaved files into a copy plan (where each one goes in the
# repository), leaving out other people's publications and installed software, and lists what is left out.
import json, os
here = os.path.dirname(__file__)
S = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
DEST = 'austerity-explainer/working-files'
missing = json.load(open(os.path.join(here, 'missing.json')))
THIRD_PARTY = [S + '/mcpsrc/', S + '/boe/', S + '/boepdf/', S + '/nber/', S + '/boe.txt', S + '/bell.txt']
REPLACED = {S + '/sam3d/download/objects-bundle.zip'}    # saved unpacked instead (same files)
MAP = [(S + '/held-back/working-files/', DEST + '/chapter-2-held-back/'),
       (S + '/held-back/', DEST + '/chapter-2-held-back/'),
       (S + '/save-all/', DEST + '/session-scratch/save-all/'),
       (S + '/', DEST + '/session-scratch/'),
       ('/home/user/work/chapter-2/', DEST + '/chapter-2-work-folder/'),
       ('/home/user/work/paper-pop-up-film-kit/', DEST + '/film-kit-live-leftovers/'),
       ('/home/user/work/plugin-test/', DEST + '/plugin-install-tests/plugin-test/'),
       ('/home/user/work/setup-test/', DEST + '/plugin-install-tests/setup-test/')]
plan, left_out = [], []
for path, size, ext in missing:
    if any(path.startswith(t) for t in THIRD_PARTY): left_out.append((path, size, 'someone else\'s publication or software')); continue
    if path in REPLACED: left_out.append((path, size, 'zip saved unpacked instead')); continue
    for source, target in MAP:
        if path.startswith(source): plan.append((path, target + path[len(source):], size)); break
    else: left_out.append((path, size, 'no place found'))
json.dump({'plan': plan, 'left_out': left_out}, open(os.path.join(here, 'copy-plan.json'), 'w'), indent=0)
print('to copy', len(plan), round(sum(p[2] for p in plan) / 1e6, 1), 'MB; left out', len(left_out), round(sum(p[1] for p in left_out) / 1e6, 1), 'MB')
import collections
print(collections.Counter(r for _, _, r in left_out))
print('largest:', sorted(((round(s / 1e6, 1), d) for _, d, s in plan), reverse=True)[:5])
