"""What this does: checks that every file a kit's JavaScript imports, and every local module a kit's Python
script imports through sys.path, exists in that same kit (so a copied scene or tool doesn't lean on a file
the copy left behind). Static imports (import ... from '...'), literal dynamic imports (import('...')) and
literal /paper-film/... or /examples/... fetch addresses in JS; for Python, `import NAME` / `from NAME import`
where NAME.py sits in a folder the script adds to sys.path or in its own folder.
Bare package names (three, playwright-core, node:...) are skipped; template-string imports with ${...} are
listed as "not checked".

Use: python3 -I check_imports.py KIT_FOLDER
Exit 1 if anything is missing.
"""
import os
import re
import sys

kit = os.path.abspath(sys.argv[1])
missing, checked, skipped = [], 0, []
js_files = []
for folder, dirs, files in os.walk(kit):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '__pycache__', 'calculators')]
    js_files += [os.path.join(folder, f) for f in files if f.endswith(('.js', '.mjs'))]

static = re.compile(r'''(?:^|\n)\s*(?:import|export)\s[^'"]*?\sfrom\s+['"]([^'"]+)['"]''')
side_effect = re.compile(r'''(?:^|\n)\s*import\s+['"]([^'"]+)['"]''')
dynamic = re.compile(r'''import\(\s*(['"`])([^'"`]+)\1\s*\)''')
for path in sorted(js_files):
    text = open(path, encoding='utf-8').read()
    targets = static.findall(text) + side_effect.findall(text) + [m[1] for m in dynamic.findall(text)]
    for target in targets:
        if '${' in target:
            skipped.append(f'{os.path.relpath(path, kit)}: {target}')
            continue
        if not (target.startswith('.') or target.startswith('/')):
            continue   # a package (three, playwright-core) or node: built-in
        resolved = os.path.join(kit, target.lstrip('/')) if target.startswith('/') else os.path.normpath(os.path.join(os.path.dirname(path), target))
        checked += 1
        if not os.path.exists(resolved):
            missing.append(f'{os.path.relpath(path, kit)} imports {target} (missing)')

# Python: local modules found through sys.path.insert(...) or the script's own folder
py_files = []
for folder, dirs, files in os.walk(kit):
    dirs[:] = [d for d in dirs if d not in ('node_modules', '__pycache__', 'calculators')]
    py_files += [os.path.join(folder, f) for f in files if f.endswith('.py')]
for path in sorted(py_files):
    text = open(path, encoding='utf-8').read()
    here = os.path.dirname(path)
    folders = [here]
    for parts in re.findall(r"sys\.path\.insert\(0,\s*os\.path\.join\(([^\n]*)\)\)", text):
        pieces = re.findall(r"'([^']+)'", parts)
        if 'dirname(os.path.abspath(__file__))' in parts or 'HERE' in parts:
            folders.append(os.path.normpath(os.path.join(here, *pieces)))
    names = set(re.findall(r'^\s*import\s+([A-Za-z_][A-Za-z0-9_]*)', text, re.M)) | set(re.findall(r'^\s*from\s+([A-Za-z_][A-Za-z0-9_]*)\s+import', text, re.M))
    for name in sorted(names):
        candidates = [os.path.join(f, name + '.py') for f in folders]
        local_anywhere = any(os.path.exists(os.path.join(dp, name + '.py')) for dp, _, _ in os.walk(os.path.join(kit, 'paper-film')))
        if any(os.path.exists(c) for c in candidates):
            checked += 1
        elif local_anywhere:
            missing.append(f'{os.path.relpath(path, kit)} imports {name}, which is in the kit but not on its path')

print(f'checked {checked} local imports in {len(js_files)} JS and {len(py_files)} Python files; missing: {len(missing)}')
for line in missing:
    print('  MISSING', line)
for line in skipped:
    print('  not checked (built at run time):', line)
sys.exit(1 if missing else 0)
