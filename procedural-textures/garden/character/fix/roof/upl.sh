#!/bin/bash
# uploads the fixed roof stage, its modules, the small maps, the harness and the job files to the store (same absolute paths)
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/roof
cd $D
FILES="${@:-stage_roof.py r_common.py r_maps.py r_tiles.py r_marks.py r_ridge.py r_walls.py r_stones.py r_lantern.py r_moss.py normal_tools.py render_fix.py build_fix.py maps/sw_plaster.jpg}"
for f in $FILES; do python3 -I $R/render_client_serverless.py upload $D/$f --remote $D/$f | tail -1; done
