# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE SHEET MAKER of the walls layers. Two halves in one file:
#   1. DRAWING (Blender side, any set): draws a list of pictures of one scene, each with its own layers, look and dial values, with the kit's hook and chain:
#        blender -b --disable-autoexec SCENE.blend --python walls/sheet_walls.py -- SET_ID_OR_FILE SCENE_ID OUT_FOLDER CONFIG.json
#      CONFIG.json: {"size": [w, h], "samples": 24, "camera": "<name>", "extra_cameras": [{"name", "location", "look_at", "fov_v"}], "stack": false,
#                    "pictures": [{"name": "before", "layers": [], "look": null, "overrides": {"soot": {"film_mult": 0.7}}, "camera": "<optional>"}, ...]}
#      (an empty layer list is the picture before; layers go in through apply_walls.apply; the dials come from the look and the overrides; the scene is put back after each picture).
#      The main-scene pictures of the walls report were drawn through the kit's own picture runner (harness/runner.py, which does the same); this half is for scenes that have no lighting rigs
#      of their own, such as a garden set.
#   2. MONTAGE (plain Python with Pillow, no Blender): grid(items, columns, panel size, out_file, title) puts pictures (and crops of them) side by side with a label on each, as a JPG;
#      before_after(...) and crop helpers. Used for the pictures of the report; every picture is a JPG under 400 KB.
import json
import os
import sys

try:
    import bpy
except ImportError:
    bpy = None

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True


# ----------------------------------------------------------------------------------------------------------------------------- montage (Pillow)
def _font(size=18):
    from PIL import ImageFont
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/dejavu/DejaVuSans.ttf'):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def panel(path, size, label=None, crop=None):
    """One picture (or a crop box (left, top, right, bottom) of it) scaled to `size`, with a label in the corner."""
    from PIL import Image, ImageDraw
    image = Image.open(path).convert('RGB')
    if crop:
        image = image.crop(crop)
    image = image.resize(size, Image.LANCZOS)
    if label:
        draw = ImageDraw.Draw(image)
        font = _font(max(14, size[0] // 28))
        draw.rectangle([0, 0, draw.textlength(label, font=font) + 10, font.size + 8], fill=(0, 0, 0))
        draw.text((5, 3), label, fill=(255, 255, 255), font=font)
    return image


def grid(items, columns, size, out_file, title=None, quality=84, gap=4):
    """items: [(path, label) or (path, label, crop box)]. Writes a JPG and returns its size in bytes (a report picture must stay under 400 KB)."""
    from PIL import Image, ImageDraw
    rows = (len(items) + columns - 1) // columns
    top = 36 if title else 0
    sheet = Image.new('RGB', (columns * size[0] + (columns - 1) * gap, rows * size[1] + (rows - 1) * gap + top), (18, 18, 18))
    if title:
        ImageDraw.Draw(sheet).text((8, 6), title, fill=(235, 235, 235), font=_font(20))
    for index, item in enumerate(items):
        sheet.paste(panel(item[0], size, item[1], item[2] if len(item) > 2 else None), ((index % columns) * (size[0] + gap), top + (index // columns) * (size[1] + gap)))
    sheet.save(out_file, quality=quality, optimize=True)
    return os.path.getsize(out_file)


def before_after(before, after, out_file, size, crop=None, labels=('before', 'after'), title=None):
    return grid([(before, labels[0], crop), (after, labels[1], crop)], 2, size, out_file, title)


# ----------------------------------------------------------------------------------------------------------------------------- drawing (Blender)
def draw_pictures(set_ref, scene_id, out, config):
    from apply import kit as kit_module
    from harness import cameras, render
    from masks import bus as bus_module
    from walls import apply_walls
    size = tuple(config.get('size', (1200, 800)))
    samples = config.get('samples', 24)
    os.makedirs(out, exist_ok=True)
    k0 = kit_module.Kit.load(set_ref, scene_id=scene_id, strict=False)
    cams, _ = cameras.make_all(k0.settings, scene_id)
    for spec in config.get('extra_cameras', []):
        cams[spec['name']] = cameras._make('wk_' + spec['name'], spec['location'], look_at=spec.get('look_at'), fov_vertical=spec.get('fov_v', 40.0))
    default = cams.get(config.get('camera')) or bpy.context.scene.camera
    done = {}
    for pic in config['pictures']:
        kit = kit_module.Kit.load(set_ref, scene_id=scene_id, look=pic.get('look'), strict=False)
        bus_module.attach(kit)
        apply_walls.register(kit)
        kit.prepare()
        if pic.get('layers'):
            apply_walls.apply(kit, look=pic.get('look'), layers=pic['layers'], overrides=pic.get('overrides'))
        camera = cams.get(pic.get('camera')) or default
        path = os.path.join(out, pic['name'] + '.png')
        seconds = render.draw(path, size[0], size[1], samples, camera, raytracing=True, bits=8)
        kit.remove()
        done[pic['name']] = round(seconds, 2)
        print('DRAWN', pic['name'], round(seconds, 2), flush=True)
    json.dump(done, open(os.path.join(out, 'sheet_times.json'), 'w'), indent=1)


if bpy is not None and '--' in sys.argv:
    args = sys.argv[sys.argv.index('--') + 1:]
    draw_pictures(args[0], args[1], args[2], json.load(open(args[3])))
