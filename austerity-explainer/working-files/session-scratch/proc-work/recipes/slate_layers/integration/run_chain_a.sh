#!/bin/bash
# What this does (plain words): runs the long bakes one after the other (debug views, ladder, resolution), so two helpers' worth of CPU is not used at once.
SL=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/slate_layers
cd $SL
python3 -I debug_views/make_debug_views.py all > debug_views/make.log 2>&1
python3 -I resolution/run_resolution.py all > resolution/run.log 2>&1
echo done > integration/chain_a.done
