#!/bin/bash
# What this does (plain words): bakes some description files with Blender at 1254 dots and scores each. Use: bake_score_rows.sh DESCRIPTION_FOLDER OUTPUT_FOLDER SCORE_SCRIPT name1 name2 ...
# (SCORE_SCRIPT is analysis/score_folder.py for the mud or analysis/score_golden.py for the golden mud.)
cd "$(dirname "$0")/.."
desc="$1"; out="$2"; scorer="$3"; shift 3
mkdir -p "$out"
for name in "$@"; do
  generator/bake_one.sh $desc/$name.json $out/$name 1254 8 > scores/bake_$name.log 2>&1
  python3 -I $scorer $out/$name > scores/$name.line 2>&1
  cp $out/$name/score.json scores/$(basename $out)_$name.json
  echo "$name $(cat scores/$name.line)"
done
