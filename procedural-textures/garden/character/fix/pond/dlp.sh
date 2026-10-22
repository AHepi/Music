#!/bin/bash
# usage: dlp.sh PREVIEWDIR name1.jpg name2.jpg ...  (downloads from the store into the same local folder)
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/pond/previews/$1
shift
mkdir -p $D
for f in "$@"; do ./dl.sh $D/$f $D/$f >/dev/null; done
ls -la $D | tail -n +2
