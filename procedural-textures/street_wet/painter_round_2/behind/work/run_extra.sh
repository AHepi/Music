HERE=proc-work/street_wet/painter_round_2/behind
R="$HERE/stage/kit_copy/paper-film/tools/render-paper-film.mjs"
echo "=== r2_moved_ownbehind $(date +%T)"
PAPER_FILM_QUERY="view=moved&painting=lockout-r2-front.jpg&behind=lockout-r2-front.jpg" node "$R" lockout-test "$HERE/stage/stills/r2_moved_ownbehind" --stills 6.0 2>&1 | grep "still-"
echo "ALL DONE"
