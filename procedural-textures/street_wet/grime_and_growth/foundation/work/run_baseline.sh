#!/bin/sh
# Draws the baseline look three times (three separate Blender runs per scene file) on the rented machine through harness/run_testset.py.
KIT=proc-work/kits/weathering
W=proc-work/street_wet/grime_and_growth/foundation/work/baseline
cd $KIT
for tag in r1 r2 r3; do
  python3 -I harness/run_testset.py pit_village_street base $W --today --tag $tag > $W/$tag.log 2>&1
done
echo ALL_DONE > $W/done.txt
