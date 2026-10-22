#!/bin/bash
# uploads every script, the changed maps and job files of this folder to the store
export PYTHONDONTWRITEBYTECODE=1
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/ground
cd $D
for f in *.py *.sh tools/*.py maps/path_mask.png jobs/*.json "$@"; do
  [ -f "$f" ] && python3 -I $R/render_client_serverless.py upload $D/$f --remote $D/$f >/dev/null 2>&1 || echo "skip $f"
done
echo uploaded
