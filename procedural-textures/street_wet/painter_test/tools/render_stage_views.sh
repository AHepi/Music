#!/bin/bash
# What this file does (plain words): draws still pictures from the COPY of the film's lockout stage (stage/kit_copy), through the film's own renderer, in a hidden
# Chromium with software graphics, one process at a time. Each variant is one folder in stage/stills/. All stills are taken at 6.0 s of the lockout clip, where no title
# or LOCKED OUT words are on the screen (the live fire, flames and smoke are drawn on top in every variant the same way).
#   projector = the plate's own camera (the first frame of the film); moved = the end of the film's street move (1.4 m forward, 0.3 m right, 0.05 up, turned 5 degrees, lens 26)
#   weights   = the moved view coloured by what each surface wears: orange the painting, green the behind painting, blue its own 3D surface
# Variants: dry = the film's own dry painting and dry behind painting; wet = the new wet painting with the film's dry behind painting (what swapping only the main painting does);
#           wetwet = the new wet painting also used as its own behind painting (shows the wet look alone, with the near props' painted outlines left on the road when uncovered).
# Run: bash tools/render_stage_views.sh   (about 1 to 3 minutes a picture on this machine)
HERE="$(cd "$(dirname "$0")/.." && pwd)"
R="$HERE/stage/kit_copy/paper-film/tools/render-paper-film.mjs"
OUT="$HERE/stage/stills"
mkdir -p "$OUT"
run() {   # name, query
  echo "=== $1  ($2)  $(date +%T)"
  PAPER_FILM_QUERY="$2" node "$R" lockout-test "$OUT/$1" --stills 6.0 2>&1 | tail -4
}
WET="painting=lockout-wet-painted.jpg"
run dry_projector   "view=projector"
run wet_projector   "view=projector&$WET"
run dry_moved       "view=moved"
run wet_moved       "view=moved&$WET"
run wetwet_moved    "view=moved&$WET&behind=lockout-wet-painted.jpg"
run wet_weights     "view=weights&$WET"
echo "ALL DONE $(date +%T)"
