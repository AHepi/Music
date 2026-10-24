# What this does: lists every file made in this project that is not yet in the repository,
# leaving out videos, audio and installed software, and sums them by folder and kind.
import os, sys, hashlib, json, collections
VIDEO = {'.mp4', '.webm', '.mov', '.mkv', '.avi', '.m4v', '.mpg', '.mpeg', '.ts', '.y4m'}
AUDIO = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus', '.aif', '.aiff', '.wma'}
SKIP_DIRS = {'node_modules', '.git', '__pycache__', 'bvenv', '.venv', 'venv', 'site-packages', '.cache', '.npm'}
REPO = '/home/user/Music'
ROOTS = sys.argv[1:]
def file_hash(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''): h.update(block)
    return h.hexdigest()
repo_hashes = set()
for base, dirs, files in os.walk(REPO):
    dirs[:] = [d for d in dirs if d != '.git']
    for name in files:
        p = os.path.join(base, name)
        if os.path.isfile(p) and not os.path.islink(p): repo_hashes.add(file_hash(p))
missing, skipped = [], collections.Counter()
for root in ROOTS:
    for base, dirs, files in os.walk(root):
        kept = []
        for d in dirs:
            if d in SKIP_DIRS: skipped['dir:' + d] += 1
            else: kept.append(d)
        dirs[:] = kept
        for name in files:
            p = os.path.join(base, name)
            if os.path.islink(p) or not os.path.isfile(p): continue
            ext = os.path.splitext(name)[1].lower()
            size = os.path.getsize(p)
            if ext in VIDEO: skipped['video'] += size; continue
            if ext in AUDIO: skipped['audio'] += size; continue
            if ext == '.pyc': continue
            if file_hash(p) in repo_hashes: skipped['already in repo'] += size; continue
            missing.append((p, size, ext))
json.dump(missing, open(os.path.join(os.path.dirname(__file__), 'missing.json'), 'w'))
by_root = collections.Counter(); by_ext = collections.Counter(); count_ext = collections.Counter()
for p, size, ext in missing:
    rel = p
    for r in ROOTS:
        if p.startswith(r): rel = r.rstrip('/').split('/')[-1] + '/' + os.path.relpath(p, r).split('/')[0]
    by_root[rel] += size; by_ext[ext] += size; count_ext[ext] += 1
print('missing files', len(missing), 'total MB', round(sum(s for _, s, _ in missing) / 1e6, 1))
print('skipped', {k: (round(v / 1e6, 1) if isinstance(v, int) and v > 1000 else v) for k, v in skipped.items()})
print('over 50 MB:', [(p, round(s / 1e6)) for p, s, _ in missing if s > 50e6][:40])
print('by kind (MB, count):', [(e, round(s / 1e6, 1), count_ext[e]) for e, s in by_ext.most_common(25)])
print('by folder (MB):')
for k, v in by_root.most_common(60): print(f'  {v/1e6:8.1f}  {k}')
