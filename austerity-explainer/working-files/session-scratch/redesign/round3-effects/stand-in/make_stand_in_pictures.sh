#!/bin/bash
# What this does: turns the stand-in Works plates (assemble_works_stand_in.py) into the pictures pages 3 to 5 read:
# each plate as a JPEG (as the real plates are kept), and page 3's two state pictures made with the kit's
# make_state_picture.py, the plates standing in for the paintings:
#   works-w1-men-gone-state.png  W1's plate with the men (and what they changed) taken from the working plate, where
#                                the quiet plate and the men-gone plate differ: the men gone, the windows still dark
#   works-w1-working-state.png   W1's plate with everything that differs from the working plate taken from it: the
#                                men gone and every window lit
# Run: bash make_stand_in_pictures.sh STAND_IN_FOLDER
set -e
folder="$1"
tool=/home/user/Music/austerity-explainer/film-kit/paper-film/tools/make_state_picture.py
cd "$folder"
for plate in works-w3-plate works-w1-plate works-w1-men-gone-plate works-w1-working-plate works-w2-plate; do
  python3 -I -c "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=95)" "$plate.png" "$plate.jpg"
done
python3 -I "$tool" works-w1-plate.png works-w1-working-plate.png works-w1-plate.png works-w1-men-gone-plate.png \
  works-w1-men-gone-state.png works-w1-men-gone-mask.png --look works-w1-men-gone-look.jpg
python3 -I "$tool" works-w1-plate.png works-w1-working-plate.png works-w1-plate.png works-w1-working-plate.png \
  works-w1-working-state.png works-w1-working-mask.png --look works-w1-working-look.jpg
