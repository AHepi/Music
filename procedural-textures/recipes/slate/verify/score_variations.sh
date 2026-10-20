#!/bin/bash
S=proc-work/recipes/slate
for i in 101 102 103 104 105 106 107 108; do $S/verify/score_one.sh var_$i $S/variations/var_$i; done
