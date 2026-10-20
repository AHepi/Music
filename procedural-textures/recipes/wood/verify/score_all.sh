#!/bin/bash
P=proc-work
V=$P/recipes/wood/verify
cd $P
for d in $V/ladder_*; do
  python3 -I lib/pixel_compare.py wood $d --json $d/pixel.json --sheet $d/pixel_sheet.png > $d/pixel.log 2>&1
  python3 -I lib/texture_compare.py wood $d --json $d/texture.json --sheet $d/texture_sheet.png > $d/texture.log 2>&1
done
echo done > $V/score_done.txt
