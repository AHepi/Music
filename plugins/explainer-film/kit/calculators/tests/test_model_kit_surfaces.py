"""What this does: tests the two helpers that build the film's 3D models (kit/paper-film/blender/textures.py and model_kit.py) after they were changed so that
(1) they need no Pillow (Blender's own Python has none), (2) normal maps are written as lossless PNG files, and (3) every bevelled edge carries hardened normals and a Weighted
Normal modifier, so a big flat face shades evenly right up to its edge.
Parts:
  A. always (plain Python, Pillow blocked on purpose): textures.py imports and makes pictures with no Pillow; a picture written by its own PNG writer reads back exactly the same
     (checked with a small decoder written here, and with Pillow too when Pillow is installed); a JPEG without Pillow fails with a plain sentence, not a crash deep inside.
  B. when Blender is there (BLENDER, or machine-settings.env, or the PATH): fixtures/model_kit/check_bevel.py runs inside Blender with Pillow blocked: the bevel jump in shading
     falls (measured: a flat-shaded bevel jumps 50 degrees between neighbouring strips, the hardened one about 16), the modifiers are the two named, the big face stays exactly
     flat, the normal map is a PNG marked Non-Color, a colour picture is a PNG when Pillow is missing, and the .glb still writes with its PNG inside. The drawn comparison
     (old and new bevel side by side) is saved by that script when asked, for a person to look at.
Run: python3 kit/calculators/tests/test_model_kit_surfaces.py   (about 5 seconds; with Blender about 10 more)
"""
import json
import os
import struct
import subprocess
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import Checker, KIT, FIXTURES, blender_program, work_folder  # noqa: E402

BLENDER_FOLDER = os.path.join(KIT, 'paper-film', 'blender')
FIXTURE = os.path.join(FIXTURES, 'model_kit', 'check_bevel.py')
check = Checker('film model helpers: no Pillow, lossless normal maps, hardened bevels')
folder = work_folder('model-kit-test-')


def decode_png(path):
    """A small PNG reader written for this test (8 bit, no interlace, filters 0 to 4): returns an array (height, width, channels). It checks every chunk's CRC."""
    with open(path, 'rb') as handle:
        data = handle.read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a PNG'
    position, header, joined = 8, None, b''
    while position < len(data):
        length = struct.unpack('>I', data[position:position + 4])[0]
        kind, body = data[position + 4:position + 8], data[position + 8:position + 8 + length]
        crc = struct.unpack('>I', data[position + 8 + length:position + 12 + length])[0]
        assert crc == zlib.crc32(kind + body) & 0xffffffff, f'bad CRC in chunk {kind!r}'
        if kind == b'IHDR':
            header = struct.unpack('>IIBBBBB', body)
        elif kind == b'IDAT':
            joined += body
        position += 12 + length
    width, height, depth, colour_type, _, _, interlace = header
    assert depth == 8 and interlace == 0
    channels = {0: 1, 2: 3, 6: 4}[colour_type]
    raw = np.frombuffer(zlib.decompress(joined), dtype=np.uint8).reshape(height, width * channels + 1)
    out = np.zeros((height, width * channels), dtype=np.uint8)
    for row in range(height):
        kind_of_filter, line = raw[row, 0], raw[row, 1:].astype(np.int32)
        previous = out[row - 1].astype(np.int32) if row else np.zeros(width * channels, dtype=np.int32)
        if kind_of_filter == 0:
            current = line
        elif kind_of_filter == 2:
            current = (line + previous) & 255
        elif kind_of_filter == 1:
            current = line.copy()
            for i in range(channels, width * channels):
                current[i] = (current[i] + current[i - channels]) & 255
        else:
            raise AssertionError(f'filter {kind_of_filter} is not used by the writer')
        out[row] = current
    return out.reshape(height, width, channels)


# ---------------------------------------------------------------- A. no Pillow needed
sys.modules['PIL'] = None                                  # from here on, `import PIL` raises ImportError, as it does in Blender
sys.path.insert(0, BLENDER_FOLDER)
import textures  # noqa: E402

check.true('textures.py imports with Pillow blocked', 'textures' in sys.modules, 'imported', recorded='Blender has no Pillow; the module used to start with `from PIL import Image`')
colour, normal, units = textures.brick('red', size=128, seed=3)
check.equal('a made picture is a Picture holding whole numbers 0..255 and knows its size', (type(colour).__name__, colour.pixels.dtype.name, colour.size), ('Picture', 'uint8', (128, 128)))

for name, array in (('colour', colour.pixels), ('normal map', normal.pixels), ('one channel', colour.pixels[:, :, 0]), ('four channels', np.dstack([colour.pixels, 255 - colour.pixels[:, :, :1]]))):
    target = os.path.join(folder, name.replace(' ', '-') + '.png')
    textures.write_png(target, array)
    back = decode_png(target)
    expected = array if array.ndim == 3 else array[:, :, None]
    check.true(f'a PNG of the {name} reads back exactly the same, every pixel (decoded by the test\'s own reader, every CRC checked)', back.shape == expected.shape and np.array_equal(back, expected), f'largest difference {int(np.abs(back.astype(int) - expected.astype(int)).max())}')

noise = np.random.default_rng(1).integers(0, 256, (37, 53, 3), dtype=np.uint8)          # an odd size, and values that wrap when rows are subtracted
textures.write_png(os.path.join(folder, 'noise.png'), noise)
check.true('a picture of pure noise, odd in size, also reads back exactly (the row differences wrap around correctly)', np.array_equal(decode_png(os.path.join(folder, 'noise.png')), noise))

normal.save(os.path.join(folder, 'brick-normal.png'))
try:
    colour.save(os.path.join(folder, 'brick.jpg'), quality=90)
    message = 'no error'
except RuntimeError as problem:
    message = str(problem)
check.true('writing a JPEG with no Pillow stops with a plain sentence that says what to do (write a PNG, or run outside Blender)', 'Pillow is not installed' in message and 'png' in message.lower(), message[:120])

full, full_normal, _ = textures.brick('red')
textures.write_png(os.path.join(folder, 'full-normal.png'), full_normal.pixels)
size_bytes = os.path.getsize(os.path.join(folder, 'full-normal.png'))
check.within('a full-size (1024 pixel) normal map as a PNG stays a sensible size for a .glb (megabytes)', size_bytes / 1e6, 0.1, 4.0, recorded=f'measured: {size_bytes / 1e6:.2f} MB for the brick normal map')

# Pillow, when it is installed, must agree (run in a separate process, since Pillow is blocked above)
np.save(os.path.join(folder, 'colour.npy'), colour.pixels)
reading = ('import sys, numpy as np\nfrom PIL import Image\n'
           'a = np.array(Image.open(sys.argv[1]).convert("RGB")); b = np.load(sys.argv[2])\nprint(int(np.abs(a.astype(int) - b.astype(int)).max()), a.shape == b.shape)\n')
done = subprocess.run([sys.executable, '-I', '-c', reading, os.path.join(folder, 'colour.png'), os.path.join(folder, 'colour.npy')], capture_output=True, text=True)
if 'No module named' in done.stderr:
    check.note('skipped: Pillow is not installed here, so its own reading of the kit\'s PNG was not compared (the test\'s own decoder above did the check)')
else:
    check.equal('Pillow opens the kit\'s PNG and reads the same pixels (largest difference, same shape)', done.stdout.split(), ['0', 'True'])

# ---------------------------------------------------------------- B. inside Blender
blender = blender_program()
if not blender:
    check.note('skipped: Blender was not found (set BLENDER, run explainer-film-setup, or put blender on the PATH), so the bevel and the .glb were not tried')
else:
    environment = dict(os.environ, MODEL_KIT_FOLDER=BLENDER_FOLDER)
    picture = os.environ.get('MODEL_KIT_PICTURE', '')
    command = ['xvfb-run', '-a', blender] if picture else [blender]                         # only the optional drawing needs a display; the checks do not
    command += ['-b', '--disable-autoexec', '--python', FIXTURE, '--', folder] + ([picture] if picture else [])
    done = subprocess.run(command, capture_output=True, text=True, timeout=600, env=environment)
    row = [line for line in done.stdout.splitlines() if line.startswith('RESULT ')]
    if not row:
        check.true('the Blender check ran and printed its result', False, (done.stdout + done.stderr)[-500:])
    else:
        result = json.loads(row[0][len('RESULT '):])
        flat, hard = result['flat'], result['hardened']
        check.equal('the new bevel carries a bevel modifier with hardened normals AND a Weighted Normal modifier', (hard['modifiers_before_apply'], hard['harden_flag']), ([['BEVEL', 'bevel'], ['WEIGHTED_NORMAL', 'weighted-normal']], True))
        check.equal('the old plain bevel (HARDEN_BEVEL_NORMALS = False) is still available and has neither', (flat['modifiers_before_apply'], flat['harden_flag']), ([['BEVEL', 'bevel']], False))
        check.true('the shading jump between neighbouring strips of a bevel falls to under half of the flat-shaded one', hard['jump_degrees'] < 0.5 * flat['jump_degrees'], f'{flat["jump_degrees"]:.1f} degrees flat-shaded, {hard["jump_degrees"]:.1f} hardened', recorded='measured on a 2 m box, bevel 0.1 m, 2 segments')
        check.true('the big flat face stays exactly flat in both (no normal tilts away from the face)', flat['big_face_min_dot'] > 0.9999 and hard['big_face_min_dot'] > 0.9999, f'least dot {hard["big_face_min_dot"]:.4f}')
        check.equal('both bevels make the same shape (same number of faces); only the shading differs', flat['faces'], hard['faces'])
        images = result['images']
        check.equal('the normal map is a PNG marked Non-Color', images.get('slate-normal.png'), ['.png', 'Non-Color'])
        check.equal('with Pillow missing the colour picture is a PNG marked sRGB (not an error)', images.get('slate.png'), ['.png', 'sRGB'])
        check.true('the .glb still writes with its PNG pictures and its normals inside', result['glb_bytes'] > 10000 and result['glb_has_png'] and result['glb_has_normals'], f'{result["glb_bytes"] / 1e6:.2f} MB')
        if result.get('picture'):
            check.note(f'the old and new bevel drawn side by side: {result["picture"]}')

check.finish()
