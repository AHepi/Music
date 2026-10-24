#!/bin/bash
# usage: pg.sh pattern [maxlines]
cd /home/user/Music/plugins/explainer-film
rg -n -i --no-heading -g '!*.pyc' -g '!*.glb' -g '!*.gz' -g '!*.whl' -g '!kit/calculators/tests/fixtures/**' -g '!kit/examples/austerity-chapter-1/transcripts/**' -g '!kit/examples/*/transcripts/**' -g '!kit/place-kit/data/surfaces.json' -g '!kit/place-kit/data/roles.json' -e "$1" . 2>/dev/null | cut -c1-260 | head -${2:-12}
