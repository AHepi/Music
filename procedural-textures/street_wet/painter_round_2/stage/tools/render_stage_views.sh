#!/bin/bash
# What this file does (plain words): draws the standard set of still pictures of the film's lockout scene from the COPY of the film's stage (kit_copy), into stills/FOLDER/ (FOLDER = "before" or "after" the brightness fix),
# each at 6.0 s of the lockout clip (no title on screen; the live fire, flames and smoke are drawn on top in every picture alike). Two pictures are drawn at a time to use the machine well.
#   projector = the plate's own camera (the first frame of the film)   moved = the end of the film's street move (1.4 m forward, 0.3 m right, 0.05 up, turned 5 degrees, lens 26)
#   move      = the street move itself at 6.0 s (about three quarters of the way)   weights = the moved view coloured by what each surface wears (orange the painting, green the behind painting, blue its own surface)
#   wet_*     = the new wet FRONT painting (lockout-r2-front.jpg) with the new wet BEHIND painting (lockout-r2-behind.jpg)
#   wetolddry_moved = the new wet front painting with the film's old DRY behind painting (what swapping only the front painting would give; the first test's problem picture)
#   wetown_moved    = the new wet front painting used as its own behind painting (the reference for the "dry-looking patches" number of the first test)
#   dry_*     = the film's own dry painting and dry behind painting (the film's lockout as it is today)
# Run: bash tools/render_stage_views.sh FOLDER [EXTRA_QUERY]     (EXTRA_QUERY, e.g. "lk_filmic=0", is added to every picture's address)
HERE="$(cd "$(dirname "$0")/.." && pwd)"
D="$HERE/tools/draw.sh"
F="${1:?folder name: before or after}"; X="${2:+&$2}"
FRONT="painting=lockout-r2-front.jpg"; BEHIND="behind=lockout-r2-behind.jpg"
(
 bash "$D" $F wet_projector   "view=projector&$FRONT&$BEHIND$X"
 bash "$D" $F wet_moved       "view=moved&$FRONT&$BEHIND$X"
 bash "$D" $F wet_move        "view=move&$FRONT&$BEHIND$X"
 bash "$D" $F wetolddry_moved "view=moved&$FRONT$X"
 bash "$D" $F wetown_moved    "view=moved&$FRONT&behind=lockout-r2-front.jpg$X"
) &
(
 bash "$D" $F wet_weights     "view=weights&$FRONT&$BEHIND$X"
 bash "$D" $F dry_projector   "view=projector$X"
 bash "$D" $F dry_moved       "view=moved$X"
 bash "$D" $F dry_move        "view=move$X"
) &
wait
echo "ALL DONE $(date +%T)"
