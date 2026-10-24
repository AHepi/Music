"""What this file does (plain words): cuts the same box out of three pictures at the plate size (1536 x 2730): the same wet plate drawn with the kit's earlier layers alone (no kit; integrated/plates/lockout/final_lockout_B_wet_base.png), the kit's final wet plate, and the
painting lined up to the plate; puts them side by side at one scale. Run: python3 -I tools/crops.py NAME x0 y0 x1 y1 [scale]  -> work/crop_NAME.jpg"""
import sys, os
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/'
_cache = {}
def load():
    if not _cache:
        _cache['base'] = Image.open(B + 'grime_and_growth/integrated/plates/lockout/final_lockout_B_wet_base.png').convert('RGB')
        _cache['kit'] = Image.open(B + 'grime_and_growth/fix/plates/lockout/final_lockout_B_wet_kit.png').convert('RGB')
        _cache['paint'] = Image.open(os.path.join(HERE, 'pictures/kit_painting_lined_up.png')).convert('RGB')
        _cache['paint_r2'] = Image.open(B + 'painter_round_2/paint/front_painting_lined_up.png').convert('RGB')
        import numpy as np
        d = (np.asarray(_cache['kit']).astype(np.int32) - np.asarray(_cache['base']).astype(np.int32)) * 4 + 128   # what the kit added, x4, mid-grey = nothing
        _cache['delta'] = Image.fromarray(np.clip(d, 0, 255).astype(np.uint8))
    return _cache
def crop3(name, box, scale=1.0, which=('base', 'kit', 'paint'), out=None):
    c = load(); x0, y0, x1, y1 = box
    w, h = int((x1 - x0) * scale), int((y1 - y0) * scale)
    sheet = Image.new('RGB', (w * len(which) + 6 * (len(which) - 1), h), (255, 255, 255))
    for i, k in enumerate(which):
        sheet.paste(c[k].crop(box).resize((w, h), Image.LANCZOS), (i * (w + 6), 0))
    p = out or os.path.join(HERE, 'work/crop_%s.jpg' % name)
    sheet.save(p, quality=90)
    return p
if __name__ == '__main__':
    name = sys.argv[1]; box = tuple(int(v) for v in sys.argv[2:6]); scale = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
    which = tuple(sys.argv[7].split(',')) if len(sys.argv) > 7 else ('base', 'kit', 'paint')
    print(crop3(name, box, scale, which))
