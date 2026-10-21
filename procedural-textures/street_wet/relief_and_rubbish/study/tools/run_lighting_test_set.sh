#!/bin/bash
# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# THE ONE COMMAND for the lighting test set. It draws every picture of the set (the street file, then the film's lockout shot file opened read-only), measures how visible the joints between the
# setts are in each picture, and prints PASS / FAIL for each (the pass line is in b09_lighting_test_set.py). One Blender run at a time; pictures already drawn are skipped, so it can be run again.
# Use:   bash run_lighting_test_set.sh SET OUT_FOLDER [--variant NAME] [--args JSON] [--after-apply FILE.py]
#   SET            quick (9 hard pictures: about 20 minutes) or full (22 pictures: about 40 minutes)
#   OUT_FOLDER     where the pictures (JPEG), the masks and measurements.json go (it is made if missing); about 5 MB for the full set
#   --variant      a named change of the road material from b02_lighting_and_variants.py (default baseline = the road as it is today); --args gives its settings as JSON
#   --after-apply  OR a Python file of your own that is run once inside Blender after the wetness layer is on (it can change the road's material: this is how to test a new solution)
# Example (the study's recommended first setting):
#   bash run_lighting_test_set.sh quick work/r11 --variant joint_picture --args '{"colour_mult":0.85,"rough_to":0.9,"spec_keep":0.65,"coat_keep":0.55,"picture":"joint_cavity_closed.png"}'
# It never saves a Blender file and never changes the film project. It stops if the free disk space falls below 1.25 GB.
HERE="$(cd "$(dirname "$0")" && pwd)"
S="$(cd "$HERE/../../.." && pwd)"                    # street_wet
BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
LOCKOUT=/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend
SET="$1"; OUT="$2"; shift 2
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"
python3 -I "$HERE/b09_lighting_test_set.py" jobs "$SET" "$OUT" "$@" || exit 1
free_mb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
cd "$S"
for kind in street lockout; do
  [ -f "$OUT/jobs_$kind.json" ] || continue
  if [ "$(free_mb)" -lt 1250 ]; then echo "STOP: free disk space is below 1.25 GB"; exit 1; fi
  if [ $kind = street ]; then FILE=set_copy/street.blend; else FILE=$LOCKOUT; fi
  xvfb-run -a $BLENDER -b --disable-autoexec -t 2 "$FILE" --python "$HERE/b03_render_jobs.py" -- "$OUT/jobs_$kind.json" "$OUT" > "$OUT/log_$kind.txt" 2>&1
  python3 -I "$HERE/b05_measure_folder.py" "$OUT" "$OUT/jobs_$kind.json" --convert > "$OUT/measure_$kind.txt" 2>&1
done
python3 -I "$HERE/b09_lighting_test_set.py" report "$SET" "$OUT" | tee "$OUT/report.txt"
