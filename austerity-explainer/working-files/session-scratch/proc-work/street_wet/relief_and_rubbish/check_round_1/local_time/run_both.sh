#!/bin/bash
# What this does: runs the two local timing jobs one after the other (never two Blender processes at once) and writes the answers to local_time/result_*.txt
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/relief_and_rubbish/check_round_1/local_time
for look in joints rubbish; do
  python3 -I $D/run_one_local.py $D/$look/jobs_lockout.json $D/$look > $D/result_$look.txt 2>&1
done
echo done > $D/all_done.txt
