#!/bin/bash
# What this file does (plain words): draws a few stills of OTHER existing scenes of the film (not the lockout) from the COPY of the film's stage, into stills/FOLDER/, to prove that the brightness fix changes nothing in them:
#   notice_end   = the notice corner clip held on its composed frame (6.0 s)        notice_move = the notice corner clip's slide at 4.5 s
#   chapter2_a/b = two moments of "inflation chapter 2 for newcomers" (a page-by-page cinema chapter with paper cut-outs and charts, 30 s and 75 s)
#   chapter1_a   = a moment of "austerity chapter 1" (40 s)
# Run: bash tools/render_other_scenes.sh FOLDER     (before the fix, then again after the fix; the two folders are then compared pixel by pixel)
HERE="$(cd "$(dirname "$0")/.." && pwd)"
D="$HERE/tools/draw.sh"
F="${1:?folder name: before or after}"
(
 bash "$D" $F notice_end   "view=end" 6.0 notice-corner
 bash "$D" $F notice_move  "x=1" 4.5 notice-corner
) &
(
 bash "$D" $F chapter2_a "x=1" 30.0 inflation-chapter-2-newcomers
 bash "$D" $F chapter2_b "x=1" 75.0 inflation-chapter-2-newcomers
 bash "$D" $F chapter1_a "x=1" 40.0 austerity-chapter-1
) &
wait
echo "ALL DONE $(date +%T)"
