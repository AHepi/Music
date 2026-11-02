#!/bin/bash
# What this does: paints the tea house picture (B) with brushstrokes six different ways, one after the other.
cd /home/claude/brushstroke-trial
SCENE=/home/claude/blind-test-2/plugin-build/DRESSED-4.blend
BASE=/home/claude/blind-test-2/plugin-build/round-2.png
RES=/home/claude/downloads/brushstroke-tools/extracted/assets/core/brushstroke_tools-resources.blend
STY=/home/claude/downloads/brushstroke-tools/extracted/assets/styles/brushstroke_tools-oil_brushes.blend
run() {
  name=$1; shift
  start=$(date +%s)
  python3 paint_over.py -- $SCENE $BASE "out/variations/$name.png" --resources $RES --styles $STY --samples 24 "$@" > "out/variations/$name.log" 2>&1
  echo "$name: exit $? in $(( $(date +%s) - start )) s"
}
run "B fine strokes" --style fat --width 0.25 --length 0.7 --density 4.5
run "C medium strokes" --style fat --width 0.45 --length 1.1 --density 3
run "D large strokes" --style fat --width 0.8 --length 1.8 --density 1.8
run "E medium strokes, dry brush" --style dry --width 0.45 --length 1.1 --density 3
run "F medium strokes, feathery brush" --style feathery --width 0.45 --length 1.1 --density 3
run "G medium strokes, foreground left as drawn" --style fat --width 0.45 --length 1.1 --density 3 --start-at 7
echo "all done $(date +%H:%M:%S)"
