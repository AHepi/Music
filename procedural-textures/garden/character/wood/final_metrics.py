"""final_metrics.py - value range, saturation and detail energy of a 2400x1600 picture (same maths as concept/hf_measure_second_helper.py).
Runs with plain python3 (numpy + PIL) or inside Blender (reads the PNG through bpy):
   python3 final_metrics.py IMAGE.png [OUT.json] [--jpg PREVIEW.jpg] [--crop NAME x0 y0 x1 y1 OUT.jpg]
   blender -b --python final_metrics.py -- IMAGE.png OUT.json ..."""
import sys, os, json
import numpy as np

BOXES = {"roof": (700, 300, 1500, 500), "bridge": (0, 1250, 900, 1500), "grass fg": (1500, 1350, 2400, 1600), "maple": (100, 300, 800, 700),
         "sand": (1700, 900, 2300, 1300), "wall": (1500, 580, 2300, 800), "rock": (200, 840, 420, 1050), "deck_hero": (0, 1050, 1000, 1250)}


def load_rgb(path):
    try:
        from PIL import Image
        return np.asarray(Image.open(path).convert('RGB')).astype(np.float32) / 255.0
    except ImportError:
        import bpy
        img = bpy.data.images.load(path)
        img.colorspace_settings.name = 'Non-Color'
        w, h = img.size
        px = np.array(img.pixels[:], np.float32).reshape(h, w, 4)[::-1, :, :3]
        bpy.data.images.remove(img)
        return px


def gblur(a, sigma=2.0):
    r = int(3 * sigma + 1)
    x = np.arange(-r, r + 1)
    k = np.exp(-x * x / (2 * sigma * sigma)); k /= k.sum()
    p = np.pad(a, ((r, r), (0, 0)), mode='reflect')
    a = sum(k[i] * p[i:i + a.shape[0]] for i in range(2 * r + 1))
    p = np.pad(a, ((0, 0), (r, r)), mode='reflect')
    return sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))


def metrics(a):
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    l8 = np.round(lum * 255)
    hf = np.abs(l8 - gblur(l8, 2.0))
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    out = {"percentiles": {str(p): round(float(np.percentile(lum, p)), 4) for p in (1, 5, 25, 50, 75, 95, 99)}, "mean_lum": round(float(lum.mean()), 4), "mean_saturation": round(float(sat.mean()), 4),
           "detail_energy": {k: round(float(hf[y0:y1, x0:x1].mean()), 2) for k, (x0, y0, x1, y1) in BOXES.items() if y1 <= hf.shape[0] and x1 <= hf.shape[1]}}
    return out


def main(argv):
    path = argv[0]
    outj = argv[1] if len(argv) > 1 and not argv[1].startswith('--') else None
    a = load_rgb(path)
    m = metrics(a)
    print('FINAL_METRICS', os.path.basename(path), json.dumps(m))
    if outj:
        json.dump(m, open(outj, 'w'), indent=1)
    if '--jpg' in argv or '--crop' in argv:
        from PIL import Image
        im = Image.fromarray((a * 255 + 0.5).astype(np.uint8))
        if '--jpg' in argv:
            im.resize((1200, 800), Image.LANCZOS).save(argv[argv.index('--jpg') + 1], quality=85)
        if '--crop' in argv:
            i = argv.index('--crop')
            x0, y0, x1, y1 = [int(v) for v in argv[i + 2:i + 6]]
            im.crop((x0, y0, x1, y1)).save(argv[i + 6], quality=86)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    main(args)
