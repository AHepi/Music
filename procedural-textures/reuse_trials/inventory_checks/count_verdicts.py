# What this does (plain words): reads the tool tables of section 4 of "00 Inventory - which tools fit which surface.md" (the rows that start with "|" and
# have eight cells: tool, what it does, brick, wood, metal, mud, gravel, evidence), checks that every surface cell starts with one of the six verdicts,
# counts the verdicts per surface and prints a table, and writes the rows as inventory_rows.json next to this file (for the structured answer).
# Plain Python; reads one text file, writes one JSON file.
# Use: python3 -I count_verdicts.py
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
INVENTORY = os.path.join(HERE, '..', '00 Inventory - which tools fit which surface.md')
VERDICTS = ['as is', 'settings only', 'needs a new layout', 'needs a new layer', 'needs code changes', 'not useful']
SURFACES = ['brick', 'wood', 'metal', 'mud', 'gravel']

text = open(INVENTORY, encoding='utf-8').read()
section = text.split('## 4. Every tool')[1].split('## 5. ')[0]
kind = ''
rows, problems = [], []
for line in section.splitlines():
    if line.startswith('### 4'):
        kind = line[4:].strip()
    if not line.startswith('|') or line.startswith('|---') or line.startswith('| tool |'):
        continue
    cells = [c.strip() for c in line.strip().strip('|').split('|')]
    if len(cells) != 8:
        problems.append(('wrong number of cells', len(cells), line[:80]))
        continue
    row = {'name': cells[0].replace('`', ''), 'kind': kind, 'what_it_does': cells[1], 'evidence': cells[7]}
    for surface, cell in zip(SURFACES, cells[2:7]):
        plain = re.sub(r'\*\*', '', cell).strip()
        verdict = next((v for v in VERDICTS if plain.lower().startswith(v)), None)
        if verdict is None:
            problems.append(('no verdict', surface, cells[0], plain[:60]))
        row[surface] = plain
        row[surface + '_verdict'] = verdict
    rows.append(row)

counts = {s: {v: 0 for v in VERDICTS} for s in SURFACES}
for row in rows:
    for s in SURFACES:
        if row[s + '_verdict']:
            counts[s][row[s + '_verdict']] += 1
print('rows:', len(rows), ' problems:', problems)
print('| | ' + ' | '.join(SURFACES) + ' |')
for v in VERDICTS:
    print('| ' + v + ' | ' + ' | '.join(str(counts[s][v]) for s in SURFACES) + ' |')
print('| fits now (as is or settings only) | ' + ' | '.join(f"{counts[s]['as is'] + counts[s]['settings only']} of {len(rows)}" for s in SURFACES) + ' |')
json.dump({'rows': rows, 'counts': counts}, open(os.path.join(HERE, 'inventory_rows.json'), 'w'), indent=1)
