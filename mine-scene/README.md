# Coal mine scene

What this is: a coal-mine scene built in Blender 5.2 by script from the six surface pictures, normal maps and height maps the user uploaded
(brick, slate, wood, rusted metal, mud, gravel), photographed at dusk in a tall 9:16 frame.

- `01 Coal mine - dusk photo 1080x1920.png`: the photo.
- `Coal mine - project story.md`: goal, what was tried (failures included), word list, next step.
- `assemble_mine.py`: builds every part and takes the photo. `lib/mine_common.py`: shared toolbox. `lib/prepare_textures.py`: prepares the uploaded textures.
- `modules/`: one file per part (engine house, headframe, chimney and smoke, track and carts, ground and yard, village and sky). `previews/`: each part's own preview script.
- `tests/`: the small test scenes used to check the maps and real displacement, plus dependency-free design regression checks.
- `Notes for the six builders.md`: the brief the parallel builders worked from.

The current scene uses a procedural physical dusk sky by default. Set `MINE_SKY_MODE=painted` to restore the original painted cloudy sky.
Run the layout and wiring checks with `python3 -m unittest discover -s tests -p 'test_design_regressions.py'`.

The user's uploaded pictures and maps are not in this folder. To rebuild: unpack them, run `lib/prepare_textures.py COLOUR_FOLDER MAPS_FOLDER textures_ready`
(see its first lines), then `blender -b --disable-autoexec --python assemble_mine.py -- OUT_NAME --width 1080 --samples 128`
(about 8 minutes on 4 processors). Plain Blender only: no film plugin, no add-on.
