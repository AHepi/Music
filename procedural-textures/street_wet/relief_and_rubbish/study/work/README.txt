What is in this folder (plain words)
------------------------------------
This is the study's working folder. Nothing in it is a deliverable on its own; the note ("10 Research - sett relief and rubbish for the street.md", one folder up) is.
  r01 ...  r13      the pictures (JPEG) and measurements of each Blender run, in order: r01 baseline + diagnosis, r02 to r04 and r06 first solution tries, r05, r09, r11 rubbish prototype
                    pictures, r07 the whole lighting test set with the joint picture mild1, r08 the fourth tests (texture filter, hybrid geometry, 1080 x 1920), r10 and r12 the puddle
                    masks (plain light), r13 the self-test of the one-command script. Each has measurements.json (and measurements_nopuddle.json where the puddle dots were left out) and
                    the masks (mask_<camera>_<size>.png: R = joint, G = stone face, B = road).
  jobs/             the lists of pictures each Blender run drew (JSON), written by tools/b06*_make_*jobs*.py
  logs/             what each run printed
  note_text/        the hand-written text parts of the note, with [[PLACEHOLDERS]] that tools/b13_write_note.py fills from the measurement files
  baseline_store/   the baseline measurements renamed to the test set's picture names (lockout_A_* -> lockout_B_*), for a first report
  cal/              the lighting calibration pictures (sheets only)
  polyhaven_download/  Poly Haven's 2k ambient occlusion and height pictures of square_cobblestone (CC0), downloaded only to measure them
  *.png at this level: joint_cores.png (the measuring mask picture), joint_cavity*.png (the joint pictures; joint_cavity_closed.png is the recommended one), joint_height.png (the groove
                    picture for real geometry), rubbish_plan_mask*.png (the rubbish masks), joint_mask_*.png / joint_*.json (checks), plan_street.json / plan_lockout.json (the street plan)
  look_*.jpg        the picture sheets as first made (the finished ones are copied to ../pictures)
