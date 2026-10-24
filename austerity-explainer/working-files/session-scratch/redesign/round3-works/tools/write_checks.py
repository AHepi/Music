# Writes the four Works shot check files into the kit's examples folder.
import json, os
OUT = '/home/user/Music/austerity-explainer/film-kit/examples/inflation-chapter-2-newcomers'
def about(view, arg, state=''):
    return ("What this file is: the shot check for the Works' view " + view + " (paper-film/blender/inflation-chapter-2-newcomers/works/"
            "assemble_works.py, plan 34 part 1 'A. The Works'): which objects make up each prop and figure, their parts in the story, "
            "the lane's direction, where the typed words go. Each waiting man is his own group, so the checker counts them and draws "
            "their outlines (solo/NAME.png). Used by paper-film/blender/shot_facts.py and paper-film/tools/check_shot.py; run from the kit's "
            "top folder with BLEND=assets/models/inflation-chapter-2-newcomers/works/works-lane.blend paper-film/tools/check-shot.sh "
            "paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py THIS_FILE OUT [PICTURE] -- --view " + arg + state + ".")
title_zone = [0.06, 0.05, 0.9, 0.22]
w1 = {
 "about": about("W1 (No. 1's gate)", 'w1'),
 "size": [1080, 1920],
 "groups": {
  "no-1 gate": ["no-1-gate", "no-1-chain"], "no-1 board": ["gate-board-no-1"], "brazier": ["brazier-drum", "brazier_coal_*"],
  "lantern": ["hurricane-lantern"], "lunch tin": ["lunch-tin"], "petrol drum": ["no-1-drum-petrol"], "diesel drum": ["no-1-drum-diesel"],
  "gate lamp": ["no-1-gate-lamp"], **{f"man {k}": [f"man-{k}"] for k in range(1, 8)},
  "no-1 chimney": ["no-1-chimney"], "no-2 chimneys": ["no-2-chimney-a", "no-2-chimney-b"]},
 "subject": "no-1 gate",
 "story": ["brazier", "lantern", "diesel drum"] + [f"man {k}" for k in range(1, 8)],
 "lights_in_story": ["lantern"],
 "pairs_also": ["no-1 board", "petrol drum", "lunch tin", "gate lamp"],
 "work": [],
 "on_ground": ["brazier", "petrol drum", "diesel drum"] + [f"man {k}" for k in range(1, 8)],
 "must_read": ["no-1 board"], "box_excludes": ["no-1 board"],
 "lines": {"lane": [0, 1, 0], "level": [0, 1, 0]}, "lines_key": "lane", "eye_height": [1.5, 1.9], "title_zone": title_zone,
}
w2 = {
 "about": about("W2 (No. 2's open gate, flat out; the subject is the open gateway: its leaves, swung into the yard, and the crates "
                "standing in it)", 'w2'),
 "size": [1080, 1920],
 "groups": {
  "no-2 gateway": ["no-2-gate", "no-2-crate-*"], "no-2 board": ["gate-board-no-2"], "petrol drum": ["no-2-drum-petrol"], "diesel drum": ["no-2-drum-diesel"],
  "gate lamp": ["no-2-gate-lamp"], "hand truck": ["hand-truck"],
  **{f"man {k}": [f"no-2-man-{k}"] for k in range(1, 9)},
  "no-1 chimney": ["no-1-chimney"], "no-2 chimneys": ["no-2-chimney-a", "no-2-chimney-b"]},
 "subject": "no-2 gateway",
 "story": ["petrol drum", "diesel drum", "hand truck"],
 "pairs_also": ["no-2 board", "gate lamp"] + [f"man {k}" for k in range(1, 9)],
 "work": [],
 "on_ground": ["petrol drum", "diesel drum", "hand truck"] + [f"man {k}" for k in range(1, 9)],
 "must_read": ["no-2 board"], "box_excludes": ["no-2 board"],
 "lines": {"lane": [0, 1, 0], "level": [0, 1, 0]}, "lines_key": "lane", "eye_height": [1.5, 1.9], "title_zone": title_zone,
}
w3 = {
 "about": about("W3 (both gates; the subject is the two gates and the high dividing wall between them, where the lane's lines meet)", 'w3'),
 "size": [1080, 1920],
 "groups": {
  "two gates and the wall between": ["no-1-gate", "no-1-chain", "no-2-gate", "dividing-wall"], "gate boards": ["gate-board-no-1", "gate-board-no-2"],
  "brazier": ["brazier-drum", "brazier_coal_*"], "lantern": ["hurricane-lantern"], "no-1 drums": ["no-1-drum-*"], "no-2 drums": ["no-2-drum-*"],
  "no-2 crates": ["no-2-crate-*", "hand-truck"], "handcart": ["handcart", "handcart-crate-*"], "bank sign": ["bank-hanging-sign"],
  **{f"man {k}": [f"man-{k}"] for k in range(1, 8)},
  "no-1 chimney": ["no-1-chimney"], "no-2 chimneys": ["no-2-chimney-a", "no-2-chimney-b"]},
 "subject": "two gates and the wall between",
 "story": ["gate boards", "brazier", "no-2 crates"] + [f"man {k}" for k in range(1, 8)],
 "lights_in_story": ["lantern"],
 "pairs_also": ["lantern", "no-1 drums", "no-2 drums", "handcart", "bank sign"],
 "work": [],
 "on_ground": ["brazier", "no-1 drums", "no-2 drums", "no-2 crates", "handcart"] + [f"man {k}" for k in range(1, 8)],
 "must_read": ["gate boards", "bank sign"],
 "lines": {"lane": [0, 1, 0], "level": [0, 1, 0]}, "lines_key": "lane", "title_zone": title_zone,
 "eye_height": [0.8, 7.0],
 "eye_height_note": "The camera stands at the end house's upstairs window, 4.6 m above the street: the checker measures down to the window sill just below it (about 0.9 m), so the range is wide on purpose.",
}
w4 = {
 "about": about("W4 (inside No. 2's yard)", 'w4'),
 "size": [1080, 1920],
 "groups": {
  "no-2 gate": ["no-2-gate"], "jacket and cap": ["jacket-and-cap"], "upturned crate": ["w4-upturned-crate"],
  "mug and wages": ["tin-mug-and-wages"], "crates": ["no-2-crate-*", "hand-truck"],
  **{f"man {k}": [f"no-2-man-{k}"] for k in range(1, 9)}, "handcart": ["handcart", "handcart-crate-*"]},
 "subject": "no-2 gate",
 "story": ["jacket and cap", "upturned crate", "mug and wages"] + [f"man {k}" for k in range(1, 9)],
 "pairs_also": ["crates", "handcart"],
 "work": [],
 "on_ground": ["upturned crate", "crates", "handcart"] + [f"man {k}" for k in range(1, 9)],
 "stands_on": {"mug and wages": "upturned crate"},
 "must_read": [],
 "lines": {"lane": [0, -1, 0], "level": [0, -1, 0]}, "lines_key": "lane", "eye_height": [1.5, 1.9], "title_zone": title_zone,
}
import copy
w2s = copy.deepcopy(w2)
w2s['about'] = about("W2 in No. 2's slowed state (its helper plate: the eight men waiting, the gate half shut)", 'w2', ' --state slowed')
w2s['story'] = w2['story'] + [f"man {k}" for k in range(1, 9)]
w2s['pairs_also'] = ["no-2 board", "gate lamp"]
for name, data in (('works-w1-shot-check.json', w1), ('works-w2-shot-check.json', w2), ('works-w2-slowed-shot-check.json', w2s), ('works-w3-shot-check.json', w3), ('works-w4-shot-check.json', w4)):
    assert len(data['groups']) <= 20, (name, len(data['groups']))
    with open(os.path.join(OUT, name), 'w') as handle:
        json.dump(data, handle, indent=1)
    print(name, len(data['groups']), 'groups')
