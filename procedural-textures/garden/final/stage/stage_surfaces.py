# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# BUILDER 3 "SURFACES" for the Japanese garden. It changes MATERIALS ONLY (no geometry, no lights, no world, no camera) on the already-open starting scene
# (courtyard_final.blend, or that scene after the shapes and life stages have run):
#
#     import sys; sys.path.insert(0, '<this folder>')
#     import stage_surfaces
#     stage_surfaces.apply({'look': 'real'})        # photographed surfaces (Poly Haven, CC0) + the weathering kit on top
#     stage_surfaces.apply({'look': 'painted'})     # hand-painted passages, flat colour, no scans, no kit
#
# options (all optional):
#   look            'real' (default) or 'painted'
#   weathering      real look only: put the weathering kit on top (default True)
#   weathering_look the kit's look file (default 'mossy_courtyard_kept')
#   maps_dir        where the Poly Haven pictures are (default <this folder>/maps)
#   pack_images     pack the pictures into the .blend (default False; the final step packs when it saves)
#   addon_dir       painted look: folder of the Astra add-on 0.2.1 (read only) to use its pigment tool on wood and plaster (default none = hand-made nodes only)
#   verbose         print the report (default True)
#
# Every object is found by its name (the same patterns the weathering kit uses) or by its custom property garden_role (set by builders 1 and 2 on the objects they
# create); a placeholder material 'GARDEN placeholder <role>' is replaced by that role's material. Objects that glow, leaves, water, hills and the sky are never
# touched. Re-running is safe: materials are rebuilt in place, nothing is added twice.
import bpy
import os
import re
import sys
import time
import json

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

import surf_kit as K  # noqa: E402
import importlib  # noqa: E402

OWNER = 'surfaces'

# ------------------------------------------------------------------------------------------------------------------------------ which object is what
NAME_RULES = [
    (r'^Astra / Courtyard receiving ground$|^Courtyard ground source$', 'ground.earth'),
    (r'^Raked gravel court$', 'ground.gravel'),
    (r'^Astra / pebbles grouped bodies$', 'pebbles'),
    (r'^Astra / varied planks', 'plank'),
    (r'^Bridge pier \d+$', 'stone.pier'),
    (r'^(Rock|Gravel rock) \d+$|^Pond edge stone \d+$', 'stone.rock'),
    (r'^Stepping stone \d+$|^Veranda step', 'stone.step'),
    (r'^Lantern (base|post|gallery|firebox|cap|finial)$|^Water basin$', 'stone.lantern'),
    (r'^Stone plinth$', 'stone.plinth'),
    (r'^Hall posts$|^Shoji bars$', 'timber.post'),
    (r'^Hall beams$|^Eave soffit$', 'timber.beam'),
    (r'^Hall plaster$', 'wall.hall'),
    (r'^(Back wall, (left|right)|Right wall behind hall)$', 'wall.garden'),
    (r'^(Back wall, (left|right)|Right wall behind hall) cap$', 'wall.cap'),
    (r'^Hall roof$', 'roof'),
    (r'^CT / Ceramic pan prototype$', 'roof.tile'),
    (r'^Maple (trunk|branch)', 'bark.maple'),
    (r'^Pine (trunk|limb)', 'bark.pine'),
]
ROLE_TO_FAMILY = {  # for objects other builders made (custom property garden_role)
    'stone.natural': 'stone.rock', 'stone.dressed': 'stone.lantern', 'timber.deck': 'plank', 'timber.frame': 'timber.post', 'roof.tile': 'roof',
    'wall.plaster': 'wall.garden', 'wall.cap': 'wall.cap', 'ground.earth': 'ground.earth', 'ground.gravel': 'ground.gravel', 'bark': 'bark.maple',
}
# materials that are rebuilt in place, and for each shared one the family that keeps the original datablock
IN_PLACE_PATTERNS = [
    r'^Moss and earth$', r'^Raked gravel$', r'^Plaster wall$', r'^Dark timber$', r'^Beam timber$', r'^Plinth stone$', r'^Wall cap tile$', r'^Bark$',
    r'^CT / Stone painterly surface', r'^Astra / planks tone', r'^Astra / pebbles tone', r'^CT / Ceramic painterly surface$',
    r'^CT / Ceramic ridge host-local surface$', r'^CT / Timber painterly surface$',
]
PRIMARY_FAMILY = {'Plaster wall': 'wall.hall', 'Plinth stone': 'stone.plinth', 'Bark': 'bark.maple', 'Dark timber': 'timber.post', 'Beam timber': 'timber.beam'}
ROOF_MATERIALS = {'CT / Ceramic painterly surface': 'roof.tile', 'CT / Ceramic ridge host-local surface': 'roof.ridge', 'CT / Timber painterly surface': 'roof.deck'}
NEVER_OBJECT = [r'^Shoji paper$', r'^Open room back$', r'^Lantern window glow$', r'^Hills, ', r'^Dark plain$', r'^Maple leaves$', r'^Maple inner mass$', r'^Pine pads$',
                r'^Bamboo ', r'^Fallen leaves$', r'^Lily pads$', r'^Lotus blossoms$', r'^Pond water$', r'^Basin water$', r'^Astra / moss grouped bodies$']


def family_of(obj):
    if obj.type not in ('MESH', 'CURVE'):
        return None
    for pat in NEVER_OBJECT:
        if re.search(pat, obj.name):
            return None
    for pat, fam in NAME_RULES:
        if re.search(pat, obj.name):
            return fam
    role = obj.get('garden_role')
    if role in ROLE_TO_FAMILY:
        return ROLE_TO_FAMILY[role]
    return None


def is_in_place(name):
    return any(re.search(p, name) for p in IN_PLACE_PATTERNS)


def is_placeholder(name):
    return name.startswith('GARDEN placeholder')


def plank_run(obj):
    m = re.search(r'\.(\d+)$', obj.name)
    return int(m.group(1)) if m else 0


def material_slots_of(obj):
    if obj.type == 'MESH':
        return list(obj.data.materials)
    return list(obj.data.materials)


def set_slot_material(obj, index, mat):
    obj.data.materials[index] = mat
    # slots linked to the object instead of the data
    if index < len(obj.material_slots) and obj.material_slots[index].link == 'OBJECT':
        obj.material_slots[index].material = mat


def hall_z0(mat_name):
    """Lowest z of the objects using a material (the foot of a wall), used for the damp-foot blend."""
    zs = []
    for o in bpy.data.objects:
        if o.type == 'MESH' and any(s.material and s.material.name == mat_name for s in o.material_slots):
            zs += [(o.matrix_world @ v.co).z for v in o.data.vertices]
    return min(zs) if zs else 0.0


# ------------------------------------------------------------------------------------------------------------------------------ the real stack (look = 'real')
def vertical_mask(S, lo=0.55, hi=0.95):
    """1 on steep / vertical faces, 0 on flat-up and flat-down faces (from the world normal)."""
    b = S.b
    nx, ny, nz = b.sep(S.nrm)
    return b.math('SUBTRACT', 1.0, b.smooth(b.math('ABSOLUTE', nz), lo, hi))


def real_ground(mat, opt, ctx):
    S = K.Surface(mat, 'ground')
    b = S.b
    c, r, h = S.scan('forest_leaves_02', 'planar', scale=2.4, antitile=True, options=opt)
    px, py, pz = b.sep(S.pos)
    # broad directional passages: stretched noise, three zones (damp dark / mossy green / dry earth), firm-ish edges, quiet middles
    st = b.comb(b.math('MULTIPLY', px, 0.5), b.math('MULTIPLY', py, 1.1), b.math('MULTIPLY', pz, 4.0))
    big = b.noise(st, 0.32, detail=3.0, rough=0.55, distortion=0.5)
    big = b.maprange(big, 0.30, 0.70, 0.0, 1.0)
    zones = b.ramp(big, [(0.0, (0.040, 0.047, 0.027)), (0.36, (0.040, 0.047, 0.027)), (0.46, (0.078, 0.128, 0.034)), (0.62, (0.078, 0.128, 0.034)), (0.74, (0.17, 0.12, 0.072)), (1.0, (0.17, 0.12, 0.072))], 'LINEAR', 'passages: damp / moss / dry')
    c = S.normalise(c, 'forest_leaves_02', zones, contrast=0.75, options=opt)
    macro = b.maprange(b.noise(b.vmath('SCALE', S.pos, scale=0.9), 1.0, detail=2.0), 0.3, 0.7, 0.82, 1.14)
    c = b.vmath('SCALE', c, scale=macro)
    S.finish(c, r, h, bump=(0.55, 0.03), rough_remap=(0.55, 1.0, 0.78, 1.0))


def real_gravel(mat, opt, ctx):
    S = K.Surface(mat, 'gravel')
    b = S.b
    c, r, h = S.scan('gravel_floor_02', 'planar', scale=1.5, antitile=True, options=opt)
    c = S.normalise(c, 'gravel_floor_02', (0.46, 0.45, 0.42), contrast=0.9, options=opt)
    macro = b.maprange(b.noise(b.vmath('SCALE', S.pos, scale=0.55), 1.0, detail=2.0), 0.3, 0.7, 0.90, 1.07)
    c = b.vmath('SCALE', c, scale=macro)
    S.finish(c, r, h, bump=(0.28, 0.003), rough_remap=(0.2, 0.8, 0.68, 0.95))


STONE_KINDS = {
    #            main scan            scale  target colour (linear)       lichen sides
    'rock': ('rock_boulder_dry', 1.5, (0.19, 0.205, 0.2), True),
    'pier': ('rock_boulder_dry', 1.4, (0.125, 0.138, 0.135), True),
    'step': ('rock_08', 1.2, (0.215, 0.205, 0.19), False),
    'lantern': ('rock_08', 0.9, (0.17, 0.165, 0.155), False),
}


def real_stone(mat, opt, ctx):
    kind = ctx.get('kind', 'rock')
    main, scale, target, lichen = STONE_KINDS[kind]
    S = K.Surface(mat, mat.name)
    b = S.b
    c, r, h = S.scan(main, 'tri', scale=scale, options=opt, sharp=4.0)
    c = S.normalise(c, main, target, contrast=0.72, options=opt)
    if lichen:
        lc, lr, lh = S.scan('lichen_rock', 'tri', scale=1.1, options=opt, offset_mult=0.7, sharp=4.0)
        lc = S.normalise(lc, 'lichen_rock', (0.095, 0.09, 0.07), contrast=0.7, options=opt)
        patch = b.smooth(b.noise(b.vmath('ADD', b.vmath('SCALE', S.pos, scale=2.1), S.offset), 1.0, detail=3.0), 0.42, 0.64)
        amount = b.math('ADD', 0.30, b.math('MULTIPLY', S.rand, 0.7))
        fac = b.math('MULTIPLY', b.math('MULTIPLY', vertical_mask(S), patch), amount)
        c = b.mixc(fac, c, lc)
        h = b.mixf(b.math('MULTIPLY', fac, 0.6), h, lh)
    c = S.vary(c, 0.14)
    S.finish(c, r, h, bump=(0.55, 0.02), rough_remap=(0.35, 0.8, 0.62, 0.92))


def real_plinth(mat, opt, ctx):
    S = K.Surface(mat, 'plinth')
    b = S.b
    c, r, h = S.scan('japanese_stone_wall', 'tri', scale=1.9, options=opt)
    c = S.normalise(c, 'japanese_stone_wall', (0.165, 0.16, 0.145), contrast=0.85, options=opt)
    S.finish(c, r, h, bump=(0.6, 0.015), rough_remap=(0.5, 1.0, 0.65, 0.92))


def real_roof(mat, opt, ctx):
    kind = ctx.get('part', 'roof.tile')
    S = K.Surface(mat, mat.name)
    b = S.b
    if kind == 'roof.deck':
        tscan = opt.get('timber_scan', 'old_wood_floor')
        c, r, h = S.scan(tscan, 'tri', grain='x', scale=1.6, options=opt)
        c = S.normalise(c, tscan, (0.075, 0.055, 0.04), contrast=0.7, options=opt)
        S.finish(c, r, h, bump=(0.4, 0.01), rough_remap=(0.5, 1.0, 0.7, 0.92))
        return
    c, r, h = S.scan('grey_roof_tiles', 'tri', scale=opt.get('roof_scale', 2.4), options=opt, sharp=3.0)
    target = (0.088, 0.092, 0.098) if kind == 'roof.tile' else (0.072, 0.075, 0.08)
    c = S.normalise(c, 'grey_roof_tiles', target, contrast=0.6, options=opt)
    c = S.vary(c, 0.12)
    S.finish(c, r, h, bump=(0.5, 0.02), rough_remap=(0.3, 0.8, 0.40, 0.82))


def real_cap(mat, opt, ctx):
    S = K.Surface(mat, 'cap')
    c, r, h = S.scan('grey_roof_tiles', 'tri', scale=1.4, options=opt, sharp=3.0)
    c = S.normalise(c, 'grey_roof_tiles', (0.065, 0.07, 0.078), contrast=0.7, options=opt)
    S.finish(c, r, h, bump=(0.45, 0.012), rough_remap=(0.3, 0.8, 0.4, 0.8))


def real_hall_plaster(mat, opt, ctx):
    S = K.Surface(mat, 'hall plaster')
    b = S.b
    c, r, h = S.scan('white_stucco', 'tri', scale=1.8, options=opt)
    c = S.normalise(c, 'white_stucco', (0.52, 0.485, 0.43), contrast=1.0, options=opt)
    macro = b.maprange(b.noise(b.vmath('SCALE', S.pos, scale=0.7), 1.0, detail=3.0), 0.3, 0.7, 0.84, 1.06)
    c = b.vmath('SCALE', c, scale=macro)
    S.finish(c, r, h, bump=(0.35, 0.008), rough_remap=(0.0, 1.0, 0.82, 0.96))


def real_garden_wall(mat, opt, ctx):
    S = K.Surface(mat, 'garden wall')
    b = S.b
    c, r, h = S.scan('worn_plaster_wall', 'tri', scale=2.6, options=opt)
    c = S.normalise(c, 'worn_plaster_wall', (0.31, 0.275, 0.225), contrast=0.5, options=opt)
    fc, fr, fh = S.scan('worn_cracked_plaster', 'tri', scale=1.3, options=opt, offset_mult=0.6)
    fc = S.normalise(fc, 'worn_cracked_plaster', (0.20, 0.165, 0.115), contrast=0.7, options=opt)
    z0 = ctx.get('z0', 0.0)
    px, py, pz = b.sep(S.pos)
    foot = b.math('SUBTRACT', 1.0, b.smooth(pz, z0 + 0.10, z0 + 0.60))
    fac = b.math('MULTIPLY', foot, b.maprange(b.noise(b.vmath('SCALE', S.pos, scale=1.6), 1.0, detail=3.0), 0.3, 0.7, 0.5, 1.0))
    c = b.mixc(fac, c, fc)
    h = b.mixf(fac, h, fh)
    c = S.vary(c, 0.08)
    S.finish(c, r, h, bump=(0.5, 0.012), rough_remap=(0.0, 1.0, 0.82, 0.97))


def real_timber(mat, opt, ctx):
    fam = ctx['family']
    tscan = opt.get('timber_scan', 'old_wood_floor')
    S = K.Surface(mat, mat.name)
    grain = 'z' if fam == 'timber.post' else 'x'
    c, r, h = S.scan(tscan, 'tri', grain=grain, scale=1.3, options=opt, sharp=6.0)
    target = (0.125, 0.088, 0.058) if fam == 'timber.post' else (0.10, 0.071, 0.047)
    c = S.normalise(c, tscan, target, contrast=0.75, options=opt)
    S.finish(c, r, h, bump=(0.45, 0.008), rough_remap=(0.5, 1.0, 0.6, 0.9))


def real_plank(mat, opt, ctx):
    run = ctx.get('run', 0)
    veranda = run <= 2
    base = ctx.get('orig_rgb', (0.15, 0.1, 0.07))
    lum = 0.2126 * base[0] + 0.7152 * base[1] + 0.0722 * base[2]
    tone = max(0.6, min(1.5, lum / 0.095))
    S = K.Surface(mat, mat.name)
    b = S.b
    if veranda:
        key = 'weathered_planks'
        target = tuple(v * tone for v in (0.125, 0.088, 0.060))
        scale = 1.0
    else:
        key = 'wood_planks_grey'
        target = tuple(v * tone for v in (0.205, 0.195, 0.175))
        scale = 0.85
    c, r, h = S.scan(key, 'tri', grain='x', scale=scale, options=opt, sharp=8.0, offset_mult=1.0)
    c = S.normalise(c, key, target, contrast=0.8, options=opt)
    S.finish(c, r, h, bump=(0.5, 0.006), rough_remap=(0.4, 1.0, 0.6, 0.9))


def real_bark(mat, opt, ctx):
    fam = ctx['family']
    S = K.Surface(mat, mat.name)
    if fam == 'bark.pine':
        key, target, scale = 'pine_bark', (0.115, 0.08, 0.06), 1.1
    else:
        key, target, scale = 'trident_maple_bark', (0.105, 0.078, 0.057), 1.3
    c, r, h = S.scan(key, 'tri', scale=scale, options=opt, sharp=4.0)
    c = S.normalise(c, key, target, contrast=0.7, options=opt)
    S.finish(c, r, h, bump=(0.6, 0.012), rough_remap=(0.4, 1.0, 0.7, 0.95))


def real_pebbles(mat, opt, ctx):
    base = ctx.get('orig_rgb', (0.2, 0.19, 0.17))
    S = K.Surface(mat, mat.name)
    b = S.b
    c, r, h = S.scan('clean_pebbles', 'tri', scale=0.6, options=opt, sharp=4.0)
    c = S.normalise(c, 'clean_pebbles', base, contrast=0.9, options=opt)
    c = S.vary(c, 0.18)
    S.finish(c, r, h, bump=(0.4, 0.004), rough_remap=(0.4, 1.0, 0.6, 0.9))


REAL_BUILDERS = {
    'ground.earth': real_ground, 'ground.gravel': real_gravel, 'stone.rock': real_stone, 'stone.pier': real_stone, 'stone.step': real_stone,
    'stone.lantern': real_stone, 'stone.plinth': real_plinth, 'roof': real_roof, 'roof.tile': real_roof, 'roof.ridge': real_roof, 'roof.deck': real_roof,
    'wall.cap': real_cap, 'wall.hall': real_hall_plaster, 'wall.garden': real_garden_wall, 'timber.post': real_timber, 'timber.beam': real_timber,
    'plank': real_plank, 'bark.maple': real_bark, 'bark.pine': real_bark, 'pebbles': real_pebbles,
}


# ------------------------------------------------------------------------------------------------------------------------------ the painted stack (look = 'painted')
# (built in painted_stack.py; imported on demand so the real look does not need it)
def painted_builders():
    import painted_stack
    importlib.reload(painted_stack)
    return painted_stack.PAINTED_BUILDERS


# ------------------------------------------------------------------------------------------------------------------------------ the job list
def principled_base_rgb(mat):
    """The Base Color number of the first Principled box (before it is rebuilt)."""
    if mat is None or mat.node_tree is None:
        return None
    for n in mat.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeBsdfPrincipled':
            c = n.inputs['Base Color']
            if not c.links:
                return tuple(c.default_value[:3])
    return None


def stone_kind(family):
    return {'stone.rock': 'rock', 'stone.pier': 'pier', 'stone.step': 'step', 'stone.lantern': 'lantern'}.get(family)


def collect_jobs():
    """Looks at every object and returns (jobs, reassign, skipped):
       jobs      {material name: {'families': {family: [objects]}, 'run': int}}      materials to rebuild in place
       reassign  [(object, slot index, family)]                                       slots that get a shared 'GARDEN <family>' material (placeholders, split materials)
    """
    by_mat = {}
    reassign = []
    for obj in bpy.data.objects:
        fam = family_of(obj)
        if fam is None:
            continue
        for index, mat in enumerate(material_slots_of(obj)):
            if mat is None:
                continue
            if is_placeholder(mat.name):
                reassign.append((obj, index, fam, None))
            elif is_in_place(mat.name):
                by_mat.setdefault(mat.name, {}).setdefault(fam, []).append(obj)
    # the roof's materials are set inside geometry nodes: no object slot holds them
    for name, fam in ROOF_MATERIALS.items():
        if name in bpy.data.materials:
            by_mat.setdefault(name, {}).setdefault(fam, [])
    jobs = {}
    for name, fams in by_mat.items():
        primary = PRIMARY_FAMILY.get(name)
        if len(fams) > 1:
            keep = primary if primary in fams else sorted(fams, key=lambda f: -len(fams[f]))[0]
            for fam, objs in fams.items():
                if fam == keep:
                    continue
                for obj in objs:
                    for index, mat in enumerate(material_slots_of(obj)):
                        if mat is not None and mat.name == name:
                            reassign.append((obj, index, fam, name))
            fams = {keep: fams[keep]}
        jobs[name] = fams
    return jobs, reassign


def build_family_material(builders, mat, fam, objs, opt, extra=None):
    ctx = {'family': fam}
    if fam.startswith('stone.') and fam != 'stone.plinth':
        ctx['kind'] = stone_kind(fam)
    if fam in ('roof.tile', 'roof.ridge', 'roof.deck'):
        ctx['part'] = fam
    if fam == 'plank' and objs:
        ctx['run'] = plank_run(objs[0])
    if fam == 'wall.garden':
        ctx['z0'] = hall_z0(mat.name)
    if mat.get('garden_orig_rgb') is not None:
        ctx['orig_rgb'] = tuple(mat['garden_orig_rgb'])
    else:
        rgb = principled_base_rgb(mat)
        if rgb is not None:
            mat['garden_orig_rgb'] = list(rgb)
            ctx['orig_rgb'] = rgb
    if extra:
        ctx.update(extra)
    fn = builders[fam]
    fn(mat, opt, ctx)
    mat['garden_owner'] = OWNER
    mat['garden_family'] = fam
    mat['garden_look'] = opt['look']


def shared_family_material(builders, fam, opt, orig_name=None):
    name = f'GARDEN {fam}'
    mat = bpy.data.materials.get(name)
    if mat is None:
        original = bpy.data.materials.get(orig_name) if orig_name else None
        # a split-off material starts as a copy of the one it was split from (the painted look keeps what it does not retune); a placeholder gets a fresh one
        mat = original.copy() if original is not None else bpy.data.materials.new(name)
        mat.name = name
    build_family_material(builders, mat, fam, [], opt)
    return mat


# ------------------------------------------------------------------------------------------------------------------------------ the stage
def snapshot():
    return {
        'objects': sorted(o.name for o in bpy.data.objects),
        'materials': sorted(m.name for m in bpy.data.materials),
        'node_groups': sorted(g.name for g in bpy.data.node_groups),
        'images': sorted(i.name for i in bpy.data.images),
        'slots': {o.name: [m.name if m else None for m in material_slots_of(o)] for o in bpy.data.objects if o.type in ('MESH', 'CURVE')},
    }


def diff(before, after):
    rep = {}
    for key in ('objects', 'materials', 'node_groups', 'images'):
        b, a = set(before[key]), set(after[key])
        rep[key + '_created'] = sorted(a - b)
        rep[key + '_deleted'] = sorted(b - a)
    rep['objects_slot_changed'] = sorted(n for n in after['slots'] if n in before['slots'] and before['slots'][n] != after['slots'][n])
    return rep


def pack_my_images():
    """Packs into the .blend every picture that lives in this folder: the Poly Haven maps and the kit's mask pictures (call it before saving the final scene file)."""
    packed, total = 0, 0
    for img in bpy.data.images:
        if img.source != 'FILE' or not img.filepath:
            continue
        path = os.path.abspath(bpy.path.abspath(img.filepath))
        if path.startswith(HERE + os.sep):
            total += 1
            if not img.packed_file:
                try:
                    img.pack()
                    packed += 1
                except Exception:
                    pass
    return {'pictures_under_this_folder': total, 'newly_packed': packed}


def apply(options=None):
    t0 = time.time()
    opt = {'look': 'real', 'weathering': True, 'weathering_look': 'mossy_courtyard_kept', 'pack_images': False, 'verbose': True}
    opt.update(options or {})
    look = opt['look']
    assert look in ('real', 'painted'), "options['look'] must be 'real' or 'painted'"
    importlib.reload(K)
    before = snapshot()
    builders = REAL_BUILDERS if look == 'real' else painted_builders()
    jobs, reassign = collect_jobs()
    built = []
    use_pigment = look == 'painted' and bool(opt.get('addon_dir'))
    if use_pigment:
        import pigment_stage
        for keep in pigment_stage.ORIGINAL_MATERIALS:
            jobs.pop(keep, None)                                  # the pigment tool starts from the add-on's original noise materials
    for name, fams in sorted(jobs.items()):
        fam = list(fams.keys())[0]
        build_family_material(builders, bpy.data.materials[name], fam, fams[fam], opt)
        built.append((name, fam))
    shared = {}
    for obj, index, fam, orig_name in reassign:
        if fam not in shared:
            shared[fam] = shared_family_material(builders, fam, opt, orig_name)
        set_slot_material(obj, index, shared[fam])
    # placeholders nobody uses any more
    for mat in list(bpy.data.materials):
        if is_placeholder(mat.name) and mat.users == 0:
            bpy.data.materials.remove(mat)
    pack_images_report = None
    pigment_report = None
    if use_pigment:
        importlib.reload(pigment_stage)
        pigment_report = pigment_stage.apply(opt['addon_dir'], opt)
    weathering_report = None
    if look == 'real' and opt['weathering']:
        import weathering_stage
        importlib.reload(weathering_stage)
        weathering_report = weathering_stage.apply(opt)
    if opt['pack_images'] and look == 'real':
        pack_images_report = pack_my_images()
    after = snapshot()
    rep = diff(before, after)
    rep['built'] = len(built)
    rep['reassigned_slots'] = len(reassign)
    rep['look'] = look
    rep['seconds'] = round(time.time() - t0, 1)
    rep['weathering'] = weathering_report
    rep['packed_images'] = pack_images_report
    rep['pigment'] = pigment_report
    if opt['verbose']:
        print('=== stage_surfaces: look =', look, '===')
        print('materials rebuilt in place:', len(built), '| slots moved to a shared role material:', len(reassign))
        print('objects created:', rep['objects_created'], '| deleted:', rep['objects_deleted'], '| slots changed on', len(rep['objects_slot_changed']), 'objects')
        print('materials created:', len(rep['materials_created']), rep['materials_created'][:8], '| deleted:', len(rep['materials_deleted']), rep['materials_deleted'][:8])
        print('node groups created:', len(rep['node_groups_created']), '| images loaded:', len(rep['images_created']), '| seconds:', rep['seconds'])
    return rep
