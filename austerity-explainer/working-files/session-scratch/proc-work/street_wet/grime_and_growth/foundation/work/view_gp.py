import sys, json, numpy as np, cv2
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering')
from masks import pack
d = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/masks/packs/pit_village_street/street'
m = json.load(open(d + '/manifest.json'))
cache = {}
def get(name):
    e = m['masks']['GP'][name]
    pic = e['picture']
    if pic not in cache: cache[pic] = pack.read_png(d + '/' + m['pictures'][pic]['file'])
    a = cache[pic]
    ch = 'RGBA'.index(e['channel'])
    return a[..., ch]
names = sys.argv[2].split(',')
y0, y1 = float(sys.argv[3]), float(sys.argv[4])
tiles = []
for n in names:
    a = get(n)
    if a.shape[0] != 2100:   # fine grid or other: resize to normal
        a = cv2.resize(a, (225, 2100), interpolation=cv2.INTER_AREA)
    r0, r1 = int((y0 + 12) / 0.04), int((y1 + 12) / 0.04)
    t = np.flipud(a[r0:r1])
    t = (np.clip(t, 0, 1) * 255).astype(np.uint8)
    t = cv2.cvtColor(t, cv2.COLOR_GRAY2BGR)
    cv2.putText(t, n, (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
    tiles.append(t); tiles.append(np.full((t.shape[0], 4, 3), 60, np.uint8))
cv2.imwrite(sys.argv[1], np.concatenate(tiles, axis=1), [cv2.IMWRITE_JPEG_QUALITY, 85])
print('written', sys.argv[1])
