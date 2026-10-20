#!/bin/bash
# What this does: for each of the six recipes, bakes the colour picture once per "stage" (the picture after only the first n steps) at 256 px and joins
# them into one labelled strip, so the guide can show what each layer adds. Needs the recipes' 'stage' setting. Run from this folder: ./make_stage_strips.sh
HERE="$(cd "$(dirname "$0")" && pwd)"; PROC="$HERE/../.."
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
mkdir -p "$HERE/out/stages"
declare -A STAGES
STAGES[brick]="1 layout only|2 + colour per brick|3 + flat patches|4 + spalls and soot|5 + mortar, outline|6 + smudges, grain"
STAGES[slate]="1 layout: gaps|2 + brush strokes, tone per slate|3 + blotches|4 + moss|5 + lichen, chipped rim"
STAGES[wood]="1 boards and gaps|2 + splinter strips|3 + grain, grey patches, flakes|4 + cracks|5 + knots|6 + splatter, joints, pebbles"
STAGES[metal]="1 plate with brush streaks|2 + straps and braces|3 + rivets|4 + brown, scuffs, rust|5 + drips, bare-metal chips|6 + scratches"
STAGES[mud]="1 flat brown ground, streaks|2 + ruts|3 + puddles|4 + pebble clusters|5 + medium and big stones"
STAGES[gravel]="1 soil only|2 + tiny stones|3 + small stones|4 + medium stones|5 + large stones"
for surface in brick slate wood metal mud gravel; do
  IFS='|' read -ra LIST <<< "${STAGES[$surface]}"
  index=0
  for stage in "${LIST[@]}"; do
    folder="$HERE/out/stages/${surface}_$index"
    $BLENDER -b --disable-autoexec -t 2 --python "$PROC/lib/bake_harness.py" -- "$HERE/recipes/recipe_$surface.py" "$folder" --size 256 --params "{\"stage\": \"$stage\"}" > /dev/null 2>&1
    index=$((index+1))
  done
  python3 -I - "$HERE" "$surface" "${STAGES[$surface]}" <<'PY'
import sys, os, cv2, numpy as np
here, surface, labels = sys.argv[1], sys.argv[2], sys.argv[3].split('|')
tiles = []
for index, label in enumerate(labels):
    image = cv2.imread(os.path.join(here, 'out', 'stages', f'{surface}_{index}', 'colour.png'))
    image = cv2.resize(image, (256, 256), interpolation=cv2.INTER_AREA)
    banner = np.full((34, 256, 3), 245, np.uint8)
    cv2.putText(banner, label[:36], (5, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (20, 20, 20), 1, cv2.LINE_AA)
    tiles.append(np.vstack([banner, image]))
cv2.imwrite(os.path.join(here, 'pictures', f'layers_{surface}.png'), np.hstack(tiles))
print('wrote layers_' + surface)
PY
done
