# What this does (plain words): quick look at whether a sampled tile has the right overall tone: median brightness and mean colour on the brick faces and in the
# mortar, compared with the reference's. Use: python3 -I calibrate_check.py DESCRIPTION.json BAKED_FOLDER
import cv2, numpy as np, json, sys, os
W = 1254
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
def masks(rows, tile):
    m = np.zeros((tile, tile), np.uint8)
    for r in rows:
        for x0, x1, c in r['bricks']:
            for dx in (-tile, 0, tile):
                for dy in (-tile, 0, tile):
                    cv2.rectangle(m, (int(x0 + dx), int(r['y0'] + dy)), (int(x1 + dx), int(r['y1'] + dy)), 1, -1)
    return m > 0
def stats(img_path, rows):
    im = cv2.imread(img_path)
    m = masks(rows, im.shape[0])
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    rgb = im[..., ::-1].astype(float)
    return {'brick_rgb': rgb[m].mean(0).round(0).tolist(), 'brick_grey_median': float(np.median(g[m])), 'brick_grey_p10_p90': [float(np.percentile(g[m], 10)), float(np.percentile(g[m], 90))],
            'mortar_rgb': rgb[~m].mean(0).round(0).tolist(), 'mortar_grey_median': float(np.median(g[~m]))}
if __name__ == '__main__':
    ref_rows = json.load(open(os.path.join(HERE, 'descriptions', 'stage1_bricks_only.json')))['layers'][0]['rows']
    print('reference', stats(os.path.join(PROC, 'reference', 'brick', 'colour.png'), ref_rows))
    s = json.load(open(sys.argv[1]))
    print('sample   ', stats(os.path.join(sys.argv[2], 'colour.png'), [l for l in s['layers'] if l['type'] == 'bricks'][0]['rows']))
