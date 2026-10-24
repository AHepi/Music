#!/bin/bash
# What this file does (plain words): makes a working COPY of the film kit's stage, scenes and tools in a folder of its own, so a clip or
# a still can be drawn from the film as it was BEFORE the wet street went in (or as it is after), without the film project being touched
# by the drawing. Big read-only things (the 3D models, node_modules, pieces, other assets) are links to the film project's own files;
# the small code files (stage, scenes, tools, the lockout timing) are real copies, so they can be compared file by file with the film's.
# The two lockout painting files are always REAL copies (not links), so the copy keeps what they were when it was made even after the
# film project renames them.
# Run: bash make_kit_copy.sh DESTINATION_FOLDER     (the code files and the lockout paintings are taken from the film project's files as they are now)
set -e
DEST="$1"
FILM=/home/user/Music/austerity-explainer/film-kit
rm -rf "$DEST"; mkdir -p "$DEST/paper-film/out" "$DEST/examples/lockout-test" "$DEST/assets/models/pit-village"
for t in stage scenes tools; do mkdir -p "$DEST/paper-film/$t"; cp -r "$FILM/paper-film/$t/." "$DEST/paper-film/$t/"; done
ln -s "$FILM/paper-film/node_modules" "$DEST/paper-film/node_modules"
ln -s "$FILM/paper-film/pieces" "$DEST/paper-film/pieces"
ln -s "$FILM/paper-film/package.json" "$DEST/paper-film/package.json"
cp "$FILM/examples/lockout-test/timeline.json" "$DEST/examples/lockout-test/"
for d in "$FILM"/examples/*; do n=$(basename "$d"); if [ "$n" != lockout-test ]; then ln -s "$d" "$DEST/examples/$n"; fi; done
for d in "$FILM"/assets/*; do n=$(basename "$d"); if [ "$n" != models ]; then ln -s "$d" "$DEST/assets/$n"; fi; done
for d in "$FILM"/assets/models/*; do n=$(basename "$d"); if [ "$n" != pit-village ]; then ln -s "$d" "$DEST/assets/models/$n"; fi; done
for f in "$FILM"/assets/models/pit-village/*; do
  n=$(basename "$f")
  case "$n" in
    lockout-painted*.jpg|lockout-behind*.jpg) cp "$f" "$DEST/assets/models/pit-village/$n";;   # real copies, so they stay as they were when the copy was made
    *) ln -s "$f" "$DEST/assets/models/pit-village/$n";;
  esac
done
du -sh "$DEST"
