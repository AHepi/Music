#!/bin/bash
# What this does: draws the notice corner at 4.5 s and 10 s three ways, one after another (scratch test of the
# kit sync): the plugin kit's copy, the plugin kit with skyCard(), and the film kit's own copy.
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/sync-kit
K=$S/setup-test/film-kit
F=/home/user/Music/austerity-explainer/film-kit
echo "start $(date +%T)"; cd $K && timeout 900 node paper-film/tools/render-paper-film.mjs notice-corner $S/renders/plugin-notice --stills 4.5 10
echo "start $(date +%T)"; cd $K && timeout 900 node paper-film/tools/render-paper-film.mjs notice-corner-skycard-test $S/renders/plugin-skycard --stills 4.5 10
echo "start $(date +%T)"; cd $F && timeout 900 node paper-film/tools/render-paper-film.mjs notice-corner $S/renders/filmkit-notice --stills 4.5 10
echo ALL-DONE
