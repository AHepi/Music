#!/bin/bash
# What this file does (plain words): draws still pictures from the COPY of the film's lockout stage (stage/kit_copy), through the film's own renderer, in a hidden Chromium with software graphics, one at a time,
# each at 6.0 s of the lockout clip (no titles on screen; the live fire, flames and smoke are drawn on top in every picture alike). Each variant is one folder in stage/stills/.
#   FRONT = the new front painting (lockout-r2-front.jpg); behind = the film's own DRY behind painting (the film's default), the new wet behind painting before the free colour match, or after it.
#   projector = the plate's own camera (the first frame of the film); moved = the end of the film's street move (1.4 m forward, 0.3 m right, 0.05 up, turned 5 degrees, lens 26);
#   move = the street move itself at 6.0 s (about three quarters of the way); weights = the moved view coloured by what each surface wears (orange the painting, green the behind painting, blue its own surface)
# Run: bash tools/render_stage_views.sh
HERE="$(cd "$(dirname "$0")/.." && pwd)"
R="$HERE/stage/kit_copy/paper-film/tools/render-paper-film.mjs"
OUT="$HERE/stage/stills"
mkdir -p "$OUT"
run() {   # name, query
  echo "=== $1  ($2)  $(date +%T)"
  PAPER_FILM_QUERY="$2" node "$R" lockout-test "$OUT/$1" --stills 6.0 2>&1 | grep "still-"
}
FRONT="painting=lockout-r2-front.jpg"
NEWB="behind=lockout-r2-behind.jpg"
NOTM="behind=lockout-r2-behind-notmatched.jpg"
run r2_projector_wetbehind   "view=projector&$FRONT&$NEWB"
run r2_moved_drybehind       "view=moved&$FRONT"
run r2_moved_wetbehind_notmatched "view=moved&$FRONT&$NOTM"
run r2_moved_wetbehind       "view=moved&$FRONT&$NEWB"
run r2_move_drybehind        "view=move&$FRONT"
run r2_move_wetbehind        "view=move&$FRONT&$NEWB"
run r2_weights               "view=weights&$FRONT&$NEWB"
echo "ALL DONE $(date +%T)"
# added afterwards: the new front painting used as its own behind painting (what the ground would look like if the behind painting matched the front one exactly; the near props' painted outlines stay on the road there),
# the reference for the "dry-looking patches" number of the first painter test
run r2_moved_ownbehind       "view=moved&$FRONT&behind=lockout-r2-front.jpg"
# added afterwards: the film's second shot, close and square to the notice (view=notice, the end of the close shot), with the old dry and the new wet behind painting
run r2_notice_drybehind      "view=notice&$FRONT"
run r2_notice_wetbehind      "view=notice&$FRONT&$NEWB"
