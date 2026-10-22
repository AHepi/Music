#!/bin/bash
# copy the master scripts into ship/ (the folder that goes to RunPod)
D=proc-work/garden/life
cp $D/stage_life.py $D/astra_loader.py $D/ship/
find $D/ship -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
du -sh $D/ship
