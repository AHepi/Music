#!/bin/bash
# What this does (plain words): runs the whole ANALYSIS chain of the mud recipe on the golden-puddle mud picture (colour only), with the same scripts as for the mud:
# palette and things (extract_elements.py, threshold 3 instead of 7), traced ground (trace_ground.py), rut curves (find_ruts.py), ground model (fit_ground_model.py), sampler numbers
# (fit_sampler_stats.py). Use: bash run_golden_analysis.sh   (about 6 minutes)
cd "$(dirname "$0")"
python3 -I trace_ground.py mud_golden 2000 5000 > golden_trace.log 2>&1
python3 -I find_ruts.py mud_golden 10 > golden_ruts.log 2>&1
python3 -I fit_ground_model.py mud_golden ruts_s10_mud_golden.pkl 150 0.6 > golden_ground_model.log 2>&1
python3 -I fit_sampler_stats.py mud_golden > golden_stats.log 2>&1
echo GOLDEN_ANALYSIS_DONE
