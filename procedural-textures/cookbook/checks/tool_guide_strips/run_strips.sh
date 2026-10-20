#!/bin/sh
# What this does (plain words): makes every NEW strip used by "06 Guide - pattern makers.md" and "06 Guide - shapers.md".
# Step 1 runs make_tool_guide_strips.py inside Blender (small 256-dot squares in work/, measured numbers in numbers.json).
# Step 2 joins each folder of squares into one labelled strip with lib/make_strip.py, then saves it as a small JPG in
# cookbook/pictures/ (the PNG versions were 180 to 670 KB; the JPGs are 45 to 155 KB). Takes about 15 seconds of Blender time.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
WORK_ROOT=$(cd "$HERE/../../.." && pwd)
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
W="$HERE/work"
P="$WORK_ROOT/cookbook/pictures"
mkdir -p "$W"
"$BLENDER" -b --disable-autoexec -t 2 --python "$HERE/make_tool_guide_strips.py" > "$W/run.log" 2>&1
strip() { python3 -I "$WORK_ROOT/lib/make_strip.py" "$W/$1" "$P/$2.png" --title "$3"; }
strip wave_phase_offset pattern-strip-wave-phase-offset "Wave Texture: Phase Offset (Bands X, Sine, 5 bands)"
strip noise_normalize pattern-strip-noise-normalize "Noise Texture: Normalize on and off (true values; below 0 = black, above 1 = white)"
strip radial_tiling_facets pattern-strip-radial-tiling-facets "Radial Tiling: Segment Rotation as facet shading (a rivet head)"
strip math_compare_width shaper-strip-math-compare-width "Math Compare (value = 0.5 within Epsilon): line width"
strip clamp shaper-strip-clamp "Clamp on a noise (0..1): it cuts the ends but does not stretch"
strip mix_factor shaper-strip-mix-factor "Mix, Multiply: soot over brick, Factor = stain mask x amount"
strip mix_stain_modes shaper-strip-mix-stain-modes "Mix blend modes for the same soot stain (Factor = mask x 1)"
strip separate_combine shaper-strip-separate-combine "Separate and Combine (noise tiles stretched 0.3..0.7 to 0..1)"
strip ramp_threshold_share shaper-strip-ramp-stop-and-share "Color Ramp Constant on raw noise: where the rust stop sits"
python3 -I -c "
import cv2, glob, os, sys
folder = sys.argv[1]
for path in sorted(glob.glob(os.path.join(folder, 'pattern-strip-*.png')) + glob.glob(os.path.join(folder, 'shaper-strip-*.png'))):
    cv2.imwrite(path[:-4] + '.jpg', cv2.imread(path), [cv2.IMWRITE_JPEG_QUALITY, 90])
    os.remove(path)
    print(path[:-4] + '.jpg', os.path.getsize(path[:-4] + '.jpg'))
" "$P"
