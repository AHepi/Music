#!/usr/bin/env bash
# What this does: draws the round 6 plates (1536 x 2730, 48 samples) in three Blender runs, so no one run holds the
# Works in memory for long (round 6: a run of six film-size pictures was stopped by the machine's memory limit while
# other helpers' work ran): W3's two, W1's four, W2's two. Each run's log is kept; then the logs are searched for
# shadow faults (scratch, round 6 set).
set -uo pipefail
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round6-set
KIT=/home/user/Music/austerity-explainer/film-kit
W=$KIT/assets/models/inflation-chapter-2-newcomers/works
mkdir -p $S/plates
cd $KIT
for group in "w3 works-w3-plate,works-w3-working-plate" "w1 works-w1-plate,works-w1-working-plate,works-w1-men-gone-plate,works-w1-behind-plate" "w2 works-w2-plate,works-w2-slowed-plate"; do
  set -- $group
  DISPLAY=:96 /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b $W/works-lane.blend --python paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py \
    -- --plates $S/plates --only $2 > $S/plates/plates-$1.log 2>&1
  echo "plates $1: exit $? ; $(grep -c 'Saved:' $S/plates/plates-$1.log) saved; shadow faults: $(grep -c 'Shadow buffer full\|Could not allocate shadow atlas' $S/plates/plates-$1.log)"
done
