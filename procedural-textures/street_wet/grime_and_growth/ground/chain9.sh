#!/bin/bash
cd proc-work/street_wet/grime_and_growth/ground
until grep -q "CHAIN8 DONE" proc-work/street_wet/grime_and_growth/ground/chain8.log; do sleep 4; done
python3 -I proc-work/kits/weathering/ground/run_round.py pit_village_street kit:dirt,groundcracks,groundmoss,iron proc-work/street_wet/grime_and_growth/ground/rounds r7 --layers dirt,groundcracks,groundmoss,iron
echo ROUND7 DONE
python3 -I proc-work/kits/weathering/ground/measure_ground.py pit_village_street proc-work/street_wet/grime_and_growth/ground/rounds/r7 --out proc-work/street_wet/grime_and_growth/ground/measures_r7.json
echo CHAIN9 DONE
