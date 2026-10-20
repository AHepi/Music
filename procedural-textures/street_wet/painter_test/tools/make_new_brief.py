"""What this file does (plain words): builds the NEW painter brief for the wet street from the OLD brief, so that every
difference is a deliberate, listed change. The old brief is the one recorded for the notice-corner painting
(film-kit/assets/models/pit-village/notice-corner-paintings.json), because the lockout painting's own brief was
never saved. It writes: briefs/brief_old.txt, briefs/brief_new_wet.txt, briefs/brief_old_and_new_side_by_side.html
and briefs/brief_changes_list.md.  Run: python3 -I tools/make_new_brief.py   (nothing is sent to any painter by this file)
"""
import difflib, html, json, os, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/notice-corner-paintings.json'
old = json.load(open(REPO))['paintings'][0]['prompt']

# each change: (label, kind, old text, new text); kind WET = the point of the test, PROPS = needed because this plate's
# props differ from the notice corner's, so the painter is not told to keep things that are not there
changes = [
 ('finish', 'WET',
  'simplified painterly textures on brick, stone, slate and wood, and matte painted finish.',
  'simplified painterly textures on brick, stone, slate and wood, and painted wet shine and painted reflections.'),
 ('wet street', 'WET',
  'It is a pit-village street at dusk on 1 May 1926.',
  'It is a pit-village street at dusk on 1 May 1926, wet after rain.'),
 ('props kept', 'PROPS',
  'the empty old wooden kitchen chair with worn, grubby pale paint, darker than the notice, its back to the board, with a small hurricane lantern on its seat (amber glass, a small flame inside); the wooden pail at the chair\'s feet, with no handle; the dark timber notice board on its two posts with the cream notice (plain paper with grey rows of print-like marks, no readable letters); the black gas lamp standing free on its own post above the board; the brick terraces, the colliery building, its tall chimney and winding wheels; and far up on the left the small two-wheeled handcart seen from behind, the coal sacks and the dustbins.',
  'the dark timber notice board on its two posts with the cream notice (plain paper with grey rows of print-like marks, no readable letters); the small wooden pail at the foot of the board, with no handle; the black gas lamps on their posts down both sides of the street; the brick terraces and stone cottages, the colliery building, its tall chimney and winding wheels; the wooden handcart on the left with its big spoked wheel and the spade leaning on it; the pile of coal sacks in the road; the small heap of black coal lumps on the road; the dustbin at the right edge; and the ladder on the left pavement.'),
 ('gutter', 'WET',
  'The gutter beside the kerb is a shallow, smooth stone channel with no steps, ridges or grating.',
  'The gutter beside the kerb is a shallow, smooth stone channel with no steps, ridges or grating, with the rainwater lying in it as image 1 shows.'),
 ('colour and wet paragraph', 'WET',
  'The road, pavement and walls are cool blue-grey dusk, and the brick is weathered and greyed by coal smoke without getting any darker. Warm light stays only where it already is: round the drum, on the board, on the chair seat, at the lamps and in the few lit windows.',
  'The road, pavement and walls are cool blue-grey dusk, and the brick is weathered and greyed by coal smoke without getting any darker. '
  'The street is wet after rain, and image 1 shows exactly where. Keep all of that wet look exactly where image 1 has it, at the same size and the same strength, painted in the hand of image 2 (painted reflections made of flat shapes of colour with a few ink lines and visible brush strokes; not a photograph, not a mirror): the wet sheen on the setts of the road and on the pavement flags; the lamp, lit-window and brazier reflections lying on the road as soft painted streaks and pools of warm light; the soft reflections of the handcart and the sacks on the road under them; the puddles in the gutters and in the low spots of the road, each one a smooth painted sheet of cool grey-blue with the houses, lamps and lit windows mirrored upside down in it; the thin dark wet lines between the setts and between the flags; and the darker, damper foot of the walls. The road is darker and glossier than a dry road, and never looks dry. Add no wet look where image 1 has none. '
  'Warm light stays only where it already is: round the drum, on the board, at the lamps, in the few lit windows, and in their reflections on the wet road where image 1 shows them.'),
 ('thin parts', 'PROPS',
  '(the lantern\'s wire handle, the lamp arms, the gate bars, the chair rungs, the winding rope)',
  '(the lamp arms, the gate bars, the cart\'s rails and spokes, the spade\'s handle, the winding rope)'),
 ('touching pairs', 'PROPS',
  'the drum\'s side and the board\'s left post, the gas-lamp head and the wall pipe and bracket beside it, the far lamps and the house downpipes, the chair back across the bottom of the notice; the winding rope never joins the lamp.',
  'the drum\'s side and the board\'s left post, each gas-lamp head and the wall pipe and bracket beside it, the far lamps and the house downpipes, the spade and the cart\'s wheel; the winding rope never joins the lamp.'),
 ('never add halos', 'WET',
  'glows, halos or light rays round any light, the notice or the drum;',
  'glows, halos or light rays round any light, the notice or the drum (the wet road\'s reflections of the lights are not halos: keep those as image 1 has them);'),
 ('never add puddles', 'WET',
  'puddles or reflections; a moon,',
  'a moon,'),
]
new = old
for label, kind, a, b in changes:
    assert new.count(a) == 1, f'change "{label}": the old text was not found exactly once'
    new = new.replace(a, b)
assert 'matte' not in new.lower() and 'puddles or reflections' not in new

os.makedirs(os.path.join(HERE, 'briefs'), exist_ok=True)
NOTE_TXT = ('NOTE (plain words): this file is the painter brief %s, exactly as it is sent, one paragraph, after the line of equals signs.\n'
            'Made by tools/make_new_brief.py. The old brief is the notice corner painting\'s brief (the lockout painting\'s own brief was not saved).\n'
            '==========\n')
open(os.path.join(HERE, 'briefs/brief_old.txt'), 'w').write(NOTE_TXT % 'OLD (dry street)' + old + '\n')
open(os.path.join(HERE, 'briefs/brief_new_wet.txt'), 'w').write(NOTE_TXT % 'NEW (wet street)' + new + '\n')
json.dump({'old': old, 'new': new}, open(os.path.join(HERE, 'briefs/brief_pair.json'), 'w'), indent=1)

# side by side, word level, differences marked
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
<title>Painter brief old and new</title>
<!-- NOTE (plain words): the old painter brief (dry street) and the new one (wet street) side by side. Red struck-through = taken out of the old brief.
Green = put into the new brief. Made by tools/make_new_brief.py. Nothing here is sent anywhere. -->
<style>body{{font:16px/1.5 system-ui,sans-serif;margin:16px;background:#fff;color:#111}}
@media (prefers-color-scheme:dark){{body{{background:#161616;color:#ddd}}}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media(max-width:800px){{.cols{{grid-template-columns:1fr}}}}
h1{{font-size:20px}}h2{{font-size:16px}}p{{white-space:pre-wrap}}
del{{background:#fbb;color:#600;text-decoration:line-through}}ins{{background:#bfb;color:#030;text-decoration:none}}
@media (prefers-color-scheme:dark){{del{{background:#5a2020;color:#fcc}}ins{{background:#1d4a1d;color:#cfc}}}}</style></head><body>
<h1>Painter brief: old (dry street) and new (wet street)</h1>
<p>Old = the notice corner painting's brief (the lockout painting's own brief was not saved). Red = removed, green = added.</p>
<div class="cols"><div><h2>OLD</h2><p>{''.join(left)}</p></div><div><h2>NEW</h2><p>{''.join(right)}</p></div></div></body></html>'''
open(os.path.join(HERE, 'briefs/brief_old_and_new_side_by_side.html'), 'w').write(page)

md = ['<!-- NOTE (plain words): the list of every change from the old brief to the new one, with the reason. WET = the point of the test. PROPS = this plate has other props than the notice corner, so the painter is not told to keep things that are not there. -->',
      '# Changes from the old brief to the new brief\n']
for label, kind, a_, b_ in changes:
    md.append(f'## {label} ({kind})\n\nOLD: {a_}\n\nNEW: {b_ or "(taken out)"}\n')
open(os.path.join(HERE, 'briefs/brief_changes_list.md'), 'w').write('\n'.join(md))
print(len(old.split()), 'words old;', len(new.split()), 'words new')
print(new)
