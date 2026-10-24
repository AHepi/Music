### 7.9 Time

Building the node tree takes about half a second. At 1254 dots one map of the full recipe took about 60 to 70 seconds on 2 threads when the machine was less busy (colour 69 s, height 65 s, roughness 56 s in the OLD default bake); the layout with empty layers took 13 to 16 seconds per map (`tests/timing.json`). The four layers
cost about 50 seconds per map together. **After the look fixes, with another job always running beside, load average 7 to 10:** the new default (all five maps and the extra bump-node normal) took 587 s; the four ladder rungs (colour and height each) about 8 minutes in one run; one 1254-dot colour tile 100 to 170 s;
the 2 x 2 area (2508 dots, colour and height) 1344 s (old default: 522 s at a load of about 4); a 512-dot bake of all maps 112 s (old: 35 s). The new layers did not make the recipe slower in any way I could tell apart from the load. The 4 x 4 area (5016 dots, colour only) took 1595 s for the old default and was not baked again.
Nothing here was timed on a quiet machine.

