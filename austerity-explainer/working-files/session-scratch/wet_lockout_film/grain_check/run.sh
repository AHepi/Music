#!/bin/bash
W=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/wet_lockout_film; G=$W/grain_check; D=$W/tools/draw_still.sh; REAL=/home/user/Music/austerity-explainer/film-kit
bash $D $W/kit_before $G/out old "x=1" 20.0 house-sample
bash $D $REAL $G/out new "x=1" 20.0 house-sample
bash $D $G/kit_old_space $G/out oldspace "x=1" 20.0 house-sample
bash $D $G/kit_old_nograin $G/out oldnograin "x=1" 20.0 house-sample
bash $D $G/kit_new_nograin $G/out newnograin "x=1" 20.0 house-sample
bash $D $W/kit_before $G/out old2 "x=1" 20.0 house-sample
echo ALL DONE
