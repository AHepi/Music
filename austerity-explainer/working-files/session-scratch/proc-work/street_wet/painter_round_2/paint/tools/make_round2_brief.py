"""What this file does (plain words): builds the painter brief for the FRONT PAINTING of round 2 from the first test's brief
(painter_test/briefs/brief_new_wet.txt, read only), changing as little as possible. Every change is listed with its reason.
It writes, into paint/briefs/: brief_round2.txt (the brief exactly as it is sent, after the line of equals signs),
brief_first_test_and_round2_side_by_side.html (red = taken out, green = put in), brief_round2_changes_list.md, brief_round2_pair.json.
Nothing is sent to any painter by this file.  Run: python3 -I tools/make_round2_brief.py
"""
import difflib, html, json, os, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIRST = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_test/briefs/brief_new_wet.txt'
raw = open(FIRST).read()
old = raw.split('==========\n', 1)[1].strip()

# (label, reason, old text, new text); each old text must occur exactly once
changes = [
 ('lamp glass', 'the person asked: the gas lamp glass glows warm amber (the first painting made it pale yellow-white)',
  'Every gas lamp has warm amber glass with a small bright gas mantle inside.',
  'Every gas lamp has warm amber glass with a small bright gas mantle inside, and the gas lamp glass glows warm amber.'),
 ('sky', 'the first painting added heavy pale-white brush-stroke clouds to a plain dark sky although the never-add list banned bright clouds',
  'The road, pavement and walls are cool blue-grey dusk, and the brick is weathered and greyed by coal smoke without getting any darker. ',
  'The road, pavement and walls are cool blue-grey dusk, and the brick is weathered and greyed by coal smoke without getting any darker. '
  'The sky is dark grey-blue cloud with soft edges, like image 2\'s darker skies; no pale, white or bright clouds anywhere; keep the sky as dark as image 1. '),
 ('streaks', 'the first painting made the far lamp reflection streaks on the road much stronger than the plate had them',
  'Add no wet look where image 1 has none. ',
  'Add no wet look where image 1 has none. Do not make the lamp reflection streaks on the road stronger or longer than in image 1. '),
 ('joint lines', 'keep the thin dark joint lines under every light (the person asked that the stonework stays visible)',
  'Add no wet look where image 1 has none. Do not make',
  'Add no wet look where image 1 has none. Keep the thin dark lines between the setts and between the flags everywhere, even where the road shines. Do not make'),
 ('rubbish kept', 'the plate now has small rubbish in the gutters and along the walls; the painter must keep it and invent no writing or modern litter',
  'Keep: the rusty drum',
  'Keep the small rubbish where image 1 has it (cinders, coal dust, ash, paper scraps, straw, leaves, mud along the gutters and the foot of the walls, round the drum and sacks); add no writing, print or modern litter. Keep: the rusty drum'),
 ('never add: litter', 'the first brief said "no ... litter in the road or on the pavement", which would now fight the sentence that keeps the plate\'s small rubbish',
  'extra props (no coal tub, rails, barrel, crates or litter in the road or on the pavement)',
  'extra props (no coal tub, rails, barrel or crates in the road or on the pavement)'),
 ('never add: clouds', 'say the same thing in the never-add list as in the sky sentence',
  'a moon, stars or bright clouds;',
  'a moon, stars or any pale, white or bright clouds;'),
 ('halo sentence', 'the lamp glass is now asked to glow amber, so say that this glow is not the banned halo',
  '(the wet road\'s reflections of the lights are not halos: keep those as image 1 has them)',
  '(the wet road\'s reflections of the lights, and the warm amber of the lamp glass itself, are not halos: keep those as image 1 has them)'),
]
new = old
for label, why, a, b in changes:
    # the 'joint lines' edit works on the text made by the 'streaks' edit
    assert new.count(a) == 1, f'change "{label}": old text found {new.count(a)} times'
    new = new.replace(a, b)
# order check: streaks sentence must come after the joint-lines sentence's place; print for a human read
assert 'matte' not in new.lower()

os.makedirs(os.path.join(HERE, 'briefs'), exist_ok=True)
NOTE = ('NOTE (plain words): this file is the painter brief for the FRONT PAINTING of round 2 (the wet street, 21 October 2026), exactly as it is sent: one paragraph, after the line of equals signs.\n'
        'Made by tools/make_round2_brief.py from the first test\'s brief (painter_test/briefs/brief_new_wet.txt) with eight small changes, listed in brief_round2_changes_list.md.\n'
        '==========\n')
open(os.path.join(HERE, 'briefs/brief_round2.txt'), 'w').write(NOTE + new + '\n')
json.dump({'first_test': old, 'round2': new}, open(os.path.join(HERE, 'briefs/brief_round2_pair.json'), 'w'), indent=1)

def tokens(s): return re.findall(r'\S+\s*', s)
a, b = tokens(old), tokens(new)
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
left, right = [], []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    ta, tb = html.escape(''.join(a[i1:i2])), html.escape(''.join(b[j1:j2]))
    if tag == 'equal': left.append(ta); right.append(tb)
    else:
        if ta: left.append(f'<del>{ta}</del>')
        if tb: right.append(f'<ins>{tb}</ins>')
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painter brief first test and round 2</title>
<!-- NOTE (plain words): the first test's painter brief and the round 2 brief side by side. Red struck-through = taken out of the first brief.
Green = put into the round 2 brief. Made by tools/make_round2_brief.py. Nothing here is sent anywhere. -->
<style>body{{font:16px/1.5 system-ui,sans-serif;margin:16px;background:#fff;color:#111}}
@media (prefers-color-scheme:dark){{body{{background:#161616;color:#ddd}}}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media(max-width:800px){{.cols{{grid-template-columns:1fr}}}}
h1{{font-size:20px}}h2{{font-size:16px}}p{{white-space:pre-wrap}}
del{{background:#fbb;color:#600;text-decoration:line-through}}ins{{background:#bfb;color:#030;text-decoration:none}}
@media (prefers-color-scheme:dark){{del{{background:#5a2020;color:#fcc}}ins{{background:#1d4a1d;color:#cfc}}}}</style></head><body>
<h1>Painter brief: first test and round 2 (front painting)</h1>
<p>Red = taken out, green = put in.</p>
<div class="cols"><div><h2>FIRST TEST (20 October)</h2><p>{''.join(left)}</p></div><div><h2>ROUND 2 (this one)</h2><p>{''.join(right)}</p></div></div></body></html>'''
open(os.path.join(HERE, 'briefs/brief_first_test_and_round2_side_by_side.html'), 'w').write(page)

md = ['<!-- NOTE (plain words): every change from the first test\'s brief to the round 2 front-painting brief, with the reason. -->',
      '# Changes from the first test\'s brief to the round 2 brief\n']
for label, why, a_, b_ in changes:
    md.append(f'## {label}\n\nWhy: {why}\n\nOLD: {a_}\n\nNEW: {b_}\n')
open(os.path.join(HERE, 'briefs/brief_round2_changes_list.md'), 'w').write('\n'.join(md))
print(len(old.split()), 'words first test;', len(new.split()), 'words round 2')
print(new)
