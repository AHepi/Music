#!/bin/bash
SL=proc-work/recipes/slate_layers
cd $SL
ONLY=v3_heavily_damaged python3 -I variations/make_variations.py bake > variations/bake_v3.log 2>&1
python3 -I variations/make_variations.py score > variations/score.log 2>&1
python3 -I variations/make_variations.py sheet >> variations/score.log 2>&1
python3 -I area/make_area.py all 2 > area/run2.log 2>&1
echo done > integration/chain_b.done
