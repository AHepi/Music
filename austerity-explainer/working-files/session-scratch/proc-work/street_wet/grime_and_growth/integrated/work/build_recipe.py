# Integrator: puts the recipe note together: recipe_A.md (hand-written, sections 1 to 6) + the measuring list + the dial appendix (generated from the dial table dump) + the numbers (from
# the final round's measure files) + what is not done.  python3 -I build_recipe.py
import collections
import json
import os

W = os.path.dirname(os.path.abspath(__file__))
KIT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
OUT = os.path.join(KIT, '15 Recipe - weathering kit - grime, cracks, stains, weeds and moss - how it is made.md')


def jl(path):
    return json.load(open(os.path.join(W, path)))


def entry(which):
    p = os.path.join(W, 'entry_tests', which, 'entry_test.json')
    return json.load(open(p)) if os.path.exists(p) else None


def fmt(v):
    if v is None:
        return ''
    if isinstance(v, float):
        return f'{v:g}'
    return str(v)


def dial_tables():
    d = jl('dials_dump.json')
    out = ['## 8. Every dial (range, default, the street\'s value, the courtyard\'s value, what it does)', '',
           'Generated from the dial table of the finished kit. Every layer also has the six common dials listed first. "street" is `presets/sooty_1926.json`, "courtyard" is `presets/mossy_courtyard_kept.json`. Names are Title Case on the node group (`Film Mult`).', '']
    order = ['soot', 'runoff', 'foot', 'steps', 'wallcracks', 'wallgrowth', 'paint', 'dirt', 'groundcracks', 'groundmoss', 'iron', 'growth']
    for key in order:
        t = d[key]
        out.append(f'### {key}  (slot {t["slot"]}; roles in the plan: {t["meta"].get("roles", "")})')
        out.append('')
        out.append('| dial | range | default | street | courtyard | what it does |')
        out.append('|---|---|---|---|---|---|')
        for r in t['rows']:
            doc = (r.get('doc') or '').replace('|', '/').replace('\n', ' ')
            out.append(f"| `{r['name']}` | {fmt(r['lo'])} to {fmt(r['hi'])} {r.get('unit') or ''} | {fmt(r['default'])} | {fmt(r.get('street'))} | {fmt(r.get('courtyard'))} | {doc} |")
        out.append('')
    return '\n'.join(out)


MEASURES = '''## 7. How it is measured (the scripts, and the pass line each one is)

All pictures are drawn on the rented machine (the street file: 74 lighting and close pictures; the lockout file: 19; plates 1536 x 2730 at 48 samples) and brought back; the measuring scripts are plain Python on those pictures. "Before" is always the earlier layers alone (the second painter round's), drawn in the same run, so nothing but the new parts differs.

| pass line | what it asks | script (in `harness/`, run by `integrated/work/measure_all.py`) |
|---|---|---|
| P1 sett joints still pass | with puddle and litter dots left out and the kit's own dots left in: at least 21 of 22 lighting pictures pass the joint test, nothing that passed before fails, no harsh black grid (joint contrast at most 0.75) | `measure_joints.py` |
| P2 the wet look is kept | wet-over-dry brightness of road, pavement and walls within 0.05 of before, puddle cover within 2 points, shine highlights within 85 to 115 percent, every kit element no brighter wet than dry | `measure_wet.py` |
| P3 readable at the painter's size | each element's marks, at the painter's 0.45 scale, at least 60 percent good, at most 15 percent lost, at most 15 percent crushed, and a minimum number of good marks | `measure_readable.py` (+ `plate_detail_check.py`) |
| P4 nothing wrong for 1926 | no forbidden thing in the look, each element's share inside its period cap, no orange or yellow or bright green outside rust and plants | `measure_period.py`, `coverage.py` |
| P5 the street is not one dark mush | against before, per surface class on each plate: M1 at most 25 percent of the class darkened by a third, M2 the share under plate brightness 0.10 rises by at most 8 points (3 on walls and trims), M3 mean brightness drops by at most 12 percent, M4 spread kept at 85 percent, M5 kit/before brightness in the 5-10, 10-20 and 20-40 m bands stays between 0.80 and 1.00 and within 0.08 band to band | `measure_mush.py` |
| P6 no plants on the crown or lanes | the growth fields are exactly 0 there, no plant stands in those zones, near the fire or on a doorstep, at most 3 percent of weeds within 5 cm of litter | `measure_zones.py` (via `integrated/work/measure_p6.py`) |
| P7 the same drawing time within +30 percent | plate time at most 1.3 times before; the first picture after putting the kit on at most 1.5 times before and never over 40 s | `measure_time.py`, `integrated/work/run_time_*.py` |
| P8 master dial 0 changes nothing, remove restores | each layer at 0 equals the input; all at 0 equals before; remove gives the scene back | `selftests.py` per builder, and `harness/test_weathering_entry.py` for the whole door |
| P9 reuse | the lint finds 0 set names in kit code; both settings files validate; the courtyard takes the same call | `lint_no_set_names.py`, `test_weathering_entry.py` on the courtyard |

'''


def numbers():
    d = jl('r5/measures_kit.json')
    p6 = jl('r5/p6_kit.json')
    tf = {}
    lines = []
    a = lines.append
    a('## 9. The numbers (final settings; the final round is `integrated/work/r5`)')
    a('')
    p1 = d['p1']
    a('### P1 sett joints')
    a(f"* With everything on: **{p1['summary']['official']['passed']} of {p1['summary']['official']['of']}** lighting pictures pass (before the new parts: {p1['base_summary']['official']['passed']} of 22). The one that fails, `lockout_B_heavy` (the lockout in heavy rain, middle road band), failed before too. `lockout_B_wet` now passes (it failed before by 0.005). Nothing that passed before fails now.")
    a(f"* With every dot counted: {p1['summary']['all_dots']['passed']} of 22 (before: {p1['base_summary']['all_dots']['passed']}). Highest joint contrast near the camera {p1['summary']['max_near_contrast']:.2f} (limit 0.75): no harsh black grid. Grid visible in near and middle bands: {p1['summary']['grid_visible_near_and_middle']['count']} of 22 (before: {p1['base_summary']['grid_visible_near_and_middle']['count']}).")
    a(f"* **NOT met: the count with the kit\'s own dots left out too.** The line asks for the same as before (20); it is {p1['summary']['without_kit']['passed']} of 22, failing `lockout_B_dry`, `lockout_B_wet`, `lockout_B_heavy`, `lockout_E_wet`. The kit's own marks cover 31 to 45 percent of the road dots (the ground film's mask is a wide soft area, not a mark), so leaving them out leaves the lockout's middle band with too few joint dots to judge. It says little about the joints themselves.")
    p2 = d['p2']
    a('')
    a('### P2 the wet look')
    base = p2['base_wet_to_dry']
    diffs = {k: round(v['road'] - base[k]['road'], 3) for k, v in p2['wet_to_dry'].items()}
    a(f"* Road wet-over-dry within 0.05 of before in {sum(1 for v in diffs.values() if abs(v) <= 0.05)} of the {len(diffs)} pictures that have a dry twin (10 of the 22). Out: `main_A_heavy` {diffs['main_A_heavy']:+.3f}, `main_E_wet` {diffs['main_E_wet']:+.3f}, `main_E_heavy` {diffs['main_E_heavy']:+.3f} (light E is the brazier glare; the road is 3.7 times brighter wet there, so these are 2 to 4 percent). Pavement `close_A_heavy` +0.052. Walls are within 0.05 in all {len(diffs)} (the kit makes them 0.01 to 0.04 less dark wet than before).")
    a(f"* Highlight share of the wet road (light C wet 0.0337, light D wet 0.0420; the line is 85 to 115 percent of 0.05 = 0.0425 to 0.0575): 2 pictures just under. Puddle cover is unchanged (the kit does not touch the water layer).")
    a(f"* Every kit element no brighter wet than dry: **NOT met**, {len([f for f in p2['failures'] if f.startswith('element')])} of {len(p2['element_wet_dry'])} lines. Soot, run-off and iron come out at 0.8 to 1.15; ground film 0.83 to 1.67; cracks and moss ribbons 1.3 to 3.7. For ground elements the line cannot be met in this light (the whole road is 1.4 to 3.7 times brighter wet); divided by the surface's own wet/dry the ground film is 0.38 to 0.78 (duller than its surface, as intended), cracks 0.92 to 1.11, moss ribbons 0.59 to 1.18, soot 1.01 to 1.10, iron 0.99 to 1.06.")
    a(f"* The plants' wet-over-dry brightness (growth builder's measure): 0.63 to 0.90 against the moss band 0.55 to 0.85; one picture (lighting C wet) over.")
    a('')
    a('### P3 readable at the painter\'s size (scale 0.45, inside each element\'s design zone)')
    a('')
    a('| element (layer) | plate | marks | good | share good | lost | crushed | line |')
    a('|---|---|---|---|---|---|---|---|')
    for tag, e in d['p3']['elements'].items():
        name, cam = tag.split('@')
        a(f"| {name} | {cam} | {e['marks']} | {e['good']} | {(e['share_good'] or 0):.0%} | {(e['share_lost'] or 0):.0%} | {(e['share_crushed'] or 0):.0%} | {'pass' if e['passed'] else 'FAIL'} |")
    a('')
    a('Plain reading: **only the weeds and moss cushions pass** (main 70 percent good, lockout 100 percent; the notice camera 45 percent, which looks down on a lit pavement so the plants have no contrast, fails). Everything else fails the 60 percent line: the walls are dark and seen almost edge-on, so 41 to 48 percent of the soot patches and 63 percent of the notice camera\'s run-off streaks are lost, and the main camera has no run-off mark and no whitened step inside the zone. Cracks gained marks when made stronger (36 good on the main plate against 28 before; 110 against 71 on the notice plate) but most marks stay faint. **Nothing was painted**: how many of these marks survive the repaint is not known.')
    a('')
    a('### P4 nothing wrong for 1926')
    a('* Forbidden things: none (no graffiti, road lines, studs, bins, dishes, oil, trench patches, flower boxes, lichen; `lichen_amount` 0).')
    a('* Orange or yellow outside rust and plants, share of the changed dots (limit 0.05 percent): main 0.05, notice 0.10, close road 0.24, lockout 0.12 percent. **Over the line** (main by a hair). The brightened warm-lit brick and the dusty-pale wall foot are the likely cause; no bright green (0.0).')
    a('* Soot "on 85 to 100 percent of wall area": the measure reads the soot layer\'s Mask, which is the pale washed patches (14.5, 21 and 14.7 percent of the wall: the plan wants 15 to 25), not the film (which is on every wall), so the line is not a fair test of this layer; run-off streaks 1.5 to 2.8 percent of wall area (the plan wants 3 to 6): **under**.')
    a('* Not automated, not measured by anyone: washed share per house, streak pairs at sills, splash band length, whitened steps share, flag and kerb damage shares (the ground builder measured them on plan pictures: fine cracks 10.4 percent, broken 2.5, tilted 3.2, kerb chips 31, disturbed setts 4.9, open joints 15.7, tar 0.7, moss in kerb and gutter joints 10.6 percent, all inside their caps; chipped corners not counted), tar, weed cover, whitewash. A fresh person looking at eight 100 percent crops has not been done.')
    a('')
    a('### P5 the street is not one dark mush')
    a('Against before, on the four plates (main, lockout, notice, close road), every surface class:')
    a('* **M1 to M4 all pass.** Darkened by a third: walls 0.12 to 0.23 of the class (limit 0.25), everything else at most 0.05. Share under plate brightness 0.10: walls and trims go DOWN (-3.4 to -6.6 and up to +1.0 points; the line allows +3), road at most +0.8, pavement, kerb, iron, roofs, chimneys, colliery within +1.3. Mean brightness: walls 0.98 to 1.05, road 0.97 to 1.00, iron 0.97, nothing under 0.966 (limit 0.88); the whole plate 0.984 to 1.003 (limit 0.92). Spread inside the class: lowest 0.91 (chimneys), road 0.93 (limit 0.85).')
    a('* **M5 is NOT met.** The upper limit of 1.00 is broken wherever the kit LIGHTENS a class (pale washed patches, pale streaks, whitened steps): walls 10 to 20 m 1.06 to 1.12, trims 1.00 to 1.76 (the close camera sees few of them), roofs and chimneys 1.0 to 1.13, road 1.01 at most. Walls differ by more than 0.08 from band to band (lockout 0.13, notice 0.16, close road 0.16). Nothing is below 0.90. This is the cost of the "pale marks on dark walls" design: the walls read at 10 to 20 m because the mid-distance wall is a little brighter than before, while the 20 to 40 m wall is 0.90 to 0.99. Fixing it means lowering `washed_pale` or `washed_share`, which would lower the soot readability that already fails.')
    a('* The `paint` layer is off (it was the only layer that failed M2 to M4).')
    a('')
    a('### P6 no plants on the crown, the lanes, the doorsteps')
    a('* The moss, weed, lichen and algae fields are exactly 0.0 in the crown, the traffic lanes and the keep-clear strips (street and lockout).')
    for n in ('plate_main_A_wet', 'plate_notice_A_wet', 'plate_close_road_A_wet', 'plate_lockout_B_wet'):
        r = p6[n]
        a(f"* {n.replace('plate_', '').replace('_', ' ')}: {r['count']} plants, in the crown / lanes / keep-clear / doorstep / within 1 m of the fire: {r['result']['counts']['crown']} / {r['result']['counts']['footfall']} / {r['result']['counts']['keepclear']} / {r['result']['counts']['doorstep']} / {r['result']['counts']['fire_1m']}; weeds within 5 cm of litter: {r['result']['weeds_near_rubbish']} of {r['result']['weeds']}.")
    a('* Plants standing inside puddles: 36 percent of the plants in view of the main camera (32 of 88; section 3.2, item 2). Not a pass line, but the most visible fault left.')
    a('')
    a('### P7 drawing time (plate 1536 x 2730, 48 samples, best of three, the rented card shared with another job)')
    a('* Street main camera: before 2.19 s, everything on 4.52 s (**2.06 times**; limit 1.3). Lockout camera: 3.18 s against 5.58 s (**1.75 times**). NOT met.')
    a('* Per layer alone on the street plate (before = 2.15 s): iron +0 percent, steps +1, runoff +2, groundcracks +2, dirt +3, groundmoss +3, foot +4, soot +5, wallcracks +5, wallgrowth +6, **growth +70** (3.65 s: the litter clearance, section 3.2 item 1; +0.5 percent without it). The plan had walls +8, ground +8, growth +10 percent.')
    a('* First picture after putting the kit on (shader build plus the first draw): street 19.5 + 5.1 = about 25 s, lockout 20.0 + 6.3 = about 26 s (limit 40 s: met; the line of 1.5 times the before picture, about 4 s, NOT met). One lockout round measured 77 s once, while the machine was busy with two of my runs at once.')
    a('* Plants in a picture: 195 to 407 (limit 2,500).')
    a('')
    a('### P8 master dial 0 and removing (the integrated test, `harness/test_weathering_entry.py`, 270 x 480 pictures on the rented machine)')
    rows = []
    for which in ('street', 'lockout', 'courtyard'):
        e = entry(which)
        if not e or e['errors']:
            rows.append(f'* {which}: the test did not finish ({(e["errors"][0][-200:] if e and e["errors"] else "no result")}).')
            continue
        t = e['tests']
        m0 = t['master_0_equals_earlier_only']
        lf = t.get('leftovers')
        rows.append(f"* **{which}**: all master dials at 0 against the earlier layers alone: {m0['dots_over_one_step'] * 100:.2f} percent of dots more than one step apart (largest difference {m0['max_difference']:.3f} of full brightness); two draws of one state: {t['determinism']['dots_over_one_step'] * 100:.2f} percent apart; after `remove()` the picture of the scene as it was: {t['remove_all']['picture']['dots_over_one_step'] * 100:.2f} percent apart; apply and remove twice: node counts {t['apply_remove_twice_same_node_count']['node_counts']} ({'the same' if t['apply_remove_twice_same_node_count']['same'] else 'NOT the same'}); kit node groups left behind: {len(lf) if lf is not None else '?'}; the kit changes {t['kit_changes_the_picture']['dots_over_one_step'] * 100:.0f} percent of the dots; each group switched off alone changes the picture (walls {t['group_off']['walls']['dots_over_one_step'] * 100:.0f}, ground {t['group_off']['ground']['dots_over_one_step'] * 100:.0f}, growth {t['group_off']['growth']['dots_over_one_step'] * 100:.1f} percent of dots).")
    a('\n'.join(rows))
    a('* The courtyard\'s master 0 is not exact: the add-on\'s stones go through an adapter box (a rebuilt Principled BSDF) and EEVEE draws it up to one step of 255 differently on about 0.5 percent of dots (a few dots up to 0.09). In Cycles the adapter is identical (the foundation measured it).')
    a('* The builders\' own isolation tests (a layer alone changes only its own roles) passed on the street, the lockout file and the courtyard in their folders; runoff on the courtyard cannot be tested (it draws nothing there).')
    a('')
    a('### P9 reuse')
    a('* The lint finds **0 hits** over `apply/ masks/ harness/ walls/ ground/ growth/` and the new `apply_weathering.py`. Both settings files validate (0 errors, 0 warnings for the street). The same call `aw.apply(...)` ran on the courtyard scene without a crash (12 layers registered; walls and ground layers went into 4 to 103 materials, the shader-group stones through the adapter; the growth layer is separate 3D pieces and is not counted in materials), with the two settings sections (`ground`, `growth`) moved into the set files and the courtyard looks carrying the growth layer\'s courtyard values.')
    a('')
    a('### P10 the "behind" plate')
    a('* The lockout plate with the props hidden differs from the plate with props in 25.7 percent of the dots by more than 2 steps (the plan asked 1 percent). Before the kit it is 26.0 percent: the hidden props change the light and the glare, so this is not the kit; the line cannot be met even by the earlier layers.')
    a('')
    a('### P11 hygiene')
    a('* Written: only `kits/weathering/` (the new files and the changes listed in section 11) and `street_wet/grime_and_growth/integrated/`, plus the pictures folder. Not written: the film project, `set_copy`, `street_wet/tools`, `relief_and_rubbish`, `painter_round_2`, `painter_test`, `japanese-courtyard`, the add-on folder. The lockout file and the courtyard file were only opened, never saved. No commit, no push, no paid call, no machine stopped, `~/.runpod` not touched. The integrated folder is under its 150 MB limit; free disk stayed above 0.9 GB (lowest 0.91).')
    return '\n'.join(lines)


TAIL = '''
---

## 10. What is not done, not tested, not sure

**Not done.**
* The plants cannot see the water layer's puddles (36 percent of the plants of the main plate stand in one). Fix: the water layer hands its puddle field to the plants as a ground-plan picture.
* The litter clearance of the plants costs +1.5 s a plate with the second round's 58,753 litter pieces. A cheaper clearance (a ground-plan picture of where litter lies instead of a nearest-point question) is not built.
* `paint` is untuned and off.
* The wet-over-dry line for kit elements on the road cannot be met as written; it should compare an element with its own surface.
* M5's upper limit (1.00) cannot be met by a design that lightens walls on purpose; either the line or the design has to give.
* The walls' water-film cut in `wallcracks` is not done (an unexplained difference at amount 0 when the coat is changed); the cracks cut roughness and shine only.
* `Kit.materials_for` should know the water layer's copies (the walls builder patches it on the instance).
* The courtyard has no wall sheets, no plate camera, no lighting rigs and no test set yet; `runoff` draws nothing there.

**Not tested.**
* Nothing was painted. Whether the painter keeps the green plants green, keeps a 3 to 5 dot crack, or turns the pale washed patches into plaster, is unknown (the chart plate for the Paint step was not drawn here).
* The lockout "behind" plate and the notice and close-road plates were drawn and measured, but no fresh person has looked at eight 100 percent crops and no period expert has read them.
* Cycles, heavy-rain pictures at plate size, and lighting E at plate size.
* The second courtyard look (`mossy_courtyard_neglected`), and any courtyard picture beyond the 600 x 400 test pictures.
* A fresh rented machine that has forgotten the kit.

**Not sure.**
* Whether the soot is enough, or too much, for the film: the plate's mean brightness stays within 1.1 percent of before, but the right terrace goes noticeably darker and greyer while the left row hardly changes, and the whitened steps come out cold blue-grey under the night light.
* The amounts (1926 weeds, moss, cracks) are all judgement.
* Whether a 4.5 dot crack of contrast 0.16 looks like a crack or a scratch once painted.
* Whether the ground film's pale patches read as dirt or as a smear on the wet road (the main plate's near road shows large soft pale shapes).

## 11. What the integrator changed in the kit (everything outside the three builders' folders)

* New: `apply_weathering.py` (the door), `street_weathering.py` (the street wrapper), `harness/test_weathering_entry.py`, `integrate/pin_round2.py`, `integrate/legacy_round2/` and `integrate/legacy_round2.json` (the second painter round's earlier layers), `integrate/tune_log.md`.
* `harness/legacy_stack.py`: which pinned copy is used is chosen by the set (`legacy.pinned_root`) or by `WK_LEGACY_PINNED`; the old default is unchanged.
* `harness/lint_no_set_names.py`: also scans `apply_weathering.py`.
* `masks/ground_plan.py`: the step finder reads two optional keys (`max_height_m`, `max_extent_m`); the street and lockout packs were rebuilt (`masks/packs/pit_village_street/...`; the old packs are not kept).
* `sets/pit_village_street.json`: `ground` and `growth` sections moved in from the builders' sidecar files; `legacy.pinned_root`; `geometry.steps.max_height_m` and `max_extent_m`; `apply.soot.role_dials` (trims, colliery); `apply.paint.roles` emptied.
* `sets/japanese_courtyard.json`: `ground` and `growth` sections moved in.
* `presets/sooty_1926.json`: the dial values of section 5. `presets/mossy_courtyard_*.json`: the growth layer's courtyard values.
* The builders' sidecar files (`ground/ground_sets`, `growth/growth_sets`, `ground/looks_ground`, `growth/looks_growth`) are still there and are only read when a set file has no such section.
* Nothing in `walls/`, `ground/`, `growth/` was edited.
'''


def main():
    a = open(os.path.join(W, 'recipe_A.md')).read()
    text = a + '\n---\n\n' + MEASURES + '\n' + dial_tables() + '\n---\n\n' + numbers() + '\n' + TAIL
    open(OUT, 'w').write(text)
    print('written', OUT, len(text), 'characters')


if __name__ == '__main__':
    main()
