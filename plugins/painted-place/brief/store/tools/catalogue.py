"""
What this file does: writes the store's catalogue into Store.md, between its two catalogue lines, from the items' own
descriptions: each part's CARD, each tool's TOOL and each material's 'store_what'. Run it after adding or changing
anything in the store, so the catalogue never disagrees with the code.

    python3 catalogue.py            (needs the bpy module)
    python3 catalogue.py --check    (prints what it would write and whether Store.md is up to date; changes nothing)
"""

import importlib.util
import os
import sys

import bpy

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import store  # noqa: E402

STORE_MD = os.path.join(store.STORE, 'Store.md')
START = '<!-- catalogue starts'
END = '<!-- catalogue ends -->'
NOT_TOOLS = ('store', 'card', 'catalogue')


def _cell(text):
    return str(text).replace('|', '/').replace('\n', ' ').strip()


def _options(options):
    if not options:
        return ''
    return '; '.join('`%s`: %s' % (key, value) for key, value in options.items())


def _size(size):
    try:
        return ' x '.join('%.2f' % float(v) for v in size) + ' m'
    except (TypeError, ValueError):
        return _cell(size)


def _card_link(folder, name, view=None):
    file_name = '%s - %s.png' % (name, view) if view else '%s.png' % name
    path = os.path.join(store.STORE, 'cards', folder, file_name)
    if not os.path.exists(path):
        return ''
    return '[card](<cards/%s/%s>)' % (folder, file_name)


def _tool_module(name):
    spec = importlib.util.spec_from_file_location('store_tool_' + name, os.path.join(TOOLS, name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parts_rows():
    rows = ['### Parts', '', 'Place one with `store.add_part(name, location=(x, y, z), turn=degrees, seed=n, option=value)`. '
            'The size is at the default options; the front faces −Y.', '',
            '| part | what it is | size (x, y, z) | options | reads from | card | came from | trap |', '|---|---|---|---|---|---|---|---|']
    for name in store.names('parts'):
        try:
            card = store.part_card(name)
        except Exception as problem:            # a part that cannot be read is listed with its problem, never hidden
            card = {'what': '(could not be read: %s)' % problem}
        rows.append('| `%s` | %s | %s | %s | %s | %s | %s | %s |' % (
            name, _cell(card.get('what', '')), _size(card.get('size_m', '')), _cell(_options(card.get('options'))),
            _cell(card.get('views', '')), _card_link('parts', name, 'three'), _cell(card.get('source', '')), _cell(card.get('trap', ''))))
    if len(rows) == 6:
        rows.append('| (none yet) | | | | | | | |')
    return rows


def tools_rows():
    rows = ['### Tools', '', 'Import a tool in your script (`import lay_walkway`) or run it from the command line; each answers `--help`. '
            'Each makes its thing only where you say.', '',
            '| tool | what it makes | how to call it | options | card | came from | trap |', '|---|---|---|---|---|---|---|']
    for name in store.names('tools'):
        if name in NOT_TOOLS:
            continue
        try:
            tool = getattr(_tool_module(name), 'TOOL', None)
        except Exception as problem:
            tool = {'what': '(could not be read: %s)' % problem}
        if not tool:
            continue
        rows.append('| `%s` | %s | `%s` | %s | %s | %s | %s |' % (
            name, _cell(tool.get('what', '')), _cell(tool.get('call', '')), _cell(_options(tool.get('options'))),
            _card_link('tools', name), _cell(tool.get('source', '')), _cell(tool.get('trap', ''))))
    return rows


def materials_rows():
    rows = ['### Materials', '', 'Use one with `store.use_material(obj, name)` or `store.material(name)`. '
            'SURFACE materials are photographs from the shelf, already darkened into the look; their real size is the photograph\'s.', '',
            '| material | what it is | real size | card |', '|---|---|---|---|']
    with bpy.data.libraries.load(store.MATERIALS_BLEND, link=False) as (source, target):
        target.materials = list(source.materials)
    for material in sorted(bpy.data.materials, key=lambda m: (not m.name.startswith('SURFACE'), not m.name.startswith('MADE'), m.name.lower())):
        if material.library is not None:
            continue
        what = material.get('store_what', '')
        size = material.get('store_size_m')
        file_name = material.name.replace(' • ', ' - ').replace('•', '-').replace('/', '-').strip()
        link = '[card](<cards/materials/%s.png>)' % file_name if os.path.exists(os.path.join(store.STORE, 'cards', 'materials', file_name + '.png')) else ''
        rows.append('| `%s` | %s | %s | %s |' % (material.name, _cell(what), _size(size) if size else '', link))
    return rows


def catalogue_text():
    lines = parts_rows() + [''] + tools_rows() + [''] + materials_rows()
    return '\n'.join(lines)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    text = catalogue_text()
    page = open(STORE_MD, encoding='utf-8').read()
    start = page.index(START)
    start_end = page.index('\n', start) + 1
    end = page.index(END)
    updated = page[:start_end] + text + '\n' + page[end:]
    if '--check' in sys.argv:
        print(text)
        print('\nStore.md is %s' % ('up to date' if updated == page else 'out of date: run catalogue.py'))
        return 0 if updated == page else 1
    open(STORE_MD, 'w', encoding='utf-8').write(updated)
    print('wrote the catalogue into', STORE_MD, '(%d parts, %d tools)' % (len(store.names('parts')), len([t for t in store.names('tools') if t not in NOT_TOOLS])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
