"""What this does: finds REAL PHOTOGRAPHED SURFACES for the surface pass, so a road looks like a photographed dirt road and not like a few colours made in code.
For each material slot it picks, in this order:
  1. the person's OWN texture library, when the place settings name one ("own_surfaces": a folder with one sub-folder per surface, each holding a colour picture, a
     normal picture and a height picture, and a mapping from roles or surfaces to those sub-folders): nothing is copied anywhere, the pictures are read where they are;
  2. the free Poly Haven scan (CC0) that data/surfaces.json names for the surface ("polyhaven"), downloaded ONCE per machine into a cache folder outside every
     repository (PLACE_KIT_SCAN_CACHE, else ~/.cache/explainer-film/surface-scans): the colour picture, the OpenGL normal map, the roughness map and the height
     (displacement) map, at the sizes the house numbers say (colour 2k, the other maps 1k: the audit's normal-map minimum is 1024);
  3. nothing (the caller then uses the made-in-code recipe, and says so): a surface with no scan named, a machine with no network (or PLACE_KIT_OFFLINE=1, or
     "surface_scans": "off" in the place settings), or a download that failed.
The request to Poly Haven carries a plain agent name and nothing about the person. Every downloaded or library normal map is checked against its own height map with
the kit's own normal test (normals.direction_correlation) the first time it is used: a map whose green (or red) points the other way is turned round, and a map that
leans as a whole (its mean red or green outside the audit's band: a scan whose plane was not quite level) has the lean taken out; the corrected copy is kept in the
cache, and the result is written into the scan's info.json, so the check runs once per machine.
Plain Python for the choosing and the downloading (tested without Blender); the parts that read pictures need Blender (bpy) and numpy and import it when called.
A concrete example: choose_scan('ground.dirt_road', 'dirt_road', spec, settings) on a machine with network returns {'source': 'polyhaven', 'id': 'brown_mud_dry',
'metres': 1.3, 'files': {'colour': '.../brown_mud_dry_diff_2k.jpg', 'normal': ..., 'roughness': ..., 'height': ...}}; offline it returns None with the reason.
"""
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request

API = 'https://api.polyhaven.com'
AGENT = 'explainer-film-place-kit/1.5 (surface scans)'
MAP_KINDS = ('colour', 'normal', 'roughness', 'height')
POLYHAVEN_KEYS = {'colour': ('Diffuse',), 'normal': ('nor_gl',), 'roughness': ('Rough',), 'height': ('Displacement',)}
FORMATS = {'colour': ('jpg', 'png'), 'normal': ('png', 'jpg'), 'roughness': ('jpg', 'png'), 'height': ('png', 'jpg')}
LIBRARY_WORDS = {
    'colour': ('colour', 'color', 'albedo', 'basecolor', 'base_color', 'diffuse', 'diff'),
    'normal': ('normal', 'nor_gl', 'nor', 'nrm'),
    'height': ('height', 'displacement', 'disp', 'bump'),
    'roughness': ('roughness', 'rough'),
}
PICTURE_ENDINGS = ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.exr')
LOCK_WAIT_SECONDS = 300
CHECK_VERSION = 2               # the normal check of a cached scan is made again when this changes (2: the whole-map lean is taken out too)


class ScanUnavailable(Exception):
    """No scan can be had for this surface right now; the message says why in plain words."""


# ------------------------------------------------------------------ where things are
def cache_folder():
    """The per-machine folder that keeps downloaded scans (never inside a repository)."""
    chosen = os.environ.get('PLACE_KIT_SCAN_CACHE')
    if chosen:
        return os.path.abspath(os.path.expanduser(chosen))
    base = os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~'), '.cache')
    return os.path.join(base, 'explainer-film', 'surface-scans')


def offline(settings=None):
    """True when the kit must not try the network: PLACE_KIT_OFFLINE=1, or the place settings say "surface_scans": "off"."""
    if str(os.environ.get('PLACE_KIT_OFFLINE', '')).strip().lower() in ('1', 'true', 'yes', 'on'):
        return True
    data = getattr(settings, 'data', settings) or {}
    return str(data.get('surface_scans', 'auto')).lower() == 'off'


def resolution(kind, quick=False):
    """'2k' or '1k' for a map kind, from the house numbers (quick runs use the maps' size for every picture)."""
    from .. import house_numbers
    if kind == 'colour' and not quick:
        return str(house_numbers.value('place_surfaces.scan_colour_resolution'))
    return str(house_numbers.value('place_surfaces.scan_maps_resolution'))


# ------------------------------------------------------------------ the network (plain urllib, curl when urllib cannot get through)
def _get(url, timeout):
    request = urllib.request.Request(url, headers={'User-Agent': AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_bytes(url, timeout=60):
    """The body at an https address, or ScanUnavailable with the reason. Tries Python's own client first, then curl (which follows the machine's proxy settings)."""
    try:
        return _get(url, timeout)
    except (urllib.error.URLError, OSError, ValueError) as first:
        curl = shutil.which('curl')
        if curl is None:
            raise ScanUnavailable(f'no network answer from {url.split("/")[2]} ({first})')
        run = subprocess.run([curl, '-sS', '--fail', '-L', '--max-time', str(int(timeout)), '-A', AGENT, url], capture_output=True)
        if run.returncode != 0:
            raise ScanUnavailable(f'no network answer from {url.split("/")[2]} ({first}; curl: {run.stderr.decode(errors="replace").strip()[:120]})')
        return run.stdout


def polyhaven_file_list(scan_id, timeout=60):
    """Poly Haven's list of the files of one scan (its own names and addresses: the address pattern differs between scans, so it is never guessed)."""
    try:
        return json.loads(fetch_bytes(f'{API}/files/{scan_id}', timeout))
    except ValueError as problem:
        raise ScanUnavailable(f'Poly Haven gave no readable file list for {scan_id} ({problem})')


def polyhaven_address(file_list, kind, size):
    """(address, format) of one map at one size from Poly Haven's file list; the next size down when that size is missing; None when the scan has no such map."""
    for key in POLYHAVEN_KEYS[kind]:
        sizes = file_list.get(key) or {}
        for wanted in (size, '1k', '2k'):
            entry = sizes.get(wanted) or {}
            for extension in FORMATS[kind]:
                if (entry.get(extension) or {}).get('url'):
                    return entry[extension]['url'], extension, wanted
    return None


def _write_atomically(path, data):
    temporary = path + '.part'
    with open(temporary, 'wb') as handle:
        handle.write(data)
    os.replace(temporary, path)


class _Lock:
    """One helper downloads a scan while the others wait (several builders may finish places on one machine at once)."""

    def __init__(self, folder):
        self.path = os.path.join(folder, '.downloading')

    def __enter__(self):
        began = time.time()
        while True:
            try:
                handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(handle, str(os.getpid()).encode())
                os.close(handle)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > LOCK_WAIT_SECONDS:
                        os.remove(self.path)              # a helper that died mid-download
                        continue
                except OSError:
                    continue
                if time.time() - began > LOCK_WAIT_SECONDS:
                    raise ScanUnavailable('another helper has been downloading this scan for five minutes')
                time.sleep(1.0)

    def __exit__(self, *_):
        try:
            os.remove(self.path)
        except OSError:
            pass


def read_info(folder):
    path = os.path.join(folder, 'info.json')
    if os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as handle:
                return json.load(handle)
        except (OSError, ValueError):
            return {}
    return {}


def write_info(folder, info):
    os.makedirs(folder, exist_ok=True)
    _write_atomically(os.path.join(folder, 'info.json'), json.dumps(info, indent=1, sort_keys=True).encode())


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def polyhaven_scan(scan_id, metres, quick=False, timeout=60, settings=None):
    """The scan's maps on this machine (downloaded the first time). Returns {'source', 'id', 'folder', 'metres', 'files': {kind: path}, 'info'}; raises ScanUnavailable."""
    if not re.match(r'^[a-z0-9_]+$', scan_id or ''):
        raise ScanUnavailable(f'"{scan_id}" is not a Poly Haven scan name')
    folder = os.path.join(cache_folder(), 'polyhaven', scan_id)
    wanted = {kind: resolution(kind, quick) for kind in MAP_KINDS}
    info = read_info(folder)

    def have():
        files = {}
        for kind in MAP_KINDS:
            entry = (info.get('files') or {}).get(kind) or {}
            path = os.path.join(folder, entry.get('file', '')) if entry.get('file') else None
            if path and os.path.exists(path) and entry.get('size') in (wanted[kind], *(['2k'] if wanted[kind] == '1k' else [])):
                files[kind] = path
        return files

    files = have()
    if not all(kind in files for kind in ('colour', 'normal')):
        if offline(settings):
            raise ScanUnavailable('downloads are switched off (PLACE_KIT_OFFLINE or "surface_scans": "off") and this scan is not in the cache yet')
        os.makedirs(folder, exist_ok=True)
        with _Lock(folder):
            info = read_info(folder)
            files = have()
            if not all(kind in files for kind in ('colour', 'normal')):
                listing = polyhaven_file_list(scan_id, timeout)
                info.setdefault('files', {})
                for kind in MAP_KINDS:
                    if kind in files:
                        continue
                    found = polyhaven_address(listing, kind, wanted[kind])
                    if found is None:
                        continue
                    address, extension, size = found
                    name = f'{scan_id}_{kind}_{size}.{extension}'
                    data = fetch_bytes(address, timeout)
                    if len(data) < 1000:
                        raise ScanUnavailable(f'the {kind} picture of {scan_id} came back nearly empty ({len(data)} bytes)')
                    _write_atomically(os.path.join(folder, name), data)
                    info['files'][kind] = {'file': name, 'size': size, 'format': extension, 'bytes': len(data), 'sha256': sha256_of(os.path.join(folder, name)),
                                           'address': address}
                info.update(source='polyhaven', id=scan_id, licence='CC0 (public domain): https://polyhaven.com/license', downloaded=time.strftime('%Y-%m-%d'),
                            agent=AGENT, metres=metres)
                write_info(folder, info)
                files = have()
    if 'colour' not in files or 'normal' not in files:
        raise ScanUnavailable(f'the Poly Haven scan {scan_id} has no colour picture or no normal map at the sizes asked')
    return {'source': 'polyhaven', 'id': scan_id, 'key': scan_id, 'folder': folder, 'metres': float(metres) if metres else None, 'files': files, 'info': info}


# ------------------------------------------------------------------ the person's own library
def own_library(settings):
    """The place settings' "own_surfaces" block, or None: {"folder": PATH, "use": {ROLE OR SURFACE (a role may end in *): SUB-FOLDER}, "metres": {SUB-FOLDER: metres}}."""
    data = getattr(settings, 'data', settings) or {}
    block = data.get('own_surfaces')
    if not isinstance(block, dict) or not block.get('folder'):
        return None
    return block


def library_choice(block, role, surface_id):
    """The sub-folder of the person's library for this role and surface: an exact role first, then a role pattern, then the surface id. None when none matches."""
    use = block.get('use') or {}
    if role in use:
        return use[role]
    for pattern, name in use.items():
        if '*' in pattern and fnmatch.fnmatchcase(role or '', pattern):
            return name
    return use.get(surface_id)


def library_files(folder):
    """{kind: path} of the pictures in one library sub-folder, found by the words in their names (colour/color/albedo/diff..., normal/nor..., height/displacement/disp...,
    rough...). A name that says the map was left as uploaded, or is DirectX, is used only when there is nothing else. Returns ({kind: path}, {kind: 'directx' | None})."""
    pictures = sorted(f for f in os.listdir(folder) if f.lower().endswith(PICTURE_ENDINGS))
    found, conventions = {}, {}
    for kind, words in LIBRARY_WORDS.items():
        candidates = []
        for name in pictures:
            stem = os.path.splitext(name)[0].lower()
            parts = re.split(r'[^a-z0-9]+', stem)
            if kind == 'roughness' and not any(w in parts or stem.startswith(w) for w in words):
                continue
            if kind != 'roughness' and not any(w in parts for w in words) and not any(stem == w for w in words):
                continue
            if kind == 'colour' and any(w in parts for w in ('normal', 'nor', 'height', 'disp', 'rough', 'roughness')):
                continue
            plain = not any(w in stem for w in ('as_uploaded', 'directx', '_dx', 'original'))
            candidates.append((0 if plain else 1, len(stem), name))
        if candidates:
            chosen = sorted(candidates)[0][2]
            found[kind] = os.path.join(folder, chosen)
            lowered = chosen.lower()
            conventions[kind] = 'directx' if (kind == 'normal' and ('directx' in lowered or '_dx' in lowered or 'nor_dx' in lowered)) else None
    return found, conventions


def library_scan(block, name, fallback_metres):
    """One sub-folder of the person's library as a scan, or ScanUnavailable. Needs at least a colour picture; the normal map is made from the height when there is none."""
    root = os.path.abspath(os.path.expanduser(block['folder']))
    folder = os.path.join(root, name)
    if not os.path.isdir(folder):
        raise ScanUnavailable(f'the library folder "{name}" is not in {root}')
    files, conventions = library_files(folder)
    if 'colour' not in files:
        raise ScanUnavailable(f'the library folder "{name}" has no colour picture (a name with colour, color, albedo or diffuse in it)')
    metres = (block.get('metres') or {}).get(name)
    if metres is None and os.path.exists(os.path.join(folder, 'metres.txt')):
        try:
            with open(os.path.join(folder, 'metres.txt'), encoding='utf-8') as handle:
                metres = float(handle.read().split()[0])
        except (OSError, ValueError, IndexError):
            metres = None
    key = 'own_' + re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_') + '_' + hashlib.md5(folder.encode()).hexdigest()[:6]
    return {'source': 'own', 'id': name, 'key': key, 'folder': folder, 'metres': float(metres) if metres else float(fallback_metres),
            'metres_given': metres is not None, 'files': files, 'conventions': conventions,
            'work_folder': os.path.join(cache_folder(), 'own', key), 'info': read_info(os.path.join(cache_folder(), 'own', key))}


# ------------------------------------------------------------------ choosing
def choose_scan(role, surface_id, spec, settings, quick=False):
    """(scan or None, plain sentence). The person's library first, then the Poly Haven scan, then None (the made-in-code recipe)."""
    from .. import settings_file
    block = own_library(settings)
    tile = float(settings_file.number(spec['tile_metres'])) if spec.get('tile_metres') else 2.0
    if block:
        name = library_choice(block, role, surface_id)
        if name:
            try:
                scan = library_scan(block, name, tile)
                return scan, f'{role}: the person\'s own surface "{name}"' + ('' if scan['metres_given'] else f' (its real size was not given, so {tile:g} m was assumed)')
            except ScanUnavailable as problem:
                said = f'{role}: the person\'s own surface could not be used ({problem})'
                scan, more = _polyhaven_for(spec, settings, quick)
                return scan, said + '; ' + more
    return _polyhaven_for(spec, settings, quick)


def _polyhaven_for(spec, settings, quick):
    from .. import settings_file
    scan_id = spec.get('polyhaven')
    if not scan_id:
        return None, 'no photographed scan is named for this surface, so the made-in-code surface is used'
    metres = settings_file.number(spec['scan_metres']) if spec.get('scan_metres') else None
    try:
        scan = polyhaven_scan(scan_id, metres, quick=quick, settings=settings)
        return scan, f'the photographed Poly Haven scan {scan_id} ({metres:g} m a copy)'
    except ScanUnavailable as problem:
        return None, f'the Poly Haven scan {scan_id} could not be had ({problem}), so the made-in-code surface is used instead'


# ------------------------------------------------------------------ Blender side: the pictures, checked once
def _load(path, name, non_colour):
    import bpy
    image = bpy.data.images.get(name)
    if image is not None and os.path.abspath(bpy.path.abspath(image.filepath or '')) == os.path.abspath(path):
        return image
    if image is not None:
        image.name = name + ' (old)'
    image = bpy.data.images.load(path, check_existing=False)
    image.name = name
    image.colorspace_settings.name = 'Non-Color' if non_colour else 'sRGB'
    image['pk_scan'] = 1
    return image


def _grey(image):
    """A loaded picture as one grey channel (rows from the top), 0..1."""
    from . import normals
    array = normals.image_to_array(image)
    return array[..., 0] if array.shape[2] >= 1 else array


def _resize_nearest(array, rows, cols):
    import numpy as np
    r = (np.arange(rows) * array.shape[0] // rows).astype(int)
    c = (np.arange(cols) * array.shape[1] // cols).astype(int)
    return array[r][:, c]


def prepare_images(scan, check_limit=None):
    """Loads the scan's pictures into Blender and proves the normal map points the right way (once per machine: the result goes into the scan's info.json).
    Returns {'colour', 'normal', 'roughness', 'height' (images or None), 'height_mean', 'normal_check': {...}, 'turned': [axes]}."""
    import numpy as np
    from .. import house_numbers
    from . import normals
    limit = float(check_limit if check_limit is not None else house_numbers.value('place_surfaces.normal_direction_correlation_min'))
    key = scan['key']
    work = scan.get('work_folder') or scan['folder']
    os.makedirs(work, exist_ok=True)
    info = read_info(work)
    files = dict(scan['files'])
    height_image = _load(files['height'], f'pk_scan_{key}_height', True) if files.get('height') else None
    height_array = _grey(height_image) if height_image is not None else None
    made_normal = None
    if not files.get('normal'):
        if height_array is None:
            raise ScanUnavailable(f'{scan["id"]}: no normal map and no height picture to make one from')
        path = os.path.join(work, f'{key}_normal_made_from_height.png')
        if not os.path.exists(path):
            from . import heights
            normal = normals.height_to_normal(heights.calibrate_height(height_array - float(height_array.mean()), 30.0), 1.0, tile=True)
            normals.write_png(path, np.rint(normals.to_rgb(normal) * 255).astype(np.uint8))
        files['normal'] = made_normal = path
    previous = info.get('normal_check') or {}
    check = previous if (previous.get('source_sha256') == _quick_hash(scan['files'].get('normal') or made_normal) and previous.get('version') == CHECK_VERSION) else None
    normal_path = files['normal']
    if check is None:
        raw = _load(normal_path, f'pk_scan_{key}_nor_raw', True)
        rgb = normals.image_to_array(raw)[..., :3]
        turned = []
        if height_array is not None:
            height = _resize_nearest(height_array, rgb.shape[0], rgb.shape[1])
            step = max(1, rgb.shape[0] // 512)
            correlation = normals.direction_correlation(rgb[::step, ::step], height[::step, ::step])
        else:
            correlation = {'x': 'not informative', 'y': 'not informative'}
            if (scan.get('conventions') or {}).get('normal') == 'directx':
                correlation['y'] = -1.0          # the file says DirectX and there is no height to prove it: trust the name
        for axis, channel in (('x', 0), ('y', 1)):
            value = correlation.get(axis)
            if isinstance(value, float) and value < -limit:
                rgb[..., channel] = 1.0 - rgb[..., channel]
                turned.append(axis)
        # a photographed map can lean as a whole (the scan's plane was not quite level): a surface lit by it would look turned toward one side, so the lean is taken out
        band = house_numbers.value('place_surfaces.normal_red_green_mean_band')
        lean = [float(rgb[..., 0].mean()) - 0.5, float(rgb[..., 1].mean()) - 0.5]
        recentred = None
        if not all(band[0] <= 0.5 + d <= band[1] for d in lean):
            vectors = rgb * 2.0 - 1.0
            vectors[..., 0] -= 2.0 * lean[0]
            vectors[..., 1] -= 2.0 * lean[1]
            vectors[..., 2] = np.sqrt(np.clip(1.0 - vectors[..., 0] ** 2 - vectors[..., 1] ** 2, 0.02, 1.0))
            vectors /= np.linalg.norm(vectors, axis=2, keepdims=True)
            rgb = np.clip(vectors * 0.5 + 0.5, 0.0, 1.0)
            recentred = [round(lean[0], 4), round(lean[1], 4)]
        if turned or recentred:
            corrected = os.path.join(work, f'{key}_normal_opengl_checked.png')
            normals.write_png(corrected, np.rint(np.clip(rgb, 0, 1) * 255).astype(np.uint8))
            normal_path = corrected
        import bpy
        bpy.data.images.remove(raw)
        check = {'correlation': correlation, 'turned': turned, 'recentred': recentred, 'file': os.path.basename(normal_path) if (turned or recentred) else None,
                 'source_sha256': _quick_hash(scan['files'].get('normal') or made_normal),
                 'checked': time.strftime('%Y-%m-%d'), 'limit': limit, 'version': CHECK_VERSION, 'height_mean': float(height_array.mean()) if height_array is not None else None}
        info['normal_check'] = check
        write_info(work, info)
    elif check.get('file'):
        normal_path = os.path.join(work, check['file'])
    normal_image = _load(normal_path, f'pk_scan_{key}_nor', True)
    normal_image['pk_convention'] = 'opengl'
    normal_image['pk_height_partner'] = height_image.name if height_image is not None else ''
    colour_image = _load(files['colour'], f'pk_scan_{key}_colour', False)
    rough_image = _load(files['roughness'], f'pk_scan_{key}_rough', True) if files.get('roughness') else None
    colour_hash = _quick_hash(files['colour'])
    mean = info.get('colour_mean_linear') if info.get('colour_hash') == colour_hash else None
    if mean is None:
        array = normals.image_to_array(colour_image)[..., :3]
        step = max(1, array.shape[0] // 512)
        encoded = array[::step, ::step].reshape(-1, 3).astype(np.float64)
        linear = np.where(encoded <= 0.04045, encoded / 12.92, ((encoded + 0.055) / 1.055) ** 2.4)          # the picture is sRGB; the nodes work in linear light
        mean = [float(v) for v in linear.mean(axis=0)]
        info = read_info(work)
        info.update(colour_mean_linear=mean, colour_hash=colour_hash)
        write_info(work, info)
    return {'colour': colour_image, 'normal': normal_image, 'roughness': rough_image, 'height': height_image, 'colour_mean': mean,
            'height_mean': check.get('height_mean') if check.get('height_mean') is not None else 0.5, 'normal_check': check, 'turned': check.get('turned', [])}


def _quick_hash(path):
    """A short hash of a file's size and first megabyte (enough to see that a library picture was replaced)."""
    if not path or not os.path.exists(path):
        return None
    digest = hashlib.sha256(str(os.path.getsize(path)).encode())
    with open(path, 'rb') as handle:
        digest.update(handle.read(1 << 20))
    return digest.hexdigest()[:16]


def pack_images(images):
    """Packs the scan pictures into the .blend, so the file carries them to a rented card (the cache folder is only on this machine)."""
    from . import normals
    for image in images:
        if image is not None and not image.packed_file:
            normals.pack(image)
