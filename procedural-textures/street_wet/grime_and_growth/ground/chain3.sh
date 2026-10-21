#!/bin/bash
cd proc-work/street_wet/grime_and_growth/ground
until grep -q "CHAIN2 DONE" proc-work/street_wet/grime_and_growth/ground/chain2.log; do sleep 5; done
python3 -I proc-work/street_wet/grime_and_growth/ground/st.py japanese_courtyard courtyard --upload
python3 -I proc-work/street_wet/grime_and_growth/ground/court.py court_r3
echo CHAIN3 DONE
