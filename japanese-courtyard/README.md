# Japanese courtyard

What this is: a quick Japanese-style courtyard built in Blender 5.2 by script, using the Astra Painted Workbench add-on
(version 0.2.0, the user's upload), and photographed at golden hour.

- `01 Japanese courtyard - golden hour photo.png`: the photo, 2400 x 1600.
- `build_courtyard.py`: builds the scene and takes the photo. `astra_loader.py`: loads the add-on from its unpacked folder and holds a
  small Blender 5.2 workaround (the add-on was written for 5.1).
- `Japanese courtyard - project story.md`: the goal, what was tried (failures included), word list and next step.

The add-on itself is not in this folder (it is the user's own upload). To rebuild, unpack it somewhere and run:

    blender -b --disable-autoexec --python build_courtyard.py -- ADDON_FOLDER OUT_NAME [--quick] [--samples N] [--width W]

`--quick` makes a small preview in about 25 seconds. The full photo takes about 13 minutes on 4 processors.
