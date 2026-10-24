#!/bin/bash
# What this file does (plain words): draws ONE still picture of one scene through a kit's own renderer (hidden Chromium, software graphics).
# Run: bash draw_still.sh KIT_FOLDER OUT_FOLDER NAME "QUERY" SECOND SCENE     -> OUT_FOLDER/NAME/still-SECOND.jpg   (KIT_FOLDER holds paper-film/)
KIT="$1"; OUT="$2/$3"; QUERY="$4"; SEC="$5"; SCENE="$6"
mkdir -p "$OUT"
echo "=== $3 ($SCENE, $SEC s, $QUERY) kit=$(basename $KIT) $(date +%T)"
PAPER_FILM_QUERY="$QUERY" node "$KIT/paper-film/tools/render-paper-film.mjs" "$SCENE" "$OUT" --stills "$SEC" 2>&1 | grep -E "still-|rror" | tail -3
