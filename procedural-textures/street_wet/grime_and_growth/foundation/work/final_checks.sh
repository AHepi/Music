#!/bin/bash
# Final foundation run: rebuild the three packs, then the self-tests and bus tests on the rented machine (all scenes), then the mask-view pictures.
KIT=proc-work/kits/weathering
F=proc-work/street_wet/grime_and_growth/foundation
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
STREET=proc-work/street_wet/set_copy/street.blend
LOCK=/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend
COURT=scratchpad/astra-work/out/courtyard_final.blend
cd $KIT
W=$F/work
( time $B -b --disable-autoexec $STREET --python masks/reader.py -- pit_village_street street $KIT/masks/packs/pit_village_street/street $F/raw_street ) > $W/reader_street_3.log 2>&1
python3 -I masks/make_pack.py pit_village_street street $F/raw_street --rubbish $F/raw_street/rubbish_heap.png >> $W/reader_street_3.log 2>&1
( time $B -b --disable-autoexec $LOCK --python masks/reader.py -- pit_village_street lockout $KIT/masks/packs/pit_village_street/lockout $F/raw_lockout ) > $W/reader_lockout_3.log 2>&1
python3 -I masks/make_pack.py pit_village_street lockout $F/raw_lockout --rubbish $F/raw_lockout/rubbish_heap.png >> $W/reader_lockout_3.log 2>&1
( time $B -b --disable-autoexec $COURT --python masks/reader.py -- japanese_courtyard courtyard $KIT/masks/packs/japanese_courtyard/courtyard $F/raw_courtyard ) > $W/reader_courtyard_3.log 2>&1
echo READERS_DONE > $W/readers_done.txt
