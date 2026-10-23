"""What this does: tests list_prop_lettering.py (every word written on a built prop, for the fact checker):
  1. made-up files: a prop script whose saved facts hold a "lettering" list (each word found, with its prop and line), a list item worked
     out only when the script runs (listed under "not_read", never silently dropped), a prop library index.json and a lettering-sizes.json;
  2. the kit's own prop scripts: the colliery name board's four lines are found at build_scripted_props.py line 669;
  3. a folder that is not there stops with exit 2.
Run: python3 kit/calculators/tests/test_list_prop_lettering.py
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, CALCULATORS, work_folder  # noqa: E402

TOOL = os.path.join(CALCULATORS, 'list_prop_lettering.py')
check = Checker('list_prop_lettering: every word written on a built prop')
work = work_folder('prop-lettering-test-')
script = os.path.join(work, 'build_shop_props.py')
open(script, 'w').write('''"""What this does: a made-up prop script."""
def shop_sign(library, words):
    library.save_prop('shop-sign', 'a painted shop sign', 'own work', 'CC0',
                      {'lettering': ['GROCER', 'EST. 1921'], 'texture': 'shop-sign 1024x256'})
    library.save_prop('price-card', 'a price card', 'own work', 'CC0', {'lettering': [words]})
''')
json.dump([{'file': 'newspaper.glb', 'lettering': ['THE DAILY HERALD', 'FRIDAY, APRIL 30, 1926']}, {'file': 'crate.glb'}],
          open(os.path.join(work, 'index.json'), 'w'), indent=1)
json.dump({'notice.png': {'words': 'LOCKED OUT', 'font': 'Ultra'}}, open(os.path.join(work, 'lettering-sizes.json'), 'w'), indent=1)
out = os.path.join(work, 'prop-lettering.json')
done = subprocess.run([sys.executable, '-I', '-B', TOOL, work, '--out', out], capture_output=True, text=True, timeout=120)
data = json.load(open(out)) if os.path.exists(out) else {'strings': [], 'not_read': []}
found = {(s['text'], s['prop']): s for s in data['strings']}
check.true('the prop script\'s "lettering" list is read, with its prop and the line of each word',
           found.get(('GROCER', 'shop-sign'), {}).get('line') == 4 and ('EST. 1921', 'shop-sign') in found, json.dumps(data['strings'])[:300])
check.true('the case that must not slip through: a word worked out only when the script runs is listed under "not_read" (with file and line), and said',
           any(n['expression'] == 'words' and n['line'] == 5 and n['prop'] == 'price-card' for n in data['not_read']) and 'LOOK' in done.stdout,
           json.dumps(data['not_read'])[:200])
check.true('a prop library\'s index.json is read (a dated newspaper masthead is a claim to check: 30 April 1926 was a Friday)',
           ('FRIDAY, APRIL 30, 1926', 'newspaper.glb') in found and found[('FRIDAY, APRIL 30, 1926', 'newspaper.glb')]['line'] is not None, str(sorted(found))[:200])
check.true('lettering-sizes.json\'s words are read', ('LOCKED OUT', 'notice.png') in found, str(sorted(found))[:200])
check.true('the file has the shape the fact checker reads: {"strings": [{"text", "prop", "file", "line"}]}',
           data['strings'] and all({'text', 'prop', 'file', 'line'} <= set(s) for s in data['strings']))

kit_out = os.path.join(work, 'kit-lettering.json')
done = subprocess.run([sys.executable, '-I', '-B', TOOL, '--out', kit_out], capture_output=True, text=True, timeout=300)
kit = json.load(open(kit_out)) if os.path.exists(kit_out) else {'strings': []}
board = [s for s in kit['strings'] if s['prop'] == 'colliery-name-board']
check.true('the kit\'s own colliery name board: its four lines are found at build_scripted_props.py line 669',
           len(board) == 4 and all(s['line'] == 669 and s['file'].endswith('build_scripted_props.py') for s in board), json.dumps(board)[:300])
done = subprocess.run([sys.executable, '-I', '-B', TOOL, os.path.join(work, 'no-such-folder'), '--out', os.path.join(work, 'x.json')], capture_output=True, text=True, timeout=60)
check.true('a folder that is not there stops with exit 2 and says so', done.returncode == 2 and 'is not there' in done.stderr, f'exit {done.returncode}: {done.stderr[:120]}')
check.finish()
