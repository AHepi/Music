#!/bin/bash
# What this does (plain words): last batch: the resolution table with the final sampled description (variation tile 11) and the half-tile seamless test for the S class.
B=proc-work
R=$B/recipes/brick
cd $R
until [ -f extras3_done.flag ]; do sleep 5; done
rm -rf resolution/size_*
python3 -I generator/resolution_test.py variations/description_11.json resolution > resolution/run.log 2>&1
python3 -I generator/seam_test.py generator/descriptions/description_S.json scores/seam_S > scores/seam_S.log 2>&1
rm -rf scores/seam_*/plain scores/seam_*/shifted
echo extras4_done > extras4_done.flag
