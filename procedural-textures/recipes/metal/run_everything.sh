#!/bin/bash
# What this does (plain words): the list of commands that rebuilds everything in this folder from the reference pictures, in the order they were run.
# It is a record and a recipe, not something to run blindly: the Blender steps take a few minutes each and the measuring steps read the reference.
# The generator itself (generator/metal_generator.py) never reads the reference; only the scripts in analysis/ do.
HERE="$(cd "$(dirname "$0")" && pwd)"
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd "$HERE"

# --- A. measure the reference (analysis only) ---------------------------------------------------------------------------------------
python3 -I analysis/derivation_ceiling.py          # how the reference height and normal come from its colour (5.0 levels, 6.7 degrees)
python3 -I analysis/find_rivets.py                 # finds the 34 rivets by sliding a picture of one rivet over the tile
python3 -I analysis/measure_profiles.py            # edge profiles of the 6 bars (typical colours across each edge)
python3 -I analysis/measure_rivet.py               # typical rivet, ring by ring and slice by slice
python3 -I analysis/make_layout.py                 # writes description/layout_v0.json (bars, rivets, seams, edge profiles) and scores it with the fast preview

# --- B. wear: procedural layers (shader noise) and traced patches --------------------------------------------------------------------
python3 -I analysis/wear_v2.py; python3 -I analysis/make_wear_v3.py   # first guess of the wear layers, then the tuned layers
python3 -I analysis/try_wear.py final description/S_v3_uncal.json  # calibrate the thresholds with Blender and bake a trial (outputs/trial_final); prints the wear statistics next to the reference's
python3 -I analysis/build_descriptions.py          # S0, S, M and L descriptions (traced patches chosen by gain per byte on a healed copy of the reference)
python3 -I analysis/build_rd_descriptions.py       # the in-between descriptions for the rate-distortion table

# --- C. bake and compare ---------------------------------------------------------------------------------------------------------------
for name in S0 S M L; do python3 -I generator/bake_and_score.py $name --samples 8; done     # colour, height, normal, roughness, metallic, ao + both comparison tools
for name in layerA layerB R16k R32k R128k R256k; do python3 -I generator/bake_and_score.py $name --samples 8; done

# --- D. scale ----------------------------------------------------------------------------------------------------------------------------
python3 -I analysis/make_sampler_model.py                   # the numbers the random description generator draws from
python3 -I generator/run_variations.py                      # 8 new tiles from seeds 1..8 + differences between them
python3 -I generator/final_tests.py seam S0 S M L           # half-tile-shift seamless test
python3 -I generator/final_tests.py area 21                 # one 2508-dot picture of new unique content
python3 -I generator/final_tests.py resolution S L          # 512, 1254, 2508 dots

# --- E. real-geometry route and height comparison ------------------------------------------------------------------------------------------
$BLENDER -b --disable-autoexec -t 2 --python generator/metal_geometry_route.py -- description/S0.json outputs/geometry_route
python3 -I analysis/height_routes.py outputs/S0 outputs/geometry_route S0
python3 -I analysis/height_routes.py outputs/L outputs/geometry_route L

# --- F. transfer to a surface that was not given (ship's hull plates), description only ------------------------------------------------------
python3 -I transfer/make_hull_plates.py
python3 -I analysis/calibrate_wear.py description/hull_plates_uncal.json description/hull_plates.json
$BLENDER -b --disable-autoexec -t 2 --python generator/metal_generator.py -- description/hull_plates.json transfer/hull_plates --samples 8

# --- G. pictures for the guide, final numbers -----------------------------------------------------------------------------------------------
$BLENDER -b --disable-autoexec -t 2 --python generator/make_sweeps.py
for s in wear_size rust_amount streak_length edge_attraction grain layers; do python3 -I ../../lib/make_strip.py guide_pictures/sweep_$s guide_pictures/strip_$s.png --cell 300 --title "Metal: $s"; done
python3 -I generator/collect_final_report.py
