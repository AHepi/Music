#!/bin/bash
# draws one still with a given kit copy: draw2.sh KIT NAME SCENE SECOND QUERY
C=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/wet_lockout_film/check
KIT=$1; NAME=$2; SCENE=$3; SEC=$4; Q=$5
mkdir -p $C/stills/$KIT/$NAME
( cd $C/$KIT/paper-film && PAPER_FILM_QUERY="$Q" timeout 1500 node tools/render-paper-film.mjs $SCENE $C/stills/$KIT/$NAME --stills $SEC 2>&1 | grep -E "still-|rror" | tail -2 )
