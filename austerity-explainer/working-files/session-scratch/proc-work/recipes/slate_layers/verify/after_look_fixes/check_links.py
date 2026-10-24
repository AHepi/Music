# What this does (plain words): reads the two 05 guides and the folder map, finds every picture link (![..](path)) and every name in `back quotes`
# that looks like a file or folder path, and checks whether it exists (looked for relative to the slate_layers folder, then to the proc-work folder).
# Names with a star or a placeholder (OUT, <layer>, ...) are listed separately. Use: python3 -I check_links.py
import glob, os, re, sys, json
SL = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/slate_layers'
PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
docs = ['05 Recipe - slate in layers - how it is made.md', '05 Lessons - slate in layers - what carries over to other surfaces.md', 'README - folder map.md']
EXT = r'(?:md|py|json|png|jpg|jpeg|txt|log|sh|csv|blend)'
missing, placeholders, ok = {}, {}, {}
for doc in docs:
    text = open(os.path.join(SL, doc)).read()
    found = set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text))
    for tok in re.findall(r'`([^`\n]+)`', text):
        t = tok.strip()
        if ' ' in t and not re.search(r'\.' + EXT + r'$', t) and not t.endswith('/'):
            continue
        if re.fullmatch(r'[\w./\-+ ()]+', t) and (re.search(r'\.' + EXT + r'$', t) or t.endswith('/') or '/' in t) and not t.startswith('--'):
            found.add(t)
    for t in sorted(found):
        if re.search(r'[*<>{}]|\bOUT\b|OUT_FOLDER|RECIPE|COLOUR|HEIGHT|\.\.\.', t) or t.startswith('http'):
            placeholders.setdefault(doc, []).append(t); continue
        cands = [os.path.join(SL, t), os.path.join(PROC, t), os.path.join(SL, 'outputs', 'default', t), os.path.join(SL, 'look_fixes', t), os.path.join(SL, 'tests', t), os.path.join(SL, 'variations', t),
                 os.path.join(SL, 'integration', t), os.path.join(SL, 'ladder', t), os.path.join(SL, 'area', t), os.path.join(SL, 'verify', t), os.path.join(SL, 'recipe', t)]
        hit = [c for c in cands if os.path.exists(c)]
        (ok if hit else missing).setdefault(doc, []).append(t)
for doc in docs:
    print('=====', doc, ' ok:', len(ok.get(doc, [])), ' missing:', len(missing.get(doc, [])), ' placeholder/skipped:', len(placeholders.get(doc, [])))
    for t in missing.get(doc, []):
        print('   MISSING', t)
json.dump({'missing': missing, 'placeholders': placeholders}, open(SL + '/verify/after_look_fixes/link_check_result.json', 'w'), indent=1)
