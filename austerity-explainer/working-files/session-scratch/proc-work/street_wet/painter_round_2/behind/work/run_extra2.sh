HERE=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/behind
R="$HERE/stage/kit_copy/paper-film/tools/render-paper-film.mjs"
for v in "r2_notice_drybehind|view=notice&painting=lockout-r2-front.jpg" "r2_notice_wetbehind|view=notice&painting=lockout-r2-front.jpg&behind=lockout-r2-behind.jpg"; do
  n="${v%%|*}"; q="${v#*|}"
  echo "=== $n $(date +%T)"
  PAPER_FILM_QUERY="$q" node "$R" lockout-test "$HERE/stage/stills/$n" --stills 6.0 2>&1 | grep "still-"
done
echo "ALL DONE 2"
