# usage: shots.sh PREFIX OUTDIR
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/desk-9883
mkdir -p $2
i=0
for pos in "0 -3.4 4.9 0 0.15 0 32" "-0.6 -2.0 0.6 -0.75 -1.15 0.02 30" "1.0 -1.95 0.65 0.85 -1.12 0.06 30" "-0.5 0.5 0.95 -0.9 1.45 0.35 28" "0.9 0.6 1.1 0.95 1.55 0.1 28"; do
  i=$((i+1)); echo "$pos" > $D/campos.txt
  $D/c.sh run-file $D/cam.py >/dev/null 2>&1
  out=$($D/c.sh render_thumbnail_to_path "{\"output_path\": \"$1-$i.png\"}" 2>/dev/null | grep -o '/[^"]*\.png' | head -1)
  echo "$out"; cp "$out" $2/
done
