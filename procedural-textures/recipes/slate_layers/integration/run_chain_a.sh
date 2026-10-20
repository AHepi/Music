#!/bin/bash
# What this does (plain words): runs the long bakes one after the other (debug views, ladder, resolution), so two helpers' worth of CPU is not used at once.
SL=proc-work/recipes/slate_layers
cd $SL
python3 -I debug_views/make_debug_views.py all > debug_views/make.log 2>&1
python3 -I resolution/run_resolution.py all > resolution/run.log 2>&1
echo done > integration/chain_a.done
