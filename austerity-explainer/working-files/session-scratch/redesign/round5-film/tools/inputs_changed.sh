#!/bin/bash
# What this does: checks whether any file the filming reads (the Works export, plates and state pictures, the pages,
# the stage, the timeline, the notice corner's files) has changed since filming began, by taking the same
# fingerprints again and listing every file that differs from inputs/hashes-before.txt.
# Use: bash inputs_changed.sh SCRATCH_FOLDER
cd /home/user/Music/austerity-explainer/film-kit
here="$1/inputs"
{ find assets/models/inflation-chapter-2-newcomers paper-film/scenes paper-film/stage assets/models/pit-village -type f \( -name '*.glb' -o -name '*.json' -o -name '*.jpg' -o -name '*.png' -o -name '*.js' -o -name '*.html' -o -name '*.webp' -o -name '*.mjs' \) -print0 | sort -z | xargs -0 md5sum
  md5sum examples/inflation-chapter-2-newcomers/timeline-estimated.json; } > "$here/hashes-now.txt"
diff "$here/hashes-before.txt" "$here/hashes-now.txt" && echo "no input changed since filming began"
