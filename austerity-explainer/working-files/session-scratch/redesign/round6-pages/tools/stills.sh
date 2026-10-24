#!/bin/bash
# What this does: draws stills of chapter 2 for newcomers at the given moments (seconds) into OUT, one render at a time.
# Use: bash stills.sh OUT SECONDS ...
set -u
out="$1"; shift; mkdir -p "$out"
cd /home/user/Music/austerity-explainer/film-kit
node paper-film/tools/render-paper-film.mjs inflation-chapter-2-newcomers "$out" --stills "$@" > "$out/render.log" 2>&1
grep -c "still-" "$out/render.log"; grep "check \|page 5:\|Error" "$out/render.log" | sort -u
