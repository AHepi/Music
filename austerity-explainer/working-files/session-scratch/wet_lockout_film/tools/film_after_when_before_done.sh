#!/bin/bash
# What this file does (plain words): waits until the dry ("before") clip has been filmed and joined, checks that the checking copy of the kit (kit_check) still holds
# exactly the film project's stage, scenes and tools, then films the wet clip from it the way the kit films it (film-chapter-parallel.sh, 2 at a time, 240-frame chunks).
W="$(cd "$(dirname "$0")/.." && pwd)"
while [ ! -s "$W/kit_before/paper-film/out/lockout-test-silent.mp4" ]; do sleep 10; done
echo "before clip finished $(date +%T)"
R=/home/user/Music/austerity-explainer/film-kit
for t in stage scenes tools; do diff -rq "$W/kit_check/paper-film/$t" "$R/paper-film/$t" | grep -v "Only in $W/kit_check/paper-film/scenes: lockout-.*-hook.js"; done
for f in lockout-painted.jpg lockout-behind.jpg lockout-painted-dry.jpg lockout-behind-dry.jpg; do cmp "$W/kit_check/assets/models/pit-village/$f" "$R/assets/models/pit-village/$f" || echo "DIFFERENT $f"; done
cmp "$W/kit_check/examples/lockout-test/timeline.json" "$R/examples/lockout-test/timeline.json" || echo "DIFFERENT timeline"
echo "copy checked $(date +%T)"
cd "$W/kit_check" && bash paper-film/tools/film-chapter-parallel.sh lockout-test 2 240
echo "after clip finished $(date +%T)"
