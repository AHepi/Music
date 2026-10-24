# Fix round: writes the combined recipe note (kits/weathering/15 Recipe ...md) from the integrator's original (kept in fix/backup) plus the fix round's changes and numbers.
#   python3 -I update_recipe.py        (always starts from the backup, so running it twice gives the same note)
import json
import os
import re
import sys

K = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
FIX = K + 'street_wet/grime_and_growth/fix/'
NOTE = K + 'kits/weathering/15 Recipe - weathering kit - grime, cracks, stains, weeds and moss - how it is made.md'
ORIG = FIX + 'backup/15 Recipe - weathering kit - grime, cracks, stains, weeds and moss - how it is made.md'

C = json.load(open(FIX + 'keep/checks_final_run2.json'))
JOINTS = json.load(open(FIX + 'work/checks_final_street.json'))['joints']
M1S = json.load(open(FIX + 'keep/measures_t22_street_run2.json'))
M1L = json.load(open(FIX + 'keep/measures_t22_lockout_run2.json'))
P6 = json.load(open(FIX + 'rounds/final/p6_fix.json'))
TIME = json.load(open(FIX + 'keep/time_run2.json'))
ENTRY = {}
for which in ('street', 'lockout', 'courtyard'):
    p = FIX + f'work/entry_tests/{which}/entry_test.json'
    if os.path.exists(p):
        ENTRY[which] = json.load(open(p))

text = open(ORIG).read()


def sub(old, new, count=1):
    global text
    assert text.count(old) == count, (old[:80], text.count(old))
    text = text.replace(old, new)


def pct(x, nd=0):
    return f'{100 * x:.{nd}f}'


# ------------------------------------------------------------------------------------------------------ numbers used below
pl = C['plants']
pd = C['puddles']
wc = C['walls_colour']
mu = C['mush']
dry, wet = pl['street_dry'], pl['street_wet']
ldry, lwet = pl['lockout_dry'], pl['lockout_wet']
w_l_d, w_r_d = wc['street_dry']['walls_left'], wc['street_dry']['walls_right']
m_d, m_w = mu['street_dry'], mu['street_wet']
l_d, l_w = mu['lockout_dry'], mu['lockout_wet']
p1s, p1l = M1S['p1']['summary'], M1L['p1']['summary']
p6s, p6l = P6['final_main_A_wet_kit'], P6['final_lockout_B_wet_kit']
ts, tl = TIME['street'], TIME['lockout']


def entry_line(which):
    d = ENTRY.get(which)
    if not d:
        return f'* **{which}**: not run.'
    t = d['tests']
    g = t['group_off']
    return (f"* **{which}** ({len(d['errors'])} errors): `remove()` gives the scene back (picture {t['remove_all']['picture']['dots_over_one_step'] * 100:.3f} percent of dots over one step apart); all master dials at 0 against the earlier layers alone "
            f"{t['master_0_equals_earlier_only']['dots_over_one_step'] * 100:.2f} percent of dots over one step (largest {t['master_0_equals_earlier_only']['max_difference']}); two draws of one state {t['determinism']['dots_over_one_step'] * 100:.2f} percent apart; "
            f"apply and remove twice: node counts {t['apply_remove_twice_same_node_count']['node_counts']}; kit leftovers {len(t['leftovers'])}; the kit changes {t['kit_changes_the_picture']['dots_over_one_step'] * 100:.0f} percent of the dots; "
            f"each group off alone changes the picture (walls {g['walls']['dots_over_one_step'] * 100:.0f}, ground {g['ground']['dots_over_one_step'] * 100:.0f}, growth {g['growth']['dots_over_one_step'] * 100:.1f} percent of dots).")


# ------------------------------------------------------------------------------------------------------ 0 the header
sub("Written by the integrator, 21 October 2026, in plain words.",
    "Written by the integrator, 21 October 2026, in plain words; **section 12 and the notes marked \"fix round\" were added after the two checkers' findings (the same day).**")

# ------------------------------------------------------------------------------------------------------ 3.2 items 1 and 2
sub("Decision: kept on**; a plate takes 1.5 s longer, which does not matter for a handful of stills, and no weed stands on a coal lump.",
    "Decision: kept on**; a plate takes 1.5 s longer, which does not matter for a handful of stills, and no weed stands on a coal lump. **Fix round: built.** The clearance is now a look-up in a baked picture (`litter_dist`, section 12.3) instead of a search over every piece; the growth layer's share of the drawing time fell from +70 percent to a few percent, and 0 of 101 weeds (street) and 0 of 60 (lockout) stand within 5 cm of a litter piece's centre.")
sub("**Not fixed**: the proper fix is for the water layer to hand its puddle field to the plants as a ground-plan picture. Written down as the first job of the next round.",
    "**Fix round: fixed.** The water layer's puddle picture is drawn once from above and stamped into the pack as `above_water` (0 in a puddle, section 12.3); the plants already read that mask, so no plant root now stands in a puddle (0 of 157 on the main plate), and the checkers' pixel count (green blobs whose centre is in a puddle) fell from 39 to 19 percent (the rest are leaves leaning over a puddle's edge and reflections).")

# ------------------------------------------------------------------------------------------------------ 5 the looks
sub("| set: steps | `geometry.steps.max_height_m`, `max_extent_m` | none | 0.8, 2.0 | section 3.2, item 3 |\n",
    "| set: steps | `geometry.steps.max_height_m`, `max_extent_m` | none | 0.8, 2.0 | section 3.2, item 3 |\n"
    "| *fix round* soot | `film_mult`, `washed_share`, `washed_pale`, `edge_sharp`, `grey_pull`, `pale_warm` | 0.60, 0.17, 0.8, 0.85, 0.25, (new) | 0.80, 0.07, 0.5, 0.55, 0.10, 1.0 | the pale panels and the cold grey cast on the red brick (section 12.1); the film goes back up because fewer pale patches means a darker average wall |\n"
    "| *fix round* set: soot role values | trims / colliery `film_mult` | 1.4 / 1.65 | 1.2 / 1.25 | so that trims and the colliery keep about the film they had under the new 0.80 |\n"
    "| *fix round* steps | `white_cream`, `white_value` | (new) | 1.0, 0.85 | whitened steps cream, not blue-white |\n"
    "| *fix round* dirt | `ring_pale`, `dip_dark`, `film_max_share` | (new), (new), 0.25 | 0.0, 0.12, 0.15 | no bright arcs from the water marks; smaller film patches |\n"
    "| *fix round* groundcracks | `open_joint_share`, `open_depth_mm`, `sett_disturb` | 0.14, (new), 0.7 | 0.07, 0.8, 0.35 | fewer sett cracks, no pale hairline along the joint |\n"
    "| *fix round* growth | `colour_gain`, `colour_sat`, `cushions_amount`, `dead_grass_share`, `weed_cover`, `gutter_tuft_share` | 1.0, (new), 0.6, 0.15, 0.01, 0.05 | 0.55, 0.85, 0.3, 0.08, 0.02, 0.10 | plants 4 to 5 times lifted instead of 8, duller, half the flat moss strings, fewer pale dead-grass tufts, more weeds to make up for the ones kept out of puddles and off litter |\n"
    "| *fix round* foot, runoff | `salt_bloom`; `width_dots`, `stain_value`, `iron_rust`, `leak_share`, `source_share`, `pair_share` | 0.02; 10, 0.9, 0.5, 0.15, 0.8, 0.8 | 0.008; 14, 1.0, 0.9, 0.3, 0.9, 1.0 | fewer white flecks at the wall foot; wider, rust-coloured run-off |\n")

# ------------------------------------------------------------------------------------------------------ 6 adding a new set
sub("    then, if the set has litter, `python3 -I masks/make_pack.py <set id> <scene id> <raw folder> --rubbish <picture>`.",
    "    then, if the set has litter, `python3 -I masks/make_pack.py <set id> <scene id> <raw folder> --rubbish <picture>`. **Fix round:** a set that has the earlier water layer and litter layer then draws and stamps two more pictures: `python3 -I harness/make_plan_pictures.py <set id> <scene id> <work folder>` (rented machine, about 40 s; section 12.3), so that plants stay out of puddles and off litter.")

# ------------------------------------------------------------------------------------------------------ 8 the dial tables: the street column of the changed dials and the new rows
CHANGED = {
    'soot': {'film_mult': 0.8, 'washed_share': 0.07, 'washed_pale': 0.5, 'edge_sharp': 0.55, 'grey_pull': 0.1},
    'runoff': {'width_dots': 14, 'stain_value': 1.0, 'iron_rust': 0.9, 'leak_share': 0.3, 'source_share': 0.9, 'pair_share': 1.0},
    'foot': {'salt_bloom': 0.008},
    'dirt': {'film_max_share': 0.15},
    'groundcracks': {'open_joint_share': 0.07, 'sett_disturb': 0.35},
    'growth': {'colour_gain': 0.55, 'colour_sat': 0.85, 'cushions_amount': 0.3, 'dead_grass_share': 0.08, 'weed_cover': 0.02, 'gutter_tuft_share': 0.1},
}
NEW_ROWS = {
    'soot': [('pale_warm', '0 to 1', '0', '1.0', '', 'Colour of the washed patches: 0 = a neutral pale stone (reads grey-blue under a night sky), 1 = a warm buff stone that keeps the warm hue of brick. (fix round)')],
    'steps': [('white_cream', '0 to 1', '0', '1.0', '', 'Colour of whitened stone: 0 = a cold near-white, 1 = a warm cream (donkey stone; a cold white reads blue-white under a night sky). (fix round)'),
              ('white_value', '0.5 to 1.2', '1', '0.85', '', 'Brightness of whitened stone against the colour chosen by white_cream (below 1 so it does not read as plastic). (fix round)')],
    'dirt': [('ring_pale', '0 to 0.8', '0.45', '0', '', 'How much paler than the stone the tide line of a dried puddle is (0 = no pale line; at 0.45 it showed as a bright arc). (fix round)'),
             ('dip_dark', '0 to 0.4', '0.12', '0.12', '', 'How much darker the shallow dip inside a dried puddle ring is. (fix round)')],
    'groundcracks': [('open_depth_mm', '0 to 6 mm', '3', '0.8', '', 'How deep an open sett joint is cut into the surface: a deep one catches the light and shows as a pale hairline on a wet road. (fix round)')],
}


def section_bounds(layer):
    m = re.search(rf'^### {layer}  \(slot', text, re.M)
    n = re.search(r'^###? ', text[m.end():], re.M)
    return m.start(), m.end() + (n.start() if n else len(text) - m.end())


for layer, dials in CHANGED.items():
    for dial, value in dials.items():
        a, b = section_bounds(layer)
        block = text[a:b]
        pat = re.compile(rf'^(\| `{dial}` \| [^|]*\| [^|]*\| )([^|]*)(\| [^|]*\| .*)$', re.M)
        m = pat.search(block)
        if not m:
            print('no row', layer, dial)
            continue
        new_block = block[:m.start()] + m.group(1) + f'{value} ' + m.group(3) + block[m.end():]
        text = text[:a] + new_block + text[b:]
for layer, rows in NEW_ROWS.items():
    a, b = section_bounds(layer)
    block = text[a:b]
    lines = block.rstrip('\n').split('\n')
    # insert after the last table row
    last = max(i for i, l in enumerate(lines) if l.startswith('| `'))
    add = [f'| `{name}` | {rng} | {default} | {street} | {court} | {doc} |' for name, rng, default, street, court, doc in rows]
    lines[last + 1:last + 1] = add
    text = text[:a] + '\n'.join(lines) + '\n\n' + text[b:].lstrip('\n')

# ------------------------------------------------------------------------------------------------------ 9 the numbers
sub("## 9. The numbers (final settings; the final round is `integrated/work/r5`)",
    "## 9. The numbers (the integrator's final settings before the fix round; the final round was `integrated/work/r5`; **the fix round's numbers are in section 12.5**)")

# ------------------------------------------------------------------------------------------------------ 10 not done
sub("* The plants cannot see the water layer's puddles (36 percent of the plants of the main plate stand in one). Fix: the water layer hands its puddle field to the plants as a ground-plan picture.\n",
    "* ~~The plants cannot see the water layer's puddles.~~ **Done in the fix round** (baked `above_water`, section 12.3).\n")
sub("* The litter clearance of the plants costs +1.5 s a plate with the second round's 58,753 litter pieces. A cheaper clearance (a ground-plan picture of where litter lies instead of a nearest-point question) is not built.\n",
    "* ~~The litter clearance of the plants costs +1.5 s a plate.~~ **Done in the fix round** (baked `litter_dist`, section 12.3).\n")

# ------------------------------------------------------------------------------------------------------ 11 what the integrator changed
sub("* Nothing in `walls/`, `ground/`, `growth/` was edited.",
    "* Nothing in `walls/`, `ground/`, `growth/` was edited by the integrator. (The fix round did edit a few lines in them: section 12.7.)")

# ------------------------------------------------------------------------------------------------------ 12 the fix round
sec = f"""

---

## 12. The fix round (after the two checkers)

Two fresh checkers looked at the integrated street (the four plates and four sheets, nothing painted) and found what a viewer would notice first. This section says what they found, what was changed for each finding (dials where possible, two small kit additions where not), what was redrawn, every number before and after, and what is still not right. The "before" is always the integrator's round r5 (`integrated/plates`); the earlier layers alone ("base") are unchanged. Nothing was painted: no call to the painter was made.

### 12.1 Finding by finding

| what a viewer sees | what was done | where it lives |
|---|---|---|
| Weeds and moss glow lime-green on the dark road, the first thing the eye lands on (median plant brightness {dry['before']['plant_lum_med']} against {dry['before']['ring_lum_med']} round it) | colour lift 8 times to 4.4 times (`growth.colour_gain` 0.55 of the 8 times in `species.json`), saturation x0.85, half the flat moss strings (`cushions_amount` 0.3), fewer pale dead-grass tufts (`dead_grass_share` 0.08) | look dials only |
| Plants stand in puddles in the wet state (39 percent of the plant blobs) | the earlier water layer's puddle picture (drawn once from above, in the wet state of the plates) is stamped into the pack's `above_water`; the growth layer already grows nothing where it is 0 | new picture, `masks/stamp_pack.py`, `harness/make_plan_pictures.py`, runner view `plan:puddles` |
| Hard-edged pale or blue-white panels and a cold grey cast on the left brick terrace; the red loses its warmth | washed patches 17 to 7 percent of the wall (`washed_share`), paleness 0.8 to 0.5, softer edges (`edge_sharp` 0.55), colder grey pull 0.25 to 0.10, the patches' own colour made warmer (`pale_warm` 1.0), and the film back up from 0.60 to 0.80 so the walls do not go dark mush (trims and colliery role values lowered to 1.2 and 1.25 so they keep their film) | look dials, one new dial (`soot.pale_warm`), set file role values |
| Whitened doorsteps are cold blue-white wedges | warm cream (`steps.white_cream` 1.0) a little less bright (`white_value` 0.85) | two new dials |
| Near wet road looks over-processed: film patches with bright arcs, three near-identical rings, a thin crack on nearly every sett | no pale tide line on the water marks (`dirt.ring_pale` 0, new), smaller film patches (`film_max_share` 0.15), sett disturbance halved (`sett_disturb` 0.35), open joints 14 to 7 percent and cut only 0.8 mm deep instead of 3 mm (`open_joint_share`, `groundcracks.open_depth_mm`, new): the pale hairline along a joint was the cut's slope catching the light | look dials, two new dials |
| Run-off streaks and wall-foot damp invisible at film size; the element called "stains" does not show | streaks 14 dots wide, rust-coloured under the pipe joints (`iron_rust` 0.9), more long leaks (0.3), on 90 percent of the sources; white flecks at the wall foot cut to 0.008 | look dials. **Not solved**: see 12.6 |
| The lockout plate hardly changes | left as it is (a judgement call: it already reads as grubby from the litter and the iron). If visible weather is wanted there it has to come from the walls and the gutter | nothing changed |
| Drawing time 2.1 times a plate, 70 percent of it the plants' litter clearance | the clearance is a look-up in a baked picture (`litter_dist`) | new picture, one change in `growth/scatter.py` |
| Reuse hygiene: the lint missed one-decimal numbers (the street's bounds sat in `masks/check_against_earlier.py`, a camera name in `growth/jobs_growth.py`); stale courtyard sidecar files; the round's PNGs were deleted so nothing could be re-checked | the lint now catches lists of numbers and camera names copied from a set file; both scripts read the set file instead (`legacy.places_grid`, `growth.close_camera`); the four sidecar files were moved out of the kit (to `grime_and_growth/fix/retired_sidecars`); every PNG of this round has a SHA-256 hash in `fix/keep/` and the final plates are kept as PNG | code |

### 12.2 What stayed as it was
No layer was added or removed. The master dials, the order, the roles, the packs (except the two new pictures) and every dial not listed in the table of 12.1 are unchanged; a dial added in this round has a default that gives the old behaviour (`pale_warm` 0, `white_cream` 0, `white_value` 1, `ring_pale` 0.45, `dip_dark` 0.12, `open_depth_mm` 3), so the courtyard's look, which does not name them, draws as before.

### 12.3 The two baked pictures (how to make them for a new set)
* **`above_water`** (the mask that says "water here, grow nothing"): for a pond it was always made from the set's water level. For a set with the earlier water layer's puddles, `harness/make_plan_pictures.py SET SCENE WORK_DIR` draws the puddle mask seen from above (runner view `plan:puddles`, 2 cm dots, in the wet state of the plates), `masks/stamp_pack.py` marks a dot as puddle above 0.5 (the same line the measures use), widens it by 3 cm and writes 0 there. About 18 percent of the street's ground counts as puddle. A mask that says "puddle" in a dry plate too is the price of keeping the dry and the wet plate the same plants.
* **`litter_dist`** (a new mask, picture `gp_h.png`, 2 cm dots): the distance in metres (0 to 0.25, scaled to 0 to 1) to the nearest litter piece. It is made from the litter pieces of the objects named in `growth.avoid_pieces_of` seen from above (white shapes, runner view `plan:litter`, 1 cm dots) **and the centre of every piece** (the runner writes `plan_litter_points.json`): a first version from the picture alone lost 44 percent of the pieces because thin straws and dust are narrower than a dot, and 170 of 236 weeds then stood within 5 cm of a piece's centre. With the centres added, 0 of 101. The growth layer's `avoid_m` (5 cm) dial still means what it says: a plant is not stood where `litter_dist` x 0.25 m is below it. A pack without the picture falls back to the old nearest-point search (slow, same answer).
* Both pictures are valid only for the state they were drawn in (the plates' puddle amount; the litter's amount and seed). Draw them again when those change. Stamping puddles twice only widens them: put the pack's `gp_c.png` and `manifest.json` back first to change the margin.

### 12.4 The new dials
`soot.pale_warm`, `steps.white_cream`, `steps.white_value`, `dirt.ring_pale`, `dirt.dip_dark`, `groundcracks.open_depth_mm` (rows are in section 8). The soot layer's washed patches and the run-off streaks lift their colour toward a pale target; the target of the patches can now be warm.

### 12.5 The numbers, before and after (plates 1536 x 2730, 64 samples, kit against the earlier layers alone; PNG, the checkers' own scripts re-run: `fix/work/checks.py`)

**Plants (main plate, the ground part).**

| | dry before | dry after | wet before | wet after |
|---|---|---|---|---|
| green plant dots | {dry['before']['green_dots']} | {dry['after']['green_dots']} | {wet['before']['green_dots']} | {wet['after']['green_dots']} |
| median plant brightness | {dry['before']['plant_lum_med']} | {dry['after']['plant_lum_med']} | {wet['before']['plant_lum_med']} | {wet['after']['plant_lum_med']} |
| brightness of the ring round them | {dry['before']['ring_lum_med']} | {dry['after']['ring_lum_med']} | {wet['before']['ring_lum_med']} | {wet['after']['ring_lum_med']} |
| plant over ring | {dry['before']['plant_over_ring']} | {dry['after']['plant_over_ring']} | {wet['before']['plant_over_ring']} | {wet['after']['plant_over_ring']} |
| share of plant dots over brightness 0.45 | {pct(dry['before']['share_V_over_045'])} % | {pct(dry['after']['share_V_over_045'])} % | {pct(wet['before']['share_V_over_045'])} % | {pct(wet['after']['share_V_over_045'])} % |

The plan wanted a plant brightness of 0.17 to 0.33: now 0.26 dry and 0.17 wet (before 0.39 and 0.29). The lockout plate, lit more strongly (lighting B): plants {ldry['after']['plant_lum_med']} dry and {lwet['after']['plant_lum_med']} wet (before {ldry['before']['plant_lum_med']} and {lwet['before']['plant_lum_med']}); two thirds of its dry plant dots are still over 0.45, so the lockout's plants are the brightest thing left.

**Puddles.** The checkers' pixel count (green blobs of 25 dots or more whose centre is inside a puddle of the earlier water layer): main wet plate {pd['street_wet']['before']['in_puddle']} of {pd['street_wet']['before']['plants']} ({pct(pd['street_wet']['before']['share'])} %) before, {pd['street_wet']['after']['in_puddle']} of {pd['street_wet']['after']['plants']} ({pct(pd['street_wet']['after']['share'])} %) after; green dots inside a puddle {pct(pd['street_wet']['before']['green_dots_in_puddle'])} % before, {pct(pd['street_wet']['after']['green_dots_in_puddle'])} % after. Lockout wet plate {pd['lockout_wet']['before']['in_puddle']} of {pd['lockout_wet']['before']['plants']} before, {pd['lockout_wet']['after']['in_puddle']} of {pd['lockout_wet']['after']['plants']} after. The exact count from the plant list (root position against the stamped mask): **0 of {p6s['count']}** plants stand in a puddle on the main plate. The blobs that remain are leaves leaning over a puddle's edge (a fifth of the plants stand within 10 cm of one) and reflections of plants in the water; which of the two was not counted.

**Plant counts and clearance (P6).** Main plate {p6s['count']} plants ({p6s['result']['weeds']} weeds, {p6s['count'] - p6s['result']['weeds']} moss strings; before 195): in the crown / lanes / keep-clear / doorstep / within 1 m of the fire {p6s['result']['counts']['crown']} / {p6s['result']['counts']['footfall']} / {p6s['result']['counts']['keepclear']} / {p6s['result']['counts']['doorstep']} / {p6s['result']['counts']['fire_1m']}; weeds within 5 cm of a litter piece's centre {p6s['result']['weeds_near_rubbish']} of {p6s['result']['weeds']}. Lockout plate {p6l['count']} plants ({p6l['result']['weeds']} weeds): all zero, {p6l['result']['weeds_near_rubbish']} near litter. The habitat fields are exactly 0 in the zones (street and lockout).

**Walls (main plate).** Red-to-blue ratio of the wall class, left terrace: earlier layers alone {w_l_d['r_over_b_base']}, before the fix {w_l_d['r_over_b_before']}, after {w_l_d['r_over_b_after']}; right terrace {w_r_d['r_over_b_base']}, {w_r_d['r_over_b_before']}, {w_r_d['r_over_b_after']} (the closer to the first number, the warmer). Wall dots lifted more than 1.6 times above base (the pale panels): left {pct(w_l_d['pale_before'], 1)} % before, {pct(w_l_d['pale_after'], 1)} % after; right {pct(w_r_d['pale_before'], 1)} % before, {pct(w_r_d['pale_after'], 1)} % after.

**Not dark mush (P5, per surface class, main plate dry / wet, then lockout dry / wet).**

| class | mean brightness against base: before | after | darkened by a third: before | after | share under 0.10, base | before | after |
|---|---|---|---|---|---|---|---|
| walls (main dry) | {m_d['walls']['mean_ratio_before']} | {m_d['walls']['mean_ratio_after']} | {pct(m_d['walls']['darkened_third_before'], 1)} % | {pct(m_d['walls']['darkened_third_after'], 1)} % | {pct(m_d['walls']['under010_base'], 1)} % | {pct(m_d['walls']['under010_before'], 1)} % | {pct(m_d['walls']['under010_after'], 1)} % |
| walls (main wet) | {m_w['walls']['mean_ratio_before']} | {m_w['walls']['mean_ratio_after']} | {pct(m_w['walls']['darkened_third_before'], 1)} % | {pct(m_w['walls']['darkened_third_after'], 1)} % | {pct(m_w['walls']['under010_base'], 1)} % | {pct(m_w['walls']['under010_before'], 1)} % | {pct(m_w['walls']['under010_after'], 1)} % |
| trims (main dry) | {m_d['trims']['mean_ratio_before']} | {m_d['trims']['mean_ratio_after']} | {pct(m_d['trims']['darkened_third_before'], 1)} % | {pct(m_d['trims']['darkened_third_after'], 1)} % | {pct(m_d['trims']['under010_base'], 1)} % | {pct(m_d['trims']['under010_before'], 1)} % | {pct(m_d['trims']['under010_after'], 1)} % |
| road (main dry) | {m_d['road']['mean_ratio_before']} | {m_d['road']['mean_ratio_after']} | {pct(m_d['road']['darkened_third_before'], 1)} % | {pct(m_d['road']['darkened_third_after'], 1)} % | {pct(m_d['road']['under010_base'], 1)} % | {pct(m_d['road']['under010_before'], 1)} % | {pct(m_d['road']['under010_after'], 1)} % |
| colliery (main dry) | {m_d['colliery']['mean_ratio_before']} | {m_d['colliery']['mean_ratio_after']} | {pct(m_d['colliery']['darkened_third_before'], 1)} % | {pct(m_d['colliery']['darkened_third_after'], 1)} % | {pct(m_d['colliery']['under010_base'], 1)} % | {pct(m_d['colliery']['under010_before'], 1)} % | {pct(m_d['colliery']['under010_after'], 1)} % |
| walls (lockout dry) | {l_d['walls']['mean_ratio_before']} | {l_d['walls']['mean_ratio_after']} | {pct(l_d['walls']['darkened_third_before'], 1)} % | {pct(l_d['walls']['darkened_third_after'], 1)} % | {pct(l_d['walls']['under010_base'], 1)} % | {pct(l_d['walls']['under010_before'], 1)} % | {pct(l_d['walls']['under010_after'], 1)} % |
| walls (lockout wet) | {l_w['walls']['mean_ratio_before']} | {l_w['walls']['mean_ratio_after']} | {pct(l_w['walls']['darkened_third_before'], 1)} % | {pct(l_w['walls']['darkened_third_after'], 1)} % | {pct(l_w['walls']['under010_base'], 1)} % | {pct(l_w['walls']['under010_before'], 1)} % | {pct(l_w['walls']['under010_after'], 1)} % |

Whole plate against base: main dry {m_d['plate_mean_ratio_before']} to {m_d['plate_mean_ratio_after']}, main wet {m_w['plate_mean_ratio_before']} to {m_w['plate_mean_ratio_after']}, lockout dry {l_d['plate_mean_ratio_before']} to {l_d['plate_mean_ratio_after']}, lockout wet {l_w['plate_mean_ratio_before']} to {l_w['plate_mean_ratio_after']}. The plan's lines (M1 at most 25 percent of the class darkened by a third, M2 under-0.10 share up by at most 3 points on walls and trims and 8 on the rest, M3 mean at least 0.88): all met on both plates in both states (the largest rise is the colliery's, +5.4 points on the main plate, +5.2 on the lockout; walls +1.1 and +1.8). The dry walls were over the M1 line before (26.6 percent): now {pct(m_d['walls']['darkened_third_after'], 1)} percent. M5 (distance bands) was not re-run (it fails by design, section 9).

**Joint contrast (the checkers' bands of the main plate at 540 x 960; joint over stone, puddle dots left out in the wet picture), after over base:** dry near {JOINTS['dry near rows 800-960']['after_over_base']}, mid {JOINTS['dry mid rows 700-800']['after_over_base']}, far {JOINTS['dry far rows 600-700']['after_over_base']}; wet near {JOINTS['wet near rows 800-960']['after_over_base']}, mid {JOINTS['wet mid rows 700-800']['after_over_base']}, far {JOINTS['wet far rows 600-700']['after_over_base']} (before: 1.019, 1.001, 1.017; 1.000, 1.027, 1.093). The joints are as visible as without the kit.

**P1 sett joints (the 22 lighting pictures: street {p1s['official']['of']}, lockout {p1l['official']['of']}).** Official count {p1s['official']['passed'] + p1l['official']['passed']} of 22 (street {p1s['official']['passed']} of {p1s['official']['of']}, lockout {p1l['official']['passed']} of {p1l['official']['of']}; the one failure, `lockout_B_heavy`, fails without the kit too); with every dot counted {p1s['all_dots']['passed'] + p1l['all_dots']['passed']} of 22 (before the fix round 20; the three misses are `lockout_B_wet` and `lockout_B_heavy`, which fail without the kit too, and `lockout_E_wet`, which passed before); with the kit's own dots left out too **{p1s['without_kit']['passed'] + p1l['without_kit']['passed']} of 22 (before 18, the line is 20: now met)**; no harsh black grid (largest joint contrast {max(p1s['max_near_contrast'], p1l['max_near_contrast'])}, limit 0.75).

**P2 the wet look.** Street: 3 lines out (before the fix round 6): light E wet road wet/dry {M1S['p2']['wet_to_dry']['main_E_wet']['road']} against {M1S['p2']['base_wet_to_dry']['main_E_wet']['road']} (-0.097; was -0.154), light E heavy {M1S['p2']['wet_to_dry']['main_E_heavy']['road']} against {M1S['p2']['base_wet_to_dry']['main_E_heavy']['road']} (-0.088; was -0.120), light C wet highlight share 0.0361 (line 0.0425; was 0.0337). Lockout: no line out. (The per-element lines were not re-run: they need the layers' own pictures, which this round did not draw.)

**P7 drawing time (best of three, 1536 x 2730 at 48 samples, the card shared with another job).** Street: earlier layers alone {min(ts['base'])} s, everything {min(ts['kit'])} s = **{ts['ratio_best']} times** (before the fix round 2.06; line 1.3). Lockout: {min(tl['base'])} s against {min(tl['kit'])} s = **{tl['ratio_best']} times** (before 1.75). The first picture after putting the kit on: street {ts['kit_look_change'][0]} s look change + {ts['kit'][0]} s first draw, lockout {tl['kit_look_change'][0]} s + {tl['kit'][0]} s (limit 40 s: met; the 1.5 times line is not).

**P8 and the door (the integrated test, `harness/test_weathering_entry.py`, run again after the code changes).**
{entry_line('street')}
{entry_line('lockout')}
{entry_line('courtyard')}

### 12.6 What is still not right, not tested, not sure
* **The stains are still not visible at film size.** The walls are seen edge-on and are nearly black; the run-off streaks, wall-foot damp and washed patches are a few dots wide on the main plate. The streaks are wider and rustier now, but this was not measured against the painter's size (the readable-at-the-painter's-size counts, P3, were not re-run: the first checker said not to spend the round on them, and the layer pictures they need were not drawn). If "stains" must show on the walls of the main plate, the honest answers are to let the painter add them or to move the camera nearer a wall; the ground's dried puddle marks and the rust halos are the stains that do show.
* **Fewer plants** ({p6s['count']} in view of the main camera against 195): the puddle and litter rules keep plants out of the gutter, where the weeds liked to grow. They are small, dim tufts along the kerb foot and the gutter now. `weed_cover` and `gutter_tuft_share` are the dials to raise (the plan's own caps are 2 percent and 8 percent; the look is at 2 and 10).
* The pale dead-grass tufts are still the lightest things on the dark road; `dead_grass_share` is down to 0.08.
* The lockout's plants and the sett joints' open share (7 percent now; the plan's period line says 10 to 20 percent) were not re-checked against the period table (P4 was not re-run).
* Not run: P3 readable at the painter's size, P4 period caps, the per-layer drawing times, M5, the notice and close-road plates at full size, the heavy-rain pictures at plate size. The lamp-post rust (the checker's minor finding: a strong brick red) is unchanged: `iron.rust_bright` was tried at 1.0, 1.4, 1.7 and 3.0 and made no visible difference on the posts, so the look does not name it (the final plates were drawn with 1.4 in the look; taking it out changes nothing that could be seen).
* The whitened steps now read khaki-cream; in deep shade a few look slightly olive.
* **Nothing was painted.** The one cheap chart-plate repaint that the painted-look study asked for is still the next step: whether the painter keeps the dim green plants green, the dull terrace brick red and the cream steps cream is unknown.
* The pack's rubbish picture (`rubbish_heap`) is still the first painter round's (drawn from the earlier, smaller litter); only the new `litter_dist` comes from the second round's litter.

### 12.7 Files changed in the fix round
* Kit code: `harness/runner.py` (views `plan:puddles` and `plan:litter`, `piece_points`), `harness/class_pass.py` (a plain white override), `harness/lint_no_set_names.py` (lists of numbers and camera names), `masks/names.py` (the `litter_dist` row and the `above_water` words), `growth/scatter.py` and `growth/apply_growth.py` (the baked clearance, with the old search as the fallback), `growth/jobs_growth.py`, `masks/check_against_earlier.py` (no street numbers), `walls/steps.py`, `walls/soot.py`, `walls/walls_common.py` (`lift_to` takes a colour made in the nodes), `walls/dials_walls.py`, `ground/dirt.py`, `ground/groundcracks.py`, `ground/dials_ground.py`.
* New: `masks/stamp_pack.py`, `harness/make_plan_pictures.py`.
* Data: `presets/sooty_1926.json` (the table in section 5), `sets/pit_village_street.json` (`legacy.places_grid`, the soot role values of trims and the colliery), the street and lockout packs (`above_water`, new `gp_h.png`, `manifest.json`); `README.md`, `HOW TO USE.md`, `integrate/tune_log.md`.
* Moved out of the kit: the four sidecar files `ground/ground_sets/*.json`, `growth/growth_sets/*.json` (now in `grime_and_growth/fix/retired_sidecars`).
* Work, numbers and the originals of everything that was changed: `street_wet/grime_and_growth/fix/` (`backup/` holds the originals, `keep/` the numbers and the SHA-256 hashes of the PNGs, `plates/` the four final plates as PNG, `work/` the scripts).
"""
text = text.rstrip('\n') + '\n' + sec
open(NOTE, 'w').write(text)
print('written', len(text))
