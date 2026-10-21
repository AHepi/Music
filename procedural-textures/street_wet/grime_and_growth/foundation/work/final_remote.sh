#!/bin/bash
# Self-tests, bus tests and the mask-view pictures on the rented machine, one run after the other.
KIT=proc-work/kits/weathering
F=proc-work/street_wet/grime_and_growth/foundation
W=$F/work
cd $W
ALL=hook,remove,nothing,legacy_nothing,dial_zero,isolation,determinism,reuse,lighting
python3 -I t_selftests_street.py street 135x240 $ALL > $W/fr_self_street_135.log 2>&1
python3 -I t_selftests_street.py street 540x960 nothing,legacy_nothing,dial_zero,isolation,determinism > $W/fr_self_street_540.log 2>&1
python3 -I t_selftests_street.py lockout 135x240 $ALL > $W/fr_self_lockout_135.log 2>&1
python3 -I t_selftests_street.py lockout 540x960 nothing,legacy_nothing,dial_zero,isolation,determinism > $W/fr_self_lockout_540.log 2>&1
python3 -I t_selftests_street.py courtyard 1200x800 hook,remove,nothing,dial_zero,isolation,determinism,reuse > $W/fr_self_courtyard.log 2>&1
python3 -I t_bus_remote.py street ground,walls,dots,nodes > $W/fr_bus_street.log 2>&1
python3 -I t_bus_remote.py lockout ground,walls > $W/fr_bus_lockout.log 2>&1
python3 -I t_bus_remote.py courtyard ground > $W/fr_bus_courtyard.log 2>&1
cd $KIT
python3 -I harness/run_testset.py pit_village_street today $W/maskviews --parts none --maskviews --tag mv > $W/fr_maskviews.log 2>&1
echo REMOTE_DONE > $W/remote_done.txt
