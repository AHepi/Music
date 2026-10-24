# What this does: measures the seam of every height picture in a folder (seam_ratio about 1.0 = seamless) and writes a half-tile-shifted contact sheet.
import sys, json, os
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/research/experiments_seamless_tiles_and_baking')
import measure_seams as ms, numpy as np
folder, out_json, out_sheet = sys.argv[1:4]
names = sorted(f[:-4] for f in os.listdir(folder) if f.endswith('.png'))
greys = {n: ms.load_grey(os.path.join(folder, n + '.png')) for n in names}
results = {n: ms.measure(greys[n]) for n in names}
json.dump(results, open(out_json, 'w'), indent=1)
ms.sheet(names, greys, results, out_sheet, columns=4, cell=256)
for n in names: print(f'{n:22s} seam_ratio {results[n]["seam_ratio"]:6}  x {results[n]["seam_x"]:6}  y {results[n]["seam_y"]:6}  peak {results[n]["seam_peak"]}')
