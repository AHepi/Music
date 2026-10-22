# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Small helpers every measuring script shares. Plain Python (numpy, OpenCV): nothing here needs Blender.
#   - reading pictures (8 or 16 bit) as numbers 0..1, and the brightness the earlier studies used (Rec.709 weights of the picture as shown)
#   - the helper pictures the runner draws (see testset.py): class (role per dot), depth (metres per dot), puddle, dirt, layer masks
#   - the picture lists of a set (the 22 lighting pictures, the plates) and the class table of a set
# A "folder" is a folder the runner's pictures were brought back to (JPG, JSON, and the PNG of the pictures a measure needs exactly).
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

DEPTH_RANGE_M = 128.0


def read_rgb(path):
    """The picture as float RGB 0..1 (8 or 16 bit; as shown, no colour change)."""
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if a is None:
        raise FileNotFoundError(path)
    scale = 65535.0 if a.dtype == np.uint16 else 255.0
    if a.ndim == 2:
        a = np.stack([a] * 3, axis=2)
    return a[..., 2::-1].astype(np.float32) / scale if a.shape[2] >= 3 else a.astype(np.float32) / scale


def lum(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def read_lum(path):
    return lum(read_rgb(path))


def read_channel(path, channel=0):
    """One channel (0 = red) of a raw mask picture as float 0..1."""
    return read_rgb(path)[..., channel]


def exists(folder, name, ext='.png'):
    return os.path.exists(os.path.join(folder, name + ext))


def pic(folder, name):
    """The best file for a picture name: PNG if kept, else JPG."""
    for ext in ('.png', '.jpg'):
        p = os.path.join(folder, name + ext)
        if os.path.exists(p):
            return p
    return None


def info(folder, name):
    p = os.path.join(folder, name + '.json')
    return json.load(open(p)) if os.path.exists(p) else None


def role_table(settings):
    return {role: index + 1 for index, role in enumerate(settings.roles)}


def classes(settings):
    """{class name: [role ids]} from test_set.classes, else one class per role family."""
    table = role_table(settings)
    given = (settings.get('test_set') or {}).get('classes')
    if given:
        return {name: sorted({table[r] for role in roles for r in settings.expand_roles([role]) if r in table}) for name, roles in given.items()}
    families = {}
    for role, rid in table.items():
        families.setdefault(role.split('.')[0], []).append(rid)
    return families


def read_class(path):
    """Role id per dot (int array) from a class picture (value = id / 64, 16 bit)."""
    a = read_rgb(path)[..., 0]
    return np.rint(a * 64.0).astype(np.int16)


def read_depth(path):
    """Distance in metres per dot from a depth picture (value = metres / 128)."""
    return read_rgb(path)[..., 0] * DEPTH_RANGE_M


def class_mask(class_map, ids):
    return np.isin(class_map, list(ids))


def t22_list(settings, scene_id=None):
    """[(label, light, state, scene id)] of the lighting pictures (names '<label>_<light>_<state>')."""
    ts = settings.get('test_set') or {}
    out = []
    for label, rows in ts.get('lighting22', {}).items():
        sid = ts.get('scene_of', {}).get(label, scene_id)
        if scene_id and sid != scene_id:
            continue
        for light, states in rows:
            for state in states:
                out.append((label, light, state, sid))
    return out


def size_of(settings, label):
    return tuple((settings.get('test_set') or {})['size_of'][label][:2])


def camera_of(settings, label):
    return (settings.get('test_set') or {})['camera_of'][label]


def plate_list(settings):
    """[(camera, light, state, scene id, w, h)] of the plate pictures."""
    ts = settings.get('test_set') or {}
    out = []
    plate = settings.get('plate')
    for camera, light, state in ts.get('plates', []):
        w, h = (ts.get('plate_sizes') or {}).get(camera, plate['size'])
        out.append((camera, light, state, ts.get('scene_of', {}).get(camera), w, h))
    return out


def folders_for(paths):
    """Accepts one folder or a list; returns the list."""
    return [paths] if isinstance(paths, str) else list(paths)


def load_set(set_id):
    from apply import settings as settings_module
    return settings_module.load_set(set_id)


def jdump(data, path):
    with open(path, 'w') as handle:
        json.dump(data, handle, indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))


def dilate(mask, k=5):
    return cv2.dilate(mask.astype(np.uint8), np.ones((k, k), np.uint8)) > 0
