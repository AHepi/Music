#!/bin/bash
cd "$(dirname "$0")/.."
python3 scripts/c1_feature_survival.py > numbers/c1_printout.txt 2>&1
python3 scripts/c1b_regions.py > numbers/c1b_printout.txt 2>&1
python3 scripts/c7_specific_match.py > numbers/c7_printout.txt 2>&1
python3 scripts/b2_band_transfer.py > numbers/b2_band_transfer_printout.txt 2>&1
python3 scripts/d1_tone_map.py > numbers/d1_printout.txt 2>&1
echo ALLDONE > numbers/run_all_done.txt
