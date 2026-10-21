"""What this file does (plain words): builds the painter brief for the WET BEHIND PAINTING (round 2, 21 October 2026) from the brief that was sent for the
front painting (paint/briefs/brief_round2.txt, read only). Image 1 is now the street with the near props hidden, and image 2 is the finished front painting,
so the brief changes in three ways: (a) it tells the painter that image 2 is the same street WITH extra things standing in it that image 1 does not have,
and that none of them may be painted into image 1; (b) the lists of props to keep, the wet-look list, the thin-parts list, the meet-but-never-join list and
the never-add list lose the props that are not in image 1; (c) it asks for image 2's colours, brightness and contrast, so the two paintings match.
Every change is listed with its reason in briefs/brief_behind_changes_list.md. Nothing is sent to any painter by this file.
It writes into behind/briefs/: brief_behind.txt (exactly as it is sent, after the line of equals signs), brief_front_and_behind_side_by_side.html
(red = taken out, green = put in), brief_behind_changes_list.md, brief_behind_pair.json.
Run: python3 -I tools/make_behind_brief.py
"""
import difflib, html, json, os, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONT = 'proc-work/street_wet/painter_round_2/paint/briefs/brief_round2.txt'
raw = open(FRONT).read()
old = raw.split('==========\n', 1)[1].strip()

EXTRAS = ('a rusty drum, a notice board on two posts, a wooden handcart with a spade, a pile of coal sacks, a heap of coal on the road, '
          'a small pail at the foot of the board, a dustbin and a hanging lantern')

# (label, reason, old text, new text); each old text must occur exactly once in the text as it stands when the change is made
changes = [
 ('image 2 is the same street with extra things',
  'image 2 is now the finished front painting of the same street; it has the near props that image 1 does not have. Without this the painter may copy them into image 1',
  'Repaint image 1 completely as a hand-painted illustration in the exact painting style of image 2: the same visible brush strokes, dark ink outlines, simplified painterly textures on brick, stone, slate and wood, and painted wet shine and painted reflections.',
  'Repaint image 1 completely as a hand-painted illustration in the exact painting style of image 2: the same visible brush strokes, dark ink outlines, simplified painterly textures on brick, stone, slate and wood, and painted wet shine and painted reflections. '
  'Image 2 is a painting of this very same street from the same spot, with some extra things standing in it (' + EXTRAS + '); image 1 does not have any of them, so paint none of them: copy only the hand, the colours, the brightness and the contrast of image 2, and use it only where it shows the same street as image 1. '
  'Wherever the two pictures show the same road, pavement, kerb, gutter, wall, window, lamp and puddle, image 1 must come out looking exactly like image 2 in colour and brightness, as if painted on the same day by the same hand.'),
 ('open ground where the props stood',
  'the main risk: the painter drawing the missing props, or their rings, shadows or outlines, on the road where they stood in image 2. Also says the wet look and rubbish there',
  'Keep image 1\'s camera, framing, perspective and every shape, outline, size and position exactly as they are, and keep its pattern of light and dark; change only the brushwork and the colour handling. ',
  'Keep image 1\'s camera, framing, perspective and every shape, outline, size and position exactly as they are, and keep its pattern of light and dark; change only the brushwork and the colour handling. '
  'In the middle of the road, on the left and on the right of it, image 1 is open ground: wet setts with scattered cinders, coal chips and dust, a few puddles, and nothing standing on them. Paint exactly that, with the same wet setts, the same thin dark joint lines, the same rubbish and the same puddles as the rest of the road; leave no ring, mark, stain, outline or shadow of anything that is in image 2 but not in image 1. '),
 ('rubbish: where it lies',
  'the old sentence put the rubbish round the drum and sacks; they are not in image 1. The rubbish now lies on the open road',
  'mud along the gutters and the foot of the walls, round the drum and sacks); add no writing, print or modern litter. Keep: the rusty drum with its open top, dull dark rust-brown, not orange, its top a dark sooty hollow with only a faint orange glow low inside behind the front rim; the dark timber notice board on its two posts with the cream notice (plain paper with grey rows of print-like marks, no readable letters); the small wooden pail at the foot of the board, with no handle; the black gas lamps on their posts down both sides of the street; the brick terraces and stone cottages, the colliery building, its tall chimney and winding wheels; the wooden handcart on the left with its big spoked wheel and the spade leaning on it; the pile of coal sacks in the road; the small heap of black coal lumps on the road; the dustbin at the right edge; and the ladder on the left pavement.',
  'mud along the gutters and the foot of the walls, and scattered over the open road in the middle of the street); add no writing, print or modern litter. Keep: the black gas lamps on their posts down both sides of the street; the brick terraces and stone cottages, the colliery building, its tall chimney and winding wheels; the ladder on the left pavement; the small heap of black coal lumps on the right pavement; and the small wooden pail, the barrel and the wooden tub where image 1 has them on the pavements.'),
 ('image 2 lamp glass',
  'the front painting is now image 2: its lamps are the right ones to copy (the person asked for warm amber, the front painter made them warm cream-gold; the two paintings must agree)',
  'Every gas lamp has warm amber glass with a small bright gas mantle inside, and the gas lamp glass glows warm amber.',
  'Every gas lamp is painted exactly as image 2 paints it: warm glass with a small bright gas mantle inside.'),
 ('sky',
  'image 2 now has a plain dark smooth sky (the free sky of the front painting); ask for the same, no clouds. The sky is put in for free afterwards in any case',
  'The sky is dark grey-blue cloud with soft edges, like image 2\'s darker skies; no pale, white or bright clouds anywhere; keep the sky as dark as image 1. ',
  'The sky is a plain, smooth, dark grey-blue, exactly as dark and as plain as image 2\'s sky and image 1\'s; no clouds, and nothing pale or white anywhere in it. '),
 ('wet look: reflections',
  'no handcart or sacks stand in image 1, so no reflections of them; the warm pool on the road is a soft pool of firelight with no fire in the picture',
  'the lamp, lit-window and brazier reflections lying on the road as soft painted streaks and pools of warm light; the soft reflections of the handcart and the sacks on the road under them; the puddles',
  'the lamp and lit-window reflections lying on the road as soft painted streaks of warm light; the one soft pool of warm firelight lying on the road in the middle of the street, painted as a pool of warm light on the wet setts and no brighter than the same kind of pool in image 2 (the fire itself is not in the picture: paint no fire, no coals, no drum, no glow in the air); the puddles'),
 ('nothing brighter than the lamps',
  'the notice is not in image 1, so the "nothing is brighter than the notice" rule needs another measure',
  'Nothing is brighter than the notice. ',
  'Nothing on the road or the pavement is brighter than the lamp glass or the lit windows, and the road is never whiter or brighter than image 2\'s road. '),
 ('warm light only where it is',
  'the drum and the board are not in image 1',
  'Warm light stays only where it already is: round the drum, on the board, at the lamps, in the few lit windows, and in their reflections on the wet road where image 1 shows them.',
  'Warm light stays only where it already is: at the lamps, in the few lit windows, in the one soft warm pool on the road, and in their reflections on the wet road where image 1 shows them.'),
 ('thin parts',
  'the cart and spade are not in image 1; the ladder is',
  'Thin parts (the lamp arms, the gate bars, the cart\'s rails and spokes, the spade\'s handle, the winding rope)',
  'Thin parts (the lamp arms, the gate bars, the ladder\'s rails and rungs, the winding rope)'),
 ('never join',
  'the drum, board, spade and cart are not in image 1',
  'Where two things meet or nearly meet, keep each edge exactly where it is and never join them: the drum\'s side and the board\'s left post, each gas-lamp head and the wall pipe and bracket beside it, the far lamps and the house downpipes, the spade and the cart\'s wheel; the winding rope never joins the lamp.',
  'Where two things meet or nearly meet, keep each edge exactly where it is and never join them: each gas-lamp head and the wall pipe and bracket beside it, the far lamps and the house downpipes; the winding rope never joins the lamp.'),
 ('never add: smoke',
  'no drum in image 1',
  'smoke or steam anywhere (not from the drum, not from any chimney)',
  'smoke or steam anywhere (not from the road, not from any chimney)'),
 ('never add: glows',
  'no notice or drum in image 1',
  'glows, halos or light rays round any light, the notice or the drum (',
  'glows, halos or light rays round any light ('),
 ('never add: pail handle and props',
  'the pails that are in image 1 have handles, so the old "no handle" rule goes; the long list of near things not to paint into image 1 is put here again, as the last words the painter reads',
  'a handle on the pail; people, animals or birds; extra props (no coal tub, rails, barrel or crates in the road or on the pavement);',
  'people, animals or birds; extra props (nothing in the road or on the pavement that image 1 does not have, above all no drum, notice board, posts, handcart, spade, coal sacks, heap of coal on the road, dustbin, lantern, coal tub, rails or crates);'),
]
new = old
for label, why, a, b in changes:
    assert new.count(a) == 1, f'change "{label}": old text found {new.count(a)} times'
    new = new.replace(a, b)
assert 'matte' not in new.lower()

os.makedirs(os.path.join(HERE, 'briefs'), exist_ok=True)
NOTE = ('NOTE (plain words): this file is the painter brief for the WET BEHIND PAINTING of round 2 (the wet street with the near props hidden, 21 October 2026), exactly as it is sent: one paragraph, after the line of equals signs.\n'
        'Made by tools/make_behind_brief.py from the front painting\'s brief (paint/briefs/brief_round2.txt), with the changes listed in brief_behind_changes_list.md.\n'
        '==========\n')
open(os.path.join(HERE, 'briefs/brief_behind.txt'), 'w').write(NOTE + new + '\n')
json.dump({'front_brief': old, 'behind_brief': new}, open(os.path.join(HERE, 'briefs/brief_behind_pair.json'), 'w'), indent=1)


def tokens(s): return re.findall(r'\S+\s*', s)


a, b = tokens(old), tokens(new)
sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
left, right = [], []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    ta, tb = html.escape(''.join(a[i1:i2])), html.escape(''.join(b[j1:j2]))
    if tag == 'equal':
        left.append(ta); right.append(tb)
    else:
        if ta: left.append(f'<del>{ta}</del>')
        if tb: right.append(f'<ins>{tb}</ins>')
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painter brief front and behind</title>
<!-- NOTE (plain words): the painter brief of the front painting and the brief of the behind painting side by side. Red struck-through = taken out of the front brief.
Green = put into the behind brief. Made by tools/make_behind_brief.py. Nothing here is sent anywhere. -->
<style>body{{font:16px/1.5 system-ui,sans-serif;margin:16px;background:#fff;color:#111}}
@media (prefers-color-scheme:dark){{body{{background:#161616;color:#ddd}}}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}@media(max-width:800px){{.cols{{grid-template-columns:1fr}}}}
h1{{font-size:20px}}h2{{font-size:16px}}p{{white-space:pre-wrap}}
del{{background:#fbb;color:#600;text-decoration:line-through}}ins{{background:#bfb;color:#030;text-decoration:none}}
@media (prefers-color-scheme:dark){{del{{background:#5a2020;color:#fcc}}ins{{background:#1d4a1d;color:#cfc}}}}</style></head><body>
<h1>Painter brief: front painting and behind painting (round 2)</h1>
<p>Red = taken out, green = put in.</p>
<div class="cols"><div><h2>FRONT PAINTING (as sent)</h2><p>{''.join(left)}</p></div><div><h2>BEHIND PAINTING (this one)</h2><p>{''.join(right)}</p></div></div></body></html>'''
open(os.path.join(HERE, 'briefs/brief_front_and_behind_side_by_side.html'), 'w').write(page)

md = ['<!-- NOTE (plain words): every change from the front painting\'s brief to the behind painting\'s brief, with the reason. -->',
      '# Changes from the front painting\'s brief to the behind painting\'s brief\n']
for label, why, a_, b_ in changes:
    md.append(f'## {label}\n\nWhy: {why}\n\nOLD: {a_}\n\nNEW: {b_}\n')
open(os.path.join(HERE, 'briefs/brief_behind_changes_list.md'), 'w').write('\n'.join(md))
print(len(old.split()), 'words front;', len(new.split()), 'words behind')
print(new)
