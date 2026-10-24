#!/bin/bash
C=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/wet_lockout_film/check
for k in kit_old kit_new; do
  bash $C/draw2.sh $k notice notice-corner 2.0 "x=1"
  bash $C/draw2.sh $k chap2 inflation-chapter-2-newcomers 15.0 "x=1"
done
for k in kit_old kit_new kit_ctrl kit_old; do
  n=house; [ $k = kit_old ] && [ -d $C/stills/kit_old/house ] && n=house_again
  bash $C/draw2.sh $k $n house-sample 20.0 ""
done
echo ALLDONE
