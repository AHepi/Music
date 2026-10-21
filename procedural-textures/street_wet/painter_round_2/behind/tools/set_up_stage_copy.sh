#!/bin/bash
# What this file does (plain words): builds stage/kit_copy/, a COPY of the film kit's stage, scenes and renderer (the same way the first painter test did), so the new wet FRONT painting and the new wet BEHIND painting can be dropped into
# the film's real lockout stage the way the film does it, WITHOUT touching the film project. Big files (the 3D sets, node_modules, other assets) are links to the film project's own files and are only read.
# Only the lockout scene file is edited in the copy: the two painting file names can be given in the address (?painting=NAME&behind=NAME), so one copy shows every combination.
# The paintings are saved as real JPEGs of quality 92, like the film's own lockout-painted.jpg and lockout-behind.jpg (1536 x 2730), next to the film's files in the copy:
#   lockout-r2-front.jpg = the new front painting (front_painting_final.png)    lockout-r2-behind.jpg = the new behind painting (behind_painting_final.png)
#   lockout-r2-behind-notmatched.jpg = the behind painting before the free colour match (for the comparison)
# Run: bash tools/set_up_stage_copy.sh
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
FILM=/home/user/Music/austerity-explainer/film-kit
K="$HERE/stage/kit_copy"
rm -rf "$K"; mkdir -p "$K/paper-film/tools" "$K/examples/lockout-test" "$K/assets/models/pit-village"
cp -r "$FILM/paper-film/stage" "$K/paper-film/stage"
cp -r "$FILM/paper-film/scenes" "$K/paper-film/scenes"
cp "$FILM/paper-film/tools/render-paper-film.mjs" "$K/paper-film/tools/"
ln -s "$FILM/paper-film/node_modules" "$K/paper-film/node_modules"
ln -s "$FILM/paper-film/pieces" "$K/paper-film/pieces"
cp "$FILM/examples/lockout-test/timeline.json" "$K/examples/lockout-test/"
for d in "$FILM"/assets/*; do n=$(basename "$d"); if [ "$n" != models ]; then ln -s "$d" "$K/assets/$n"; fi; done
for d in "$FILM"/assets/models/*; do n=$(basename "$d"); if [ "$n" != pit-village ]; then ln -s "$d" "$K/assets/models/$n"; fi; done
for f in "$FILM"/assets/models/pit-village/*; do ln -s "$f" "$K/assets/models/pit-village/$(basename "$f")"; done
python3 -I - <<PY
import cv2
P = "$HERE"
K = "$K/assets/models/pit-village/"
for src, name in ((P + "/../paint/front_painting_final.png", "lockout-r2-front.jpg"), (P + "/../paint/behind_painting_final.png", "lockout-r2-behind.jpg"), (P + "/work/behind_with_free_sky.png", "lockout-r2-behind-notmatched.jpg")):
    img = cv2.imread(src)
    assert img.shape[:2] == (2730, 1536), (src, img.shape)
    cv2.imwrite(K + name, img, [cv2.IMWRITE_JPEG_QUALITY, 92])
PY
python3 -I - <<PY
p = "$K/paper-film/scenes/lockout-test.js"
s = open(p).read()
a = "loadTexture(\`\${SET}/lockout-painted.jpg\`), loadTexture(\`\${SET}/lockout-behind.jpg\`)"
assert s.count(a) == 1
s = s.replace(a, "loadTexture(\`\${SET}/\${new URLSearchParams(location.search).get('painting') ?? 'lockout-painted.jpg'}\`), loadTexture(\`\${SET}/\${new URLSearchParams(location.search).get('behind') ?? 'lockout-behind.jpg'}\`)")
s = "// NOTE (plain words): COPY of the film kit's lockout-test.js, made for the wet behind painting test (round 2). The only change: the painting and the behind picture file names can be given in the address (?painting=NAME&behind=NAME). Everything else is the film's own.\n" + s
open(p, "w").write(s)
PY
du -sh "$K"; ls -la "$K/assets/models/pit-village" | grep r2
