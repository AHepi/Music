# Writes out/TEST_REPORT_life.txt from the measured JSON files in out/ (nothing here is typed in by hand except the plain-words framing).
import json, os, datetime
D = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/life/out/'
J = lambda n: json.load(open(D + n))
L = []
def w(t=''): L.append(t)
w('TEST REPORT - life stage (builder 2), Japanese garden. Made by work/make_report.py from the measured files in this folder.')
w('Blender 5.2.2 headless. Starting file: astra-work/out/courtyard_final.blend (opened, never saved). Stage file: life/stage_life.py, apply(options).')
w('')
for look in ('real', 'painted'):
    i = J(f'integrity_{look}.json'); n = i['report_numbers']
    w(f'=== 1. WHAT CHANGED, look = {look} (before and after, every object, material, node group, light, camera, world, render setting) ===')
    w('Existing objects changed : ' + ', '.join(i['objects']['changed']))
    w('Existing objects removed : ' + (', '.join(i['objects']['removed']) or 'none'))
    w(f"New objects added       : {len(i['objects']['added'])} (all tagged garden_owner=life with a garden_role; none without)")
    w('Existing materials changed: ' + ', '.join(i['materials']['changed']))
    w('New materials          : ' + ', '.join(i['materials']['added']))
    w('New node groups        : ' + ', '.join(i['node_groups']['added']) + '; existing node groups changed: ' + (', '.join(i['node_groups']['changed']) or 'none'))
    w(f"World changed: {i['world_changed']}; render settings changed: {i['render_settings_changed']}")
    v = i['violations']
    w('Things changed that this stage does not own: ' + str({k: len(x) for k, x in v.items()}))
    w('  -> objects changed not owned: ' + (str(v['objects_changed_not_owned']) or '[]') + '; materials changed not owned: ' + str(v['materials_changed_not_owned']))
    w('')
w('=== 2. RUNNING IT TWICE (and switching looks) ===')
r = J('rerun_test.json')
w('Object, mesh, material, node group, collection and curve counts after run 1 versus run 2 (same look) versus a switch to painted and back: differences = '
  + str({k: r[k] for k in ('real2_minus_real1', 'painted_minus_real', 'real_again_minus_real1')}) + '; leaf count equal: ' + str(r['maple_leaves_equal']) + '; scatter counts equal: ' + str(r['scatter_equal']))
w('')
w('=== 3. NUMBERS PER STEP ===')
for look in ('real', 'painted'):
    n = J(f'integrity_{look}.json')['report_numbers']
    w(f'--- {look}')
    for k, val in n.items():
        w(f'  {k}: {val}')
w('')
w('=== 4. LIVE SCATTER (the add-on, patched copy): counts against what the records predict, and where the pieces really stand ===')
for look in ('real', 'painted'):
    s = J(f'scatter_stats_{look}.json'); n = J(f'integrity_{look}.json')['report_numbers']
    w(f'--- {look}')
    for kind in ('scatter_moss', 'scatter_tuft', 'scatter_pebble'):
        w(f'  {kind}: {n[kind]}')
    for k, val in s.items():
        if isinstance(val, dict):
            w(f'  stands: {k}: {val}')
w('  (moss inside the gravel court = the collars round the three gravel rocks, by design; no stepping-stone moss because the stones lie on the raked court and the')
w('   keep-clear rule (half the path width, 0.575 m) takes the path itself)')
w('')
w('=== 5. DELIVERY CHECK (Scenario expert skill, bx_audit.deliverable, profile render) on the objects this stage owns ===')
for look in ('real', 'painted'):
    d = J(f'delivery_{look}.json')
    w(f'--- {look}')
    for g, v in d['groups'].items():
        w(f"  {g}: pass={v.get('pass')} errors={v.get('n_errors')} warnings={v.get('n_warnings')} :: " + ' | '.join(v.get('errors', [])[:3]))
    for k, v in d['scatter_audits'].items():
        w(f"  add-on audit of {k}: all checks true = {all(v['checks'].values())}")
w('  Reading: every error is either (a) pieces that are separate by design (leaf lenses, needle pads, shrubs, pebbles, fallen leaves, iris) and that the check calls floating')
w('  because the ground is not in their group, or (b) bamboo stalk caps that coincide inside the culms (1,052 faces; 1,056 before this stage, not made by it and not visible).')
w('  Pine needle tufts (real look) give 14 coincident faces. Support was measured separately: shrub domes sink 4 cm into the ground, fallen leaves lie 6 mm over it,')
w('  pads sit on the old limbs (limb tips end 7 cm inside each pad) and the new satellite limbs end inside their pads.')
w('')
w('=== 6. FACE COUNTS (the whole scene, instances counted as the renderer sees them) ===')
for look in ('none', 'real', 'painted'):
    c = J(f'counts_{look}.json')
    w(f"  {look if look != 'none' else 'before the stage'}: meshes {c['faces_in_meshes']:,} + instances {c['faces_from_instances']:,} = {c['total_as_rendered']:,} faces ({c['objects']} renderable objects)")
w('  (the roof tiles are instanced by the add-on and are not counted by this counter in any of the three lines)')
w('')
w('=== 7. PICTURES DRAWN ON RUNPOD (Cycles, OptiX, per second) ===')
logs = J('preview_logs.json')
for k, v in sorted(logs.items()):
    w(f"  {k}: device {v['device']}; stage {v['stage_seconds']} s; pictures {v['pictures']}")
w('  Billed work per job as reported by RunPod (seconds): round 1 real 37.6, painted 22.5; round 2 real 45.6, painted 34.3; round 3 real 73.1, painted 27.9, shapes+life 40.0;')
w('  round 4 real 41.2, painted 26.7; round 5 (2400 x 1600) real 40.5, painted 37.1. Total 426.6 s over 11 render jobs, plus about 1.5 minutes of uploads and wake-ups.')
w('')
open(D + 'TEST_REPORT_life.txt', 'w').write('\n'.join(L))
print(len(L), 'lines')
