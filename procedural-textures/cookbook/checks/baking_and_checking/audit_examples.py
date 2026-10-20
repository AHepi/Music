# What this does: runs lib/description_audit.py (the check that a description is a list of meaningful numbers, not a picture in disguise) on
# real description files from the builds and on three small made-up files, and saves every result to audit_examples.json:
#   1. slate S1 (layout + stamps, a real procedural description) at the 8 KB limit;
#   2. slate L fine (a traced description) at the 64 KB limit and at the 512 KB limit;
#   3. a made-up "picture in disguise": a 100 x 100 grid of grey values (should be refused);
#   4. a made-up flat list of 5000 numbers (should be refused);
#   5. a made-up list of 100 polygon outlines of DIFFERENT lengths (6 to 78 numbers), the first five long: the false alarm three builds reported.
# Plain Python. Use: python3 -I audit_examples.py
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
AUDIT = os.path.join(PROC, 'lib', 'description_audit.py')
MADE_UP = os.path.join(HERE, 'audit_made_up')
os.makedirs(MADE_UP, exist_ok=True)
generator = random.Random(1)
made_up_files = {
    'grid_100x100.json': {'format': 'made up', 'grey': [[generator.randint(0, 255) for _ in range(100)] for _ in range(100)]},
    'flat_list_5000.json': {'format': 'made up', 'values': [generator.randint(0, 255) for _ in range(5000)]},
    'hundred_outlines.json': {'format': 'made up', 'patches': [[generator.randint(0, 9) for _ in range(70 + 2 * index if index < 5 else 6 + (index * 7) % 60)] for index in range(100)]},
}
for name, data in made_up_files.items():
    with open(os.path.join(MADE_UP, name), 'w') as handle:
        json.dump(data, handle)
cases = [
    ('slate S1 layout + stamps, limit 8 KB', os.path.join(PROC, 'recipes', 'slate', 'description', 'S1_layout_stamps.json'), 8),
    ('slate L traced fine, limit 64 KB', os.path.join(PROC, 'recipes', 'slate', 'description', 'L_trace_fine.json'), 64),
    ('slate L traced fine, limit 512 KB', os.path.join(PROC, 'recipes', 'slate', 'description', 'L_trace_fine.json'), 512),
    ('made up: a 100 x 100 grid of grey values', os.path.join(MADE_UP, 'grid_100x100.json'), 64),
    ('made up: a flat list of 5000 numbers', os.path.join(MADE_UP, 'flat_list_5000.json'), 64),
    ('made up: 100 polygon outlines of 6 to 78 numbers, first five long', os.path.join(MADE_UP, 'hundred_outlines.json'), 64),
]
results = {}
for label, path, limit in cases:
    run = subprocess.run([sys.executable, '-I', AUDIT, path, '--limit-kilobytes', str(limit)], capture_output=True, text=True)
    report = json.loads(run.stdout)
    report['file'] = os.path.relpath(path, PROC)
    report['exit_code'] = run.returncode
    report['verdict'] = 'passed' if run.returncode == 0 else 'refused'
    results[label] = report
    print(label, '->', report['verdict'], report['bytes'], 'bytes', report['problems'])
with open(os.path.join(HERE, 'audit_examples.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
