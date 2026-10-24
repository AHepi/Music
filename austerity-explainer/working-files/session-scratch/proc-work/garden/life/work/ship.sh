#!/bin/bash
# copy the master scripts into ship/ (the folder that goes to RunPod)
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/life
cp $D/stage_life.py $D/astra_loader.py $D/ship/
find $D/ship -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
du -sh $D/ship
