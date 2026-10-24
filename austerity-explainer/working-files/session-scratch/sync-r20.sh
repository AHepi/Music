#!/bin/bash
# Copies round 20's working files from the live kit into the repository (safe to run again).
set -eu
KIT=/home/user/work/paper-pop-up-film-kit
REPO=/home/user/Music/austerity-explainer/chapter-2-inflation
FC=$REPO/film-code
mkdir -p "$FC/scenes/inflation-chapter-2" "$FC/stage" "$FC/tools" "$FC/blender" "$REPO/pictures/models" "$REPO/pictures/reliefs" "$REPO/pictures/pieces"
for f in cinema-chapter.js cinema-kit.js cinema-test-pages.js effects.js graphics.js models.js model-loader.js model-preview.js inflation-chapter-2.js; do cp "$KIT/paper-film/scenes/$f" "$FC/scenes/$f"; done
cp "$KIT"/paper-film/scenes/inflation-chapter-2/*.js "$FC/scenes/inflation-chapter-2/"
cp "$KIT"/paper-film/stage/cinema-stage.* "$FC/stage/"
for f in film-chapter-parallel.sh prepare_relief.py relief_points.py render-paper-film.mjs camera_audit.py frame_check.py tone_piece.py; do cp "$KIT/paper-film/tools/$f" "$FC/tools/$f"; done
cp "$KIT"/paper-film/blender/*.py "$FC/blender/"
cp "$KIT"/assets/models/inflation-chapter-2/*.glb "$REPO/pictures/models/"
cp "$KIT"/assets/reliefs/inflation-chapter-2/406b-* "$REPO/pictures/reliefs/"
cp "$KIT"/paper-film/pieces/inflation-chapter-2/politician-{face,jaw,mouth}.png "$REPO/pictures/pieces/"
cp "/home/user/work/chapter-2/reference/21 Guide - camera rule, filling the frame, no clipping.md" "$REPO/20 Guide - camera rule, filling the frame, no clipping.md"
echo "synced"
