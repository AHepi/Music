#!/bin/bash
# What this file does (plain words): draws the plate view (the first frame of the film) of the lockout scene with the new wet front painting several times, each time with some steps of the stage's finishing look switched off or changed
# (needs the "diagnostic" state of the stage copy: python3 -I tools/patch_engine.py diagnostic), into stills/diagnosis/. This is the real-stage evidence for which step costs how much brightness (the Python copy of the finish, finish_model.py, only predicts it).
#   off_all      = nothing of the finish left except the painting itself (filmic curve off, contrast 1.0, lift 0, tint off, frame edge off, grain off): the painting should arrive exactly as painted
#   only_edge    = only the dark frame edge (vignette 0.3) on             only_curve = only the filmic curve on            only_cl = only contrast 1.04 and lift 0.015 on        only_tint = only the cool/warm tint on
#   film_no_edge = the film's look with the frame edge off
# And the candidate fixes (toe = the curve may brighten but never darken), wet and dry:
#   toe1, toe1_v25, toe1_v20, toe1_cl (contrast 1.0 and lift 0), and the film's dry painting with toe1_v25 and toe1_v20
# Run: bash tools/render_diagnosis.sh
HERE="$(cd "$(dirname "$0")/.." && pwd)"
D="$HERE/tools/draw.sh"
FRONT="painting=lockout-r2-front.jpg"; BEHIND="behind=lockout-r2-behind.jpg"
OFF="lk_curve=0&lk_contrast=1&lk_lift=0&lk_tintAmount=0&lk_vignette=0&lk_grain=0"
V="view=projector&$FRONT&$BEHIND"
(
 bash "$D" diagnosis off_all      "$V&$OFF"
 bash "$D" diagnosis only_edge    "$V&$OFF&lk_vignette=0.3"
 bash "$D" diagnosis only_curve   "$V&$OFF&lk_curve=1"
 bash "$D" diagnosis only_cl      "$V&$OFF&lk_contrast=1.04&lk_lift=0.015"
 bash "$D" diagnosis only_tint    "$V&$OFF&lk_tintAmount=0.35"
 bash "$D" diagnosis film_no_edge "$V&lk_vignette=0"
) &
(
 bash "$D" diagnosis toe1         "$V&lk_toe=1"
 bash "$D" diagnosis toe1_v25     "$V&lk_toe=1&lk_vignette=0.25"
 bash "$D" diagnosis toe1_v20     "$V&lk_toe=1&lk_vignette=0.20"
 bash "$D" diagnosis toe1_cl      "$V&lk_toe=1&lk_contrast=1&lk_lift=0"
 bash "$D" diagnosis dry_toe1_v25 "view=projector&lk_toe=1&lk_vignette=0.25"
 bash "$D" diagnosis dry_toe1_v20 "view=projector&lk_toe=1&lk_vignette=0.20"
) &
wait
echo "ALL DONE $(date +%T)"
