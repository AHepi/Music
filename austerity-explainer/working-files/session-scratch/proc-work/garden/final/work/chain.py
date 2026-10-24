# What this does (plain words): STEP 5 chain. Opens the starting garden file (never saved over), runs the five stages one after another
# (light 'cameras' first so the weathering kit finds a camera called 'photo', then shapes, life, surfaces with the weathering kit, light),
# takes a full fingerprint of the scene before the first stage and after each one, checks that each stage only touched what it owns,
# saves garden_<look>.blend (compressed, pictures packed for the real look) and writes a JSON report.
# Run: blender -b --disable-autoexec START.blend -P chain.py -- LOOK OUT.blend REPORT.json [--skip shapes,life,...] [--no-pack]
import bpy, sys, os, json, time, hashlib, traceback, re
import numpy as np

sys.dont_write_bytecode = True
FINAL = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/final'
STAGE = FINAL + '/stage'
MAPS = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/surfaces/maps'
sys.path.insert(0, STAGE)

argv = sys.argv[sys.argv.index('--') + 1:]
LOOK, OUT, REPORT = argv[0], argv[1], argv[2]
SKIP = []
if '--skip' in argv:
    SKIP = [s for s in argv[argv.index('--skip') + 1].split(',') if s]
PACK = '--no-pack' not in argv
bpy.context.preferences.filepaths.save_version = 0


def say(*a):
    print('[chain]', *a, flush=True)


# --------------------------------------------------------------------------------------------- fingerprints
def mat_sig(m):
    nt = m.node_tree
    if nt is None:
        return ('none',)
    kinds = sorted(n.bl_idname + ':' + n.name for n in nt.nodes)
    h = hashlib.md5(('|'.join(kinds)).encode()).hexdigest()[:10]
    vals = []
    for n in nt.nodes:
        for s in n.inputs:
            if hasattr(s, 'default_value'):
                try:
                    v = s.default_value
                    v = tuple(round(x, 3) for x in v) if hasattr(v, '__len__') else round(float(v), 3)
                except Exception:
                    v = None
                vals.append((n.name, s.identifier, v))
    vh = hashlib.md5(repr(vals).encode()).hexdigest()[:10]
    return (len(nt.nodes), len(nt.links), h, vh)


def fingerprint():
    bpy.context.view_layer.update()
    fp = {'objects': {}, 'materials': {}, 'groups': {}, 'lights': {}, 'cameras': {}, 'world': None, 'render': {}, 'images': len(bpy.data.images)}
    for ob in bpy.data.objects:
        d = {'type': ob.type, 'owner': ob.get('garden_owner'), 'role': ob.get('garden_role'),
             'coll': sorted(c.name for c in ob.users_collection if not c.name.startswith('G4 ') or c.name == 'G4 light'),
             'mw': tuple(round(x, 4) for row in ob.matrix_world for x in row),
             'hide': (ob.hide_render, ob.hide_viewport),
             'mods': tuple((m.type, m.name, (m.node_group.name if getattr(m, 'node_group', None) else None)) for m in ob.modifiers),
             'slots': tuple((s.material.name if s.material else None) for s in ob.material_slots),
             'parent': ob.parent.name if ob.parent else None,
             'lg': getattr(ob, 'lightgroup', '')}
        if ob.type == 'MESH':
            me = ob.data
            n = len(me.vertices)
            co = np.empty(n * 3, dtype=np.float32)
            me.vertices.foreach_get('co', co)
            sm = np.empty(len(me.polygons), dtype=np.bool_)
            me.polygons.foreach_get('use_smooth', sm)
            d['geo'] = (n, len(me.polygons), hashlib.md5(np.round(co, 4).tobytes()).hexdigest()[:12])
            d['smooth'] = int(sm.sum())
        elif ob.type == 'CURVE':
            d['geo'] = (len(ob.data.splines), sum(len(s.points) + len(s.bezier_points) for s in ob.data.splines))
        fp['objects'][ob.name] = d
    for m in bpy.data.materials:
        fp['materials'][m.name] = mat_sig(m)
    for g in bpy.data.node_groups:
        fp['groups'][g.name] = (len(g.nodes), len(g.links))
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT':
            L = ob.data
            fp['lights'][ob.name] = (L.type, round(L.energy, 3), tuple(round(c, 3) for c in L.color), ob.hide_render)
        if ob.type == 'CAMERA':
            fp['cameras'][ob.name] = (round(ob.data.lens, 2), tuple(round(x, 4) for row in ob.matrix_world for x in row))
    w = bpy.context.scene.world
    if w and w.node_tree:
        fp['world'] = (w.name, len(w.node_tree.nodes), len(w.node_tree.links))
    sc = bpy.context.scene
    fp['render'] = {'engine': sc.render.engine, 'res': (sc.render.resolution_x, sc.render.resolution_y), 'samples': getattr(sc.cycles, 'samples', None),
                    'view': sc.view_settings.view_transform, 'look': sc.view_settings.look, 'exposure': round(sc.view_settings.exposure, 3)}
    return fp


def diff(a, b):
    r = {k: [] for k in ('objects_new', 'objects_deleted', 'geometry', 'transform', 'modifiers', 'slots', 'visibility', 'shading', 'collection', 'parent',
                         'materials_new', 'materials_deleted', 'materials_changed', 'groups_new', 'groups_deleted', 'groups_changed',
                         'lights_changed', 'cameras_changed')}
    ao, bo = a['objects'], b['objects']
    r['objects_new'] = sorted(set(bo) - set(ao))
    r['objects_deleted'] = sorted(set(ao) - set(bo))
    for n in set(ao) & set(bo):
        x, y = ao[n], bo[n]
        if x.get('geo') != y.get('geo'):
            r['geometry'].append(n)
        if x['mw'] != y['mw']:
            r['transform'].append(n)
        if x['mods'] != y['mods']:
            r['modifiers'].append(n)
        if x['slots'] != y['slots']:
            r['slots'].append(n)
        if x['hide'] != y['hide']:
            r['visibility'].append(n)
        if x.get('smooth') != y.get('smooth'):
            r['shading'].append(n)
        if x['coll'] != y['coll']:
            r['collection'].append(n)
        if x['parent'] != y['parent']:
            r['parent'].append(n)
    am, bm = a['materials'], b['materials']
    r['materials_new'] = sorted(set(bm) - set(am))
    r['materials_deleted'] = sorted(set(am) - set(bm))
    r['materials_changed'] = sorted(n for n in set(am) & set(bm) if am[n] != bm[n])
    ag, bg = a['groups'], b['groups']
    r['groups_new'] = sorted(set(bg) - set(ag))
    r['groups_deleted'] = sorted(set(ag) - set(bg))
    r['groups_changed'] = sorted(n for n in set(ag) & set(bg) if ag[n] != bg[n])
    r['lights_changed'] = sorted(n for n in set(a['lights']) | set(b['lights']) if a['lights'].get(n) != b['lights'].get(n))
    r['cameras_changed'] = sorted(n for n in set(a['cameras']) | set(b['cameras']) if a['cameras'].get(n) != b['cameras'].get(n))
    r['world_changed'] = a['world'] != b['world']
    r['render_changed'] = {k: (a['render'].get(k), b['render'].get(k)) for k in b['render'] if a['render'].get(k) != b['render'].get(k)}
    for k in list(r):
        if isinstance(r[k], list):
            r[k] = sorted(r[k])
    return r


# --------------------------------------------------------------------------------------------- ownership rules (plan section 7)
LIFE_MAY_TOUCH = re.compile(r'^(Maple |Pine |Bamboo |Fallen leaves|Lily pads|Lotus blossoms|Pond water|Astra / moss grouped bodies|Astra / Courtyard receiving ground|Astra / pebbles grouped bodies)')
LIGHT_MAY_TOUCH = re.compile(r'^(Hills|Dark plain|Camera|photo|veranda|Focus|Lantern window glow|Rim light|Roof lift|Golden hour sun|Cool sky fill|Lantern light)')
SHAPES_NOT = re.compile(r'^(Maple |Pine |Bamboo |Fallen leaves|Lily pads|Lotus blossoms|Pond water|Astra / moss|Hills|Dark plain|Camera|photo)')


def life_or_light_ok(stage, obj, ob_fp):
    own = ob_fp.get('owner')
    if stage == 'life':
        return own == 'life' or bool(LIFE_MAY_TOUCH.match(obj))
    if stage == 'light':
        return own == 'light' or bool(LIGHT_MAY_TOUCH.match(obj))
    return False


def check_stage(stage, d, fp_before, fp_after):
    bad = []
    for kind in ('geometry', 'transform', 'modifiers', 'visibility', 'collection', 'parent'):
        for n in d[kind]:
            ob = fp_after['objects'][n]
            if stage == 'shapes':
                if SHAPES_NOT.match(n) and ob.get('owner') != 'shapes':
                    bad.append((kind, n))
            elif not life_or_light_ok(stage, n, ob):
                bad.append((kind, n))
    for n in d['shading']:
        ob = fp_after['objects'][n]
        if stage == 'shapes':
            if SHAPES_NOT.match(n):
                bad.append(('shading', n))
        elif not life_or_light_ok(stage, n, ob):
            bad.append(('shading', n))
    if stage == 'surfaces':
        for n in d['objects_new'] + d['objects_deleted']:
            bad.append(('object added/removed', n))
    if stage in ('surfaces', 'shapes', 'life'):
        if d['lights_changed'] or d['cameras_changed'] or d['world_changed'] or d['render_changed']:
            bad.append(('lights/cameras/world/render', str((d['lights_changed'], d['cameras_changed'], d['world_changed'], d['render_changed']))[:300]))
    if stage in ('shapes', 'life', 'light'):
        for n in d['objects_new']:
            if fp_after['objects'][n]['type'] == 'CAMERA' and d['objects_deleted']:
                continue                                  # a camera rename (Camera -> photo) shows as one new and one deleted object
            if fp_after['objects'][n].get('owner') != stage:
                bad.append(('new object not tagged garden_owner=' + stage, n))
    return bad


KIT_NAMES = ['photo', 'Golden hour sun', 'Lantern window glow', 'Hall posts', 'Back wall, left', 'Back wall, right', 'Right wall behind hall',
             'Stone plinth', 'Hall roof', 'Raked gravel court', 'Pond water', 'Maple leaves', 'Lantern base', 'Lantern cap']
KIT_PATTERNS = [r'^Rock \d+$', r'^Stepping stone \d+$', r'^Pond edge stone \d+$', r'^Lantern (base|post|gallery|firebox|cap)$', r'^Astra / varied planks']


def final_checks(start_fp, fp):
    out = {}
    names = set(fp['objects'])
    out['kit_names_missing'] = [n for n in KIT_NAMES if n not in names]
    out['kit_patterns_matching'] = {p: sum(1 for n in names if re.match(p, n)) for p in KIT_PATTERNS}
    lost, empty, placeholders = [], [], []
    for n, d in fp['objects'].items():
        if d['type'] not in ('MESH', 'CURVE'):
            continue
        s0 = start_fp['objects'].get(n)
        if s0 is not None:
            had = [m for m in s0['slots'] if m]
            now = [m for m in d['slots'] if m]
            if had and len(now) < len(had):
                lost.append(n)
        if d['type'] == 'MESH' and d['geo'][1] > 0 and not any(d['slots']) and not d['mods']:
            empty.append(n)
        for m in d['slots']:
            if m and m.startswith('GARDEN placeholder'):
                placeholders.append((n, m))
    out['objects_that_lost_materials'] = lost
    out['mesh_objects_without_any_material'] = empty
    out['placeholder_materials_left'] = placeholders
    out['objects_total'] = len(fp['objects'])
    out['materials_total'] = len(fp['materials'])
    return out


# --------------------------------------------------------------------------------------------- run
REP = {'look': LOOK, 'skip': SKIP, 'stages': {}, 'violations': {}, 'failed': [], 'blender': bpy.app.version_string, 'start_file': bpy.data.filepath}
t_all = time.time()
start_fp = fingerprint()
cur = start_fp
REP['start'] = {'objects': len(start_fp['objects']), 'materials': len(start_fp['materials']), 'node_groups': len(start_fp['groups'])}
touched_by = {}


def _short(res):
    try:
        txt = json.dumps(res, default=str)
    except Exception:
        return str(res)[:3000]
    if len(txt) > 12000 and isinstance(res, dict):
        return {k: (v if len(json.dumps(v, default=str)) < 1500 else '<%d chars>' % len(json.dumps(v, default=str))) for k, v in res.items()}
    return json.loads(txt) if len(txt) <= 12000 else txt[:3000]


def run_stage(name, fn, skipname=None):
    global cur
    if (skipname or name) in SKIP:
        say('SKIP', name)
        REP['stages'][name] = {'skipped': True}
        return
    t = time.time()
    say('=== STAGE', name, LOOK)
    err = None
    res = None
    try:
        res = fn()
    except Exception:
        err = traceback.format_exc()
        say('STAGE FAILED', name, '\n', err)
    secs = round(time.time() - t, 1)
    new = fingerprint()
    d = diff(cur, new)
    bad = check_stage('light' if name == 'light_cameras' else name, d, cur, new)
    for kind in ('geometry', 'transform', 'modifiers', 'slots', 'visibility', 'shading'):
        for n in d[kind]:
            touched_by.setdefault(n, []).append((name, kind))
    for n in d['objects_new']:
        touched_by.setdefault(n, []).append((name, 'new'))
    summary = {k: (len(v) if isinstance(v, list) else v) for k, v in d.items()}
    REP['stages'][name] = {'seconds': secs, 'error': err, 'summary': summary,
                           'diff': {k: (v if not isinstance(v, list) or len(v) <= 300 else v[:300] + ['... %d more' % (len(v) - 300)]) for k, v in d.items()},
                           'violations': bad, 'returned': _short(res)}
    if err:
        REP['failed'].append(name)
    if bad:
        REP['violations'][name] = bad
    say(name, 'seconds', secs, 'summary', json.dumps(summary), 'violations', len(bad))
    cur = new


run_stage('light_cameras', lambda: __import__('stage_light').apply({'look': LOOK, 'steps': ['cameras']}), 'light')
run_stage('shapes', lambda: __import__('stage_shapes').apply({'look': LOOK}))
run_stage('life', lambda: __import__('stage_life').apply({'look': LOOK}))
run_stage('surfaces', lambda: __import__('stage_surfaces').apply({'look': LOOK, 'maps_dir': MAPS, 'pack_images': PACK and LOOK == 'real', 'verbose': True}))
run_stage('light', lambda: __import__('stage_light').apply({'look': LOOK}))

REP['touched_by_more_than_one_stage'] = {n: v for n, v in touched_by.items()
                                         if len({s for s, _ in v}) > 1 and not all(s in ('light_cameras', 'light') for s, _ in v)}
REP['final'] = final_checks(start_fp, cur)
REP['seconds_total'] = round(time.time() - t_all, 1)
REP['mesh_faces_in_real_meshes'] = sum(len(ob.data.polygons) for ob in bpy.data.objects if ob.type == 'MESH')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True, copy=True)
REP['saved'] = OUT
REP['saved_bytes'] = os.path.getsize(OUT)
json.dump(REP, open(REPORT, 'w'), indent=1, default=str)
say('SAVED', OUT, REP['saved_bytes'], 'bytes; failed stages:', REP['failed'], '; stages with violations:', list(REP['violations']))
say('CHAIN_DONE', LOOK, REP['seconds_total'], 's')
