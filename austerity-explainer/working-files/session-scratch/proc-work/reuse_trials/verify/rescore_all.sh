#!/bin/bash
# What this does: the independent re-score. For every surface and every final seed set it runs lib/texture_compare.py on the
# trial's stored colour/height/normal, and again on a normal map REMADE here from the stored height with make_normal.py at the
# strength the helper claimed (to prove the helper did not tune the normal map separately). It writes one JSON per run into
# verify/scores/ and then prints one line per run. No Blender is used. Temporary remade pictures go in verify/tmp_normals and are deleted.
cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work || exit 1
ROOT=reuse_trials
V=$ROOT/verify
mkdir -p $V/scores $V/tmp_normals
declare -A STRENGTH=( [brick]=6 [wood]=8 [metal]=5 [mud]=9 [gravel]=10 )
for s in brick wood metal mud gravel; do
  for d in $ROOT/$s/final/seeds_*; do
    name=$(basename $d)
    [ -f $d/colour.png ] || continue
    python3 -I lib/texture_compare.py $s $d --json $V/scores/${s}_${name}_stored.json > /dev/null
    t=$V/tmp_normals/${s}_${name}
    mkdir -p $t
    ln -sf $(pwd)/$d/colour.png $t/colour.png
    ln -sf $(pwd)/$d/height.png $t/height.png
    python3 -I recipes/slate_layers/integration/make_normal.py $d/height.png $t/normal.png ${STRENGTH[$s]}
    python3 -I lib/texture_compare.py $s $t --json $V/scores/${s}_${name}_remadenormal.json > /dev/null
    rm -rf $t
  done
done
rmdir $V/tmp_normals 2>/dev/null
python3 -I - <<'PY'
import json, glob, os
for f in sorted(glob.glob('reuse_trials/verify/scores/*.json')):
    d = json.load(open(f))
    g = d['groups']
    print(f"{os.path.basename(f):50s} overall {d['overall']:.3f} colour {g['colour']:.3f} height {g['height']:.3f} normal {g['normal']:.3f} tiling {g['tiling']:.3f}")
PY
