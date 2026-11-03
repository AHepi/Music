"""
What this file does: checks the store's one rule, that nothing in it places itself: no part or tool reads the camera,
surveys the scene, or looks objects up by name to decide where things go; tools work only on what the caller passes.
It reads the code itself (the parsed Python), not its comments. It also checks that Store.md's catalogue is up to date
with the parts', tools' and materials' own descriptions.
    python3 tests/test_store_rules.py
"""
import ast
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import STORE, TOOLS, check  # noqa: E402

ALLOWED_CAMERA = {'card.py', 'catalogue.py', 'store.py', 'finish.py'}   # the card pictures need a camera of their own


def offences(path):
    tree = ast.parse(open(path, encoding='utf-8').read(), filename=path)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == 'camera':
            found.append('reads a camera (line %d)' % node.lineno)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = [a.name for a in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            if any(m and ('survey' in m or 'apply_by_role' in m or m.startswith('lay_details')) for m in modules):
                found.append('imports the old dressing (line %d)' % node.lineno)
        if isinstance(node, ast.Attribute) and node.attr in ('objects',) and isinstance(node.value, ast.Attribute) and node.value.attr == 'scene':
            found.append('walks every object in the scene (line %d)' % node.lineno)
    return found


def main():
    checked = 0
    for folder in (TOOLS, os.path.join(STORE, 'parts', 'src')):
        for name in sorted(os.listdir(folder)):
            if not name.endswith('.py') or name in ALLOWED_CAMERA:
                continue
            problems = offences(os.path.join(folder, name))
            check(not problems, '%s: %s' % (name, '; '.join(problems)))
            checked += 1
    print('PASS no part or tool reads the camera, surveys the scene or walks its objects (%d files)' % checked)
    result = subprocess.run([sys.executable, os.path.join(TOOLS, 'catalogue.py'), '--check'], capture_output=True, text=True, timeout=600)
    check(result.returncode == 0, "Store.md's catalogue is out of date: run python3 store/tools/catalogue.py\n" + result.stdout[-400:] + result.stderr[-400:])
    print("PASS Store.md's catalogue matches the store")
    print('PASS test_store_rules')


if __name__ == '__main__':
    main()
