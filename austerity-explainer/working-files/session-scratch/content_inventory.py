"""What this does: lists every file in the working folders whose contents are not yet anywhere in
the repository (matched by a fingerprint of the contents, so renamed copies count as present).
Use: python3 -I content_inventory.py REPO OUTPUT.json FOLDER [FOLDER ...]"""
import hashlib, json, os, sys

SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'mcp-env'}

def fingerprint(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def walk(root):
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = os.path.join(folder, name)
            if os.path.isfile(path) and not os.path.islink(path):
                yield path

repo, output, folders = sys.argv[1], sys.argv[2], sys.argv[3:]
in_repo = {}
for path in walk(repo):
    in_repo.setdefault(fingerprint(path), path)
missing = []
for root in folders:
    for path in walk(root):
        size = os.path.getsize(path)
        if size > 200 * 1024 * 1024:
            missing.append({'path': path, 'size': size, 'note': 'too big to fingerprint quickly'}); continue
        if fingerprint(path) not in in_repo:
            missing.append({'path': path, 'size': size})
json.dump(missing, open(output, 'w'), indent=1)
print(len(missing), 'files not in the repository,', round(sum(m['size'] for m in missing) / 1e6), 'MB')
