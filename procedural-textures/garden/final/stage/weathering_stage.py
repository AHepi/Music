# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# PART B of the surfaces stage: puts the weathering kit (a private patched copy in ./kit, see out/kit_patch5_diffs.txt) on top of the scanned surfaces. Called by
# stage_surfaces.apply() for look='real'. What it does, in order:
#   1. finds the sun lamp and writes its real direction into the set file (the kit used to assume north = +y and latitude 35)
#   2. rebuilds the mask pack (the where-pictures: height above ground, damp, shade, moss sites ...) from the CURRENT geometry when the other builders have changed it
#      or the sun has moved (options 'rebuild_masks': 'auto' (default) | 'always' | 'never'); about 30 to 60 s
#   3. applies the kit with the garden look: dust-and-algae film, runoff under caps and eaves, damp foot, plaster hairlines and stone chips, wall growth (the main layer),
#      dirt on gravel, earth and stones, patch moss on earth and stones. NOT applied: steps, paint, ground cracks, iron, puddles and wetness, joints, rubbish, the 3D growth layer.
#   4. camera_for_picture(): tells the layers how big one picture dot is for a camera (call it before each picture; the render job does)
# remove() takes everything off again (every material exactly as it was before the kit).
import bpy
import os
import sys
import json
import time
import math
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, 'kit')
LAYERS = ['soot', 'runoff', 'foot', 'wallgrowth', 'wallcracks', 'dirt', 'groundmoss']
OFF_LAYERS = ['steps', 'paint', 'groundcracks', 'iron', 'growth']
SET_ID = 'japanese_courtyard'
SCENE_ID = 'courtyard'
_HANDLE = {}


def _kit_modules():
    if KIT not in sys.path:
        sys.path.insert(0, KIT)
    sys.dont_write_bytecode = True
    import apply_weathering as aw
    return aw


def sun_direction():
    """Unit vector from the ground toward the sun for the brightest sun lamp in the scene (the lamp shines along its own -Z)."""
    best = None
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT' and ob.data.type == 'SUN' and not ob.hide_render and ob.data.energy > 0:
            if best is None or ob.data.energy > best.data.energy:
                best = ob
    if best is None:
        return None, None
    m = best.matrix_world.to_3x3()
    v = m @ __import__('mathutils').Vector((0.0, 0.0, 1.0))
    v.normalize()
    return [round(v.x, 4), round(v.y, 4), round(v.z, 4)], best.name


def write_sun_into_set(direction):
    path = os.path.join(KIT, 'sets', SET_ID + '.json')
    d = json.load(open(path))
    old = d['shade'].get('toward_sun')
    if old is not None and sum(a * b for a, b in zip(old, direction)) > math.cos(math.radians(0.5)):
        return False
    d['shade']['toward_sun'] = direction
    json.dump(d, open(path, 'w'), indent=1)
    return True


def pack_directory():
    return os.path.join(KIT, 'masks', 'packs', SET_ID, SCENE_ID)


def pack_sun():
    mf = os.path.join(pack_directory(), 'manifest.json')
    if not os.path.exists(mf):
        return None
    return json.load(open(mf)).get('sun_direction')


def rebuild_masks(direction):
    """Reads the open scene's geometry again and writes a fresh mask pack into ./kit (about 20 to 60 s)."""
    aw = _kit_modules()
    from masks import reader
    pdir = pack_directory()          # the pack that ships in ./kit is replaced (the pristine one is ours/kit_patched/masks/packs/japanese_courtyard/courtyard)
    t = time.time()
    manifest = reader.run(SET_ID, SCENE_ID, pdir, raw_dir=os.path.join(HERE, 'work', 'raw_masks'), sheets=True, with_shade=True)
    mf = os.path.join(pdir, 'manifest.json')
    m = json.load(open(mf))
    m['sun_direction'] = direction
    json.dump(m, open(mf, 'w'), indent=1)
    shutil.rmtree(os.path.join(HERE, 'work', 'raw_masks'), ignore_errors=True)
    return round(time.time() - t, 1)


def others_changed_geometry():
    return any(ob.get('garden_owner') in ('shapes', 'life') for ob in bpy.data.objects)


def apply(opt):
    t0 = time.time()
    aw = _kit_modules()
    if aw.current() is not None:
        aw.remove()
    rep = {'layers_on': LAYERS, 'layers_not_used': OFF_LAYERS}
    direction, lamp = sun_direction()
    rep['sun_lamp'] = lamp
    rep['sun_direction'] = direction
    if direction is not None:
        rep['set_file_sun_updated'] = write_sun_into_set(direction)
    mode = opt.get('rebuild_masks', 'auto')
    need = mode == 'always' or (mode == 'auto' and (others_changed_geometry() or (direction is not None and pack_sun() != direction)))
    rep['mask_pack'] = 'rebuilt' if need else 'shipped'
    if need:
        rep['mask_seconds'] = rebuild_masks(direction)
    w = aw.apply(SET_ID, opt.get('weathering_look', 'garden_kept'), scene_id=SCENE_ID, layers=LAYERS, earlier=False, pieces=False, strict=False, state='dry')
    if opt.get('weathering_master') is not None:
        w.set_master(opt['weathering_master'])
    _HANDLE['w'] = w
    r = w.report()
    rep['problems'] = r.get('problems')
    rep['roles'] = r.get('roles')
    rep['unassigned_objects'] = r.get('unassigned_objects')
    rep['materials_per_layer'] = {k: len(v) for k, v in w.applied.items()}
    rep['skipped'] = {k: (len(v) if hasattr(v, '__len__') else v) for k, v in (r.get('skipped') or {}).items()}
    rep['seconds'] = round(time.time() - t0, 1)
    cam = bpy.context.scene.camera
    if cam is not None and opt.get('picture_height'):
        camera_for_picture(cam, opt['picture_height'])
    return rep


def camera_for_picture(camera, picture_height):
    """Tells the kit's layers how big one dot of the coming picture is (marks are sized in picture dots). Call before each picture with its camera and height in pixels."""
    w = _HANDLE.get('w')
    if w is None:
        return False
    w.camera(camera, plate_height=picture_height)
    return True


def remove():
    w = _HANDLE.pop('w', None)
    aw = _kit_modules()
    if w is not None:
        w.remove()
    else:
        aw.remove()
