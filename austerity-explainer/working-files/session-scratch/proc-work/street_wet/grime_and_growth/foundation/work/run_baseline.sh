#!/bin/sh
# Draws the baseline look three times (three separate Blender runs per scene file) on the rented machine through harness/run_testset.py.
KIT=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering
W=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/foundation/work/baseline
cd $KIT
for tag in r1 r2 r3; do
  python3 -I harness/run_testset.py pit_village_street base $W --today --tag $tag > $W/$tag.log 2>&1
done
echo ALL_DONE > $W/done.txt
