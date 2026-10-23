"""What this does: lists every word written on a built prop, so the fact checker can check them like any other claim. A name on a prop is a
claim: an invented name (a newspaper's masthead, a shop, a firm) must be made up on purpose and checked against real ones, a real name must
be used correctly, and dates and weekdays must be right (30 April 1926 was a Friday). The words live in three places, all read here:
  - the prop scripts: a "lettering" list in the facts a script saves with its prop (for example the colliery name board in
    paper-film/blender/pit-village/props/build_scripted_props.py: {'lettering': ['ABBOTSCLOUGH', 'COLLIERY', ...]});
  - a prop library's index.json (save_prop writes each prop's "lettering" list there);
  - lettering-sizes.json (the lettering pictures' "words", written when the pictures are painted by code).
A list item a script only works out when it runs (a variable, an f-string) cannot be read here: it goes under "not_read" with its file
and line, so nobody thinks it was checked; give the prop library's index.json, which holds the words as they came out.

Use:
    python3 list_prop_lettering.py --out prop-lettering.json [FOLDERS_OR_FILES ...]
With no folder it reads the kit's paper-film/blender. It writes
    {"strings": [{"text", "prop", "file", "line", "from"}], "not_read": [{"expression", "prop", "file", "line"}], ...}
and prints a plain summary. Exit 0 (an empty list is not an error, but it is said plainly), 2 when a folder is not there.
"""
import argparse
import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from calculator_output import InputProblem, run_main  # noqa: E402

SKIP_FOLDERS = ('node_modules', '.git', '__pycache__', 'out')


def source_text(node, source):
    try:
        return ast.get_source_segment(source, node) or ast.dump(node)
    except Exception:                       # noqa: BLE001  (a segment that cannot be cut is shown as Python's own dump)
        return ast.dump(node)


def prop_of(dict_node, parents):
    """The prop a "lettering" list belongs to: the first text argument of the call that holds the dict (save_prop('colliery-name-board', ...)),
    else the name of the function it sits in."""
    node = parents.get(dict_node)
    while node is not None:
        if isinstance(node, ast.Call):
            for argument in node.args:
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    return argument.value
                if isinstance(argument, ast.JoinedStr):
                    return '(worked out when the script runs)'
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return f'(the function {node.name})'
        node = parents.get(node)
    return '(the script)'


def from_script(path):
    source = open(path, encoding='utf-8', errors='replace').read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return [], [{'expression': '(the file is not valid Python)', 'prop': None, 'file': path, 'line': None}]
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    strings, not_read = [], []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant) and key.value == 'lettering'):
                continue
            prop = prop_of(node, parents)
            items = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
            for item in items:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    strings.append({'text': item.value, 'prop': prop, 'file': path, 'line': item.lineno, 'from': 'prop script'})
                else:
                    not_read.append({'expression': source_text(item, source), 'prop': prop, 'file': path, 'line': item.lineno})
    return strings, not_read


def line_of(lines, text, start=0):
    """The first line (1-based) at or after start that holds the text as JSON writes it; None when it is not found."""
    needle = json.dumps(text)[1:-1]
    for number in range(start, len(lines)):
        if needle in lines[number]:
            return number + 1
    return None


def from_index(path):
    lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
    data = json.load(open(path, encoding='utf-8'))
    entries = data if isinstance(data, list) else data.get('props', []) if isinstance(data, dict) else []
    strings, cursor = [], 0
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('lettering'), list):
            continue
        for text in entry['lettering']:
            if isinstance(text, str):
                line = line_of(lines, text, cursor)
                cursor = (line or cursor + 1) - 1
                strings.append({'text': text, 'prop': entry.get('file') or entry.get('name'), 'file': path, 'line': line, 'from': 'prop index'})
    return strings


def from_lettering_sizes(path):
    lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
    data = json.load(open(path, encoding='utf-8'))
    strings = []
    for picture, facts in (data.items() if isinstance(data, dict) else []):
        words = facts.get('words') if isinstance(facts, dict) else None
        for text in (words if isinstance(words, list) else [words] if isinstance(words, str) else []):
            strings.append({'text': text, 'prop': picture, 'file': path, 'line': line_of(lines, text, max(0, (line_of(lines, picture) or 1) - 1)),
                            'from': 'lettering sizes'})
    return strings


def gather(places):
    strings, not_read, read = [], [], []
    files = []
    for place in places:
        if os.path.isfile(place):
            files.append(place)
            continue
        if not os.path.isdir(place):
            raise InputProblem(f'{place} is not there (give the folders that hold the prop scripts, index.json or lettering-sizes.json).')
        for folder, folders, names in os.walk(place):
            folders[:] = sorted(f for f in folders if f not in SKIP_FOLDERS)
            files += [os.path.join(folder, n) for n in sorted(names)]
    for path in files:
        name = os.path.basename(path)
        try:
            if name.endswith('.py'):
                found, missing = from_script(path)
                if not found and not missing:
                    continue
                strings += found
                not_read += missing
            elif name == 'index.json':
                found = from_index(path)
                if not found:
                    continue
                strings += found
            elif name == 'lettering-sizes.json':
                strings += from_lettering_sizes(path)
            else:
                continue
            read.append(path)
        except (ValueError, OSError) as problem:
            not_read.append({'expression': f'(could not be read: {problem})', 'prop': None, 'file': path, 'line': None})
    return strings, not_read, read


def main(argv=None):
    parser = argparse.ArgumentParser(description='Lists every word written on a built prop (prop scripts\' "lettering" lists, prop index.json, '
                                                 'lettering-sizes.json) for the fact checker.')
    parser.add_argument('places', nargs='*', help='folders or files to read (default: the kit\'s paper-film/blender)')
    parser.add_argument('--out', required=True, help='where to write the list (JSON: {"strings": [{"text", "prop", "file", "line"}]})')
    args = parser.parse_args(argv)
    places = [os.path.abspath(p) for p in (args.places or [os.path.join(KIT, 'paper-film', 'blender')])]
    strings, not_read, read = gather(places)
    result = {'about': 'Every word written on a built prop, for the fact checker (check-facts skill, verify-facts workflow): an invented name must be '
                       'made up on purpose and checked against real ones; a real name must be used correctly; dates and weekdays must be right.',
              'made_from': places, 'files_read': read, 'strings': strings, 'not_read': not_read,
              'count': len(strings), 'different_texts': sorted({s['text'] for s in strings})}
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as handle:
        json.dump(result, handle, indent=1, ensure_ascii=False)
    print(f'list_prop_lettering: {len(strings)} string(s) written on props ({len(result["different_texts"])} different) from {len(read)} file(s); written to {args.out}.')
    for item in strings[:12]:
        print(f'  "{item["text"]}"  on {item["prop"]}  ({os.path.basename(item["file"])} line {item["line"]})')
    if len(strings) > 12:
        print(f'  and {len(strings) - 12} more (all in {args.out})')
    if not_read:
        print(f'LOOK {len(not_read)} lettering item(s) are only worked out when a script runs (a variable or an f-string), so they are not in the list: '
              + '; '.join(f'{os.path.basename(n["file"])} line {n["line"]}: {n["expression"][:40]}' for n in not_read[:5])
              + '. Give the prop library\'s index.json too: it holds the words as they came out.')
    if not strings:
        print('LOOK no lettering found: no prop script saves a "lettering" list there, and no index.json or lettering-sizes.json holds one.')
    return 0


if __name__ == '__main__':
    sys.exit(run_main(main, 'list_prop_lettering'))
