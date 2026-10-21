#!/bin/bash
# What this file does (plain words): draws ONE still picture (at a given second) of one scene of the COPY of the film's stage (kit_copy), through the film's own renderer,
# in a hidden Chromium with software graphics. Settings go in the address (PAPER_FILM_QUERY), for example "view=moved&painting=lockout-r2-front.jpg&behind=lockout-r2-behind.jpg".
# Run: bash tools/draw.sh FOLDER NAME "QUERY" [SECOND=6.0] [SCENE=lockout-test]     -> stills/FOLDER/NAME/still-SECOND.jpg
# FOLDER is "before" (the film's own stage code) or "after" (the stage code with the fix), see the notes.
HERE="$(cd "$(dirname "$0")/.." && pwd)"
R="$HERE/kit_copy/paper-film/tools/render-paper-film.mjs"
FOLDER="$1"; NAME="$2"; QUERY="$3"; SEC="${4:-6.0}"; SCENE="${5:-lockout-test}"
OUT="$HERE/stills/$FOLDER/$NAME"
mkdir -p "$OUT"
echo "=== $FOLDER/$NAME  ($SCENE, $SEC s, $QUERY)  $(date +%T)"
PAPER_FILM_QUERY="$QUERY" node "$R" "$SCENE" "$OUT" --stills "$SEC" 2>&1 | grep -E "still-|rror" | tail -3
