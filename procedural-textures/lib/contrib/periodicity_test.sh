#!/bin/bash
# What this does: the strictest seamlessness test: bake a recipe normally, then bake it again with the whole pattern slid by half a tile in
# u and v; if the recipe really repeats every 1.0, the second picture must be the first one rolled by half its size. Prints the average and
# the share of pixels that differ by more than 40/255. A result near 0 means a true seamless tile (a few hard-edge pixels differ from anti-aliasing).
# Use: ./periodicity_test.sh recipes/recipe_brick.py brick 256
RECIPE=$1; NAME=$2; SIZE=${3:-256}
HERE="$(cd "$(dirname "$0")" && pwd)"; PROC="$HERE/../.."
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
$BLENDER -b --disable-autoexec -t 2 --python "$PROC/lib/bake_harness.py" -- "$RECIPE" "$HERE/out/per_${NAME}_a" --size $SIZE >/dev/null 2>&1
$BLENDER -b --disable-autoexec -t 2 --python "$PROC/lib/bake_harness.py" -- "$RECIPE" "$HERE/out/per_${NAME}_b" --size $SIZE --params '{"shift": [0.5, 0.5]}' >/dev/null 2>&1
python3 -I - "$HERE/out/per_${NAME}_a/colour.png" "$HERE/out/per_${NAME}_b/colour.png" "$NAME" <<'PY'
import sys, cv2, numpy as np
a = cv2.imread(sys.argv[1]).astype(float); b = cv2.imread(sys.argv[2]).astype(float)
n = a.shape[0]
rolled = np.roll(a, (n // 2, n // 2), axis=(0, 1))
d = np.abs(rolled - b).mean(axis=2)
# for comparison: the same picture rolled by a different amount should differ a lot
wrong = np.abs(np.roll(a, (n // 2 + 7, n // 2 - 5), axis=(0, 1)) - b).mean(axis=2)
print(f'{sys.argv[3]}: shifted-by-half vs rolled: mean diff {d.mean():.2f}/255, pixels differing > 40: {100*(d>40).mean():.2f}%   (control, rolled wrongly: mean {wrong.mean():.2f}, {100*(wrong>40).mean():.2f}%)')
PY
