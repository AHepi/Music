#!/bin/bash
# What this file does (plain words): three more stage stills from the COPY of the film's lockout stage: the film's own street move (default view) at 6.0 s, about three quarters
# of the way through the move, for the dry painting, the new wet painting with the film's dry behind painting, and the wet painting as its own behind painting.
# Run: bash tools/render_stage_midmove.sh
HERE="$(cd "$(dirname "$0")/.." && pwd)"
R="$HERE/stage/kit_copy/paper-film/tools/render-paper-film.mjs"
OUT="$HERE/stage/stills"
WET="painting=lockout-wet-painted.jpg"
for v in "dry_midmove|x=1" "wet_midmove|$WET" "wetwet_midmove|$WET&behind=lockout-wet-painted.jpg"; do
  name="${v%%|*}"; q="${v#*|}"
  echo "=== $name  $(date +%T)"
  PAPER_FILM_QUERY="$q" node "$R" lockout-test "$OUT/$name" --stills 6.0 2>&1 | grep "still-"
done
echo "ALL DONE $(date +%T)"
