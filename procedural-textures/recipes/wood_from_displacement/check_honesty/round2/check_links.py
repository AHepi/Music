# What this does (plain words): the honesty checker's test that every picture, link and file path named in the two 08 guides (and in the builder's claims) exists on disk.
# It reads each guide, collects (a) pictures and links written as ![..](path) or [..](path), and (b) names in `backticks` that look like paths (they contain a slash or end in a file ending),
# and then checks that each one exists, relative to the recipe folder. Names with ".." between numbers (for example outputs/main_seed1..3) are expanded; names with * are matched as patterns.
# Use: python3 -I check_links.py
import glob
import json
import os
import re

BASE = 'proc-work/recipes/wood_from_displacement'
PROC = os.path.dirname(os.path.dirname(BASE))
GUIDES = ['08 Recipe - wood from your displacement and colour maps - how it is made.md',
          '08 Lessons - wood from your displacement and colour maps - what carries over to other surfaces.md']
ENDINGS = ('.py', '.json', '.jpg', '.png', '.md', '.sh', '.log', '.txt')
out = {}
for guide in GUIDES:
    text = open(os.path.join(BASE, guide)).read()
    pics = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)
    links = [l for l in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', text)]
    ticks = re.findall(r'`([^`\n]+)`', text)
    cands = []
    for t in ticks:
        t = t.strip()
        if ' ' in t and not t.endswith(ENDINGS):
            continue
        first = t.split(' ')[0]
        if ('/' in first or first.endswith(ENDINGS)) and not first.startswith(('-', '{', '[', '"', '--')) and 'blender' not in first and 'python' not in first:
            cands.append(first.rstrip(',.;:)'))
    missing, found = [], []
    for kind, items in (('picture', pics), ('link', links), ('named', cands)):
        for item in sorted(set(items)):
            if item.startswith(('http://', 'https://', '#')):
                continue
            variants = [item]
            m = re.search(r'(.*?)(\d)\.\.(\d)(.*)', item)
            if m:
                variants = [f'{m.group(1)}{i}{m.group(4)}' for i in range(int(m.group(2)), int(m.group(3)) + 1)]
            for v in variants:
                paths = [os.path.join(BASE, v), os.path.join(PROC, v), os.path.join(BASE, 'recipe', v), os.path.join(BASE, 'tools', v), os.path.join(BASE, 'scores', v)]
                ok = any(os.path.exists(p) for p in paths) or any(glob.glob(p) for p in paths if '*' in p)
                (found if ok else missing).append((kind, v))
    out[guide] = {'pictures': len(set(pics)), 'links': len(set(links)), 'named_paths': len(set(cands)), 'found': len(found), 'missing': missing}
print(json.dumps(out, indent=1))
