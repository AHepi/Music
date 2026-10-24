#!/bin/bash
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/slate
for i in 101 102 103 104 105 106 107 108; do $S/verify/score_one.sh var_$i $S/variations/var_$i; done
