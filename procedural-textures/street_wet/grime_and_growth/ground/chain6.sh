#!/bin/bash
cd proc-work/street_wet/grime_and_growth/ground
until grep -q "CHAIN5 DONE" proc-work/street_wet/grime_and_growth/ground/chain5.log; do sleep 5; done
python3 -I proc-work/street_wet/grime_and_growth/ground/showcase.py plan_r6 show_r6
echo CHAIN6 DONE
