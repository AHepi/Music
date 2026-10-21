#!/bin/bash
cd proc-work/street_wet/grime_and_growth/ground
until grep -q "CHAIN6 DONE" proc-work/street_wet/grime_and_growth/ground/chain6.log; do sleep 5; done
python3 -I proc-work/street_wet/grime_and_growth/ground/st.py japanese_courtyard courtyard
echo CHAIN7 DONE
