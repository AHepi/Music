#!/bin/bash
# Plain note: one command that takes a Material Maker graph file (.ptex), exports its maps with the real program, shrinks them to
# 1254 x 1254, and scores them against a reference surface with the two comparison tools (texture_compare = same kind of surface?,
# pixel_compare = same picture, dot for dot?). Also makes a side-by-side picture.
# Usage: evaluate_candidate.sh GRAPH.ptex OUTPUT_FOLDER REFERENCE_NAME      (e.g. brick)
set -e
HERE=proc-work
MM=$HERE/third-party/material_maker
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
PTEX=$(realpath "$1"); OUT=$(realpath -m "$2"); REF=$3
STEM=$(basename "$PTEX" .ptex)
mkdir -p "$OUT/raw" "$OUT/maps"
cp "$PTEX" "$OUT/$STEM.ptex" 2>/dev/null || true
python3 -I $MM/tools/mm_export.py "$PTEX" "$OUT/raw"
$BL -b --disable-autoexec -t 2 --python $MM/tools/exr_to_png16.py -- "$OUT/raw/${STEM}_displace.exr" "$OUT/raw/${STEM}_rough.exr" "$OUT/raw/${STEM}_occlusion.exr" 2>&1 | grep -c "^EXR" >/dev/null
python3 -I $MM/tools/finish_maps.py "$OUT/raw" "$STEM" "$OUT/maps"
python3 -I $HERE/lib/texture_compare.py $REF "$OUT/maps" --json "$OUT/maps/score_texture_compare.json" --sheet "$OUT/maps/sheet_texture_compare.png" > "$OUT/maps/texture_compare.txt" 2>&1 || true
python3 -I $HERE/lib/pixel_compare.py $REF "$OUT/maps" --json "$OUT/maps/score_pixel_compare.json" --sheet "$OUT/maps/sheet_pixel_compare.png" > "$OUT/maps/pixel_compare.txt" 2>&1 || true
python3 -I $MM/tools/side_by_side.py $REF "$OUT/maps" "$OUT/maps/side.png" --normal
python3 -I - "$OUT/maps" <<'PY'
import json,sys
d=sys.argv[1]
t=json.load(open(d+'/score_texture_compare.json')); p=json.load(open(d+'/score_pixel_compare.json'))
print('texture_compare overall:', t.get('overall'), '| keys:', [k for k in t.keys()][:8])
print('pixel_compare: tier', p.get('tier_reached'), 'colour SSIM', p.get('colour_ssim'), 'dE', p.get('colour_mean_delta_e'), 'edge_skill', p.get('edge_skill_2px'), 'height_mae_best', p.get('height_mae_best_fit_levels'), 'normal_deg', p.get('normal_mean_angle_degrees'))
PY
