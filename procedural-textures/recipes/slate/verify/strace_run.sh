#!/bin/bash
# verifier: run one small bake of the description under strace and list every file under the proc-work tree that was opened (not just a code read)
export PYTHONDONTWRITEBYTECODE=1
S=proc-work/recipes/slate
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
n=$1
strace -f -e trace=openat,open,stat,newfstatat,access -o $S/verify/strace_$(basename $n).txt $B -b --disable-autoexec -t 2 --python $S/generator/slate_generator.py -- $S/$n.json $S/verify/strace_out_$(basename $n) --size 256 > /dev/null 2>&1
echo finished $n
