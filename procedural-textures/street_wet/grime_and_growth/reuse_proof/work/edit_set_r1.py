# Round 1 of finishing the courtyard's settings file. Only the settings file and a look file are written (never kit code).
import json, copy
KIT = 'proc-work/kits/weathering'
path = KIT + '/sets/japanese_courtyard.json'
s = json.load(open('proc-work/street_wet/grime_and_growth/reuse_proof/original/japanese_courtyard.draft.json'))

s['_how_to_read'] = ("FINISHED for the reuse proof (21 October, 'Reuse - the same kit on the Japanese courtyard'): the designer's draft, with the changes the first pictures asked for "
                     "(each one is written next to the key it changed as a _why note). Same keys as pit_village_street.json; nothing in the kit code repeats any of it. "
                     "The courtyard has no plate camera yet, no 22-picture lighting test and no earlier layers, so those blocks stay as the draft left them.")

# 1. the hidden roof-tile prototype carries the roof's material: it must not be on the 'never' list, or the roof stays clean
s['never']['objects'] = [p for p in s['never']['objects'] if p != '^CT / ']
s['never']['_why'] = ("round 1: '^CT / ' removed. The 'Hall roof' object has no material slot of its own (a geometry-nodes roof); its tile material sits on the hidden "
                      "'CT / Ceramic pan prototype'. With that object on the never list the role finder gave the roof no material and moss/soot/cracks could not go on it.")

# 2. cameras of the proof: the file's own camera is entry 'photo'; two close views
s['cameras'] = [
    s['cameras'][0],
    {"name": "lantern_rocks", "location": [2.6, -1.0, 1.15], "look_at": [-1.5, 2.6, 0.7], "fov_v": 40.0, "photo_px": [1800, 1200],
     "_note": "close view of the stone lantern (right, 2.7 m away) with the pond rocks behind it; added by the reuse proof"},
    {"name": "hall_posts", "location": [3.9, 1.3, 1.25], "look_at": [0.3, 5.0, 1.1], "fov_v": 42.0, "photo_px": [1800, 1200],
     "_note": "close view of the hall posts, the veranda edge and the plinth foot, from the stepping-stone path; added by the reuse proof"},
]

# 3. the plinth is the ground the hall stands on (post feet and the wall foot are measured from its top, not from the earth under it)
g = s['geometry']
g['ground']['roles'] = ["ground.earth", "ground.gravel", "stone.dressed"]
g['ground']['skip_objects'] = ["^Courtyard ground source$", "^Lantern finial$"]
g['ground']['_why'] = ("round 1: the plinth (stone.dressed, top at z 0.55) counts as ground, so the height of a post foot or a wall foot is measured from the plinth top. Without it every "
                       "post foot is 0.55 m 'above the ground' and the foot layer (splash band, damp tide mark, rot) never reaches it. The tiny lantern finial is also stone.dressed and is skipped.")

# 4. raked gravel: plants and moss are raked out of the middle, the outer 35 cm are left to the edge (weeds and moss at the gravel edge)
for item in s['keep_clear']:
    if item.get('id') == 'raked_gravel_court':
        item['min'] = [1.25, -5.55]
        item['max'] = [8.75, 1.55]
        item['feather_m'] = 0.3
        item['_why'] = "round 1: drawn in by 35 cm so the gravel's outer edge may grow weeds and moss; the raked middle stays clear."

# 5. which layer goes on which roles
a = s['apply']
a['soot']['roles'] = ["wall.plaster", "stone.dressed", "timber.frame", "roof.tile", "wall.cap"]
a['foot']['roles'] = ["wall.plaster", "stone.dressed", "timber.frame", "stone.natural"]
a['foot']['role_dials'] = {"stone.natural": {"splash_strength": 0.7, "tide_strength": 0.7}, "timber.frame": {"tide_strength": 1.3, "splash_strength": 1.2}}
a['wallgrowth']['roles'] = ["wall.plaster", "wall.cap", "stone.dressed", "stone.natural", "roof.tile", "timber.deck"]
a['dirt']['roles'] = ["ground.gravel", "ground.earth", "stone.natural"]
a['wallgrowth']['_why'] = "round 1: stone.natural added (moss, algae and lichen on the lantern, rocks and stepping stones)."
a['foot']['_why'] = "round 1: stone.natural added (damp splash band at the foot of every stone); timber.frame gets a stronger tide mark (rot at the post feet)."
a['dirt']['_why'] = "round 1: stone.natural added (water marks and film on the stones)."

# 6. ground layers' choices per surface kind for the new surface
gr = s['ground']['role_dials']
gr['dirt']['stone.natural'] = {"film": 0.6, "polish": 0.0, "water_marks": 1.0, "rust_halo": 0.0, "drum_ring": 0.0, "tar_patches": 0.0, "tar_splash": 0.0, "scrub_strip": 0.0}
gr['groundmoss']['stone.natural'] = {"joint_share": 0.0, "patch_moss": 1.0, "algae_fan": 0.6, "liverwort": 0.8, "far_band": 0.0}

json.dump(s, open(path, 'w'), indent=1)
print('written', path)
