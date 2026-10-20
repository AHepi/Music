# What this does: counts the verdicts in the tool table of guide "07 Reuse - which tools work on which surfaces" (the table between the two
# TOOL TABLE comment lines). For every surface it counts how many tools got each label: as is, settings, new layout, new layer, copy + edit, not useful.
# A cell is counted under the FIRST label it starts with (a note in brackets after the label is ignored).
# It prints the counts as a markdown table. With --write it puts that table into the guide in place of the line COUNTS_PLACEHOLDER
# (or replaces the table it wrote earlier, which sits between the two TOOL COUNTS comment lines).
# Usage: python3 -I count_tool_verdicts.py            (print only)
#        python3 -I count_tool_verdicts.py --write    (print and write into the guide)
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GUIDE = os.path.abspath(os.path.join(HERE, '..', '..', '07 Reuse - which tools work on which surfaces.md'))
SURFACES = ['brick', 'wood', 'metal', 'mud', 'gravel']
LABELS = ['as is', 'settings', 'new layout', 'new layer', 'copy + edit', 'not useful']

START = '<!-- TOOL TABLE START -->'
END = '<!-- TOOL TABLE END -->'
COUNTS_START = '<!-- TOOL COUNTS START -->'
COUNTS_END = '<!-- TOOL COUNTS END -->'


def label_of(cell):
    text = cell.strip().lower()
    for label in LABELS:
        if text.startswith(label):
            return label
    return None


def main():
    with open(GUIDE, encoding='utf-8') as handle:
        text = handle.read()
    table = text.split(START)[1].split(END)[0]
    counts = {name: {label: 0 for label in LABELS} for name in SURFACES}
    rows, problems = 0, []
    for line in table.splitlines():
        if not line.startswith('|') or line.startswith('|---') or line.startswith('| tool '):
            continue
        # group header rows ("| **A. ...** | | | ...") have only their first cell filled; skip them
        if all(not part.strip() for part in line.split('|')[2:]):
            continue
        cells = [cell for cell in line.strip().strip('|').split(' | ')]
        if len(cells) != 8:
            problems.append('row with %d cells: %s' % (len(cells), line[:80]))
            continue
        rows += 1
        for name, cell in zip(SURFACES, cells[2:7]):
            label = label_of(cell)
            if label is None:
                problems.append('no label in %s cell of %s: %s' % (name, cells[0][:40], cell[:40]))
            else:
                counts[name][label] += 1
    lines = ['How the %d tools in the table fit each surface (counted by `cookbook/checks/reuse_overview/count_tool_verdicts.py`; a cell is counted under'
             % rows,
             'its first label; guides, layers, tests and scripts are counted alike, so read it as "how much of the shelf is usable", not "how close the tile looks"):',
             '',
             '| | brick | wood | metal | mud | gravel |',
             '|---|---|---|---|---|---|']
    for label in LABELS:
        lines.append('| %s | %s |' % (label, ' | '.join(str(counts[name][label]) for name in SURFACES)))
    lines.append('| **fits now (as is or settings)** | %s |' % ' | '.join('**%d of %d**' % (counts[name]['as is'] + counts[name]['settings'], rows) for name in SURFACES))
    result = '\n'.join(lines)
    print(result)
    for problem in problems:
        print('PROBLEM:', problem)
    if '--write' in sys.argv:
        block = COUNTS_START + '\n' + result + '\n' + COUNTS_END
        if 'COUNTS_PLACEHOLDER' in text:
            text = text.replace('COUNTS_PLACEHOLDER', block)
        else:
            head = text.split(COUNTS_START)[0]
            tail = text.split(COUNTS_END)[1]
            text = head + block + tail
        with open(GUIDE, 'w', encoding='utf-8') as handle:
            handle.write(text)
        print('written into', GUIDE)


main()
