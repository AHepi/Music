# What this file does: lists every file made in this project that is not yet in the repository
# (second full save, 24 October 2026), decides for each one whether it goes in, where it goes,
# and whether it is moved or copied, and writes the plan to plan.json. It leaves out videos,
# audio, other people's work, installed software, the person's uploaded textures, the Astra
# add-on, files over GitHub's size limit, and any text file that looks like it holds a secret.
import collections
import hashlib
import json
import os
import re
import subprocess

SCRATCH = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad'
WORKFLOW_SCRIPTS = '/root/.claude/projects/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/workflows/scripts'
REPO = '/home/user/Music'
DEST = 'austerity-explainer/working-files'
HERE = os.path.dirname(os.path.abspath(__file__))
LIMIT_BYTES = 95 * 1024 * 1024

ROOTS = [
    (SCRATCH + '/', DEST + '/session-scratch/', 'scratch'),
    ('/home/user/work/chapter-2/', DEST + '/chapter-2-work-folder/', 'live'),
    ('/home/user/work/paper-pop-up-film-kit/', DEST + '/film-kit-live-leftovers/', 'live'),
    ('/home/user/work/plugin-test/', DEST + '/plugin-install-tests/plugin-test/', 'live'),
    ('/home/user/work/setup-test/', DEST + '/plugin-install-tests/setup-test/', 'live'),
    (WORKFLOW_SCRIPTS + '/', DEST + '/session-workflow-scripts/', 'live'),
]
VIDEO = {'.mp4', '.webm', '.mov', '.mkv', '.avi', '.m4v', '.mpg', '.mpeg', '.y4m'}
AUDIO = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus', '.aif', '.aiff', '.wma'}
INSTALLED = {'.pyc', '.so', '.dll', '.dylib', '.whl', '.wasm', '.pack', '.idx', '.ttf', '.otf', '.woff', '.woff2'}
HEAVY = {'.png', '.jpg', '.jpeg', '.webp', '.exr', '.hdr', '.tif', '.tiff', '.bmp', '.npy', '.npz', '.glb', '.gltf',
         '.blend', '.blend1', '.obj', '.fbx', '.ply', '.spz', '.raw', '.bin', '.gif', '.pkl'}
SKIP_DIR_NAMES = {'node_modules', '.git', '__pycache__', 'bvenv', '.venv', 'venv', 'site-packages', '.cache', '.npm'}
NEVER = [SCRATCH + '/astra-upload', SCRATCH + '/astra-work', SCRATCH + '/proc-work/reference']
THIRD_PARTY = [SCRATCH + '/mcpsrc/', SCRATCH + '/boe/', SCRATCH + '/boepdf/', SCRATCH + '/nber/', SCRATCH + '/boe.txt',
               SCRATCH + '/bell.txt', SCRATCH + '/runpod-skills/', SCRATCH + '/uploads/', SCRATCH + '/downloads/',
               SCRATCH + '/skills_install/staging/', SCRATCH + '/webcache/poly_tex.html']
LIVE_SCRATCH_FOLDERS = [SCRATCH + '/runpod/', SCRATCH + '/village-compare/', SCRATCH + '/village-blind-judging/',
                        SCRATCH + '/village-control/pictures/', SCRATCH + '/village-test/rebuild/',
                        SCRATCH + '/village-test/verify/', SCRATCH + '/save-all-2/']
OPUS = SCRATCH + '/village-control-opus/'
OPUS_NOW = [OPUS + 'pictures_pass1/', OPUS + 'feedback_for_pass2.md', OPUS + 'pass1_report.md']
POLY_HAVEN_NAME = re.compile(r'_(diff|nor_gl|nor_dx|rough|disp|arm|ao|spec|metal|bump|col|height)_(1k|2k|4k|8k)\b|polyhaven|poly_haven', re.I)


def blob_id(path):
    size = os.path.getsize(path)
    digest = hashlib.sha1(b'blob %d\0' % size)
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


repo_blobs = set(line.split()[1] for line in subprocess.run(
    ['git', '-C', REPO, 'ls-files', '-s'], capture_output=True, text=True).stdout.splitlines())
reference_blobs = set()
for base, dirs, files in os.walk(SCRATCH + '/proc-work/reference'):
    for name in files:
        reference_blobs.add(blob_id(os.path.join(base, name)))

plan, left_out = [], []
for root, target, kind in ROOTS:
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES]
        for name in files:
            path = os.path.join(base, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            size = os.path.getsize(path)
            ext = os.path.splitext(name)[1].lower()
            reason = None
            if any(path.startswith(n) for n in NEVER) or 'astra' in path.lower():
                reason = 'never saved (your uploads or the Astra add-on)'
            elif path.startswith(OPUS) and not any(path.startswith(o) for o in OPUS_NOW):
                reason = 'Opus second pass still running; saved when it ends'
            elif any(path.startswith(t) for t in THIRD_PARTY) or name.startswith('webfetch-'):
                reason = "someone else's publication or software"
            elif POLY_HAVEN_NAME.search(path):
                reason = 'downloaded scan from Poly Haven (someone else\'s work)'
            elif ext in VIDEO:
                reason = 'video'
            elif ext in AUDIO:
                reason = 'audio'
            elif ext in INSTALLED:
                reason = 'installed software, fonts or caches'
            elif ext == '.zip':
                reason = 'zip (packed copy)'
            elif size > LIMIT_BYTES:
                reason = "over GitHub's 100 MB file limit"
            if reason:
                left_out.append((path, size, reason))
                continue
            bid = blob_id(path)
            if bid in reference_blobs:
                left_out.append((path, size, 'copy of your uploaded textures'))
                continue
            if bid in repo_blobs:
                continue
            repo_blobs.add(bid)
            action = 'copy'
            if kind == 'scratch' and ext in HEAVY and not any(path.startswith(l) for l in LIVE_SCRATCH_FOLDERS) \
                    and not path.startswith(OPUS):
                action = 'move'
            plan.append({'source': path, 'target': target + path[len(root):], 'size': size, 'ext': ext, 'action': action})

json.dump({'plan': plan, 'left_out': left_out}, open(os.path.join(HERE, 'plan.json'), 'w'), indent=0)
total = sum(p['size'] for p in plan)
print('to save', len(plan), 'files', round(total / 1048576), 'MB; moved', round(sum(p['size'] for p in plan if p['action'] == 'move') / 1048576),
      'MB; copied', round(sum(p['size'] for p in plan if p['action'] == 'copy') / 1048576), 'MB')
by_reason = collections.Counter()
by_reason_size = collections.Counter()
for path, size, reason in left_out:
    by_reason[reason] += 1
    by_reason_size[reason] += size
print('left out:')
for reason, count in by_reason.most_common():
    print(f'  {count:6d} files {by_reason_size[reason] / 1048576:8.1f} MB  {reason}')
by_folder = collections.Counter()
for p in plan:
    parts = p['target'].split('/')
    by_folder['/'.join(parts[2:4])] += p['size']
print('to save, by folder (MB):')
for folder, size in by_folder.most_common(40):
    print(f'  {size / 1048576:8.1f}  {folder}')
by_ext = collections.Counter()
for p in plan:
    by_ext[p['ext']] += p['size']
print('by kind (MB):', [(e, round(s / 1048576, 1)) for e, s in by_ext.most_common(20)])
