#!/bin/bash
# What this file does (plain words): draws the eight comparison stills of the proof that the other scenes are unchanged, with the OLD stage (kit_before:
# the film as it was before this job) into stills/old/ and with the NEW stage (the film project's real files; for the dry lockout, kit_check with the old-look
# scene copy and the dry alternates) into stills/new/. Then draws the wet lockout and the dry street under the new look.
W="$(cd "$(dirname "$0")/.." && pwd)"
D="$W/tools/draw_still.sh"
REAL=/home/user/Music/austerity-explainer/film-kit
OLD="$W/kit_before"; CHK="$W/kit_check"
DRYQ="painting=lockout-painted-dry.jpg&behind=lockout-behind-dry.jpg"
# --- old stage (the film as it was)
for v in projector moved move; do bash $D $OLD $W/stills/old dry_$v "view=$v" 6.0 lockout-test; done
bash $D $OLD $W/stills/old notice_end   "view=end" 6.0 notice-corner
bash $D $OLD $W/stills/old notice_move  "x=1" 4.5 notice-corner
bash $D $OLD $W/stills/old chapter2_a   "x=1" 30.0 inflation-chapter-2-newcomers
bash $D $OLD $W/stills/old chapter2_b   "x=1" 75.0 inflation-chapter-2-newcomers
bash $D $OLD $W/stills/old chapter1_a   "x=1" 40.0 austerity-chapter-1
# --- new stage (the film project's real files)
for v in projector moved move; do bash $D $CHK $W/stills/new dry_$v "view=$v&$DRYQ" 6.0 lockout-oldlook-hook; done
bash $D $REAL $W/stills/new notice_end   "view=end" 6.0 notice-corner
bash $D $REAL $W/stills/new notice_move  "x=1" 4.5 notice-corner
bash $D $REAL $W/stills/new chapter2_a   "x=1" 30.0 inflation-chapter-2-newcomers
bash $D $REAL $W/stills/new chapter2_b   "x=1" 75.0 inflation-chapter-2-newcomers
bash $D $REAL $W/stills/new chapter1_a   "x=1" 40.0 austerity-chapter-1
# --- the wet lockout in the film as it is now (real files), and the dry street under the new look
for v in projector moved move weights; do bash $D $REAL $W/stills/wet wet_$v "view=$v" 6.0 lockout-test; done
for v in projector moved move; do bash $D $CHK $W/stills/drynewlook drynew_$v "view=$v&$DRYQ" 6.0 lockout-newlook-hook; done
echo "ALL DONE $(date +%T)"
