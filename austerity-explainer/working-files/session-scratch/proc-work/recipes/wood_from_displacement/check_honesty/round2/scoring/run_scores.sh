#!/bin/sh
# What this does (plain words): the honesty checker's re-score of the default tiles with the project's own tool lib/texture_compare.py (called directly, not through the builder's scripts).
cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work || exit 1
R=recipes/wood_from_displacement
C=$PWD/$R/check_honesty/round2/scoring
for s in 1 2 3; do
  nice -n 10 python3 -I lib/texture_compare.py wood $PWD/$R/outputs/main_seed$s --json $C/score_main_seed$s.json > $C/score_main_seed$s.out 2>&1
  nice -n 10 python3 -I lib/texture_compare.py wood $C/links/comparison_seed$s --json $C/score_comparison_seed$s.json > $C/score_comparison_seed$s.out 2>&1
done
nice -n 10 python3 -I lib/texture_compare.py wood $PWD/$R/tests/earlier_wood_seed105 --json $C/score_earlier_seed105.json > $C/score_earlier_seed105.out 2>&1
echo done > $C/scores.done
