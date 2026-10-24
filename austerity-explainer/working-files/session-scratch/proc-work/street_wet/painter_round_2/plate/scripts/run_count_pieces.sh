#!/bin/bash
# What this does (plain words): runs count_pieces_by_zone.py on the rented machine (street copy open) and brings the JSON back. Use: bash run_count_pieces.sh
T=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/plate
C=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client_cached.py
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet
mkdir -p $T/rubbish/work/zones
python3 -I $C upload $T/scripts > /dev/null 2>&1
python3 -I $C upload $T/rubbish/tools > /dev/null 2>&1
J=$(python3 -I $C run "mkdir -p $T/rubbish/work/zones && /workspace/blender/blender -b --disable-autoexec $S/set_copy/street.blend --python $T/scripts/count_pieces_by_zone.py -- $T/rubbish/work/zones/zones.json" --cwd $S | tail -1)
python3 -I $C wait $J --limit 300 | tail -4
python3 -I $C download $T/rubbish/work/zones/zones.json --local $T/rubbish/work/zones/zones.json | tail -1
