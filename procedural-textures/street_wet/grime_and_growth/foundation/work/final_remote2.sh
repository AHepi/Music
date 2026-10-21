#!/bin/bash
KIT=proc-work/kits/weathering
F=proc-work/street_wet/grime_and_growth/foundation
W=$F/work
cd $W
python3 -I t_bus_remote.py street ground,walls,dots,nodes > $W/fr2_bus_street.log 2>&1
python3 -I t_bus_remote.py lockout ground,walls > $W/fr2_bus_lockout.log 2>&1
python3 -I t_bus_remote.py courtyard ground,walls > $W/fr2_bus_courtyard.log 2>&1
cd $KIT
rm -rf $W/maskviews
python3 -I harness/run_testset.py pit_village_street today $W/maskviews --parts none --maskviews --tag mv > $W/fr2_maskviews.log 2>&1
echo REMOTE2_DONE > $W/remote2_done.txt
